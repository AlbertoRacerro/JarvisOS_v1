#!/usr/bin/env python3
"""Conformance checks for spec 029 SETTINGS-1.

This checker freezes the frontend-only authority and non-disclosure boundary.
Browser race, focus, uncertainty, and effective-200%-width evidence remains
mandatory in addition to these source/scope assertions.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]

ALLOWED_IMPLEMENTATION_PATHS = {
    "docs/specs/STATUS.md",
    "frontend/src/App.tsx",
    "frontend/src/main.tsx",
    "frontend/src/pages/Settings.tsx",
    "frontend/src/api/settings.ts",
    "frontend/src/styles/settings.css",
    "scripts/check_settings_surface.py",
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
        raise CheckFailure(f"029 implementation changed paths outside frozen allow-list: {unexpected}")
    forbidden_prefixes = ("backend/", ".github/", "frontend/package")
    forbidden = sorted(path for path in paths if path.startswith(forbidden_prefixes))
    if forbidden:
        raise CheckFailure(f"029 implementation changed forbidden backend/workflow/package paths: {forbidden}")


def check_sources(reader=_read, *, changed_paths: set[str] | None = None) -> None:
    page = reader("frontend/src/pages/Settings.tsx")
    api = reader("frontend/src/api/settings.ts")
    app = reader("frontend/src/App.tsx")
    status = reader("docs/specs/STATUS.md")

    _check_scope(changed_paths)

    for field in (
        "monthly_api_budget_usd",
        "paid_ai_enabled",
        "scaleway_enabled",
        "scaleway_monthly_token_cap",
        "scaleway_hard_stop_token_cap",
        "max_direct_continuations",
    ):
        _require(page, field, f"allow-listed setting {field}")

    for forbidden in (
        "policy_mode\")}>Save",
        "default_ai_provider\")}>Save",
        "default_ai_model\")}>Save",
        "provider_mode\")}>Save",
        "smoke_test_mode_enabled\")}>Save",
        "scaleway_input_tokens_month_to_date\")}>Save",
        "scaleway_output_tokens_month_to_date\")}>Save",
    ):
        _forbid(page, forbidden, "unauthorized mutable setting control")

    for needle, label in (
        ("type=\"password\"", "non-revealing credential input"),
        ("State uncertain", "uncertain-reread fail-closed state"),
        ("no retry was attempted", "no automatic mutation retry wording"),
        ("confirmDelete", "explicit credential-delete confirmation"),
        ("event.key === \"Escape\"", "keyboard delete-cancel path"),
        ("loadCanonical", "canonical reread ownership"),
        ("generation.current", "stale load generation ownership"),
        ("settingsBusy", "settings mutation busy lock"),
        ("credentialBusy", "credential mutation busy lock"),
    ):
        _require(page, needle, label)

    _forbid(page, "masked_preview", "secret preview projection")
    _forbid(page, "localStorage", "credential browser persistence")
    _forbid(page, "sessionStorage", "credential browser persistence")
    _forbid(page, "dangerouslySetInnerHTML", "executable hostile status rendering")

    for needle, label in (
        ('"/ai/settings"', "canonical AI settings endpoint"),
        ('"/ai/status"', "canonical AI status endpoint"),
        ('"/secrets/scaleway/status"', "canonical secret status endpoint"),
        ('"/secrets/scaleway/api-key"', "canonical secret mutation endpoint"),
        ('"/system/info"', "canonical system info endpoint"),
        ("boundedText", "bounded public error projection"),
        ("detail.code", "typed public error code projection"),
        ("detail.message", "typed public error message projection"),
    ):
        _require(api, needle, label)

    for forbidden in (
        "/ai/tasks/run",
        "/ai/modeling/draft",
        "masked_preview",
        "response.text()",
        'fetch("https://',
    ):
        _forbid(api, forbidden, "provider/secret/arbitrary-body path")

    _require(app, 'case "settings":', "Settings route")
    _require(app, "<Settings />", "Settings product surface")
    _require(app, "useJarvisSidecar", "091 sidecar composition preservation")

    _require(status, "| 029 | in_review |", "029 in-review registry lifecycle")
    _require(status, "pull/286", "029 implementation PR registry link")


def _self_test() -> None:
    base = {
        "frontend/src/pages/Settings.tsx": (
            "monthly_api_budget_usd paid_ai_enabled scaleway_enabled scaleway_monthly_token_cap "
            "scaleway_hard_stop_token_cap max_direct_continuations type=\"password\" State uncertain "
            "no retry was attempted confirmDelete event.key === \"Escape\" loadCanonical generation.current "
            "settingsBusy credentialBusy\n"
        ),
        "frontend/src/api/settings.ts": (
            '"/ai/settings" "/ai/status" "/secrets/scaleway/status" '
            '"/secrets/scaleway/api-key" "/system/info" boundedText detail.code detail.message\n'
        ),
        "frontend/src/App.tsx": 'case "settings": <Settings /> useJarvisSidecar\n',
        "docs/specs/STATUS.md": "| 029 | in_review | [#286](https://github.com/x/pull/286) |\n",
    }
    check_sources(lambda path: base[path])

    bad = dict(base)
    bad["frontend/src/api/settings.ts"] += "response.text()\n"
    try:
        check_sources(lambda path: bad[path])
    except CheckFailure:
        pass
    else:
        raise AssertionError("self-test failed to reject arbitrary response-body projection")

    try:
        _check_scope({"backend/app/modules/ai/settings.py"})
    except CheckFailure:
        pass
    else:
        raise AssertionError("self-test failed to reject backend mutation")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    try:
        if args.self_test:
            _self_test()
            print("check_settings_surface self-test: PASS")
        else:
            check_sources(changed_paths=_pull_request_changed_paths())
            print("check_settings_surface: PASS")
    except (CheckFailure, AssertionError, OSError) as exc:
        print(f"check_settings_surface: FAIL: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
