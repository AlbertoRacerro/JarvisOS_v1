#!/usr/bin/env python3
"""Deterministic guard for provider-secret manual review workflows.

The reviewed pull request is data only. Any workflow that exposes a review-provider
secret must execute repository code from trusted master and must not reconstruct a
PR-controlled worktree before running scripts/manual_review.py.
"""

from __future__ import annotations

import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = (
    ROOT / ".github/workflows/cheap-review.yml",
    ROOT / ".github/workflows/senior-review.yml",
)

FORBIDDEN_RUN_PATTERNS = (
    re.compile(r"\bgit\s+checkout\b", re.IGNORECASE),
    re.compile(r"\bgit\s+switch\b", re.IGNORECASE),
    re.compile(r"\bgh\s+pr\s+checkout\b", re.IGNORECASE),
    re.compile(r"refs/pull/", re.IGNORECASE),
)


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _section(lines: list[str], heading: str, indent: int) -> list[str]:
    marker = " " * indent + heading + ":"
    for index, line in enumerate(lines):
        if line.rstrip() != marker:
            continue
        end = len(lines)
        for cursor in range(index + 1, len(lines)):
            candidate = lines[cursor]
            if candidate.strip() and _indent(candidate) <= indent:
                end = cursor
                break
        return lines[index + 1 : end]
    raise AssertionError(f"missing {heading!r} section")


def _steps(review_job: list[str]) -> list[list[str]]:
    steps_section = _section(review_job, "steps", 4)
    starts = [
        index
        for index, line in enumerate(steps_section)
        if _indent(line) == 6 and line.lstrip().startswith("-")
    ]
    result: list[list[str]] = []
    for offset, start in enumerate(starts):
        end = starts[offset + 1] if offset + 1 < len(starts) else len(steps_section)
        result.append(steps_section[start:end])
    if not result:
        raise AssertionError("review job has no steps")
    return result


def _step_text(step: list[str]) -> str:
    return "\n".join(line.strip() for line in step)


def check_workflow_text(text: str, *, label: str = "workflow") -> None:
    lines = text.splitlines()
    on_section = _section(lines, "on", 0)
    trigger_keys = [
        line.strip()[:-1]
        for line in on_section
        if _indent(line) == 2 and line.strip().endswith(":")
    ]
    if trigger_keys != ["workflow_dispatch"]:
        raise AssertionError(f"{label}: manual review must be workflow_dispatch-only, found {trigger_keys}")

    jobs = _section(lines, "jobs", 0)
    review_job = _section(jobs, "review", 2)
    review_text = "\n".join(review_job)
    if "github.ref == 'refs/heads/master'" not in review_text:
        raise AssertionError(f"{label}: review job is not master-gated")

    steps = _steps(review_job)
    checkout_steps = [step for step in steps if "uses: actions/checkout@" in _step_text(step)]
    if len(checkout_steps) != 1:
        raise AssertionError(f"{label}: expected exactly one checkout step, found {len(checkout_steps)}")
    checkout = _step_text(checkout_steps[0])
    if "ref: refs/heads/master" not in checkout:
        raise AssertionError(f"{label}: checkout is not pinned to trusted master")
    if "persist-credentials: false" not in checkout:
        raise AssertionError(f"{label}: checkout must set persist-credentials: false")
    if "refs/pull/" in checkout or "inputs.pr_number" in checkout.split("ref:", 1)[-1].splitlines()[0]:
        raise AssertionError(f"{label}: checkout ref depends on reviewed PR")

    provider_steps: list[list[str]] = []
    for step in steps:
        text_block = _step_text(step)
        if "CHEAP_REVIEW_API_KEY:" in text_block:
            provider_steps.append(step)
        for pattern in FORBIDDEN_RUN_PATTERNS:
            if pattern.search(text_block) and "uses: actions/checkout@" not in text_block:
                raise AssertionError(f"{label}: step can reconstruct/check out PR-controlled code: {pattern.pattern}")

    if len(provider_steps) != 1:
        raise AssertionError(f"{label}: expected one provider-secret step, found {len(provider_steps)}")
    provider = _step_text(provider_steps[0])
    if "run: python scripts/manual_review.py" not in provider:
        raise AssertionError(f"{label}: provider secret is not confined to trusted manual_review.py execution")
    if "REVIEW_PR_NUMBER:" not in provider:
        raise AssertionError(f"{label}: reviewed PR number is not passed as data")

    for step in steps:
        text_block = _step_text(step)
        if step is provider_steps[0]:
            continue
        if re.search(r"secrets\.(?:DEEPSEEK_API_KEY|GLM_API_KEY)", text_block):
            raise AssertionError(f"{label}: provider secret exposed outside trusted review step")


