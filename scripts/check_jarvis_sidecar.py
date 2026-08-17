#!/usr/bin/env python3
"""Conformance checks for spec 091 JARVIS-SIDECAR-1.

The checker freezes the minimum authority/composition seams from 091 readiness.
Behavioral race, browser, and provider-policy evidence remains mandatory in
addition to these source/scope assertions.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]

ALLOWED_IMPLEMENTATION_PATHS = {
    "backend/app/modules/ai/thread_models.py",
    "backend/app/modules/ai/thread_service.py",
    "backend/tests/test_ai_threads.py",
    "docs/specs/STATUS.md",
    "frontend/src/App.tsx",
    "frontend/src/api/threads.ts",
    "frontend/src/components/ai/JarvisSidecar.css",
    "frontend/src/components/ai/useJarvisSidecar.tsx",
    "frontend/src/components/ai/jarvisSidecarState.ts",
    "frontend/src/components/ai/jarvisSidecarStateHarness.ts",
    "frontend/src/pages/AIThreads.tsx",
    "scripts/check_jarvis_sidecar.py",
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


def _pull_request_changed_paths() -> set[str] | None:
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
        raise CheckFailure(f"091 implementation changed paths outside frozen allow-list: {unexpected}")
    forbidden_prefixes = (".github/", "frontend/package")
    forbidden = sorted(path for path in paths if path.startswith(forbidden_prefixes))
    if forbidden:
        raise CheckFailure(f"091 implementation changed forbidden workflow/package paths: {forbidden}")
    for exact in (
        "backend/app/modules/ai/models.py",
        "backend/app/modules/ai/egress_policy.py",
        "backend/app/modules/ai/egress_runtime.py",
        "backend/app/modules/ai/execution.py",
        "frontend/src/components/Layout.tsx",
        "frontend/src/components/shell/ContextualSidecar.tsx",
    ):
        if exact in paths:
            raise CheckFailure(f"091 implementation changed existing authority outside readiness: {exact}")


def check_sources(reader=_read, *, changed_paths: set[str] | None = None) -> None:
    models = reader("backend/app/modules/ai/thread_models.py")
    service = reader("backend/app/modules/ai/thread_service.py")
    app = reader("frontend/src/App.tsx")
    api = reader("frontend/src/api/threads.ts")
    sidecar = reader("frontend/src/components/ai/useJarvisSidecar.tsx")
    status = reader("docs/specs/STATUS.md")

    _check_scope(changed_paths)

    for needle, label in (
        ("context_selection", "bounded context selection field"),
        ("expected_context_digest", "preview digest binding field"),
        ("model_validator", "paired context-field validation"),
    ):
        _require(models, needle, label)
    _forbid(models, "context_blocks", "raw context-block thread API")

    for needle, label in (
        ("_find_existing_interaction", "duplicate-before-context lookup"),
        ("build_workspace_context_bundle", "server-owned context rebuild"),
        ("ContextSelectionSpec", "canonical 042 selection grammar"),
        ("bundle.context_digest", "server digest verification"),
        ("context_blocks=context_blocks", "validated context execution handoff"),
        ("existing_flow_id=flow_id", "090 pre-created-flow reuse"),
        ("request_digest", "idempotent semantic binding"),
    ):
        _require(service, needle, label)
    for forbidden in ("messages=", "thread_history", "conversation_history"):
        _forbid(service, forbidden, "raw thread-history egress")

    _require(api, "/ai/context/packs/preview", "existing 042 preview endpoint reuse")
    _require(api, "context_selection", "thread-submit context selection mapping")
    _require(api, "expected_context_digest", "thread-submit digest mapping")
    _forbid(api, "/ai/tasks/run", "parallel sidecar execution route")
    _forbid(api, 'fetch("https://', "direct external provider fetch")

    for needle, label in (
        ("useJarvisSidecar", "App-mounted sidecar controller"),
        ("...shellRegions", "stage region composition"),
        ("sidecar: jarvisSidecar", "single shell sidecar contribution"),
        ("AnalyticsDockContent", "analytics dock continuity"),
    ):
        _require(app, needle, label)
    for needle, label in (
        ("Use inspected project context", "explicit context on/off control"),
        ("previewThreadContext", "inspect-before-submit preview"),
        ("previewOwner", "stale preview ownership"),
        ("submitOwner", "stale submit ownership"),
        ("setSubmitting(false)", "obsolete busy-state release"),
        ("requestId", "stable retry request id"),
        ("Project context is off", "honest no-context state"),
        ("Current stage context", "secondary stage sidecar continuity"),
        ("Canonical state", "canonical execution projection"),
        ("Persistence", "persistence uncertainty projection"),
    ):
        _require(sidecar, needle, label)
    _forbid(sidecar, "dangerouslySetInnerHTML", "executable untrusted rendering")
    for forbidden in ("ReactMarkdown", "react-markdown", "marked("):
        _forbid(sidecar, forbidden, "Markdown execution")

    if "| 091 | in_review |" in status:
        _require(status, "pull/281", "091 implementation PR registry link")
    elif "| 091 | ready |" not in status and "| 091 | merged |" not in status:
        raise CheckFailure("091 registry lifecycle is not ready/in_review/merged")


def _self_test() -> None:
    base = {
        "backend/app/modules/ai/thread_models.py": "context_selection expected_context_digest model_validator\n",
        "backend/app/modules/ai/thread_service.py": (
            "_find_existing_interaction build_workspace_context_bundle ContextSelectionSpec "
            "bundle.context_digest context_blocks=context_blocks existing_flow_id=flow_id request_digest\n"
        ),
        "frontend/src/App.tsx": "useJarvisSidecar ...shellRegions sidecar: jarvisSidecar AnalyticsDockContent\n",
        "frontend/src/api/threads.ts": "/ai/context/packs/preview context_selection expected_context_digest\n",
        "frontend/src/components/ai/useJarvisSidecar.tsx": (
            "Use inspected project context previewThreadContext previewOwner submitOwner setSubmitting(false) "
            "requestId Project context is off Current stage context Canonical state Persistence\n"
        ),
        "docs/specs/STATUS.md": "| 091 | in_review | [#281](https://github.com/x/pull/281) |\n",
    }
    check_sources(lambda path: base[path])

    bad = dict(base)
    bad["frontend/src/api/threads.ts"] += "/ai/tasks/run\n"
    try:
        check_sources(lambda path: bad[path])
    except CheckFailure:
        pass
    else:
        raise AssertionError("self-test failed to reject parallel execution route")

    try:
        _check_scope({"frontend/src/components/Layout.tsx"})
    except CheckFailure:
        pass
    else:
        raise AssertionError("self-test failed to reject Layout mutation")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    try:
        if args.self_test:
            _self_test()
            print("check_jarvis_sidecar self-test: PASS")
        else:
            check_sources(changed_paths=_pull_request_changed_paths())
            print("check_jarvis_sidecar: PASS")
    except (CheckFailure, AssertionError, OSError) as exc:
        print(f"check_jarvis_sidecar: FAIL: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
