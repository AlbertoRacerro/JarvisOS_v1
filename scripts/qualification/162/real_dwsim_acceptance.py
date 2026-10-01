"""Run spec 162 feed/recycle acceptance against the pinned DWSIM 10.2.9 MCP."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "backend"))
OUT = Path(os.environ.get("JARVISOS_162_EVIDENCE", "/home/thera/jarvis-control/work/evidence/162/accept"))


def main() -> None:
    runtime = Path(os.environ["JARVISOS_DWSIM_MCP_PATH"]).resolve()
    digest = hashlib.sha256(runtime.read_bytes()).hexdigest()
    os.environ["JARVISOS_DWSIM_MCP_SHA256"] = digest
    with tempfile.TemporaryDirectory(prefix="jarvisos-162-data-") as data_root:
        os.environ["JARVISOS_DATA_ROOT"] = data_root
        from app.core.config import get_settings
        from app.core.database import initialize_database
        from app.main import app
        from fastapi.testclient import TestClient

        get_settings.cache_clear()
        initialize_database()
        evidence: dict[str, Any] = {
            "source_sha": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
            "dwsim_version": "10.2.9", "runtime_sha256": digest, "data_root_is_temporary": True,
            "cases": {},
        }
        with TestClient(app) as client:
            workspace = client.post("/workspaces", json={"name": "162 pinned DWSIM acceptance", "slug": "accept-162-runtime"})
            workspace.raise_for_status()
            base = f"/workspaces/{workspace.json()['id']}/process/drafts"
            q = lambda value, unit: {"value": value, "unit": unit}

            def execute(name: str, ops: list[dict[str, Any]], mirror_id: str | None = None) -> dict[str, Any]:
                created = client.post(base, json={"name": name})
                created.raise_for_status()
                draft_id, revision = created.json()["draft_id"], created.json()["revision"]
                patched = client.post(f"{base}/{draft_id}/patch", json={"expected_revision": revision, "ops": ops})
                patched.raise_for_status()
                seeded = patched.json()
                row: dict[str, Any] = {"draft_id": draft_id,
                    "jarvis_findings": seeded.get("findings", [])}
                checked = client.post(f"{base}/{draft_id}/revisions/{seeded['revision']}/validate")
                checked.raise_for_status()
                validation = checked.json()["run"]
                row["validation_status"] = validation["status"]
                row["dwsim_check_findings"] = validation.get("dwsim_check", {}).get("findings", [])
                if validation["status"] != "validated":
                    row["error"] = validation.get("error_detail") or validation.get("error")
                    return row
                ran = client.post(f"{base}/{draft_id}/revisions/{seeded['revision']}/run")
                ran.raise_for_status()
                run = ran.json()["run"]
                row["run"] = {key: run.get(key) for key in ("status", "dwsim_version", "mcp_sha256",
                    "materialization_fingerprint", "materialization_diffs", "solve", "streams", "units", "error", "error_detail")}
                if mirror_id and run.get("status") == "completed":
                    before = ran.json()["draft"]
                    mirrored = client.post(f"{base}/{draft_id}/patch", json={
                        "expected_revision": before["revision"],
                        "ops": [{"op": "set_orientation", "id": mirror_id, "flip_x": True}],
                    })
                    mirrored.raise_for_status()
                    after = mirrored.json()
                    row["orientation"] = {"revision": after["revision"], "results": after["results"],
                        "materialization_fingerprint": after["results"].get("materialization_fingerprint"),
                        "unit": next(item for item in after["objects"] if item["id"] == mirror_id)}
                return row

            def stream(tag: str, x: int, y: int, kind: str = "material") -> dict[str, Any]:
                return {"op": "add_stream", "id": tag.lower(), "tag": tag, "x": x, "y": y,
                        "stream_type": kind}

            def unit(tag: str, kind: str, x: int, y: int) -> dict[str, Any]:
                return {"op": "add_unit", "id": tag.lower(), "type": kind, "tag": tag, "x": x, "y": y}

            qfeed = {"op": "set_stream_spec", "stream": "f", "temperature": q(25, "degC"),
                "pressure": q(1.01325, "bar"), "molar_flow": q(40, "mol/s"),
                "composition_basis": "mole", "composition": {"Water": 0.5, "Methanol": 0.5}}
            heater = [{"op": "set_thermo", "compounds": ["Water", "Methanol"], "property_package": "NRTL"},
                stream("F", 50, 120), unit("H", "Heater", 300, 120), stream("P", 550, 120),
                {"op": "connect", "stream": "f", "end": "target", "unit": "h", "port": 0},
                {"op": "connect", "stream": "p", "end": "source", "unit": "h", "port": 0}, qfeed,
                {"op": "set_unit_params", "unit": "h", "mode": "outlet_temperature",
                 "values": {"outlet_temperature": q(95, "degC")}}]
            molar = execute("Molar flow feed", heater)
            evidence["cases"]["molar_flow_feed"] = molar
            assert molar["run"]["status"] == "completed", json.dumps(molar)[:3000]
            feed_result = molar["run"]["streams"]["F"]
            assert abs(feed_result["molar_flow_mol_s"] - 40) < 1e-8

            zero_ops = [*heater]
            zero_ops[6] = {**qfeed, "molar_flow": q(0, "mol/s")}
            zero = execute("Zero flow feed", zero_ops)
            evidence["cases"]["zero_flow_warning"] = zero
            warning_codes = {item["code"] for item in zero.get("jarvis_findings", [])}
            assert "FEED_FLOW_ZERO" in warning_codes, json.dumps(zero)[:3000]
            if zero.get("run", {}).get("status") == "completed":
                zero["zero_product_flow"] = zero["run"]["streams"].get("P", {}).get("mass_flow_kg_s")

            recycle = [
                {"op": "set_thermo", "compounds": ["Water"], "property_package": "NRTL"},
                stream("F", 30, 100), unit("M", "Mixer", 250, 100), unit("S", "Splitter", 500, 100),
                unit("R", "Recycle", 750, 100), stream("P", 650, 40), stream("RS", 650, 160), stream("RO", 850, 160),
                stream("MS", 400, 100),
                {"op": "connect", "stream": "f", "end": "target", "unit": "m", "port": 0},
                {"op": "connect", "stream": "ro", "end": "target", "unit": "m", "port": 1},
                {"op": "connect", "stream": "ms", "end": "source", "unit": "m", "port": 0},
                {"op": "connect", "stream": "ms", "end": "target", "unit": "s", "port": 0},
                {"op": "connect", "stream": "p", "end": "source", "unit": "s", "port": 0},
                {"op": "connect", "stream": "rs", "end": "source", "unit": "s", "port": 1},
                {"op": "connect", "stream": "rs", "end": "target", "unit": "r", "port": 0},
                {"op": "connect", "stream": "ro", "end": "source", "unit": "r", "port": 0},
                {"op": "set_stream_spec", "stream": "f", "temperature": q(25, "degC"),
                 "pressure": q(1.01325, "bar"), "mass_flow": q(3600, "kg/h"), "composition": {"Water": 1}},
                {"op": "set_unit_params", "unit": "s", "mode": "split_ratios",
                 "values": {"split_ratio_1": q(0.8, "dimensionless"), "split_ratio_2": q(0.2, "dimensionless")}},
            ]
            recycle_result = execute("Mirrored recycle", recycle, mirror_id="r")
            evidence["cases"]["mirrored_recycle"] = recycle_result
            assert recycle_result["run"]["status"] == "completed", json.dumps(recycle_result)[:3000]
            assert recycle_result["orientation"]["results"]["state"] == "current"
            OUT.mkdir(parents=True, exist_ok=True)
            (OUT / "real_dwsim_162.json").write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            print(OUT / "real_dwsim_162.json")


if __name__ == "__main__":
    main()
