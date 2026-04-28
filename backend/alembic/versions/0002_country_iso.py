"""country iso_code + name_uz

Revision ID: 0002_country_iso
Revises: 0001_initial
Create Date: 2026-04-28

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002_country_iso"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("countries", sa.Column("iso_code", sa.String(2), nullable=True))
    op.add_column("countries", sa.Column("name_uz", sa.String(255), nullable=True))
    op.create_index("ix_countries_iso_code", "countries", ["iso_code"])


def downgrade() -> None:
    op.drop_index("ix_countries_iso_code", table_name="countries")
    op.drop_column("countries", "name_uz")
    op.drop_column("countries", "iso_code")
