"""Turning database errors into API responses."""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from app.models import CONSTRAINT_MESSAGES


def constraint_violation_message(exc: IntegrityError) -> str | None:
    """The API message for a violated named constraint, or None for other integrity errors.

    Postgres includes the constraint name in the error text for check and unique
    violations. SQLite only does for check constraints.
    """
    text = str(exc.orig)
    for name, message in CONSTRAINT_MESSAGES.items():
        if name in text:
            return message
    return None


async def integrity_error_handler(request: Request, exc: IntegrityError) -> JSONResponse:
    """Report known constraint violations as 422s; anything else stays a 500."""
    message = constraint_violation_message(exc)
    if message is None:
        raise exc
    return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, content={"detail": message})
