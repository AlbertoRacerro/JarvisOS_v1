"""One central declared-assumption C1 run per layout through 169/170/171/172/174.

Run from ``backend/`` in an isolated data root (the call creates a workspace)::

    PYTHONPATH=. python ../scripts/qualification/215/central_run.py

This is the deterministic centre of the later sensitivity/Monte Carlo band, not
the band itself and not a verdict. Every value below is a declared assumption or
an S01/S22 source value; nothing is fitted to the C1 observations.
"""

from __future__ import annotations

import hashlib
import json
import math
import runpy
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
_INPUTS = runpy.run_path(str(HERE / "scenario_inputs.py"))
LAYOUTS = _INPUTS["LAYOUTS"]

# Central screening choices. Ranges belong to the later sensitivity analysis.
CENTRAL = {
    "forcing_window": "median",
    "culture_temperature_c": 25.0,
    "axis_azimuth_deg": 0.0,
    "cross_section": {"horizontal": (3, 1), "fence": (1, 7)},
    "illuminated_volume_basis": "tube_cylinder",
    "initial_biomass_kg_m3": 1.0,
    "feed_nitrogen_kg_n_m3": 0.5,
    "liquid_velocity_m_s": 0.3,
    "oxygen_kla_per_h": 20.0,
    "n_wall": 1.49,
    "n_water": 1.33,
    "ground_albedo": 0.2,
    "salinity_g_kg": 35.0,
}
STATES = {
    "forcing_window": "scenario; surrogate KNMI Deelen median-PAR 36-day window",
    "culture_temperature_c": "assumed constant inside S01's maintained 20-30 C",
    "axis_azimuth_deg": "scenario; S01 gives no array azimuth",
    "cross_section": "assumed representative optical module; not as-built",
    "illuminated_volume_basis": "calculated tube cylinder; S01 illuminated share kept as alternative",
    "initial_biomass_kg_m3": "assumed start; S01 reports no aligned initial state",
    "feed_nitrogen_kg_n_m3": "assumed nutrient-replete feed; S01 gives no medium N concentration",
    "liquid_velocity_m_s": "assumed circulation; changes hydraulics, not the well-mixed biology",
    "oxygen_kla_per_h": "assumed; S01 reports active O2 removal and the card has no O2 inhibition",
    "n_wall": "assumed PMMA-like wall index, as in the 212 proxy",
    "n_water": "assumed",
    "ground_albedo": "assumed, as in the 212 proxy",
    "salinity_g_kg": "assumed marine medium",
}


def _q(value: float, unit: str) -> dict[str, Any]:
    return {"value": value, "unit": unit}


def _case(window: dict, layout: str) -> dict[str, Any]:
    row = LAYOUTS[layout]
    tube_volume = math.pi * _INPUTS["TUBE_INNER_DIAMETER_M"] ** 2 / 4 * row["loops"] * row["tube_length_m"]
    dark_volume = row["working_volume_m3"] - tube_volume
    if dark_volume <= 0:
        raise ValueError("Working volume must exceed the illuminated tube volume")
    across, layers = CENTRAL["cross_section"][layout]
    return {
        "layout": layout, "tubes_across": across, "layers": layers,
        "tube_count": row["loops"], "tube_length_m": row["tube_length_m"],
        "illuminated_volume_m3": tube_volume, "dark_volume_m3": dark_volume,
        "working_volume_m3": row["working_volume_m3"], "ground_area_m2": row["ground_area_m2"],
        "dilution_per_day": row["dilution_per_day"],
        "feed_m3_s": row["dilution_per_day"] * row["working_volume_m3"] / 86400.0,
        "circulation_m3_s": CENTRAL["liquid_velocity_m_s"] * row["loops"]
        * math.pi * _INPUTS["TUBE_INNER_DIAMETER_M"] ** 2 / 4,
        "start_utc": window["start_utc"], "end_utc": window["end_utc"],
    }


