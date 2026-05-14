"""add DBF/GTD extra fields to gtk table

Все новые колонки nullable — старые записи из Excel останутся с NULL.
Данные заполняются при загрузке через dbf_etl.load_dbf().

Revision ID: 0004_dbf_extra_fields
Revises: 0003_gtk_dedup_hash
Create Date: 2026-05-14
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0004_dbf_extra_fields"
down_revision: Union[str, None] = "0003_gtk_dedup_hash"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_NEW_COLS = [
    ("declaration_number", sa.String(20)),
    ("incoterms",          sa.String(10)),
    ("incoterms_place",    sa.String(100)),
    ("currency_code",      sa.CHAR(3)),
    ("currency_amount",    sa.Float()),
    ("exchange_rate",      sa.Float()),
    ("gross_weight",       sa.Float()),
    ("packages_count",     sa.Integer()),
    ("customs_duty",       sa.Float()),
    ("vat_amount",         sa.Float()),
]


def upgrade() -> None:
    for col_name, col_type in _NEW_COLS:
        op.add_column("gtk", sa.Column(col_name, col_type, nullable=True))


def downgrade() -> None:
    for col_name, _ in reversed(_NEW_COLS):
        op.drop_column("gtk", col_name)
