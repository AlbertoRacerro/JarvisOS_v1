from __future__ import annotations

import hashlib
import json
from math import isfinite
from pathlib import Path
from typing import Any

from app.modules.engineering_corpus.benchmark.models import (
    BenchmarkCheckEvidence,
    BenchmarkGradeResult,
)
from app.modules.engineering_corpus.repository import bind_read_only_file


class BenchmarkConfigurationError(RuntimeError):
    """Raised when evaluator-only benchmark fixtures are invalid or unsupported."""


def _load_jsonl(path: Path) -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    try:
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                value = json.loads(line)
                if not isinstance(value, dict) or not isinstance(
                    value.get("case_id"), str
                ):
                    raise BenchmarkConfigurationError(
                        "benchmark JSONL record is missing a valid case_id"
                    )
                case_id = value["case_id"]
                if case_id in records:
                    raise BenchmarkConfigurationError(
                        "benchmark JSONL contains duplicate case_id values"
                    )
                records[case_id] = value
    except (OSError, json.JSONDecodeError) as exc:
        raise BenchmarkConfigurationError(
            "benchmark JSONL could not be loaded"
        ) from exc
    return records


def _lookup_answer_path(answer: dict[str, Any], path: str) -> tuple[bool, Any]:
    current: Any = answer
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            return False, None
        current = current[part]
    return True, current


def _bounded_actual(value: Any) -> Any:
    if value is None or isinstance(value, bool | int | float):
        return value
    if isinstance(value, str):
        return value if len(value) <= 200 else f"{value[:199]}…"
    if isinstance(value, list):
        bounded = [_bounded_actual(item) for item in value[:20]]
        if len(value) > 20:
            bounded.append({"truncated_items": len(value) - 20})
        return bounded
    if isinstance(value, dict):
        return {"type": "dict", "keys": min(len(value), 1000)}
    return {"type": type(value).__name__}


def _numeric_check(
    name: str, actual: Any, specification: dict[str, Any]
) -> BenchmarkCheckEvidence:
    try:
        actual_value = float(actual)
        expected_value = float(specification["expected"])
        rtol = float(specification.get("rtol", 1e-6))
        atol = float(specification.get("atol", 0.0))
    except (KeyError, TypeError, ValueError) as exc:
        raise BenchmarkConfigurationError("numeric benchmark check is invalid") from exc
    if (
        not all(isfinite(value) for value in (expected_value, rtol, atol))
        or rtol < 0
        or atol < 0
    ):
        raise BenchmarkConfigurationError("numeric benchmark check is invalid")
    if not isfinite(actual_value):
        return BenchmarkCheckEvidence(
            name=name, passed=False, code="non_finite", actual=_bounded_actual(actual)
        )
    passed = abs(actual_value - expected_value) <= atol + rtol * abs(expected_value)
    return BenchmarkCheckEvidence(
        name=name,
        passed=passed,
        code="pass" if passed else "mismatch",
        actual=_bounded_actual(actual),
    )


def _exact_check(
    name: str, actual: Any, specification: dict[str, Any]
) -> BenchmarkCheckEvidence:
    if "expected" not in specification:
        raise BenchmarkConfigurationError("exact benchmark check is invalid")
    passed = actual == specification["expected"]
    return BenchmarkCheckEvidence(
        name=name,
        passed=passed,
        code="pass" if passed else "mismatch",
        actual=_bounded_actual(actual),
    )


def _set_contains_check(
    name: str, actual: Any, specification: dict[str, Any]
) -> BenchmarkCheckEvidence:
    expected = specification.get("expected")
    if not isinstance(expected, list):
        raise BenchmarkConfigurationError("set benchmark check is invalid")
    if not isinstance(actual, list):
        return BenchmarkCheckEvidence(
            name=name, passed=False, code="not_list", actual=_bounded_actual(actual)
        )
    try:
        required = set(expected)
    except TypeError as exc:
        raise BenchmarkConfigurationError("set benchmark check is invalid") from exc
    try:
        passed = required.issubset(set(actual))
    except TypeError:
        return BenchmarkCheckEvidence(
            name=name,
            passed=False,
            code="unhashable_values",
            actual=_bounded_actual(actual),
        )
    return BenchmarkCheckEvidence(
        name=name,
        passed=passed,
        code="pass" if passed else "mismatch",
        actual=_bounded_actual(actual),
    )


class IsolatedBenchmarkEvaluator:
    """Grades structured answers without returning evaluator-only expected values.

    Deployment must run this class in a process whose filesystem mount includes
    private gold while normal retrieval and model workspaces do not.
    """

    def __init__(
        self,
        *,
        public_cases_path: Path,
        public_cases_sha256: str,
        private_gold_path: Path,
        private_gold_sha256: str,
        allowed_root: Path,
    ) -> None:
        self._public_binding = bind_read_only_file(
            public_cases_path,
            allowed_root=allowed_root,
            expected_sha256=public_cases_sha256,
        )
        self._gold_binding = bind_read_only_file(
            private_gold_path,
            allowed_root=allowed_root,
            expected_sha256=private_gold_sha256,
        )
        if self._public_binding.path == self._gold_binding.path:
            raise BenchmarkConfigurationError(
                "public cases and private gold must be separate files"
            )
        self._public_cases = _load_jsonl(self._public_binding.path)
        self._snapshot_sha256 = hashlib.sha256(
            f"{self._public_binding.sha256}:{self._gold_binding.sha256}".encode()
        ).hexdigest()

    @property
    def evaluator_snapshot_sha256(self) -> str:
        return self._snapshot_sha256

    def grade(self, case_id: str, answer: dict[str, Any]) -> BenchmarkGradeResult:
        public_case = self._public_cases.get(case_id)
        if public_case is None or public_case.get("status") != "promoted":
            raise BenchmarkConfigurationError("case is not available for evaluation")

        gold_records = _load_jsonl(self._gold_binding.path)
        gold = gold_records.get(case_id)
        if gold is None:
            raise BenchmarkConfigurationError("case has no evaluator fixture")
        checks_spec = gold.get("checks")
        if not isinstance(checks_spec, list) or not checks_spec:
            raise BenchmarkConfigurationError("case evaluator fixture has no checks")

        checks: list[BenchmarkCheckEvidence] = []
        for specification in checks_spec:
            if not isinstance(specification, dict):
                raise BenchmarkConfigurationError("benchmark check is invalid")
            name = specification.get("name")
            answer_path = specification.get("answer_path")
            kind = specification.get("type")
            if (
                not isinstance(name, str)
                or not isinstance(answer_path, str)
                or not isinstance(kind, str)
            ):
                raise BenchmarkConfigurationError("benchmark check is invalid")
            found, actual = _lookup_answer_path(answer, answer_path)
            if not found:
                checks.append(
                    BenchmarkCheckEvidence(
                        name=name, passed=False, code="missing_answer"
                    )
                )
                continue
            if kind == "numeric":
                check = _numeric_check(name, actual, specification)
            elif kind in {"boolean", "exact"}:
                check = _exact_check(name, actual, specification)
            elif kind == "set_contains":
                check = _set_contains_check(name, actual, specification)
            else:
                raise BenchmarkConfigurationError("benchmark check type is unsupported")
            checks.append(check)

        passed_checks = sum(check.passed for check in checks)
        return BenchmarkGradeResult(
            case_id=case_id,
            passed=passed_checks == len(checks),
            passed_checks=passed_checks,
            total_checks=len(checks),
            evaluator_snapshot_sha256=self._snapshot_sha256,
            checks=checks,
        )
