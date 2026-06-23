"""Local Phase B soft-only proposal smoke and expanded panel.

This script is evaluation-only. It asks a local Ollama model to emit only a
soft-review proposal, validates a soft-only model-facing schema, and then builds
a deterministic internal envelope by combining saved Phase A/B2 state with the
soft proposal.

It does not write memory, retrieve runtime project data, call external providers,
execute tools, approve runtime behavior, or change Phase A hard-gate behavior.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import local_model_structured_output_probe as structured_probe
import local_phase_b_soft_review_probe as phase_b_probe


DEFAULT_SOURCE_B2_REPORT_DIR = Path("reports/local_model_smoke/1G-B2-F2-B2")
DEFAULT_HOLDOUT = Path("docs/holdout/intake_generalization_v0.jsonl")
DEFAULT_SCHEMA = Path("schemas/fast_secretary_soft_proposal_v0_1.schema.json")
DEFAULT_OUT_DIR = Path("reports/local_model_smoke/1G-B2-F2-B5-B")
DEFAULT_MODEL = "qwen3:8b"
DEFAULT_CASE_IDS = "HG-007,HG-010,HG-013,HG-016,HG-017,HG-018,HG-024,HG-025"
SUMMARY_JSON = "phase_b_deterministic_soft_clamp_summary.json"
SUMMARY_MD = "phase_b_deterministic_soft_clamp_summary.md"
MAX_CASES = 8
BASELINE_B4_SOFT_QUALITY_MATCH_COUNT = 14
BASELINE_B4_SOFT_QUALITY_COMPARED_COUNT = 29
BASELINE_B5A_SOFT_QUALITY_MATCH_COUNT = 22
BASELINE_B5A_SOFT_QUALITY_COMPARED_COUNT = 29

AUTHORITY_FIELD_NAMES = {
    "phase_a_case_id",
    "phase_a_blocked",
    "phase_a_clarification_required",
    "phase_a_external_provider_allowed",
    "phase_a_requires_manual_review",
    "can_override_phase_a",
    "recommends_external_provider",
    "recommends_retrieval",
    "requires_manual_review",
    "external_provider_allowed",
    "source_policy_for_future_retrieval",
    "allowed_future_retrieval_behavior",
    "retrieval_behavior",
    "redaction_required",
    "runtime_approved",
    "memory_write_allowed",
    "tool_execution_allowed",
}

SOFT_QUALITY_EXPECTATIONS = {
    "HG-007": {
        "project_bucket_any": ["bluerev"],
        "primary_domain_any": ["retrieval", "bioprocess", "modeling"],
        "domain_tag_any": ["literature", "source", "photobioreactors", "gas-liquid", "kla"],
        "soft_reason_code_any": ["source_candidate", "assumption_candidate", "contextual_summary"],
    },
    "HG-010": {
        "soft_reason_code_any": ["clarification_context", "contextual_summary", "unknown"],
        "followup_question_required": True,
    },
    "HG-013": {
        "project_bucket_any": ["jarvisos"],
        "primary_domain_any": ["memory"],
        "soft_reason_code_any": ["clarification_context", "memory_candidate", "contextual_summary", "unknown"],
        "followup_question_required": True,
    },
    "HG-016": {
        "primary_domain_any": ["security"],
        "possible_memory_card_type_any": ["none", "decision_card"],
        "storage_relevance_not": ["high"],
    },
    "HG-017": {
        "primary_domain_any": ["security"],
        "possible_memory_card_type_any": ["none", "decision_card"],
        "storage_relevance_not": ["high"],
    },
    "HG-018": {
        "project_bucket_any": ["jarvisos"],
        "primary_domain_any": ["memory", "security", "local_ai"],
        "domain_tag_any": ["memory", "provider", "privacy", "security", "jarvisos"],
        "project_bucket_not": ["unknown"],
        "primary_domain_not": ["unknown"],
    },
    "HG-024": {
        "project_bucket_any": ["jarvisos"],
        "primary_domain_any": ["memory", "local_ai"],
        "possible_memory_card_type_any": ["decision_card", "memory_card"],
        "project_bucket_not": ["coursework", "personal", "unknown"],
    },
    "HG-025": {
        "primary_domain_any": ["memory"],
        "soft_reason_code_any": ["clarification_context", "memory_candidate", "contextual_summary"],
        "followup_question_required": True,
        "project_bucket_not": ["personal"],
    },
}


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_source_results(report_dir: Path) -> dict[str, dict[str, Any]]:
    paths = sorted(report_dir.glob("*__result.json"))
    if not paths:
        raise ValueError(f"no saved result files found in {report_dir}")
    return {path.name.split("__", 1)[0]: structured_probe.load_json(path) for path in paths}


def select_case_ids(case_ids: str) -> list[str]:
    selected = [case_id.strip() for case_id in case_ids.split(",") if case_id.strip()]
    if not selected:
        raise ValueError("--case-ids did not include any case IDs")
    if len(selected) > MAX_CASES:
        raise ValueError(f"Phase B expanded panel is limited to {MAX_CASES} cases")
    if len(selected) != len(set(selected)):
        raise ValueError("--case-ids contains duplicate case IDs")
    return selected


def compact_hard_envelope(phase_a: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_policy_for_future_retrieval": phase_a.get("source_policy_for_future_retrieval"),
        "allowed_future_retrieval_behavior": phase_a.get("allowed_future_retrieval_behavior"),
        "external_provider_allowed": phase_a.get("external_provider_allowed"),
        "requires_manual_review": phase_a.get("requires_manual_review"),
        "clarification_required": phase_a.get("clarification_required"),
        "redaction_required": phase_a.get("redaction_required"),
        "contains_secret_or_credential": phase_a.get("contains_secret_or_credential"),
        "contains_raw_private_or_ip_sensitive_context": phase_a.get(
            "contains_raw_private_or_ip_sensitive_context"
        ),
        "mentions_external_provider_or_upload_intent": phase_a.get(
            "mentions_external_provider_or_upload_intent"
        ),
        "hard_reason_code": phase_a.get("hard_reason_code"),
        "sensitivity_bucket_proposal": phase_a.get("sensitivity_bucket_proposal"),
    }



def build_general_instruction_block() -> str:
    return """
