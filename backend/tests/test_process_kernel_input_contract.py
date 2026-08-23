from __future__ import annotations

from app.modules.runner.input_contracts import canonicalize_input_contract
from app.modules.runner.process_kernel_047 import (
    build_binding_preview_v2,
    expected_contract,
)


_COMPLETE_BINDINGS = {
    "tube_length": {"value": 12.0, "unit": "m"},
    "tube_inner_diameter": {"value": 80.0, "unit": "mm"},
    "tube_outer_diameter": {"value": 90.0, "unit": "mm"},
    "reservoir_liquid_volume": {"value": 100.0, "unit": "L"},
    "target_liquid_velocity": {"value": 0.5, "unit": "m/s"},
    "liquid_density": {"value": 998.0, "unit": "kg/m3"},
    "dynamic_viscosity": {"value": 0.001, "unit": "Pa*s"},
    "minor_loss_coefficient": {"value": 2.0, "unit": "1"},
    "pump_efficiency": {"value": 0.8, "unit": "1"},
}


def _contract_bytes() -> tuple[str, str]:
    payload, digest, _ = canonicalize_input_contract(expected_contract())
    return payload, digest


def _preview(bindings: dict[str, object], *, parameter: dict[str, object] | None = None):
    payload, digest = _contract_bytes()
    return build_binding_preview_v2(
        model_version_id="process-kernel-test",
        contract_payload=payload,
        contract_sha256=digest,
        bindings=bindings,
        load_parameter=lambda parameter_id: parameter if parameter_id == "parameter-1" else None,
    )


def test_process_kernel_contract_exposes_nine_required_dof_and_becomes_ready() -> None:
    missing = _preview({})

    assert missing.state == "incomplete"
    assert missing.structural_input_dof == 9
    assert missing.bound_input_dof == 0
    assert missing.unresolved_input_dof == 9
    assert missing.normalized_input_set is None

    ready = _preview(dict(_COMPLETE_BINDINGS))

    assert ready.state == "ready"
    assert ready.structural_input_dof == 9
    assert ready.bound_input_dof == 9
    assert ready.unresolved_input_dof == 0
    assert ready.invalid_binding_count == 0
    assert ready.normalized_input_set is not None


def test_linked_parameter_preview_captures_revision_and_replays_unchanged_source() -> None:
    parameter = {
        "value": "12.0",
        "unit": "m",
        "updated_at": "2026-08-23T00:00:00+00:00",
    }
    bindings = dict(_COMPLETE_BINDINGS)
    bindings["tube_length"] = {
        "value": 12.0,
        "unit": "m",
        "source_parameter_id": "parameter-1",
    }

    first = _preview(bindings, parameter=parameter)

    assert first.state == "ready"
    assert first.normalized_input_set is not None
    assert first.normalized_input_set["tube_length"] == {
        "value": 12.0,
        "unit": "m",
        "source_parameter_id": "parameter-1",
        "source_parameter_updated_at": "2026-08-23T00:00:00+00:00",
    }

    replay = _preview(first.normalized_input_set, parameter=parameter)

    assert replay.state == "ready"
    assert replay.invalid_binding_count == 0
    assert replay.normalized_input_set == first.normalized_input_set


def test_linked_parameter_preview_fails_closed_when_canonical_revision_changes() -> None:
    parameter = {
        "value": "12.0",
        "unit": "m",
        "updated_at": "2026-08-23T00:00:00+00:00",
    }
    bindings = dict(_COMPLETE_BINDINGS)
    bindings["tube_length"] = {
        "value": 12.0,
        "unit": "m",
        "source_parameter_id": "parameter-1",
    }
    first = _preview(bindings, parameter=parameter)
    assert first.state == "ready"
    assert first.normalized_input_set is not None

    changed_parameter = {
        "value": "12.0",
        "unit": "m",
        "updated_at": "2026-08-23T01:00:00+00:00",
    }
    stale = _preview(first.normalized_input_set, parameter=changed_parameter)

    assert stale.state == "invalid"
    assert stale.invalid_binding_count == 1
    tube_length = next(variable for variable in stale.variables if variable.name == "tube_length")
    assert tube_length.errors == ["binding_parameter_revision_mismatch"]
    assert stale.normalized_input_set is None
