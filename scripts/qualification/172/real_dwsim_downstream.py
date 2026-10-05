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
        "dwsim_path_configured": bool(str(executable)), "complete": False}
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    if not executable.is_file():
        report["outcome"] = "DWSIM MCP executable unavailable"
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
        from app.modules.process_stack import draft, dynamic_engine
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
    OUTPUT.write_text(json.dumps(report, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    return 0 if report["complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
