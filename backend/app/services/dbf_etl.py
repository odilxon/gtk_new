"""
ETL: ГТД (customs declaration) DBF files → PostgreSQL.

Encoding
--------
Main DBF (База *.dbf)   : cp1251 (Windows-1251)  — подтверждено: G1A=0xC8,0xCC → "ИМ"
Lookup DBFs (SLVS03/11) : cp866

Field mapping  DBF → gtk
------------------------
G1A            → regime           "ИМ" / "ЭК" (после decode cp1251)
G7B            → date             Date-поле, YYYYMMDD
G7A + "/" + G7C→ declaration_number
G15            → country_id       числовой код → SLVS03 → name/iso2
G33            → product_id       ТНВЭД 10-зн.; category = "Глава XX" (HS-глава)
G8CODE2        → company_uzb      STIR (ИНН)
G8NAME         → companies_uzb.name
G2NAME         → company_foreign
P1             → unit             краткое наименование ед.изм.: "кг", "шт" (уже в тексте)
G38            → weight           нетто, кг
G35            → gross_weight     брутто, кг
G45USD         → price_thousand   CIF-стоимость в ФАКТИЧЕСКИХ долларах США
               (fallback: G22B если G22A=="840", т.е. контракт в USD)
G22A (числ.)   → currency_code    ISO-4217 numeric → alpha-3: "840"→"USD"
G22B           → currency_amount  сумма в валюте контракта
G23            → exchange_rate    UZS за 1 ед. валюты на дату ГТД
G20B           → incoterms        "CIP", "FOB", "EXW"…
G20NAME        → incoterms_place  место поставки
G32            → packages_count
PAYMFACT20     → customs_duty     уплаченная пошлина, UZS
PAYMFACT29     → vat_amount       уплаченный НДС, UZS

Ценовая логика
--------------
price_thousand хранит ФАКТИЧЕСКИЕ доллары (не тысячи) — так же, как у Excel ETL.
G45USD = статистическая (CIF) стоимость, уже в USD → присваивается напрямую.
Умножать на 1000 НЕ нужно (в отличие от Excel-колонки "Цена(тыс)").
Fallback: G22B используется только когда G45USD==0 и G22A=="840" (USD-контракт).
"""
from __future__ import annotations

import hashlib
import struct
import time
from datetime import date as _date
from pathlib import Path
from typing import Any, Generator

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
    Regime,
)
from app.services.gtk_etl import BATCH_SIZE, EtlResult, compute_row_hash

# ── Константы ───────────────────────────────────────────────────────────────

MAIN_ENC   = "cp1251"   # кодировка основного DBF
LOOKUP_ENC = "cp866"    # кодировка справочных DBF (SLVS03, SLVS11)

# ISO 4217 numeric → alpha-3 (наиболее встречаемые в торговле УзБ)
_ISO4217: dict[str, str] = {
    "840": "USD", "978": "EUR", "643": "RUB", "826": "GBP",
    "392": "JPY", "156": "CNY", "756": "CHF", "124": "CAD",
    "036": "AUD", "410": "KRW", "792": "TRY", "356": "INR",
    "784": "AED", "682": "SAR", "398": "KZT", "051": "AMD",
    "944": "AZN", "981": "GEL", "417": "KGS", "762": "TJS",
    "795": "TMT", "860": "UZS",
}


# ── Низкоуровневый DBF-читатель ─────────────────────────────────────────────