You are a local-only soft-review worker.

Return exactly one JSON object matching the supplied JSON Schema.
Fill only the soft-review fields in the schema.
Do not add policy, permission, routing, retrieval authorization, provider authorization, tool, memory-write, or runtime fields.
Do not include markdown, comments, code fences, or prose outside JSON.
If exact credentials or private keys appear, describe their presence generically instead of copying literal values.

Goal:
Create a useful reviewer-facing soft proposal. Describe what the input is about,
why it may matter later, and what type of review card it could become. You are
not deciding safety, policy, provider use, retrieval use, memory writes, or any
runtime action.

Use general categories, not one-off labels.

Project bucket guidance:
- "jarvisos": AI-system architecture, local model evaluation, memory infrastructure, retrieval systems, provider policy, structured-output probes, validation, schemas, automation infrastructure.
- "bluerev": the user's microalgae, photobioreactor, cleantech, process-engineering, reactor-design, or engineering-modeling project.
- "coursework": exams, university exercises, lecture notes, academic problem solving, or study material.
- "personal": personal life, relationships, habits, preferences, logistics, health, or emotional context.
- "general": broad information not tied to a durable project.
- "unknown": only when there is no reliable project signal.

Primary domain guidance:
- "memory": memory records, saved context, previous decisions, canonical or superseded information, memory promotion, memory review.
- "local_ai": local models, structured output, model evaluation, benchmark evidence, context packs, or AI capability testing.
- "software": application architecture, code, scripts, tests, schemas, repositories, automation, or implementation workflow.
- "retrieval": finding, selecting, reviewing, or using sources, documents, or literature as evidence.
- "security": credentials, secrets, private keys, sensitive paths, privacy exposure, external upload risk, or provider-boundary risk.
- "modeling": mathematical, engineering, simulation, or computational modeling assumptions.
- "bioprocess": biological or process-engineering systems, cultivation, reactors, growth, gas/liquid transfer, nutrients, biomass, or process constraints.
- "reactor_design": reactor geometry, hydraulics, materials, modules, equipment, architecture, or physical design choices.
- "coursework": academic study, exam, or exercise context.
- "personal": personal life context.
- "general": broad uncategorized information.
- "unknown": only when no domain signal is reliable.

Unknown policy:
Do not use "unknown" as a safe default. Use it only when the input lacks enough
signal to choose a better enum. If the input clearly concerns a system, project,
domain, source, decision, security issue, memory update, or modeling assumption,
choose the closest available category.

Domain tags:
Use 2 to 6 compact, reusable conceptual tags. Prefer tags that describe:
system/component, evidence type, engineering area, review state, or uncertainty.
Avoid overly narrow tags unless the input itself is specifically about that concept.

Card type guidance:
- "source_card": source, literature, document discovery, or candidate evidence.
- "decision_card": explicit decision, policy change, approval, rejection, supersession, or canonical update.
- "assumption_card": assumption, constraint, dependency, uncertainty, or condition affecting later reasoning or modeling.
- "evidence_card": benchmark result, test result, experimental evidence, report finding, or measured outcome.
- "memory_card": durable user or project context useful later but not clearly a decision, source, evidence, or assumption.
- "knowledge_card": general stable knowledge that may be reusable.
- "task_card": concrete future task or action request.
- "none": content should not become a memory candidate, especially raw secrets or low-value transient content.
- "unknown": only when the card type cannot be inferred.

Soft reason code guidance:
- "source_candidate": asks to find, review, or use sources or literature.
- "decision_candidate": changes, supersedes, approves, rejects, or establishes a decision.
- "assumption_candidate": contains assumptions, constraints, dependencies, or conditions to verify.
- "evidence_candidate": reports test results, benchmark evidence, measurements, or observed outcomes.
- "memory_candidate": contains durable context that may be useful later.
- "clarification_context": depends on an ambiguous reference, missing entity, unclear scope, or unresolved source.
- "contextual_summary": useful summary, but not clearly source, decision, assumption, evidence, or memory.
- "low_value": transient or low-value context.
- "unknown": last resort only.

Rationale:
brief_rationale should explain why the proposal is useful for a future reviewer.
Mention the general reason: source discovery, decision update, assumption
tracking, evidence review, ambiguity resolution, security/privacy context, or
durable project memory. Avoid generic filler such as "this aligns with the
criteria". Do not grant permission, approve actions, or make policy decisions.

