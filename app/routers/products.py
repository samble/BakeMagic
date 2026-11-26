from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlmodel import select

from app.db import IdPath, SessionDep
from app.errors import check_violation_message
from app.models import Product, ProductCreate, ProductPublic, ProductUpdate

router = APIRouter(prefix="/products", tags=["products"])


def get_product_or_404(session: SessionDep, product_id: int) -> Product:
    product = session.get(Product, product_id)
    if product is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Product not found")
    return product


@router.post("", response_model=ProductPublic, status_code=status.HTTP_201_CREATED)
def create_product(product_in: ProductCreate, session: SessionDep):
    product = Product.model_validate(product_in)
    session.add(product)
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        if check_violation_message(exc):
            raise  # reported as a 422 by the app's IntegrityError handler
        raise HTTPException(
            status.HTTP_409_CONFLICT, f"Product code {product_in.code!r} already exists"
        ) from exc
    session.refresh(product)
    return product


@router.get("", response_model=list[ProductPublic])
def list_products(
    session: SessionDep,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    active_only: bool = False,
):
    query = select(Product).order_by(Product.id).offset(offset).limit(limit)
    if active_only:
        query = query.where(Product.is_active)
    return session.exec(query).all()


@router.get("/{product_id}", response_model=ProductPublic)
def read_product(product_id: IdPath, session: SessionDep):
    return get_product_or_404(session, product_id)


@router.patch("/{product_id}", response_model=ProductPublic)
def update_product(product_id: IdPath, product_in: ProductUpdate, session: SessionDep):
    product = get_product_or_404(session, product_id)
    product.sqlmodel_update(product_in.model_dump(exclude_unset=True))
    session.add(product)
    session.commit()
    session.refresh(product)
    return product


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: IdPath, session: SessionDep):
    product = get_product_or_404(session, product_id)
    session.delete(product)
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Product is used by existing orders or standing orders; deactivate it instead",
        ) from exc
