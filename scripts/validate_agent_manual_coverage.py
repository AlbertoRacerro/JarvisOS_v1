#!/usr/bin/env python3
"""Fail-closed validation for the issue #656 master-file coverage manifest."""

from __future__ import annotations

import argparse
import csv
import subprocess
import sys
from pathlib import Path

ALLOWED_OWNERS = {"A", "B", "C", "D"}
ALLOWED_STATUSES = {"READ", "GENERATED/ASSET"}


def tracked_paths(base_ref: str) -> set[str]:
    raw = subprocess.check_output(
        ["git", "ls-tree", "-r", "--name-only", base_ref],
        text=True,
    )
    return {line.strip() for line in raw.splitlines() if line.strip()}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-ref", default="master")
    parser.add_argument(
        "--manifest",
        default="docs/agent-manual/FILE_COVERAGE_MANIFEST.tsv",
    )
    args = parser.parse_args()

    base = tracked_paths(args.base_ref)
    rows = []
    with Path(args.manifest).open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        expected = {"path", "owner", "status", "evidence"}
        if reader.fieldnames != ["path", "owner", "status", "evidence"]:
            print("FAIL: invalid header", file=sys.stderr)
            return 1
        for row in reader:
            if set(row) != expected:
                print("FAIL: invalid columns", file=sys.stderr)
                return 1
            rows.append(row)

    paths = [row["path"] for row in rows]
    duplicates = sorted({path for path in paths if paths.count(path) > 1})
    invalid = [
        row for row in rows
        if row["owner"] not in ALLOWED_OWNERS
        or row["status"] not in ALLOWED_STATUSES
        or not row["path"]
        or row["path"].startswith("/")
        or ".." in Path(row["path"]).parts
    ]
    manifest_set = set(paths)
    missing = sorted(base - manifest_set)
    extra = sorted(manifest_set - base)
    ambiguous = sorted(path for path in manifest_set if sum(1 for row in rows if row["path"] == path) != 1)

    print(f"BASE_TRACKED_FILES={len(base)}")
    print(f"MANIFEST_ROWS={len(rows)}")
    print(f"READ={sum(row['status'] == 'READ' for row in rows)}")
    print(f"GENERATED/ASSET={sum(row['status'] == 'GENERATED/ASSET' for row in rows)}")
    print(f"UNACCOUNTED_FILES_COUNT={len(missing)}")
    print(f"DUPLICATE_PATH_COUNT={len(duplicates)}")
    print(f"AMBIGUOUS_OWNERSHIP_COUNT={len(ambiguous)}")
    print(f"EXTRA_MANIFEST_PATH_COUNT={len(extra)}")
    if invalid or missing or extra or duplicates or ambiguous:
        if invalid:
            print("INVALID_ROWS:", file=sys.stderr)
        if missing:
            print("MISSING:", ", ".join(missing[:20]), file=sys.stderr)
        if extra:
            print("EXTRA:", ", ".join(extra[:20]), file=sys.stderr)
        if duplicates:
            print("DUPLICATES:", ", ".join(duplicates[:20]), file=sys.stderr)
        if ambiguous:
            print("AMBIGUOUS:", ", ".join(ambiguous[:20]), file=sys.stderr)
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
