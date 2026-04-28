"""Списки TNVED-кодов для группировки в чартах.

Источник: данные старого проекта qishloq_hojaligi.

- OZIQOVQAT — список из ~787 кодов из data/oziqovqat.xlsx (читается лениво).
- MEVA — определяется регулярным префиксом (07*, 08*, 0904*, 1008*, 1202*)
  плюс два точных кода. Хранение списком 134-х TNVED-ов из fixes.xlsx
  не нужно: префиксная проверка покрывает их.
- FIXES (для таблиц breakdown) — лист meva/oziq из fixes.xlsx с разбивкой
  по подкатегориям (TYPE → list[TNVED]).
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"

# Префиксы и точные коды для группы "Мева-сабзавот"
MEVA_PREFIXES = ("07", "08", "0904", "1008", "1202")
MEVA_EXACT = {"1207409000", "2008191900"}


def is_meva(tnved: str | None) -> bool:
    if not tnved:
        return False
    if tnved in MEVA_EXACT:
        return True
    return any(tnved.startswith(p) for p in MEVA_PREFIXES)


@lru_cache(maxsize=1)
def oziq_tnveds() -> set[str]:
    path = DATA_DIR / "oziqovqat.xlsx"
    if not path.exists():
        return set()
    df = pd.read_excel(path, converters={"CODE": str})
    return {str(c).strip() for c in df["CODE"].dropna()}


@lru_cache(maxsize=2)
def fixes_breakdown(group: str) -> dict[str, list[str]]:
    """Возвращает {категория: [tnved, ...]} для group ∈ {'meva', 'oziq'}."""
    if group not in {"meva", "oziq"}:
        return {}
    path = DATA_DIR / "fixes.xlsx"
    if not path.exists():
        return {}
    df = pd.read_excel(path, sheet_name=group, converters={"TNVED": str})
    out: dict[str, list[str]] = {}
    for tnved, _tovar, _type in zip(df["TNVED"], df["TOVAR"], df["TYPE"]):
        if pd.isna(tnved) or pd.isna(_type):
            continue
        out.setdefault(str(_type), []).append(str(tnved).strip())
    return out
