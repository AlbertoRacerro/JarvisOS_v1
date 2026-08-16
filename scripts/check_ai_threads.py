#!/usr/bin/env python3
"""Conformance checks for spec 090 AI-THREADS-0.

This checker freezes the high-risk cross-file seams and scope boundaries from the
090 readiness record. Runtime, integration, and browser tests remain authoritative
for behavior that cannot be proven from source shape alone.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]

ALLOWED_IMPLEMENTATION_PATHS = {
    "backend/app/core/ai_thread_schema.py",
    "backend/app/core/database.py",
    "backend/app/modules/ai/egress_runtime.py",
    "backend/app/modules/ai/execution.py",
    "backend/app/modules/ai/routes.py",
    "backend/app/modules/ai/thread_models.py",
    "backend/app/modules/ai/thread_routes.py",
    "backend/app/modules/ai/thread_service.py",
    "backend/app/modules/ai/token_flow_service.py",
    "backend/tests/test_ai_threads.py",
    "docs/specs/STATUS.md",
    "frontend/src/App.tsx",
    "frontend/src/api/threads.ts",
    "frontend/src/app/routes.ts",
    "frontend/src/components/threads/threadState.ts",
    "frontend/src/components/threads/threadStateHarness.ts",
    "frontend/src/main.tsx",
    "frontend/src/pages/AIThreads.tsx",
    "frontend/src/styles/ai-threads.css",
    "scripts/check_ai_threads.py",
}


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


def _require_any(text: str, needles: tuple[str, ...], label: str) -> None:
    if not any(needle in text for needle in needles):
        raise CheckFailure(f"missing {label}: expected one of {needles!r}")


def _pull_request_changed_paths() -> set[str] | None:
    """Return the PR diff paths when running on GitHub's pull_request merge ref.

    GitHub checks out a synthetic merge commit for pull_request workflows. Its
    first parent is the exact base; diffing parent 1 to HEAD therefore checks the
    entire PR allow-list without requiring an extra network fetch. Outside that
    environment this proof is intentionally skipped rather than guessed.
    """

    if os.environ.get("GITHUB_EVENT_NAME") != "pull_request":
        return None
    try:
        completed = subprocess.run(
            ["git", "diff", "--name-only", "HEAD^1", "HEAD"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise CheckFailure(f"cannot resolve pull-request changed paths: {exc}") from exc
    return {line.strip() for line in completed.stdout.splitlines() if line.strip()}


def _check_scope(paths: set[str] | None) -> None:
    if paths is None:
        return
    unexpected = sorted(paths - ALLOWED_IMPLEMENTATION_PATHS)
    if unexpected:
        raise CheckFailure(f"090 implementation changed paths outside frozen allow-list: {unexpected}")
    for prefix, label in (
        (".github/", "workflow"),
        ("frontend/package", "frontend package/lockfile"),
    ):
        forbidden = sorted(path for path in paths if path.startswith(prefix))
        if forbidden:
            raise CheckFailure(f"090 implementation changed forbidden {label} paths: {forbidden}")
    for exact, label in (
        ("backend/app/modules/ai/provider_registry.py", "provider registry"),
        ("backend/app/modules/ai/models.py", "public AI request models"),
        ("backend/app/core/token_flow_schema.py", "token-flow schema"),
    ):
        if exact in paths:
            raise CheckFailure(f"090 implementation changed forbidden {label}: {exact}")


def check_sources(reader=_read, *, changed_paths: set[str] | None = None) -> None:
    token_flow = reader("backend/app/modules/ai/token_flow_service.py")
    execution = reader("backend/app/modules/ai/execution.py")
    egress = reader("backend/app/modules/ai/egress_runtime.py")
    threads = reader("backend/app/modules/ai/thread_service.py")
    schema = reader("backend/app/core/ai_thread_schema.py")
    task_models = reader("backend/app/modules/ai/models.py")
    memory_api = reader("backend/app/modules/memory/api.py")
    client = reader("frontend/src/api/threads.ts")
    stage = reader("frontend/src/pages/AIThreads.tsx")
    routes = reader("frontend/src/app/routes.ts")
    app = reader("frontend/src/App.tsx")
    state = reader("frontend/src/components/threads/threadState.ts")
    harness = reader("frontend/src/components/threads/threadStateHarness.ts")
    status = reader("docs/specs/STATUS.md")

    _check_scope(changed_paths)

    # Canonical pre-created-flow authority: one shared creator, no duplicate SQL,
    # internal-only consumption, and exact validation before execution/egress.
    _require(token_flow, "def create_flow_in_transaction", "shared transactional flow helper")
    _require(threads, "create_flow_in_transaction", "thread reuse of shared flow helper")
    _forbid(threads, "INSERT INTO ai_flows", "duplicate token-flow insert in thread service")
    _require(execution, "existing_flow_id", "run_ai_task pre-created flow seam")
    _require(egress, "existing_flow_id", "egress pre-created flow seam")
    _require(token_flow, "validate_existing_flow_for_execution", "pre-created flow validation")
    for needle, label in (
        ('row["state"] != "running"', "running-state guard"),
        ('row["task_kind"] != task_kind', "task-kind identity guard"),
        ('_nonnegative_int(row["attempt_count"], "attempt_count") != 0', "zero-attempt guard"),
        ("SELECT COUNT(*) AS n FROM ai_jobs WHERE flow_id = ?", "unused-flow job guard"),
        ("terminal_reason", "terminal metadata guard"),
    ):
        _require(token_flow, needle, label)
    _forbid(task_models, "existing_flow_id", "public task request pre-created-flow control")

    # Durable idempotent ownership is committed before dispatch and replay never
    # manufactures another request/flow.
    for needle, label in (
        ("workspace_id", "workspace scope"),
        ("flow_id", "durable flow identity"),
        ("request_id", "idempotency key"),
        ("UNIQUE(thread_id, request_id)", "request id uniqueness"),
        ("UNIQUE(flow_id)", "flow ownership uniqueness"),
        ("BEGIN IMMEDIATE", "atomic reservation transaction"),
        ("persistence_state = 'dispatching'", "pre-dispatch state transition"),
        ("request_digest", "immutable submit digest"),
    ):
        _require(schema + threads, needle, label)
    _require(memory_api, "proposal", "proposal API continuity")
    _require(threads, "ai_flow_record_captures", "canonical proposal capture read")
    _forbid(schema, "provider_id", "provider copy in thread schema")
    _forbid(schema, "cost", "cost copy in thread schema")
    _forbid(schema, "latency", "latency copy in thread schema")
    _forbid(schema, "usage", "usage copy in thread schema")
    _forbid(schema, "egress_packet", "egress packet copy in thread schema")
    _forbid(schema, "proposal_body", "proposal body copy in thread schema")

    # Egress/privacy: only the current prompt is passed to canonical execution;
    # thread history is never serialized as provider context.
    _require(threads, "context_blocks=None", "explicit no-history context handoff")
    for forbidden in ("messages=", "thread_history", "conversation_history"):
        _forbid(threads, forbidden, "thread-history egress construction")

    # Product surface remains secondary and inherits App-owned workspace authority.
    _require(client, "/ai/threads", "AI thread client route")
    _require(routes, '{ id: "ai-threads", path: "/ai-threads", title: "AI Threads" }', "non-primary route")
    _forbid(routes, '{ id: "ai-threads", label:', "primary AI-threads navigation item")
    _require(stage, "workspaceId", "App-owned workspace consumption")
    _require(app, "workspaceId", "App workspace authority")
    _forbid(stage, 'fetch("https://', "direct external-provider fetch from UI")
    _forbid(stage, "dangerouslySetInnerHTML", "executable/untrusted HTML rendering")
    for forbidden in ("react-markdown", "ReactMarkdown", "marked("):
        _forbid(stage, forbidden, "Markdown execution")

    # Generation/identity guards must cover the readiness race matrix and harness.
    for needle, label in (
        ("workspace", "workspace generation/identity state"),
        ("thread", "thread generation/identity state"),
        ("submit", "submit generation/identity state"),
        ("request", "request identity state"),
    ):
        _require(state + harness, needle, label)
    _require_any(harness, ("A", "workspace-a"), "workspace race harness fixture")
    _require_any(harness, ("X", "thread-x"), "thread race harness fixture")

    # Lifecycle is explicit and 062/091/frozen orchestration surfaces remain out.
    _require_any(
        status,
        ("| 090 | ready |", "| 090 | in_review |", "| 090 | merged |"),
        "090 lifecycle",
    )
    if "| 090 | in_review |" in status:
        _require(status, "pull/276", "090 implementation PR registry link")
    for forbidden, label in (
        ("grade", "062 grade surface"),
        ("hermes", "Hermes runtime"),
        ("mcp", "MCP runtime"),
        ("autonomous agent", "autonomous-agent surface"),
    ):
        _forbid((threads + stage + schema).lower(), forbidden, label)


def _self_test() -> None:
    base = {
        "backend/app/modules/ai/token_flow_service.py": (
            'def create_flow_in_transaction(): pass\n'
            'validate_existing_flow_for_execution\n'
            'row["state"] != "running"\nrow["task_kind"] != task_kind\n'
            '_nonnegative_int(row["attempt_count"], "attempt_count") != 0\n'
            'SELECT COUNT(*) AS n FROM ai_jobs WHERE flow_id = ?\nterminal_reason\n'
        ),
        "backend/app/modules/ai/execution.py": "def run_ai_task(existing_flow_id=None): pass\n",
        "backend/app/modules/ai/egress_runtime.py": "def run_external_task(existing_flow_id=None): pass\n",
        "backend/app/modules/ai/thread_service.py": (
            "create_flow_in_transaction()\nworkspace_id flow_id request_id request_digest\n"
            "BEGIN IMMEDIATE\npersistence_state = 'dispatching'\ncontext_blocks=None\n"
            "ai_flow_record_captures\n"
        ),
        "backend/app/core/ai_thread_schema.py": (
            "workspace_id flow_id request_id UNIQUE(thread_id, request_id) UNIQUE(flow_id)\n"
        ),
        "backend/app/modules/ai/models.py": "class AITaskRunRequest: pass\n",
        "backend/app/modules/memory/api.py": "proposal\n",
        "frontend/src/api/threads.ts": "/ai/threads\n",
        "frontend/src/pages/AIThreads.tsx": "workspaceId\n",
        "frontend/src/app/routes.ts": '{ id: "ai-threads", path: "/ai-threads", title: "AI Threads" }\n',
        "frontend/src/App.tsx": "workspaceId\n",
        "frontend/src/components/threads/threadState.ts": "workspace thread submit request\n",
        "frontend/src/components/threads/threadStateHarness.ts": "workspace thread submit request A X\n",
        "docs/specs/STATUS.md": "| 090 | in_review | [#276](https://github.com/x/pull/276) |\n",
    }

    check_sources(lambda path: base[path])

    bad = dict(base)
    bad["backend/app/modules/ai/thread_service.py"] += "INSERT INTO ai_flows\n"
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

    bad = dict(base)
    bad["backend/app/modules/ai/models.py"] += "existing_flow_id: str | None = None\n"
    try:
        check_sources(lambda path: bad[path])
    except CheckFailure:
        pass
    else:
        raise AssertionError("self-test failed to reject public existing_flow_id")

    try:
        _check_scope({"backend/app/modules/ai/provider_registry.py"})
    except CheckFailure:
        pass
    else:
        raise AssertionError("self-test failed to reject out-of-scope provider registry change")

    bad = dict(base)
    bad["backend/app/core/ai_thread_schema.py"] += "provider_id TEXT\n"
    try:
        check_sources(lambda path: bad[path])
    except CheckFailure:
        pass
    else:
        raise AssertionError("self-test failed to reject provider copy in thread schema")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    try:
        if args.self_test:
            _self_test()
            print("check_ai_threads self-test: PASS")
        else:
            check_sources(changed_paths=_pull_request_changed_paths())
            print("check_ai_threads: PASS")
    except (CheckFailure, AssertionError, OSError) as exc:
        print(f"check_ai_threads: FAIL: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
