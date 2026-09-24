"""Build BLUECAD geometry from the committed 108 best-point evidence."""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import platform
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SOURCE_EVIDENCE = ROOT / "scripts/qualification/108/pbr-study.runtime-evidence.json"
OUTPUT = Path(__file__).resolve().parent


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run() -> None:
    sys.path.insert(0, str(ROOT / "backend"))
    from app.modules.bluecad.service import build_geometry_spec
    from app.modules.engineering.process_cad_handoff import (
        envelope_to_geometry_spec,
        process_design_envelope,
    )
    from app.modules.engineering.studies import StudyRun

    source = json.loads(SOURCE_EVIDENCE.read_text(encoding="utf-8"))
    if source.get("evidence_kind") != "real_runtime_execution":
        raise ValueError("108 input is not marked as real runtime evidence")
    run_record = StudyRun.model_validate(source["study"])
    if run_record.best_point_index is None:
        raise ValueError("108 study artifact has no best point")
    envelope = process_design_envelope(run_record, run_record.best_point_index)
    geometry = envelope_to_geometry_spec(envelope)
    export_dir = OUTPUT / "bluecad"
    build = build_geometry_spec(geometry, export_dir, timeout_s=90)
    if build.verdict != "pass" or build.manifest is None:
        raise RuntimeError(f"BLUECAD build/export did not pass: {build.report}")
    source_sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, check=True,
                                capture_output=True, text=True).stdout.strip()
    packages = {}
    for package in ("build123d", "numpy", "scipy", "Pint"):
        try:
            packages[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            packages[package] = None
    params = geometry["parts"][0]["params"]
    evidence = {
        "evidence_kind": "real_runtime_execution",
        "source_sha": source_sha,
        "executed_at": datetime.now(UTC).isoformat(),
        "runtime": {"python": platform.python_version(), "platform": platform.platform(), "packages": packages},
        "input": {
            "path": str(SOURCE_EVIDENCE.relative_to(ROOT)),
            "sha256": _sha256(SOURCE_EVIDENCE),
            "study_content_digest": run_record.content_digest,
            "definition_digest": run_record.definition_digest,
            "selected_point_index": run_record.best_point_index,
            "qualification_status": envelope.qualification_status,
            "envelope_digest": envelope.envelope_digest,
            "envelope_quantities": {name: quantity.model_dump(mode="json") for name, quantity in envelope.quantities},
        },
        "cad_mapping": {
            "geometry_spec_id": build.spec_id,
            "cad_only_wall_allowance_mm": params["wall_t"],
            "mapped_bore_mm": params["outer_d"] - 2 * params["wall_t"],
            "mapped_length_mm": params["length"],
            "wall_allowance_note": "CAD construction allowance; not a process/scientific input or physical qualification.",
        },
        "bluecad": {
            "verdict": build.verdict,
            "manifest": build.manifest,
            "validation_report": build.report,
            "artifacts": {
                path.name: {"bytes": path.stat().st_size, "sha256": _sha256(path)}
                for path in sorted(export_dir.iterdir()) if path.is_file()
            },
        },
        "interpretation": (
            "BLUECAD built and exported geometry from the selected best point in the 108 runtime artifact. "
            "The underlying study uses synthetic PBR coefficients and is unqualified; Tier 0/1 CAD validation "
            "does not establish process, material, pressure, biological, or physical validity."
        ),
    }
    (OUTPUT / "process-cad-handoff.runtime-evidence.json").write_text(
        json.dumps(evidence, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    run()
