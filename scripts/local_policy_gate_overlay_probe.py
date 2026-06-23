import argparse
import json
import re
import sys
from copy import deepcopy
from typing import Any


HARD_GATE_FIELDS = {
    "contains_secret_or_credential",
    "contains_raw_private_or_ip_sensitive_context",
    "mentions_external_provider_or_upload_intent",
    "memory_boundary_or_write_authority_claim",
    "retrieval_or_source_use_request",
    "unresolved_assumption_or_open_decision",
    "clarification_required",
    "redaction_required",
    "external_provider_allowed",
    "source_policy_for_future_retrieval",
    "allowed_future_retrieval_behavior",
    "lifecycle_status_proposal",
    "sensitivity_bucket_proposal",
    "requires_manual_review",
    "hard_reason_code",
    "hard_uncertain_fields",
}

SAFE_DEFAULTS: dict[str, Any] = {
    "contains_secret_or_credential": False,
    "contains_raw_private_or_ip_sensitive_context": False,
    "mentions_external_provider_or_upload_intent": False,
    "memory_boundary_or_write_authority_claim": False,
    "retrieval_or_source_use_request": False,
    "unresolved_assumption_or_open_decision": False,
    "clarification_required": False,
    "redaction_required": False,
    "external_provider_allowed": False,
    "source_policy_for_future_retrieval": "not_applicable",
    "allowed_future_retrieval_behavior": "none",
    "lifecycle_status_proposal": "raw_input",
    "sensitivity_bucket_proposal": "internal",
    "requires_manual_review": True,
    "hard_reason_code": "low_risk",
    "hard_uncertain_fields": [],
}

SECRET_PATTERN = re.compile(
    r"(\.env\b|\.ssh\b|id_rsa\b|private key|api[_ -]?key|password|token|secret)",
    re.IGNORECASE,
)
RAW_PRIVATE_PATTERN = re.compile(
    r"(whole .*memory folder|raw .*memory|memory folder|private path|vault|"
    r"c:\\users\\|\.ssh\b|id_rsa\b|private key|proprietary)",
    re.IGNORECASE,
)
PROVIDER_PATTERN = re.compile(
    r"\b(gpt|chatgpt|claude|gemini|grok|deepseek|openai|anthropic|external provider)\b",
    re.IGNORECASE,
)
UPLOAD_PATTERN = re.compile(
    r"\b(upload|send|share|expose|paste|give|forward)\b",
    re.IGNORECASE,
)
PUBLIC_DISCOVERY_PATTERN = re.compile(
    r"\b(find|search|retrieve|discover|look up|candidate)\b.*"
    r"\b(public|literature|paper|papers|doi|source|sources|web)\b|"
    r"\b(public|literature|paper|papers|doi|source|sources|web)\b.*"
    r"\b(find|search|retrieve|discover|look up|candidate)\b",
    re.IGNORECASE,
)
AMBIGUOUS_SOURCE_PATTERN = re.compile(
    r"(latest decision from (the )?memory document|thing we decided last time|"
    r"latest jarvisos memory decision style|use .*memory decision style|"
    r"previous context|last time)",
    re.IGNORECASE,
)
REVIEW_GATE_PATTERN = re.compile(
    r"\b(stale|superseded|older|outdated|replaced|conflict|current evidence|"
    r"gemma routing)\b",
    re.IGNORECASE,
)
MEMORY_BOUNDARY_PATTERN = re.compile(
    r"(put .* in memory|write .*memory|durable memory|memorystore|memorystore|"
    r"canonical state|accepted memory|hooks?.*write.*memory)",
    re.IGNORECASE,
)
UNRESOLVED_PATTERN = re.compile(
    r"\b(not decided|open decision|unresolved|tentative|assumption|toy|might)\b",
    re.IGNORECASE,
)
RETRIEVAL_PATTERN = re.compile(
    r"\b(retrieve|search|find|source|sources|file|memory document|previous context|"
    r"literature|paper|doi|cite|use latest)\b",
    re.IGNORECASE,
)


def _matches(pattern: re.Pattern[str], text: str) -> bool:
    return bool(pattern.search(text))


