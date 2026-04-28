from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Float,
    Date,
    Enum,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
import enum

Base = declarative_base()


class Regime(enum.Enum):
    ИМ = "ИМ"
    ЭК = "ЭК"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255))
    is_active = Column(Integer, default=1)
    is_admin = Column(Integer, default=0)
    created_at = Column(Date)
    updated_at = Column(Date)


class Country(Base):
    __tablename__ = "countries"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True, nullable=False)
    gtk_records = relationship("GTK", back_populates="country")


class Region(Base):
    __tablename__ = "regions"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True, nullable=False)
    gtk_records = relationship("GTK", back_populates="region")


class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True, nullable=False)
    products = relationship("Product", back_populates="category")


class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    name = Column(String(500), nullable=False)
    tnved = Column(String(20), nullable=False)
    gtk_records = relationship("GTK", back_populates="product")
    category = relationship("Category", back_populates="products")


class CompanyUzb(Base):
    __tablename__ = "companies_uzb"
    id = Column(Integer, primary_key=True)
    stir = Column(String(50), nullable=False)
    name = Column(String(500), nullable=False)
    gtk_records = relationship("GTK", back_populates="company_uzb")


class CompanyForeign(Base):
    __tablename__ = "companies_foreign"
    id = Column(Integer, primary_key=True)
    name = Column(String(500), nullable=True)
    gtk_records = relationship("GTK", back_populates="company_foreign")


class GTK(Base):
    __tablename__ = "gtk"
    id = Column(Integer, primary_key=True)
    regime = Column(Enum(Regime), nullable=False)
    country_id = Column(Integer, ForeignKey("countries.id"), nullable=False)
    address_uz = Column(String(1000))
    address_foreign = Column(String(1000))
    region_id = Column(Integer, ForeignKey("regions.id"))
    company_uzb_id = Column(Integer, ForeignKey("companies_uzb.id"))
    company_foreign_id = Column(Integer, ForeignKey("companies_foreign.id"))
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    unit = Column(String(50))
    weight = Column(Float)
    quantity = Column(Float)
    price_thousand = Column(Float)
    date = Column(Date, nullable=False)

    country = relationship("Country", back_populates="gtk_records")
    region = relationship("Region", back_populates="gtk_records")
    product = relationship("Product", back_populates="gtk_records")
    company_uzb = relationship("CompanyUzb", back_populates="gtk_records")
    company_foreign = relationship("CompanyForeign", back_populates="gtk_records")

    __table_args__ = (
        Index("idx_gtk_regime", "regime"),
        Index("idx_gtk_date", "date"),
    )


DATABASE_URL = "postgresql+asyncpg://odya:Odilxon030101!@94.130.230.11:13465/gtk_data"
SYNC_DATABASE_URL = "postgresql://odya:Odilxon030101!@94.130.230.11:13465/gtk_data"

async_engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(
    async_engine, class_=AsyncSession, expire_on_commit=False
)

sync_engine = create_engine(SYNC_DATABASE_URL)


async def get_db():
    async with async_session() as session:
        yield session


async def init_db():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Таблицы созданы (async)")


async def create_users_table():
    """Создать таблицу users если её нет"""
    from sqlalchemy import text

    with sync_engine.connect() as conn:
        result = conn.execute(
            text("""
            SELECT 1 FROM information_schema.tables 
            WHERE table_name = 'users'
        """)
        )
        if not result.fetchone():
            conn.execute(
                text("""
                CREATE TABLE users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(100) UNIQUE NOT NULL,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    full_name VARCHAR(255),
                    is_active INTEGER DEFAULT 1,
                    is_admin INTEGER DEFAULT 0,
                    created_at DATE,
                    updated_at DATE
                )
            """)
            )
            conn.commit()
            print("Таблица users создана")
        else:
            print("Таблица users уже существует")
