"""Declared C1 geometry/operation scenarios; no biomass prediction.

Run ``python3 scripts/qualification/215/scenario_inputs.py`` from the repo root.
Source values and unresolved residuals are audited in the spec 212 evidence.
"""

from __future__ import annotations

import hashlib
import json
import math

# S01 methods and Tables 1/3. The two productivity measurements are retained
# independently because their implied daily biomass does not close for the
# horizontal layout. Secondary S22 supplies the outer diameter and pitch.
LAYOUTS = {
    "horizontal": {"loops": 3, "tube_length_m": 80.0, "working_volume_m3": 0.56,
                   "illuminated_share": 0.73, "ground_area_m2": 27.0,
                   "dilution_per_day": 0.25, "observed_areal_g_m2_day": 12.1,
                   "observed_volumetric_g_l_day": 0.65,
                   "cross_sections": ((3, 1), (1, 3))},
    "fence": {"loops": 7, "tube_length_m": 80.0, "working_volume_m3": 1.06,
              "illuminated_share": 0.71, "ground_area_m2": 31.0,
              "dilution_per_day": 0.27, "observed_areal_g_m2_day": 19.4,
              "observed_volumetric_g_l_day": 0.57,
              "cross_sections": ((1, 7), (2, 4))},
}
TUBE_INNER_DIAMETER_M = 0.046
TUBE_OUTER_DIAMETER_M = 0.050
TUBE_PITCH_M = 0.100
TUBE_CENTRE_HEIGHT_M = 0.425
# S01 gives no measured array azimuth. These are explicit sensitivity cases.
AXIS_AZIMUTHS_DEG = (0.0, 45.0, 90.0)


def build_inputs() -> dict:
    layouts = {}
    scenarios = []
    for name, row in LAYOUTS.items():
        tube_volume = math.pi * TUBE_INNER_DIAMETER_M**2 / 4 * row["loops"] * row["tube_length_m"]
        reported_lit_volume = row["working_volume_m3"] * row["illuminated_share"]
        areal_mass = row["observed_areal_g_m2_day"] * row["ground_area_m2"]
        volumetric_mass = row["observed_volumetric_g_l_day"] * row["working_volume_m3"] * 1000
        layouts[name] = {
            "source": "S01 methods and Tables 1/3; OD/pitch/height secondary S22",
            "working_volume_m3": row["working_volume_m3"],
            "ground_area_m2": row["ground_area_m2"],
            "dilution_per_day": row["dilution_per_day"],
            "tube_inner_diameter_m": TUBE_INNER_DIAMETER_M,
            "tube_outer_diameter_m": TUBE_OUTER_DIAMETER_M,
            "tube_pitch_m": TUBE_PITCH_M,
            "tube_centre_height_m": TUBE_CENTRE_HEIGHT_M,
            "tube_cylinder_volume_m3": tube_volume,
            "reported_illuminated_volume_m3": reported_lit_volume,
            "tube_minus_reported_illuminated_m3": tube_volume - reported_lit_volume,
            "observed_areal_g_m2_day": row["observed_areal_g_m2_day"],
            "observed_volumetric_g_l_day": row["observed_volumetric_g_l_day"],
            "observed_areal_implied_g_day": areal_mass,
            "observed_volumetric_implied_g_day": volumetric_mass,
            "observed_mass_residual_g_day": volumetric_mass - areal_mass,
            "carbon": "non-limiting; S01 pH-controlled CO2 (assumed model condition)",
            "oxygen": "active removal in S01; no resolved oxygen-inhibition model",
            "culture_temperature_c": "bounded scenario required: 20-30, no measured time series",
        }
        for across, layers in row["cross_sections"]:
            for azimuth in AXIS_AZIMUTHS_DEG:
                for volume_basis, illuminated_volume in (
                    ("reported_illuminated_share", reported_lit_volume),
                    ("tube_cylinder", tube_volume),
                ):
                    scenarios.append({
                        "layout": name, "tubes_across": across, "layers": layers,
                        "axis_azimuth_deg": azimuth,
                        "illuminated_volume_basis": volume_basis,
                        "illuminated_volume_m3": illuminated_volume,
                        "cross_section_state": "assumed; not as-built",
                        "azimuth_state": "scenario; not measured",
                        "volume_state": "S01 convention or calculated cylinder; residual retained",
                    })
    payload = {"status": "declared assumptions; no biomass prediction or C1 verdict",
               "layouts": layouts, "scenarios": scenarios}
    payload["input_sha256"] = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()
    return payload


if __name__ == "__main__":
    print(json.dumps(build_inputs(), indent=2, sort_keys=True, allow_nan=False))
