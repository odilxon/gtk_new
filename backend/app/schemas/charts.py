from typing import Literal

from pydantic import BaseModel

Regime = Literal["import", "export"]
Group = Literal["meva", "oziq"]


class MonthlyResponse(BaseModel):
    months: list[str]
    imports: dict[str, list[float | None]]   # year -> [12 значений]
    exports: dict[str, list[float | None]]
    import_grow: dict[str, list[float | None]]
    export_grow: dict[str, list[float | None]]


class GroupTotals(BaseModel):
    total: float
    massa: float


class GroupSummary(BaseModel):
    year: int
    group: Group
    import_: GroupTotals
    export: GroupTotals
    total: GroupTotals


class GroupBreakdownRow(BaseModel):
    name: str
    massa: float
    total: float
    avg: float


class GroupBreakdown(BaseModel):
    year: int
    group: Group
    type: Literal["import", "export", "all"]
    rows: list[GroupBreakdownRow]


class TopItemRow(BaseModel):
    label: str
    value: float


class TopItems(BaseModel):
    year: int
    items: list[TopItemRow]


class RegionPoint(BaseModel):
    name: str         # русское/узбекское имя области (как в БД)
    code: str         # uz-an, uz-tk и т.п.
    value: float
    massa: float
    meva_total: float
    meva_massa: float
    oziq_total: float
    oziq_massa: float


class RegionsResponse(BaseModel):
    year: int
    regime: Regime
    items: list[RegionPoint]
    max_value: float


class WorldPoint(BaseModel):
    iso: str
    name: str
    name_uz: str | None
    value: float
    massa: float
    meva_value: float
    meva_massa: float
    oziq_value: float
    oziq_massa: float


class WorldResponse(BaseModel):
    year: int
    regime: Regime
    items: list[WorldPoint]
    max_value: float
