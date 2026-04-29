from __future__ import annotations

from datetime import date

from sqlalchemy import Select, and_, extract, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    GTK,
    Category,
    CompanyForeign,
    CompanyUzb,
    Country,
    Product,
    Region,
    Regime,
)
from app.schemas.charts import (
    GroupBreakdown,
    GroupBreakdownRow,
    GroupSummary,
    GroupTotals,
    MonthlyResponse,
    RegionPoint,
    RegionsResponse,
    TopItemRow,
    TopItems,
    TotalsResponse,
    WorldPoint,
    WorldResponse,
)
from app.services.tnved_groups import (
    MEVA_EXACT,
    MEVA_PREFIXES,
    fixes_breakdown,
    oziq_tnveds,
)

MONTHS_RU = [
    "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
    "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь",
]

REGION_CODES = {
    "Андижон вилояти": "uz-an",
    "Бухоро вилояти": "uz-bu",
    "Жиззах вилояти": "uz-ji",
    "Навоий вилояти": "uz-nw",
    "Наманган вилояти": "uz-ng",
    "Самарқанд вилояти": "uz-sa",
    "Сирдарё вилояти": "uz-si",
    "Сурхондарё вилояти": "uz-su",
    "Тошкент вилояти": "uz-ta",
    "Тошкент шаҳри": "uz-tk",
    "Фарғона вилояти": "uz-fa",
    "Хоразм вилояти": "uz-kh",
    "Қашқадарё вилояти": "uz-qa",
    "Қорақалпоғистон Республикаси": "uz-qr",
}


# ─── фильтры ────────────────────────────────────────────────────────────


def _apply_common(
    stmt: Select,
    *,
    year: int | None = None,
    tnved: list[str] | None = None,
    region_id: int | None = None,
    country_id: int | None = None,
) -> Select:
    if year:
        stmt = stmt.where(GTK.date >= date(year, 1, 1)).where(
            GTK.date < date(year + 1, 1, 1)
        )
    if region_id:
        stmt = stmt.where(GTK.region_id == region_id)
    if country_id:
        stmt = stmt.where(GTK.country_id == country_id)
    if tnved:
        stmt = stmt.join(Product, GTK.product_id == Product.id, isouter=False)
        stmt = stmt.where(Product.tnved.in_(tnved))
    return stmt


def _meva_filter():
    return or_(
        Product.tnved.in_(MEVA_EXACT),
        *[Product.tnved.like(f"{p}%") for p in MEVA_PREFIXES],
    )


# ─── эндпоинты ──────────────────────────────────────────────────────────


async def years(db: AsyncSession) -> list[int]:
    rows = (
        await db.execute(
            select(extract("year", GTK.date)).distinct().order_by(extract("year", GTK.date).desc())
        )
    ).all()
    return [int(r[0]) for r in rows if r[0] is not None]


async def monthly(
    db: AsyncSession,
    *,
    tnved: list[str] | None,
    region_id: int | None,
    country_id: int | None,
) -> MonthlyResponse:
    yrs = await years(db)
    imports: dict[str, list[float | None]] = {}
    exports: dict[str, list[float | None]] = {}
    import_grow: dict[str, list[float | None]] = {}
    export_grow: dict[str, list[float | None]] = {}

    for y in yrs:
        for regime, sink, sink_grow in (
            (Regime.ИМ, imports, import_grow),
            (Regime.ЭК, exports, export_grow),
        ):
            stmt = (
                select(
                    extract("month", GTK.date).label("m"),
                    func.coalesce(func.sum(GTK.price_thousand), 0.0),
                )
                .where(GTK.regime == regime)
                .group_by("m")
                .order_by("m")
            )
            stmt = _apply_common(
                stmt, year=y, tnved=tnved, region_id=region_id, country_id=country_id
            )
            rows = (await db.execute(stmt)).all()
            arr: list[float | None] = [0.0] * 12
            for m, s in rows:
                arr[int(m) - 1] = float(s or 0)
            sink[str(y)] = arr.copy()

            cum: list[float | None] = arr.copy()
            for i in range(1, 12):
                if cum[i] is not None and cum[i - 1] is not None:
                    cum[i] += cum[i - 1]
            sink_grow[str(y)] = cum

    return MonthlyResponse(
        months=MONTHS_RU,
        imports=imports,
        exports=exports,
        import_grow=import_grow,
        export_grow=export_grow,
    )


