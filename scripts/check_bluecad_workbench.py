#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend/src"
MODEL_STAGE = FRONTEND / "stages/ModelStage.tsx"
WORKBENCH = FRONTEND / "components/bluecad/BluecadWorkbench.tsx"
STATE = FRONTEND / "components/bluecad/workbenchState.ts"
HARNESS = FRONTEND / "components/bluecad/workbenchStateHarness.ts"
VIEWER = FRONTEND / "components/BluecadGlbViewer.tsx"
STATUS = ROOT / "docs/specs/STATUS.md"

ALLOWED = {
    "frontend/src/App.tsx",
    "frontend/src/stages/registry.ts",
    "frontend/src/stages/ModelStage.tsx",
    "frontend/src/pages/BlueCAD.tsx",
    "frontend/src/components/Layout.tsx",
    "frontend/src/components/BluecadGlbViewer.tsx",
    "frontend/src/components/shell/ContextualNavigator.tsx",
    "frontend/src/components/shell/ContextualSidecar.tsx",
    "frontend/src/components/shell/AnalysisDock.tsx",
    "frontend/src/components/bluecad/BluecadWorkbench.tsx",
    "frontend/src/components/bluecad/BluecadNavigator.tsx",
    "frontend/src/components/bluecad/BluecadSidecar.tsx",
    "frontend/src/components/bluecad/BluecadAnalysisDock.tsx",
    "frontend/src/components/bluecad/workbenchState.ts",
    "frontend/src/components/bluecad/workbenchStateHarness.ts",
    "frontend/src/api/client.ts",
    "frontend/src/styles/global.css",
    "scripts/check_app_shell.py",
    "scripts/check_bluecad_read_model.py",
    "scripts/check_bluecad_workbench.py",
    "docs/specs/STATUS.md",
}

FAKE_TELEMETRY = re.compile(
    r"(?:AI\s+confidence|system\s+health|CPU\s*%|GPU\s*%|memory\s*%|stress\s*[:=]|186\.4\s*MPa|87%\s*validation)",
    re.IGNORECASE,
)
FORBIDDEN_AUTHORITY = re.compile(r"(?:stored_path|JARVISOS_DATA_ROOT|filesystem|api[_-]?key|run_ai_task)", re.IGNORECASE)


def fail(message: str) -> None:
    print(f"BLUECAD workbench check failed: {message}", file=sys.stderr)
    raise SystemExit(1)


def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        fail(f"missing required file: {path.relative_to(ROOT)}")


def changed_paths() -> set[str]:
    event_path = __import__("os").environ.get("GITHUB_EVENT_PATH")
    base: str | None = None
    if event_path:
        import json
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
        fail(f"files outside 085 readiness boundary changed: {', '.join(unexpected)}")
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


def check_registry() -> None:
    status = read(STATUS)
    row = next((line for line in status.splitlines() if line.startswith("| 085 |")), None)
    if row is None:
        fail("spec 085 registry row is missing")
    expected_pr = "[#239](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/239)"
    if "| in_review |" not in row or expected_pr not in row:
        fail("spec 085 must be in_review with implementation PR #239")


def check_primary_composition() -> None:
    model = read(MODEL_STAGE)
    if 'from "../pages/BlueCAD"' in model or "<BlueCAD" in model:
        fail("ModelStage still compatibility-mounts the legacy stacked BlueCAD page")
    if 'from "../components/bluecad/BluecadWorkbench"' not in model or "<BluecadWorkbench" not in model:
        fail("ModelStage does not mount the native BLUECAD workbench")


def check_state_authority() -> None:
    workbench = read(WORKBENCH)
    state = read(STATE)
    harness = read(HARNESS)
    if "getBluecadCandidateAggregate" not in workbench:
        fail("visible workbench does not consume the 084 aggregate")
    if 'resource: "bluecad-candidate"' not in workbench:
        fail("candidate selection does not publish the typed BLUECAD RecordRef")
    if ">Refresh<" not in workbench and '"Refresh"' not in workbench:
        fail("explicit manual Refresh action is missing")
    required_exports = ("acceptsRequest", "acceptsMutation", "revalidateSelection", "mutationConflicts", "duplicateBrief")
    for symbol in required_exports:
        if f"export function {symbol}" not in state:
            fail(f"production state helper is missing {symbol}")
        if symbol not in harness:
            fail(f"state harness does not exercise/import {symbol}")
        if symbol not in workbench:
            fail(f"workbench does not delegate {symbol} decisions to production state helper")
    if './workbenchState' not in harness:
        fail("state harness does not import the production helper")


def check_viewer_cleanup() -> None:
    viewer = read(VIEWER)
    markers = (
        "disposeOwnedScene",
        "object.geometry?.dispose()",
        "material.dispose()",
        "value instanceof THREE.Texture",
        "if (disposed)",
        "disposeOwnedScene(gltf.scene)",
        "controls.dispose()",
        "renderer.dispose()",
    )
    for marker in markers:
        if marker not in viewer:
            fail(f"GLB owned-resource cleanup marker missing: {marker}")
    if 'aria-label", "Interactive 3D preview' not in viewer:
        fail("GLB canvas accessible label is missing")


def check_no_fake_authority() -> None:
    bodies = [read(WORKBENCH), read(VIEWER)]
    combined = "\n".join(bodies)
    if FAKE_TELEMETRY.search(combined):
        fail("mock workstation telemetry/confidence/engineering result introduced")
    if FORBIDDEN_AUTHORITY.search(combined):
        fail("forbidden filesystem/provider/private-path authority appears in 085 UI")


def self_test() -> None:
    validate_scope(set())
    validate_scope({"frontend/src/components/bluecad/BluecadWorkbench.tsx", "scripts/check_bluecad_workbench.py"})
    try:
        validate_scope({"backend/app/main.py"})
    except SystemExit:
        pass
    else:
        fail("negative scope self-test accepted backend change")
    if FAKE_TELEMETRY.search("AI confidence 92%") is None:
        fail("fake telemetry detector self-test failed")
    if FORBIDDEN_AUTHORITY.search("stored_path") is None:
        fail("forbidden authority detector self-test failed")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    self_test()
    if args.self_test:
        print("BLUECAD workbench checker self-test passed")
        return
    validate_scope(changed_paths())
    check_registry()
    check_primary_composition()
    check_state_authority()
    check_viewer_cleanup()
    check_no_fake_authority()
    print("BLUECAD workbench checks passed")


if __name__ == "__main__":
    main()