Follow-up question:
Use suggested_followup_question only when a concrete ambiguity remains.
Good follow-up questions ask for the missing entity, source, scope, decision,
assumption, or reference. Do not ask meta-questions like whether a card should
be created. Return an empty string when no useful clarification question is
needed.
""".strip()


def build_phase_b_prompt(*, case_id: str, input_text: str) -> str:
    # Do not expose Phase A policy fields. The case_id is retained for reportability
    # only; the instruction profile remains general and case-agnostic.
    return "\n".join(
        [
            build_general_instruction_block(),
            "",
            f"Case ID: {case_id}",
            "Input text:",
            input_text,
        ]
    )

def authority_field_leakage(value: Any) -> list[str]:
    if not isinstance(value, dict):
        return []
    return sorted(field for field in value if field in AUTHORITY_FIELD_NAMES)


def parse_soft_proposal(raw_response: dict[str, Any]) -> tuple[dict[str, Any] | None, str | None]:
    return structured_probe.parse_model_content(raw_response)


def normalized(value: Any) -> str:
    return str(value).strip().lower()


def contains_any_text(value: Any, options: list[str]) -> bool:
    text = normalized(value)
    return any(normalized(option) in text for option in options)


def list_contains_any(values: Any, options: list[str]) -> bool:
    if not isinstance(values, list):
        return False
    return any(contains_any_text(item, options) for item in values)


def evaluate_soft_quality(case_id: str, proposal: Any) -> dict[str, Any]:
    """Return advisory quality diagnostics only.

    These checks are intentionally not runtime authority. They help decide
    whether the soft proposals are worth semantic review in the next milestone.
    """
    if not isinstance(proposal, dict):
        return {
            "case_id": case_id,
            "quality_compared": False,
            "quality_match_count": 0,
            "quality_compared_count": 0,
            "quality_misses": [{"field": "$", "reason": "soft proposal is not an object"}],
        }
    expectation = SOFT_QUALITY_EXPECTATIONS.get(case_id, {})
    misses: list[dict[str, Any]] = []
    compared = 0
    matched = 0

    def check_any(field: str, expected_values: list[str]) -> None:
        nonlocal compared, matched
        compared += 1
        actual = proposal.get(field)
        ok = normalized(actual) in {normalized(value) for value in expected_values}
        if ok:
            matched += 1
        else:
            misses.append(
                {
                    "field": field,
                    "actual": actual,
                    "expected_any": expected_values,
                    "reason": "advisory soft-quality expectation miss",
                }
            )

    def check_not(field: str, forbidden_values: list[str]) -> None:
        nonlocal compared, matched
        compared += 1
        actual = proposal.get(field)
        ok = normalized(actual) not in {normalized(value) for value in forbidden_values}
        if ok:
            matched += 1
        else:
            misses.append(
                {
                    "field": field,
                    "actual": actual,
                    "forbidden": forbidden_values,
                    "reason": "advisory soft-quality forbidden value",
                }
            )

    if "project_bucket_any" in expectation:
        check_any("project_bucket", expectation["project_bucket_any"])
    if "project_bucket_not" in expectation:
        check_not("project_bucket", expectation["project_bucket_not"])
    if "primary_domain_any" in expectation:
        check_any("primary_domain", expectation["primary_domain_any"])
    if "primary_domain_not" in expectation:
        check_not("primary_domain", expectation["primary_domain_not"])
    if "soft_reason_code_any" in expectation:
        check_any("soft_reason_code", expectation["soft_reason_code_any"])
    if "possible_memory_card_type_any" in expectation:
        check_any("possible_memory_card_type", expectation["possible_memory_card_type_any"])
    if "storage_relevance_not" in expectation:
        check_not("storage_relevance", expectation["storage_relevance_not"])
    if "domain_tag_any" in expectation:
        compared += 1
        if list_contains_any(proposal.get("domain_tags"), expectation["domain_tag_any"]):
            matched += 1
        else:
            misses.append(
                {
                    "field": "domain_tags",
                    "actual": proposal.get("domain_tags"),
                    "expected_any_substring": expectation["domain_tag_any"],
                    "reason": "advisory soft-quality missing useful tag",
                }
            )
    if expectation.get("followup_question_required"):
        compared += 1
        actual = proposal.get("suggested_followup_question")
        if isinstance(actual, str) and actual.strip():
            matched += 1
        else:
            misses.append(
                {
                    "field": "suggested_followup_question",
                    "actual": actual,
                    "expected": "non-empty question",
                    "reason": "ambiguous case should suggest a clarification question",
                }
            )

    return {
        "case_id": case_id,
        "quality_compared": compared > 0,
        "quality_match_count": matched,
        "quality_compared_count": compared,
        "quality_misses": misses,
    }


def phase_a_secret_or_credential(phase_a: dict[str, Any]) -> bool:
    return (
        phase_a.get("contains_secret_or_credential") is True
        or phase_a.get("sensitivity_bucket_proposal") == "secret"
        or phase_a.get("hard_reason_code") == "secret_or_credential"
    )


def phase_a_raw_private_or_provider_sensitive(phase_a: dict[str, Any]) -> bool:
    return (
        phase_a.get("contains_raw_private_or_ip_sensitive_context") is True
        or phase_a.get("sensitivity_bucket_proposal") == "sensitive"
        or phase_a.get("hard_reason_code") == "provider_or_upload_intent"
    )


def deterministic_soft_clamp_reasons(phase_a: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    if phase_a_secret_or_credential(phase_a):
        reasons.append("secret_or_credential")
    if phase_a_raw_private_or_provider_sensitive(phase_a):
        reasons.append("raw_private_or_provider_sensitive")
    if phase_b_probe.phase_a_blocked(phase_a):
        reasons.append("phase_a_blocked")
    return reasons


def apply_deterministic_soft_clamp(
    *,
    phase_a: dict[str, Any],
    raw_proposal: dict[str, Any] | None,
) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
    """Return the effective proposal used by the envelope.

    The raw model proposal remains preserved for audit. Clamping is deterministic
    and driven only by Phase A hard-gate state.
    """
    if not isinstance(raw_proposal, dict):
        return raw_proposal, []

    reasons = deterministic_soft_clamp_reasons(phase_a)
    effective = dict(raw_proposal)
    clamps: list[dict[str, Any]] = []
    if not reasons:
        return effective, clamps

    secret = "secret_or_credential" in reasons
    private = "raw_private_or_provider_sensitive" in reasons

    if secret:
        replacements = {
            "summary_short": "Security-sensitive input was detected and withheld from memory candidacy.",
            "primary_domain": "security",
            "domain_tags": ["security", "sensitive-context"],
            "storage_relevance": "none",
            "usefulness_for_future_review": "low",
            "possible_memory_card_type": "none",
            "soft_reason_code": "contextual_summary",
            "brief_rationale": (
                "Phase A flagged secret or credential material. The effective soft proposal keeps only "
                "generic security-review context and does not preserve the sensitive content."
            ),
            "suggested_followup_question": "",
        }
        severity = "secret_or_credential"
    elif private:
        replacements = {
            "summary_short": "Sensitive private context was detected and requires review without exposing raw content.",
            "primary_domain": "security",
            "domain_tags": ["security", "private-context"],
            "storage_relevance": "low",
            "usefulness_for_future_review": "low",
            "possible_memory_card_type": "none",
            "soft_reason_code": "contextual_summary",
            "brief_rationale": (
                "Phase A flagged private or provider-sensitive context. The effective soft proposal keeps only "
                "generic security-review context."
            ),
            "suggested_followup_question": "",
        }
        severity = "raw_private_or_provider_sensitive"
    else:
        replacements = {
            "storage_relevance": "low",
            "possible_memory_card_type": "none",
        }
        severity = "phase_a_blocked"

    for field, replacement in replacements.items():
        previous = effective.get(field)
        if previous != replacement:
            effective[field] = replacement
            clamps.append(
                {
                    "field": field,
                    "reason": severity,
                    "previous": previous,
                    "replacement": replacement,
                }
            )

    return effective, clamps


def build_review_envelope(
    *,
    case_id: str,
    source_result: dict[str, Any],
    raw_soft_proposal: dict[str, Any] | None,
    effective_soft_proposal: dict[str, Any] | None,
    raw_proposal_validation: dict[str, Any],
    effective_proposal_validation: dict[str, Any],
    raw_authority_leakage: list[str],
    effective_authority_leakage: list[str],
    raw_soft_quality: dict[str, Any],
    effective_soft_quality: dict[str, Any],
    deterministic_clamps: list[dict[str, Any]],
) -> dict[str, Any]:
    phase_a = phase_b_probe.corrected_phase_a_output(source_result)
    return {
        "schema_version": "fast_secretary_review_envelope_v0_1",
        "case_id": case_id,
        "soft_generation_mode": "local_model",
        "manual_review_required": True,
        "semantic_truth_scored": False,
        "runtime_approved": False,
        "external_provider_calls_made": False,
        "local_model_calls_made": True,
        "phase_a_hard_gate": compact_hard_envelope(phase_a),
        "phase_b_soft_proposal_model_raw": raw_soft_proposal,
        "phase_b_soft_proposal_effective": effective_soft_proposal,
        "phase_b_soft_proposal": effective_soft_proposal,
        "phase_b_soft_proposal_model_raw_schema_valid": raw_proposal_validation["schema_valid"],
        "phase_b_soft_proposal_effective_schema_valid": effective_proposal_validation["schema_valid"],
        "phase_b_soft_proposal_schema_valid": effective_proposal_validation["schema_valid"],
        "phase_b_soft_proposal_model_raw_validation_errors": raw_proposal_validation["errors"],
        "phase_b_soft_proposal_effective_validation_errors": effective_proposal_validation["errors"],
        "phase_b_soft_proposal_validation_errors": effective_proposal_validation["errors"],
        "phase_b_soft_proposal_model_raw_authority_field_leakage_count": len(raw_authority_leakage),
        "phase_b_soft_proposal_effective_authority_field_leakage_count": len(effective_authority_leakage),
        "authority_field_leakage": effective_authority_leakage,
        "authority_field_leakage_count": len(effective_authority_leakage),
        "soft_proposal_deterministic_clamps": deterministic_clamps,
        "soft_quality_review_required": True,
        "soft_quality_truth_scored": False,
        "raw_soft_quality_diagnostic": raw_soft_quality,
        "effective_soft_quality_diagnostic": effective_soft_quality,
        "soft_quality_diagnostic": effective_soft_quality,
    }


def build_model_result(
    *,
    case_id: str,
    source_result: dict[str, Any],
    schema: dict[str, Any],
    schema_path: Path,
    model: str,
    raw_path: Path,
    raw_call: dict[str, Any],
) -> dict[str, Any]:
    parsed, parse_error = (None, raw_call["error"])
    if raw_call["ok"] and isinstance(raw_call["body"], dict):
        parsed, parse_error = parse_soft_proposal(raw_call["body"])
    raw_validation = structured_probe.validate_instance(parsed, schema) if parsed is not None else {
        "schema_valid": False,
        "errors": [{"field": "$", "error": "json_not_parsed"}],
    }
    phase_a = phase_b_probe.corrected_phase_a_output(source_result)
    effective_proposal, deterministic_clamps = apply_deterministic_soft_clamp(
        phase_a=phase_a,
        raw_proposal=parsed,
    )
    effective_validation = (
        structured_probe.validate_instance(effective_proposal, schema)
        if effective_proposal is not None
        else {
            "schema_valid": False,
            "errors": [{"field": "$", "error": "json_not_parsed"}],
        }
    )
    raw_leakage = authority_field_leakage(parsed)
    effective_leakage = authority_field_leakage(effective_proposal)
    raw_soft_quality = evaluate_soft_quality(case_id, parsed)
    effective_soft_quality = evaluate_soft_quality(case_id, effective_proposal)
    envelope = build_review_envelope(
        case_id=case_id,
        source_result=source_result,
        raw_soft_proposal=parsed,
        effective_soft_proposal=effective_proposal,
        raw_proposal_validation=raw_validation,
        effective_proposal_validation=effective_validation,
        raw_authority_leakage=raw_leakage,
        effective_authority_leakage=effective_leakage,
        raw_soft_quality=raw_soft_quality,
        effective_soft_quality=effective_soft_quality,
        deterministic_clamps=deterministic_clamps,
    )
    return {
        "schema_version": "phase_b_deterministic_soft_clamp_result_v0",
        "milestone": "1G-B2-F2-B5-B",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "case_id": case_id,
        "model": model,
        "schema_path": str(schema_path),
        "raw_response_path": str(raw_path),
        "manual_review_required": True,
        "semantic_truth_scored": False,
        "runtime_approved": False,
        "phase_a_result_source": source_result.get("_source_result_path"),
        "ollama_ok": raw_call["ok"],
        "ollama_status": raw_call["status"],
        "duration_seconds": raw_call["duration_seconds"],
        "json_parse_passed": parsed is not None,
        "json_parse_error": parse_error,
        "phase_b_soft_proposal_model_raw_schema_valid": raw_validation["schema_valid"],
        "phase_b_soft_proposal_effective_schema_valid": effective_validation["schema_valid"],
        "schema_valid": effective_validation["schema_valid"],
        "validation_errors": effective_validation["errors"],
        "phase_b_soft_proposal_model_raw_validation_errors": raw_validation["errors"],
        "phase_b_soft_proposal_effective_validation_errors": effective_validation["errors"],
        "phase_b_soft_proposal_model_raw_authority_field_leakage": raw_leakage,
        "phase_b_soft_proposal_effective_authority_field_leakage": effective_leakage,
        "phase_b_soft_proposal_model_raw_authority_field_leakage_count": len(raw_leakage),
        "phase_b_soft_proposal_effective_authority_field_leakage_count": len(effective_leakage),
        "authority_field_leakage": effective_leakage,
        "authority_field_leakage_count": len(effective_leakage),
        "phase_b_soft_proposal_model_raw": parsed,
        "phase_b_soft_proposal_effective": effective_proposal,
        "phase_b_soft_proposal": effective_proposal,
        "soft_proposal_deterministic_clamps": deterministic_clamps,
        "soft_quality_review_required": True,
        "soft_quality_truth_scored": False,
        "raw_soft_quality_diagnostic": raw_soft_quality,
        "effective_soft_quality_diagnostic": effective_soft_quality,
        "soft_quality_diagnostic": effective_soft_quality,
        "review_envelope": envelope,
    }


def soft_quality_summary(
    results: list[dict[str, Any]],
    *,
    diagnostic_key: str,
    baseline_match_count: int,
    baseline_compared_count: int,
) -> dict[str, Any]:
    compared = 0
    matched = 0
    cases_with_misses: list[dict[str, Any]] = []
    for result in results:
        diagnostic = result.get(diagnostic_key) or {}
        compared += diagnostic.get("quality_compared_count", 0)
        matched += diagnostic.get("quality_match_count", 0)
        misses = diagnostic.get("quality_misses", [])
        if misses:
            cases_with_misses.append({"case_id": result["case_id"], "misses": misses})
    miss_count = compared - matched
    baseline_rate = baseline_match_count / baseline_compared_count
    current_rate = matched / compared if compared else None
    improved_over_baseline = matched > baseline_match_count
    return {
        "soft_quality_review_required": True,
        "soft_quality_truth_scored": False,
        "soft_quality_match_count": matched,
        "soft_quality_compared_count": compared,
        "soft_quality_miss_count": miss_count,
        "soft_quality_match_rate": current_rate,
        "baseline_match_count": baseline_match_count,
        "baseline_compared_count": baseline_compared_count,
        "baseline_match_rate": baseline_rate,
        "improved_over_baseline": improved_over_baseline,
        "baseline_b4_match_count": BASELINE_B4_SOFT_QUALITY_MATCH_COUNT,
        "baseline_b4_compared_count": BASELINE_B4_SOFT_QUALITY_COMPARED_COUNT,
        "baseline_b4_match_rate": BASELINE_B4_SOFT_QUALITY_MATCH_COUNT / BASELINE_B4_SOFT_QUALITY_COMPARED_COUNT,
        "baseline_b5a_match_count": BASELINE_B5A_SOFT_QUALITY_MATCH_COUNT,
        "baseline_b5a_compared_count": BASELINE_B5A_SOFT_QUALITY_COMPARED_COUNT,
        "baseline_b5a_match_rate": BASELINE_B5A_SOFT_QUALITY_MATCH_COUNT / BASELINE_B5A_SOFT_QUALITY_COMPARED_COUNT,
        "improved_over_b4_baseline": matched > BASELINE_B4_SOFT_QUALITY_MATCH_COUNT,
        "improved_over_b5a_baseline": matched > BASELINE_B5A_SOFT_QUALITY_MATCH_COUNT,
        "cases_with_soft_quality_misses": cases_with_misses,
        "note": "Diagnostic only: soft-quality checks do not approve runtime behavior or semantic truth.",
    }


def summarize_results(results: list[dict[str, Any]], report_dir: Path) -> dict[str, Any]:
    parse_count = sum(1 for result in results if result["json_parse_passed"])
    raw_schema_valid_count = sum(
        1 for result in results if result["phase_b_soft_proposal_model_raw_schema_valid"]
    )
    effective_schema_valid_count = sum(
        1 for result in results if result["phase_b_soft_proposal_effective_schema_valid"]
    )
    raw_leakage_results = [
        {
            "case_id": result["case_id"],
            "authority_field_leakage": result["phase_b_soft_proposal_model_raw_authority_field_leakage"],
        }
        for result in results
        if result["phase_b_soft_proposal_model_raw_authority_field_leakage"]
    ]
    effective_leakage_results = [
        {
            "case_id": result["case_id"],
            "authority_field_leakage": result["phase_b_soft_proposal_effective_authority_field_leakage"],
        }
        for result in results
        if result["phase_b_soft_proposal_effective_authority_field_leakage"]
    ]
    raw_validation_failures = [
        {
            "case_id": result["case_id"],
            "errors": result["phase_b_soft_proposal_model_raw_validation_errors"],
        }
        for result in results
        if not result["phase_b_soft_proposal_model_raw_schema_valid"]
    ]
    effective_validation_failures = [
        {
            "case_id": result["case_id"],
            "errors": result["phase_b_soft_proposal_effective_validation_errors"],
        }
        for result in results
        if not result["phase_b_soft_proposal_effective_schema_valid"]
    ]
    deterministic_clamp_cases = [
        {
            "case_id": result["case_id"],
            "clamp_count": len(result.get("soft_proposal_deterministic_clamps") or []),
            "clamps": result.get("soft_proposal_deterministic_clamps") or [],
        }
        for result in results
        if result.get("soft_proposal_deterministic_clamps")
    ]
    deterministic_clamp_count = sum(case["clamp_count"] for case in deterministic_clamp_cases)
    raw_quality = soft_quality_summary(
        results,
        diagnostic_key="raw_soft_quality_diagnostic",
        baseline_match_count=BASELINE_B5A_SOFT_QUALITY_MATCH_COUNT,
        baseline_compared_count=BASELINE_B5A_SOFT_QUALITY_COMPARED_COUNT,
    )
    effective_quality = soft_quality_summary(
        results,
        diagnostic_key="effective_soft_quality_diagnostic",
        baseline_match_count=BASELINE_B5A_SOFT_QUALITY_MATCH_COUNT,
        baseline_compared_count=BASELINE_B5A_SOFT_QUALITY_COMPARED_COUNT,
    )
    pass_structural = (
        len(results) > 0
        and parse_count == len(results)
        and effective_schema_valid_count == len(results)
        and not effective_leakage_results
    )
    pass_deterministic_clamp = pass_structural and effective_quality["improved_over_b5a_baseline"]
    return {
        "schema_version": "phase_b_deterministic_soft_clamp_summary_v0",
        "milestone": "1G-B2-F2-B5-B",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "report_dir": str(report_dir),
        "total_runs": len(results),
        "manual_review_required": True,
        "semantic_truth_scored": False,
        "runtime_approved": False,
        "parse_count": parse_count,
        "phase_b_soft_proposal_model_raw_schema_valid_count": raw_schema_valid_count,
        "phase_b_soft_proposal_effective_schema_valid_count": effective_schema_valid_count,
        "schema_valid_count": effective_schema_valid_count,
        "schema_valid_all_cases": effective_schema_valid_count == len(results),
        "phase_b_soft_proposal_model_raw_validation_failures": raw_validation_failures,
        "phase_b_soft_proposal_effective_validation_failures": effective_validation_failures,
        "validation_failures": effective_validation_failures,
        "phase_b_soft_proposal_model_raw_authority_field_leakage_count": len(raw_leakage_results),
        "phase_b_soft_proposal_effective_authority_field_leakage_count": len(effective_leakage_results),
        "authority_field_leakage_count": len(effective_leakage_results),
        "phase_b_soft_proposal_model_raw_authority_field_leakage": raw_leakage_results,
        "phase_b_soft_proposal_effective_authority_field_leakage": effective_leakage_results,
        "authority_field_leakage": effective_leakage_results,
        "deterministic_soft_clamp_count": deterministic_clamp_count,
        "deterministic_soft_clamp_cases": deterministic_clamp_cases,
        "model_facing_schema": "fast_secretary_soft_proposal_v0_1.schema.json",
        "model_facing_schema_has_authority_fields": False,
        "model_facing_instruction_profile": "general_soft_review_v0_2",
        "instruction_profile_case_specific": False,
        "local_ollama_calls_made": True,
        "external_provider_calls_made": False,
        "network_calls_made": False,
        "accepted_for_runtime": False,
        "strong_enough_for_semantic_quality_review": pass_deterministic_clamp,
        "strong_enough_for_runtime": False,
        "raw_soft_quality_summary": raw_quality,
        "effective_soft_quality_summary": effective_quality,
        "soft_quality_summary": effective_quality,
        "recommended_next_milestone": (
            "1G-B2-F2-B5 - Phase B semantic quality review"
            if pass_deterministic_clamp
            else "1G-B2-F2-B5-B-R - Deterministic secret/private soft clamp repair"
        ),
        "answers": {
            "parseable_json_all_cases": parse_count == len(results),
            "raw_schema_valid_all_cases": raw_schema_valid_count == len(results),
            "effective_schema_valid_all_cases": effective_schema_valid_count == len(results),
            "schema_valid_all_cases": effective_schema_valid_count == len(results),
            "raw_authority_field_leakage_count": len(raw_leakage_results),
            "effective_authority_field_leakage_count": len(effective_leakage_results),
            "authority_field_leakage_count": len(effective_leakage_results),
            "model_facing_schema_has_authority_fields": False,
            "instruction_profile_case_specific": False,
            "runtime_approved": False,
            "external_provider_calls_made": False,
            "soft_quality_review_required": True,
            "soft_quality_truth_scored": False,
            "raw_soft_quality_match_count": raw_quality["soft_quality_match_count"],
            "effective_soft_quality_match_count": effective_quality["soft_quality_match_count"],
            "effective_soft_quality_improved_over_b5a_baseline": effective_quality[
                "improved_over_b5a_baseline"
            ],
            "deterministic_soft_clamp_count": deterministic_clamp_count,
            "strong_enough_for_semantic_quality_review": pass_deterministic_clamp,
        },
    }


def write_summary_markdown(path: Path, summary: dict[str, Any]) -> None:
    raw_quality = summary["raw_soft_quality_summary"]
    effective_quality = summary["effective_soft_quality_summary"]
    lines = [
        "# 1G-B2-F2-B5-B Deterministic Phase B Soft Clamp Summary",
        "",
        "Manual review is required. This smoke does not prove semantic truth or approve runtime use.",
        "",
        f"- total runs: {summary['total_runs']}",
        f"- parse: {summary['parse_count']}/{summary['total_runs']}",
        f"- raw schema valid: {summary['phase_b_soft_proposal_model_raw_schema_valid_count']}/{summary['total_runs']}",
        f"- effective schema valid: {summary['phase_b_soft_proposal_effective_schema_valid_count']}/{summary['total_runs']}",
        f"- raw authority field leakage count: {summary['phase_b_soft_proposal_model_raw_authority_field_leakage_count']}",
        f"- effective authority field leakage count: {summary['phase_b_soft_proposal_effective_authority_field_leakage_count']}",
        f"- deterministic soft clamp count: {summary['deterministic_soft_clamp_count']}",
        f"- deterministic soft clamp cases: {[case['case_id'] for case in summary['deterministic_soft_clamp_cases']]}",
        f"- model-facing schema has authority fields: {summary['model_facing_schema_has_authority_fields']}",
        f"- instruction profile case-specific: {summary['instruction_profile_case_specific']}",
        f"- local Ollama calls made: {summary['local_ollama_calls_made']}",
        f"- external provider calls made: {summary['external_provider_calls_made']}",
        f"- runtime approved: {summary['runtime_approved']}",
        f"- raw soft quality: {raw_quality['soft_quality_match_count']}/{raw_quality['soft_quality_compared_count']}",
        f"- effective soft quality: {effective_quality['soft_quality_match_count']}/{effective_quality['soft_quality_compared_count']}",
        f"- B5-A baseline: {effective_quality['baseline_b5a_match_count']}/{effective_quality['baseline_b5a_compared_count']}",
        f"- effective improved over B5-A baseline: {effective_quality['improved_over_b5a_baseline']}",
        f"- raw soft quality miss count: {raw_quality['soft_quality_miss_count']}",
        f"- effective soft quality miss count: {effective_quality['soft_quality_miss_count']}",
        f"- strong enough for semantic quality review: {summary['strong_enough_for_semantic_quality_review']}",
        f"- recommended next milestone: {summary['recommended_next_milestone']}",
        "",
        "Qwen receives only the soft-only proposal schema and the input text. Phase A hard fields are merged later by deterministic Python into an internal review envelope.",
        "",
        "The raw Qwen soft proposal is preserved for audit. The review envelope uses the deterministic effective soft proposal.",
        "",
        "Raw quality describes Qwen behavior. Effective quality describes Qwen plus deterministic clamp behavior. Neither approves runtime behavior, memory writes, retrieval, provider use, tool execution, or semantic truth.",
        "",
        "No memory, retrieval, provider routing, tool execution, backend route, frontend UI, queue, worker, hook, MCP, or BlueRev modeling behavior is added.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def run_local_smoke(
    *,
    source_b2_report_dir: Path,
    holdout_path: Path,
    schema_path: Path,
    out_dir: Path,
    model: str,
    case_ids: str,
    timeout_seconds: int,
) -> dict[str, Any]:
    if timeout_seconds < 1:
        raise ValueError("--timeout-seconds must be greater than 0")
    selected_case_ids = select_case_ids(case_ids)
    source_results = load_source_results(source_b2_report_dir)
    holdout = phase_b_probe.load_holdout_cases(holdout_path)
    schema = structured_probe.load_json(schema_path)
    structured_probe.validate_schema_shape(schema)
    if authority_field_leakage(schema.get("properties", {})):
        raise ValueError("model-facing soft proposal schema contains authority fields")
    out_dir.mkdir(parents=True, exist_ok=True)

    results: list[dict[str, Any]] = []
    for case_id in selected_case_ids:
        if case_id not in source_results:
            raise ValueError(f"missing source B2 result for {case_id}")
        if case_id not in holdout:
            raise ValueError(f"missing holdout input for {case_id}")
        source_result = dict(source_results[case_id])
        source_result["_source_result_path"] = str(source_b2_report_dir / f"{case_id}__result.json")
        prompt = build_phase_b_prompt(
            case_id=case_id,
            input_text=holdout[case_id]["input_text"],
        )
        raw_call = structured_probe.call_ollama_chat(
            model=model,
            prompt=prompt,
            schema=schema,
            timeout_seconds=timeout_seconds,
        )
        raw_path = out_dir / f"{case_id}__phase_b_soft_only_raw_response.json"
        result_path = out_dir / f"{case_id}__phase_b_soft_only_result.json"
        write_json(raw_path, raw_call)
        result = build_model_result(
            case_id=case_id,
            source_result=source_result,
            schema=schema,
            schema_path=schema_path,
            model=model,
            raw_path=raw_path,
            raw_call=raw_call,
        )
        write_json(result_path, result)
        results.append(result)
        raw_quality = result["raw_soft_quality_diagnostic"]
        effective_quality = result["effective_soft_quality_diagnostic"]
        print(
            f"{model} {case_id}: "
            f"parse={result['json_parse_passed']} "
            f"raw_schema_valid={result['phase_b_soft_proposal_model_raw_schema_valid']} "
            f"effective_schema_valid={result['phase_b_soft_proposal_effective_schema_valid']} "
            f"raw_authority_leakage={result['phase_b_soft_proposal_model_raw_authority_field_leakage_count']} "
            f"effective_authority_leakage={result['phase_b_soft_proposal_effective_authority_field_leakage_count']} "
            f"clamps={len(result['soft_proposal_deterministic_clamps'])} "
            f"raw_soft_quality={raw_quality['quality_match_count']}/{raw_quality['quality_compared_count']} "
            f"effective_soft_quality={effective_quality['quality_match_count']}/{effective_quality['quality_compared_count']} "
            f"duration={result['duration_seconds']}"
        )

    summary = summarize_results(results, out_dir)
    write_json(out_dir / SUMMARY_JSON, summary)
    write_summary_markdown(out_dir / SUMMARY_MD, summary)
    print(f"summary json: {out_dir / SUMMARY_JSON}")
    print(f"summary md: {out_dir / SUMMARY_MD}")
    return summary


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Deterministic Phase B soft-review clamp smoke.")
    parser.add_argument("--source-b2-report-dir", default=str(DEFAULT_SOURCE_B2_REPORT_DIR))
    parser.add_argument("--holdout", default=str(DEFAULT_HOLDOUT))
    parser.add_argument("--schema-path", default=str(DEFAULT_SCHEMA))
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--case-ids", default=DEFAULT_CASE_IDS)
    parser.add_argument("--timeout-seconds", type=int, default=180)
    parser.add_argument("--run-local", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    try:
        if not args.run_local:
            raise ValueError("--run-local is required")
        run_local_smoke(
            source_b2_report_dir=Path(args.source_b2_report_dir),
            holdout_path=Path(args.holdout),
            schema_path=Path(args.schema_path),
            out_dir=Path(args.out_dir),
            model=args.model,
            case_ids=args.case_ids,
            timeout_seconds=args.timeout_seconds,
        )
        return 0
    except ValueError as exc:
        print(f"phase b deterministic soft clamp failed: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
