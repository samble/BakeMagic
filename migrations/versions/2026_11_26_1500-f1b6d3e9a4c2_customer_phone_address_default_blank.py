"""customer phone and address default to blank, not null

Revision ID: f1b6d3e9a4c2
Revises: e5f2c8a1d7b3
Create Date: 2026-11-26 15:00:00

"""
from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'f1b6d3e9a4c2'
down_revision: str | Sequence[str] | None = 'e5f2c8a1d7b3'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

COLUMNS = ('phone', 'address')


def upgrade() -> None:
    """Store "not on file" as '' instead of NULL."""
    for column in COLUMNS:
        op.execute(f"UPDATE customer SET {column} = '' WHERE {column} IS NULL")
        op.alter_column('customer', column, nullable=False, server_default='')


def downgrade() -> None:
    """Make the columns nullable again. Blank values are kept as ''."""
    for column in COLUMNS:
        op.alter_column('customer', column, nullable=True, server_default=None)
