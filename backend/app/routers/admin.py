from __future__ import annotations

import os
import tempfile

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel

from app.security import get_current_admin
from app.services.gtk_etl import EtlResult, load_excel

router = APIRouter(
    prefix="/api/admin",
    tags=["admin"],
    dependencies=[Depends(get_current_admin)],
)

# Лимит размера файла. Подняли до 100 MB — типовой Excel ожидается 60–80 MB.
MAX_BYTES = 100 * 1024 * 1024


class UploadResponse(BaseModel):
    rows_total: int
    added: int
    duplicates_skipped: int
    invalid_skipped: int
    countries: int
    regions: int
    categories: int
    products: int
    companies_uzb: int
    companies_foreign: int
    duration_ms: int

    @classmethod
    def from_etl(cls, r: EtlResult) -> "UploadResponse":
        return cls(**r.to_dict())


@router.post("/upload-gtk", response_model=UploadResponse)
async def upload_gtk(file: UploadFile = File(...)) -> UploadResponse:
    if not (file.filename or "").lower().endswith(".xlsx"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only .xlsx files are accepted",
        )

    # Стримим во временный файл и одновременно проверяем лимит размера.
    fd, tmp_path = tempfile.mkstemp(suffix=".xlsx")
    try:
        size = 0
        with os.fdopen(fd, "wb") as out:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                size += len(chunk)
                if size > MAX_BYTES:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"File too large (>{MAX_BYTES // (1024 * 1024)} MB)",
                    )
                out.write(chunk)

        # ETL — синхронный (pandas + sync engine), уводим из event loop.
        result = await run_in_threadpool(load_excel, tmp_path)

        # Авто-обогащение ISO-кодов стран — на случай новых стран в Excel.
        # Регионы теперь не enrich'им (по решению пользователя).
        try:
            from scripts.enrich import enrich_countries  # ленивый импорт

            await run_in_threadpool(enrich_countries)
        except Exception:
            # необязательная стадия, не валим запрос если упала
            pass

        return UploadResponse.from_etl(result)
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
