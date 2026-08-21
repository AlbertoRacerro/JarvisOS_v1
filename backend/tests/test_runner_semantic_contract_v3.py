from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from app.modules.runner.input_contracts import (
    ModelInputContractV3,
    canonicalize_input_contract,
    parse_stored_input_contract,
)
from app.modules.runner.safety import RunnerSafetyError


_CONTRACT_PATH = (
    Path(__file__).parents[1]
    / "app"
    / "modules"
    / "runner"
    / "examples"
    / "bluerev_geometry_hydraulics_semantic_v0.contract.json"
)


def _payload() -> dict[str, object]:
    return json.loads(_CONTRACT_PATH.read_text(encoding="utf-8"))


def test_schema_v3_semantic_companion_round_trips_canonically() -> None:
    encoded, digest, normalized = canonicalize_input_contract(_payload())

    contract, parsed_digest = parse_stored_input_contract(encoded, digest)

    assert isinstance(contract, ModelInputContractV3)
    assert parsed_digest == digest
    assert normalized["semantic_context"]["applicable_part_kinds"] == ["tube_run"]
    object_variables = {
        variable.name
        for variable in contract.variables
        if variable.applicable_part_kinds
    }
    assert object_variables == {
        "tube_length",
        "tube_inner_diameter",
        "tube_outer_diameter",
    }


@pytest.mark.parametrize(
    "mutate",
    [
        lambda payload: payload["semantic_context"].update(
            {"applicable_part_kinds": ["tube_run", "tube_run"]}
        ),
        lambda payload: payload["variables"][0].update(
            {"applicable_part_kinds": ["not_implementation_applicable"]}
        ),
        lambda payload: payload["semantic_context"].update({"model_family_key": "Not Stable"}),
        lambda payload: payload["variables"][0].update({"property_group": " Geometry"}),
        lambda payload: payload["variables"][0].update({"unknown_semantic_field": "nope"}),
    ],
)
def test_schema_v3_semantic_metadata_fails_closed(mutate) -> None:
    payload = copy.deepcopy(_payload())
    mutate(payload)

    with pytest.raises(RunnerSafetyError) as exc_info:
        canonicalize_input_contract(payload)

    assert exc_info.value.code == "runner_input_contract_invalid"
