"""Spec 214 acceptance 3: both spec 212 C1 layouts rebuilt in the Design shell reproduce the 212 proxy."""

import runpy
from pathlib import Path

import pytest

REFERENCE_LAYOUTS = {
    "horizontal": "299d44fa051c4d4e22d5f05cd6030897da2ffe94d9130f34a3d9bb15c25271a1",
    "fence": "bf9fefe9a10c391d51d4d851e12a7e03b9e81a702142a789d69032b23dffeeb8",
}


@pytest.fixture(scope="module")
def parity_output(tmp_path_factory: pytest.TempPathFactory) -> dict:
    root = tmp_path_factory.mktemp("c1-shell")
    with pytest.MonkeyPatch.context() as patch:
        from app.core.config import get_settings

        patch.setenv("JARVISOS_DATA_ROOT", str(root / "data"))
        get_settings.cache_clear()
        script = Path(__file__).resolve().parents[2] / "scripts/qualification/214/c1_shell_parity.py"
        try:
            yield runpy.run_path(str(script))["parity"]()
        finally:
            get_settings.cache_clear()


def test_shell_rebuild_reproduces_212_inputs_and_optics_exactly(parity_output: dict) -> None:
    assert parity_output["reference"]["input_digest"] == (
        "c38e2c851f94968b6bf2774b58a6183554952e7dc512d1f66fafd80dcba44877")
    assert parity_output["parity_exact"] is True
    for name, case in parity_output["cases"].items():
        assert case["component_source"]["linked"] is True
        assert case["tube_cylinder_minus_212_m3"] == 0
        recorded = case["runs"]["recorded_212_setup"]
        assert recorded["layout_digest"] == REFERENCE_LAYOUTS[name]
        assert recorded["model_version"] == "optics_t2.v1"
        assert all(item["minus_212"] == 0 for item in recorded["outputs"].values())
        assert case["productivity_prediction"] is None


def test_shell_reports_existing_owner_limits_instead_of_hiding_them(parity_output: dict) -> None:
    for case in parity_output["cases"].values():
        # The Process T2 owner uses the inner diameter optically; 212 used the outer diameter.
        owner = case["runs"]["process_t2_owner"]
        assert owner["diameter_m"] == 0.046 and owner["layout_digest"] != case["reference_layout_digest"]
        assert owner["outputs"]["proxy_intercepted_umol_s_m_per_tube"]["minus_212"] < 0
        # An 80 m loop maps to the tube template but exceeds its 5 m range; nothing is attached.
        geometry = case["geometry"]
        assert geometry["mapping"]["supported"] is True and geometry["mapping"]["length_mm"] == 80000
        assert geometry["deepen_status"] == 422 and "5000" in geometry["deepen_detail"]