async def totals(
    db: AsyncSession,
    *,
    year: int,
    tnved: list[str] | None,
    region_id: int | None,
    country_id: int | None,
) -> TotalsResponse:
    async def _sum(regime: Regime) -> GroupTotals:
        stmt = select(
            func.coalesce(func.sum(GTK.price_thousand), 0.0),
            func.coalesce(func.sum(GTK.weight), 0.0),
        ).where(GTK.regime == regime)
        stmt = _apply_common(
            stmt,
            year=year,
            tnved=tnved,
            region_id=region_id,
            country_id=country_id,
        )
        total, massa = (await db.execute(stmt)).one()
        return GroupTotals(total=float(total or 0), massa=float(massa or 0))

    im = await _sum(Regime.ИМ)
    ex = await _sum(Regime.ЭК)
    return TotalsResponse(
        year=year,
        import_=im,
        export=ex,
        total=GroupTotals(total=im.total + ex.total, massa=im.massa + ex.massa),
    )


async def group_summary(
    db: AsyncSession,
    *,
    year: int,
    group: str,
    tnved: list[str] | None,
    region_id: int | None,
    country_id: int | None,
) -> GroupSummary:
    if group == "meva":
        condition = _meva_filter()
    else:
        condition = Product.tnved.in_(oziq_tnveds())

    async def _sum(regime: Regime) -> GroupTotals:
        stmt = (
            select(
                func.coalesce(func.sum(GTK.price_thousand), 0.0),
                func.coalesce(func.sum(GTK.weight), 0.0),
            )
            .join(Product, GTK.product_id == Product.id)
            .where(GTK.regime == regime, condition)
            .where(GTK.date >= date(year, 1, 1))
            .where(GTK.date < date(year + 1, 1, 1))
        )
        if region_id:
            stmt = stmt.where(GTK.region_id == region_id)
        if country_id:
            stmt = stmt.where(GTK.country_id == country_id)
        if tnved:
            stmt = stmt.where(Product.tnved.in_(tnved))
        total, massa = (await db.execute(stmt)).one()
        return GroupTotals(total=float(total or 0), massa=float(massa or 0))

    im = await _sum(Regime.ИМ)
    ex = await _sum(Regime.ЭК)
    return GroupSummary(
        year=year,
        group=group,
        import_=im,
        export=ex,
        total=GroupTotals(total=im.total + ex.total, massa=im.massa + ex.massa),
    )


async def group_breakdown(
    db: AsyncSession,
    *,
    year: int,
    group: str,
    type_: str,
    tnved: list[str] | None,
    region_id: int | None,
    country_id: int | None,
) -> GroupBreakdown:
    breakdown_map = fixes_breakdown(group)
    rows: list[GroupBreakdownRow] = []

    for category, codes in breakdown_map.items():
        stmt = (
            select(
                func.coalesce(func.sum(GTK.price_thousand), 0.0),
                func.coalesce(func.sum(GTK.weight), 0.0),
            )
            .join(Product, GTK.product_id == Product.id)
            .where(Product.tnved.in_(codes))
            .where(GTK.date >= date(year, 1, 1))
            .where(GTK.date < date(year + 1, 1, 1))
        )
        if type_ == "import":
            stmt = stmt.where(GTK.regime == Regime.ИМ)
        elif type_ == "export":
            stmt = stmt.where(GTK.regime == Regime.ЭК)
        if region_id:
            stmt = stmt.where(GTK.region_id == region_id)
        if country_id:
            stmt = stmt.where(GTK.country_id == country_id)
        if tnved:
            stmt = stmt.where(Product.tnved.in_(tnved))
        total, massa = (await db.execute(stmt)).one()
        total = float(total or 0)
        massa = float(massa or 0)
        avg = round(massa / total, 2) if total > 0 else 0
        rows.append(
            GroupBreakdownRow(name=category, massa=massa, total=total, avg=avg)
        )

    rows.sort(key=lambda r: r.total, reverse=True)
    return GroupBreakdown(year=year, group=group, type=type_, rows=rows)


