from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlmodel import select

from app.db import IdPath, SessionDep
from app.models import Customer, CustomerCreate, CustomerPublic, CustomerUpdate

router = APIRouter(prefix="/customers", tags=["customers"])


def get_customer_or_404(session: SessionDep, customer_id: int) -> Customer:
    customer = session.get(Customer, customer_id)
    if customer is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Customer not found")
    return customer


def commit_or_409(session: SessionDep) -> None:
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(
            status.HTTP_409_CONFLICT, "A customer with that email already exists"
        ) from exc


@router.post("", response_model=CustomerPublic, status_code=status.HTTP_201_CREATED)
def create_customer(customer_in: CustomerCreate, session: SessionDep):
    customer = Customer.model_validate(customer_in)
    session.add(customer)
    commit_or_409(session)
    session.refresh(customer)
    return customer


@router.get("", response_model=list[CustomerPublic])
def list_customers(
    session: SessionDep,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    return session.exec(select(Customer).order_by(Customer.id).offset(offset).limit(limit)).all()


@router.get("/{customer_id}", response_model=CustomerPublic)
def read_customer(customer_id: IdPath, session: SessionDep):
    return get_customer_or_404(session, customer_id)


@router.patch("/{customer_id}", response_model=CustomerPublic)
def update_customer(customer_id: IdPath, customer_in: CustomerUpdate, session: SessionDep):
    customer = get_customer_or_404(session, customer_id)
    customer.sqlmodel_update(customer_in.model_dump(exclude_unset=True))
    session.add(customer)
    commit_or_409(session)
    session.refresh(customer)
    return customer
