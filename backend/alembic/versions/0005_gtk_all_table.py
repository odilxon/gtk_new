"""create gtk_all flat table for raw GTD/DBF data

Денормализованная таблица без внешних ключей — хранит сырые данные ГТД
(коды стран, ТНВЭД, наименования компаний) как есть из DBF-файлов.
Таблица gtk остаётся нетронутой.

Revision ID: 0005_gtk_all_table
Revises: 0004_dbf_extra_fields
Create Date: 2026-05-14
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0005_gtk_all_table"
down_revision: Union[str, None] = "0004_dbf_extra_fields"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "gtk_all",
        sa.Column("id",                  sa.Integer(),    primary_key=True),
        # Декларация
        sa.Column("regime",              sa.String(4),    nullable=False),
        sa.Column("date",                sa.Date(),       nullable=False),
        sa.Column("declaration_number",  sa.String(20)),
        # Страна (сырые данные)
        sa.Column("country_code",        sa.String(3)),
        sa.Column("country_name",        sa.String(255)),
        sa.Column("country_iso2",        sa.String(2)),
        # Товар
        sa.Column("tnved",               sa.String(20)),
        sa.Column("product_description", sa.String(1000)),
        # Компании
        sa.Column("company_uzb_name",    sa.String(500)),
        sa.Column("company_uzb_stir",    sa.String(50)),
        sa.Column("company_foreign_name",sa.String(500)),
        # Измерения
        sa.Column("unit",                sa.String(50)),
        sa.Column("weight",              sa.Float()),
        sa.Column("gross_weight",        sa.Float()),
        sa.Column("quantity",            sa.Float()),
        sa.Column("packages_count",      sa.Integer()),
        # Цена / валюта
        sa.Column("price_usd",           sa.Float()),
        sa.Column("currency_code",       sa.CHAR(3)),
        sa.Column("currency_amount",     sa.Float()),
        sa.Column("exchange_rate",       sa.Float()),
        # Поставка
        sa.Column("incoterms",           sa.String(10)),
        sa.Column("incoterms_place",     sa.String(100)),
        # Платежи
        sa.Column("customs_duty",        sa.Float()),
        sa.Column("vat_amount",          sa.Float()),
        # Служебные
        sa.Column("source_file",         sa.String(255)),
        sa.Column("dedup_hash",          sa.CHAR(64),     nullable=False),
    )
    op.create_index("idx_gtkall_regime",  "gtk_all", ["regime"])
    op.create_index("idx_gtkall_date",    "gtk_all", ["date"])
    op.create_index("idx_gtkall_country", "gtk_all", ["country_code"])
    op.create_index("idx_gtkall_tnved",   "gtk_all", ["tnved"])
    op.create_index("idx_gtkall_stir",    "gtk_all", ["company_uzb_stir"])
    op.create_index("idx_gtkall_dedup",   "gtk_all", ["dedup_hash"], unique=True)


def downgrade() -> None:
    op.drop_index("idx_gtkall_dedup",   table_name="gtk_all")
    op.drop_index("idx_gtkall_stir",    table_name="gtk_all")
    op.drop_index("idx_gtkall_tnved",   table_name="gtk_all")
    op.drop_index("idx_gtkall_country", table_name="gtk_all")
    op.drop_index("idx_gtkall_date",    table_name="gtk_all")
    op.drop_index("idx_gtkall_regime",  table_name="gtk_all")
    op.drop_table("gtk_all")
