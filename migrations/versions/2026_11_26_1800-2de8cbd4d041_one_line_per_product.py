"""one line per product

Revision ID: 2de8cbd4d041
Revises: fdb0f4e816c1
Create Date: 2026-11-26 10:25:46.712645

"""
from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '2de8cbd4d041'
down_revision: str | Sequence[str] | None = 'fdb0f4e816c1'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


# (line table, parent id column)
LINE_TABLES = (("order_line", "order_id"), ("standing_order_line", "standing_order_id"))


def merge_duplicate_lines(table: str, parent: str) -> None:
    """Fold lines for the same product on the same parent into the lowest-id line."""
    op.execute(
        f"""
        UPDATE {table} AS keep
        SET quantity = merged.total
        FROM (
            SELECT min(id) AS keep_id, sum(quantity) AS total
            FROM {table}
            GROUP BY {parent}, product_id
            HAVING count(*) > 1
        ) AS merged
        WHERE keep.id = merged.keep_id
        """
    )
    op.execute(
        f"""
        DELETE FROM {table} AS dup
        USING {table} AS keep
        WHERE keep.{parent} = dup.{parent}
          AND keep.product_id = dup.product_id
          AND keep.id < dup.id
        """
    )


def upgrade() -> None:
    """Allow each product on only one line per order / standing order.

    Existing duplicates are merged first: quantities are summed onto the earliest
    line and the others deleted. Order lines are only merged when they share a
    unit price; otherwise this stops so the order can be fixed by hand.
    """
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM order_line
                GROUP BY order_id, product_id
                HAVING count(DISTINCT unit_price) > 1
            ) THEN
                RAISE EXCEPTION 'An order has the same product on several lines at different '
                    'unit prices; fix those lines by hand, then re-run this migration.';
            END IF;
        END $$
        """
    )
    for table, parent in LINE_TABLES:
        merge_duplicate_lines(table, parent)

    op.create_unique_constraint(
        "uq_order_line_order_product", "order_line", ["order_id", "product_id"]
    )
    op.create_unique_constraint(
        "uq_standing_order_line_standing_order_product",
        "standing_order_line",
        ["standing_order_id", "product_id"],
    )


def downgrade() -> None:
    """Drop the constraints. Lines merged by the upgrade stay merged."""
    op.drop_constraint(
        "uq_standing_order_line_standing_order_product", "standing_order_line", type_="unique"
    )
    op.drop_constraint("uq_order_line_order_product", "order_line", type_="unique")
