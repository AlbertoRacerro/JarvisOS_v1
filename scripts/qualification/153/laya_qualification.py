#!/usr/bin/env python3
"""Measure the configured Laya backend against fixed advisory fixtures."""
from __future__ import annotations

import json
import statistics
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "backend"))

from app.modules.local_ai.decision_gateway import DecisionGateway

OUTPUT = Path(__file__).with_name("laya_qualification.json")

# These are contract-level examples. In particular, ambiguous/underspecified
# inputs are expected to abstain even if the currently configured rules disagree.
FIXTURES: dict[str, list[dict[str, Any]]] = {
    "route_class": [
        {"id": "direct-answer", "request": {"summary": "Answer a self-contained factual question.", "read_tool_ids": [], "required_capability_available": True}, "expected": "answer_directly"},
        {"id": "available-read-tool", "request": {"summary": "Look up an accepted project decision before answering.", "read_tool_ids": ["jarvis_retrieval_query"], "required_capability_available": True}, "expected": "use_read_tool"},
        {"id": "ungranted-capability", "request": {"summary": "The step requires an unavailable write capability.", "read_tool_ids": [], "required_capability_available": False}, "expected": "needs_ungranted_capability"},
        {"id": "ambiguous-low-confidence", "request": {"summary": "?", "read_tool_ids": [], "required_capability_available": True}, "expected": "abstained"},
        {"id": "malformed", "request": {"summary": "Answer directly.", "required_capability_available": "yes"}, "expected": "abstained"},
        {"id": "out-of-catalogue", "kind": "route_destination", "request": {"summary": "Answer directly.", "read_tool_ids": [], "required_capability_available": True}, "expected": "abstained"},
    ],
    "retry_or_stop": [
        {"id": "retry-first-retryable-failure", "request": {"previous_outcome": "failed", "attempt_count": 0, "retryable": True}, "expected": "retry"},
        {"id": "retry-empty-result", "request": {"previous_outcome": "empty", "attempt_count": 0, "retryable": True}, "expected": "retry"},
        {"id": "stop-nonretryable", "request": {"previous_outcome": "failed", "attempt_count": 0, "retryable": False}, "expected": "stop"},
        {"id": "stop-after-attempt", "request": {"previous_outcome": "failed", "attempt_count": 1, "retryable": True}, "expected": "stop"},
        {"id": "malformed", "request": {"previous_outcome": "failed", "attempt_count": "zero", "retryable": True}, "expected": "abstained"},
        {"id": "out-of-catalogue", "kind": "retry", "request": {"previous_outcome": "failed", "attempt_count": 0, "retryable": True}, "expected": "abstained"},
    ],
    "escalate": [
        {"id": "stay-local", "request": {"summary": "The local route is available and sufficient.", "stronger_route_ids": [], "local_route_available": True}, "expected": "stay_local"},
        {"id": "ask-human", "request": {"summary": "No local route can perform this task.", "stronger_route_ids": [], "local_route_available": False}, "expected": "ask_human"},
        {"id": "suggest-admitted-stronger-route", "request": {"summary": "A stronger admitted local route is available.", "stronger_route_ids": ["local:llamacpp"], "local_route_available": True}, "expected": "suggest_stronger_route"},
        {"id": "suggest-route-without-local-route", "request": {"summary": "Only the stronger admitted local route can help.", "stronger_route_ids": ["local:ollama"], "local_route_available": False}, "expected": "suggest_stronger_route"},
        {"id": "malformed", "request": {"summary": "No route available.", "stronger_route_ids": [], "local_route_available": 1}, "expected": "abstained"},
        {"id": "out-of-catalogue", "kind": "escalation_level", "request": {"summary": "No route available.", "stronger_route_ids": [], "local_route_available": False}, "expected": "abstained"},
    ],
    "model_select": [
        {"id": "select-among-admitted-local-candidates", "request": {"task_kind": "general", "candidate_ids": ["local:llamacpp", "local:ollama"], "context_tokens": 1024, "capability": ""}, "expected": "one_of_candidates"},
        {"id": "select-coding-candidate", "request": {"task_kind": "coding", "candidate_ids": ["local:llamacpp", "local:ollama"], "context_tokens": 2048, "capability": "coding"}, "expected": "one_of_candidates"},
        {"id": "abstain-no-currently-available-candidate", "request": {"task_kind": "general", "candidate_ids": ["local:not-configured"], "context_tokens": 1024, "capability": ""}, "expected": "abstained"},
        {"id": "abstain-candidates-do-not-fit-context", "request": {"task_kind": "general", "candidate_ids": ["local:llamacpp", "local:ollama"], "context_tokens": 1_000_000, "capability": ""}, "expected": "abstained"},
        {"id": "malformed", "request": {"task_kind": "general", "candidate_ids": [], "context_tokens": -1}, "expected": "abstained"},
        {"id": "out-of-catalogue", "kind": "model_rank", "request": {"task_kind": "general", "candidate_ids": ["local:llamacpp"], "context_tokens": 1024, "capability": ""}, "expected": "abstained"},
    ],
}


