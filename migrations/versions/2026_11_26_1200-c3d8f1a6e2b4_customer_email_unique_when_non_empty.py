"""customer email unique only when non-empty

Revision ID: c3d8f1a6e2b4
Revises: 62aeb0f369ab
Create Date: 2026-11-26 12:00:00

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'c3d8f1a6e2b4'
down_revision: str | Sequence[str] | None = '62aeb0f369ab'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Make the unique email index partial, skipping empty strings."""
    op.drop_index('ix_customer_email', table_name='customer')
    op.create_index(
        'ix_customer_email',
        'customer',
        ['email'],
        unique=True,
        postgresql_where=sa.text("email <> ''"),
    )


def downgrade() -> None:
    """Restore the unconditional unique email index.

    Fails if more than one customer has an empty email.
    """
    op.drop_index('ix_customer_email', table_name='customer')
    op.create_index('ix_customer_email', 'customer', ['email'], unique=True)
