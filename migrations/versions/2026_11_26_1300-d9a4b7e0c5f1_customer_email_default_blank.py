"""customer email defaults to blank

Revision ID: d9a4b7e0c5f1
Revises: c3d8f1a6e2b4
Create Date: 2026-11-26 13:00:00

"""
from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'd9a4b7e0c5f1'
down_revision: str | Sequence[str] | None = 'c3d8f1a6e2b4'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Default customer.email to '' so rows can be inserted without one."""
    op.alter_column('customer', 'email', server_default='')


def downgrade() -> None:
    """Remove the default. Existing blank emails are left as they are."""
    op.alter_column('customer', 'email', server_default=None)
