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

_BUNDLED_047_MODULE = "tests.test_bluerev_geometry_hydraulics_v0"
_LEGACY_RUNNER_MODULES = frozenset(
    {
        "tests.test_model_scenario_dof",
        "tests.test_python_runner",
        "tests.test_python_runner_bluecad_l2",
        "tests.test_python_runner_calc_v0",
    }
)


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--require-bluecad-real-tools",
        action="store_true",
        default=False,
        help="Fail instead of skipping when the hash-verified Gmsh/CalculiX proof toolchain is unavailable.",
    )


@pytest.hookimpl(hookwrapper=True)
def pytest_fixture_setup(fixturedef, request):
    """Scope legacy runner adapters to the exact historical test modules."""

    outcome = yield
    if fixturedef.argname != "client":
        return
    result = outcome.get_result()
    if not isinstance(result, TestClient):
        return
    module = getattr(request.node, "module", None)
    module_name = getattr(module, "__name__", "")
    if module_name == _BUNDLED_047_MODULE:
        outcome.force_result(Bundled047TestClient(result))
    elif module_name in _LEGACY_RUNNER_MODULES:
        outcome.force_result(LegacyRunnerTestClient(result))


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
