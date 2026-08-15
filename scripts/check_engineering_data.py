#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "frontend/src/App.tsx"
PAGE = ROOT / "frontend/src/pages/EngineeringData.tsx"
STATE = ROOT / "frontend/src/components/engineering-data/engineeringDataState.ts"
HARNESS = ROOT / "frontend/src/components/engineering-data/engineeringDataStateHarness.ts"
MAIN = ROOT / "frontend/src/main.tsx"
STATUS = ROOT / "docs/specs/STATUS.md"
CLIENT = ROOT / "frontend/src/api/client.ts"


def fail(message: str) -> None:
    raise SystemExit(f"ENGINEERING-DATA-1 check failed: {message}")


def require(text: str, needle: str, label: str) -> None:
    if needle not in text:
        fail(f"missing {label}: {needle}")


def self_test() -> None:
    unsafe = "JSON.stringify(record)"
    if "JSON.stringify" not in unsafe:
        fail("self-test whole-object search detector failed")
    if re.search(r"\b(fresh|stale|proposed|rejected)\b", "Freshness Unavailable", re.IGNORECASE):
        fail("self-test fake-authority detector matched honest unavailable label")
    if not re.search(r"\b(stale|proposed)\b", "stale proposed", re.IGNORECASE):
        fail("self-test fake-authority detector missed fake state")


def check() -> None:
    for path in (APP, PAGE, STATE, HARNESS, MAIN, STATUS, CLIENT):
        if not path.exists():
            fail(f"missing required file {path.relative_to(ROOT)}")
    app = APP.read_text(encoding="utf-8")
    page = PAGE.read_text(encoding="utf-8")
    state = STATE.read_text(encoding="utf-8")
    harness = HARNESS.read_text(encoding="utf-8")
    main = MAIN.read_text(encoding="utf-8")
    status = STATUS.read_text(encoding="utf-8")
    client = CLIENT.read_text(encoding="utf-8")

    require(app, 'case "engineering-data"', "engineering-data route")
    require(app, "<EngineeringData", "native engineering-data mount")
    if 'title="Engineering Data" description="Searchable engineering-record navigation belongs' in app:
        fail("/engineering-data remains placeholder-only")
    require(app, "workspaceId={workspaceId}", "App workspace binding")
    require(app, "onWorkspaceChange={setWorkspaceId}", "App workspace callback")

    for needle in ("listModelSpecs", "listAssumptions", "listParameters", "listDecisions"):
        require(client, f"export function {needle}", f"existing {needle} read contract")
        require(page, needle, f"035 consumption of {needle}")

    for needle, label in (
        ("ENGINEERING_KINDS", "fixed kind set"),
        ("projectEngineeringData", "typed explicit projection"),
        ("visibleEngineeringRecords", "explicit-field filtering"),
        ("chooseEngineeringSelection", "deterministic selection recovery"),
        ("acceptsWorkspaceResponse", "workspace generation guard"),
        ('toLocaleLowerCase("en-US")', "pinned Unicode-aware lowercase"),
    ):
        require(state, needle, label)
    if "JSON.stringify" in state or "JSON.stringify" in page:
        fail("whole-object stringify/search path present")

    for needle, label in (
        ("workspaceDiscoveryGeneration", "workspace discovery guard"),
        ("recordsGeneration", "record generation guard"),
        ("Model specs unavailable.", "model-spec partial failure"),
        ("Assumptions unavailable.", "assumption partial failure"),
        ("Parameters unavailable.", "parameter partial failure"),
        ("Decisions unavailable.", "decision partial failure"),
        ("Confidence (persisted)", "honest persisted confidence label"),
        ("Value (persisted text)", "inert parameter value"),
        ('label="Freshness" value="Unavailable"', "honest unavailable freshness"),
        ("aria-pressed", "native selected row semantics"),
        ("Open legacy Domain Foundation", "legacy continuity link"),
        ('href="/design/flowsheet"', "lineage navigation"),
        ('href="/runs"', "runs navigation"),
    ):
        require(page, needle, label)

    lowered = page.lower()
    for forbidden in ("promote", "reject proposal", "recompute", "confidence score", "correctness probability"):
        if forbidden in lowered:
            fail(f"forbidden mutation/fake authority present: {forbidden}")
    fake_state = re.compile(r"\b(fresh|stale|proposed|rejected)\b", re.IGNORECASE)
    honest = page.replace('label="Freshness" value="Unavailable"', "")
    if fake_state.search(honest):
        fail("035 presents freshness/proposal authority not present in record contracts")

    require(main, 'import "./styles/engineering-data.css";', "independently removable engineering-data styles")
    require(harness, "stale A-B-A response accepted", "state harness stale-response case")
    require(harness, "unknown status became hidden", "state harness unknown-status case")
    lifecycle_ok = "| 035 | in_review |" in status or "| 035 | ready | — |" in status or "| 035 | merged |" in status
    if not lifecycle_ok:
        fail("registry lifecycle for 035 is not canonical readiness/implementation/merged state")

    self_test()
    print("ENGINEERING-DATA-1 check passed")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        print("ENGINEERING-DATA-1 self-test passed")
        return
    check()


if __name__ == "__main__":
    main()
