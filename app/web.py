"""Production entry point: the API and the built frontend from one server.

The frontend calls the API at /api/* (the same paths the Vite dev server proxies),
so the API is mounted under /api and every other path serves the single-page app.
Unknown paths fall back to index.html so client-side routes like /standing-orders
load on refresh. Development keeps using app.main with the Vite dev server.
"""

import os
from pathlib import Path

from fastapi import FastAPI
from starlette.exceptions import HTTPException
from starlette.staticfiles import StaticFiles
from starlette.types import Scope

from app.main import app as api

# The `npm run build` output; BAKEMAGIC_FRONTEND_DIST points elsewhere (tests use it).
FRONTEND_DIST = Path(
    os.environ.get("BAKEMAGIC_FRONTEND_DIST")
    or Path(__file__).resolve().parent.parent / "frontend" / "dist"
)


class SPAStaticFiles(StaticFiles):
    """Static files that answer unknown paths with index.html (except missing assets)."""

    async def get_response(self, path: str, scope: Scope):
        try:
            return await super().get_response(path, scope)
        except HTTPException as exc:
            # A missing bundle file should 404, not quietly return HTML.
            if exc.status_code != 404 or path.startswith("assets/"):
                raise
            return await super().get_response("index.html", scope)


def create_app(dist: Path = FRONTEND_DIST) -> FastAPI:
    if not (dist / "index.html").is_file():
        raise RuntimeError(f"No frontend build at {dist}; run `npm run build` in frontend/")
    # A FastAPI (not bare Starlette) wrapper so `fastapi run app/web.py` picks it up;
    # its own docs are off, the API's live at /api/docs.
    web = FastAPI(openapi_url=None, docs_url=None, redoc_url=None)
    web.mount("/api", api)
    web.mount("/", SPAStaticFiles(directory=dist, html=True))
    return web


app = create_app()
