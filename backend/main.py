from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, func, case, cast, Integer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from pydantic import BaseModel, EmailStr
from datetime import date, datetime
from typing import Optional
import hashlib

from models import (
    get_db,
    async_engine,
    async_session,
    User,
    Country,
    Region,
    Category,
    Product,
    CompanyUzb,
    CompanyForeign,
    GTK,
    Regime,
)

app = FastAPI(title="GTK API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: Optional[str]
    is_admin: int

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class GTKFilter(BaseModel):
    regime: Optional[str] = None
    country_id: Optional[int] = None
    region_id: Optional[int] = None
    category_id: Optional[int] = None
    product_id: Optional[int] = None
    company_uzb_id: Optional[int] = None
    company_foreign_id: Optional[int] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    search: Optional[str] = None


class GTKResponse(BaseModel):
    id: int
    regime: str
    country_id: int
    country_name: Optional[str] = None
    address_uz: Optional[str]
    address_foreign: Optional[str]
    region_id: Optional[int]
    region_name: Optional[str]
    company_uzb_id: Optional[int]
    company_uzb_name: Optional[str]
    company_foreign_id: Optional[int]
    company_foreign_name: Optional[str]
    product_id: int
    product_name: Optional[str]
    category_id: Optional[int]
    category_name: Optional[str]
    tnved: Optional[str]
    unit: Optional[str]
    weight: Optional[float]
    quantity: Optional[float]
    price_thousand: Optional[float]
    date: date

    class Config:
        from_attributes = True


class PaginatedGTKResponse(BaseModel):
    items: list[GTKResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class GTKStats(BaseModel):
    total_count: int
    import_sum: float
    export_sum: float
    top_countries: list[dict]
    top_categories: list[dict]


@app.on_event("startup")
async def startup():
    async with async_engine.begin() as conn:
        pass


@app.post("/api/auth/register", response_model=UserResponse)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == user_data.username))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Username already exists")

    result = await db.execute(select(User).where(User.email == user_data.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already exists")

    password_hash = hashlib.sha256(user_data.password.encode()).hexdigest()
    user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=password_hash,
        full_name=user_data.full_name,
        is_active=1,
        is_admin=0,
        created_at=datetime.now().date(),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@app.post("/api/auth/login", response_model=TokenResponse)
async def login(credentials: LoginRequest, db: AsyncSession = Depends(get_db)):
    password_hash = hashlib.sha256(credentials.password.encode()).hexdigest()
    result = await db.execute(
        select(User).where(
            User.username == credentials.username, User.password_hash == password_hash
        )
    )
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = f"{user.id}:{user.password_hash}"
    return TokenResponse(
        access_token=access_token, user=UserResponse.model_validate(user)
    )


@app.get("/api/auth/me", response_model=UserResponse)
async def get_current_user(
    Authorization: str = Query(..., description="Bearer token"),
    db: AsyncSession = Depends(get_db),
):
    if not Authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid token format")

    token = Authorization.replace("Bearer ", "")
    try:
        user_id = int(token.split(":")[0])
    except:
        raise HTTPException(status_code=401, detail="Invalid token")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found")

    return user


@app.get("/api/gtk", response_model=PaginatedGTKResponse)
async def get_gtk(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    regime: Optional[str] = Query(None),
    country_id: Optional[int] = Query(None),
    region_id: Optional[int] = Query(None),
    category_id: Optional[int] = Query(None),
    product_id: Optional[int] = Query(None),
    company_uzb_id: Optional[int] = Query(None),
    company_foreign_id: Optional[int] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    offset = (page - 1) * page_size

    query = select(GTK).options(
        selectinload(GTK.country),
        selectinload(GTK.region),
        selectinload(GTK.product).selectinload(Product.category),
        selectinload(GTK.company_uzb),
        selectinload(GTK.company_foreign),
    )
    count_query = select(func.count(GTK.id))

    if regime:
        query = query.where(GTK.regime == Regime[regime])
        count_query = count_query.where(GTK.regime == Regime[regime])
    if country_id:
        query = query.where(GTK.country_id == country_id)
        count_query = count_query.where(GTK.country_id == country_id)
    if region_id:
        query = query.where(GTK.region_id == region_id)
        count_query = count_query.where(GTK.region_id == region_id)
    if product_id:
        query = query.where(GTK.product_id == product_id)
        count_query = count_query.where(GTK.product_id == product_id)
    if company_uzb_id:
        query = query.where(GTK.company_uzb_id == company_uzb_id)
        count_query = count_query.where(GTK.company_uzb_id == company_uzb_id)
    if company_foreign_id:
        query = query.where(GTK.company_foreign_id == company_foreign_id)
        count_query = count_query.where(GTK.company_foreign_id == company_foreign_id)
    if date_from:
        query = query.where(GTK.date >= date_from)
        count_query = count_query.where(GTK.date >= date_from)
    if date_to:
        query = query.where(GTK.date <= date_to)
        count_query = count_query.where(GTK.date <= date_to)
    if category_id:
        query = query.where(Product.category_id == category_id)
        count_query = count_query.where(Product.category_id == category_id)
    if search:
        search_filter = f"%{search}%"
        query = query.join(Product).where(
            Product.name.ilike(search_filter) | Product.tnved.ilike(search_filter)
        )
        count_query = count_query.join(Product).where(
            Product.name.ilike(search_filter) | Product.tnved.ilike(search_filter)
        )

    query = query.join(Product).offset(offset).limit(page_size)

    result = await db.execute(query)
    records = result.scalars().all()

    count_result = await db.execute(count_query)
    total = count_result.scalar()

    items = []
    for r in records:
        items.append(
            GTKResponse(
                id=r.id,
                regime=r.regime.value,
                country_id=r.country_id,
                address_uz=r.address_uz,
                address_foreign=r.address_foreign,
                region_id=r.region_id,
                company_uzb_id=r.company_uzb_id,
                company_foreign_id=r.company_foreign_id,
                product_id=r.product_id,
                unit=r.unit,
                weight=r.weight,
                quantity=r.quantity,
                price_thousand=r.price_thousand,
                date=r.date,
                country_name=r.country.name if r.country else None,
                region_name=r.region.name if r.region else None,
                company_uzb_name=r.company_uzb.name if r.company_uzb else None,
                company_foreign_name=r.company_foreign.name
                if r.company_foreign
                else None,
                product_name=r.product.name if r.product else None,
                category_id=r.product.category_id if r.product else None,
                category_name=r.product.category.name
                if r.product and r.product.category
                else None,
                tnved=r.product.tnved if r.product else None,
            )
        )

    total_pages = (total + page_size - 1) // page_size
    return PaginatedGTKResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@app.get("/api/gtk/stats", response_model=GTKStats)
async def get_gtk_stats(db: AsyncSession = Depends(get_db)):
    total_result = await db.execute(select(func.count(GTK.id)))
    total_count = total_result.scalar()

    import_result = await db.execute(
        select(func.coalesce(func.sum(GTK.price_thousand), 0)).where(
            GTK.regime == Regime.ИМ
        )
    )
    import_sum = float(import_result.scalar() or 0)

    export_result = await db.execute(
        select(func.coalesce(func.sum(GTK.price_thousand), 0)).where(
            GTK.regime == Regime.ЭК
        )
    )
    export_sum = float(export_result.scalar() or 0)

    countries_result = await db.execute(
        select(GTK.country_id, func.count(GTK.id).label("count"))
        .group_by(GTK.country_id)
        .order_by(func.count(GTK.id).desc())
        .limit(5)
    )
    top_countries = []
    for row in countries_result:
        country_result = await db.execute(
            select(Country).where(Country.id == row.country_id)
        )
        country = country_result.scalar_one()
        top_countries.append(
            {"id": row.country_id, "name": country.name, "count": row.count}
        )

    categories_result = await db.execute(
        select(Product.category_id, func.count(GTK.id).label("count"))
        .join(GTK, GTK.product_id == Product.id)
        .group_by(Product.category_id)
        .order_by(func.count(GTK.id).desc())
        .limit(5)
    )
    top_categories = []
    for row in categories_result:
        cat_result = await db.execute(
            select(Category).where(Category.id == row.category_id)
        )
        category = cat_result.scalar_one()
        top_categories.append(
            {"id": row.category_id, "name": category.name, "count": row.count}
        )

    return GTKStats(
        total_count=total_count,
        import_sum=import_sum,
        export_sum=export_sum,
        top_countries=top_countries,
        top_categories=top_categories,
    )


@app.get("/api/countries", response_model=list[dict])
async def get_countries(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Country).order_by(Country.name))
    countries = result.scalars().all()
    return [{"id": c.id, "name": c.name} for c in countries]


@app.get("/api/regions", response_model=list[dict])
async def get_regions(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Region).order_by(Region.name))
    regions = result.scalars().all()
    return [{"id": r.id, "name": r.name} for r in regions]


@app.get("/api/categories", response_model=list[dict])
async def get_categories(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Category).order_by(Category.name))
    categories = result.scalars().all()
    return [{"id": c.id, "name": c.name} for c in categories]


@app.get("/api/products", response_model=list[dict])
async def get_products(
    category_id: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    query = select(Product)
    if category_id:
        query = query.where(Product.category_id == category_id)
    if search:
        query = query.where(Product.name.ilike(f"%{search}%"))
    result = await db.execute(query.limit(50))
    products = result.scalars().all()
    return [
        {"id": p.id, "name": p.name, "tnved": p.tnved, "category_id": p.category_id}
        for p in products
    ]


@app.get("/api/companies-uzb", response_model=list[dict])
async def get_companies_uzb(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CompanyUzb).order_by(CompanyUzb.name))
    companies = result.scalars().all()
    return [{"id": c.id, "name": c.name, "stir": c.stir} for c in companies]


@app.get("/api/companies-foreign", response_model=list[dict])
async def get_companies_foreign(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CompanyForeign).order_by(CompanyForeign.name))
    companies = result.scalars().all()
    return [{"id": c.id, "name": c.name} for c in companies]


@app.get("/health")
def health_check():
    return {"status": "ok"}
