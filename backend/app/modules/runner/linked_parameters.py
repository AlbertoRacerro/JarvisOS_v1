from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from math import isfinite
from typing import Any

from app.modules.runner.input_contracts import parse_stored_input_contract
from app.modules.runner.safety import RunnerSafetyError

LINKED_PARAMETER_UNUSABLE_CODE = "runner_linked_parameter_unusable"
LINKED_PARAMETER_UNUSABLE_MESSAGE = "A linked Parameter is no longer usable for this queued run."


@dataclass(frozen=True)
class LinkedParameterUsability:
    usable: bool
    parameter: dict[str, object] | None
    reason: str | None


def contract_requires_canonical_linked_parameters(
    contract_payload: str | None,
    contract_sha256: str | None,
) -> bool:
    """Return whether stored contract authority makes source_parameter_id a canonical FK.

    Historical no-contract and schema-v1 runner payloads permit provenance-like source
    tokens. 058c freshness enforcement therefore applies only to authoritative schema-v2/v3
    contracts, never by inspecting payload shape or guessing identifier semantics. Partial or
    malformed stored-contract evidence remains fail-closed through the canonical parser.
    """

    if contract_payload is None and contract_sha256 is None:
        return False
    contract, _ = parse_stored_input_contract(contract_payload, contract_sha256)
    return contract.schema_version in {2, 3}


def inspect_linked_parameter_usability(
    connection: sqlite3.Connection,
    workspace_id: str,
    parameter_id: str,
) -> LinkedParameterUsability:
    """Return fail-closed 058c usability for one canonical linked Parameter.

    This consumes existing Parameter lifecycle plus the canonical 051 freshness
    overlay. It deliberately does not follow replacement links or create a new
    freshness authority.
    """

    row = connection.execute(
        "SELECT id, workspace_id, value, unit, status FROM parameters WHERE id = ?",
        (parameter_id,),
    ).fetchone()
    if row is None:
        return LinkedParameterUsability(False, None, "missing")

    parameter = dict(row)
    if str(parameter.get("workspace_id")) != workspace_id:
        return LinkedParameterUsability(False, None, "inaccessible")
    if str(parameter.get("status")) == "superseded":
        return LinkedParameterUsability(False, None, "superseded")

    value = _finite_number(parameter.get("value"))
    unit = parameter.get("unit")
    if value is None:
        return LinkedParameterUsability(False, None, "invalid_value")
    if not isinstance(unit, str) or not unit.strip():
        return LinkedParameterUsability(False, None, "invalid_unit")

    record_ref = f"parameter:{parameter_id}"
    stale = connection.execute(
        """
        SELECT 1
        FROM freshness_marks
        WHERE workspace_id = ? AND record_ref = ?
        LIMIT 1
        """,
        (workspace_id, record_ref),
    ).fetchone()
    if stale is not None:
        return LinkedParameterUsability(False, None, "stale")

    return LinkedParameterUsability(True, parameter, None)


def load_usable_linked_parameter(
    connection: sqlite3.Connection,
    workspace_id: str,
    parameter_id: str,
) -> dict[str, object] | None:
    result = inspect_linked_parameter_usability(connection, workspace_id, parameter_id)
    return result.parameter if result.usable else None


def require_linked_parameters_usable(
    connection: sqlite3.Connection,
    workspace_id: str,
    normalized_input_payload: str | dict[str, Any],
) -> None:
    for parameter_id in linked_parameter_ids(normalized_input_payload):
        if not inspect_linked_parameter_usability(connection, workspace_id, parameter_id).usable:
            raise RunnerSafetyError(
                LINKED_PARAMETER_UNUSABLE_CODE,
                LINKED_PARAMETER_UNUSABLE_MESSAGE,
            )


def linked_parameter_ids(normalized_input_payload: str | dict[str, Any]) -> tuple[str, ...]:
    if isinstance(normalized_input_payload, str):
        try:
            payload = json.loads(normalized_input_payload)
        except json.JSONDecodeError as exc:
            raise RunnerSafetyError("runner_input_invalid", "Stored runner input payload is invalid JSON.") from exc
    else:
        payload = normalized_input_payload

    if not isinstance(payload, dict):
        raise RunnerSafetyError("runner_input_invalid", "Stored runner input payload must be an object.")

    ids: set[str] = set()
    for item in payload.values():
        if not isinstance(item, dict):
            continue
        source_parameter_id = item.get("source_parameter_id")
        if source_parameter_id is None:
            continue
        if not isinstance(source_parameter_id, str) or not source_parameter_id.strip():
            raise RunnerSafetyError("runner_input_invalid", "Stored linked Parameter identity is invalid.")
        ids.add(source_parameter_id)
    return tuple(sorted(ids))


def _finite_number(value: object) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return number if isfinite(number) else None
