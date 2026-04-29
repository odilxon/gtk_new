"""Один раз помножить gtk.price_thousand на 1000.

Excel-колонка называлась "Цена(тыс)" — значения там в тысячах долларов.
Старая версия db_load складывала их в БД как есть, поэтому в gtk сейчас
лежит, например, 17.56 вместо 17560. Этот скрипт разово исправляет уже
залитые данные.

После этого в db_load уже стоит множитель *1000 на этапе ETL — для свежих
загрузок повторять не нужно. И ВНИМАНИЕ: нельзя запускать скрипт дважды
по тем же данным, иначе они умножатся ещё на 1000.

Использование:
    python -m scripts.fix_prices
"""
from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.orm import sessionmaker

from app.database import sync_engine


def main() -> None:
    Session = sessionmaker(bind=sync_engine)
    session = Session()
    try:
        before = session.execute(
            text("SELECT COUNT(*) FROM gtk WHERE price_thousand IS NOT NULL")
        ).scalar()
        print(f"К умножению: {before:,} строк")

        res = session.execute(
            text(
                "UPDATE gtk SET price_thousand = price_thousand * 1000 "
                "WHERE price_thousand IS NOT NULL"
            )
        )
        session.commit()
        print(f"Готово: обновлено {res.rowcount} строк.")
    finally:
        session.close()


if __name__ == "__main__":
    main()
