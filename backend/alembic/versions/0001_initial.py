"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-04-28

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("username", sa.String(100), nullable=False, unique=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255)),
        sa.Column("is_active", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("is_admin", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime()),
        sa.Column("updated_at", sa.DateTime()),
    )
    op.create_index("ix_users_username", "users", ["username"], unique=True)
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "countries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False, unique=True),
    )

    op.create_table(
        "regions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False, unique=True),
    )

    op.create_table(
        "categories",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False, unique=True),
    )

    op.create_table(
        "products",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "category_id",
            sa.Integer(),
            sa.ForeignKey("categories.id"),
            nullable=False,
        ),
        sa.Column("name", sa.String(500), nullable=False),
        sa.Column("tnved", sa.String(20), nullable=False),
    )
    op.create_index("ix_products_tnved", "products", ["tnved"])

    op.create_table(
        "companies_uzb",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("stir", sa.String(50), nullable=False),
        sa.Column("name", sa.String(500), nullable=False),
    )
    op.create_index("ix_companies_uzb_stir", "companies_uzb", ["stir"])

    op.create_table(
        "companies_foreign",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(500), nullable=True),
    )

    regime_enum = sa.Enum("ИМ", "ЭК", name="regime")
    regime_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "gtk",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("regime", regime_enum, nullable=False),
        sa.Column(
            "country_id", sa.Integer(), sa.ForeignKey("countries.id"), nullable=False
        ),
        sa.Column("address_uz", sa.String(1000)),
        sa.Column("address_foreign", sa.String(1000)),
        sa.Column("region_id", sa.Integer(), sa.ForeignKey("regions.id")),
        sa.Column("company_uzb_id", sa.Integer(), sa.ForeignKey("companies_uzb.id")),
        sa.Column(
            "company_foreign_id", sa.Integer(), sa.ForeignKey("companies_foreign.id")
        ),
        sa.Column(
            "product_id", sa.Integer(), sa.ForeignKey("products.id"), nullable=False
        ),
        sa.Column("unit", sa.String(50)),
        sa.Column("weight", sa.Float()),
        sa.Column("quantity", sa.Float()),
        sa.Column("price_thousand", sa.Float()),
        sa.Column("date", sa.Date(), nullable=False),
    )
    op.create_index("idx_gtk_regime", "gtk", ["regime"])
    op.create_index("idx_gtk_date", "gtk", ["date"])
    op.create_index("idx_gtk_country", "gtk", ["country_id"])
    op.create_index("idx_gtk_product", "gtk", ["product_id"])


def downgrade() -> None:
    op.drop_index("idx_gtk_product", table_name="gtk")
    op.drop_index("idx_gtk_country", table_name="gtk")
    op.drop_index("idx_gtk_date", table_name="gtk")
    op.drop_index("idx_gtk_regime", table_name="gtk")
    op.drop_table("gtk")
    sa.Enum(name="regime").drop(op.get_bind(), checkfirst=True)
    op.drop_table("companies_foreign")
    op.drop_index("ix_companies_uzb_stir", table_name="companies_uzb")
    op.drop_table("companies_uzb")
    op.drop_index("ix_products_tnved", table_name="products")
    op.drop_table("products")
    op.drop_table("categories")
    op.drop_table("regions")
    op.drop_table("countries")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_index("ix_users_username", table_name="users")
    op.drop_table("users")
