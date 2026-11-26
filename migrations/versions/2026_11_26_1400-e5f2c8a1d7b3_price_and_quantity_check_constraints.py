"""price and quantity check constraints

Revision ID: e5f2c8a1d7b3
Revises: d9a4b7e0c5f1
Create Date: 2026-11-26 14:00:00

"""
from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'e5f2c8a1d7b3'
down_revision: str | Sequence[str] | None = 'd9a4b7e0c5f1'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Enforce price >= 0 and quantity > 0 in the database.

    Fails if existing rows already break these rules; fix those first.
    """
    op.create_check_constraint('ck_product_price_non_negative', 'product', 'price >= 0')
    op.create_check_constraint('ck_order_line_quantity_positive', 'order_line', 'quantity > 0')
    op.create_check_constraint(
        'ck_order_line_unit_price_non_negative', 'order_line', 'unit_price >= 0'
    )


def downgrade() -> None:
    """Drop the check constraints."""
    op.drop_constraint('ck_order_line_unit_price_non_negative', 'order_line', type_='check')
    op.drop_constraint('ck_order_line_quantity_positive', 'order_line', type_='check')
    op.drop_constraint('ck_product_price_non_negative', 'product', type_='check')
