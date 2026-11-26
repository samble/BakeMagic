from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy.orm import selectinload
from sqlmodel import select

from app.db import IdPath, SessionDep
from app.models import (
    INT32_MAX,
    Order,
    OrderCreate,
    OrderLine,
    OrderPublic,
    OrderStatus,
    OrderStatusUpdate,
)
from app.routers.common import require_active_products, require_customer

router = APIRouter(prefix="/orders", tags=["orders"])


def get_order_or_404(session: SessionDep, order_id: int) -> Order:
    order = session.get(Order, order_id, options=[selectinload(Order.lines)])
    if order is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Order not found")
    return order


@router.post("", response_model=OrderPublic, status_code=status.HTTP_201_CREATED)
def create_order(order_in: OrderCreate, session: SessionDep):
    require_customer(session, order_in.customer_id)
    products = require_active_products(session, {line.product_id for line in order_in.lines})

    order = Order(
        customer_id=order_in.customer_id,
        notes=order_in.notes,
        lines=[
            OrderLine(
                product_id=line.product_id,
                quantity=line.quantity,
                unit_price=products[line.product_id].price,
            )
            for line in order_in.lines
        ],
    )
    session.add(order)
    session.commit()
    return get_order_or_404(session, order.id)


@router.get("", response_model=list[OrderPublic])
def list_orders(
    session: SessionDep,
    customer_id: int | None = Query(None, le=INT32_MAX),
    order_status: OrderStatus | None = Query(None, alias="status"),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    query = select(Order).options(selectinload(Order.lines)).order_by(Order.id.desc())
    if customer_id is not None:
        query = query.where(Order.customer_id == customer_id)
    if order_status is not None:
        query = query.where(Order.status == order_status)
    return session.exec(query.offset(offset).limit(limit)).all()


@router.get("/{order_id}", response_model=OrderPublic)
def read_order(order_id: IdPath, session: SessionDep):
    return get_order_or_404(session, order_id)


@router.patch("/{order_id}/status", response_model=OrderPublic)
def update_order_status(order_id: IdPath, status_in: OrderStatusUpdate, session: SessionDep):
    order = get_order_or_404(session, order_id)
    if order.status in (OrderStatus.completed, OrderStatus.cancelled):
        raise HTTPException(status.HTTP_409_CONFLICT, f"Order is already {order.status}")
    order.status = status_in.status
    session.add(order)
    session.commit()
    return get_order_or_404(session, order_id)