def _ops(case: dict[str, Any], card: dict[str, Any], profile: dict[str, Any]) -> list[Any]:
    from app.modules.process_stack.draft_models import (
        AddStream,
        AddUnit,
        Connect,
        SetScenario,
        SetStreamCulture,
        SetStreamSpec,
        SetThermo,
        SetUnitModel,
        SetUnitParams,
    )

    temperature_k = CENTRAL["culture_temperature_c"] + 273.15
    pbr = {
        "tube_inner_diameter": _q(_INPUTS["TUBE_INNER_DIAMETER_M"], "m"),
        "tube_length": _q(case["tube_length_m"], "m"),
        "tube_count": _q(case["tube_count"], "dimensionless"),
        "liquid_velocity": _q(CENTRAL["liquid_velocity_m_s"], "m/s"),
        "pump_efficiency": _q(60.0, "percent"), "baffle_friction_multiplier": _q(1.0, "dimensionless"),
        "oxygen_kla": _q(CENTRAL["oxygen_kla_per_h"], "1/h"), "oxygen_saturation": _q(8.0, "mg/L"),
        # T2 drives light from the profile; the T1 sinusoid fields are inert but required.
        "peak_par": _q(1500.0, "umol/(m2.s)"), "photoperiod": _q(12.0, "h"),
        "diffuse_fraction": _q(0.2, "dimensionless"),
        "temperature_mean": _q(CENTRAL["culture_temperature_c"], "degC"),
        "temperature_amplitude": _q(0.0, "K"),
        "tubes_across": _q(case["tubes_across"], "dimensionless"),
        "layers": _q(case["layers"], "dimensionless"),
        "pitch_h": _q(_INPUTS["TUBE_PITCH_M"], "m"), "pitch_v": _q(_INPUTS["TUBE_PITCH_M"], "m"),
        "stagger_offset": _q(0.0, "m"), "axis_azimuth": _q(CENTRAL["axis_azimuth_deg"], "dimensionless"),
        "centre_height_above_sea": _q(_INPUTS["TUBE_CENTRE_HEIGHT_M"], "m"),
        "n_wall": _q(CENTRAL["n_wall"], "dimensionless"), "n_water": _q(CENTRAL["n_water"], "dimensionless"),
        "sea_albedo": _q(CENTRAL["ground_albedo"], "dimensionless"),
    }
    ops: list[Any] = [
        SetThermo(op="set_thermo", compounds=["Water"], property_package="NRTL"),
        AddUnit(op="add_unit", id="pump", type="Pump", tag="Pump", x=0, y=0),
        AddUnit(op="add_unit", id="pbr", type="PhotobioreactorT1", tag="PBR", x=100, y=0),
        SetUnitParams(op="set_unit_params", unit="pbr", options={"optics_model": "t2"}, values=pbr),
        SetUnitModel(op="set_unit_model", unit="pbr", model={
            "card_id": card["id"], "card_revision": card["revision"], "card_digest": card["digest"]}),
        AddUnit(op="add_unit", id="tank", type="HoldupTank", tag="Tank", x=200, y=0),
        SetUnitParams(op="set_unit_params", unit="tank", mode="dynamic", values={
            "liquid_volume": _q(case["dark_volume_m3"], "m3"), "min_volume": _q(0.0, "m3"),
            "max_volume": _q(case["dark_volume_m3"], "m3"), "temperature": _q(temperature_k, "K")}),
        AddUnit(op="add_unit", id="split", type="Splitter", tag="Split", x=300, y=0),
        SetUnitParams(op="set_unit_params", unit="split", mode="split_ratios", values={
            "split_ratio_1": _q(0.5, "dimensionless"), "split_ratio_2": _q(0.5, "dimensionless")}),
        AddUnit(op="add_unit", id="mix", type="Mixer", tag="Mix", x=400, y=0),
    ]
    ring = ("pump", "pbr", "tank", "split", "mix")
    for k, (src, dst) in enumerate(zip(ring, ring[1:] + ring[:1], strict=True)):
        ops += [AddStream(op="add_stream", id=f"s{k}", tag=f"S{k}", x=50 * k, y=100),
                Connect(op="connect", stream=f"s{k}", end="source", unit=src, port=1 if src == "split" else 0),
                Connect(op="connect", stream=f"s{k}", end="target", unit=dst, port=0)]
    ops += [
        AddStream(op="add_stream", id="feed", tag="Feed", x=400, y=200),
        Connect(op="connect", stream="feed", end="target", unit="mix", port=1),
        SetStreamSpec(op="set_stream_spec", stream="feed", pressure=_q(1.0, "bar"),
                      temperature=_q(temperature_k, "K"), mass_flow=_q(1.0, "kg/s"),
                      composition={"Water": 1.0}, composition_basis="mass"),
        SetStreamCulture(op="set_stream_culture", stream="feed", culture={
            "biomass": _q(0.0, "kg/m3"), "nitrogen": _q(CENTRAL["feed_nitrogen_kg_n_m3"], "kg/m3"),
            "oxygen": _q(0.0, "kg/m3"), "salinity": _q(CENTRAL["salinity_g_kg"], "g/kg")}),
        AddStream(op="add_stream", id="harvest", tag="Harvest", x=300, y=200),
        Connect(op="connect", stream="harvest", end="source", unit="split", port=0),
    ]
    initial = {"X": CENTRAL["initial_biomass_kg_m3"], "N": CENTRAL["feed_nitrogen_kg_n_m3"], "O2": 0.008}
    ops.append(SetScenario(op="set_scenario", id="run", value={
        "units": ["PBR", "Tank"],
        "profiles": [{"profile_id": profile["profile_id"], "digest": profile["digest"]}],
        "start_utc": case["start_utc"], "end_utc": case["end_utc"], "output_cadence_s": 3600,
        "rtol": 1e-8, "atol": 1e-12, "temperature_source": "unit_mean",
        "circulation": {"Pump": case["circulation_m3_s"]}, "feed_flows": {"Feed": case["feed_m3_s"]},
        "initial": {"PBR": dict(initial), "Tank": dict(initial)},
    }))
    return ops