def _passed(expected: str, actual: dict[str, Any], request: dict[str, Any]) -> bool:
    if expected == "abstained":
        return actual.get("outcome") == "abstained"
    if actual.get("outcome") != "decided":
        return False
    recommendation = actual.get("recommendation")
    if expected == "one_of_candidates":
        return recommendation in request.get("candidate_ids", [])
    return recommendation == expected


def _revision(model_ref: object) -> str:
    value = str(model_ref)
    return value.rsplit("@", 1)[-1] if "@" in value else value.rsplit(".", 1)[-1]


def main() -> None:
    gateway = DecisionGateway.from_config()
    cases_by_kind: dict[str, dict[str, Any]] = {}
    backend_refs: set[str] = set()
    for kind, fixtures in FIXTURES.items():
        cases = []
        for fixture in fixtures:
            request = fixture["request"]
            actual = gateway.decide(fixture.get("kind", kind), request)
            expected = fixture["expected"]
            backend_refs.add(str(actual.get("model_ref", "unknown")))
            cases.append({
                "id": fixture["id"], "expected": expected,
                "actual": {key: actual.get(key) for key in (
                    "kind", "outcome", "recommendation", "confidence", "reason_code",
                    "model_ref", "latency_ms", "request_digest",
                )},
                "pass": _passed(expected, actual, request),
            })
        latencies = [case["actual"]["latency_ms"] for case in cases if isinstance(case["actual"]["latency_ms"], int)]
        abstentions = sum(case["actual"]["outcome"] == "abstained" for case in cases)
        cases_by_kind[kind] = {
            "status": "qualified" if all(case["pass"] for case in cases) else "unqualified",
            "pass_count": sum(case["pass"] for case in cases), "case_count": len(cases),
            "abstentions": abstentions,
            "latency_ms": {
                "p50": statistics.median(latencies) if latencies else None,
                "max": max(latencies) if latencies else None,
            },
            "backend_model_refs": sorted({case["actual"]["model_ref"] for case in cases}),
            "backend_revisions": sorted({
                _revision(case["actual"]["model_ref"])
                for case in cases if case["actual"]["model_ref"]
            }),
            "cases": cases,
        }
    result = {
        "schema": "jarvisos.153-laya-qualification.v1",
        "source_sha": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=Path(__file__).resolve().parents[3], text=True,
        ).strip(),
        "created_at": datetime.now(UTC).isoformat(),
        "configured_backend": type(gateway.backend).__name__,
        "backend_model_refs": sorted(backend_refs),
        "fixture_source": "fixed contract-level fixtures in laya_qualification.py; no outputs are adapted to observed backend behavior",
        "kinds": cases_by_kind,
    }
    OUTPUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({kind: {key: value for key, value in data.items() if key != "cases"}
                      for kind, data in cases_by_kind.items()}, indent=2))


if __name__ == "__main__":
    main()
