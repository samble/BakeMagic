"""seed data: a snapshot of the dev database on 2026-11-26

product: 6 rows
customer: 8 rows
orders: 4 rows
order_line: 8 rows (two lines for one product merged; see migration 2de8cbd4d041)
standing_order: 4 rows
standing_order_line: 8 rows

Revision ID: 5b185ddad4aa
Revises:
Create Date: 2026-11-26 10:17:39.791373

"""
from collections.abc import Sequence
from datetime import UTC, datetime
from decimal import Decimal

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '5b185ddad4aa'
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Lightweight table definitions with just the seeded columns, so this revision
# keeps working as app.models changes. Parents come before children.
TABLES = (
    sa.table(
        'product',
        sa.column('code', sa.String(20)),
        sa.column('name', sa.String(100)),
        sa.column('description', sa.String(255)),
        sa.column('price', sa.Numeric(10, 2)),
        sa.column('is_active', sa.Boolean()),
        sa.column('id', sa.Integer()),
        sa.column('created_at', sa.DateTime(timezone=True)),
    ),
    sa.table(
        'customer',
        sa.column('email', sa.String(255)),
        sa.column('phone', sa.String(30)),
        sa.column('address', sa.String(255)),
        sa.column('id', sa.Integer()),
        sa.column('created_at', sa.DateTime(timezone=True)),
        sa.column('name', sa.String(100)),
    ),
    sa.table(
        'orders',
        sa.column('id', sa.Integer()),
        sa.column('customer_id', sa.Integer()),
        sa.column('status', sa.Enum('created', 'paid', 'in_progress', 'ready', 'completed', 'cancelled', name='orderstatus', create_type=False)),
        sa.column('notes', sa.String(255)),
        sa.column('created_at', sa.DateTime(timezone=True)),
    ),
    sa.table(
        'order_line',
        sa.column('id', sa.Integer()),
        sa.column('order_id', sa.Integer()),
        sa.column('product_id', sa.Integer()),
        sa.column('quantity', sa.Integer()),
        sa.column('unit_price', sa.Numeric(10, 2)),
    ),
    sa.table(
        'standing_order',
        sa.column('id', sa.Integer()),
        sa.column('customer_id', sa.Integer()),
        sa.column('sun', sa.Boolean()),
        sa.column('mon', sa.Boolean()),
        sa.column('tue', sa.Boolean()),
        sa.column('wed', sa.Boolean()),
        sa.column('thu', sa.Boolean()),
        sa.column('fri', sa.Boolean()),
        sa.column('sat', sa.Boolean()),
        sa.column('notes', sa.String(255)),
        sa.column('is_active', sa.Boolean()),
        sa.column('created_at', sa.DateTime(timezone=True)),
    ),
    sa.table(
        'standing_order_line',
        sa.column('id', sa.Integer()),
        sa.column('standing_order_id', sa.Integer()),
        sa.column('product_id', sa.Integer()),
        sa.column('quantity', sa.Integer()),
    ),
)

