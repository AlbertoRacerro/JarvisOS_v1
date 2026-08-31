#!/usr/bin/env python3
"""Classify a pull-request diff into conservative CI execution domains."""

from __future__ import annotations

import argparse
import sys


def classify_scope(paths: list[str]) -> dict[str, bool]:
    # Paths are Git evidence, not user prose: preserve every character.
    # Lossy normalization could turn a non-doc path such as " docs/a.md"
    # into an apparent docs/ path and incorrectly grant a fast path.
    changed = [path for path in paths if path]

    # Empty/unknown input fails closed to the complete suite.
    if not changed:
        return {
            "docs_only": False,
            "run_backend": True,
            "run_frontend": True,
            "run_bluecad": True,
            "full_required": True,
        }

    if all(path.startswith("docs/") for path in changed):
        return {
            "docs_only": True,
            "run_backend": False,
            "run_frontend": False,
            "run_bluecad": False,
            "full_required": False,
        }

    # Only docs/backend/frontend are independently classifiable. Root files,
    # workflows, scripts, dependency/control files outside those trees, or any
    # unfamiliar path force the complete suite. Rename collapsing is disabled
    # by the workflow so moves across these boundaries are observed fail-closed.
    known = all(
        path.startswith(("docs/", "backend/", "frontend/")) for path in changed
    )
    if not known:
        return {
            "docs_only": False,
            "run_backend": True,
            "run_frontend": True,
            "run_bluecad": True,
            "full_required": True,
        }

    run_backend = any(path.startswith("backend/") for path in changed)
    frontend_changed = any(path.startswith("frontend/") for path in changed)

    return {
        "docs_only": False,
        "run_backend": run_backend,
        # Backend contracts are still mirrored manually in the frontend until
        # the accepted contract-codegen hardening lands. Preserve frontend build
        # as a cheap parallel regression gate for every backend change.
        "run_frontend": run_backend or frontend_changed,
        # Backend is treated conservatively as a possible BLUECAD dependency.
        # This avoids fragile source->test impact inference while still allowing
        # frontend-only work to skip the backend/CAD runtime lanes entirely.
        "run_bluecad": run_backend,
        "full_required": False,
    }


def self_test() -> None:
    assert classify_scope(["docs/specs/STATUS.md"]) == {
        "docs_only": True,
        "run_backend": False,
        "run_frontend": False,
        "run_bluecad": False,
        "full_required": False,
    }

    frontend = classify_scope(["frontend/src/App.tsx"])
    assert frontend["run_frontend"]
    assert not frontend["run_backend"]
    assert not frontend["run_bluecad"]

    backend = classify_scope(["backend/app/main.py"])
    assert backend["run_backend"]
    assert backend["run_frontend"]
    assert backend["run_bluecad"]

    mixed = classify_scope(["docs/a.md", "backend/app/main.py", "frontend/src/App.tsx"])
    assert mixed["run_backend"] and mixed["run_frontend"] and mixed["run_bluecad"]
    assert not mixed["full_required"]

    for paths in (
        [],
        ["README.md"],
        [".github/workflows/ci.yml"],
        ["scripts/check_spec_status.py"],
        [" docs/a.md"],
        ["\tdocs/a.md"],
        ["docs/a.md", "scripts/check_spec_status.py"],
    ):
        scope = classify_scope(paths)
        assert scope["full_required"]
        assert scope["run_backend"]
        assert scope["run_frontend"]
        assert scope["run_bluecad"]

    print("ci-scope: self-test OK")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0

    scope = classify_scope(sys.stdin.read().splitlines())
    for key in ("docs_only", "run_backend", "run_frontend", "run_bluecad", "full_required"):
        print(f"{key}={'true' if scope[key] else 'false'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