def _iter_dbf(path: Path, encoding: str) -> Generator[dict[str, Any], None, None]:
    """Генератор: один dict на каждую живую (не удалённую) запись DBF."""
    with open(path, "rb") as f:
        hdr      = f.read(32)
        n_rec    = struct.unpack("<I", hdr[4:8])[0]
        hdr_size = struct.unpack("<H", hdr[8:10])[0]
        rec_size = struct.unpack("<H", hdr[10:12])[0]

        fields: list[tuple[str, str, int]] = []
        while True:
            fd = f.read(32)
            if not fd or fd[0] == 0x0D:
                break
            name  = fd[0:11].split(b"\x00")[0].decode("ascii", errors="replace")
            ftype = chr(fd[11])
            flen  = fd[16]
            fields.append((name, ftype, flen))

        f.seek(hdr_size)
        for _ in range(n_rec):
            rec = f.read(rec_size)
            if not rec or rec[0] == 0x1A:   # EOF-маркер
                break
            if rec[0] == 0x2A:              # удалённая запись
                continue
            row: dict[str, Any] = {}
            off = 1
            for name, ftype, flen in fields:
                raw = rec[off : off + flen]
                if ftype == "C":
                    row[name] = raw.decode(encoding, errors="replace").strip() or None
                elif ftype == "D":
                    s = raw.decode("ascii").strip()
                    row[name] = s if len(s) == 8 else None
                elif ftype == "N":
                    s = raw.decode("ascii").strip()
                    try:
                        row[name] = float(s) if s else None
                    except ValueError:
                        row[name] = None
                elif ftype == "L":
                    row[name] = raw[0:1] in (b"T", b"t", b"Y", b"y")
                else:
                    row[name] = None
                off += flen
            yield row


# ── Справочники ─────────────────────────────────────────────────────────────


def _norm_code(raw: str | None) -> str:
    """'36' / '036' / '156' → нормализованный 3-значный строковый код."""
    if not raw:
        return ""
    try:
        return str(int(raw)).zfill(3)
    except ValueError:
        return ""


def load_country_lookup(
    slvs03_path: Path,
) -> dict[str, tuple[str, str | None]]:
    """Возвращает {norm_3digit_code: (name_ru, iso2_or_None)}.

    Если файл содержит поле KOD1 (вариант со знаком `), ISO-2 код заполнится.
    """
    result: dict[str, tuple[str, str | None]] = {}
    for row in _iter_dbf(slvs03_path, LOOKUP_ENC):
        code = _norm_code(row.get("P2"))
        name = (row.get("P1") or "").strip()
        iso2 = (row.get("KOD1") or "").strip() or None
        if code and name:
            result[code] = (name, iso2)
    return result


# ── Вспомогательные функции разбора полей ──────────────────────────────────


def _parse_date(g7b: str | None) -> _date | None:
    if not g7b or len(g7b) != 8:
        return None
    try:
        return _date(int(g7b[:4]), int(g7b[4:6]), int(g7b[6:8]))
    except ValueError:
        return None


def _resolve_price(row: dict[str, Any]) -> float | None:
    """Фактическая стоимость в USD для поля price_thousand.

    Приоритет:
    1. G45USD — CIF-стоимость, уже в USD.
    2. G22B   — только если валюта контракта USD (G22A == "840").
    """
    g45 = row.get("G45USD")
    if g45 and g45 > 0:
        return float(g45)
    if (row.get("G22A") or "").strip() == "840":
        g22b = row.get("G22B")
        if g22b and g22b > 0:
            return float(g22b)
    return None


def _currency_alpha(g22a: str | None) -> str | None:
    if not g22a:
        return None
    code = g22a.strip()
    return _ISO4217.get(code) or _ISO4217.get(code.zfill(3))


# ── Flush helpers ────────────────────────────────────────────────────────────


def _flush_countries(
    session: Session,
    new_countries: dict[str, tuple[str, str | None]],  # norm_code → (name, iso2)
    countries_by_name: dict[str, int],
    countries_by_code: dict[str, int],
) -> None:
    new_names = {
        name for _, (name, _) in new_countries.items()
        if name not in countries_by_name
    }
    if new_names:
        session.execute(
            pg_insert(Country.__table__).on_conflict_do_nothing(
                index_elements=["name"]
            ),
            [
                {"name": name, "iso_code": iso2}
                for norm, (name, iso2) in new_countries.items()
                if name in new_names
            ],
        )
        session.commit()
        from sqlalchemy import text
        rows = session.execute(
            text("SELECT id, name FROM countries WHERE name = ANY(:names)"),
            {"names": list(new_names)},
        ).all()
        for r in rows:
            countries_by_name[r.name] = r.id

    for norm_code, (name, _) in new_countries.items():
        cid = countries_by_name.get(name)
        if cid:
            countries_by_code[norm_code] = cid
    new_countries.clear()


