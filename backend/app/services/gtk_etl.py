"""ETL загрузки Excel → таблица gtk с дедупликацией.

Используется и из CLI (`scripts/db_load.py`), и из HTTP-эндпоинта
`/api/admin/upload-gtk`. Дубликаты gtk-строк отсекаются через UNIQUE INDEX
по `dedup_hash` (SHA-256 от канонического представления полей строки).

ВАЖНО: функция `compute_row_hash` вызывается из миграции `0003_gtk_dedup_hash`
для бэкфилла существующих данных. Менять формат можно только синхронно с
новой миграцией, пересчитывающей все хеши.
"""
from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass
from datetime import date as _date
from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.database import sync_engine
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

# Та же константа, что и в старом db_load — латинская "E" в "Eд.измерения".
COL_UNIT = "Eд.измерения"

BATCH_SIZE = 5000


@dataclass
class EtlResult:
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

    def to_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()


# ─── хеш ────────────────────────────────────────────────────────────────


def _f(v: Any) -> str:
    if v is None:
        return ""
    return f"{float(v):.6f}"


def _s(v: Any) -> str:
    return "" if v is None else str(v)


def compute_row_hash(
    *,
    date: _date | None,
    regime: Any,
    country_id: int | None,
    product_id: int | None,
    company_uzb_id: int | None,
    company_foreign_id: int | None,
    address_uz: str | None,
    address_foreign: str | None,
    unit: str | None,
    weight: float | None,
    quantity: float | None,
    price_thousand: float | None,
) -> str:
    """Канонический SHA-256 для строки gtk.

    Формат: pipe-separated, числа форматируются как `f"{v:.6f}"`, NULL → "".
    Регим — строковое значение енама ('ИМ' / 'ЭК').
    """
    if isinstance(regime, Regime):
        regime_str = regime.value
    else:
        regime_str = str(regime) if regime is not None else ""

    parts = [
        date.isoformat() if date else "",
        regime_str,
        _s(country_id),
        _s(product_id),
        _s(company_uzb_id),
        _s(company_foreign_id),
        address_uz or "",
        address_foreign or "",
        unit or "",
        _f(weight),
        _f(quantity),
        _f(price_thousand),
    ]
    canonical = "|".join(parts)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


# ─── загрузка ───────────────────────────────────────────────────────────


def load_excel(excel_path: str | Path, *, engine: Engine | None = None) -> EtlResult:
    """Загрузить Excel-файл в БД с дедупликацией. Sync — функцию можно
    вызывать как из CLI, так и из FastAPI-хэндлера через `run_in_threadpool`.
    """
    started = time.monotonic()
    path = Path(excel_path)

    df = pd.read_excel(path)
    rows_total = len(df)

    Session = sessionmaker(bind=engine or sync_engine)
    session = Session()
    try:
        countries_map = _upsert_lookup(session, Country, df["Страна"].dropna().unique())
        regions_raw = [
            n for n in df["Область"].dropna().unique() if str(n).strip()
        ] if "Область" in df.columns else []
        regions_map = _upsert_lookup(session, Region, regions_raw)
        categories_map = _upsert_lookup(
            session, Category, df["Категория продукции"].dropna().unique()
        )
        products_map = _upsert_products(session, df, categories_map)
        companies_uzb_map = _upsert_companies_uzb(session, df)
        companies_foreign_map = _upsert_companies_foreign(session, df)

        added, dup, invalid = _insert_gtk_rows(
            session,
            df,
            countries_map=countries_map,
            regions_map=regions_map,
            products_map=products_map,
            companies_uzb_map=companies_uzb_map,
            companies_foreign_map=companies_foreign_map,
        )
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

    return EtlResult(
        rows_total=rows_total,
        added=added,
        duplicates_skipped=dup,
        invalid_skipped=invalid,
        countries=len(countries_map),
        regions=len(regions_map),
        categories=len(categories_map),
        products=len(products_map),
        companies_uzb=len(companies_uzb_map),
        companies_foreign=len(companies_foreign_map),
        duration_ms=int((time.monotonic() - started) * 1000),
    )


