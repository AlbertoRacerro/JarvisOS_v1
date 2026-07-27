from __future__ import annotations

import importlib.util
from collections.abc import Iterator
from pathlib import Path
from types import ModuleType

import pytest
from fastapi.testclient import TestClient

from app.core.database import open_sqlite_connection


def _load_preview_support() -> ModuleType:
    path = Path(__file__).parents[1] / "test_cad_link_topology_preview.py"
    spec = importlib.util.spec_from_file_location("cad_link_074_preview_recheck_support", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SUPPORT = _load_preview_support()


@pytest.fixture
def client(tmp_path, monkeypatch) -> Iterator[TestClient]:
    monkeypatch.setenv("JARVISOS_DATA_ROOT", str(tmp_path / "JarvisOS"))
    monkeypatch.setenv("DATABASE_URL", "must-not-enter-cad-link-074-transaction-recheck")
    from app.core.config import get_settings

    get_settings.cache_clear()
    from app.core.bootstrap import initialize_storage
    from app.main import create_app

    initialize_storage(seed_default=True)
    with TestClient(create_app()) as test_client:
        yield test_client
    get_settings.cache_clear()


def test_short_writer_transaction_recheck_preserves_fresh_preview_identity(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.modules.bluecad import cad_link_topology

    simulation_run_id = SUPPORT._create_source_run(client)
    request = cad_link_topology.CadLink072PreviewRequest(
        source_simulation_run_id=simulation_run_id,
        layout_spec=SUPPORT._layout(),
        analysis_spec=None,
    )
    monkeypatch.setattr(
        cad_link_topology,
        "run_kernel_preflight",
        SUPPORT._fake_preflight,
    )
    initial = cad_link_topology.preview_cad_link_072("bluerev", request)

    def fail_if_called(*_args, **_kwargs):
        raise AssertionError("kernel work is forbidden inside the SQLite writer transaction")

    monkeypatch.setattr(cad_link_topology, "run_kernel_preflight", fail_if_called)
    with open_sqlite_connection() as connection:
        connection.execute("BEGIN IMMEDIATE")
        try:
            current = cad_link_topology._rebuild_preview_without_kernel(
                connection,
                "bluerev",
                request,
                initial["kernel_preflight"],
            )
        finally:
            connection.rollback()

    assert current["source_snapshot"] == initial["source_snapshot"]
    assert current["resolved_spec"] == initial["resolved_spec"]
    assert current["reconciliation"] == initial["reconciliation"]
    assert current["preview_digest"] == initial["preview_digest"]
