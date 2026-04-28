from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class LookupItem(BaseModel):
    id: int
    name: str


class CompanyUzbItem(BaseModel):
    id: int
    name: str
    stir: str


class ProductItem(BaseModel):
    id: int
    name: str
    tnved: str
    category_id: int


class TopItem(BaseModel):
    id: int
    name: str
    count: int


class Paginated(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int
