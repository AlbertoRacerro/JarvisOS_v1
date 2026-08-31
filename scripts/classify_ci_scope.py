#!/usr/bin/env python3
"""Classify whether a pull-request diff is safe for the docs-only CI fast path."""

from __future__ import annotations

import argparse
import sys


def is_docs_only(paths: list[str]) -> bool:
    normalized = [path.strip() for path in paths if path.strip()]
    return bool(normalized) and all(path.startswith("docs/") for path in normalized)


def self_test() -> None:
    assert is_docs_only(["docs/specs/STATUS.md"])
    assert is_docs_only(["docs/a.md", "docs/specs/b.md"])
    assert not is_docs_only([])
    assert not is_docs_only(["README.md"])
    assert not is_docs_only(["docs/a.md", "scripts/check_spec_status.py"])
    assert not is_docs_only([".github/workflows/ci.yml"])
    print("ci-scope: self-test OK")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0

    paths = sys.stdin.read().splitlines()
    print(f"docs_only={'true' if is_docs_only(paths) else 'false'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
