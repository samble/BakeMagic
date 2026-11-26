"""Database tables and API schemas.

Each resource follows the SQLModel pattern: a `*Base` with shared fields, the
`table=True` model stored in Postgres, and plain Pydantic schemas for request
bodies (`*Create`, `*Update`) and responses (`*Public`).
"""

from datetime import datetime, timezone
from decimal import Decimal
from enum import StrEnum

from pydantic import field_validator, validate_email
from sqlalchemy import CheckConstraint, DateTime, Index
from sqlmodel import Field, Relationship, SQLModel


# Largest value a Postgres INTEGER column (used for all ids) can hold.
INT32_MAX = 2_147_483_647

# Check constraints, and the API error message for each one when it is violated.
CHECK_CONSTRAINT_MESSAGES = {
    "ck_product_price_non_negative": "Price must be zero or greater",
    "ck_order_line_quantity_positive": "Quantity must be greater than zero",
    "ck_order_line_unit_price_non_negative": "Unit price must be zero or greater",
}


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class PatchSchema(SQLModel):
    """Base for PATCH bodies: a field may be omitted, but not sent as null.

    Fields are typed `X | None = None` only so they can be left out; an explicit
    null would otherwise reach the database (NOT NULL violations) or be ambiguous.
    """

    @field_validator("*", mode="before")
    @classmethod
    def reject_null(cls, value):
        if value is None:
            raise ValueError("null is not allowed; omit the field to leave it unchanged")
        return value


# ---------- Products ----------

class ProductBase(SQLModel):
    code: str = Field(max_length=20, unique=True, index=True)
    name: str = Field(max_length=100)
    description: str | None = Field(default=None, max_length=255)
    price: Decimal = Field(ge=0, max_digits=10, decimal_places=2)
    is_active: bool = True


class Product(ProductBase, table=True):
    __table_args__ = (CheckConstraint("price >= 0", name="ck_product_price_non_negative"),)

    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=utcnow, sa_type=DateTime(timezone=True))


class ProductCreate(ProductBase):
    pass


class ProductUpdate(PatchSchema):
    name: str | None = Field(default=None, max_length=100)
    description: str | None = Field(default=None, max_length=255)
    price: Decimal | None = Field(default=None, ge=0, max_digits=10, decimal_places=2)
    is_active: bool | None = None


class ProductPublic(ProductBase):
    id: int
    created_at: datetime


# ---------- Customers ----------

def blank_or_email(value: str) -> str:
    """Accept "" (no email on file) or a valid address, normalised like EmailStr."""
    return value if value == "" else validate_email(value)[1]


class CustomerBase(SQLModel):
    first_name: str = Field(max_length=50)
    last_name: str = Field(max_length=50)
    # Blank means no email on file. Unique only when non-empty: see ix_customer_email below.
    email: str = Field(default="", max_length=255, sa_column_kwargs={"server_default": ""})
    phone: str | None = Field(default=None, max_length=30)
    address: str | None = Field(default=None, max_length=255)

    _check_email = field_validator("email")(blank_or_email)


class Customer(CustomerBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=utcnow, sa_type=DateTime(timezone=True))

    orders: list["Order"] = Relationship(back_populates="customer")


# Partial unique index: rows with an empty email don't conflict with each other.
Index(
    "ix_customer_email",
    Customer.email,
    unique=True,
    postgresql_where=Customer.email != "",
    sqlite_where=Customer.email != "",
)


class CustomerCreate(CustomerBase):
    pass


class CustomerUpdate(PatchSchema):
    first_name: str | None = Field(default=None, max_length=50)
    last_name: str | None = Field(default=None, max_length=50)
    email: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=30)
    address: str | None = Field(default=None, max_length=255)

    _check_email = field_validator("email")(blank_or_email)


class CustomerPublic(CustomerBase):
    id: int
    created_at: datetime


# ---------- Orders ----------

class OrderStatus(StrEnum):
    created = "created"
    paid = "paid"
    in_progress = "in_progress"
    ready = "ready"
    completed = "completed"
    cancelled = "cancelled"


class OrderLine(SQLModel, table=True):
    __tablename__ = "order_line"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_order_line_quantity_positive"),
        CheckConstraint("unit_price >= 0", name="ck_order_line_unit_price_non_negative"),
    )

    id: int | None = Field(default=None, primary_key=True)
    order_id: int = Field(foreign_key="orders.id", index=True, ondelete="CASCADE")
    product_id: int = Field(foreign_key="product.id", index=True)
    quantity: int = Field(gt=0)
    # Price captured at order time, so later price changes don't rewrite history.
    unit_price: Decimal = Field(max_digits=10, decimal_places=2)

    order: "Order" = Relationship(back_populates="lines")


class Order(SQLModel, table=True):
    __tablename__ = "orders"  # "order" is a reserved word in SQL

    id: int | None = Field(default=None, primary_key=True)
    customer_id: int = Field(foreign_key="customer.id", index=True)
    status: OrderStatus = Field(default=OrderStatus.created, max_length=20)
    notes: str | None = Field(default=None, max_length=255)
    created_at: datetime = Field(default_factory=utcnow, sa_type=DateTime(timezone=True))

    customer: Customer = Relationship(back_populates="orders")
    lines: list[OrderLine] = Relationship(
        back_populates="order", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )

    @property
    def total(self) -> Decimal:
        return sum((line.unit_price * line.quantity for line in self.lines), Decimal("0"))


class OrderLineCreate(SQLModel):
    product_id: int = Field(le=INT32_MAX)
    quantity: int = Field(gt=0)


class OrderCreate(SQLModel):
    customer_id: int = Field(le=INT32_MAX)
    notes: str | None = Field(default=None, max_length=255)
    lines: list[OrderLineCreate] = Field(min_length=1)


class OrderStatusUpdate(SQLModel):
    status: OrderStatus


class OrderLinePublic(SQLModel):
    id: int
    product_id: int
    quantity: int
    unit_price: Decimal


class OrderPublic(SQLModel):
    id: int
    customer_id: int
    status: OrderStatus
    notes: str | None
    created_at: datetime
    lines: list[OrderLinePublic]
    total: Decimal
