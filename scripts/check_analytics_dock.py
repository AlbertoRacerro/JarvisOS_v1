#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "frontend/src/App.tsx"
COMPONENT = ROOT / "frontend/src/components/analytics/AnalyticsDockContent.tsx"
STATE = ROOT / "frontend/src/components/analytics/analyticsState.ts"
HARNESS = ROOT / "frontend/src/components/analytics/analyticsStateHarness.ts"
MAIN = ROOT / "frontend/src/main.tsx"
STATUS = ROOT / "docs/specs/STATUS.md"


def fail(message: str) -> None:
    raise SystemExit(f"ANALYTICS-DOCK-1 check failed: {message}")


def require(text: str, needle: str, label: str) -> None:
    if needle not in text:
        fail(f"missing {label}: {needle}")


def self_test() -> None:
    forbidden = "mean median standard deviation percentage ranking score chart"
    for needle in ("mean", "median", "percentage", "ranking", "chart"):
        if needle not in forbidden:
            fail(f"self-test forbidden semantic detector missed {needle}")
    exact = '(model_version_id, output_key) exact unit equality'
    if "model_version_id" not in exact or "output_key" not in exact or "exact unit" not in exact:
        fail("self-test metric/unit authority detector failed")


def check() -> None:
    for path in (APP, COMPONENT, STATE, HARNESS, MAIN, STATUS):
        if not path.exists():
            fail(f"missing required file {path.relative_to(ROOT)}")
    app = APP.read_text(encoding="utf-8")
    component = COMPONENT.read_text(encoding="utf-8")
    state = STATE.read_text(encoding="utf-8")
    harness = HARNESS.read_text(encoding="utf-8")
    main = MAIN.read_text(encoding="utf-8")
    status = STATUS.read_text(encoding="utf-8")

    require(app, "AnalyticsDockContent", "analytics dock contribution")
    require(app, 'route.id === "runs" || route.id === "engineering-data"', "bounded native route mounting")
    require(app, "dock: <AnalyticsDockContent", "existing dock content slot")
    if "new AnalysisDock" in app or "analytics-route" in app:
        fail("new analytics container/route detected")

    for needle, label in (
        ("MAX_SELECTED_RUNS = 6", "six-run cap"),
        ("MAX_OUTPUT_KEYS = 128", "output-key cap"),
        ("MAX_OUTPUT_PAYLOAD_BYTES = 1_048_576", "payload byte cap"),
        ("acceptsWorkspaceResponse", "generation+workspace guard"),
        ("modelVersionId", "model-version metric identity"),
        ("rejectedKeys", "per-metric rejection"),
        ("units.size !== 1", "exact unit equality gate"),
        ("No conversion was applied", "explicit no-conversion rejection"),
        ("max - min", "bounded range summary"),
    ):
        require(state, needle, label)

    lowered_state = state.lower()
    for forbidden in ("unit map", "convertunit", "unit alias", "mean(", "median", "standard deviation", "percent change", "ranking", "score"):
        if forbidden in lowered_state:
            fail(f"forbidden analytics authority/statistic present: {forbidden}")

    for needle, label in (
        ("listRuns", "existing run list contract"),
        ('type="checkbox"', "native multi-selection controls"),
        ("Six-run comparison limit reached", "selection-cap feedback"),
        ("Direct comparison requires the same exact model version", "operator comparability disclosure"),
        ("Minimum", "minimum summary"),
        ("Maximum", "maximum summary"),
        ("Range", "range summary"),
        ('aria-live="polite"', "comparison status announcement"),
    ):
        require(component, needle, label)

    lowered_component = component.lower()
    for forbidden in ("confidence", "health score", "ai insight", "optimization score", "trend score"):
        if forbidden in lowered_component:
            fail(f"fake analytics authority present: {forbidden}")
    if "<svg" in lowered_component or "canvas" in lowered_component:
        fail("chart/graphics surface added to minimum analytics dock")

    require(main, 'import "./styles/analytics.css";', "independently removable analytics styles")
    require(harness, "stale A-B-A response accepted", "A-B-A stale-response harness case")
    require(harness, "Pa/kPa mismatch was converted or accepted", "exact-unit rejection harness case")
    require(harness, "six-run cap was not enforced", "selection bound harness case")

    lifecycle_ok = (
        "| 089 | ready | — |" in status
        or "| 089 | in_review |" in status
        or "| 089 | merged |" in status
    )
    if not lifecycle_ok:
        fail("registry lifecycle for 089 is not canonical readiness/implementation/merged state")

    self_test()
    print("ANALYTICS-DOCK-1 check passed")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        print("ANALYTICS-DOCK-1 self-test passed")
        return
    check()


if __name__ == "__main__":
    main()
