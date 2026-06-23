"""Deterministic Phase B soft-review fixture probe.

This script is evaluation-only. It does not write memory, retrieve runtime
project data, call models, call providers, execute tools, or approve behavior.
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import local_model_structured_output_probe as structured_probe


DEFAULT_PHASE_A_REPORT_DIR = Path("reports/local_model_smoke/1G-B2-F2-C")
DEFAULT_HOLDOUT = Path("docs/holdout/intake_generalization_v0.jsonl")
DEFAULT_SCHEMA = Path("schemas/fast_secretary_soft_review_v0_1.schema.json")
DEFAULT_OUT_DIR = Path("reports/local_model_smoke/1G-B2-F2-B1")
SUMMARY_JSON = "phase_b_soft_review_fixture_summary.json"
SUMMARY_MD = "phase_b_soft_review_fixture_summary.md"


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_phase_a_results(report_dir: Path) -> list[dict[str, Any]]:
    paths = sorted(report_dir.glob("*__result.json"))
    if not paths:
        raise ValueError(f"no Phase A result files found in {report_dir}")
    return [structured_probe.load_json(path) | {"_source_result_path": str(path)} for path in paths]


def load_holdout_cases(path: Path) -> dict[str, dict[str, Any]]:
    return {case["case_id"]: case for case in structured_probe.load_holdout(path)}


def corrected_phase_a_output(result: dict[str, Any]) -> dict[str, Any]:
    corrected = result.get("policy_overlay_corrected_output")
    if isinstance(corrected, dict):
        return corrected
    parsed = result.get("parsed_output")
    if isinstance(parsed, dict):
        return parsed
    raise ValueError(f"{result.get('case_id')} does not include a Phase A object")


def classify_text_project(text: str) -> str:
    lower = text.lower()
    if "bluerev" in lower or "microalgae" in lower or "algae" in lower:
        return "bluerev"
    if "jarvisos" in lower or "memorystore" in lower or "memory" in lower:
        return "jarvisos"
    if "cppom" in lower or "handout" in lower or "course" in lower:
        return "coursework"
    return "unknown"


def classify_text_domain(text: str, phase_a: dict[str, Any]) -> str:
    lower = text.lower()
    if phase_a.get("contains_secret_or_credential"):
        return "security"
    if "memory" in lower or "memorystore" in lower:
        return "memory"
    if "literature" in lower or "doi" in lower or "source" in lower:
        return "retrieval"
    if "microalgae" in lower or "bioprocess" in lower:
        return "bioprocess"
    if "model" in lower:
        return "modeling"
    return "general"


def domain_tags(text: str, phase_a: dict[str, Any]) -> list[str]:
    lower = text.lower()
    tags: list[str] = []
    candidates = [
        ("memory", "memory"),
        ("provider", "provider"),
        ("gpt", "provider"),
        ("claude", "provider"),
        ("literature", "literature"),
        ("doi", "source"),
        ("source", "source"),
        ("microalgae", "microalgae"),
        ("bluerev", "bluerev"),
        ("secret", "secret"),
        ("private key", "secret"),
        (".ssh", "secret"),
        ("stale", "superseded"),
        ("superseded", "superseded"),
        ("latest", "ambiguous-source"),
    ]
    for needle, tag in candidates:
        if needle in lower and tag not in tags:
            tags.append(tag)
    if phase_a.get("clarification_required") and "clarification" not in tags:
        tags.append("clarification")
    if phase_a.get("source_policy_for_future_retrieval") == "blocked" and "blocked" not in tags:
        tags.append("blocked")
    return tags[:6]


def phase_a_blocked(phase_a: dict[str, Any]) -> bool:
    return (
        phase_a.get("source_policy_for_future_retrieval") == "blocked"
        or phase_a.get("allowed_future_retrieval_behavior") == "blocked"
    )


def phase_a_clarification_required(phase_a: dict[str, Any]) -> bool:
    return (
        phase_a.get("clarification_required") is True
        or phase_a.get("allowed_future_retrieval_behavior") == "clarification_required"
    )


def storage_relevance(phase_a: dict[str, Any]) -> str:
    if phase_a_blocked(phase_a) and phase_a.get("contains_secret_or_credential"):
        return "none"
    if phase_a.get("source_policy_for_future_retrieval") == "review_only":
        return "medium"
    if phase_a_clarification_required(phase_a):
        return "low"
    return "low"


def possible_card_type(phase_a: dict[str, Any]) -> str:
    if phase_a.get("contains_secret_or_credential") or phase_a_blocked(phase_a):
        return "none"
    behavior = phase_a.get("allowed_future_retrieval_behavior")
    if behavior == "candidate_discovery_only":
        return "source_card"
    if phase_a.get("unresolved_assumption_or_open_decision"):
        return "assumption_card"
    if phase_a.get("memory_boundary_or_write_authority_claim"):
        return "decision_card"
    return "memory_card"


def soft_reason_code(phase_a: dict[str, Any]) -> str:
    if phase_a_blocked(phase_a):
        return "blocked_by_phase_a"
    if phase_a_clarification_required(phase_a):
        return "clarification_context"
    if phase_a.get("allowed_future_retrieval_behavior") == "candidate_discovery_only":
        return "source_candidate"
    if phase_a.get("unresolved_assumption_or_open_decision"):
        return "assumption_candidate"
    if phase_a.get("memory_boundary_or_write_authority_claim"):
        return "decision_candidate"
    return "contextual_summary"


def make_summary(input_text: str, phase_a: dict[str, Any]) -> str:
    if phase_a.get("contains_secret_or_credential"):
        return "Sensitive or secret-bearing input requires review without exposing raw content."
    if phase_a_blocked(phase_a):
        return "Phase A blocked this input for authority-sensitive review."
    if phase_a_clarification_required(phase_a):
        return "Input needs clarification before reliable source or memory use."
    if phase_a.get("allowed_future_retrieval_behavior") == "candidate_discovery_only":
        return "Input may support candidate source discovery under review."
    cleaned = re.sub(r"\s+", " ", input_text.strip())
    return cleaned[:220] if cleaned else "Soft review candidate for manual inspection."


def suggested_followup(phase_a: dict[str, Any]) -> str:
    if phase_a_clarification_required(phase_a):
        return "Which exact source, project, or prior decision should be used?"
    return ""


def build_soft_review(
    *,
    case_id: str,
    input_text: str,
    phase_a: dict[str, Any],
) -> dict[str, Any]:
    blocked = phase_a_blocked(phase_a)
    clarification = phase_a_clarification_required(phase_a)
    provider_allowed = bool(phase_a.get("external_provider_allowed"))
    manual_review = True

    recommends_retrieval = (
        False
        if blocked or clarification
        else phase_a.get("allowed_future_retrieval_behavior") == "candidate_discovery_only"
    )

    return {
        "phase_a_case_id": case_id,
        "summary_short": make_summary(input_text, phase_a),
        "project_bucket": classify_text_project(input_text),
        "primary_domain": classify_text_domain(input_text, phase_a),
        "domain_tags": domain_tags(input_text, phase_a),
        "storage_relevance": storage_relevance(phase_a),
        "usefulness_for_future_review": storage_relevance(phase_a),
        "possible_memory_card_type": possible_card_type(phase_a),
        "soft_reason_code": soft_reason_code(phase_a),
        "brief_rationale": (
            "Advisory review context only. Phase A corrected hard-gate fields remain authoritative."
        ),
        "suggested_followup_question": suggested_followup(phase_a),
        "soft_uncertain_fields": ["phase_b_labels"] if clarification else [],
        "phase_a_blocked": blocked,
        "phase_a_clarification_required": clarification,
        "phase_a_external_provider_allowed": provider_allowed,
        "phase_a_requires_manual_review": manual_review,
        "can_override_phase_a": False,
        "recommends_external_provider": False,
        "recommends_retrieval": recommends_retrieval,
        "requires_manual_review": True,
    }


def monotonicity_violations(review: dict[str, Any], phase_a: dict[str, Any]) -> list[str]:
    violations: list[str] = []
    if review.get("can_override_phase_a") is not False:
        violations.append("can_override_phase_a must be false")
    if review.get("requires_manual_review") is not True:
        violations.append("requires_manual_review must be true")
    if review.get("phase_a_requires_manual_review") is not True:
        violations.append("phase_a_requires_manual_review must be true")
    if phase_a.get("external_provider_allowed") is False and review.get("recommends_external_provider"):
        violations.append("Phase B recommended provider use while Phase A disallowed it")
    if (
        phase_a_blocked(phase_a)
        or phase_a_clarification_required(phase_a)
    ) and review.get("recommends_retrieval"):
        violations.append("Phase B recommended retrieval while Phase A blocked or required clarification")
    return violations


def run_fixture(
    *,
    phase_a_report_dir: Path,
    holdout_path: Path,
    schema_path: Path,
    out_dir: Path,
) -> dict[str, Any]:
    schema = structured_probe.load_json(schema_path)
    structured_probe.validate_schema_shape(schema)
    phase_a_results = load_phase_a_results(phase_a_report_dir)
    holdout = load_holdout_cases(holdout_path)
    out_dir.mkdir(parents=True, exist_ok=True)

    result_rows: list[dict[str, Any]] = []
    for result in phase_a_results:
        case_id = result["case_id"]
        if case_id not in holdout:
            raise ValueError(f"missing holdout case for {case_id}")
        phase_a = corrected_phase_a_output(result)
        review = build_soft_review(
            case_id=case_id,
            input_text=holdout[case_id]["input_text"],
            phase_a=phase_a,
        )
        validation = structured_probe.validate_instance(review, schema)
        violations = monotonicity_violations(review, phase_a)
        row = {
            "schema_version": "phase_b_soft_review_fixture_result_v0",
            "case_id": case_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "source_phase_a_result_path": result.get("_source_result_path"),
            "manual_review_required": True,
            "semantic_truth_scored": False,
            "model_calls_made": False,
            "network_calls_made": False,
            "phase_b_review": review,
            "schema_valid": validation["schema_valid"],
            "validation_errors": validation["errors"],
            "monotonicity_violations": violations,
        }
        write_json(out_dir / f"{case_id}__phase_b_soft_review.json", row)
        result_rows.append(row)

    schema_valid_count = sum(1 for row in result_rows if row["schema_valid"])
    violation_rows = [
        {"case_id": row["case_id"], "violations": row["monotonicity_violations"]}
        for row in result_rows
        if row["monotonicity_violations"]
    ]
    summary = {
        "schema_version": "phase_b_soft_review_fixture_summary_v0",
        "milestone": "1G-B2-F2-B1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_phase_a_report_dir": str(phase_a_report_dir),
        "report_dir": str(out_dir),
        "total_cases": len(result_rows),
        "schema_valid_count": schema_valid_count,
        "schema_valid_all_cases": schema_valid_count == len(result_rows),
        "monotonicity_violation_count": len(violation_rows),
        "monotonicity_violations": violation_rows,
        "manual_review_required": True,
        "semantic_truth_scored": False,
        "model_calls_made": False,
        "network_calls_made": False,
        "phase_b_can_override_phase_a": False,
        "runtime_approved": False,
        "recommended_next_milestone": (
            "1G-B2-F2-B2 - Phase B soft-review harness integration"
            if schema_valid_count == len(result_rows) and not violation_rows
            else "1G-B2-F2-B1-R - Phase B fixture repair"
        ),
    }
    write_json(out_dir / SUMMARY_JSON, summary)
    write_summary_markdown(out_dir / SUMMARY_MD, summary)
    return summary


def write_summary_markdown(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# 1G-B2-F2-B1 Phase B Soft-Review Fixture Summary",
        "",
        "Manual review is required. This fixture does not prove semantic truth or approve runtime use.",
        "",
        f"- total cases: {summary['total_cases']}",
        f"- schema valid: {summary['schema_valid_count']}/{summary['total_cases']}",
        f"- monotonicity violations: {summary['monotonicity_violation_count']}",
        f"- model calls made: {summary['model_calls_made']}",
        f"- network calls made: {summary['network_calls_made']}",
        f"- Phase B can override Phase A: {summary['phase_b_can_override_phase_a']}",
        f"- runtime approved: {summary['runtime_approved']}",
        f"- recommended next milestone: {summary['recommended_next_milestone']}",
        "",
        "No memory, retrieval, provider routing, tool execution, backend route, frontend UI, queue, worker, hook, MCP, or BlueRev modeling behavior is added.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Phase B soft-review fixture probe.")
    parser.add_argument("--phase-a-report-dir", default=str(DEFAULT_PHASE_A_REPORT_DIR))
    parser.add_argument("--holdout", default=str(DEFAULT_HOLDOUT))
    parser.add_argument("--schema-path", default=str(DEFAULT_SCHEMA))
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    summary = run_fixture(
        phase_a_report_dir=Path(args.phase_a_report_dir),
        holdout_path=Path(args.holdout),
        schema_path=Path(args.schema_path),
        out_dir=Path(args.out_dir),
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