def run_central(workspace_id: str, days: float | None = None) -> dict[str, Any]:
    """Run both layouts once at the central assumptions and report S01 conventions.

    ``days`` truncates the declared 36-day window for fast structural tests only.
    """
    from app.modules.process_stack import draft, dynamic_engine

    card = runpy.run_path(str(HERE / "assumed_card.py"))["create_assumed_card"](workspace_id)
    profile = runpy.run_path(str(HERE / "profile_handoff.py"))["pin_t2_profile"](workspace_id)
    window = next(case for case in runpy.run_path(str(HERE / "run_matrix.py"))["build_matrix"]()["cases"]
                  if case["forcing_window"] == CENTRAL["forcing_window"]
                  and case["pbr_temperature_mean_k"] == CENTRAL["culture_temperature_c"] + 273.15)
    if days is not None:
        start = datetime.fromisoformat(window["start_utc"].replace("Z", "+00:00"))
        window = {**window, "end_utc": (start + timedelta(days=days)).isoformat().replace("+00:00", "Z")}
    output: dict[str, Any] = {
        "status": "central declared-assumption run; not the uncertainty band and not a verdict"
                  + ("" if days is None else f"; truncated to {days} d for testing"),
        "labels": ["surrogate forcing: KNMI Deelen, not AlgaePARC measured",
                   "assumed / not qualified CCAP 211/78 card"],
        "central": {key: list(value.items()) if isinstance(value, dict) else value
                    for key, value in CENTRAL.items()},
        "states": STATES, "card_digest": card["card"]["digest"], "profile_digest": profile["digest"],
        "evaluator": dynamic_engine.EVALUATOR_VERSION, "layouts": {},
    }
    for layout in LAYOUTS:
        case = _case(window, layout)
        state = draft.create_draft(workspace_id, f"C1 {layout} central declared-assumption run")
        state = draft.patch(workspace_id, state["draft_id"], state["revision"],
                            _ops(case, card["card"], profile))
        snapshot = dynamic_engine.prepare(workspace_id, state["draft_id"], "run")
        result = dynamic_engine.run(snapshot, cancelled=lambda: False, progress=lambda _value: None)
        if result.status != "succeeded":
            raise RuntimeError(f"{layout} run failed: {result.error}")
        run_days = (dynamic_engine._stamp(case["end_utc"]) - dynamic_engine._stamp(case["start_utc"])) / 86400.0
        harvest_g = 1000.0 * float(result.series["harvest_X_kg"][-1])
        row = LAYOUTS[layout]
        nitrogen = result.series["PBR_N"]
        output["layouts"][layout] = {
            **{key: value for key, value in case.items() if key not in {"start_utc", "end_utc"}},
            "days": run_days, "harvest_g": harvest_g,
            "predicted_areal_g_m2_day": harvest_g / row["ground_area_m2"] / run_days,
            "predicted_volumetric_g_l_day": harvest_g / (1000.0 * row["working_volume_m3"]) / run_days,
            "observed_areal_g_m2_day": row["observed_areal_g_m2_day"],
            "observed_volumetric_g_l_day": row["observed_volumetric_g_l_day"],
            "final_loop_biomass_kg_m3": float(result.series["PBR_X_mean"][-1]),
            "min_pbr_nitrogen_kg_m3": float(min(nitrogen)),
            "snapshot_digest": snapshot.digest,
            "biomass_residual_rel": result.manifest["balances"]["aggregate"]["biomass"]["residual_rel"],
        }
    output["summary_sha256"] = summary_digest(output)
    return output


# Card and snapshot digests carry workspace-local identifiers, the balance
# residual is round-off noise (~1e-13), and repeated runs agree only to about
# 1e-12 relative, so the pinned summary excludes those and rounds floats.
RUN_LOCAL = {"card_digest", "snapshot_digest", "summary_sha256", "biomass_residual_rel"}
SIGNIFICANT_DIGITS = 9


def summary_digest(output: dict[str, Any]) -> str:
    """Digest the reproducible content: no run-local IDs, floats to 9 significant digits."""
    def stable(value: Any) -> Any:
        if isinstance(value, dict):
            return {key: stable(item) for key, item in value.items() if key not in RUN_LOCAL}
        if isinstance(value, list):
            return [stable(item) for item in value]
        if isinstance(value, float):
            return float(f"{value:.{SIGNIFICANT_DIGITS}g}")
        return value

    return hashlib.sha256(json.dumps(stable(output), sort_keys=True, separators=(",", ":"),
                                     allow_nan=False).encode()).hexdigest()


if __name__ == "__main__":
    from app.core.database import initialize_database
    from app.modules.workspaces.models import WorkspaceCreate
    from app.modules.workspaces.service import create_workspace

    initialize_database()
    workspace = create_workspace(WorkspaceCreate(name="C1 215 central", slug="c1-215-central")).id
    print(json.dumps(run_central(workspace), indent=2, sort_keys=True, allow_nan=False))
