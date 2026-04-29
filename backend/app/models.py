import enum

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
)
from sqlalchemy.orm import relationship

from app.database import Base


class Regime(enum.Enum):
    ИМ = "ИМ"
    ЭК = "ЭК"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255))
    is_active = Column(Integer, default=1, nullable=False)
    is_admin = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)


class Country(Base):
    __tablename__ = "countries"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True, nullable=False)
    iso_code = Column(String(2), index=True)
    name_uz = Column(String(255))
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
    tnved = Column(String(20), nullable=False, index=True)
    gtk_records = relationship("GTK", back_populates="product")
    category = relationship("Category", back_populates="products")


class CompanyUzb(Base):
    __tablename__ = "companies_uzb"
    id = Column(Integer, primary_key=True)
    stir = Column(String(50), nullable=False, index=True)
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
    # Имя историческое — Excel-колонка называлась "Цена(тыс)". Сейчас здесь
    # хранится фактическая сумма в долларах: db_load умножает значение из
    # Excel на 1000 при загрузке. Старые записи поправил scripts/fix_prices.
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
        Index("idx_gtk_country", "country_id"),
        Index("idx_gtk_product", "product_id"),
    )
