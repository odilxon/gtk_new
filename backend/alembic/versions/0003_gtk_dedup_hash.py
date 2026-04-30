"""gtk.dedup_hash + UNIQUE index, backfill existing rows

Revision ID: 0003_gtk_dedup_hash
Revises: 0002_country_iso
Create Date: 2026-04-30

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from app.models import Regime
from app.services.gtk_etl import compute_row_hash

revision: str = "0003_gtk_dedup_hash"
down_revision: Union[str, None] = "0002_country_iso"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


BATCH = 5000


def upgrade() -> None:
    # 1. nullable-колонка для бэкфилла
    op.add_column("gtk", sa.Column("dedup_hash", sa.CHAR(64), nullable=True))

    conn = op.get_bind()
    print("Backfilling dedup_hash for existing rows...")
    max_id = (
        conn.execute(sa.text("SELECT id FROM gtk ORDER by id DESC LIMIT 1")).scalar()
        or 0
    )
    print(f" Max id in gtk: {max_id}")
    if max_id > 0:
        # 2. бэкфилл по id-окнам, чтобы не тащить всё в память
        last_id = 0
        total = 0
        while True:
            rows = conn.execute(
                sa.text(
                    """
                    SELECT id, date, regime, country_id, product_id,
                           company_uzb_id, company_foreign_id,
                           address_uz, address_foreign,
                           unit, weight, quantity, price_thousand
                    FROM gtk
                    WHERE id > :last_id
                    ORDER BY id
                    LIMIT :batch
                    """
                ),
                {"last_id": last_id, "batch": BATCH},
            ).all()
            if not rows:
                break
            updates = []
            for r in rows:
                # regime в БД хранится как строка-имя енама ('ИМ' / 'ЭК')
                regime_val = r.regime
                if isinstance(regime_val, Regime):
                    regime_val = regime_val.value
                h = compute_row_hash(
                    date=r.date,
                    regime=regime_val,
                    country_id=r.country_id,
                    product_id=r.product_id,
                    company_uzb_id=r.company_uzb_id,
                    company_foreign_id=r.company_foreign_id,
                    address_uz=r.address_uz,
                    address_foreign=r.address_foreign,
                    unit=r.unit,
                    weight=r.weight,
                    quantity=r.quantity,
                    price_thousand=r.price_thousand,
                )
                updates.append({"id": r.id, "h": h})
            conn.execute(
                sa.text("UPDATE gtk SET dedup_hash = :h WHERE id = :id"),
                updates,
            )
            last_id = rows[-1].id
            total += len(rows)
            if total % 50000 == 0:
                print(f"  backfilled {total}")
        print(f"Backfilled {total} rows")

    # 3. удалить дубликаты по dedup_hash, оставить самый старый id
    deleted = conn.execute(
        sa.text(
            """
            DELETE FROM gtk WHERE id IN (
                SELECT id FROM (
                    SELECT id,
                           ROW_NUMBER() OVER (
                               PARTITION BY dedup_hash ORDER BY id
                           ) AS rn
                    FROM gtk
                ) t WHERE rn > 1
            )
            """
        )
    ).rowcount
    if deleted:
        print(f"Removed {deleted} duplicate rows")

    # 4. NOT NULL + 5. UNIQUE INDEX
    op.alter_column("gtk", "dedup_hash", nullable=False)
    op.create_index("ix_gtk_dedup_hash", "gtk", ["dedup_hash"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_gtk_dedup_hash", table_name="gtk")
    op.drop_column("gtk", "dedup_hash")
