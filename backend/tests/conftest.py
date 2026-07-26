# ruff: noqa: E402, I001
from __future__ import annotations

import sys
from collections.abc import Iterator
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
for path in (ROOT / "backend", ROOT / "scripts"):
    path_text = str(path)
    if path_text not in sys.path:
        sys.path.insert(0, path_text)

from app.core.config import DEFAULT_DATA_ROOT, get_settings
from fastapi.testclient import TestClient
from tests.legacy_runner_client import Bundled047TestClient, LegacyRunnerTestClient

_BUNDLED_047_FILE = "test_bluerev_geometry_hydraulics_v0.py"
_LEGACY_RUNNER_FILES = frozenset(
    {
        "test_model_scenario_dof.py",
        "test_python_runner.py",
        "test_python_runner_bluecad_l2.py",
        "test_python_runner_calc_v0.py",
    }
)


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--require-bluecad-real-tools",
        action="store_true",
        default=False,
        help="Fail instead of skipping when the hash-verified Gmsh/CalculiX proof toolchain is unavailable.",
    )


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_call(item: pytest.Item) -> None:
    """Replace only the resolved client argument of named historical tests."""

    client = getattr(item, "funcargs", {}).get("client")
    if not isinstance(client, TestClient):
        return
    filename = Path(str(item.path)).name
    if filename == _BUNDLED_047_FILE:
        item.funcargs["client"] = Bundled047TestClient(client)
    elif filename in _LEGACY_RUNNER_FILES:
        item.funcargs["client"] = LegacyRunnerTestClient(client)


@pytest.fixture(autouse=True)
def isolated_data_root(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[None]:
    isolated_root = tmp_path / "jarvisos-data"

    monkeypatch.setenv("JARVISOS_DATA_ROOT", str(isolated_root))
    get_settings.cache_clear()

    settings = get_settings()
    resolved_root = settings.data_root.resolve()
    resolved_tmp = tmp_path.resolve()
    default_root = DEFAULT_DATA_ROOT.resolve()

    assert resolved_root != default_root, f"data_root still points to default {default_root}"
    assert resolved_tmp in resolved_root.parents or resolved_root == resolved_tmp, (
        f"data_root {resolved_root} is not under tmp_path {resolved_tmp}"
    )

    try:
        yield
    finally:
        get_settings.cache_clear()
