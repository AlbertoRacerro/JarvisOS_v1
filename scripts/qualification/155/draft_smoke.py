#!/usr/bin/env python3
"""155 host qualification: Jarvis draft edits, verified DWSIM materialization, run binding, proposals.

Runs the real HTTP routes against the configured pinned DWSIM MCP in a temporary data root and
writes ``draft_smoke.json``. The data is a synthetic water/methanol pump-heater-valve-flash train.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "backend"))


def main() -> int:
    runtime = Path(os.environ["JARVISOS_DWSIM_MCP_PATH"]).resolve()
    os.environ["JARVISOS_DWSIM_MCP_SHA256"] = hashlib.sha256(runtime.read_bytes()).hexdigest()
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent / "draft_smoke.json"
    evidence: dict[str, object] = {}
    with tempfile.TemporaryDirectory(prefix="jarvisos-155-smoke-") as data_root:
        os.environ["JARVISOS_DATA_ROOT"] = data_root
        from app.core.config import get_settings
        from app.core.database import initialize_database
        from app.main import app
        from app.modules.process_stack import draft_compiler

        get_settings.cache_clear()
        initialize_database()
        with TestClient(app) as client:
            workspace = client.post("/workspaces", json={"name": "155 draft smoke", "slug": "draft-smoke-155"})
            workspace.raise_for_status()
            base = f"/workspaces/{workspace.json()['id']}/process/drafts"
            created = client.post(base, json={"name": "Synthetic methanol-water train"})
            created.raise_for_status()
            draft_id = created.json()["draft_id"]
            state = {"revision": created.json()["revision"]}
            latencies: list[float] = []

            def patch(*ops: dict[str, object]) -> dict[str, object]:
                started = time.perf_counter()
                response = client.post(f"{base}/{draft_id}/patch",
                                       json={"expected_revision": state["revision"], "ops": list(ops)})
                latencies.append(time.perf_counter() - started)
                if response.is_error:
                    raise AssertionError(f"patch failed: {response.status_code} {response.text}")
                state["revision"] = response.json()["revision"]
                return response.json()

            q = lambda value, unit: {"value": value, "unit": unit}  # noqa: E731
            patch({"op": "set_thermo", "compounds": ["Water", "Methanol"], "property_package": "NRTL"})
            patch({"op": "add_stream", "id": "feed", "tag": "Feed", "x": 40, "y": 120})
            patch({"op": "add_unit", "id": "p1", "type": "Pump", "tag": "P1", "x": 140, "y": 120})
            patch({"op": "add_stream", "id": "s2", "tag": "S2", "x": 220, "y": 120})
            patch({"op": "add_unit", "id": "h1", "type": "Heater", "tag": "H1", "x": 300, "y": 120})
            patch({"op": "add_stream", "id": "s3", "tag": "S3", "x": 380, "y": 120})
            patch({"op": "add_unit", "id": "v1", "type": "Valve", "tag": "V1", "x": 460, "y": 120})
            patch({"op": "add_stream", "id": "s4", "tag": "S4", "x": 540, "y": 120})
            patch({"op": "add_unit", "id": "fl1", "type": "Flash", "tag": "FL1", "x": 620, "y": 120})
            patch({"op": "add_stream", "id": "vap", "tag": "Vap", "x": 720, "y": 60},
                  {"op": "add_stream", "id": "liq", "tag": "Liq", "x": 720, "y": 180})
            for stream, end, unit, port in [("feed", "target", "p1", 0), ("s2", "source", "p1", 0),
                                            ("s2", "target", "h1", 0), ("s3", "source", "h1", 0),
                                            ("s3", "target", "v1", 0), ("s4", "source", "v1", 0),
                                            ("s4", "target", "fl1", 0), ("vap", "source", "fl1", 0),
                                            ("liq", "source", "fl1", 1)]:
                patch({"op": "connect", "stream": stream, "end": end, "unit": unit, "port": port})
            before_spec = patch({"op": "move", "id": "h1", "x": 305, "y": 118})
            evidence["findings_before_specs"] = [item["code"] for item in before_spec["findings"]]
            patch({"op": "set_stream_spec", "stream": "feed", "temperature": q(25, "degC"), "pressure": q(1.01325, "bar"),
                   "mass_flow": q(3600, "kg/h"), "composition": {"Water": 0.7, "Methanol": 0.3}})
            patch({"op": "set_unit_params", "unit": "p1", "mode": "outlet_pressure",
                   "values": {"outlet_pressure": q(5, "bar")}})
            patch({"op": "set_unit_params", "unit": "h1", "values": {"outlet_temperature": q(95, "degC")}})
            ready = patch({"op": "set_unit_params", "unit": "v1", "mode": "outlet_pressure",
                           "values": {"outlet_pressure": q(1.2, "bar")}})
            evidence["findings_ready"] = ready["findings"]
            evidence["patch_latency_ms"] = {"count": len(latencies), "max": round(max(latencies) * 1000, 1),
                                            "median": round(sorted(latencies)[len(latencies) // 2] * 1000, 1)}

            def act(revision: str, action: str) -> dict[str, object]:
                started = time.perf_counter()
                response = client.post(f"{base}/{draft_id}/revisions/{revision}/{action}")
                if response.is_error:
                    raise AssertionError(f"{action} failed: {response.status_code} {response.text}")
                payload = response.json()
                payload["wall_seconds"] = round(time.perf_counter() - started, 2)
                return payload

            solved_revision = state["revision"]
            validated = act(solved_revision, "validate")
            evidence["validate"] = {k: validated["run"].get(k) for k in (
                "status", "materialization_fingerprint", "materialization_diffs", "dwsim_check", "compile_seconds")}
            first = act(solved_revision, "run")
            second = act(solved_revision, "run")
            for payload in (first, second):
                if payload["run"]["status"] != "completed":
                    raise AssertionError(f"run did not complete: {json.dumps(payload['run'])[:2000]}")
            evidence["run_1"] = {k: first["run"].get(k) for k in (
                "run_id", "status", "draft_revision", "materialization_fingerprint", "expected_fingerprint",
                "dwsim_version", "mcp_sha256", "compiler_version", "mass_balance", "solved_case_sha256",
                "compile_seconds")} | {"wall_seconds": first["wall_seconds"], "streams": first["run"]["streams"]}
            evidence["determinism"] = {
                "fingerprint_1": first["run"]["materialization_fingerprint"],
                "fingerprint_2": second["run"]["materialization_fingerprint"],
                "validate_fingerprint": validated["run"]["materialization_fingerprint"],
                "equal": len({first["run"]["materialization_fingerprint"], second["run"]["materialization_fingerprint"],
                              validated["run"]["materialization_fingerprint"]}) == 1,
            }
            if not evidence["determinism"]["equal"]:
                raise AssertionError("same revision produced different materialization fingerprints")
            evidence["results_after_run"] = second["draft"]["results"]

            # Injected materialization fault: drop the valve outlet-pressure write from the plan.
            original_plan = draft_compiler.plan

            def faulty(document):
                return [(tool, args) for tool, args in original_plan(document)
                        if not (tool == "dwsim_unitop_set" and args["name"] == "V1")]

            draft_compiler.plan = faulty
            try:
                refused = act(solved_revision, "run")
            finally:
                draft_compiler.plan = original_plan
            evidence["injected_mismatch"] = {k: refused["run"].get(k) for k in (
                "status", "materialization_diffs", "solve", "streams")}
            if refused["run"]["status"] != "materialization_mismatch" or refused["run"].get("streams"):
                raise AssertionError("an injected mismatch was not refused before solve")
            if refused["draft"]["results"]["state"] != "current":
                raise AssertionError("a refused attempt must not replace the last current results")

            edited = patch({"op": "set_unit_params", "unit": "h1", "values": {"outlet_temperature": q(80, "degC")}})
            evidence["results_after_edit"] = edited["results"]
            if edited["results"]["state"] != "stale":
                raise AssertionError("results did not go stale after an edit")

            proposal = client.post(f"{base}/{draft_id}/proposals", json={
                "base_revision": state["revision"], "source": "hermes:smoke", "rationale": "synthetic check",
                "changes": [{"target": "V1", "property": "outlet_pressure", "proposed": q(2, "bar")}]})
            proposal.raise_for_status()
            pending = proposal.json()
            after_propose = client.get(f"{base}/{draft_id}").json()
            if after_propose["revision"] != state["revision"]:
                raise AssertionError("a proposal changed the draft before approval")
            approved = client.post(f"{base}/{draft_id}/proposals/{pending['proposal_id']}/approve", json={})
            approved.raise_for_status()
            state["revision"] = approved.json()["draft"]["revision"]
            evidence["proposal"] = {"changes": pending["changes"], "state": pending["state"],
                                    "applied_revision": approved.json()["proposal"]["applied_revision"]}
            rerun = act(state["revision"], "run")
            evidence["rerun"] = {"status": rerun["run"]["status"], "draft_revision": rerun["run"]["draft_revision"],
                                 "results": rerun["draft"]["results"],
                                 "S4_pressure_Pa": rerun["run"]["streams"]["S4"]["pressure_Pa"]}
            if rerun["draft"]["results"]["state"] != "current" or abs(
                    rerun["run"]["streams"]["S4"]["pressure_Pa"] - 200000.0) > 1e-3:
                raise AssertionError("rerun after approval is not current or not bound to the approved change")
            evidence["revisions"] = client.get(f"{base}/{draft_id}/revisions").json()[:6]
    evidence["runtime"] = {"path": str(runtime), "mcp_sha256": os.environ["JARVISOS_DWSIM_MCP_SHA256"]}
    evidence["source_sha"] = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True,
                                            cwd=ROOT, check=False).stdout.strip()
    out.write_text(json.dumps(evidence, indent=1, sort_keys=True, default=str) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "out": str(out), "determinism": evidence["determinism"]["equal"],
                      "patch_latency_ms": evidence["patch_latency_ms"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
