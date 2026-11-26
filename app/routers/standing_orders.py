from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy.orm import selectinload
from sqlmodel import select

from app.db import IdPath, SessionDep
from app.models import (
    INT32_MAX,
    StandingOrder,
    StandingOrderCreate,
    StandingOrderLine,
    StandingOrderLineCreate,
    StandingOrderPublic,
    StandingOrderUpdate,
    Weekday,
)
from app.routers.common import require_active_products, require_customer

router = APIRouter(prefix="/standing-orders", tags=["standing orders"])


def get_standing_order_or_404(session: SessionDep, standing_order_id: int) -> StandingOrder:
    standing_order = session.get(
        StandingOrder, standing_order_id, options=[selectinload(StandingOrder.lines)]
    )
    if standing_order is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Standing order not found")
    return standing_order


def build_lines(session: SessionDep, lines: list[StandingOrderLineCreate]) -> list[StandingOrderLine]:
    require_active_products(session, {line.product_id for line in lines})
    return [StandingOrderLine(product_id=line.product_id, quantity=line.quantity) for line in lines]


@router.post("", response_model=StandingOrderPublic, status_code=status.HTTP_201_CREATED)
def create_standing_order(standing_order_in: StandingOrderCreate, session: SessionDep):
    require_customer(session, standing_order_in.customer_id)
    standing_order = StandingOrder(
        customer_id=standing_order_in.customer_id,
        notes=standing_order_in.notes,
        is_active=standing_order_in.is_active,
        lines=build_lines(session, standing_order_in.lines),
    )
    standing_order.set_days(standing_order_in.days)
    session.add(standing_order)
    session.commit()
    return get_standing_order_or_404(session, standing_order.id)


@router.get("", response_model=list[StandingOrderPublic])
def list_standing_orders(
    session: SessionDep,
    customer_id: int | None = Query(None, le=INT32_MAX),
    day: Weekday | None = None,
    active_only: bool = False,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    query = (
        select(StandingOrder)
        .options(selectinload(StandingOrder.lines))
        .order_by(StandingOrder.id)
    )
    if customer_id is not None:
        query = query.where(StandingOrder.customer_id == customer_id)
    if day is not None:
        query = query.where(getattr(StandingOrder, day.value))
    if active_only:
        query = query.where(StandingOrder.is_active)
    return session.exec(query.offset(offset).limit(limit)).all()


@router.get("/{standing_order_id}", response_model=StandingOrderPublic)
def read_standing_order(standing_order_id: IdPath, session: SessionDep):
    return get_standing_order_or_404(session, standing_order_id)


@router.patch("/{standing_order_id}", response_model=StandingOrderPublic)
def update_standing_order(
    standing_order_id: IdPath, standing_order_in: StandingOrderUpdate, session: SessionDep
):
    standing_order = get_standing_order_or_404(session, standing_order_id)
    changes = standing_order_in.model_dump(exclude_unset=True, exclude={"days", "lines"})
    standing_order.sqlmodel_update(changes)
    if standing_order_in.days is not None:
        standing_order.set_days(standing_order_in.days)
    if standing_order_in.lines is not None:
        standing_order.lines = build_lines(session, standing_order_in.lines)
    session.add(standing_order)
    session.commit()
    return get_standing_order_or_404(session, standing_order_id)


@router.delete("/{standing_order_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_standing_order(standing_order_id: IdPath, session: SessionDep):
    session.delete(get_standing_order_or_404(session, standing_order_id))
    session.commit()
