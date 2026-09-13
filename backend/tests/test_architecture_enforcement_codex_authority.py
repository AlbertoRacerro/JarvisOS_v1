from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "check_architecture_enforcement.py"
SPEC = importlib.util.spec_from_file_location("check_architecture_enforcement_codex_test", SCRIPT)
assert SPEC and SPEC.loader
scanner = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = scanner
SPEC.loader.exec_module(scanner)

EXCEPTION = {
    "rule_id": "AE004",
    "exact_match": ".github/workflows/codex-result-delivery.yml::on.issue_comment",
    "classification": "accepted_owner",
    "owner_or_removal_spec": "022/128 codex-result authority 2026-09-13",
    "rationale": "single exact Codex-result dispatcher into the existing trusted delivery bridge",
}


def _root(tmp_path: Path) -> tuple[Path, Path]:
    root = tmp_path
    (root / "backend/app").mkdir(parents=True)
    (root / "scripts").mkdir()
    workflows = root / ".github/workflows"
    workflows.mkdir(parents=True)
    configs = root / "configs"
    configs.mkdir()
    config = configs / "architecture_enforcement.json"
    config.write_text(json.dumps({"exceptions": [EXCEPTION]}), encoding="utf-8")
    (workflows / "codex-result-delivery.yml").write_bytes(
        (ROOT / ".github/workflows/codex-result-delivery.yml").read_bytes()
    )
    (root / "scripts/codex_result_delivery_dispatch.py").write_bytes(
        (ROOT / "scripts/codex_result_delivery_dispatch.py").read_bytes()
    )
    return root, config


def test_exact_codex_issue_comment_workflow_is_the_only_admitted_exception(tmp_path: Path) -> None:
    root, config = _root(tmp_path)
    assert not [f for f in scanner.scan(root, config) if f.rule_id == "AE004"]

    (root / ".github/workflows/other.yml").write_text(
        "name: forbidden\non:\n  issue_comment:\n    types: [created]\njobs: {}\n",
        encoding="utf-8",
    )
    findings = [f for f in scanner.scan(root, config) if f.rule_id == "AE004"]
    assert len(findings) == 1
    assert findings[0].path == ".github/workflows/other.yml"
    assert findings[0].symbol == "on.issue_comment"


def test_exact_exception_does_not_admit_coordination_bus_mutation(tmp_path: Path) -> None:
    root, config = _root(tmp_path)
    allowed = root / ".github/workflows/codex-result-delivery.yml"
    allowed.write_text(
        allowed.read_text(encoding="utf-8")
        + "\n# WORKPACK\n# git push origin HEAD:feature\n",
        encoding="utf-8",
    )
    findings = [f for f in scanner.scan(root, config) if f.rule_id == "AE004"]
    assert len(findings) == 1
    assert findings[0].path == ".github/workflows/codex-result-delivery.yml"
    assert findings[0].symbol == "<yaml>"


def test_exact_exception_fails_closed_on_non_v2_behavior_drift(tmp_path: Path) -> None:
    root, config = _root(tmp_path)
    allowed = root / ".github/workflows/codex-result-delivery.yml"
    allowed.write_text(
        allowed.read_text(encoding="utf-8").replace("contents: read", "contents: write"),
        encoding="utf-8",
    )
    findings = [f for f in scanner.scan(root, config) if f.rule_id == "AE004"]
    assert len(findings) == 1
    assert findings[0].symbol == "on.issue_comment"
    assert "behavior drifted" in findings[0].detail


def test_exact_exception_fails_closed_on_dispatcher_behavior_drift(tmp_path: Path) -> None:
    root, config = _root(tmp_path)
    dispatcher = root / "scripts/codex_result_delivery_dispatch.py"
    dispatcher.write_text(
        dispatcher.read_text(encoding="utf-8") + "\n# unauthorized behavior drift\n",
        encoding="utf-8",
    )
    findings = [f for f in scanner.scan(root, config) if f.rule_id == "AE004"]
    assert len(findings) == 1
    assert findings[0].symbol == "on.issue_comment"
    assert "dispatcher behavior drifted" in findings[0].detail
