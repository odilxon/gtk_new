"""ETL для загрузки данных из Excel в БД.

Использование:
    python -m scripts.db_load load gtk_data_2020.xlsx
    python -m scripts.db_load clean     # удалить все записи из gtk (справочники остаются)
    python -m scripts.db_load drop      # снести все таблицы (опасно)

Перед первой загрузкой накатить миграции: `alembic upgrade head`.

Сама ETL-логика лежит в `app.services.gtk_etl` — её же использует
HTTP-эндпоинт `/api/admin/upload-gtk`.
"""
from __future__ import annotations

import sys

from sqlalchemy.orm import sessionmaker

from app.database import Base, sync_engine
from app.models import GTK
from app.services.gtk_etl import load_excel


def clean_gtk() -> None:
    Session = sessionmaker(bind=sync_engine)
    session = Session()
    try:
        deleted = session.query(GTK).delete()
        session.commit()
        print(f"Удалено записей из gtk: {deleted}")
    finally:
        session.close()


def drop_db() -> None:
    Base.metadata.drop_all(sync_engine)
    print("Таблицы удалены")


def load_data(excel_path: str) -> None:
    print(f"Чтение файла: {excel_path}")
    res = load_excel(excel_path)
    print(
        f"Готово: добавлено {res.added}, "
        f"пропущено как дубль {res.duplicates_skipped}, "
        f"невалидных {res.invalid_skipped}, "
        f"всего в файле {res.rows_total}, "
        f"за {res.duration_ms} мс"
    )
    print(
        f"  стран {res.countries}, областей {res.regions}, "
        f"категорий {res.categories}, товаров {res.products}, "
        f"узб. компаний {res.companies_uzb}, иностр. компаний {res.companies_foreign}"
    )


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
