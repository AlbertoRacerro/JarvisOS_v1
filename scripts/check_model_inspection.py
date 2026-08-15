#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VIEWER = ROOT / "frontend/src/components/BluecadGlbViewer.tsx"
WORKBENCH = ROOT / "frontend/src/components/bluecad/BluecadWorkbench.tsx"
STATUS = ROOT / "docs/specs/STATUS.md"

ALLOWED = {
    "frontend/src/components/BluecadGlbViewer.tsx",
    "frontend/src/components/bluecad/BluecadWorkbench.tsx",
    "scripts/check_model_inspection.py",
    "docs/specs/STATUS.md",
}


def fail(message: str) -> None:
    print(f"MODEL-INSPECTION-A0 check failed: {message}", file=sys.stderr)
    raise SystemExit(1)


def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        fail(f"missing required file: {path.relative_to(ROOT)}")


def changed_paths() -> set[str]:
    base: str | None = None
    event_path = os.environ.get("GITHUB_EVENT_PATH")
    if event_path:
        try:
            payload = json.loads(Path(event_path).read_text(encoding="utf-8"))
            candidate = payload.get("pull_request", {}).get("base", {}).get("sha")
            if isinstance(candidate, str) and re.fullmatch(r"[0-9a-f]{40}", candidate):
                base = candidate
        except (OSError, json.JSONDecodeError):
            pass
    if base is None:
        for ref in ("origin/master", "master"):
            try:
                base = subprocess.check_output(
                    ["git", "merge-base", "HEAD", ref], cwd=ROOT, text=True, stderr=subprocess.DEVNULL
                ).strip()
                break
            except (OSError, subprocess.CalledProcessError):
                continue
    if base is None:
        fail("cannot resolve PR/base merge point")
    try:
        output = subprocess.check_output(["git", "diff", "--name-only", f"{base}...HEAD"], cwd=ROOT, text=True)
    except (OSError, subprocess.CalledProcessError) as exc:
        fail(f"cannot inspect diff: {type(exc).__name__}")
    return {line.strip().replace("\\", "/") for line in output.splitlines() if line.strip()}


def validate_scope(paths: set[str]) -> None:
    unexpected = sorted(paths - ALLOWED)
    if unexpected:
        fail(f"files outside 086 readiness boundary changed: {', '.join(unexpected)}")
    forbidden = sorted(
        path for path in paths
        if path.startswith("backend/")
        or path.startswith(".github/")
        or path.endswith("package.json")
        or path.endswith("package-lock.json")
        or "migration" in path.lower()
    )
    if forbidden:
        fail(f"forbidden backend/dependency/workflow/schema surface changed: {', '.join(forbidden)}")


def require(source: str, markers: dict[str, str], surface: str) -> None:
    for label, marker in markers.items():
        if marker not in source:
            fail(f"{surface} missing {label}: {marker}")


def check_sources(viewer: str, workbench: str) -> None:
    require(viewer, {
        "raycaster": "new THREE.Raycaster()",
        "canvas-relative coordinates": "getBoundingClientRect()",
        "pointer down": 'addEventListener("pointerdown"',
        "pointer up": 'addEventListener("pointerup"',
        "material-drag threshold": "Math.hypot",
        "artifact-only hit inventory": "intersectObjects(Array.from(meshByKey.values()), false)",
        "session generation": "generationRef",
        "session key": "viewer-session-",
        "stale command guard": "inspectionCommand.sessionKey !== sessionKeyRef.current",
        "serializable inspection facts": "GeometryInspectionMesh",
        "world bounds": "worldBounds",
        "triangle count": "triangleCount",
        "owned cleanup": "disposeOwnedScene",
        "inspection cleanup": "selectCurrentMeshRef.current = null",
    }, "viewer")
    require(workbench, {
        "geometry-only disclaimer": "Geometry-only · current viewer session · no semantic component identity",
        "keyboard selector": "Inspectable mesh",
        "same-state command": "inspectionCommand={inspectionCommand}",
        "viewer state callback": "onInspectionChange={handleInspectionChange}",
        "clear selection": "Clear inspection",
        "unitless bounds": "unitless",
        "candidate record selection preserved": 'resource: "bluecad-candidate"',
    }, "workbench")

    if re.search(r"\b(?:Component ID|Engineering record ID|Semantic component ID)\b", workbench, re.IGNORECASE):
        fail("inspection UI claims semantic record/component identity")
    if "fetch(" in viewer or "XMLHttpRequest" in viewer or "WebSocket" in viewer:
        fail("inspection viewer adds an unauthorized backend/network path")
    if "localStorage" in viewer or "sessionStorage" in viewer or "localStorage" in workbench:
        fail("inspection adds persistence")
    if "uuid" in workbench.lower():
        fail("inspection exposes a Three.js UUID as UI/domain identity")


def check_status(status: str) -> None:
    rows = [line.strip() for line in status.splitlines() if line.strip().startswith("| 086 |")]
    if len(rows) != 1:
        fail(f"expected exactly one canonical 086 registry row; found {len(rows)}")
    cells = [cell.strip() for cell in rows[0].strip("|").split("|")]
    if len(cells) != 6:
        fail("086 registry row is malformed")
    if cells[1] not in {"ready", "in_progress", "in_review"}:
        fail(f"086 registry lifecycle is not implementation-compatible: {cells[1]}")


def self_test() -> None:
    valid_viewer = " ".join([
        "new THREE.Raycaster()", "getBoundingClientRect()", 'addEventListener("pointerdown"',
        'addEventListener("pointerup"', "Math.hypot", "intersectObjects(Array.from(meshByKey.values()), false)",
        "generationRef", "viewer-session-", "inspectionCommand.sessionKey !== sessionKeyRef.current",
        "GeometryInspectionMesh", "worldBounds", "triangleCount", "disposeOwnedScene",
        "selectCurrentMeshRef.current = null"
    ])
    valid_workbench = " ".join([
        "Geometry-only · current viewer session · no semantic component identity", "Inspectable mesh",
        "inspectionCommand={inspectionCommand}", "onInspectionChange={handleInspectionChange}",
        "Clear inspection", "unitless", 'resource: "bluecad-candidate"'
    ])
    check_sources(valid_viewer, valid_workbench)
    for bad_viewer in (valid_viewer + " fetch(", valid_viewer + " localStorage"):
        try:
            check_sources(bad_viewer, valid_workbench)
        except SystemExit:
            pass
        else:
            fail("self-test accepted forbidden viewer authority")
    try:
        check_sources(valid_viewer.replace("getBoundingClientRect()", ""), valid_workbench)
    except SystemExit:
        pass
    else:
        fail("self-test accepted non-canvas-relative pointer inspection")
    try:
        validate_scope({"frontend/src/components/BluecadGlbViewer.tsx", "backend/routes/inspection.py"})
    except SystemExit:
        pass
    else:
        fail("self-test accepted backend scope expansion")
    check_status("| 086 | ready | — | MODEL-INSPECTION-A0 | 006, 085 | geometry |")
    print("MODEL-INSPECTION-A0 self-test passed")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    validate_scope(changed_paths())
    check_sources(read(VIEWER), read(WORKBENCH))
    check_status(read(STATUS))
    print("MODEL-INSPECTION-A0 conformance check passed")


if __name__ == "__main__":
    main()
