"""C1 source arithmetic and bounded optics regression; no biomass validation claim."""

import runpy
from pathlib import Path

import pytest


@pytest.fixture(scope="module")
def c1_output():
    script = Path(__file__).resolve().parents[2] / "scripts/qualification/212/c1_proxy_optics.py"
    return runpy.run_path(str(script))["exercise"]()


def test_c1_published_denominators_remain_distinct(c1_output):
    horizontal = c1_output["cases"]["horizontal"]
    fence = c1_output["cases"]["fence"]

    # Independent arithmetic from S01 methods and Tables 1/3. The horizontal
    # published areal and volumetric means do not close on those denominators.
    assert horizontal["tube_cylinder_m3"] == pytest.approx(0.3988566, abs=1e-6)
    assert fence["tube_cylinder_m3"] == pytest.approx(0.9306654, abs=1e-6)
    assert horizontal["reported_illuminated_m3"] == pytest.approx(0.4088)
    assert fence["reported_illuminated_m3"] == pytest.approx(0.7526)
    assert horizontal["areal_implied_mass_g_d"] == pytest.approx(326.7)
    assert horizontal["volumetric_implied_mass_g_d"] == pytest.approx(364.0)
    assert fence["areal_implied_mass_g_d"] == pytest.approx(601.4)
    assert fence["volumetric_implied_mass_g_d"] == pytest.approx(604.2)
    assert horizontal["observed_mass_denominator_residual_g_d"] == pytest.approx(37.3)
    assert fence["observed_mass_denominator_residual_g_d"] == pytest.approx(2.8)


def test_c1_proxy_executes_both_layouts_without_inventing_productivity(c1_output):
    assert c1_output["model_version"] == "optics_t2.v1"
    assert c1_output["input_digest"] == "c38e2c851f94968b6bf2774b58a6183554952e7dc512d1f66fafd80dcba44877"
    assert set(c1_output["cases"]) == {"horizontal", "fence"}
    for case in c1_output["cases"].values():
        assert case["productivity_prediction"] is None
        assert case["prediction_status"].startswith("unsupported:")
        assert case["proxy_intercepted_umol_s_m_per_tube"] > case["proxy_transmitted_umol_s_m_per_tube"] > 0
        assert case["proxy_equivalent_par_umol_m2_s"] > 0
        assert len(case["layout_digest"]) == 64
    assert c1_output["cases"]["horizontal"]["proxy_intercepted_umol_s_m_per_tube"] == pytest.approx(50.3336, abs=1e-4)
    assert c1_output["cases"]["fence"]["proxy_intercepted_umol_s_m_per_tube"] == pytest.approx(49.8004, abs=1e-4)
