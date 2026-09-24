"""Run the committed synthetic 10-day diel PBR scenario through real CVODE."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import platform
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

FIXTURE_PATH = Path(__file__).with_name("synthetic-parameters.json")
DEFAULT_OUTPUT = Path(__file__).with_name("pbr_day_night.v2.runtime-evidence.json")
MODEL = {
    "authority_owner": "bluerev",
    "object_type": "dynamic_model",
    "object_id": "pbr-loop-a",
    "workspace_id": "bluerev",
    "revision": "1",
}


def run(output: Path) -> None:
    sys.path.insert(0, str(ROOT / "backend"))
    from app.modules.bluerev.pbr_evaluator import EVALUATOR_ID, PbrDayNightEvaluator
    from app.modules.engineering.evaluator_contracts import EvaluationRequest, validate_evaluation_result

    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    now = datetime.now(UTC)
    inputs = []
    for group in ("coefficients", "design"):
        for name, (value, unit) in fixture[group].items():
            quantity = {"value": value, "unit": unit}
            if group == "coefficients":
                quantity["basis_ref"] = fixture["basis_ref"]
            inputs.append({"name": name, "value": quantity})
    request = EvaluationRequest.model_validate({
        "request_ref": {
            "authority_owner": "bluerev", "object_type": "evaluation_request", "object_id": "pbr-run-107",
            "workspace_id": "bluerev", "revision": "1",
        },
        "evaluator_id": EVALUATOR_ID,
        "subject_ref": MODEL,
        "inputs": inputs,
        "requested_at": now - timedelta(seconds=1),
        "deadline_at": now + timedelta(minutes=5),
    })
    evaluator = PbrDayNightEvaluator()
    result = evaluator.evaluate(request)
    validate_evaluation_result(request, result)
    if result.status != "succeeded":
        raise RuntimeError(f"real PBR evaluation failed: {result.failure}")
    values = {item.name: item.value.value for item in result.outputs}
    units = {item.name: item.value.unit for item in result.outputs}
    design = fixture["design"]
    duration_hours = design["duration"][0] * 24.0
    harvest_hour = design["harvest_hour"][0] or 24.0
    harvests = []
    while harvest_hour < duration_hours:
        harvests.append(harvest_hour)
        harvest_hour += 24.0
    package_versions = {}
    for package in ("scikit-sundae", "numpy", "scipy", "CoolProp", "fluids", "Pint"):
        try:
            package_versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            package_versions[package] = None
    source_sha = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, check=True, capture_output=True, text=True,
    ).stdout.strip()
    evidence = {
        "evidence_kind": "real_runtime_execution",
        "evaluator_id": EVALUATOR_ID,
        "model_version": "pbr_day_night.v2",
        "source_sha": source_sha,
        "source_note": "SHA identifies the committed evaluator and scenario runner used for this execution.",
        "executed_at": datetime.now(UTC).isoformat(),
        "runtime": {"python": platform.python_version(), "platform": platform.platform(),
                    "packages": package_versions},
        "backend": {"name": evaluator.descriptor().backend_name,
                    "version": evaluator.descriptor().backend_version,
                    "availability": evaluator.availability().model_dump(mode="json")},
        "fixture": {"path": str(FIXTURE_PATH.relative_to(ROOT)),
                    "sha256": hashlib.sha256(FIXTURE_PATH.read_bytes()).hexdigest(),
                    "provenance": fixture["provenance"]},
        "scenario": {
            "duration_days": design["duration"][0],
            "peak_par": {"value": design["peak_par"][0], "unit": design["peak_par"][1]},
            "photoperiod": {"value": design["photoperiod"][0], "unit": design["photoperiod"][1]},
            "day_night_model": "sinusoidal PAR each photoperiod; zero PAR for remaining daily hours",
            "harvest_events": [{"time": value, "unit": "h from simulation start"} for value in harvests],
        },
        "result": {
            "status": result.status,
            "fidelity": result.fidelity,
            "qualification_status": result.validity.qualification_status if result.validity else None,
            "outputs": {name: {"value": value, "unit": units[name]} for name, value in values.items()},
            "balances": {
                "nitrogen_error_kg_m3": values["nitrogen_balance_error"],
                "oxygen_error_kg_m3": values["oxygen_balance_error"],
                "oxygen_degassed_kg_m3": values["degassed_oxygen"],
            },
            "numerical_diagnostics": result.numerical.model_dump(mode="json"),
        },
        "interpretation": "This proves runtime execution and numerical closure for a synthetic fixture, not biological or physical qualification.",
    }
    output.write_text(json.dumps(evidence, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    run(args.output)