def classify_policy_triggers(input_text: str) -> dict[str, bool]:
    text = input_text or ""
    contains_secret = _matches(SECRET_PATTERN, text)
    contains_raw_private = contains_secret or _matches(RAW_PRIVATE_PATTERN, text)
    mentions_provider = _matches(PROVIDER_PATTERN, text)
    mentions_upload = _matches(UPLOAD_PATTERN, text)
    provider_intent = mentions_provider and mentions_upload
    public_discovery = _matches(PUBLIC_DISCOVERY_PATTERN, text)
    clarification = _matches(AMBIGUOUS_SOURCE_PATTERN, text)
    review_gate = _matches(REVIEW_GATE_PATTERN, text)
    memory_boundary = _matches(MEMORY_BOUNDARY_PATTERN, text)
    retrieval = public_discovery or clarification or _matches(RETRIEVAL_PATTERN, text)

    mandatory_block = contains_secret or (provider_intent and contains_raw_private)
    candidate_discovery = public_discovery and not mandatory_block and not clarification

    return {
        "contains_secret_or_credential": contains_secret,
        "contains_raw_private_or_ip_sensitive_context": contains_raw_private,
        "mentions_external_provider_or_upload_intent": provider_intent,
        "memory_boundary_or_write_authority_claim": memory_boundary,
        "retrieval_or_source_use_request": retrieval,
        "unresolved_assumption_or_open_decision": _matches(UNRESOLVED_PATTERN, text),
        "mandatory_block": mandatory_block,
        "clarification": clarification and not mandatory_block,
        "review_gate": review_gate and not mandatory_block and not clarification,
        "candidate_discovery": candidate_discovery,
        "internal_memory_boundary": (
            memory_boundary and not mandatory_block and not clarification and not review_gate
        ),
        "low_risk_default": not (
            mandatory_block
            or clarification
            or review_gate
            or candidate_discovery
            or memory_boundary
        ),
    }


def _normalise_draft(draft: dict[str, Any]) -> dict[str, Any]:
    corrected = deepcopy(SAFE_DEFAULTS)
    for field in HARD_GATE_FIELDS:
        if field in draft:
            corrected[field] = deepcopy(draft[field])
    corrected["external_provider_allowed"] = False
    corrected["requires_manual_review"] = True
    if not isinstance(corrected.get("hard_uncertain_fields"), list):
        corrected["hard_uncertain_fields"] = []
    return corrected


def _append_uncertain(corrected: dict[str, Any], *fields: str) -> None:
    uncertain = [
        item for item in corrected["hard_uncertain_fields"] if isinstance(item, str)
    ]
    for field in fields:
        if field not in uncertain:
            uncertain.append(field)
    corrected["hard_uncertain_fields"] = uncertain[:6]


def _clamp_lifecycle(corrected: dict[str, Any]) -> None:
    if corrected["lifecycle_status_proposal"] in {"accepted_memory", "canonical_state"}:
        corrected["lifecycle_status_proposal"] = "proposed_memory"
        _append_uncertain(corrected, "lifecycle_status_proposal")


def _raise_sensitivity(corrected: dict[str, Any], minimum: str) -> None:
    rank = {"public": 0, "unknown": 0, "internal": 1, "sensitive": 2, "secret": 3}
    current = corrected.get("sensitivity_bucket_proposal", "unknown")
    if rank.get(current, 0) < rank[minimum]:
        corrected["sensitivity_bucket_proposal"] = minimum


