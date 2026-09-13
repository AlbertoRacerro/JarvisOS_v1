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
    return root, config


def test_exact_codex_issue_comment_workflow_is_the_only_admitted_exception(tmp_path: Path) -> None:
    root, config = _root(tmp_path)
    allowed = root / ".github/workflows/codex-result-delivery.yml"
    allowed.write_text("name: allowed\non:\n  issue_comment:\n    types: [created]\njobs: {}\n", encoding="utf-8")
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
        "name: forbidden-v2\n"
        "on:\n  issue_comment:\n    types: [created]\n"
        "env:\n  MARKER: JARVIS_COORD_V2\n  OP: apply_patch\n"
        "jobs: {}\n",
        encoding="utf-8",
    )
    findings = [f for f in scanner.scan(root, config) if f.rule_id == "AE004"]
    assert len(findings) == 1
    assert findings[0].path == ".github/workflows/codex-result-delivery.yml"
    assert findings[0].symbol == "<yaml>"
