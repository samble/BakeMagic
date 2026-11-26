"""Turning database errors into API responses."""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from app.models import CHECK_CONSTRAINT_MESSAGES


def check_violation_message(exc: IntegrityError) -> str | None:
    """The API message for a violated check constraint, or None for other integrity errors.

    Postgres and SQLite both include the constraint name in the error text.
    """
    text = str(exc.orig)
    for name, message in CHECK_CONSTRAINT_MESSAGES.items():
        if name in text:
            return message
    return None


async def integrity_error_handler(request: Request, exc: IntegrityError) -> JSONResponse:
    """Report check constraint violations as 422s; anything else stays a 500."""
    message = check_violation_message(exc)
    if message is None:
        raise exc
    return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, content={"detail": message})