def _flush_categories(
    session: Session,
    new_categories: dict[str, None],
    categories_by_name: dict[str, int],
) -> None:
    new_names = [n for n in new_categories if n not in categories_by_name]
    if new_names:
        session.execute(
            pg_insert(Category.__table__).on_conflict_do_nothing(
                index_elements=["name"]
            ),
            [{"name": n} for n in new_names],
        )
        session.commit()
        from sqlalchemy import text
        rows = session.execute(
            text("SELECT id, name FROM categories WHERE name = ANY(:names)"),
            {"names": new_names},
        ).all()
        for r in rows:
            categories_by_name[r.name] = r.id
    new_categories.clear()


def _flush_products(
    session: Session,
    new_products: dict[str, str],  # tnved → cat_name
    products_by_tnved: dict[str, int],
    categories_by_name: dict[str, int],
) -> None:
    to_insert = []
    for tnved, cat_name in new_products.items():
        if tnved in products_by_tnved:
            continue
        cat_id = categories_by_name.get(cat_name)
        if not cat_id:
            continue
        to_insert.append({"category_id": cat_id, "name": tnved, "tnved": tnved})

    if to_insert:
        session.execute(
            pg_insert(Product.__table__).on_conflict_do_nothing(),
            to_insert,
        )
        session.commit()
        from sqlalchemy import text
        tnveds = list(new_products.keys())
        rows = session.execute(
            text("SELECT id, tnved FROM products WHERE tnved = ANY(:tnveds)"),
            {"tnveds": tnveds},
        ).all()
        for r in rows:
            products_by_tnved[r.tnved] = r.id
    new_products.clear()


def _flush_uzb(
    session: Session,
    new_uzb: dict[str, str],  # stir → name
    uzb_by_stir: dict[str, int],
) -> None:
    to_insert = [
        {"stir": stir, "name": name}
        for stir, name in new_uzb.items()
        if stir not in uzb_by_stir
    ]
    if to_insert:
        session.execute(
            pg_insert(CompanyUzb.__table__).on_conflict_do_nothing(),
            to_insert,
        )
        session.commit()
        from sqlalchemy import text
        stirs = list(new_uzb.keys())
        rows = session.execute(
            text("SELECT id, stir FROM companies_uzb WHERE stir = ANY(:stirs)"),
            {"stirs": stirs},
        ).all()
        for r in rows:
            uzb_by_stir[r.stir] = r.id
    new_uzb.clear()


def _flush_foreign(
    session: Session,
    new_foreign: set[str],
    foreign_by_name: dict[str, int],
) -> None:
    to_insert = [
        {"name": name}
        for name in new_foreign
        if name not in foreign_by_name
    ]
    if to_insert:
        session.execute(
            pg_insert(CompanyForeign.__table__).on_conflict_do_nothing(),
            to_insert,
        )
        session.commit()
        from sqlalchemy import text
        names = list(new_foreign)
        rows = session.execute(
            text("SELECT id, name FROM companies_foreign WHERE name = ANY(:names)"),
            {"names": names},
        ).all()
        for r in rows:
            foreign_by_name[r.name] = r.id
    new_foreign.clear()