async def top_organizations(
    db: AsyncSession,
    *,
    year: int,
    regime_str: str,
    limit: int,
    tnved: list[str] | None,
    region_id: int | None,
    country_id: int | None,
) -> TopItems:
    if regime_str == "import":
        col = CompanyForeign.name
        join_cls, join_cond = CompanyForeign, GTK.company_foreign_id == CompanyForeign.id
        regime = Regime.ИМ
    else:
        col = CompanyUzb.name
        join_cls, join_cond = CompanyUzb, GTK.company_uzb_id == CompanyUzb.id
        regime = Regime.ЭК

    stmt = (
        select(col, func.coalesce(func.sum(GTK.price_thousand), 0.0).label("s"))
        .join(join_cls, join_cond)
        .where(GTK.regime == regime)
        .where(GTK.date >= date(year, 1, 1))
        .where(GTK.date < date(year + 1, 1, 1))
        .group_by(col)
        .order_by(func.sum(GTK.price_thousand).desc())
        .limit(limit)
    )
    stmt = _apply_common(stmt, tnved=tnved, region_id=region_id, country_id=country_id)
    rows = (await db.execute(stmt)).all()
    return TopItems(
        year=year,
        items=[TopItemRow(label=r[0] or "—", value=float(r[1] or 0)) for r in rows],
    )


async def top_countries(
    db: AsyncSession,
    *,
    year: int,
    regime_str: str,
    limit: int,
    tnved: list[str] | None,
    region_id: int | None,
) -> TopItems:
    regime = Regime.ИМ if regime_str == "import" else Regime.ЭК
    stmt = (
        select(Country.name, func.coalesce(func.sum(GTK.price_thousand), 0.0).label("s"))
        .join(Country, GTK.country_id == Country.id)
        .where(GTK.regime == regime)
        .where(GTK.date >= date(year, 1, 1))
        .where(GTK.date < date(year + 1, 1, 1))
        .group_by(Country.name)
        .order_by(func.sum(GTK.price_thousand).desc())
        .limit(limit)
    )
    stmt = _apply_common(stmt, tnved=tnved, region_id=region_id)
    rows = (await db.execute(stmt)).all()
    return TopItems(
        year=year,
        items=[TopItemRow(label=r[0] or "—", value=float(r[1] or 0)) for r in rows],
    )


async def regions(
    db: AsyncSession,
    *,
    year: int,
    regime_str: str,
    tnved: list[str] | None,
    country_id: int | None,
) -> RegionsResponse:
    regime = Regime.ИМ if regime_str == "import" else Regime.ЭК

    base_stmt = (
        select(
            Region.name,
            func.coalesce(func.sum(GTK.price_thousand), 0.0),
            func.coalesce(func.sum(GTK.weight), 0.0),
        )
        .join(Region, GTK.region_id == Region.id)
        .where(GTK.regime == regime)
        .where(GTK.date >= date(year, 1, 1))
        .where(GTK.date < date(year + 1, 1, 1))
        .group_by(Region.name)
    )
    base_stmt = _apply_common(base_stmt, tnved=tnved, country_id=country_id)
    base_rows = (await db.execute(base_stmt)).all()
    base_map = {name: (float(t or 0), float(m or 0)) for name, t, m in base_rows}

    async def _grouped(condition) -> dict[str, tuple[float, float]]:
        stmt = (
            select(
                Region.name,
                func.coalesce(func.sum(GTK.price_thousand), 0.0),
                func.coalesce(func.sum(GTK.weight), 0.0),
            )
            .join(Region, GTK.region_id == Region.id)
            .join(Product, GTK.product_id == Product.id)
            .where(GTK.regime == regime)
            .where(GTK.date >= date(year, 1, 1))
            .where(GTK.date < date(year + 1, 1, 1))
            .where(condition)
            .group_by(Region.name)
        )
        if country_id:
            stmt = stmt.where(GTK.country_id == country_id)
        rows_ = (await db.execute(stmt)).all()
        return {name: (float(t or 0), float(m or 0)) for name, t, m in rows_}

    meva_map = await _grouped(_meva_filter())
    oziq_map = await _grouped(Product.tnved.in_(oziq_tnveds()))

    items: list[RegionPoint] = []
    max_value = 0.0
    for name, code in REGION_CODES.items():
        total, massa = base_map.get(name, (0.0, 0.0))
        if total <= 0:
            continue
        m_total, m_massa = meva_map.get(name, (0.0, 0.0))
        o_total, o_massa = oziq_map.get(name, (0.0, 0.0))
        max_value = max(max_value, total)
        items.append(
            RegionPoint(
                name=name,
                code=code,
                value=round(total, 2),
                massa=round(massa, 2),
                meva_total=round(m_total, 2),
                meva_massa=round(m_massa, 2),
                oziq_total=round(o_total, 2),
                oziq_massa=round(o_massa, 2),
            )
        )

    return RegionsResponse(
        year=year, regime=regime_str, items=items, max_value=round(max_value, 2)
    )


