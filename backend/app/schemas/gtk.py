from datetime import date

from pydantic import BaseModel, ConfigDict

from app.schemas.common import TopItem


class GTKItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    regime: str
    country_id: int
    country_name: str | None = None
    address_uz: str | None = None
    address_foreign: str | None = None
    region_id: int | None = None
    region_name: str | None = None
    company_uzb_id: int | None = None
    company_uzb_name: str | None = None
    company_foreign_id: int | None = None
    company_foreign_name: str | None = None
    product_id: int
    product_name: str | None = None
    category_id: int | None = None
    category_name: str | None = None
    tnved: str | None = None
    unit: str | None = None
    weight: float | None = None
    quantity: float | None = None
    price_thousand: float | None = None
    date: date


class GTKStats(BaseModel):
    total_count: int
    import_sum: float
    export_sum: float
    top_countries: list[TopItem]
    top_categories: list[TopItem]
