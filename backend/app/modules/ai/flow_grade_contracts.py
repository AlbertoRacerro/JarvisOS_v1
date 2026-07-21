from __future__ import annotations

import json
import re
import sqlite3
from typing import Literal

Grade = Literal["useful", "partly", "rework", "failed"]
GradeSource = Literal["operator_ui", "operator_api"]

TERMINAL_FLOW_STATES = frozenset(
    {"complete", "partial_terminal", "failed_terminal", "cancelled_terminal"}
)
FINAL_ATTEMPT_STATUSES = frozenset(
    {
        "config_error",
        "provider_error",
        "route_unavailable",
        "success",
        "validation_error",
    }
)
GRADES = frozenset({"useful", "partly", "rework", "failed"})
SOURCES = frozenset({"operator_ui", "operator_api"})
REASON_CODES = frozenset(
    {
        "correct_complete",
        "minor_edits",
        "incomplete_missing_evidence",
        "wrong_reasoning_facts",
        "hallucination",
        "wrong_tool_route",
        "too_verbose_brief",
        "provider_tool_failure",
        "policy_block",
        "other",
    }
)
ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")
DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
ACTOR = "local_operator"
SUBJECT_SCHEMA_VERSION = "grade-subject-v0"
GRADE_SCHEMA_VERSION = "grade-v0"
GRADE_POLICY_VERSION = "grade-policy-v0"


class FlowGradeError(ValueError):
    pass


class FlowGradeNotFoundError(FlowGradeError):
    pass


class FlowGradeConflictError(FlowGradeError):
    pass


class FlowGradeContractError(FlowGradeError):
    pass


def safe_id(value: object, label: str) -> str:
    if not isinstance(value, str) or ID_RE.fullmatch(value) is None:
        raise FlowGradeContractError(f"{label} is invalid")
    return value


def required_digest(value: object, label: str) -> str:
    if not isinstance(value, str) or DIGEST_RE.fullmatch(value) is None:
        raise FlowGradeConflictError(f"{label} is not finalized")
    return value


def optional_digest(value: object, label: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or DIGEST_RE.fullmatch(value) is None:
        raise FlowGradeConflictError(f"{label} is invalid")
    return value


def json_object(value: object, label: str) -> dict[str, object]:
    try:
        decoded = json.loads(str(value))
    except (TypeError, json.JSONDecodeError) as exc:
        raise FlowGradeConflictError(f"{label} is invalid") from exc
    if not isinstance(decoded, dict):
        raise FlowGradeConflictError(f"{label} must be an object")
    return decoded


def json_list(value: object, label: str) -> list[object]:
    try:
        decoded = json.loads(str(value))
    except (TypeError, json.JSONDecodeError) as exc:
        raise FlowGradeConflictError(f"{label} is invalid") from exc
    if not isinstance(decoded, list):
        raise FlowGradeConflictError(f"{label} must be a list")
    return decoded


def canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def normalize_reason_codes(values: list[str] | tuple[str, ...]) -> list[str]:
    if len(values) > 5:
        raise FlowGradeContractError("at most five reason codes are allowed")
    result: list[str] = []
    for value in values:
        if value not in REASON_CODES:
            raise FlowGradeContractError(f"unsupported reason code: {value}")
        if value not in result:
            result.append(value)
    return result


def normalize_note(value: str | None) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise FlowGradeContractError("note must be text")
    result = value.strip()
    if not result:
        return None
    if len(result) > 1000:
        raise FlowGradeContractError("note must contain at most 1000 characters")
    if "\x00" in result:
        raise FlowGradeContractError("note contains an invalid character")
    return result


def decode_subject(row: sqlite3.Row) -> dict[str, object]:
    return {
        "id": str(row["id"]),
        "flow_id": str(row["flow_id"]),
        "terminal_attempt_id": row["terminal_attempt_id"],
        "subject_version": int(row["subject_version"]),
        "flow_outcome_digest": str(row["flow_outcome_digest"]),
        "final_accounting_digest": str(row["final_accounting_digest"]),
        "final_output_digest": row["final_output_digest"],
        "valid": bool(row["valid"]),
        "invalidated_at": row["invalidated_at"],
        "created_at": str(row["created_at"]),
    }


def decode_event(row: sqlite3.Row) -> dict[str, object]:
    return {
        "id": str(row["id"]),
        "flow_id": str(row["flow_id"]),
        "subject_id": str(row["subject_id"]),
        "subject_version": int(row["subject_version"]),
        "flow_outcome_digest": str(row["flow_outcome_digest"]),
        "event_index": int(row["event_index"]),
        "action": str(row["action"]),
        "grade": row["grade"],
        "reason_codes": json_list(row["reason_codes_json"], "reason_codes_json"),
        "note": row["note_text"],
        "actor": str(row["actor"]),
        "source": str(row["source"]),
        "supersedes_event_id": row["supersedes_event_id"],
        "idempotency_key": str(row["idempotency_key"]),
        "created_at": str(row["created_at"]),
        "schema_version": str(row["schema_version"]),
        "policy_version": str(row["policy_version"]),
        "replayed": False,
    }
