from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "event_bound_continuation_plan.py"
SPEC = importlib.util.spec_from_file_location("event_bound_continuation_plan", SCRIPT)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = mod
SPEC.loader.exec_module(mod)

HEAD = "a" * 40
OTHER = "b" * 40


class Delegate:
    def __init__(self, pulls: list[dict]) -> None:
        self.pulls = pulls

    def open_pulls(self) -> list[dict]:
        return self.pulls


def pull(number: int, head: str) -> dict:
    return {"number": number, "head": {"sha": head}}


def test_binding_requires_pr_and_head_together() -> None:
    with pytest.raises(mod.daily.ContinuationError, match="supplied together"):
        mod.parse_binding("77", "")
    with pytest.raises(mod.daily.ContinuationError, match="supplied together"):
        mod.parse_binding("", HEAD)


def test_binding_rejects_invalid_values() -> None:
    with pytest.raises(mod.daily.ContinuationError, match="invalid"):
        mod.parse_binding("not-a-pr", HEAD)
    with pytest.raises(mod.daily.ContinuationError, match="invalid"):
        mod.parse_binding("77", "not-a-sha")


def test_bound_reader_selects_only_exact_event_front() -> None:
    reader = mod.BoundReader(Delegate([pull(77, HEAD), pull(88, OTHER)]), 77, HEAD)
    assert reader.open_pulls() == [pull(77, HEAD)]


def test_bound_reader_stale_head_becomes_no_candidate() -> None:
    reader = mod.BoundReader(Delegate([pull(77, OTHER)]), 77, HEAD)
    assert reader.open_pulls() == []


def test_bound_reader_missing_pr_becomes_no_candidate() -> None:
    reader = mod.BoundReader(Delegate([pull(88, OTHER)]), 77, HEAD)
    assert reader.open_pulls() == []
