"""Reproducible C1 geometry and one-condition T2 optics exercise.

This is a declared proxy, not a reconstruction of 2013 weather or productivity.
Run from backend/ with:
PYTHONPATH=. uv run --no-project --with numpy python ../scripts/qualification/212/c1_proxy_optics.py
"""

from __future__ import annotations

import json
import math

import numpy as np

from app.modules.process_stack import optics_t2

CASES = {
    "horizontal": {"loops": 3, "tube_length_m": 80.0, "working_volume_m3": 0.56,
                   "illuminated_share": 0.73, "ground_area_m2": 27.0,
                   "areal_g_m2_d": 12.1, "volumetric_g_l_d": 0.65,
                   "tubes_across": 3, "layers": 1},
    "fence": {"loops": 7, "tube_length_m": 80.0, "working_volume_m3": 1.06,
              "illuminated_share": 0.71, "ground_area_m2": 31.0,
              "areal_g_m2_d": 19.4, "volumetric_g_l_d": 0.57,
              "tubes_across": 1, "layers": 7},
}


def exercise() -> dict:
    # Tube ID and loop lengths: S01 methods/Table 3. OD, 50 mm clearance and
    # 400 mm ground clearance: secondary S22 access via de Vree dissertation.
    # Cross-section tube counts are deliberately assumed: loop count does not
    # establish the as-built array. Solar condition and optical constants are
    # sensitivity assumptions, not observations from the 2013 campaign.
    condition = {"sun_elevation_deg": 45.0, "sun_azimuth_deg": 90.0,
                 "dni_par_umol_m2_s": 700.0, "dhi_par_umol_m2_s": 100.0,
                 "axis_azimuth_deg": 0.0, "n_wall": 1.49, "n_water": 1.33,
                 "ground_albedo": 0.2}
    output = {"scope": "one-condition optical proxy; no biomass prediction",
              "model_version": optics_t2.VERSION, "condition": condition, "cases": {}}
    for name, case in CASES.items():
        layout = optics_t2.build_layout(
            diameter=0.05, tubes_across=case["tubes_across"], layers=case["layers"],
            pitch_h=0.10, pitch_v=0.10, axis_azimuth=0.0,
            centre_height=0.425, n_wall=1.49, n_water=1.33,
            lower_albedo=0.2)
        optical = optics_t2.array_model(layout).evaluate(
            np.array([math.pi / 4]), np.array([math.pi / 2]),
            np.array([700.0]), np.array([100.0]))
        cylinder_m3 = math.pi * 0.046**2 / 4 * case["loops"] * case["tube_length_m"]
        reported_lit_m3 = case["working_volume_m3"] * case["illuminated_share"]
        areal_mass_g_d = case["areal_g_m2_d"] * case["ground_area_m2"]
        volumetric_mass_g_d = case["volumetric_g_l_d"] * case["working_volume_m3"] * 1000
        output["cases"][name] = {
            "source": "S01 methods/Table 1/Table 3; geometry extras secondary S22",
            "layout_assumption": f"{case['tubes_across']} across x {case['layers']} layers, one representative module",
            "layout_digest": layout.digest(), "tube_cylinder_m3": cylinder_m3,
            "productivity_prediction": None,
            "prediction_status": "unsupported: no source-matched 2013 forcing or CCAP 211/78 card",
            "reported_illuminated_m3": reported_lit_m3,
            "cylinder_minus_reported_illuminated_m3": cylinder_m3 - reported_lit_m3,
            "areal_implied_mass_g_d": areal_mass_g_d,
            "volumetric_implied_mass_g_d": volumetric_mass_g_d,
            "observed_mass_denominator_residual_g_d": volumetric_mass_g_d - areal_mass_g_d,
            "proxy_intercepted_umol_s_m_per_tube": float(optical["intercepted"][0]),
            "proxy_transmitted_umol_s_m_per_tube": float(optical["transmitted"][0]),
            "proxy_equivalent_par_umol_m2_s": float(optical["i0_eq"][0]),
        }
    return output


if __name__ == "__main__":
    print(json.dumps(exercise(), indent=2, sort_keys=True, allow_nan=False))
