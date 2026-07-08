"""Deterministic parser for opt-in JarvisOS proposed memory records."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

MAX_RECORDS = 10
RECORD_VERSION = "jarvis_records_v0"

JARVIS_RECORDS_PROMPT_FRAGMENT = """Optional structured record capture: if your answer includes candidate engineering decisions, assumptions, or parameters that should be reviewed before becoming project memory, emit at most one fenced code block tagged `jarvis-records`. The block must contain JSON with `record_version` equal to `jarvis_records_v0` and a `records` array of at most 10 decision, assumption, or parameter objects. Do not include workspace_id; JarvisOS supplies workspace scope deterministically. Omit the block entirely when there are no record proposals."""

_BLOCK_RE = re.compile(r"```[ \t]*jarvis-records[ \t]*\r?\n(?P<body>.*?)\r?\n```", re.DOTALL)

_ALLOWED_TOP = {"record_version", "records"}
_ALLOWED_BY_KIND = {
    "decision": {"record_kind", "title", "decision_text", "rationale", "linked_run_id", "notes"},
    "assumption": {"record_kind", "statement", "scope", "confidence", "source_ref", "notes"},
    "parameter": {
        "record_kind",
        "name",
        "symbol",
        "value",
        "unit",
        "value_status",
        "value_min",
        "value_max",
        "source_ref",
        "confidence",
        "notes",
    },
}


@dataclass(frozen=True)
class RecordParseResult:
    records: list[dict[str, Any]]
    error: str | None = None


def _strip_workspace_fields(value: Any) -> Any:
    if not isinstance(value, dict):
        return value
    cleaned = {key: item for key, item in value.items() if key != "workspace_id"}
    records = cleaned.get("records")
    if isinstance(records, list):
        cleaned["records"] = [
            {key: item for key, item in record.items() if key != "workspace_id"} if isinstance(record, dict) else record
            for record in records
        ]
    return cleaned


def _validate_payload(payload: Any) -> list[dict[str, Any]]:
    if not isinstance(payload, dict):
        raise ValueError("payload must be an object")
    unknown_top = set(payload) - _ALLOWED_TOP
    if unknown_top:
        raise ValueError(f"unknown top-level keys: {sorted(unknown_top)}")
    if payload.get("record_version") != RECORD_VERSION:
        raise ValueError("record_version must be jarvis_records_v0")
    records = payload.get("records")
    if not isinstance(records, list):
        raise ValueError("records must be an array")
    if len(records) > MAX_RECORDS:
        raise ValueError("records must contain at most 10 items")
    validated: list[dict[str, Any]] = []
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            raise ValueError(f"record #{index} must be an object")
        kind = record.get("record_kind")
        if kind not in _ALLOWED_BY_KIND:
            raise ValueError(f"record #{index} has invalid record_kind")
        unknown = set(record) - _ALLOWED_BY_KIND[kind]
        if unknown:
            raise ValueError(f"record #{index} has unknown keys: {sorted(unknown)}")
        if kind == "decision" and (not str(record.get("title") or "").strip() or not str(record.get("decision_text") or "").strip()):
            raise ValueError(f"record #{index} decision requires title and decision_text")
        if kind == "assumption" and not str(record.get("statement") or "").strip():
            raise ValueError(f"record #{index} assumption requires statement")
        if kind == "parameter":
            if not str(record.get("name") or "").strip():
                raise ValueError(f"record #{index} parameter requires name")
            if "unit" in record and not str(record.get("unit") or "").strip():
                raise ValueError(f"record #{index} parameter unit cannot be blank")
            if record.get("value_status") not in {None, "candidate", "literature", "measured", "validated", "accepted"}:
                raise ValueError(f"record #{index} parameter has invalid value_status")
        validated.append(dict(record))
    return validated


def parse_jarvis_records_block(response_text: str) -> RecordParseResult:
    match = _BLOCK_RE.search(response_text)
    if match is None:
        return RecordParseResult(records=[])
    try:
        raw_payload = json.loads(match.group("body"))
    except json.JSONDecodeError as exc:
        return RecordParseResult(records=[], error=f"records_json_error: {exc.msg}")

    payload = _strip_workspace_fields(raw_payload)
    dropped = 0
    if isinstance(payload, dict) and isinstance(payload.get("records"), list) and len(payload["records"]) > MAX_RECORDS:
        dropped = len(payload["records"]) - MAX_RECORDS
        payload = {**payload, "records": payload["records"][:MAX_RECORDS]}
    try:
        records = _validate_payload(payload)
    except ValueError as exc:
        return RecordParseResult(records=[], error=f"records_schema_error: {exc}")
    error = f"records_truncated: {dropped} dropped" if dropped else None
    return RecordParseResult(records=records, error=error)
