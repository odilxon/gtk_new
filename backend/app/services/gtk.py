from datetime import date

from fastapi import HTTPException, status
from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import GTK, Category, Country, Product, Regime
from app.schemas.gtk import GTKItem, GTKStats
from app.schemas.common import Paginated, TopItem


def _apply_filters(
    stmt: Select,
    *,
    regime: str | None,
    country_id: int | None,
    region_id: int | None,
    category_id: int | None,
    product_id: int | None,
    company_uzb_id: int | None,
    company_foreign_id: int | None,
    date_from: date | None,
    date_to: date | None,
    search: str | None,
    tnved: list[str] | None = None,
) -> Select:
    if regime:
        stmt = stmt.where(GTK.regime == Regime[regime])
    if country_id:
        stmt = stmt.where(GTK.country_id == country_id)
    if region_id:
        stmt = stmt.where(GTK.region_id == region_id)
    if product_id:
        stmt = stmt.where(GTK.product_id == product_id)
    if company_uzb_id:
        stmt = stmt.where(GTK.company_uzb_id == company_uzb_id)
    if company_foreign_id:
        stmt = stmt.where(GTK.company_foreign_id == company_foreign_id)
    if date_from:
        stmt = stmt.where(GTK.date >= date_from)
    if date_to:
        stmt = stmt.where(GTK.date <= date_to)
    if category_id or search or tnved:
        stmt = stmt.join(Product, GTK.product_id == Product.id)
        if category_id:
            stmt = stmt.where(Product.category_id == category_id)
        if search:
            like = f"%{search}%"
            stmt = stmt.where(
                Product.name.ilike(like) | Product.tnved.ilike(like)
            )
        if tnved:
            stmt = stmt.where(Product.tnved.in_(tnved))
    return stmt


def _to_item(r: GTK) -> GTKItem:
    return GTKItem(
        id=r.id,
        regime=r.regime.value,
        country_id=r.country_id,
        country_name=r.country.name if r.country else None,
        address_uz=r.address_uz,
        address_foreign=r.address_foreign,
        region_id=r.region_id,
        region_name=r.region.name if r.region else None,
        company_uzb_id=r.company_uzb_id,
        company_uzb_name=r.company_uzb.name if r.company_uzb else None,
        company_foreign_id=r.company_foreign_id,
        company_foreign_name=r.company_foreign.name if r.company_foreign else None,
        product_id=r.product_id,
        product_name=r.product.name if r.product else None,
        category_id=r.product.category_id if r.product else None,
        category_name=r.product.category.name
        if r.product and r.product.category
        else None,
        tnved=r.product.tnved if r.product else None,
        unit=r.unit,
        weight=r.weight,
        quantity=r.quantity,
        price_thousand=r.price_thousand,
        date=r.date,
    )


async def list_gtk(
    db: AsyncSession,
    *,
    page: int,
    page_size: int,
    regime: str | None = None,
    country_id: int | None = None,
    region_id: int | None = None,
    category_id: int | None = None,
    product_id: int | None = None,
    company_uzb_id: int | None = None,
    company_foreign_id: int | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    search: str | None = None,
    tnved: list[str] | None = None,
) -> Paginated[GTKItem]:
    filters = dict(
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

    base = select(GTK).options(
        selectinload(GTK.country),
        selectinload(GTK.region),
        selectinload(GTK.product).selectinload(Product.category),
        selectinload(GTK.company_uzb),
        selectinload(GTK.company_foreign),
    )
    base = _apply_filters(base, **filters)

    count_stmt = _apply_filters(select(func.count(GTK.id)), **filters)

    offset = (page - 1) * page_size
    rows = (
        await db.execute(base.order_by(GTK.date.desc()).offset(offset).limit(page_size))
    ).scalars().all()
    total = (await db.execute(count_stmt)).scalar_one()

    total_pages = (total + page_size - 1) // page_size if total else 0
    return Paginated[GTKItem](
        items=[_to_item(r) for r in rows],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


async def get_record(db: AsyncSession, record_id: int) -> GTKItem:
    stmt = (
        select(GTK)
        .where(GTK.id == record_id)
        .options(
            selectinload(GTK.country),
            selectinload(GTK.region),
            selectinload(GTK.product).selectinload(Product.category),
            selectinload(GTK.company_uzb),
            selectinload(GTK.company_foreign),
        )
    )
    record = (await db.execute(stmt)).scalar_one_or_none()
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="GTK record not found"
        )
    return _to_item(record)


async def get_stats(db: AsyncSession) -> GTKStats:
    total = (await db.execute(select(func.count(GTK.id)))).scalar_one()

    sums = (
        await db.execute(
            select(
                GTK.regime,
                func.coalesce(func.sum(GTK.price_thousand), 0.0),
            ).group_by(GTK.regime)
        )
    ).all()
    import_sum = 0.0
    export_sum = 0.0
    for regime, total_sum in sums:
        if regime == Regime.ИМ:
            import_sum = float(total_sum)
        elif regime == Regime.ЭК:
            export_sum = float(total_sum)

    countries_rows = (
        await db.execute(
            select(Country.id, Country.name, func.count(GTK.id).label("cnt"))
            .join(GTK, GTK.country_id == Country.id)
            .group_by(Country.id, Country.name)
            .order_by(func.count(GTK.id).desc())
            .limit(5)
        )
    ).all()

    categories_rows = (
        await db.execute(
            select(Category.id, Category.name, func.count(GTK.id).label("cnt"))
            .join(Product, Product.category_id == Category.id)
            .join(GTK, GTK.product_id == Product.id)
            .group_by(Category.id, Category.name)
            .order_by(func.count(GTK.id).desc())
            .limit(5)
        )
    ).all()

    return GTKStats(
        total_count=total,
        import_sum=import_sum,
        export_sum=export_sum,
        top_countries=[TopItem(id=r.id, name=r.name, count=r.cnt) for r in countries_rows],
        top_categories=[TopItem(id=r.id, name=r.name, count=r.cnt) for r in categories_rows],
    )