def _flush_all_lookups(
    session: Session,
    new_countries:  dict[str, tuple[str, str | None]],
    new_categories: dict[str, None],
    new_products:   dict[str, str],
    new_uzb:        dict[str, str],
    new_foreign:    set[str],
    countries_by_name: dict[str, int],
    countries_by_code: dict[str, int],
    categories_by_name: dict[str, int],
    products_by_tnved:  dict[str, int],
    uzb_by_stir:        dict[str, int],
    foreign_by_name:    dict[str, int],
) -> None:
    _flush_countries(session, new_countries, countries_by_name, countries_by_code)
    _flush_categories(session, new_categories, categories_by_name)
    _flush_products(session, new_products, products_by_tnved, categories_by_name)
    _flush_uzb(session, new_uzb, uzb_by_stir)
    _flush_foreign(session, new_foreign, foreign_by_name)


def _flush_gtk_batch(
    session: Session,
    batch: list[dict],
    countries_by_code: dict[str, int],
    products_by_tnved: dict[str, int],
    uzb_by_stir:       dict[str, int],
    foreign_by_name:   dict[str, int],
) -> tuple[int, int, int]:
    """Возвращает (added, duplicates_skipped, invalid_skipped)."""
    seen_hashes: set[str] = set()
    insert_rows: list[dict] = []
    invalid = 0

    for item in batch:
        country_id = countries_by_code.get(item["_country_code"])
        product_id = products_by_tnved.get(item["_tnved"])
        if not country_id or not product_id:
            invalid += 1
            continue

        uzb_id     = uzb_by_stir.get(item["_stir"])     if item["_stir"]      else None
        foreign_id = foreign_by_name.get(item["_foreign"])if item["_foreign"]  else None

        h = compute_row_hash(
            date=item["date"],
            regime=item["regime"],
            country_id=country_id,
            product_id=product_id,
            company_uzb_id=uzb_id,
            company_foreign_id=foreign_id,
            address_uz=None,
            address_foreign=None,
            unit=item["unit"],
            weight=item["weight"],
            quantity=item["quantity"],
            price_thousand=item["price_thousand"],
        )
        if h in seen_hashes:
            continue
        seen_hashes.add(h)

        insert_rows.append({
            "regime":             item["regime"],
            "country_id":         country_id,
            "address_uz":         None,
            "address_foreign":    None,
            "region_id":          None,
            "company_uzb_id":     uzb_id,
            "company_foreign_id": foreign_id,
            "product_id":         product_id,
            "unit":               item["unit"],
            "weight":             item["weight"],
            "quantity":           item["quantity"],
            "price_thousand":     item["price_thousand"],
            "date":               item["date"],
            "dedup_hash":         h,
            # DBF-only поля
            "declaration_number": item["declaration_number"],
            "incoterms":          item["incoterms"],
            "incoterms_place":    item["incoterms_place"],
            "currency_code":      item["currency_code"],
            "currency_amount":    item["currency_amount"],
            "exchange_rate":      item["exchange_rate"],
            "gross_weight":       item["gross_weight"],
            "packages_count":     item["packages_count"],
            "customs_duty":       item["customs_duty"],
            "vat_amount":         item["vat_amount"],
        })

    if not insert_rows:
        return 0, 0, invalid

    stmt = pg_insert(GTK.__table__).values(insert_rows)
    stmt = stmt.on_conflict_do_nothing(index_elements=["dedup_hash"])
    result = session.execute(stmt)
    session.commit()

    inserted  = result.rowcount or 0
    db_dups   = len(insert_rows) - inserted
    intra_dup = len(batch) - invalid - len(insert_rows)
    return inserted, intra_dup + db_dups, invalid


# ── Основная функция загрузки ────────────────────────────────────────────────


