"""Checks shared by the order and standing order endpoints."""

from fastapi import HTTPException, status
from sqlmodel import select

from app.db import SessionDep
from app.models import Customer, Product


def require_customer(session: SessionDep, customer_id: int) -> Customer:
    customer = session.get(Customer, customer_id)
    if customer is None:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Customer does not exist")
    return customer


def require_active_products(session: SessionDep, product_ids: set[int]) -> dict[int, Product]:
    """Load the given products by id, or 422 if any are unknown or inactive."""
    products = {
        p.id: p for p in session.exec(select(Product).where(Product.id.in_(product_ids))).all()
    }
    missing = sorted(product_ids - products.keys())
    if missing:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, f"Unknown product ids: {missing}")
    inactive = sorted(pid for pid, p in products.items() if not p.is_active)
    if inactive:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, f"Inactive product ids: {inactive}")
    return products