def check_workflow(path: Path) -> None:
    check_workflow_text(path.read_text(encoding="utf-8"), label=str(path.relative_to(ROOT)))


def _safe_fixture() -> str:
    return """name: fixture\non:\n  workflow_dispatch:\n    inputs:\n      pr_number:\n        required: true\njobs:\n  review:\n    if: ${{ github.ref == 'refs/heads/master' }}\n    steps:\n      - uses: actions/checkout@v4\n        with:\n          ref: refs/heads/master\n          persist-credentials: false\n      - name: Review\n        env:\n          REVIEW_PR_NUMBER: ${{ inputs.pr_number }}\n          CHEAP_REVIEW_API_KEY: ${{ secrets.DEEPSEEK_API_KEY }}\n        run: python scripts/manual_review.py\n"""


def _vulnerable_fixture() -> str:
    return """name: fixture\non:\n  workflow_dispatch:\n    inputs:\n      pr_number:\n        required: true\njobs:\n  review:\n    if: ${{ github.ref == 'refs/heads/master' }}\n    steps:\n      - uses: actions/checkout@v4\n        with:\n          ref: refs/pull/${{ inputs.pr_number }}/head\n      - name: Partial repair\n        run: git checkout FETCH_HEAD -- scripts/manual_review.py\n      - name: Review\n        env:\n          REVIEW_PR_NUMBER: ${{ inputs.pr_number }}\n          CHEAP_REVIEW_API_KEY: ${{ secrets.DEEPSEEK_API_KEY }}\n        run: python scripts/manual_review.py\n"""


def _prove_untrusted_shadow_is_not_on_execution_path() -> None:
    """Model the corrected worktree boundary with an adversarial sibling module.

    The provider-bearing command executes a trusted script from the trusted tree.
    A separate synthetic PR tree contains a hostile json.py, but it is never used
    as cwd, PYTHONPATH, script path, or import root. The sentinel must stay absent.
    """
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        trusted = root / "trusted"
        untrusted = root / "untrusted"
        (trusted / "scripts").mkdir(parents=True)
        (untrusted / "scripts").mkdir(parents=True)
        sentinel = root / "PWNED"
        (untrusted / "scripts/json.py").write_text(
            f"from pathlib import Path\nPath({str(sentinel)!r}).write_text('pwned')\n",
            encoding="utf-8",
        )
        (trusted / "scripts/manual_review.py").write_text(
            "import json\nassert json.loads('{\\\"ok\\\": true}')['ok'] is True\n",
            encoding="utf-8",
        )
        completed = subprocess.run(
            [sys.executable, "scripts/manual_review.py"],
            cwd=trusted,
            env={"PATH": str(Path(sys.executable).parent)},
            capture_output=True,
            text=True,
            check=False,
        )
        if completed.returncode != 0:
            raise AssertionError(f"trusted fixture failed: {completed.stderr}")
        if sentinel.exists():
            raise AssertionError("untrusted sibling module gained import execution authority")


def self_test() -> None:
    check_workflow_text(_safe_fixture(), label="safe fixture")
    try:
        check_workflow_text(_vulnerable_fixture(), label="vulnerable fixture")
    except AssertionError:
        pass
    else:
        raise AssertionError("checker accepted the pre-099 vulnerable workflow shape")
    _prove_untrusted_shadow_is_not_on_execution_path()


def main() -> int:
    if "--self-test" in sys.argv:
        self_test()
    for workflow in WORKFLOWS:
        check_workflow(workflow)
    print("manual review secret boundary: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
