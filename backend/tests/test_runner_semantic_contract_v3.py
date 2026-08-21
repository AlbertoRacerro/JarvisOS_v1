from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from app.modules.runner import service as runner_service
from app.modules.runner.guarded_service import (
    BUNDLED_BLUEREV_PROCESS0_SEMANTIC_LABEL,
    _bluerev_process0_semantic_contract_path,
    _is_exact_bundled,
)
from app.modules.runner.input_contracts import (
    ModelInputContractV3,
    canonicalize_input_contract,
    parse_stored_input_contract,
)
from app.modules.runner.safety import RunnerSafetyError, sha256_file

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


def _assert_invalid(payload: dict[str, object]) -> None:
    with pytest.raises(RunnerSafetyError) as exc_info:
        canonicalize_input_contract(payload)
    assert exc_info.value.code == "runner_input_contract_invalid"


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


def test_schema_v3_semantic_companion_has_exact_bundled_admission_only() -> None:
    script_path = runner_service._bluerev_process0_script_path()
    script_sha = sha256_file(script_path)
    contract = json.loads(_bluerev_process0_semantic_contract_path().read_text(encoding="utf-8"))
    _, contract_sha, _ = canonicalize_input_contract(contract)
    exact = {
        "script_path": str(script_path),
        "script_sha256": script_sha,
        "implementation_kind": runner_service.CALC_V0_IMPLEMENTATION_KIND,
        "version_label": BUNDLED_BLUEREV_PROCESS0_SEMANTIC_LABEL,
        "input_contract_sha256": contract_sha,
    }

    assert _is_exact_bundled(exact) is True

    wrong_label = dict(exact, version_label=runner_service.BUNDLED_BLUEREV_PROCESS0_LABEL)
    assert _is_exact_bundled(wrong_label) is False

    legacy_contract = json.loads(
        runner_service._bluerev_process0_contract_path().read_text(encoding="utf-8")
    )
    _, legacy_contract_sha, _ = canonicalize_input_contract(legacy_contract)
    wrong_contract = dict(exact, input_contract_sha256=legacy_contract_sha)
    assert _is_exact_bundled(wrong_contract) is False


@pytest.mark.parametrize(
    "machine_identifier",
    [
        "A",
        "A" + "b" * 63,
        "Upper_Case_9",
    ],
)
def test_schema_v3_machine_identifier_accepts_exact_grammar(machine_identifier: str) -> None:
    payload = copy.deepcopy(_payload())
    payload["semantic_context"]["model_family_key"] = machine_identifier

    _, _, normalized = canonicalize_input_contract(payload)

    assert normalized["semantic_context"]["model_family_key"] == machine_identifier


@pytest.mark.parametrize(
    "machine_identifier",
    [
        "A" + "b" * 64,
        "has-hyphen",
        "has.dot",
        "has/slash",
        "has:colon",
        "has*wildcard",
        " space",
        "éngineering",
        "A\nB",
    ],
)
def test_schema_v3_machine_identifier_rejects_outside_exact_grammar(
    machine_identifier: str,
) -> None:
    payload = copy.deepcopy(_payload())
    payload["semantic_context"]["model_family_key"] = machine_identifier

    _assert_invalid(payload)


def test_schema_v3_human_label_accepts_nfc_engineering_text_through_120_code_points() -> None:
    payload = copy.deepcopy(_payload())
    label = "Ω" * 119 + "!"
    payload["semantic_context"]["model_family_label"] = label

    _, _, normalized = canonicalize_input_contract(payload)

    assert normalized["semantic_context"]["model_family_label"] == label


@pytest.mark.parametrize(
    "label",
    [
        "Ω" * 121,
        " leading",
        "trailing ",
        "Cafe\u0301",
        "line\nbreak",
        "tab\tbreak",
        "control\x00value",
        "format\u200bvalue",
    ],
)
def test_schema_v3_human_labels_fail_closed_on_exact_contract(label: str) -> None:
    payload = copy.deepcopy(_payload())
    payload["semantic_context"]["model_option_label"] = label

    _assert_invalid(payload)


def test_schema_v3_property_group_uses_same_human_label_contract() -> None:
    payload = copy.deepcopy(_payload())
    payload["variables"][0]["property_group"] = "Geometry\u200b"

    _assert_invalid(payload)


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

    _assert_invalid(payload)
