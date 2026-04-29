from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.common import Paginated
from app.schemas.gtk import GTKItem, GTKStats
from app.security import get_current_user
from app.services import gtk as gtk_service

router = APIRouter(prefix="/api/gtk", tags=["gtk"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=Paginated[GTKItem])
async def list_gtk(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    regime: str | None = Query(None),
    country_id: int | None = Query(None),
    region_id: int | None = Query(None),
    category_id: int | None = Query(None),
    product_id: int | None = Query(None),
    company_uzb_id: int | None = Query(None),
    company_foreign_id: int | None = Query(None),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    search: str | None = Query(None),
    tnved: list[str] | None = Query(None),
    db: AsyncSession = Depends(get_db),
) -> Paginated[GTKItem]:
    return await gtk_service.list_gtk(
        db,
        page=page,
        page_size=page_size,
        regime=regime,
        country_id=country_id,
        region_id=region_id,
        category_id=category_id,
        product_id=product_id,
        company_uzb_id=company_uzb_id,
        company_foreign_id=company_foreign_id,
        date_from=date_from,
        date_to=date_to,
        search=search,
        tnved=tnved,
    )


@router.get("/stats", response_model=GTKStats)
async def stats(db: AsyncSession = Depends(get_db)) -> GTKStats:
    return await gtk_service.get_stats(db)


@router.get("/{record_id}", response_model=GTKItem)
async def get_record(
    record_id: int, db: AsyncSession = Depends(get_db)
) -> GTKItem:
    return await gtk_service.get_record(db, record_id)
