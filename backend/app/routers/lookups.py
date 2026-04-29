from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import (
    Category,
    CompanyForeign,
    CompanyUzb,
    Country,
    Product,
    Region,
)
from app.schemas.common import CompanyUzbItem, LookupItem, ProductItem, TnvedSearchItem
from app.security import get_current_user

router = APIRouter(
    prefix="/api",
    tags=["lookups"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/countries", response_model=list[LookupItem])
async def countries(db: AsyncSession = Depends(get_db)) -> list[LookupItem]:
    rows = (await db.execute(select(Country).order_by(Country.name))).scalars().all()
    return [LookupItem(id=c.id, name=c.name) for c in rows]


@router.get("/regions", response_model=list[LookupItem])
async def regions(db: AsyncSession = Depends(get_db)) -> list[LookupItem]:
    rows = (await db.execute(select(Region).order_by(Region.name))).scalars().all()
    return [LookupItem(id=r.id, name=r.name) for r in rows]


@router.get("/categories", response_model=list[LookupItem])
async def categories(db: AsyncSession = Depends(get_db)) -> list[LookupItem]:
    rows = (await db.execute(select(Category).order_by(Category.name))).scalars().all()
    return [LookupItem(id=c.id, name=c.name) for c in rows]


@router.get("/products", response_model=list[ProductItem])
async def products(
    category_id: int | None = Query(None),
    search: str | None = Query(None),
    limit: int = Query(50, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
) -> list[ProductItem]:
    stmt = select(Product)
    if category_id:
        stmt = stmt.where(Product.category_id == category_id)
    if search:
        stmt = stmt.where(Product.name.ilike(f"%{search}%"))
    rows = (await db.execute(stmt.limit(limit))).scalars().all()
    return [
        ProductItem(id=p.id, name=p.name, tnved=p.tnved, category_id=p.category_id)
        for p in rows
    ]


@router.get("/products/tnved-search", response_model=list[TnvedSearchItem])
async def tnved_search(
    q: str = Query(..., min_length=3, max_length=20),
    limit: int = Query(30, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
) -> list[TnvedSearchItem]:
    """Поиск ТНВЕД по префиксу: введи минимум 3 цифры — вернёт уникальные коды.

    Один ТНВЕД может относиться к нескольким товарам — берём `min(name)`
    как репрезентативное название.
    """
    stmt = (
        select(Product.tnved, func.min(Product.name))
        .where(Product.tnved.like(f"{q}%"))
        .group_by(Product.tnved)
        .order_by(Product.tnved)
        .limit(limit)
    )
    rows = (await db.execute(stmt)).all()
    return [TnvedSearchItem(tnved=t, name=n or "") for t, n in rows]


@router.get("/companies-uzb", response_model=list[CompanyUzbItem])
async def companies_uzb(db: AsyncSession = Depends(get_db)) -> list[CompanyUzbItem]:
    rows = (
        await db.execute(select(CompanyUzb).order_by(CompanyUzb.name))
    ).scalars().all()
    return [CompanyUzbItem(id=c.id, name=c.name, stir=c.stir) for c in rows]


@router.get("/companies-foreign", response_model=list[LookupItem])
async def companies_foreign(db: AsyncSession = Depends(get_db)) -> list[LookupItem]:
    rows = (
        await db.execute(select(CompanyForeign).order_by(CompanyForeign.name))
    ).scalars().all()
    return [LookupItem(id=c.id, name=c.name or "") for c in rows]
