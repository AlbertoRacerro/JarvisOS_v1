"""Real DWSIM 10.2.9 proof for a three day dynamic PBR-to-Heater downstream sample."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "backend" / "tests"))
OUTPUT = Path("/home/thera/jarvis-control/work/evidence/172/real-dwsim-downstream.json")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    executable = Path(os.environ.get("JARVISOS_DWSIM_MCP_PATH", ""))
    report: dict[str, Any] = {"source_sha": subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "source_dirty": bool(subprocess.check_output(
            ["git", "status", "--porcelain"], cwd=ROOT, text=True).strip()),
        "dwsim_path_configured": bool(os.environ.get("JARVISOS_DWSIM_MCP_PATH")) and executable.is_file(),
        "complete": False}
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    if not executable.is_file():
        report.update(dwsim_version=None, outcome="DWSIM MCP executable unavailable",
                      recycle_case={"outcome": "not_run", "reason": "DWSIM MCP executable unavailable"})
        OUTPUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        return 2
    os.environ["JARVISOS_DWSIM_MCP_SHA256"] = _sha(executable)
    report["dwsim_mcp_sha256"] = _sha(executable)
    with tempfile.TemporaryDirectory(prefix="jarvisos-172-real-") as root:
        os.environ["JARVISOS_DATA_ROOT"] = root
        subprocess.run([sys.executable, "-m", "app.core.bootstrap"], cwd=ROOT / "backend", check=True,
                       env=os.environ.copy(), capture_output=True, text=True)
        from app.modules.bio_models import service as bio_models
        from app.modules.environment import profiles
        from app.modules.process_stack import draft, dwsim, dynamic_engine
        from app.modules.process_stack.draft_models import (
            AddStream,
            AddUnit,
            Connect,
            DraftQuantity,
            SetScenario,
            SetUnitModel,
            SetUnitParams,
        )
        from tests.plumbing_170_support import pbr_ops, pin_of

        report["dwsim_version"] = dwsim._version(executable)
        workspace_id = f"172real{int(time.time())}"
        from app.modules.workspaces.models import WorkspaceCreate
        from app.modules.workspaces.service import create_workspace

        workspace = create_workspace(WorkspaceCreate(name="172 real DWSIM", slug=workspace_id))
        workspace_id = workspace.id
        start = datetime(2026, 2, 1, tzinfo=UTC)
        end = start + timedelta(days=3)
        stamps = [start + timedelta(hours=hour) for hour in range(73)]
        profile = profiles.create_profile(
            workspace_id, name="172 real downstream profile",
            timestamps=[item.isoformat().replace("+00:00", "Z") for item in stamps],
            channels={"par": [300.0] * len(stamps)}, resolution_minutes=60,
            provenance={"kind": "real_dwsim_172_acceptance"})
        parameter_set = bio_models.create_set(workspace_id, "172 downstream parameters")
        for symbol, value, unit in (
            ("K_I", 150.0, "umol/(m**2*s)"), ("K_j_0", 0.001, "kg/m3"), ("k_d", 0.003, "1/hour"),
            ("a", 1.8, "1"), ("b", 0.5, "1"), ("c", 0.1, "1"), ("d", 0.01, "1"),
            ("w_ash", 0.05, "1"), ("k_X", 150.0, "m**2/kg"), ("T_min", 278.15, "K"),
            ("T_opt", 298.15, "K"), ("T_max", 318.15, "K"),
        ):
            parameter_set = bio_models.edit_set_value(
                workspace_id, parameter_set["id"], symbol,
                {"value": value, "unit": unit, "expected_unit": unit},
                parameter_set["revision"], parameter_set["digest"],
            )
        card = bio_models.create_card(
            workspace_id, "172 real downstream card", parameter_set["id"],
            {"light": "light.monod", "optics": "optics.slab_response_average", "temperature": "temperature.ctmi",
             "nutrients": ["nutrient.monod"], "combination": "combine.liebig", "loss": "loss.first_order",
             "stoichiometry": "stoich.photoautotrophic"},
            {"value": 0.08, "unit": "1/hour"},
        )
        state = draft.create_draft(workspace_id, "PBR to Heater downstream")
        ops = pbr_ops(model=False, flow_kg_s=0.01)
        ops += [
            AddUnit(op="add_unit", id="heater", type="Heater", tag="Heater", x=300, y=0),
            AddStream(op="add_stream", id="heater_out", tag="HeaterOut", x=400, y=0),
            Connect(op="connect", stream="product", end="target", unit="heater", port=0),
            Connect(op="connect", stream="heater_out", end="source", unit="heater", port=0),
            SetUnitParams(op="set_unit_params", unit="heater", mode="outlet_temperature",
                          values={"outlet_temperature": DraftQuantity(value=298.15, unit="K")}),
        ]
        state = draft.patch(workspace_id, state["draft_id"], state["revision"], ops)
        state = draft.patch(workspace_id, state["draft_id"], state["revision"], [
            SetUnitModel(op="set_unit_model", unit="pbr", model=pin_of(card)),
            SetScenario(op="set_scenario", id="three_days", value={
                "units": ["PBR"], "profiles": [{"profile_id": profile["profile_id"], "digest": profile["digest"]}],
                "start_utc": start.isoformat().replace("+00:00", "Z"),
                "end_utc": end.isoformat().replace("+00:00", "Z"), "output_cadence_s": 86400,
                "downstream_cadence_s": 86400, "temperature_source": "unit_mean",
                "initial": {"PBR": {"X": 0.2, "N": 0.05, "O2": 0.008}},
            }),
        ])
        snapshot = dynamic_engine.prepare(workspace_id, state["draft_id"], "three_days")
        from app.modules.process_stack.dynamic_downstream import build_sampler

        sampler = build_sampler(snapshot)
        if sampler is None:
            raise RuntimeError("The PBR-to-Heater draft did not produce a downstream sampler")
        result = dynamic_engine.run(snapshot, cancelled=lambda: False, progress=lambda _value: None, sampler=sampler)
        without_downstream = dynamic_engine.run(snapshot, cancelled=lambda: False, progress=lambda _value: None)
        biological_channels = sorted(name for name in result.series if name in {"PBR_X", "PBR_N", "PBR_O2"})
        same_biology = bool(biological_channels) and all(
            (result.series[key] == without_downstream.series[key]).all() for key in biological_channels
        )
        outcomes = result.manifest.get("downstream_outcomes", [])
        report.update({"scenario_status": result.status, "downstream_outcomes": outcomes,
                       "series_rows": len(result.series.get("t_s", [])),
                       "biological_channels": biological_channels,
                       "biology_identical_without_sampler": same_biology,
                       "complete": (result.status == "succeeded" and bool(outcomes)
                                    and all(item.get("status") == "succeeded" for item in outcomes)
                                    and same_biology),
                       "outcome": "completed" if result.status == "succeeded" else result.error})
        report["recycle_case"] = _recycle_case(
            workspace_id, state, start, end, profile, card, pin_of, draft, dynamic_engine)
    OUTPUT.write_text(json.dumps(report, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    return 0 if report["complete"] else 1


def _recycle_case(workspace_id, state, start, end, profile, card, pin_of, draft, dynamic_engine):
    """PBR -> Heater -> Mixer -> Splitter -> (purge | recycle to Mixer): the loop is wholly downstream of the
    first non-T1 unit, so real DWSIM owns it while CVODE owns the PBR."""
    from app.modules.process_stack.draft_models import (
        AddStream,
        AddUnit,
        Connect,
        Disconnect,
        DraftQuantity,
        SetScenario,
        SetUnitModel,
        SetUnitParams,
    )
    from tests.plumbing_170_support import pbr_ops

    result: dict[str, Any] = {"topology": "PBR -> Heater -> Mixer -> Splitter -> purge + recycle to Mixer"}
    try:
        recycle = draft.create_draft(workspace_id, "PBR downstream recycle")
        ops = pbr_ops(model=False, flow_kg_s=0.01) + [
            AddUnit(op="add_unit", id="mixer", type="Mixer", tag="Mixer", x=250, y=0),
            AddUnit(op="add_unit", id="heater", type="Heater", tag="Heater", x=350, y=0),
            AddUnit(op="add_unit", id="split", type="Splitter", tag="Split", x=450, y=0),
            AddStream(op="add_stream", id="hot", tag="Hot", x=300, y=0),
            AddStream(op="add_stream", id="mixed", tag="Mixed", x=400, y=0),
            AddStream(op="add_stream", id="purge", tag="Purge", x=500, y=-50),
            AddStream(op="add_stream", id="back", tag="Back", x=450, y=80),
            Disconnect(op="disconnect", stream="product", end="source"),
            Connect(op="connect", stream="product", end="source", unit="pbr", port=0),
            Connect(op="connect", stream="product", end="target", unit="heater", port=0),
            Connect(op="connect", stream="hot", end="source", unit="heater", port=0),
            Connect(op="connect", stream="hot", end="target", unit="mixer", port=0),
            Connect(op="connect", stream="mixed", end="source", unit="mixer", port=0),
            Connect(op="connect", stream="mixed", end="target", unit="split", port=0),
            Connect(op="connect", stream="purge", end="source", unit="split", port=0),
            Connect(op="connect", stream="back", end="source", unit="split", port=1),
            Connect(op="connect", stream="back", end="target", unit="mixer", port=1),
            SetUnitParams(op="set_unit_params", unit="heater", mode="outlet_temperature",
                          values={"outlet_temperature": DraftQuantity(value=298.15, unit="K")}),
            SetUnitParams(op="set_unit_params", unit="split", mode="split_ratios", values={
                "split_ratio_1": DraftQuantity(value=0.9, unit="dimensionless"),
                "split_ratio_2": DraftQuantity(value=0.1, unit="dimensionless")}),
        ]
        recycle = draft.patch(workspace_id, recycle["draft_id"], recycle["revision"], ops)
        recycle = draft.patch(workspace_id, recycle["draft_id"], recycle["revision"], [
            SetUnitModel(op="set_unit_model", unit="pbr", model=pin_of(card)),
            SetScenario(op="set_scenario", id="recycle", value={
                "units": ["PBR"], "profiles": [{"profile_id": profile["profile_id"], "digest": profile["digest"]}],
                "start_utc": start.isoformat().replace("+00:00", "Z"),
                "end_utc": end.isoformat().replace("+00:00", "Z"), "output_cadence_s": 86400,
                "downstream_cadence_s": 86400, "temperature_source": "unit_mean",
                "initial": {"PBR": {"X": 0.2, "N": 0.05, "O2": 0.008}},
            }),
        ])
        try:
            dynamic_engine.prepare(workspace_id, recycle["draft_id"], "recycle")
            result["recycle_free_preflight"] = {"outcome": "admitted"}
        except dynamic_engine.DynamicError as exc:
            result["recycle_free_preflight"] = {"outcome": "refused", "code": exc.code,
                                                "detail": getattr(exc, "detail", {})}
        # DWSIM orders a loop only through a native Recycle block, so tear Back before the Mixer.
        recycle = draft.patch(workspace_id, recycle["draft_id"], recycle["revision"], [
            AddUnit(op="add_unit", id="rec", type="Recycle", tag="Rec", x=350, y=80),
            AddStream(op="add_stream", id="torn", tag="Torn", x=300, y=80),
            Disconnect(op="disconnect", stream="back", end="target"),
            Connect(op="connect", stream="back", end="target", unit="rec", port=0),
            Connect(op="connect", stream="torn", end="source", unit="rec", port=0),
            Connect(op="connect", stream="torn", end="target", unit="mixer", port=1),
        ])
        result["topology"] += " via native Recycle Rec"
        snapshot = dynamic_engine.prepare(workspace_id, recycle["draft_id"], "recycle")
        from app.modules.process_stack.dynamic_downstream import build_sampler

        sampler = build_sampler(snapshot)
        run = dynamic_engine.run(snapshot, cancelled=lambda: False, progress=lambda _v: None, sampler=sampler)
        outcomes = run.manifest.get("downstream_outcomes", [])
        result.update(scenario_status=run.status, downstream_outcomes=outcomes,
                      outcome=("succeeded" if outcomes and all(o.get("status") == "succeeded" for o in outcomes)
                               else "downstream_unconverged_or_failed"))
    except dynamic_engine.DynamicError as exc:
        result.update(outcome="not_run", reason=f"T1 topology preflight rejected: {exc.code}: {exc}",
                      code=exc.code,
                      detail=getattr(exc, "detail", {}))
    except Exception as exc:  # noqa: BLE001 - record the real failure, never hide it
        result.update(outcome="error", reason=f"{type(exc).__name__}: {exc}")
    return result


if __name__ == "__main__":
    raise SystemExit(main())