# Rows keep their original ids so foreign keys between them line up.
SEED_ROWS = {
    'product': [
        {'code': 'SCONE-PLAIN', 'name': 'Plain scone', 'description': None, 'price': Decimal("6.00"), 'is_active': True, 'id': 1, 'created_at': datetime(2026, 11, 26, 0, 36, 36, 863214, tzinfo=UTC)},
        {'code': 'SCONE-CHOC', 'name': 'Chocolate Scone', 'description': None, 'price': Decimal("6.00"), 'is_active': True, 'id': 2, 'created_at': datetime(2026, 11, 26, 15, 10, 48, 691218, tzinfo=UTC)},
        {'code': 'BREAD-WHITE', 'name': 'White Sandwhich Loaf', 'description': None, 'price': Decimal("8.00"), 'is_active': True, 'id': 3, 'created_at': datetime(2026, 11, 26, 15, 11, 12, 398791, tzinfo=UTC)},
        {'code': 'BREAD-WHEAT', 'name': 'Wheat Sandwich Loaf', 'description': None, 'price': Decimal("8.00"), 'is_active': True, 'id': 4, 'created_at': datetime(2026, 11, 26, 15, 11, 26, 464690, tzinfo=UTC)},
        {'code': 'HEARTH-SESAME', 'name': 'Sesame Semolina Hearth Loaf', 'description': None, 'price': Decimal("8.00"), 'is_active': True, 'id': 5, 'created_at': datetime(2026, 11, 26, 15, 11, 47, 97498, tzinfo=UTC)},
        {'code': 'HEARTH-OLIVE', 'name': 'Hearth Olive Loaf', 'description': None, 'price': Decimal("8.00"), 'is_active': True, 'id': 6, 'created_at': datetime(2026, 11, 26, 15, 12, 2, 578422, tzinfo=UTC)},
    ],
    'customer': [
        {'email': 'test.customerman@example.com', 'phone': '', 'address': '', 'id': 1, 'created_at': datetime(2026, 11, 26, 0, 36, 15, 703537, tzinfo=UTC), 'name': 'Test Customerman'},
        {'email': 'testerman.email@example.com', 'phone': '', 'address': '', 'id': 2, 'created_at': datetime(2026, 11, 26, 15, 7, 29, 573092, tzinfo=UTC), 'name': 'Email Testerman'},
        {'email': '', 'phone': '1234567890', 'address': '', 'id': 3, 'created_at': datetime(2026, 11, 26, 15, 7, 40, 127662, tzinfo=UTC), 'name': 'Phone Testerman'},
        {'email': '', 'phone': '', 'address': '123 Main St, Beverly Hills CA 90210', 'id': 4, 'created_at': datetime(2026, 11, 26, 15, 7, 53, 957620, tzinfo=UTC), 'name': 'Address Testerman'},
        {'email': 'phoneguy@example.com', 'phone': '12345678769899', 'address': '', 'id': 5, 'created_at': datetime(2026, 11, 26, 15, 8, 30, 393030, tzinfo=UTC), 'name': 'Phone and Email testerman'},
        {'email': '', 'phone': '1234567891', 'address': '443 Depot Street, New York City NY 04238', 'id': 6, 'created_at': datetime(2026, 11, 26, 15, 9, 11, 333013, tzinfo=UTC), 'name': 'Phone Address Testerman'},
        {'email': 'addressguy@example.com', 'phone': '', 'address': '999 No Name Rd, Arlington VT 04221', 'id': 7, 'created_at': datetime(2026, 11, 26, 15, 9, 42, 85385, tzinfo=UTC), 'name': 'Email and adderss testerman'},
        {'email': 'all3@example.com', 'phone': '348384939080', 'address': '10011 Binary Drive, Xiangxu, Schenzen Province China', 'id': 8, 'created_at': datetime(2026, 11, 26, 15, 10, 34, 625470, tzinfo=UTC), 'name': 'All Three Incorporated'},
    ],
    'orders': [
        {'id': 1, 'customer_id': 3, 'status': 'in_progress', 'notes': None, 'created_at': datetime(2026, 11, 26, 15, 13, 39, 374081, tzinfo=UTC)},
        {'id': 2, 'customer_id': 2, 'status': 'paid', 'notes': None, 'created_at': datetime(2026, 11, 26, 15, 13, 51, 898576, tzinfo=UTC)},
        {'id': 3, 'customer_id': 7, 'status': 'created', 'notes': 'You can email them', 'created_at': datetime(2026, 11, 26, 15, 14, 21, 99149, tzinfo=UTC)},
        {'id': 4, 'customer_id': 4, 'status': 'in_progress', 'notes': 'This one is ready', 'created_at': datetime(2026, 11, 26, 15, 14, 53, 326467, tzinfo=UTC)},
    ],
    'order_line': [
        {'id': 1, 'order_id': 1, 'product_id': 1, 'quantity': 5, 'unit_price': Decimal("6.00")},
        {'id': 2, 'order_id': 1, 'product_id': 3, 'quantity': 3, 'unit_price': Decimal("8.00")},
        {'id': 3, 'order_id': 2, 'product_id': 1, 'quantity': 1, 'unit_price': Decimal("6.00")},
        {'id': 4, 'order_id': 2, 'product_id': 2, 'quantity': 4, 'unit_price': Decimal("6.00")},
        {'id': 5, 'order_id': 3, 'product_id': 1, 'quantity': 1, 'unit_price': Decimal("6.00")},
        {'id': 6, 'order_id': 4, 'product_id': 1, 'quantity': 2, 'unit_price': Decimal("6.00")},
        {'id': 7, 'order_id': 4, 'product_id': 2, 'quantity': 2, 'unit_price': Decimal("6.00")},
        {'id': 9, 'order_id': 4, 'product_id': 3, 'quantity': 1, 'unit_price': Decimal("8.00")},
    ],
    'standing_order': [
        {'id': 2, 'customer_id': 1, 'sun': True, 'mon': False, 'tue': False, 'wed': True, 'thu': False, 'fri': True, 'sat': False, 'notes': None, 'is_active': True, 'created_at': datetime(2026, 11, 26, 14, 38, 7, 641055, tzinfo=UTC)},
        {'id': 3, 'customer_id': 3, 'sun': False, 'mon': True, 'tue': True, 'wed': False, 'thu': True, 'fri': False, 'sat': False, 'notes': 'Call em on they cell phone', 'is_active': True, 'created_at': datetime(2026, 11, 26, 15, 12, 35, 810921, tzinfo=UTC)},
        {'id': 4, 'customer_id': 7, 'sun': True, 'mon': True, 'tue': True, 'wed': True, 'thu': True, 'fri': True, 'sat': True, 'notes': None, 'is_active': True, 'created_at': datetime(2026, 11, 26, 15, 13, 0, 323833, tzinfo=UTC)},
        {'id': 5, 'customer_id': 8, 'sun': False, 'mon': False, 'tue': True, 'wed': False, 'thu': False, 'fri': False, 'sat': False, 'notes': None, 'is_active': True, 'created_at': datetime(2026, 11, 26, 15, 13, 20, 906916, tzinfo=UTC)},
    ],
    'standing_order_line': [
        {'id': 2, 'standing_order_id': 2, 'product_id': 1, 'quantity': 5},
        {'id': 3, 'standing_order_id': 3, 'product_id': 1, 'quantity': 3},
        {'id': 4, 'standing_order_id': 3, 'product_id': 3, 'quantity': 5},
        {'id': 5, 'standing_order_id': 3, 'product_id': 6, 'quantity': 3},
        {'id': 6, 'standing_order_id': 4, 'product_id': 3, 'quantity': 4},
        {'id': 7, 'standing_order_id': 4, 'product_id': 5, 'quantity': 6},
        {'id': 8, 'standing_order_id': 5, 'product_id': 6, 'quantity': 2},
        {'id': 9, 'standing_order_id': 5, 'product_id': 2, 'quantity': 6},
    ],
}


def reset_id_sequences() -> None:
    """Move each id sequence past the highest id, since rows were inserted with explicit ids."""
    for table in TABLES:
        op.execute(
            f"SELECT setval(pg_get_serial_sequence('{table.name}', 'id'), "
            f"COALESCE((SELECT MAX(id) FROM {table.name}), 0) + 1, false)"
        )


def upgrade() -> None:
    """Insert the seed rows. Fails if any of these ids already exist."""
    for table in TABLES:
        op.bulk_insert(table, SEED_ROWS[table.name])
    reset_id_sequences()


def downgrade() -> None:
    """Delete the seeded rows by id, children first. Rows added since are kept."""
    for table in reversed(TABLES):
        ids = [row["id"] for row in SEED_ROWS[table.name]]
        op.execute(table.delete().where(table.c.id.in_(ids)))
    reset_id_sequences()
