from __future__ import annotations

from pydantic import BaseModel, Field


class BenchmarkCheckEvidence(BaseModel):
    name: str
    passed: bool
    code: str
    actual: object | None = None


class BenchmarkGradeResult(BaseModel):
    case_id: str
    passed: bool
    passed_checks: int
    total_checks: int
    evaluator_snapshot_sha256: str
    checks: list[BenchmarkCheckEvidence] = Field(default_factory=list)