def _insert_gtk_rows(
    session: Session,
    df: pd.DataFrame,
    *,
    countries_map: dict[str, int],
    regions_map: dict[str, int],
    products_map: dict[tuple, int],
    companies_uzb_map: dict[str, int],
    companies_foreign_map: dict[str, int],
) -> tuple[int, int, int]:
    """Возвращает (added, duplicates_skipped, invalid_skipped)."""
    added = 0
    duplicates = 0
    invalid = 0
    batch: list[dict[str, Any]] = []

    for _, row in df.iterrows():
        country_id = countries_map.get(row["Страна"])
        if not country_id:
            invalid += 1
            continue

        tnved = str(row["ТНВЕД"])
        product_id = products_map.get(
            (row["Категория продукции"], row["Товар"], tnved)
        )
        if not product_id:
            invalid += 1
            continue

        region_name = row.get("Область") if "Область" in row else None
        region_id = (
            regions_map.get(region_name) if pd.notna(region_name) else None
        )

        stir = row.get("СТИР Узб")
        company_uzb_id = (
            companies_uzb_map.get(str(stir)) if pd.notna(stir) else None
        )
        company_foreign_id = companies_foreign_map.get(row["Организация Хориж"])

        address_uz = row["Адрес Узб"] if pd.notna(row.get("Адрес Узб")) else None
        address_foreign = (
            row["Адрес Хориж"] if pd.notna(row.get("Адрес Хориж")) else None
        )
        unit = row[COL_UNIT] if pd.notna(row.get(COL_UNIT)) else None
        weight = float(row["Вес(кг)"]) if pd.notna(row.get("Вес(кг)")) else None
        quantity = (
            float(row["Количество"]) if pd.notna(row.get("Количество")) else None
        )
        # Excel-колонка "Цена(тыс)" — значение в тысячах долларов; домножаем,
        # чтобы в БД лежала фактическая сумма.
        price_thousand = (
            float(row["Цена(тыс)"]) * 1000 if pd.notna(row.get("Цена(тыс)")) else None
        )

        try:
            d = pd.to_datetime(row["Дата"]).date()
        except Exception:
            invalid += 1
            continue

        regime = Regime[row["Режим"]]

        dedup_hash = compute_row_hash(
            date=d,
            regime=regime,
            country_id=country_id,
            product_id=product_id,
            company_uzb_id=company_uzb_id,
            company_foreign_id=company_foreign_id,
            address_uz=address_uz,
            address_foreign=address_foreign,
            unit=unit,
            weight=weight,
            quantity=quantity,
            price_thousand=price_thousand,
        )

        batch.append(
            {
                "regime": regime,
                "country_id": country_id,
                "address_uz": address_uz,
                "address_foreign": address_foreign,
                "region_id": region_id,
                "company_uzb_id": company_uzb_id,
                "company_foreign_id": company_foreign_id,
                "product_id": product_id,
                "unit": unit,
                "weight": weight,
                "quantity": quantity,
                "price_thousand": price_thousand,
                "date": d,
                "dedup_hash": dedup_hash,
            }
        )

        if len(batch) >= BATCH_SIZE:
            ins, skipped = _flush_batch(session, batch)
            added += ins
            duplicates += skipped
            batch.clear()

    if batch:
        ins, skipped = _flush_batch(session, batch)
        added += ins
        duplicates += skipped

    return added, duplicates, invalid


def _flush_batch(session: Session, batch: list[dict[str, Any]]) -> tuple[int, int]:
    # Сначала отсечём дубликаты внутри самого батча — если в Excel две
    # одинаковые строки, ON CONFLICT DO NOTHING вставит одну, но мы хотим
    # знать число «уникальных-новых» против дублей.
    seen: set[str] = set()
    unique_batch: list[dict[str, Any]] = []
    intra_batch_dups = 0
    for item in batch:
        h = item["dedup_hash"]
        if h in seen:
            intra_batch_dups += 1
            continue
        seen.add(h)
        unique_batch.append(item)

    if not unique_batch:
        return 0, intra_batch_dups

    stmt = pg_insert(GTK.__table__).values(unique_batch)
    stmt = stmt.on_conflict_do_nothing(index_elements=["dedup_hash"])
    result = session.execute(stmt)
    session.commit()

    inserted = result.rowcount or 0
    db_dups = len(unique_batch) - inserted
    return inserted, intra_batch_dups + db_dups


# ─── upsert справочников (как раньше) ──────────────────────────────────


def _upsert_lookup(session: Session, model, names) -> dict[str, int]:
    existing = {x.name: x.id for x in session.query(model).all()}
    for name in names:
        if pd.notna(name) and name not in existing:
            session.add(model(name=name))
    session.commit()
    return {x.name: x.id for x in session.query(model).all()}


def _upsert_products(
    session: Session, df: pd.DataFrame, categories_map: dict[str, int]
) -> dict[tuple, int]:
    existing_keys: set[tuple] = {
        (p.category.name, p.name, p.tnved) for p in session.query(Product).all()
    }
    rows = df.drop_duplicates(subset=["Категория продукции", "Товар", "ТНВЕД"])
    for _, row in rows.iterrows():
        cat_name = row["Категория продукции"]
        prod_name = row["Товар"]
        tnved = str(row["ТНВЕД"])
        if pd.isna(cat_name) or pd.isna(prod_name):
            continue
        category_id = categories_map.get(cat_name)
        if not category_id:
            continue
        if (cat_name, prod_name, tnved) in existing_keys:
            continue
        session.add(Product(category_id=category_id, name=prod_name, tnved=tnved))
    session.commit()
    return {
        (p.category.name, p.name, p.tnved): p.id for p in session.query(Product).all()
    }


def _upsert_companies_uzb(session: Session, df: pd.DataFrame) -> dict[str, int]:
    existing = {c.stir: c.id for c in session.query(CompanyUzb).all()}
    rows = df.drop_duplicates(subset=["СТИР Узб", "Организация Узб"])
    for _, row in rows.iterrows():
        stir = row["СТИР Узб"]
        name = row["Организация Узб"]
        if pd.isna(stir) or pd.isna(name):
            continue
        if str(stir) in existing:
            continue
        session.add(CompanyUzb(stir=str(stir), name=name))
    session.commit()
    return {c.stir: c.id for c in session.query(CompanyUzb).all()}


def _upsert_companies_foreign(session: Session, df: pd.DataFrame) -> dict[str, int]:
    existing = {c.name: c.id for c in session.query(CompanyForeign).all()}
    rows = df.drop_duplicates(subset=["Организация Хориж"])
    for _, row in rows.iterrows():
        name = row["Организация Хориж"]
        if pd.notna(name) and name not in existing:
            session.add(CompanyForeign(name=name))
    session.commit()
    return {c.name: c.id for c in session.query(CompanyForeign).all()}
