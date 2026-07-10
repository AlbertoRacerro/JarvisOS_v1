from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from app.modules.engineering_corpus.benchmark.evaluator import (
    BenchmarkConfigurationError,
    IsolatedBenchmarkEvaluator,
)
from app.modules.engineering_corpus.repository import CorpusSnapshotError


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.write_text(
        "".join(json.dumps(record, sort_keys=True) + "\n" for record in records),
        encoding="utf-8",
    )


def _build_evaluator(tmp_path: Path) -> IsolatedBenchmarkEvaluator:
    public_path = tmp_path / "public_cases.jsonl"
    gold_path = tmp_path / "private_gold.jsonl"
    _write_jsonl(
        public_path,
        [
            {
                "case_id": "SYN-001",
                "status": "promoted",
                "prompt": "Return a synthetic scalar and two labels.",
            }
        ],
    )
    _write_jsonl(
        gold_path,
        [
            {
                "case_id": "SYN-001",
                "checks": [
                    {
                        "name": "synthetic scalar",
                        "type": "numeric",
                        "answer_path": "value",
                        "expected": 123.456789,
                        "rtol": 1e-4,
                    },
                    {
                        "name": "required labels",
                        "type": "set_contains",
                        "answer_path": "labels",
                        "expected": ["alpha", "beta"],
                    },
                ],
            }
        ],
    )
    return IsolatedBenchmarkEvaluator(
        public_cases_path=public_path,
        public_cases_sha256=_sha256(public_path),
        private_gold_path=gold_path,
        private_gold_sha256=_sha256(gold_path),
        allowed_root=tmp_path,
    )


def test_evaluator_grades_good_answer_without_returning_gold(tmp_path: Path) -> None:
    evaluator = _build_evaluator(tmp_path)
    result = evaluator.grade(
        "SYN-001",
        {
            "value": 123.456789,
            "labels": ["alpha", "beta"],
        },
    )

    payload = result.model_dump_json()
    assert result.passed
    assert result.passed_checks == 2
    assert "expected" not in payload
    assert "private_gold" not in payload


def test_failed_grade_does_not_reveal_hidden_expected_values(tmp_path: Path) -> None:
    evaluator = _build_evaluator(tmp_path)
    result = evaluator.grade("SYN-001", {"value": -999.0, "labels": []})

    payload = result.model_dump_json()
    assert not result.passed
    assert "123.456789" not in payload
    assert "expected" not in payload
    assert {check.code for check in result.checks} == {"mismatch"}


def test_evaluator_rejects_unknown_case_and_unsupported_check_type(
    tmp_path: Path,
) -> None:
    evaluator = _build_evaluator(tmp_path)
    with pytest.raises(BenchmarkConfigurationError):
        evaluator.grade("UNKNOWN", {})

    public_path = tmp_path / "public2.jsonl"
    gold_path = tmp_path / "gold2.jsonl"
    _write_jsonl(public_path, [{"case_id": "X", "status": "promoted"}])
    _write_jsonl(
        gold_path,
        [
            {
                "case_id": "X",
                "checks": [{"name": "x", "type": "model_judge", "answer_path": "x"}],
            }
        ],
    )
    invalid = IsolatedBenchmarkEvaluator(
        public_cases_path=public_path,
        public_cases_sha256=_sha256(public_path),
        private_gold_path=gold_path,
        private_gold_sha256=_sha256(gold_path),
        allowed_root=tmp_path,
    )
    with pytest.raises(BenchmarkConfigurationError):
        invalid.grade("X", {"x": "anything"})


def test_evaluator_snapshot_binding_rejects_gold_outside_allowed_root(
    tmp_path: Path,
) -> None:
    root = tmp_path / "root"
    root.mkdir()
    public_path = root / "public.jsonl"
    gold_path = tmp_path / "gold.jsonl"
    _write_jsonl(public_path, [{"case_id": "X", "status": "promoted"}])
    _write_jsonl(gold_path, [{"case_id": "X", "checks": []}])

    with pytest.raises(CorpusSnapshotError):
        IsolatedBenchmarkEvaluator(
            public_cases_path=public_path,
            public_cases_sha256=_sha256(public_path),
            private_gold_path=gold_path,
            private_gold_sha256=_sha256(gold_path),
            allowed_root=root,
        )
