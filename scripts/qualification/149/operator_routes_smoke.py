"""Exercise the engineering operator API with the committed synthetic 108 PBR fixture."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import tempfile
from pathlib import Path

import yaml
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[3]


def configure_tools(prefix: Path | None, temp_root: Path) -> Path:
    config = yaml.safe_load((ROOT / "configs/bluecad_tools.yaml").read_text(encoding="utf-8"))
    if prefix is not None:
        for tool_id, binary in (("openfoam", "icoFoam"), ("openfoam_blockmesh", "blockMesh")):
            executable = prefix / "bin" / binary
            if executable.is_file():
                item = next(tool for tool in config["tools"] if tool["id"] == tool_id)
                item.update(entrypoint=str(executable), binary_sha256=hashlib.sha256(executable.read_bytes()).hexdigest(),
                            enabled=True, provenance_url="https://www.openfoam.com/releases/openfoam-v2412/")
    path = temp_root / "bluecad_tools.yaml"
    path.write_text(yaml.safe_dump(config), encoding="utf-8")
    return path


def pbr_definition(workspace_id: str) -> dict[str, object]:
    from app.modules.bluerev.pbr_evaluator import EVALUATOR_ID

    fixture_path = ROOT / "scripts/qualification/107/synthetic-parameters.json"
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    basis_ref = fixture["basis_ref"]
    fixed = []
    for name, (value, unit) in fixture["coefficients"].items():
        fixed.append({"name": name, "value": {"value": value, "unit": unit, "basis_ref": basis_ref}})
    for name, (value, unit) in fixture["design"].items():
        if name == "peak_par":
            continue
        if name == "duration":
            value = 1.0
        fixed.append({"name": name, "value": {"value": value, "unit": unit}})
    return {
        "study_ref": {"authority_owner": "bluerev", "object_type": "study", "object_id": "pbr-synthetic-operator",
                      "workspace_id": workspace_id, "revision": "149.smoke.1"},
        "evaluator_id": EVALUATOR_ID,
        "subject_ref": {"authority_owner": "bluerev", "object_type": "dynamic_model", "object_id": "pbr-loop-a",
                        "workspace_id": workspace_id, "revision": "1"},
        "method": "latin_hypercube",
        "variables": [{"name": "peak_par", "domain": {"variable": "peak_par",
                       "lower": {"value": 1200, "unit": "umol/(m**2*s)"},
                       "upper": {"value": 1800, "unit": "umol/(m**2*s)"}}}],
        "fixed_inputs": fixed,
        "objectives": [{"output": "volumetric_productivity", "sense": "maximize"}],
        "seed": 108, "budget": 3, "sample_count": 3, "deadline_per_point_s": 90,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path(__file__).with_name("operator_routes.runtime-evidence.json"))
    parser.add_argument("--openfoam-prefix", type=Path)
    args = parser.parse_args()
    data_root = Path(tempfile.mkdtemp(prefix="jarvis-149-operator-"))
    os.environ["JARVISOS_DATA_ROOT"] = str(data_root)
    temp_tools = data_root / "tool-config"
    temp_tools.mkdir()
    prefix = args.openfoam_prefix or (Path(os.environ["MAMBA_ROOT_PREFIX"]) / "envs" / "cfd"
                                      if os.environ.get("MAMBA_ROOT_PREFIX") else None)
    os.environ["JARVISOS_BLUECAD_TOOL_REGISTRY"] = str(configure_tools(prefix, temp_tools))
    dwsim = Path("/home/thera/jarvis-control/work/tools/dwsim-10.2.9/mcp-root/opt/dwsim-mcp/dwsim-mcp")
    dwsim_sha = None
    if dwsim.is_file():
        dwsim_sha = hashlib.sha256(dwsim.read_bytes()).hexdigest()
        os.environ["JARVISOS_DWSIM_MCP_PATH"] = str(dwsim)
        os.environ["JARVISOS_DWSIM_MCP_SHA256"] = dwsim_sha

    import sys
    sys.path.insert(0, str(ROOT / "backend"))
    from app.core.database import initialize_database
    from app.main import create_app
    from app.modules.engineering.operator_service import evaluator_registry
    from app.modules.workspaces.service import seed_default_workspace

    initialize_database()
    workspace = seed_default_workspace()
    app = create_app()
    app.state.engineering_evaluator_registry = evaluator_registry()
    with TestClient(app) as client:
        base = f"/workspaces/{workspace.id}/engineering"
        evaluators_response = client.get(f"{base}/evaluators")
        evaluators_response.raise_for_status()
        evaluators = evaluators_response.json()
        definition = pbr_definition(workspace.id)
        study_response = client.post(f"{base}/studies", json=definition)
        study_response.raise_for_status()
        run = study_response.json()
        feasible = [point for point in run["points"] if point["feasible"]]
        if not feasible:
            raise RuntimeError(
                "synthetic PBR study produced no feasible point: "
                f"status={run['status']} failures={[point['failure'] for point in run['points']]}"
            )
        best = next(point for point in feasible if point["index"] == run["best_point_index"])
        envelope_response = client.post(
            f"{base}/studies/pbr-synthetic-operator/runs/{run['content_digest']}/envelope",
            params={"point_index": best["index"]},
        )
        envelope_response.raise_for_status()
        escalation_response = client.post(
            f"{base}/studies/pbr-synthetic-operator/runs/{run['content_digest']}/escalations",
            json={"policy": {"operator_requested_points": [best["index"]]}, "evaluator_ids": []},
        )
        escalation_response.raise_for_status()
        capability_response = client.get(f"{base}/capabilities")
        capability_response.raise_for_status()

    fixture_path = ROOT / "scripts/qualification/107/synthetic-parameters.json"
    evidence = {
        "evidence_kind": "real_runtime_execution",
        "source_sha": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, check=True, capture_output=True,
                                      text=True).stdout.strip(),
        "data_root": str(data_root),
        "runtime_tools": {
            "openfoam_prefix": str(prefix) if prefix else None,
            "openfoam_binaries": {name: hashlib.sha256((prefix / "bin" / name).read_bytes()).hexdigest()
                                  for name in ("icoFoam", "blockMesh")
                                  if prefix is not None and (prefix / "bin" / name).is_file()},
            "dwsim_mcp_path": str(dwsim) if dwsim_sha else None,
            "dwsim_mcp_sha256": dwsim_sha,
        },
        "workspace_id": workspace.id,
        "fixture": {"path": str(fixture_path.relative_to(ROOT)),
                    "sha256": hashlib.sha256(fixture_path.read_bytes()).hexdigest(), "qualification": "synthetic/unqualified"},
        "evaluators": evaluators,
        "study": {"content_digest": run["content_digest"], "status": run["status"],
                  "qualification_status": run["qualification_status"], "point_count": len(run["points"]),
                  "feasible_count": run["feasible_count"], "best_point_index": run["best_point_index"]},
        "envelope": {"digest": envelope_response.json()["envelope_digest"],
                     "point_index": envelope_response.json()["selected_point_index"],
                     "qualification_status": envelope_response.json()["qualification_status"]},
        "escalation": {"content_digest": escalation_response.json()["content_digest"],
                       "statuses": [point["status"] for point in escalation_response.json()["points"]],
                       "reason": "No compatible higher-fidelity evaluator selected for the PBR input contract."},
        "capabilities": capability_response.json(),
        "interpretation": "FastAPI TestClient exercised the real local PBR evaluator with the committed synthetic 107 parameters; this is unqualified software/runtime evidence only.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"study": evidence["study"], "envelope": evidence["envelope"],
                      "escalation": evidence["escalation"], "evidence": str(args.output)}))


if __name__ == "__main__":
    main()
