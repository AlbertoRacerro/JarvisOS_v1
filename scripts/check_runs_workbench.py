#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "frontend/src/App.tsx"
PAGE = ROOT / "frontend/src/pages/RunsWorkbench.tsx"
API = ROOT / "frontend/src/api/runs.ts"
STATE = ROOT / "frontend/src/components/runs/state.ts"
MAIN = ROOT / "frontend/src/main.tsx"
STATUS = ROOT / "docs/specs/STATUS.md"


def fail(message: str) -> None:
    raise SystemExit(f"RUNS-WORKBENCH-1 check failed: {message}")


def require(text: str, needle: str, label: str) -> None:
    if needle not in text:
        fail(f"missing {label}: {needle}")


def self_test() -> None:
    sample = 'case "runs": content = <MigrationPendingSurface title="Runs" />;'
    if "MigrationPendingSurface" not in sample:
        fail("self-test placeholder detector failed")
    unsafe = "stored_path relative_path"
    if "stored_path" not in unsafe:
        fail("self-test path detector failed")
    if re.search(r"\beta\b", "metadata", re.IGNORECASE):
        fail("self-test ETA detector matched metadata")
    if not re.search(r"\beta\b", "Progress ETA confidence", re.IGNORECASE):
        fail("self-test ETA detector missed standalone ETA")


def check() -> None:
    for path in (APP, PAGE, API, STATE, MAIN, STATUS):
        if not path.exists():
            fail(f"missing required file {path.relative_to(ROOT)}")
    app = APP.read_text(encoding="utf-8")
    page = PAGE.read_text(encoding="utf-8")
    api = API.read_text(encoding="utf-8")
    state = STATE.read_text(encoding="utf-8")
    main = MAIN.read_text(encoding="utf-8")
    status = STATUS.read_text(encoding="utf-8")

    if 'case "runs"' not in app or "<RunsWorkbench" not in app:
        fail("/runs is not mounted to the native workbench")
    if 'title="Runs" description="The dedicated run list' in app:
        fail("/runs remains placeholder-only")
    require(app, "workspaceId={workspaceId}", "App workspace binding")
    require(app, "onWorkspaceChange={setWorkspaceId}", "App workspace callback")

    for needle, label in (
        ("SimulationRunSummary", "typed run summary"),
        ("SimulationRunDetail", "typed run detail"),
        ("RunLog", "typed log read"),
        ("RunArtifact", "typed artifact read"),
        ("RunsRequestError", "HTTP identity for disappeared detail"),
        ("listRuns", "run list client"),
        ("getRun", "run detail client"),
        ("listRunLogs", "run logs client"),
        ("listRunArtifacts", "run artifacts client"),
    ):
        require(api, needle, label)
    if "stored_path" in api or "relative_path" in api:
        fail("088 frontend artifact model exposes filesystem-oriented path fields")

    for needle, label in (
        ("acceptsResponse", "generation+identity response guard"),
        ("chooseSelection", "deterministic selection helper"),
        ("projectPayload", "bounded payload projection"),
        ("Payload unavailable / malformed", "malformed payload state"),
        ("No persisted", "null payload state"),
        ("MAX_DEPTH = 4", "payload nesting limit"),
        ("MAX_ITEMS = 50", "payload item limit"),
        ("MAX_STRING = 2_000", "payload string limit"),
        ("MAX_TOTAL = 20_000", "payload total limit"),
    ):
        require(state, needle, label)

    for needle, label in (
        ("Selected run hidden by current filter", "hidden-selection explanation"),
        ("Selected run is no longer available", "disappeared-detail state"),
        ("No persisted logs", "empty logs state"),
        ("No persisted artifacts", "empty artifacts state"),
        ("under_data_root", "storage-boundary evidence"),
        ("workspaceGeneration", "workspace request generation"),
        ("listGeneration", "list request generation"),
        ("detailGeneration", "detail request generation"),
        ("logsGeneration", "logs request generation"),
        ("artifactsGeneration", "artifact request generation"),
        ("pendingRefreshFocus", "refresh focus recovery"),
        ("data-run-id", "focused run identity"),
        ("searchRef", "stable focus fallback"),
        ("aria-pressed", "keyboard-native selected run state"),
    ):
        require(page, needle, label)

    lowered = page.lower()
    for forbidden in ("setinterval", "polling", "live tail", "rerun", "cancel run", "delete run", "create run", "confidence score", "health score"):
        if forbidden in lowered:
            fail(f"forbidden run mutation/fake authority present: {forbidden}")
    if re.search(r"\beta\b", page, re.IGNORECASE):
        fail("forbidden run mutation/fake authority present: eta")
    if "dangerouslySetInnerHTML" in page or "react-markdown" in page:
        fail("unsafe payload/log rendering path present")
    if "stored_path" in page or "relative_path" in page:
        fail("filesystem-oriented artifact path rendered by 088")

    require(main, 'import "./styles/runs.css";', "independently removable runs styles")
    lifecycle_ok = (
        "| 088 | in_review | [#256]" in status
        or "| 088 | ready | — |" in status
        or "| 088 | merged | [#256](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/256) |" in status
    )
    if not lifecycle_ok:
        fail("registry lifecycle for 088 is not a canonical readiness, implementation, or merged state")

    self_test()
    print("RUNS-WORKBENCH-1 check passed")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        print("RUNS-WORKBENCH-1 self-test passed")
        return
    check()


if __name__ == "__main__":
    main()
