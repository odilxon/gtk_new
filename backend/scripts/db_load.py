"""ETL для загрузки данных из Excel в БД.

Использование:
    python -m scripts.db_load load gtk_data_2020.xlsx
    python -m scripts.db_load clean     # удалить все записи из gtk (справочники остаются)
    python -m scripts.db_load drop      # снести все таблицы (опасно)

Перед первой загрузкой накатить миграции: `alembic upgrade head`.
"""
from __future__ import annotations

import sys

import pandas as pd
from sqlalchemy.orm import sessionmaker

from app.database import Base, sync_engine
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


def clean_gtk() -> None:
    Session = sessionmaker(bind=sync_engine)
    session = Session()
    try:
        deleted = session.query(GTK).delete()
        session.commit()
        print(f"Удалено записей из gtk: {deleted}")
    finally:
        session.close()


# В Excel колонка единицы измерения называется "Eд.измерения" — первая буква
# латинская "E", не кириллическая "Е". Не править.
COL_UNIT = "Eд.измерения"


def drop_db() -> None:
    Base.metadata.drop_all(sync_engine)
    print("Таблицы удалены")


def load_data(excel_path: str) -> None:
    print(f"Чтение файла: {excel_path}")
    df = pd.read_excel(excel_path)
    print(f"Прочитано {len(df)} записей")

    Session = sessionmaker(bind=sync_engine)
    session = Session()

    try:
        countries_map = _upsert_lookup(session, Country, df["Страна"].dropna().unique())
        print(f"  стран: {len(countries_map)}")

        regions_raw = [
            n for n in df["Область"].dropna().unique() if str(n).strip()
        ]
        regions_map = _upsert_lookup(session, Region, regions_raw)
        print(f"  областей: {len(regions_map)}")

        categories_map = _upsert_lookup(
            session, Category, df["Категория продукции"].dropna().unique()
        )
        print(f"  категорий: {len(categories_map)}")

        products_map = _upsert_products(session, df, categories_map)
        print(f"  товаров: {len(products_map)}")

        companies_uzb_map = _upsert_companies_uzb(session, df)
        print(f"  узб. компаний: {len(companies_uzb_map)}")

        companies_foreign_map = _upsert_companies_foreign(session, df)
        print(f"  иностр. компаний: {len(companies_foreign_map)}")

        print("Загрузка GTK записей...")
        added = 0
        for idx, row in df.iterrows():
            country_id = countries_map.get(row["Страна"])
            if not country_id:
                continue

            tnved = str(row["ТНВЕД"])
            product_id = products_map.get(
                (row["Категория продукции"], row["Товар"], tnved)
            )
            if not product_id:
                continue

            region_name = row["Область"]
            region_id = (
                regions_map.get(region_name) if pd.notna(region_name) else None
            )

            stir = row.get("СТИР Узб")
            company_uzb_id = (
                companies_uzb_map.get(str(stir)) if pd.notna(stir) else None
            )

            company_foreign_id = companies_foreign_map.get(row["Организация Хориж"])

            session.add(
                GTK(
                    regime=Regime[row["Режим"]],
                    country_id=country_id,
                    address_uz=row["Адрес Узб"]
                    if pd.notna(row["Адрес Узб"])
                    else None,
                    address_foreign=row["Адрес Хориж"]
                    if pd.notna(row["Адрес Хориж"])
                    else None,
                    region_id=region_id,
                    company_uzb_id=company_uzb_id,
                    company_foreign_id=company_foreign_id,
                    product_id=product_id,
                    unit=row[COL_UNIT] if pd.notna(row[COL_UNIT]) else None,
                    weight=float(row["Вес(кг)"])
                    if pd.notna(row.get("Вес(кг)"))
                    else None,
                    quantity=float(row["Количество"])
                    if pd.notna(row.get("Количество"))
                    else None,
                    price_thousand=float(row["Цена(тыс)"])
                    if pd.notna(row.get("Цена(тыс)"))
                    else None,
                    date=pd.to_datetime(row["Дата"]).date(),
                )
            )
            added += 1
            if added % 500 == 0:
                session.commit()
                print(f"  обработано {added}")

        session.commit()
        print(f"Готово: добавлено {added} записей")

    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def _upsert_lookup(session, model, names) -> dict[str, int]:
    existing = {x.name: x.id for x in session.query(model).all()}
    for name in names:
        if pd.notna(name) and name not in existing:
            session.add(model(name=name))
    session.commit()
    return {x.name: x.id for x in session.query(model).all()}


def _upsert_products(session, df, categories_map) -> dict[tuple, int]:
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


def _upsert_companies_uzb(session, df) -> dict[str, int]:
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


def _upsert_companies_foreign(session, df) -> dict[str, int]:
    existing = {c.name: c.id for c in session.query(CompanyForeign).all()}
    rows = df.drop_duplicates(subset=["Организация Хориж"])
    for _, row in rows.iterrows():
        name = row["Организация Хориж"]
        if pd.notna(name) and name not in existing:
            session.add(CompanyForeign(name=name))
    session.commit()
    return {c.name: c.id for c in session.query(CompanyForeign).all()}


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd == "load":
        excel_path = sys.argv[2] if len(sys.argv) > 2 else "gtk_data_2020.xlsx"
        load_data(excel_path)
    elif cmd == "clean":
        clean_gtk()
    elif cmd == "drop":
        drop_db()
    else:
        print(f"Неизвестная команда: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()
