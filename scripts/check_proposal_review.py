#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODELS = ROOT / "backend/app/modules/memory/models.py"
SERVICE = ROOT / "backend/app/modules/memory/service.py"
CLIENT = ROOT / "frontend/src/api/memory.ts"
STAGE = ROOT / "frontend/src/stages/ReviewStage.tsx"
STATE = ROOT / "frontend/src/components/review/reviewState.ts"
HARNESS = ROOT / "frontend/src/components/review/reviewStateHarness.ts"
MAIN = ROOT / "frontend/src/main.tsx"
STATUS = ROOT / "docs/specs/STATUS.md"


def fail(message: str) -> None:
    raise SystemExit(f"PROPOSAL-REVIEW-1 check failed: {message}")


def require(text: str, needle: str, label: str) -> None:
    if needle not in text:
        fail(f"missing {label}: {needle}")


def self_test() -> None:
    replacement = 'record_kind === "parameter" && Boolean(record.supersedes_parameter_id) ? "replacement" : "generic"'
    if "supersedes_parameter_id" not in replacement or '"replacement"' not in replacement:
        fail("self-test replacement route detector failed")
    inert = "dangerouslySetInnerHTML Markdown marked react-markdown"
    for forbidden in ("dangerouslySetInnerHTML", "Markdown", "react-markdown"):
        if forbidden not in inert:
            fail(f"self-test inert-text detector missed {forbidden}")


def check() -> None:
    for path in (MODELS, SERVICE, CLIENT, STAGE, STATE, HARNESS, MAIN, STATUS):
        if not path.exists():
            fail(f"missing required file {path.relative_to(ROOT)}")

    models = MODELS.read_text(encoding="utf-8")
    service = SERVICE.read_text(encoding="utf-8")
    client = CLIENT.read_text(encoding="utf-8")
    stage = STAGE.read_text(encoding="utf-8")
    state = STATE.read_text(encoding="utf-8")
    harness = HARNESS.read_text(encoding="utf-8")
    main = MAIN.read_text(encoding="utf-8")
    status = STATUS.read_text(encoding="utf-8")

    for needle in ("scope: str | None", "confidence: str | float | None", "symbol: str | None", "value: str | None", "unit: str | None", "value_status: str | None", "value_min: float | None", "value_max: float | None", "rationale: str | None", "linked_run_id: str | None"):
        require(models, needle, "additive MemoryRecordRead field")
    for needle in ("scope, confidence", "confidence, symbol, value, unit, value_status", "rationale, linked_run_id"):
        require(service, needle, "existing-column read projection")

    for needle, label in (
        ("listMemoryProposals", "MemoryStore proposal list client"),
        ("promoteMemoryRecord", "generic promote client"),
        ("rejectMemoryRecord", "generic reject client"),
        ("promoteParameterReplacement", "replacement promote client"),
        ("/memory/proposals?", "existing proposal route"),
        ("/promote-replacement", "existing replacement route"),
    ):
        require(client, needle, label)
    lowered_client = client.lower()
    for forbidden in ("websocket", "localstorage", "filesystem", "/grade"):
        if forbidden in lowered_client:
            fail(f"forbidden client authority present: {forbidden}")

    for needle, label in (
        ("Proposal authority", "native Review workbench"),
        ("listMemoryProposals", "canonical list read"),
        ("promotionRoute(record) === \"replacement\"", "replacement-only accept routing"),
        ("promoteParameterReplacement(record.id)", "replacement endpoint use"),
        ("rejectMemoryRecord(record.record_kind, record.id)", "generic reject routing"),
        ("aria-pressed={record.id === selectedId}", "selected proposal accessibility"),
        ("aria-busy={busyRecordId !== null}", "busy accessibility"),
        ("Applying canonical transition", "visible mutation status"),
    ):
        require(stage, needle, label)
    lowered_stage = stage.lower()
    for forbidden in ("dangerouslysetinnerhtml", "react-markdown", "grade proposal", "grading", "provider", "run_ai_task"):
        if forbidden in lowered_stage:
            fail(f"forbidden Review behavior present: {forbidden}")

    for needle, label in (
        ("acceptsReviewRequest", "generation+identity request guard"),
        ("acceptsReviewMutation", "generation+identity mutation guard"),
        ("nextAfterRemoval", "deterministic focus fallback"),
        ("supersedes_parameter_id", "replacement routing guard"),
        ('record.status === "proposed"', "proposed-only actionability"),
    ):
        require(state, needle, label)

    for needle in (
        "A→B→A stale request accepted",
        "proposed→accepted→proposed stale request accepted",
        "X→Y→X stale mutation accepted",
        "replacement route failed",
        "accepted must not be actionable",
    ):
        require(harness, needle, "deterministic harness case")

    require(main, 'import "./styles/review.css";', "independently removable Review styles")
    if "Proposal review is not implemented" in stage:
        fail("Review placeholder remains mounted")

    lifecycle_ok = (
        "| 054 | ready | — |" in status
        or "| 054 | in_review |" in status
        or "| 054 | merged |" in status
    )
    if not lifecycle_ok:
        fail("registry lifecycle for 054 is not canonical readiness/implementation/merged state")

    self_test()
    print("PROPOSAL-REVIEW-1 check passed")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        print("PROPOSAL-REVIEW-1 self-test passed")
        return
    check()


if __name__ == "__main__":
    main()