def load_dbf(
    dbf_path: str | Path,
    slvs03_path: str | Path | None = None,
    *,
    engine: Engine | None = None,
) -> EtlResult:
    """Загрузить DBF-файл ГТД в БД с дедупликацией.

    dbf_path    : путь к главному файлу данных (База *.dbf).
    slvs03_path : справочник стран SLVS03*.DBF. Без него код страны G15
                  используется как имя страны (всё равно работает).
    """
    started  = time.monotonic()
    dbf_path = Path(dbf_path)

    # ── 1. Загрузить справочник стран ────────────────────────────────────────
    country_lookup: dict[str, tuple[str, str | None]] = {}
    if slvs03_path:
        country_lookup = load_country_lookup(Path(slvs03_path))

    # ── 2. Подключение и предзагрузка кэшей из БД ────────────────────────────
    MakeSession = sessionmaker(bind=engine or sync_engine)
    session: Session = MakeSession()

    try:
        countries_by_name: dict[str, int] = {
            c.name: c.id for c in session.query(Country).all()
        }
        countries_by_code: dict[str, int] = {}
        # Заполнить code → id по уже существующим странам через lookup
        for norm_code, (name, _) in country_lookup.items():
            cid = countries_by_name.get(name)
            if cid:
                countries_by_code[norm_code] = cid

        categories_by_name: dict[str, int] = {
            c.name: c.id for c in session.query(Category).all()
        }
        products_by_tnved: dict[str, int] = {
            p.tnved: p.id for p in session.query(Product).all()
        }
        uzb_by_stir: dict[str, int] = {
            c.stir: c.id for c in session.query(CompanyUzb).all()
        }
        foreign_by_name: dict[str, int] = {
            c.name: c.id for c in session.query(CompanyForeign).all()
        }

        # Отложенные новые справочные записи (сбрасываются перед каждым батчем)
        new_countries:  dict[str, tuple[str, str | None]] = {}
        new_categories: dict[str, None] = {}
        new_products:   dict[str, str]  = {}  # tnved → cat_name
        new_uzb:        dict[str, str]  = {}  # stir → name
        new_foreign:    set[str]        = set()

        gtk_batch: list[dict] = []
        rows_total = added = duplicates = invalid = 0

        # ── 3. Стриминг главного DBF ─────────────────────────────────────────
        for raw in _iter_dbf(dbf_path, MAIN_ENC):
            rows_total += 1

            # — режим (ИМ / ЭК) ────────────────────────────────────────────
            g1a = (raw.get("G1A") or "").strip()
            try:
                regime = Regime[g1a]
            except KeyError:
                invalid += 1
                continue

            # — дата ───────────────────────────────────────────────────────
            d = _parse_date(raw.get("G7B"))
            if d is None:
                invalid += 1
                continue

            # — страна ─────────────────────────────────────────────────────
            g15_norm = _norm_code(raw.get("G15"))
            if not g15_norm:
                invalid += 1
                continue

            if g15_norm not in countries_by_code:
                if g15_norm in country_lookup:
                    name, iso2 = country_lookup[g15_norm]
                else:
                    name, iso2 = g15_norm, None
                if not name:
                    invalid += 1
                    continue
                if name not in countries_by_name:
                    new_countries[g15_norm] = (name, iso2)

            # — ТНВЭД / товар ──────────────────────────────────────────────
            tnved = (raw.get("G33") or "").strip().lstrip("0") or ""
            if not tnved:
                invalid += 1
                continue
            tnved = tnved.zfill(10)  # нормализуем к 10-знакам

            chapter  = tnved[:2]
            cat_name = f"Глава {chapter}"

            if tnved not in products_by_tnved and tnved not in new_products:
                if cat_name not in categories_by_name:
                    new_categories[cat_name] = None
                new_products[tnved] = cat_name

            # — компания УзБ ───────────────────────────────────────────────
            stir     = (raw.get("G8CODE2") or "").strip() or None
            uzb_name = (raw.get("G8NAME")  or "").strip() or None
            if stir and stir not in uzb_by_stir and stir not in new_uzb and uzb_name:
                new_uzb[stir] = uzb_name

            # — иностранная компания ───────────────────────────────────────
            foreign = (raw.get("G2NAME") or "").strip() or None
            if foreign and foreign not in foreign_by_name:
                new_foreign.add(foreign)

            # — числовые поля ──────────────────────────────────────────────
            unit      = (raw.get("P1") or "").strip() or None
            weight    = raw.get("G38")              # нетто
            gross_wt  = raw.get("G35")              # брутто
            quantity  = raw.get("ZA_ED")
            price_usd = _resolve_price(raw)

            g22a_raw  = (raw.get("G22A") or "").strip()
            cur_code  = _currency_alpha(g22a_raw)
            cur_amt   = raw.get("G22B")
            ex_rate   = raw.get("G23")

            g7a  = (raw.get("G7A") or "").strip()
            g7c  = (raw.get("G7C") or "").strip()
            decl = f"{g7a}/{g7c}" if g7a and g7c else None

            incoterms = (raw.get("G20B")    or "").strip() or None
            inc_place = (raw.get("G20NAME") or "").strip() or None

            g32 = raw.get("G32")
            pkgs = int(g32) if g32 is not None else None

            duty = raw.get("PAYMFACT20")
            vat  = raw.get("PAYMFACT29")

            gtk_batch.append({
                "_country_code": g15_norm,
                "_tnved":        tnved,
                "_stir":         stir,
                "_foreign":      foreign,
                # scalar GTK fields
                "regime":         regime,
                "date":           d,
                "unit":           unit,
                "weight":         float(weight)   if weight   is not None else None,
                "quantity":       float(quantity) if quantity is not None else None,
                "price_thousand": price_usd,
                # DBF-specific fields
                "declaration_number": decl,
                "incoterms":          incoterms,
                "incoterms_place":    inc_place,
                "currency_code":      cur_code,
                "currency_amount":    float(cur_amt)  if cur_amt  is not None else None,
                "exchange_rate":      float(ex_rate)  if ex_rate  is not None else None,
                "gross_weight":       float(gross_wt) if gross_wt is not None else None,
                "packages_count":     pkgs,
                "customs_duty":       float(duty) if duty is not None else None,
                "vat_amount":         float(vat)  if vat  is not None else None,
            })

            if len(gtk_batch) >= BATCH_SIZE:
                _flush_all_lookups(
                    session,
                    new_countries, new_categories, new_products,
                    new_uzb, new_foreign,
                    countries_by_name, countries_by_code,
                    categories_by_name, products_by_tnved,
                    uzb_by_stir, foreign_by_name,
                )
                ins, dup, inv = _flush_gtk_batch(
                    session, gtk_batch,
                    countries_by_code, products_by_tnved,
                    uzb_by_stir, foreign_by_name,
                )
                added      += ins
                duplicates += dup
                invalid    += inv
                gtk_batch.clear()
                _print_progress(rows_total, added, duplicates, invalid)

        # — финальный батч ─────────────────────────────────────────────────
        if gtk_batch:
            _flush_all_lookups(
                session,
                new_countries, new_categories, new_products,
                new_uzb, new_foreign,
                countries_by_name, countries_by_code,
                categories_by_name, products_by_tnved,
                uzb_by_stir, foreign_by_name,
            )
            ins, dup, inv = _flush_gtk_batch(
                session, gtk_batch,
                countries_by_code, products_by_tnved,
                uzb_by_stir, foreign_by_name,
            )
            added      += ins
            duplicates += dup
            invalid    += inv

    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

    return EtlResult(
        rows_total=rows_total,
        added=added,
        duplicates_skipped=duplicates,
        invalid_skipped=invalid,
        countries=len(countries_by_name),
        regions=0,
        categories=len(categories_by_name),
        products=len(products_by_tnved),
        companies_uzb=len(uzb_by_stir),
        companies_foreign=len(foreign_by_name),
        duration_ms=int((time.monotonic() - started) * 1000),
    )


