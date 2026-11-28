"""The production app: API under /api, the single-page app everywhere else."""

import importlib
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.db import get_session
from app.main import app as api


@pytest.fixture
def web(tmp_path, monkeypatch, session: Session) -> Iterator[TestClient]:
    (tmp_path / "assets").mkdir()
    (tmp_path / "index.html").write_text('<div id="root"></div>')
    (tmp_path / "assets" / "app.js").write_text("console.log(1)")
    monkeypatch.setenv("BAKEMAGIC_FRONTEND_DIST", str(tmp_path))
    import app.web

    module = importlib.reload(app.web)  # pick up the env var on every test
    api.dependency_overrides[get_session] = lambda: session
    with TestClient(module.app) as client:
        yield client
    api.dependency_overrides.clear()


def test_api_is_under_api_prefix(web: TestClient):
    assert web.get("/api/products").json() == []
    assert web.get("/api/openapi.json").status_code == 200


@pytest.mark.parametrize("path", ["/", "/standing-orders", "/orders/12"])
def test_pages_serve_the_app(web: TestClient, path: str):
    response = web.get(path)
    assert response.status_code == 200
    assert '<div id="root">' in response.text


def test_assets_are_served_and_missing_ones_404(web: TestClient):
    assert web.get("/assets/app.js").text == "console.log(1)"
    assert web.get("/assets/missing.js").status_code == 404


def test_missing_build_fails_fast(tmp_path, monkeypatch):
    monkeypatch.setenv("BAKEMAGIC_FRONTEND_DIST", str(tmp_path))
    with pytest.raises(RuntimeError, match="No frontend build"):
        import app.web

        importlib.reload(app.web)
