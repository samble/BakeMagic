from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends, Path
from sqlmodel import Session, create_engine

from app.config import get_settings
from app.models import INT32_MAX

settings = get_settings()
engine = create_engine(settings.database_url, echo=settings.sql_echo, pool_pre_ping=True)


def get_session() -> Iterator[Session]:
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]


# Path parameter for a row id: ids are Postgres INTEGERs, so larger values can't exist.
IdPath = Annotated[int, Path(le=INT32_MAX)]