def _print_progress(total: int, added: int, dups: int, inv: int) -> None:
    print(
        f"  processed {total:>8,}  |  added {added:>7,}  "
        f"dup {dups:>6,}  invalid {inv:>5,}",
        flush=True,
    )


# ── Авто-определение файлов в папке ─────────────────────────────────────────


def find_dbf_files(
    folder: str | Path,
) -> tuple[Path | None, Path | None]:
    """Вернуть (main_dbf_path, slvs03_path) из папки с DBF-файлами.

    Главный файл = самый большой .dbf в папке.
    SLVS03: предпочитает вариант со знаком ` (есть KOD1/KOD2), иначе SLVS03.DBF.
    """
    folder = Path(folder)
    dbfs = [p for p in folder.iterdir() if p.suffix.lower() == ".dbf"]
    if not dbfs:
        return None, None

    main_dbf = max(dbfs, key=lambda p: p.stat().st_size)

    slvs03: Path | None = None
    for candidate in ["SLVS03`.DBF", "SLVS03.DBF", "slvs03.dbf"]:
        p = folder / candidate
        if p.exists():
            slvs03 = p
            break

    return main_dbf, slvs03


# ── Плоский ETL: DBF → gtk_all (без FK) ────────────────────────────────────


def _flat_hash(
    declaration_number: str | None,
    tnved: str | None,
    date: _date | None,
    regime: str | None,
    currency_amount: float | None,
    currency_code: str | None,
    weight: float | None,
) -> str:
    """SHA-256 для строки gtk_all. Идентифицирует одну линию декларации."""
    def _f(v: float | None) -> str:
        return f"{v:.6f}" if v is not None else ""

    parts = [
        declaration_number or "",
        tnved or "",
        date.isoformat() if date else "",
        regime or "",
        currency_code or "",
        _f(currency_amount),
        _f(weight),
    ]
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()


