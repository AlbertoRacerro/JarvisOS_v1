from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.spa_static import SpaStaticFiles
from app.main import _SPA_RESERVED_ROOT_CLIENT_ROUTES


def test_117_brainstorm_reserved_development_route_serves_spa_exactly(tmp_path: Path) -> None:
    marker = "jarvisos-117-brainstorm-spa"
    (tmp_path / "index.html").write_text(marker, encoding="utf-8")

    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
    app.mount(
        "/",
        SpaStaticFiles(
            directory=tmp_path,
            reserved_roots={"development"},
            reserved_root_client_routes=_SPA_RESERVED_ROOT_CLIENT_ROUTES,
        ),
        name="frontend",
    )
    client = TestClient(app, raise_server_exceptions=False)

    response = client.get("/development/brainstorm", headers={"accept": "text/html"})
    assert response.status_code == 200
    assert marker in response.text

    unknown = client.get("/development/brainstorm/unknown", headers={"accept": "text/html"})
    assert unknown.status_code == 404
    assert marker not in unknown.text

    non_html = client.get("/development/brainstorm", headers={"accept": "application/json"})
    assert non_html.status_code == 404
    assert marker not in non_html.text
