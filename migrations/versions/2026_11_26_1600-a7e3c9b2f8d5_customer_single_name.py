"""customer: replace first_name and last_name with a single name

Revision ID: a7e3c9b2f8d5
Revises: f1b6d3e9a4c2
Create Date: 2026-11-26 16:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = 'a7e3c9b2f8d5'
down_revision: Union[str, Sequence[str], None] = 'f1b6d3e9a4c2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Merge first and last names into one column.

    Fails (rather than truncating) if a combined name is over 100 characters.
    """
    op.add_column('customer', sa.Column('name', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=True))
    op.execute("UPDATE customer SET name = trim(concat_ws(' ', first_name, last_name))")
    op.alter_column('customer', 'name', nullable=False)
    op.drop_column('customer', 'last_name')
    op.drop_column('customer', 'first_name')


def downgrade() -> None:
    """Split name at the first space: the first word becomes first_name, the rest last_name.

    Fails if either part is over 50 characters.
    """
    op.add_column('customer', sa.Column('first_name', sqlmodel.sql.sqltypes.AutoString(length=50), nullable=True))
    op.add_column('customer', sa.Column('last_name', sqlmodel.sql.sqltypes.AutoString(length=50), nullable=True))
    op.execute(
        "UPDATE customer SET first_name = split_part(name, ' ', 1), "
        "last_name = trim(substr(name, length(split_part(name, ' ', 1)) + 1))"
    )
    op.alter_column('customer', 'first_name', nullable=False)
    op.alter_column('customer', 'last_name', nullable=False)
    op.drop_column('customer', 'name')