def load_dbf_flat(
    dbf_path: str | Path,
    slvs03_path: str | Path | None = None,
    *,
    engine: Engine | None = None,
) -> EtlResult:
    """Загрузить DBF-файл в плоскую таблицу gtk_all без внешних ключей.

    Все значения пишутся как есть — коды стран, ТНВЭД, названия компаний.
    Если slvs03_path задан — страна обогащается именем и ISO-кодом.
    Таблица gtk и все нормализованные справочники не трогаются.
    """
    from app.models import GTKAll  # избегаем циклического импорта на верхнем уровне

    started   = time.monotonic()
    dbf_path  = Path(dbf_path)
    source    = dbf_path.name

    country_lookup: dict[str, tuple[str, str | None]] = {}
    if slvs03_path:
        country_lookup = load_country_lookup(Path(slvs03_path))

    MakeSession = sessionmaker(bind=engine or sync_engine)
    session: Session = MakeSession()

    try:
        batch:     list[dict] = []
        rows_total = added = duplicates = invalid = 0
        seen_in_batch: set[str] = set()

        for raw in _iter_dbf(dbf_path, MAIN_ENC):
            rows_total += 1

            # ── Режим ────────────────────────────────────────────────────
            regime = (raw.get("G1A") or "").strip()
            if regime not in ("ИМ", "ЭК"):
                invalid += 1
                continue

            # ── Дата ─────────────────────────────────────────────────────
            d = _parse_date(raw.get("G7B"))
            if d is None:
                invalid += 1
                continue

            # ── Страна ───────────────────────────────────────────────────
            country_code = _norm_code(raw.get("G15"))
            if country_code in country_lookup:
                country_name, country_iso2 = country_lookup[country_code]
            else:
                country_name, country_iso2 = None, None

            # ── ТНВЭД ────────────────────────────────────────────────────
            tnved_raw = (raw.get("G33") or "").strip()
            tnved = tnved_raw.lstrip("0").zfill(10) if tnved_raw else None

            # ── Описание товара (обрезаем до 1000 символов) ───────────────
            desc_raw = raw.get("G31NAME") or ""
            product_description = desc_raw[:1000] or None

            # ── Компании ─────────────────────────────────────────────────
            company_uzb_name     = raw.get("G8NAME")
            company_uzb_stir     = (raw.get("G8CODE2") or "").strip() or None
            company_foreign_name = raw.get("G2NAME")

            # ── Измерения ─────────────────────────────────────────────────
            unit      = (raw.get("P1") or "").strip() or None
            weight    = raw.get("G38")
            gross_wt  = raw.get("G35")
            quantity  = raw.get("ZA_ED")
            g32       = raw.get("G32")
            packages  = int(g32) if g32 is not None else None

            # ── Цена ─────────────────────────────────────────────────────
            price_usd = _resolve_price(raw)
            g22a      = (raw.get("G22A") or "").strip()
            cur_code  = _currency_alpha(g22a)
            cur_amt   = raw.get("G22B")
            ex_rate   = raw.get("G23")

            # ── Поставка ──────────────────────────────────────────────────
            g7a  = (raw.get("G7A") or "").strip()
            g7c  = (raw.get("G7C") or "").strip()
            decl = f"{g7a}/{g7c}" if g7a and g7c else None

            incoterms = (raw.get("G20B")    or "").strip() or None
            inc_place = (raw.get("G20NAME") or "").strip() or None

            duty = raw.get("PAYMFACT20")
            vat  = raw.get("PAYMFACT29")

            # ── Хеш ──────────────────────────────────────────────────────
            h = _flat_hash(
                declaration_number=decl,
                tnved=tnved,
                date=d,
                regime=regime,
                currency_amount=float(cur_amt) if cur_amt is not None else None,
                currency_code=cur_code,
                weight=float(weight) if weight is not None else None,
            )

            if h in seen_in_batch:
                duplicates += 1
                continue
            seen_in_batch.add(h)

            batch.append({
                "regime":              regime,
                "date":                d,
                "declaration_number":  decl,
                "country_code":        country_code or None,
                "country_name":        country_name,
                "country_iso2":        country_iso2,
                "tnved":               tnved,
                "product_description": product_description,
                "company_uzb_name":    company_uzb_name,
                "company_uzb_stir":    company_uzb_stir,
                "company_foreign_name":company_foreign_name,
                "unit":                unit,
                "weight":              float(weight)   if weight   is not None else None,
                "gross_weight":        float(gross_wt) if gross_wt is not None else None,
                "quantity":            float(quantity) if quantity is not None else None,
                "packages_count":      packages,
                "price_usd":           price_usd,
                "currency_code":       cur_code,
                "currency_amount":     float(cur_amt)  if cur_amt  is not None else None,
                "exchange_rate":       float(ex_rate)  if ex_rate  is not None else None,
                "incoterms":           incoterms,
                "incoterms_place":     inc_place,
                "customs_duty":        float(duty) if duty is not None else None,
                "vat_amount":          float(vat)  if vat  is not None else None,
                "source_file":         source,
                "dedup_hash":          h,
            })

            if len(batch) >= BATCH_SIZE:
                ins, dup = _flush_flat_batch(session, batch, GTKAll)
                added      += ins
                duplicates += dup
                batch.clear()
                seen_in_batch.clear()
                _print_progress(rows_total, added, duplicates, invalid)

        if batch:
            ins, dup = _flush_flat_batch(session, batch, GTKAll)
            added      += ins
            duplicates += dup

    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

    return EtlResult(
        rows_total=rows_total,
        added=added,
        duplicates_skipped=duplicates,
        invalid_skipped=invalid,
        countries=0,
        regions=0,
        categories=0,
        products=0,
        companies_uzb=0,
        companies_foreign=0,
        duration_ms=int((time.monotonic() - started) * 1000),
    )


def _flush_flat_batch(
    session: Session,
    batch: list[dict],
    model: type,
) -> tuple[int, int]:
    """Bulk insert батча в плоскую таблицу. Возвращает (inserted, db_dups)."""
    stmt = pg_insert(model.__table__).values(batch)
    stmt = stmt.on_conflict_do_nothing(index_elements=["dedup_hash"])
    result = session.execute(stmt)
    session.commit()
    inserted = result.rowcount or 0
    return inserted, len(batch) - inserted
