"""Synthetic four-PBR loop qualification for the Spec 172 dynamic engine.

This exercises coupled state, recycle, split, separation, and 30-day execution.
The fixture parameters are synthetic; the result is not BlueRev science evidence.
"""

from __future__ import annotations

import hashlib
import json
import os
import resource
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "backend"))

from app.core.paths import build_paths  # noqa: E402
from app.modules.process_stack import draft, dynamic_engine  # noqa: E402
from app.modules.process_stack.draft_models import (  # noqa: E402
    AddStream,
    AddUnit,
    Connect,
    Disconnect,
    DraftQuantity,
    Rename,
    SetScenario,
    SetStreamCulture,
    SetStreamSpec,
    SetUnitModel,
    SetUnitParams,
)
from tests.plumbing_170_support import new_workspace, pbr_quantities  # noqa: E402
from tests.test_process_dynamic_engine import _real_scenario  # noqa: E402

EVIDENCE = Path("/home/thera/jarvis-control/work/evidence/172/four_pbr_30d.json")
MAKEUP_M3_S = 1e-7
SPLIT_BYPASS = 0.5
BIOMASS_RECOVERY = 95.0
CONCENTRATION_FACTOR = 20.0


def _stream(stream_id: str, tag: str, source: tuple[str, int] | None,
            target: tuple[str, int] | None) -> list[object]:
    ops: list[object] = [AddStream(op="add_stream", id=stream_id, tag=tag, x=0, y=0)]
    if source is not None:
        ops.append(Connect(op="connect", stream=stream_id, end="source", unit=source[0], port=source[1]))
    if target is not None:
        ops.append(Connect(op="connect", stream=stream_id, end="target", unit=target[0], port=target[1]))
    return ops


def _build(workspace_id: str) -> tuple[dict, dynamic_engine.Snapshot]:
    state, _ = _real_scenario(workspace_id, 30 * 86400)
    directory = draft.draft_dir(workspace_id, state["draft_id"])
    head = draft._head(directory)
    document = draft.load_revision(directory, head["revision"])["document"]
    pin = document["objects"]["pbr"]["model"]
    scenario = dict(document["scenarios"]["run"])
    scenario["units"] = [f"PBR_{i}" for i in (401, 402, 403, 404)]
    scenario["initial"] = {tag: {"X": 0.2, "N": 0.05, "O2": 0.008} for tag in scenario["units"]}
    scenario["feed_flows"] = {"SeaMakeup": MAKEUP_M3_S, "Node2Dose": MAKEUP_M3_S}

    ops: list[object] = [
        Rename(op="rename", id="pbr", tag="PBR_401"),
        Rename(op="rename", id="feed", tag="SeaMakeup"),
        Rename(op="rename", id="product", tag="S401_N1"),
        Disconnect(op="disconnect", stream="feed", end="target"),
        AddUnit(op="add_unit", id="pbr402", type="PhotobioreactorT1", tag="PBR_402", x=300, y=0),
        AddUnit(op="add_unit", id="pbr403", type="PhotobioreactorT1", tag="PBR_403", x=500, y=150),
        AddUnit(op="add_unit", id="pbr404", type="PhotobioreactorT1", tag="PBR_404", x=300, y=300),
        AddUnit(op="add_unit", id="node1", type="Mixer", tag="Node1", x=100, y=0),
        AddUnit(op="add_unit", id="pump101", type="Pump", tag="P101", x=200, y=0),
        AddUnit(op="add_unit", id="tee301", type="Splitter", tag="TEE301", x=400, y=0),
        AddUnit(op="add_unit", id="f301", type="SpecifiedSeparator", tag="F301", x=500, y=0),
        AddUnit(op="add_unit", id="mix301", type="Mixer", tag="MIX301", x=500, y=100),
        AddUnit(op="add_unit", id="node2", type="Mixer", tag="Node2", x=500, y=250),
        AddUnit(op="add_unit", id="pump201", type="Pump", tag="P201", x=400, y=300),
        Connect(op="connect", stream="product", end="target", unit="node1", port=0),
        Connect(op="connect", stream="feed", end="target", unit="node1", port=1),
    ]
    connections = (
        ("n1_p101", "N1_P101", ("node1", 0), ("pump101", 0)),
        ("p101_402", "P101_402", ("pump101", 0), ("pbr402", 0)),
        ("s402_tee", "S402_TEE", ("pbr402", 0), ("tee301", 0)),
        ("bypass", "S4_Bypass", ("tee301", 0), ("mix301", 0)),
        ("tee_f301", "S5_ToF301", ("tee301", 1), ("f301", 0)),
        ("harvest", "S13_Harvest", ("f301", 0), None),
        ("return", "S12_Return", ("f301", 1), ("mix301", 1)),
        ("mix_403", "MIX_403", ("mix301", 0), ("pbr403", 0)),
        ("s403_n2", "S403_N2", ("pbr403", 0), ("node2", 0)),
        ("n2_p201", "N2_P201", ("node2", 0), ("pump201", 0)),
        ("p201_404", "P201_404", ("pump201", 0), ("pbr404", 0)),
        ("s404_401", "S404_401", ("pbr404", 0), ("pbr", 0)),
        ("dose", "Node2Dose", None, ("node2", 1)),
    )
    for stream_id, tag, source, target in connections:
        ops.extend(_stream(stream_id, tag, source, target))
    for unit_id in ("pbr402", "pbr403", "pbr404"):
        ops.extend([
            SetUnitParams(op="set_unit_params", unit=unit_id, values=pbr_quantities()),
            SetUnitModel(op="set_unit_model", unit=unit_id, model=pin),
        ])
    for pump_id in ("pump101", "pump201"):
        ops.append(SetUnitParams(op="set_unit_params", unit=pump_id, mode="pressure_increase", values={
            "pressure_increase": DraftQuantity(value=0.1, unit="bar"),
            "efficiency": DraftQuantity(value=75.0, unit="percent"),
        }))
    ops.extend([
        SetUnitParams(op="set_unit_params", unit="tee301", mode="split_ratios", values={
            "split_ratio_1": DraftQuantity(value=SPLIT_BYPASS, unit="dimensionless"),
            "split_ratio_2": DraftQuantity(value=1.0 - SPLIT_BYPASS, unit="dimensionless"),
        }),
        SetUnitParams(op="set_unit_params", unit="f301", values={
            "biomass_recovery": DraftQuantity(value=BIOMASS_RECOVERY, unit="percent"),
            "concentration_factor": DraftQuantity(value=CONCENTRATION_FACTOR, unit="dimensionless"),
        }),
        SetStreamSpec(op="set_stream_spec", stream="dose", pressure=DraftQuantity(value=1.0, unit="bar"),
                      temperature=DraftQuantity(value=298.15, unit="K"),
                      mass_flow=DraftQuantity(value=MAKEUP_M3_S * 1000.0, unit="kg/s"),
                      composition={"Water": 1.0}, composition_basis="mass"),
        SetStreamCulture(op="set_stream_culture", stream="dose", culture={
            "biomass": DraftQuantity(value=0.0, unit="kg/m3"),
            "nitrogen": DraftQuantity(value=0.05, unit="kg/m3"),
            "oxygen": DraftQuantity(value=0.0, unit="kg/m3"),
            "salinity": DraftQuantity(value=35.0, unit="g/kg"),
        }),
        SetScenario(op="set_scenario", id="run", value=scenario),
    ])
    state = draft.patch(workspace_id, state["draft_id"], state["revision"], ops)
    return state, dynamic_engine.prepare(workspace_id, state["draft_id"], "run")


