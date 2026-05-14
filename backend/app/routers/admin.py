from __future__ import annotations

import os
import tempfile
import zipfile
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel

from app.security import get_current_admin
from app.services.dbf_etl import find_dbf_files, load_dbf
from app.services.gtk_etl import EtlResult, load_excel

router = APIRouter(
    prefix="/api/admin",
    tags=["admin"],
    dependencies=[Depends(get_current_admin)],
)

MAX_BYTES     = 100 * 1024 * 1024   # 100 MB — Excel
MAX_BYTES_DBF = 2 * 1024 * 1024 * 1024  # 2 GB — DBF (zip с файлами ГТД)


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


# ── Excel upload (существующий эндпоинт) ────────────────────────────────────


@router.post("/upload-gtk", response_model=UploadResponse)
async def upload_gtk(file: UploadFile = File(...)) -> UploadResponse:
    if not (file.filename or "").lower().endswith(".xlsx"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only .xlsx files are accepted",
        )

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

        result = await run_in_threadpool(load_excel, tmp_path)

        try:
            from scripts.enrich import enrich_countries
            await run_in_threadpool(enrich_countries)
        except Exception:
            pass

        return UploadResponse.from_etl(result)
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


# ── DBF upload (новый эндпоинт) ─────────────────────────────────────────────


@router.post("/upload-gtk-dbf", response_model=UploadResponse)
async def upload_gtk_dbf(file: UploadFile = File(...)) -> UploadResponse:
    """Загрузить ГТД из DBF-файла или ZIP-архива с DBF-файлами.

    Принимает:
    - .dbf — напрямую главный файл данных (SLVS03 ищется в той же директории)
    - .zip — архив с папкой ГТД (содержащей База*.dbf + SLVS03*.DBF)

    Файлы до 2 GB. Обработка занимает несколько минут для 1M+ записей.
    """
    fname = (file.filename or "").lower()
    if not (fname.endswith(".dbf") or fname.endswith(".zip")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Accepted formats: .dbf or .zip",
        )

    # Сохраняем загружаемый файл во временную директорию
    tmp_dir = tempfile.mkdtemp(prefix="gtk_dbf_")
    try:
        upload_path = Path(tmp_dir) / (file.filename or "upload.dbf")
        size = 0
        with open(upload_path, "wb") as out:
            while True:
                chunk = await file.read(4 * 1024 * 1024)  # 4 MB chunks
                if not chunk:
                    break
                size += len(chunk)
                if size > MAX_BYTES_DBF:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail="File too large (>2 GB)",
                    )
                out.write(chunk)

        work_dir = Path(tmp_dir)
        if fname.endswith(".zip"):
            with zipfile.ZipFile(upload_path) as zf:
                zf.extractall(work_dir)
            work_dir = _find_dbf_folder(work_dir)

        main_dbf, slvs03 = find_dbf_files(work_dir)
        if not main_dbf:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="No DBF data file found in the uploaded archive",
            )

        result = await run_in_threadpool(load_dbf, main_dbf, slvs03)
        return UploadResponse.from_etl(result)

    finally:
        import shutil
        shutil.rmtree(tmp_dir, ignore_errors=True)


def _find_dbf_folder(root: Path) -> Path:
    """Найти папку с DBF внутри распакованного zip."""
    dbfs = list(root.rglob("*.dbf")) + list(root.rglob("*.DBF"))
    if not dbfs:
        return root
    # Папка с самым большим dbf-файлом
    biggest = max(dbfs, key=lambda p: p.stat().st_size)
    return biggest.parent
