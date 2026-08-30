from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "check_pr_attention_integration.py"
WORKFLOW = ROOT / ".github" / "workflows" / "pr-attention.yml"

spec = importlib.util.spec_from_file_location("check_pr_attention_integration", SCRIPT)
assert spec and spec.loader
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


def test_repository_workflow_contract_passes() -> None:
    assert checker.validate_text(WORKFLOW.read_text(encoding="utf-8")) == []


def test_negative_contract_fixtures_fail_closed() -> None:
    source = WORKFLOW.read_text(encoding="utf-8")
    cases = [
        source.replace(checker.PIN, "AlbertoRacerro/jarvis-pr-attention/cycle@main"),
        source.replace("contents: read", "contents: write"),
        source.replace("pull_request:", "pull_request_target:", 1),
        source.replace(checker.EXPECTED_HEAD, "expected-head: arbitrary"),
        source + "\n      - run: gh pr merge 999\n",
        source.replace("token: ${{ github.token }}", "accepted-head: deadbeef"),
    ]
    for candidate in cases:
        assert checker.validate_text(candidate)