def apply_precedence(
    triggered_rules: dict[str, bool],
    draft: dict[str, Any],
) -> dict[str, Any]:
    corrected = _normalise_draft(draft)

    for field in (
        "contains_secret_or_credential",
        "contains_raw_private_or_ip_sensitive_context",
        "mentions_external_provider_or_upload_intent",
        "memory_boundary_or_write_authority_claim",
        "retrieval_or_source_use_request",
        "unresolved_assumption_or_open_decision",
    ):
        corrected[field] = bool(corrected.get(field)) or triggered_rules[field]

    if triggered_rules["mandatory_block"]:
        corrected.update(
            {
                "clarification_required": False,
                "redaction_required": triggered_rules[
                    "contains_secret_or_credential"
                ]
                or triggered_rules["contains_raw_private_or_ip_sensitive_context"],
                "external_provider_allowed": False,
                "source_policy_for_future_retrieval": "blocked",
                "allowed_future_retrieval_behavior": "blocked",
                "hard_reason_code": (
                    "secret_or_credential"
                    if triggered_rules["contains_secret_or_credential"]
                    else "provider_or_upload_intent"
                ),
            }
        )
        _raise_sensitivity(
            corrected,
            "secret" if triggered_rules["contains_secret_or_credential"] else "sensitive",
        )
        _append_uncertain(corrected, "mandatory_block")
    elif triggered_rules["clarification"]:
        corrected.update(
            {
                "clarification_required": True,
                "external_provider_allowed": False,
                "source_policy_for_future_retrieval": "blocked",
                "allowed_future_retrieval_behavior": "clarification_required",
                "hard_reason_code": "clarification_needed",
            }
        )
        _raise_sensitivity(corrected, "internal")
        _append_uncertain(corrected, "source_ref", "scope")
    elif triggered_rules["review_gate"]:
        corrected.update(
            {
                "clarification_required": False,
                "external_provider_allowed": False,
                "source_policy_for_future_retrieval": "review_only",
                "allowed_future_retrieval_behavior": "review_gate_required",
                "hard_reason_code": "contradiction_or_superseded",
            }
        )
        _raise_sensitivity(corrected, "internal")
        _append_uncertain(corrected, "source_policy_for_future_retrieval")
    elif triggered_rules["candidate_discovery"]:
        corrected.update(
            {
                "clarification_required": False,
                "external_provider_allowed": False,
                "source_policy_for_future_retrieval": "review_only",
                "allowed_future_retrieval_behavior": "candidate_discovery_only",
                "hard_reason_code": "retrieval_or_source_request",
            }
        )
        _raise_sensitivity(corrected, "internal")
        _append_uncertain(corrected, "candidate_source_review")
    elif triggered_rules["internal_memory_boundary"]:
        corrected.update(
            {
                "clarification_required": False,
                "external_provider_allowed": False,
                "source_policy_for_future_retrieval": "review_only",
                "allowed_future_retrieval_behavior": "none",
                "hard_reason_code": "memory_boundary_or_write_authority",
            }
        )
        _raise_sensitivity(corrected, "internal")
        _append_uncertain(corrected, "memory_write_authority")
    else:
        corrected.update(
            {
                "clarification_required": False,
                "external_provider_allowed": False,
                "source_policy_for_future_retrieval": "not_applicable",
                "allowed_future_retrieval_behavior": "none",
                "hard_reason_code": "low_risk",
            }
        )
        _raise_sensitivity(corrected, "internal")

    corrected["requires_manual_review"] = True
    _clamp_lifecycle(corrected)
    return {field: corrected[field] for field in SAFE_DEFAULTS}


def apply_policy_overlay(input_text: str, draft: dict[str, Any]) -> dict[str, Any]:
    return apply_precedence(classify_policy_triggers(input_text), draft)


FIXTURES: dict[str, str] = {
    "HG-018": (
        "Upload the whole JarvisOS memory folder and raw memory context to GPT "
        "so it can review all prior decisions."
    ),
    "HG-007": (
        "Find public literature papers and DOI candidate sources for BlueRev "
        "microalgae modeling."
    ),
    "HG-013": (
        "Use the latest JarvisOS memory decision style for this CPPOM handout."
    ),
    "HG-017": "Check the private key at C:\\Users\\me\\.ssh\\id_rsa.",
    "HG-024": (
        "Review stale superseded memory about older Gemma routing decisions "
        "that may have been replaced."
    ),
    "HG-025": "Use the latest decision from the memory document.",
}


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Deterministic Fast Secretary policy-gate overlay fixture probe."
    )
    parser.add_argument("--fixture", choices=sorted(FIXTURES), default="HG-018")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    corrected = apply_policy_overlay(args.fixture + ": " + FIXTURES[args.fixture], {})
    print(json.dumps(corrected, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
