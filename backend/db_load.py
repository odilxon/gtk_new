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
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
import enum
import pandas as pd

Base = declarative_base()


class Regime(enum.Enum):
    ИМ = "ИМ"
    ЭК = "ЭК"


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


DATABASE_URL = "postgresql://odya:Odilxon030101!@94.130.230.11:13465/gtk_data"
engine = create_engine(DATABASE_URL)


def init_db():
    Base.metadata.create_all(engine)
    print("Таблицы созданы")


def drop_db():
    Base.metadata.drop_all(engine)
    print("Таблицы удалены")


def load_data(excel_path: str):
    print(f"Чтение файла: {excel_path}")
    df = pd.read_excel(excel_path)
    print(f"Прочитано {len(df)} записей")

    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        print("Создание стран...")
        countries_map = {}
        for name in df["Страна"].dropna().unique():
            if pd.notna(name):
                existing = session.query(Country).filter_by(name=name).first()
                if not existing:
                    country = Country(name=name)
                    session.add(country)
        session.commit()
        countries = session.query(Country).all()
        for c in countries:
            countries_map[c.name] = c.id
        print(f"  Добавлено {len(countries_map)} стран")

        print("Создание областей...")
        regions_map = {}
        for name in df["Область"].dropna().unique():
            if pd.notna(name) and str(name).strip():
                existing = session.query(Region).filter_by(name=name).first()
                if not existing:
                    region = Region(name=name)
                    session.add(region)
        session.commit()
        regions = session.query(Region).all()
        for r in regions:
            regions_map[r.name] = r.id
        print(f"  Добавлено {len(regions_map)} областей")

        print("Создание категорий...")
        categories_map = {}
        for name in df["Категория продукции"].dropna().unique():
            if pd.notna(name):
                existing = session.query(Category).filter_by(name=name).first()
                if not existing:
                    category = Category(name=name)
                    session.add(category)
        session.commit()
        categories = session.query(Category).all()
        for c in categories:
            categories_map[c.name] = c.id
        print(f"  Добавлено {len(categories_map)} категорий")

        print("Создание товаров...")
        products_map = {}
        for _, row in df.drop_duplicates(
            subset=["Категория продукции", "Товар", "ТНВЕД"]
        ).iterrows():
            category_name = row["Категория продукции"]
            product_name = row["Товар"]
            tnved = str(row["ТНВЕД"])
            if pd.notna(category_name) and pd.notna(product_name):
                category_id = categories_map.get(category_name)
                if category_id:
                    existing = (
                        session.query(Product)
                        .filter_by(
                            category_id=category_id, name=product_name, tnved=tnved
                        )
                        .first()
                    )
                    if not existing:
                        product = Product(
                            category_id=category_id, name=product_name, tnved=tnved
                        )
                        session.add(product)
        session.commit()
        products = session.query(Product).all()
        for p in products:
            key = (p.category.name, p.name, p.tnved)
            products_map[key] = p.id
        print(f"  Добавлено {len(products_map)} товаров")

        print("Создание узбекских компаний...")
        companies_uzb_map = {}
        for _, row in df.drop_duplicates(
            subset=["СТИР Узб", "Организация Узб"]
        ).iterrows():
            stir = row["СТИР Узб"]
            name = row["Организация Узб"]
            if pd.notna(stir) and pd.notna(name):
                key = str(stir)
                existing = session.query(CompanyUzb).filter_by(stir=key).first()
                if not existing:
                    company = CompanyUzb(stir=key, name=name)
                    session.add(company)
        session.commit()
        companies_uzb = session.query(CompanyUzb).all()
        for c in companies_uzb:
            companies_uzb_map[c.stir] = c.id
        print(f"  Добавлено {len(companies_uzb_map)} узбекских компаний")

        print("Создание иностранных компаний...")
        companies_foreign_map = {}
        for _, row in df.drop_duplicates(subset=["Организация Хориж"]).iterrows():
            name = row["Организация Хориж"]
            if pd.notna(name):
                existing = session.query(CompanyForeign).filter_by(name=name).first()
                if not existing:
                    company = CompanyForeign(name=name)
                    session.add(company)
        session.commit()
        companies_foreign = session.query(CompanyForeign).all()
        for c in companies_foreign:
            companies_foreign_map[c.name] = c.id
        print(f"  Добавлено {len(companies_foreign_map)} иностранных компаний")

        print("Создание записей GTK...")
        for idx, row in df.iterrows():
            regime = Regime[row["Режим"]]
            country_name = row["Страна"]
            country_id = countries_map.get(country_name)
            if not country_id:
                continue

            address_uz = row["Адрес Узб"] if pd.notna(row["Адрес Узб"]) else None
            address_foreign = (
                row["Адрес Хориж"] if pd.notna(row["Адрес Хориж"]) else None
            )

            region_name = row["Область"]
            region_id = regions_map.get(region_name) if pd.notna(region_name) else None

            stir_uz = row.get("СТИР Узб")
            company_uzb_id = (
                companies_uzb_map.get(str(stir_uz)) if pd.notna(stir_uz) else None
            )

            company_foreign_name = row["Организация Хориж"]
            company_foreign_id = (
                companies_foreign_map.get(company_foreign_name)
                if pd.notna(company_foreign_name)
                else None
            )

            category_name = row["Категория продукции"]
            product_name = row["Товар"]
            tnved = str(row["ТНВЕД"])
            product_key = (category_name, product_name, tnved)
            product_id = products_map.get(product_key)
            if not product_id:
                continue

            unit = row["Eд.измерения"] if pd.notna(row["Eд.измерения"]) else None
            weight = float(row["Вес(кг)"]) if pd.notna(row.get("Вес(кг)")) else None
            quantity = (
                float(row["Количество"]) if pd.notna(row.get("Количество")) else None
            )
            price_thousand = (
                float(row["Цена(тыс)"]) if pd.notna(row.get("Цена(тыс)")) else None
            )
            date = pd.to_datetime(row["Дата"]).date()

            gtk_record = GTK(
                regime=regime,
                country_id=country_id,
                address_uz=address_uz,
                address_foreign=address_foreign,
                region_id=region_id,
                company_uzb_id=company_uzb_id,
                company_foreign_id=company_foreign_id,
                product_id=product_id,
                unit=unit,
                weight=weight,
                quantity=quantity,
                price_thousand=price_thousand,
                date=date,
            )
            session.add(gtk_record)

            if (idx + 1) % 500 == 0:
                session.commit()
                print(f"  Обработано {idx + 1} записей...")

        session.commit()
        print(f"Загрузка завершена!")

    except Exception as e:
        session.rollback()
        print(f"Ошибка: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Использование: python db_load.py init|load <excel_path>")
        sys.exit(1)

    command = sys.argv[1]
    if command == "init":
        init_db()
    elif command == "load":
        excel_path = sys.argv[2] if len(sys.argv) > 2 else "gtk_data_2020.xlsx"
        load_data(excel_path)
    elif command == "drop":
        drop_db()
    else:
        print(f"Неизвестная команда: {command}")