def main() -> None:
    if not os.environ.get("JARVISOS_DATA_ROOT"):
        raise SystemExit("Set JARVISOS_DATA_ROOT to an isolated temporary directory.")
    build_paths().data_root.mkdir(parents=True, exist_ok=True)
    workspace_id = new_workspace()
    state, snapshot = _build(workspace_id)
    before_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    started = time.perf_counter()
    result = dynamic_engine.run(snapshot, cancelled=lambda: False, progress=lambda _value: None)
    wall_s = time.perf_counter() - started
    peak_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    with tempfile.TemporaryDirectory(prefix="jarvis-172-four-pbr-") as name:
        artifact = Path(name) / "series.npz"
        np.savez_compressed(artifact, **result.series)
        artifact_bytes = artifact.stat().st_size
    flows = snapshot.payload["topology"]["flows"]
    flow_by_tag = {item["tag"]: flows[item["id"]] for item in snapshot.payload["topology"]["streams"]}
    report = {
        "qualification": "spec_172_synthetic_four_pbr_coupled_topology",
        "scientific_status": "synthetic_engine_evidence_only_not_bluerev_parameter_qualification",
        "git_head_at_run": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "workspace_id": workspace_id,
        "draft_id": state["draft_id"],
        "draft_revision": snapshot.payload["revision"],
        "content_digest": snapshot.payload["content_digest"],
        "snapshot_digest": snapshot.digest,
        "profile": snapshot.payload["profiles"][0]["ref"],
        "model_cards": [
            {"unit": unit["tag"], "id": unit["model"]["card"].get("id"),
             "revision": unit["model"]["card"].get("revision"),
             "digest": unit["model"]["card"].get("digest")}
            for unit in snapshot.payload["units"]
        ],
        "solver": result.manifest.get("solver"),
        "status": result.status,
        "error": result.error,
        "wall_time_s": wall_s,
        "output_count": len(result.series.get("t_s", [])),
        "peak_rss_kib_linux": peak_rss,
        "rss_growth_kib_linux": peak_rss - before_rss,
        "artifact_npz_bytes": artifact_bytes,
        "initial_flows_m3_s": flow_by_tag,
        "balance_residuals": result.manifest.get("balances", {}).get("aggregate"),
        "harvest_kg": result.manifest.get("productivity", {}).get("harvest_kg"),
        "final_states_kg_m3": {
            tag: {channel: float(result.series[f"{tag}_{channel}"][-1]) for channel in ("X", "N", "O2")}
            for tag in snapshot.payload["scenario"]["units"]
        } if result.status == "succeeded" else None,
    }
    EVIDENCE.parent.mkdir(parents=True, exist_ok=True)
    EVIDENCE.write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    print(EVIDENCE)
    print(json.dumps({key: report[key] for key in ("status", "error", "wall_time_s", "output_count",
                                                  "balance_residuals", "harvest_kg")}, indent=2))
    if result.status != "succeeded" or report["output_count"] != 721:
        raise SystemExit("Four-PBR synthetic qualification did not complete successfully")
    if not all(np.isfinite(values).all() for values in result.series.values()):
        raise SystemExit("Four-PBR synthetic qualification contains nonfinite series")
    if any(item["residual_rel"] > 1e-6 for item in report["balance_residuals"].values()):
        raise SystemExit("Four-PBR synthetic qualification violates aggregate balances")
    if not report["harvest_kg"] or report["harvest_kg"] <= 0:
        raise SystemExit("Four-PBR synthetic qualification produced no harvest")
    if abs(flow_by_tag["S13_Harvest"] - 2 * MAKEUP_M3_S) > 1e-12:
        raise SystemExit("Four-PBR synthetic qualification violates boundary flow continuity")


if __name__ == "__main__":
    main()
