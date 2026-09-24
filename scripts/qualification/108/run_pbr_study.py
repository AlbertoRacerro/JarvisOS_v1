"""Run a three-point synthetic/unqualified 107 PBR study as real runtime evidence."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import platform
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
FIXTURE = ROOT / "scripts/qualification/107/synthetic-parameters.json"
DEFAULT_OUTPUT = Path(__file__).with_name("pbr-study.runtime-evidence.json")


def run(output: Path) -> None:
    sys.path.insert(0, str(ROOT / "backend"))
    from app.modules.bluerev.pbr_evaluator import EVALUATOR_ID, PbrDayNightEvaluator
    from app.modules.engineering.refs import (
        DomainBound,
        DynamicModelRef,
        Quantity,
        StudyRef,
    )
    from app.modules.engineering.studies import (
        DesignVariable,
        StudyDefinition,
        StudyObjective,
        run_study,
    )

    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    basis_ref = fixture["basis_ref"]
    fixed = []
    for name, (value, unit) in fixture["coefficients"].items():
        fixed.append({"name": name, "value": {"value": value, "unit": unit, "basis_ref": basis_ref}})
    for name, (value, unit) in fixture["design"].items():
        if name == "peak_par":
            continue
        if name == "duration":
            value = 1.0  # one full diel cycle (days)
        fixed.append({"name": name, "value": {"value": value, "unit": unit}})

    definition = StudyDefinition(
        study_ref=StudyRef(authority_owner="bluerev", object_id="pbr-synthetic-study", workspace_id="bluerev",
                           revision="108.synthetic.1"),
        evaluator_id=EVALUATOR_ID,
        subject_ref=DynamicModelRef(authority_owner="bluerev", object_id="pbr-loop-a", workspace_id="bluerev",
                                    revision="1"),
        method="latin_hypercube",
        variables=(DesignVariable(
            name="peak_par",
            domain=DomainBound(variable="peak_par", lower=Quantity(value=1200, unit="umol/(m**2*s)"),
                               upper=Quantity(value=1800, unit="umol/(m**2*s)")),
        ),),
        fixed_inputs=tuple(fixed),
        objectives=(StudyObjective(output="volumetric_productivity", sense="maximize"),),
        seed=108,
        budget=3,
        sample_count=3,
        deadline_per_point_s=90,
    )
    evaluator = PbrDayNightEvaluator()
    availability = evaluator.availability()
    study = run_study(definition, evaluator)
    if availability.state != "available":
        raise RuntimeError(f"107 evaluator unavailable: {availability.reason_code}")
    if study.status != "succeeded" or study.feasible_count != 3:
        raise RuntimeError(f"real study did not complete three feasible points: {study.status}")
    packages = {}
    for package in ("numpy", "scipy", "scikit-sundae", "CoolProp", "fluids", "Pint"):
        try:
            packages[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            packages[package] = None
    source_sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, check=True, capture_output=True,
                                text=True).stdout.strip()
    document = {
        "evidence_kind": "real_runtime_execution",
        "study_method": definition.method,
        "seed": definition.seed,
        "source_sha": source_sha,
        "executed_at": datetime.now(UTC).isoformat(),
        "runtime": {"python": platform.python_version(), "platform": platform.platform(), "packages": packages},
        "fixture": {"path": str(FIXTURE.relative_to(ROOT)),
                    "sha256": hashlib.sha256(FIXTURE.read_bytes()).hexdigest(),
                    "provenance": fixture["provenance"]},
        "evaluator": {"descriptor": evaluator.descriptor().model_dump(mode="json"),
                      "availability": availability.model_dump(mode="json")},
        "study": study.model_dump(mode="json"),
        "interpretation": (
            "Three real CVODE-backed evaluator calls, each one full diel cycle, completed over the synthetic 107 fixture. "
            "All source coefficients are synthetic; these runs do not establish biological or physical validity."
        ),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    run(parser.parse_args().output)
