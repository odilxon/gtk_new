"""Дополнить данные после первичной загрузки:

- countries: проставить iso_code и name_uz по словарю data/countries_ru_iso.json
- gtk.region_id: извлечь область из address_uz по списку 14 регионов

Использование:
    python -m scripts.enrich countries
    python -m scripts.enrich regions
    python -m scripts.enrich all
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.orm import sessionmaker

from app.database import sync_engine
from app.models import Country, Region

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# Канонический label региона → список подстрок для поиска в address_uz.
# В адресах встречаются и узбекские (кириллица), и русские варианты — нужно
# учитывать оба. Для Тошкент шаҳри явно перечислены городские формы, чтобы
# не спутать с Ташкентской областью; за счёт сортировки по длине ниже
# и фильтра region_id IS NULL они матчатся раньше «Тошкент»/«Ташкент».
REGION_ALIASES: dict[str, list[str]] = {
    "Андижон вилояти": ["Андижон", "Андижан"],
    "Бухоро вилояти": ["Бухоро", "Бухара"],
    "Жиззах вилояти": ["Жиззах", "Джизак"],
    "Навоий вилояти": ["Навоий", "Навои"],
    "Наманган вилояти": ["Наманган"],
    "Самарқанд вилояти": ["Самарқанд", "Самарканд"],
    "Сирдарё вилояти": ["Сирдарё", "Сырдарья"],
    "Сурхондарё вилояти": ["Сурхондарё", "Сурхандарья"],
    "Тошкент шаҳри": [
        "Тошкент шаҳри",
        "Ташкент ш.",
        "г. Ташкент",
        "г.Ташкент",
        "город Ташкент",
    ],
    "Тошкент вилояти": ["Тошкент", "Ташкент"],
    "Фарғона вилояти": ["Фарғона", "Фергана"],
    "Хоразм вилояти": ["Хоразм", "Хорезм"],
    "Қашқадарё вилояти": ["Қашқадарё", "Кашкадарья"],
    "Қорақалпоғистон Республикаси": ["Қорақалпоғистон", "Каракалпакстан"],
}


def enrich_countries() -> None:
    iso_path = DATA_DIR / "countries_ru_iso.json"
    if not iso_path.exists():
        print(f"!  Файл не найден: {iso_path}")
        return
    with iso_path.open("r", encoding="utf-8") as f:
        mapping: dict[str, dict[str, str]] = json.load(f)

    Session = sessionmaker(bind=sync_engine)
    session = Session()
    try:
        countries = session.query(Country).all()
        matched = 0
        unmatched: list[str] = []
        for c in countries:
            key = c.name.strip().upper()
            entry = mapping.get(key)
            if not entry:
                unmatched.append(c.name)
                continue
            c.iso_code = entry["iso"]
            c.name_uz = entry["name_uz"]
            matched += 1
        session.commit()
        print(f"countries: matched={matched} / total={len(countries)}")
        if unmatched:
            print("Без ISO:")
            for name in unmatched:
                print(f"  - {name}")
    finally:
        session.close()


def enrich_regions() -> None:
    Session = sessionmaker(bind=sync_engine)
    session = Session()
    try:
        existing = {r.name: r.id for r in session.query(Region).all()}
        for label in REGION_ALIASES.keys():
            if label not in existing:
                session.add(Region(name=label))
        session.commit()
        existing = {r.name: r.id for r in session.query(Region).all()}

        # Bulk UPDATE по каждому алиасу — серверная работа без загрузки
        # строк gtk в Python. Сортировка по убыванию длины критична:
        # "Тошкент шаҳри" / "г. Ташкент" должны матчиться раньше
        # "Тошкент"/"Ташкент", иначе записи города попадут в область
        # (фильтр region_id IS NULL отсекает уже размеченные строки).
        pairs: list[tuple[str, str]] = [
            (alias, label)
            for label, aliases in REGION_ALIASES.items()
            for alias in aliases
        ]
        pairs.sort(key=lambda p: len(p[0]), reverse=True)

        stmt = text(
            "UPDATE gtk SET region_id = :rid "
            "WHERE region_id IS NULL "
            "AND address_uz IS NOT NULL "
            "AND address_uz ILIKE :pat"
        )
        per_label: dict[str, int] = {label: 0 for label in REGION_ALIASES}
        total = 0
        for alias, label in pairs:
            region_id = existing.get(label)
            if not region_id:
                continue
            res = session.execute(stmt, {"rid": region_id, "pat": f"%{alias}%"})
            session.commit()
            n = res.rowcount or 0
            per_label[label] += n
            total += n
            print(f"  [{alias}] -> {label}: {n}")
        print("---")
        for label, n in per_label.items():
            print(f"  {label}: {n}")
        print(f"regions: обновлено {total}")
    finally:
        session.close()


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd == "countries":
        enrich_countries()
    elif cmd == "regions":
        enrich_regions()
    elif cmd == "all":
        enrich_countries()
        enrich_regions()
    else:
        print(f"Неизвестная команда: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()
