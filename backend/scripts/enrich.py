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
import re
import sys
from pathlib import Path

from sqlalchemy.orm import sessionmaker

from app.database import sync_engine
from app.models import GTK, Country, Region

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

REGIONS = [
    "Андижон", "Бухоро", "Жиззах", "Навоий", "Наманган", "Самарқанд",
    "Сирдарё", "Сурхондарё", "Тошкент шаҳри", "Тошкент",
    "Фарғона", "Хоразм", "Қашқадарё", "Қорақалпоғистон",
]
REGION_LABELS = {
    "Андижон": "Андижон вилояти",
    "Бухоро": "Бухоро вилояти",
    "Жиззах": "Жиззах вилояти",
    "Навоий": "Навоий вилояти",
    "Наманган": "Наманган вилояти",
    "Самарқанд": "Самарқанд вилояти",
    "Сирдарё": "Сирдарё вилояти",
    "Сурхондарё": "Сурхондарё вилояти",
    "Тошкент шаҳри": "Тошкент шаҳри",
    "Тошкент": "Тошкент вилояти",
    "Фарғона": "Фарғона вилояти",
    "Хоразм": "Хоразм вилояти",
    "Қашқадарё": "Қашқадарё вилояти",
    "Қорақалпоғистон": "Қорақалпоғистон Республикаси",
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
        for label in REGION_LABELS.values():
            if label not in existing:
                session.add(Region(name=label))
        session.commit()
        existing = {r.name: r.id for r in session.query(Region).all()}

        # Для скорости составим один большой regex
        pattern = re.compile(
            "|".join(re.escape(k) for k in REGIONS),
            re.IGNORECASE,
        )

        records = (
            session.query(GTK)
            .filter(GTK.region_id.is_(None), GTK.address_uz.isnot(None))
            .all()
        )
        updated = 0
        for r in records:
            m = pattern.search(r.address_uz or "")
            if not m:
                continue
            key = m.group(0)
            for canonical in REGIONS:
                if canonical.lower() == key.lower():
                    label = REGION_LABELS[canonical]
                    region_id = existing.get(label)
                    if region_id:
                        r.region_id = region_id
                        updated += 1
                    break
            if updated and updated % 500 == 0:
                session.commit()
        session.commit()
        print(f"regions: обновлено {updated} / просмотрено {len(records)}")
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
