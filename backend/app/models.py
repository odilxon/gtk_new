import enum

from sqlalchemy import (
    CHAR,
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
    # SHA-256 от канонического представления строки. UNIQUE — для дедупа
    # при повторной загрузке Excel. Формат строки и хеша — в gtk_etl.py.
    dedup_hash = Column(CHAR(64), nullable=False, unique=True, index=True)

    # ── Поля из DBF/ГТД (NULL для записей из Excel) ──────────────────────
    declaration_number = Column(String(20))   # G7A/G7C: "26002/0008601"
    incoterms          = Column(String(10))   # G20B: "CIP", "FOB", "EXW"…
    incoterms_place    = Column(String(100))  # G20NAME: "г.Ташкент"
    currency_code      = Column(CHAR(3))      # ISO-4217 alpha: "USD","EUR","RUB"
    currency_amount    = Column(Float)        # G22B: сумма в валюте контракта
    exchange_rate      = Column(Float)        # G23: UZS за 1 единицу валюты
    gross_weight       = Column(Float)        # G35: вес брутто, кг
    packages_count     = Column(Integer)      # G32: количество мест
    customs_duty       = Column(Float)        # PAYMFACT20: пошлина (UZS)
    vat_amount         = Column(Float)        # PAYMFACT29: НДС (UZS)

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


class GTKAll(Base):
    """Плоская денормализованная таблица ГТД — без внешних ключей.

    Все значения хранятся «как есть» из DBF-файлов: коды стран, ТНВЭД,
    наименования компаний, суммы. Никакой нормализации — просто сырые данные.
    Старая таблица gtk остаётся нетронутой.
    """
    __tablename__ = "gtk_all"

    id = Column(Integer, primary_key=True)

    # ── Идентификация декларации ──────────────────────────────────────────
    regime             = Column(String(4),   nullable=False)  # "ИМ" / "ЭК"
    date               = Column(Date,        nullable=False)
    declaration_number = Column(String(20))                   # G7A/G7C

    # ── Страна ───────────────────────────────────────────────────────────
    country_code = Column(String(3))    # G15: "156"
    country_name = Column(String(255))  # из SLVS03: "КИТАЙ" (пусто если нет файла)
    country_iso2 = Column(String(2))    # из SLVS03: "CN"

    # ── Товар ─────────────────────────────────────────────────────────────
    tnved               = Column(String(20))    # G33: "7002390000"
    product_description = Column(String(1000)) # G31NAME (обрезан до 1000 символов)

    # ── Компании ──────────────────────────────────────────────────────────
    company_uzb_name    = Column(String(500))  # G8NAME
    company_uzb_stir    = Column(String(50))   # G8CODE2
    company_foreign_name= Column(String(500))  # G2NAME

    # ── Измерения ─────────────────────────────────────────────────────────
    unit           = Column(String(50))   # P1: "кг", "шт"
    weight         = Column(Float)        # G38: нетто кг
    gross_weight   = Column(Float)        # G35: брутто кг
    quantity       = Column(Float)        # ZA_ED
    packages_count = Column(Integer)      # G32

    # ── Цена / валюта ─────────────────────────────────────────────────────
    price_usd       = Column(Float)    # G45USD — CIF-стоимость, фактический USD
    currency_code   = Column(CHAR(3))  # G22A → alpha-3: "USD", "EUR", "RUB"
    currency_amount = Column(Float)    # G22B — сумма в валюте контракта
    exchange_rate   = Column(Float)    # G23 — UZS за 1 ед. валюты на дату ГТД

    # ── Условия поставки ──────────────────────────────────────────────────
    incoterms       = Column(String(10))   # G20B: "CIP", "FOB"…
    incoterms_place = Column(String(100))  # G20NAME: "г.Ташкент"

    # ── Таможенные платежи (UZS) ──────────────────────────────────────────
    customs_duty = Column(Float)  # PAYMFACT20
    vat_amount   = Column(Float)  # PAYMFACT29

    # ── Источник и дедупликация ───────────────────────────────────────────
    source_file = Column(String(255))              # имя исходного DBF-файла
    dedup_hash  = Column(CHAR(64), nullable=False)  # SHA-256, UNIQUE

    __table_args__ = (
        Index("idx_gtkall_regime",   "regime"),
        Index("idx_gtkall_date",     "date"),
        Index("idx_gtkall_country",  "country_code"),
        Index("idx_gtkall_tnved",    "tnved"),
        Index("idx_gtkall_stir",     "company_uzb_stir"),
        Index("idx_gtkall_dedup",    "dedup_hash", unique=True),
    )
