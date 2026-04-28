from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.charts import (
    GroupBreakdown,
    GroupSummary,
    MonthlyResponse,
    RegionsResponse,
    TopItems,
    WorldResponse,
)
from app.security import get_current_user
from app.services import charts as svc

router = APIRouter(
    prefix="/api/charts",
    tags=["charts"],
    dependencies=[Depends(get_current_user)],
)


def common_filters(
    tnved: list[str] | None = Query(None),
    region_id: int | None = Query(None),
    country_id: int | None = Query(None),
) -> dict:
    return {"tnved": tnved, "region_id": region_id, "country_id": country_id}


@router.get("/years", response_model=list[int])
async def years(db: AsyncSession = Depends(get_db)) -> list[int]:
    return await svc.years(db)


@router.get("/monthly", response_model=MonthlyResponse)
async def monthly(
    filters: dict = Depends(common_filters),
    db: AsyncSession = Depends(get_db),
) -> MonthlyResponse:
    return await svc.monthly(db, **filters)


@router.get("/group-summary", response_model=GroupSummary)
async def group_summary(
    year: int = Query(...),
    group: Literal["meva", "oziq"] = Query(...),
    region_id: int | None = Query(None),
    country_id: int | None = Query(None),
    db: AsyncSession = Depends(get_db),
) -> GroupSummary:
    return await svc.group_summary(
        db, year=year, group=group, region_id=region_id, country_id=country_id
    )


@router.get("/group-breakdown", response_model=GroupBreakdown)
async def group_breakdown(
    year: int = Query(...),
    group: Literal["meva", "oziq"] = Query(...),
    type: Literal["import", "export", "all"] = Query("all"),
    region_id: int | None = Query(None),
    country_id: int | None = Query(None),
    db: AsyncSession = Depends(get_db),
) -> GroupBreakdown:
    return await svc.group_breakdown(
        db,
        year=year,
        group=group,
        type_=type,
        region_id=region_id,
        country_id=country_id,
    )


@router.get("/top-organizations", response_model=TopItems)
async def top_organizations(
    year: int = Query(...),
    regime: Literal["import", "export"] = Query(...),
    limit: int = Query(10, ge=1, le=50),
    filters: dict = Depends(common_filters),
    db: AsyncSession = Depends(get_db),
) -> TopItems:
    return await svc.top_organizations(
        db, year=year, regime_str=regime, limit=limit, **filters
    )


@router.get("/top-countries", response_model=TopItems)
async def top_countries(
    year: int = Query(...),
    regime: Literal["import", "export"] = Query(...),
    limit: int = Query(10, ge=1, le=50),
    tnved: list[str] | None = Query(None),
    region_id: int | None = Query(None),
    db: AsyncSession = Depends(get_db),
) -> TopItems:
    return await svc.top_countries(
        db, year=year, regime_str=regime, limit=limit, tnved=tnved, region_id=region_id
    )


@router.get("/regions", response_model=RegionsResponse)
async def regions(
    year: int = Query(...),
    regime: Literal["import", "export"] = Query(...),
    tnved: list[str] | None = Query(None),
    country_id: int | None = Query(None),
    db: AsyncSession = Depends(get_db),
) -> RegionsResponse:
    return await svc.regions(
        db, year=year, regime_str=regime, tnved=tnved, country_id=country_id
    )


@router.get("/world", response_model=WorldResponse)
async def world(
    year: int = Query(...),
    regime: Literal["import", "export"] = Query(...),
    tnved: list[str] | None = Query(None),
    region_id: int | None = Query(None),
    db: AsyncSession = Depends(get_db),
) -> WorldResponse:
    return await svc.world(
        db, year=year, regime_str=regime, tnved=tnved, region_id=region_id
    )
