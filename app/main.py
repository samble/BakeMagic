from fastapi import FastAPI, HTTPException, status
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.config import get_settings
from app.db import SessionDep
from app.errors import integrity_error_handler
from app.routers import customers, orders, products, standing_orders

app = FastAPI(title=get_settings().app_name, version="0.1.0")
app.add_exception_handler(IntegrityError, integrity_error_handler)

app.include_router(products.router)
app.include_router(customers.router)
app.include_router(orders.router)
app.include_router(standing_orders.router)


@app.get("/health", tags=["health"])
def health(session: SessionDep):
    """Liveness plus a round trip to the database."""
    try:
        session.exec(text("SELECT 1"))
    except Exception as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Database unavailable") from exc
    return {"status": "ok"}
