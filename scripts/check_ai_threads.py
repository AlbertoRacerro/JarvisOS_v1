#!/usr/bin/env python3
"""Conformance checks for spec 090 AI-THREADS-0.

This checker is intentionally source-level and dependency-free. Runtime/browser tests
remain authoritative for behaviour; these checks freeze the minimum cross-file seams
and reject known scope regressions that are easy to reintroduce accidentally.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]


class CheckFailure(RuntimeError):
    pass


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _require(text: str, needle: str, label: str) -> None:
    if needle not in text:
        raise CheckFailure(f"missing {label}: {needle!r}")


def _forbid(text: str, needle: str, label: str) -> None:
    if needle in text:
        raise CheckFailure(f"forbidden {label}: {needle!r}")


def check_sources(reader=_read) -> None:
    token_flow = reader("backend/app/modules/ai/token_flow_service.py")
    execution = reader("backend/app/modules/ai/execution.py")
    egress = reader("backend/app/modules/ai/egress_runtime.py")
    threads = reader("backend/app/modules/ai/thread_service.py")
    thread_store = reader("backend/app/modules/ai/thread_store.py")
    memory_api = reader("backend/app/modules/memory/api.py")
    client = reader("frontend/src/api/client.ts")
    stage = reader("frontend/src/workbenches/AiThreadsStage.tsx")

    # Readiness-mandated single token-flow creation authority.
    _require(token_flow, "create_flow_in_transaction", "shared transactional flow helper")
    _require(threads, "create_flow_in_transaction", "thread reuse of shared flow helper")
    _forbid(threads, "INSERT INTO ai_core_token_flows", "duplicate token-flow insert in thread service")

    # Pre-created flow seam must reach the shared egress path; omitted seam keeps legacy callers valid.
    _require(execution, "existing_flow_id", "run_ai_task pre-created flow seam")
    _require(egress, "existing_flow_id", "egress pre-created flow seam")
    _require(execution, "run_ai_task", "shared execution entry point")
    _require(egress, "run_external_task", "shared external execution entry point")

    # Thread durability and MemoryStore proposal reference surface stay explicit and workspace scoped.
    for needle, label in (
        ("workspace_id", "workspace scope"),
        ("flow_id", "durable flow identity"),
        ("client_request_id", "idempotency key"),
    ):
        _require(thread_store + threads, needle, label)
    _require(memory_api, "proposal", "proposal API continuity")

    # UI must remain a dedicated non-primary workbench over typed API calls, not fabricated provider state.
    _require(client, "ai-thread", "AI thread client route")
    _require(stage, "workspaceId", "App-owned workspace consumption")
    _forbid(stage, "fetch(\"https://", "direct external-provider fetch from UI")


def _self_test() -> None:
    base = {
        "backend/app/modules/ai/token_flow_service.py": "def create_flow_in_transaction(): pass\n",
        "backend/app/modules/ai/execution.py": "def run_ai_task(existing_flow_id=None): pass\n",
        "backend/app/modules/ai/egress_runtime.py": "def run_external_task(existing_flow_id=None): pass\n",
        "backend/app/modules/ai/thread_service.py": "create_flow_in_transaction()\nworkspace_id flow_id client_request_id\n",
        "backend/app/modules/ai/thread_store.py": "workspace_id flow_id client_request_id\n",
        "backend/app/modules/memory/api.py": "proposal\n",
        "frontend/src/api/client.ts": "ai-thread\n",
        "frontend/src/workbenches/AiThreadsStage.tsx": "workspaceId\n",
    }

    def reader(path: str) -> str:
        return base[path]

    check_sources(reader)

    bad = dict(base)
    bad["backend/app/modules/ai/thread_service.py"] += "INSERT INTO ai_core_token_flows\n"
    try:
        check_sources(lambda path: bad[path])
    except CheckFailure:
        pass
    else:
        raise AssertionError("self-test failed to reject duplicate token-flow SQL")

    bad = dict(base)
    bad["backend/app/modules/ai/egress_runtime.py"] = "def run_external_task(): pass\n"
    try:
        check_sources(lambda path: bad[path])
    except CheckFailure:
        pass
    else:
        raise AssertionError("self-test failed to reject missing egress pre-created-flow seam")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    try:
        if args.self_test:
            _self_test()
            print("check_ai_threads self-test: PASS")
        else:
            check_sources()
            print("check_ai_threads: PASS")
    except (CheckFailure, AssertionError, OSError) as exc:
        print(f"check_ai_threads: FAIL: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
