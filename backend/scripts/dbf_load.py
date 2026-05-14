"""CLI: загрузка DBF-файла ГТД в базу данных.

Использование
-------------
    # Плоская таблица gtk_all (по умолчанию — рекомендуется для новых данных)
    python -m scripts.dbf_load <папка>
    python -m scripts.dbf_load --all <корень_папок>

    # Нормализованная таблица gtk (старый формат с FK)
    python -m scripts.dbf_load <папка> --target gtk

    # Обе таблицы сразу
    python -m scripts.dbf_load <папка> --target both

Примеры
-------
    python -m scripts.dbf_load ../to_import/01.12.2020
    python -m scripts.dbf_load --all ../to_import
    python -m scripts.dbf_load ../to_import/01.12.2020 --target both
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


# ── Общие утилиты ────────────────────────────────────────────────────────────


def _etl_func(target: str):
    """Вернуть нужную ETL-функцию по имени target."""
    from app.services.dbf_etl import load_dbf, load_dbf_flat
    return {"gtk": load_dbf, "gtk_all": load_dbf_flat}[target]


def _run_load(main_dbf: Path, slvs03: Path | None, target: str) -> dict:
    """Запустить загрузку, вернуть словарь с результатами."""
    from app.services.dbf_etl import load_dbf, load_dbf_flat

    if target == "both":
        r1 = load_dbf_flat(main_dbf, slvs03)
        r2 = load_dbf(main_dbf, slvs03)
        return {
            "rows_total": r1.rows_total,
            "added":      r1.added + r2.added,
            "dup":        r1.duplicates_skipped + r2.duplicates_skipped,
            "inv":        max(r1.invalid_skipped, r2.invalid_skipped),
            "ms":         r1.duration_ms + r2.duration_ms,
            "gtk_all_added": r1.added,
            "gtk_added":     r2.added,
        }

    fn = load_dbf_flat if target == "gtk_all" else load_dbf
    r  = fn(main_dbf, slvs03)
    return {
        "rows_total": r.rows_total,
        "added":      r.added,
        "dup":        r.duplicates_skipped,
        "inv":        r.invalid_skipped,
        "ms":         r.duration_ms,
    }


def _print_single(res: dict, target: str) -> None:
    mins = res["ms"] // 60_000
    secs = (res["ms"] % 60_000) / 1000
    print()
    print("═" * 52)
    print(f"  Целевая таблица     : {target}")
    print(f"  Всего строк в файле : {res['rows_total']:>10,}")
    if "gtk_all_added" in res:
        print(f"  Добавлено gtk_all   : {res['gtk_all_added']:>10,}")
        print(f"  Добавлено gtk       : {res['gtk_added']:>10,}")
    else:
        print(f"  Добавлено           : {res['added']:>10,}")
    print(f"  Дублей пропущено    : {res['dup']:>10,}")
    print(f"  Некорректных        : {res['inv']:>10,}")
    print(f"  Время               : {mins}м {secs:.1f}с")
    print("═" * 52)


def _print_totals(results: list[dict]) -> None:
    print()
    print("═" * 60)
    print(f"  Папок обработано    : {len(results):>6}")
    print(f"  Всего строк         : {sum(r['rows_total'] for r in results):>10,}")
    print(f"  Добавлено           : {sum(r['added']      for r in results):>10,}")
    print(f"  Дублей пропущено    : {sum(r['dup']        for r in results):>10,}")
    print(f"  Некорректных        : {sum(r['inv']        for r in results):>10,}")
    total_ms = sum(r["ms"] for r in results)
    mins = total_ms // 60_000
    secs = (total_ms % 60_000) / 1000
    print(f"  Общее время         : {mins}м {secs:.0f}с")
    print("═" * 60)


# ── Точка входа ──────────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Загрузить ГТД из DBF-файла(ов) в базу данных",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "folder",
        nargs="?",
        help="Папка с DBF-файлами одного периода",
    )
    parser.add_argument(
        "--all",
        dest="all_dir",
        default=None,
        metavar="PARENT",
        help="Папка с вложенными папками периодов — обработать все за раз",
    )
    parser.add_argument(
        "--target",
        choices=["gtk_all", "gtk", "both"],
        default="gtk_all",
        help="Целевая таблица: gtk_all (плоская, по умолч.), gtk (с FK), both (обе)",
    )
    parser.add_argument(
        "--main",
        dest="main_dbf",
        default=None,
        help="Точное имя главного DBF-файла (если авто-определение не сработало)",
    )
    parser.add_argument(
        "--slvs03",
        dest="slvs03",
        default=None,
        help="Путь к справочнику стран SLVS03*.DBF",
    )
    args = parser.parse_args()

    if not args.folder and not args.all_dir:
        parser.print_help()
        sys.exit(1)

    from app.services.dbf_etl import find_dbf_files

    # ── Один период ──────────────────────────────────────────────────────────
    if args.folder:
        folder = Path(args.folder)
        if not folder.is_dir():
            print(f"Ошибка: папка не найдена: {folder}", file=sys.stderr)
            sys.exit(1)

        main_dbf, slvs03 = find_dbf_files(folder)
        if args.main_dbf:
            main_dbf = folder / args.main_dbf
        if args.slvs03:
            slvs03 = Path(args.slvs03)

        if not main_dbf or not main_dbf.exists():
            print("Ошибка: главный DBF-файл не найден. Укажите --main", file=sys.stderr)
            sys.exit(1)

        print(f"Файл     : {main_dbf.name}  ({main_dbf.stat().st_size / 1024**2:.0f} MB)")
        print(f"Справочн.: {slvs03.name if slvs03 else 'не найден'}")
        print(f"Таблица  : {args.target}")
        print()

        res = _run_load(main_dbf, slvs03, args.target)
        _print_single(res, args.target)
        return

    # ── Все периоды ──────────────────────────────────────────────────────────
    parent = Path(args.all_dir)
    if not parent.is_dir():
        print(f"Ошибка: папка не найдена: {parent}", file=sys.stderr)
        sys.exit(1)

    folders = sorted(
        [d for d in parent.iterdir() if d.is_dir()],
        key=lambda d: d.name,
    )
    dbf_folders = [d for d in folders if find_dbf_files(d)[0] is not None]

    if not dbf_folders:
        print(f"DBF-файлы не найдены ни в одной подпапке {parent}", file=sys.stderr)
        sys.exit(1)

    print(f"Найдено папок с ГТД: {len(dbf_folders)}  |  таблица: {args.target}")
    for d in dbf_folders:
        print(f"  {d.name}")
    print()

    results: list[dict] = []
    errors:  list[str]  = []

    for i, folder in enumerate(dbf_folders, 1):
        print(f"[{i}/{len(dbf_folders)}] {folder.name}")
        main_dbf, slvs03 = find_dbf_files(folder)
        size_mb = main_dbf.stat().st_size / 1024 ** 2 if main_dbf else 0
        print(f"  Файл: {main_dbf.name if main_dbf else '?'} ({size_mb:.0f} MB)")
        try:
            res = _run_load(main_dbf, slvs03, args.target)
            mins = res["ms"] // 60_000
            secs = (res["ms"] % 60_000) / 1000
            print(f"  OK  добавлено {res['added']:,} / дублей {res['dup']:,} "
                  f"/ некорр. {res['inv']:,}  [{mins}м {secs:.0f}с]")
            results.append(res)
        except Exception as exc:
            print(f"  ОШИБКА: {exc}", file=sys.stderr)
            errors.append(f"{folder.name}: {exc}")

    _print_totals(results)
    if errors:
        print(f"\nПапки с ошибками ({len(errors)}):")
        for e in errors:
            print(f"  {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
