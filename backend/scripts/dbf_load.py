"""CLI: загрузка DBF-файла ГТД в базу данных.

Использование
-------------
    python -m scripts.dbf_load <папка_с_dbf>
    python -m scripts.dbf_load <папка_с_dbf> --slvs03 <путь_к_SLVS03.DBF>

Примеры
-------
    python -m scripts.dbf_load ../to_import/01.12.2020
    python -m scripts.dbf_load ../to_import/01.12.2020 --main "База 11.dbf"
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _load_one(folder: Path, main_override: str | None, slvs03_override: str | None) -> int:
    """Загрузить одну папку. Возвращает код выхода (0 = OK)."""
    from app.services.dbf_etl import find_dbf_files, load_dbf

    main_dbf, slvs03 = find_dbf_files(folder)
    if main_override:
        main_dbf = folder / main_override
    if slvs03_override:
        slvs03 = Path(slvs03_override)

    if not main_dbf or not main_dbf.exists():
        print(f"  Ошибка: DBF-файл не найден в {folder}. Пропускаем.", file=sys.stderr)
        return 1

    size_mb = main_dbf.stat().st_size / 1024 ** 2
    print(f"  Файл     : {main_dbf.name}  ({size_mb:.0f} MB)")
    print(f"  Справочн.: {slvs03.name if slvs03 else 'не найден'}")

    result = load_dbf(main_dbf, slvs03)

    mins = result.duration_ms // 60_000
    secs = (result.duration_ms % 60_000) / 1000
    print(f"  Добавлено {result.added:,} / дублей {result.duplicates_skipped:,} "
          f"/ некорр. {result.invalid_skipped:,}  [{mins}м {secs:.0f}с]")
    return 0


def _print_final(result_list: list[dict]) -> None:
    print()
    print("═" * 60)
    total_rows = sum(r["rows_total"] for r in result_list)
    total_add  = sum(r["added"]      for r in result_list)
    total_dup  = sum(r["dup"]        for r in result_list)
    total_inv  = sum(r["inv"]        for r in result_list)
    total_ms   = sum(r["ms"]         for r in result_list)
    mins = total_ms // 60_000
    secs = (total_ms % 60_000) / 1000
    print(f"  Папок обработано    : {len(result_list):>6}")
    print(f"  Всего строк         : {total_rows:>10,}")
    print(f"  Добавлено           : {total_add:>10,}")
    print(f"  Дублей пропущено    : {total_dup:>10,}")
    print(f"  Некорректных        : {total_inv:>10,}")
    print(f"  Общее время         : {mins}м {secs:.0f}с")
    print("═" * 60)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Загрузить ГТД из DBF-файла(ов) в базу данных"
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

    from app.services.dbf_etl import find_dbf_files, load_dbf

    # ── Режим одной папки ────────────────────────────────────────────────────
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

        print(f"Главный файл : {main_dbf.name}  ({main_dbf.stat().st_size / 1024**2:.0f} MB)")
        print(f"Справочник   : {slvs03.name if slvs03 else 'не найден'}")
        print()

        result = load_dbf(main_dbf, slvs03)

        mins = result.duration_ms // 60_000
        secs = (result.duration_ms % 60_000) / 1000
        print()
        print("═" * 50)
        print(f"  Всего строк в файле : {result.rows_total:>10,}")
        print(f"  Добавлено           : {result.added:>10,}")
        print(f"  Дублей пропущено    : {result.duplicates_skipped:>10,}")
        print(f"  Некорректных        : {result.invalid_skipped:>10,}")
        print(f"  Стран               : {result.countries:>10,}")
        print(f"  Категорий           : {result.categories:>10,}")
        print(f"  Товаров (ТНВЭД)     : {result.products:>10,}")
        print(f"  Компаний УзБ        : {result.companies_uzb:>10,}")
        print(f"  Компаний иностр.    : {result.companies_foreign:>10,}")
        print(f"  Время               : {mins}м {secs:.1f}с")
        print("═" * 50)
        return

    # ── Режим всех папок ────────────────────────────────────────────────────
    parent = Path(args.all_dir)
    if not parent.is_dir():
        print(f"Ошибка: папка не найдена: {parent}", file=sys.stderr)
        sys.exit(1)

    # Собрать все вложенные папки, содержащие DBF-файлы, отсортировать по имени
    folders = sorted(
        [d for d in parent.iterdir() if d.is_dir()],
        key=lambda d: d.name,
    )
    dbf_folders = []
    for d in folders:
        main_dbf, _ = find_dbf_files(d)
        if main_dbf:
            dbf_folders.append(d)

    if not dbf_folders:
        print(f"DBF-файлы не найдены ни в одной подпапке {parent}", file=sys.stderr)
        sys.exit(1)

    print(f"Найдено папок с ГТД: {len(dbf_folders)}")
    for d in dbf_folders:
        print(f"  {d.name}")
    print()

    results: list[dict] = []
    errors: list[str]   = []

    for i, folder in enumerate(dbf_folders, 1):
        print(f"[{i}/{len(dbf_folders)}] {folder.name}")
        main_dbf, slvs03 = find_dbf_files(folder)
        try:
            result = load_dbf(main_dbf, slvs03)
            mins = result.duration_ms // 60_000
            secs = (result.duration_ms % 60_000) / 1000
            print(f"  OK  добавлено {result.added:,} / дублей {result.duplicates_skipped:,} "
                  f"/ некорр. {result.invalid_skipped:,}  [{mins}м {secs:.0f}с]")
            results.append({
                "rows_total": result.rows_total,
                "added":      result.added,
                "dup":        result.duplicates_skipped,
                "inv":        result.invalid_skipped,
                "ms":         result.duration_ms,
            })
        except Exception as exc:
            print(f"  ОШИБКА: {exc}", file=sys.stderr)
            errors.append(f"{folder.name}: {exc}")

    _print_final(results)
    if errors:
        print(f"\nПапки с ошибками ({len(errors)}):")
        for e in errors:
            print(f"  {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
