import sqlite3

import pytest

from app.modules.runner.linked_parameters import (
    LINKED_PARAMETER_UNUSABLE_CODE,
    LINKED_PARAMETER_UNUSABLE_MESSAGE,
    inspect_linked_parameter_usability,
    linked_parameter_ids,
    load_usable_linked_parameter,
    require_linked_parameters_usable,
)
from app.modules.runner.safety import RunnerSafetyError


def _connection() -> sqlite3.Connection:
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    connection.executescript(
        """
        CREATE TABLE parameters (
            id TEXT PRIMARY KEY,
            workspace_id TEXT NOT NULL,
            value TEXT,
            unit TEXT NOT NULL,
            status TEXT NOT NULL
        );
        CREATE TABLE freshness_marks (
            id TEXT PRIMARY KEY,
            workspace_id TEXT NOT NULL,
            record_ref TEXT NOT NULL
        );
        """
    )
    return connection


def _insert_parameter(
    connection: sqlite3.Connection,
    *,
    parameter_id: str = "parameter-1",
    workspace_id: str = "workspace-1",
    value: object = "12.5",
    unit: str = "m",
    status: str = "accepted",
) -> None:
    connection.execute(
        "INSERT INTO parameters (id, workspace_id, value, unit, status) VALUES (?, ?, ?, ?, ?)",
        (parameter_id, workspace_id, value, unit, status),
    )


def test_linked_parameter_usability_accepts_fresh_same_workspace_source() -> None:
    connection = _connection()
    _insert_parameter(connection)

    result = inspect_linked_parameter_usability(connection, "workspace-1", "parameter-1")

    assert result.usable is True
    assert result.reason is None
    assert result.parameter is not None
    assert result.parameter["id"] == "parameter-1"
    assert load_usable_linked_parameter(connection, "workspace-1", "parameter-1") is not None


@pytest.mark.parametrize(
    ("mutation", "reason"),
    [
        ("superseded", "superseded"),
        ("stale", "stale"),
        ("invalid_value", "invalid_value"),
        ("inaccessible", "inaccessible"),
    ],
)
def test_linked_parameter_usability_fails_closed_for_canonical_unusable_states(
    mutation: str,
    reason: str,
) -> None:
    connection = _connection()
    if mutation == "inaccessible":
        _insert_parameter(connection, workspace_id="workspace-2")
    elif mutation == "invalid_value":
        _insert_parameter(connection, value="nan")
    elif mutation == "superseded":
        _insert_parameter(connection, status="superseded")
    else:
        _insert_parameter(connection)
        connection.execute(
            "INSERT INTO freshness_marks (id, workspace_id, record_ref) VALUES (?, ?, ?)",
            ("mark-1", "workspace-1", "parameter:parameter-1"),
        )

    result = inspect_linked_parameter_usability(connection, "workspace-1", "parameter-1")

    assert result.usable is False
    assert result.parameter is None
    assert result.reason == reason


def test_linked_parameter_usability_treats_missing_source_as_unusable() -> None:
    connection = _connection()

    result = inspect_linked_parameter_usability(connection, "workspace-1", "missing")

    assert result.usable is False
    assert result.parameter is None
    assert result.reason == "missing"


def test_linked_parameter_ids_are_deterministic_and_deduplicated() -> None:
    payload = {
        "tube_length": {"value": 12.0, "unit": "m", "source_parameter_id": "parameter-b"},
        "tube_inner_diameter": {"value": 80.0, "unit": "mm", "source_parameter_id": "parameter-a"},
        "tube_outer_diameter": {"value": 90.0, "unit": "mm", "source_parameter_id": "parameter-b"},
        "pump_efficiency": {"value": 0.8, "unit": "fraction"},
    }

    assert linked_parameter_ids(payload) == ("parameter-a", "parameter-b")


def test_require_linked_parameters_usable_raises_exact_stale_claim_contract() -> None:
    connection = _connection()
    _insert_parameter(connection, status="superseded")
    payload = {"tube_length": {"value": 12.5, "unit": "m", "source_parameter_id": "parameter-1"}}

    with pytest.raises(RunnerSafetyError) as caught:
        require_linked_parameters_usable(connection, "workspace-1", payload)

    assert caught.value.code == LINKED_PARAMETER_UNUSABLE_CODE
    assert caught.value.message == LINKED_PARAMETER_UNUSABLE_MESSAGE