async def world(
    db: AsyncSession,
    *,
    year: int,
    regime_str: str,
    tnved: list[str] | None,
    region_id: int | None,
) -> WorldResponse:
    regime = Regime.ИМ if regime_str == "import" else Regime.ЭК

    base_stmt = (
        select(
            Country.name,
            Country.iso_code,
            Country.name_uz,
            func.coalesce(func.sum(GTK.price_thousand), 0.0),
            func.coalesce(func.sum(GTK.weight), 0.0),
        )
        .join(Country, GTK.country_id == Country.id)
        .where(GTK.regime == regime)
        .where(GTK.date >= date(year, 1, 1))
        .where(GTK.date < date(year + 1, 1, 1))
        .group_by(Country.id)
    )
    base_stmt = _apply_common(base_stmt, tnved=tnved, region_id=region_id)
    base_rows = (await db.execute(base_stmt)).all()
    base_map = {
        name: {
            "iso": iso,
            "name_uz": uz,
            "total": float(total or 0),
            "massa": float(massa or 0),
        }
        for name, iso, uz, total, massa in base_rows
    }

    async def _grouped(condition) -> dict[str, tuple[float, float]]:
        stmt = (
            select(
                Country.name,
                func.coalesce(func.sum(GTK.price_thousand), 0.0),
                func.coalesce(func.sum(GTK.weight), 0.0),
            )
            .join(Country, GTK.country_id == Country.id)
            .join(Product, GTK.product_id == Product.id)
            .where(GTK.regime == regime)
            .where(GTK.date >= date(year, 1, 1))
            .where(GTK.date < date(year + 1, 1, 1))
            .where(condition)
            .group_by(Country.name)
        )
        if region_id:
            stmt = stmt.where(GTK.region_id == region_id)
        return {
            name: (float(t or 0), float(m or 0))
            for name, t, m in (await db.execute(stmt)).all()
        }

    meva_map = await _grouped(_meva_filter())
    oziq_map = await _grouped(Product.tnved.in_(oziq_tnveds()))

    items: list[WorldPoint] = []
    max_value = 0.0
    for name, payload in base_map.items():
        if payload["total"] <= 0 or not payload["iso"]:
            continue
        m_total, m_massa = meva_map.get(name, (0.0, 0.0))
        o_total, o_massa = oziq_map.get(name, (0.0, 0.0))
        max_value = max(max_value, payload["total"])
        items.append(
            WorldPoint(
                iso=payload["iso"],
                name=name,
                name_uz=payload["name_uz"],
                value=round(payload["total"], 2),
                massa=round(payload["massa"], 2),
                meva_value=round(m_total, 2),
                meva_massa=round(m_massa, 2),
                oziq_value=round(o_total, 2),
                oziq_massa=round(o_massa, 2),
            )
        )

    return WorldResponse(
        year=year, regime=regime_str, items=items, max_value=round(max_value, 2)
    )
