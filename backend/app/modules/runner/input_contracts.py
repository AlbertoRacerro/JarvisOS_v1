from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Callable
from math import isfinite
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

from app.modules.runner.models import (
    BindingPreviewResponse,
    BindingVariablePreview,
)
from app.modules.runner.safety import RunnerSafetyError, canonical_json

_VARIABLE_NAME = re.compile(r"^[A-Za-z][A-Za-z0-9_]{0,63}$")
_CATEGORIES = Literal["design", "operating", "property", "model_parameter", "equipment"]


class NumericDomain(BaseModel):
    model_config = ConfigDict(extra="forbid")

    min: float | None = None
    max: float | None = None
    exclusive_min: float | None = None
    exclusive_max: float | None = None

    @field_validator("min", "max", "exclusive_min", "exclusive_max", mode="before")
    @classmethod
    def finite_number_or_none(cls, value: object) -> object:
        if value is None:
            return value
        if isinstance(value, bool) or not isinstance(value, int | float):
            raise ValueError("domain bounds must be numeric")
        if not isfinite(float(value)):
            raise ValueError("domain bounds must be finite")
        return float(value)

    @model_validator(mode="after")
    def validate_bounds(self) -> NumericDomain:
        if self.min is not None and self.exclusive_min is not None:
            raise ValueError("lower bound cannot be both inclusive and exclusive")
        if self.max is not None and self.exclusive_max is not None:
            raise ValueError("upper bound cannot be both inclusive and exclusive")
        lower = self.exclusive_min if self.exclusive_min is not None else self.min
        upper = self.exclusive_max if self.exclusive_max is not None else self.max
        if lower is not None and upper is not None and lower >= upper:
            raise ValueError("lower bound must be less than upper bound")
        return self


class InputVariable(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=64)
    label: str = Field(min_length=1, max_length=120)
    unit: str = Field(min_length=1, max_length=32)
    required: bool
    category: _CATEGORIES
    description: str = Field(min_length=1, max_length=500)
    domain: NumericDomain | None = None

    @field_validator("name")
    @classmethod
    def valid_name(cls, value: str) -> str:
        if not _VARIABLE_NAME.fullmatch(value):
            raise ValueError("variable name must be a stable identifier")
        return value

    @field_validator("label", "unit", "description")
    @classmethod
    def no_edge_whitespace(cls, value: str) -> str:
        if value != value.strip():
            raise ValueError("text fields cannot have leading or trailing whitespace")
        return value


class ModelInputContract(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1]
    evaluation_mode: Literal["forward"]
    variables: list[InputVariable] = Field(min_length=1, max_length=64)

    @model_validator(mode="after")
    def unique_names(self) -> ModelInputContract:
        names = [variable.name for variable in self.variables]
        if len(names) != len(set(names)):
            raise ValueError("variable names must be unique")
        return self


ParameterLoader = Callable[[str], dict[str, object] | None]


def canonicalize_input_contract(payload: dict[str, Any]) -> tuple[str, str, dict[str, Any]]:
    try:
        contract = ModelInputContract.model_validate(payload)
    except ValidationError as exc:
        raise RunnerSafetyError(
            "runner_input_contract_invalid",
            "Model input contract is invalid.",
        ) from exc
    normalized = contract.model_dump(mode="json", exclude_none=True)
    encoded = canonical_json(normalized)
    digest = hashlib.sha256(encoded.encode("utf-8")).hexdigest()
    return encoded, digest, normalized


def parse_stored_input_contract(
    payload: str | None,
    expected_sha256: str | None,
) -> tuple[ModelInputContract, str]:
    if not payload or not expected_sha256:
        raise RunnerSafetyError(
            "runner_input_contract_missing",
            "Model implementation has no input contract.",
        )
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    if digest != expected_sha256:
        raise RunnerSafetyError(
            "runner_input_contract_hash_mismatch",
            "Model input contract digest does not match stored payload.",
        )
    try:
        raw = json.loads(payload)
        contract = ModelInputContract.model_validate(raw)
    except (json.JSONDecodeError, ValidationError) as exc:
        raise RunnerSafetyError(
            "runner_input_contract_invalid",
            "Stored model input contract is invalid.",
        ) from exc
    if canonical_json(contract.model_dump(mode="json", exclude_none=True)) != payload:
        raise RunnerSafetyError(
            "runner_input_contract_not_canonical",
            "Stored model input contract is not canonical.",
        )
    return contract, digest


def build_binding_preview(
    *,
    model_version_id: str,
    contract_payload: str | None,
    contract_sha256: str | None,
    bindings: dict[str, Any],
    load_parameter: ParameterLoader,
) -> BindingPreviewResponse:
    contract, digest = parse_stored_input_contract(contract_payload, contract_sha256)
    contract_names = {variable.name for variable in contract.variables}
    global_errors = [f"binding_unknown_variable:{name}" for name in sorted(set(bindings) - contract_names)]
    invalid_count = len(global_errors)
    bound_required = 0
    normalized: dict[str, dict[str, object]] = {}
    variable_results: list[BindingVariablePreview] = []

    for variable in contract.variables:
        item = bindings.get(variable.name)
        if item is None:
            variable_results.append(
                BindingVariablePreview(
                    name=variable.name,
                    label=variable.label,
                    unit=variable.unit,
                    category=variable.category,
                    description=variable.description,
                    required=variable.required,
                    binding_state="missing",
                )
            )
            continue

        errors: list[str] = []
        value: float | None = None
        source_parameter_id: str | None = None
        if not isinstance(item, dict):
            errors.append("binding_object_invalid")
        else:
            allowed = {"value", "unit", "source_parameter_id"}
            if set(item) - allowed or "value" not in item or "unit" not in item:
                errors.append("binding_object_invalid")
            raw_value = item.get("value")
            if isinstance(raw_value, bool) or not isinstance(raw_value, int | float):
                errors.append("binding_value_invalid")
            elif not isfinite(float(raw_value)):
                errors.append("binding_value_invalid")
            else:
                value = float(raw_value)
            if item.get("unit") != variable.unit:
                errors.append("binding_unit_invalid")
            raw_source = item.get("source_parameter_id")
            if raw_source is not None:
                if not isinstance(raw_source, str) or not raw_source.strip():
                    errors.append("binding_parameter_reference_invalid")
                else:
                    source_parameter_id = raw_source

        if value is not None and not errors:
            errors.extend(_domain_errors(variable.domain, value))

        if source_parameter_id is not None and not errors:
            parameter = load_parameter(source_parameter_id)
            if parameter is None:
                errors.append("binding_parameter_not_found")
            else:
                parameter_value = _finite_parameter_value(parameter.get("value"))
                if parameter_value is None:
                    errors.append("binding_parameter_value_invalid")
                if parameter.get("unit") != variable.unit:
                    errors.append("binding_parameter_unit_mismatch")
                if parameter_value is not None and value is not None and parameter_value != value:
                    errors.append("binding_parameter_value_mismatch")

        if errors:
            invalid_count += 1
            state = "invalid"
        else:
            state = "parameter" if source_parameter_id else "manual"
            normalized_item: dict[str, object] = {
                "value": value,
                "unit": variable.unit,
            }
            if source_parameter_id:
                normalized_item["source_parameter_id"] = source_parameter_id
            normalized[variable.name] = normalized_item
            if variable.required:
                bound_required += 1

        variable_results.append(
            BindingVariablePreview(
                name=variable.name,
                label=variable.label,
                unit=variable.unit,
                category=variable.category,
                description=variable.description,
                required=variable.required,
                binding_state=state,
                value=value,
                source_parameter_id=source_parameter_id,
                errors=errors,
            )
        )

    structural = sum(1 for variable in contract.variables if variable.required)
    unresolved = structural - bound_required
    if invalid_count:
        preview_state = "invalid"
    elif unresolved:
        preview_state = "incomplete"
    else:
        preview_state = "ready"

    return BindingPreviewResponse(
        model_version_id=model_version_id,
        contract_sha256=digest,
        evaluation_mode="forward",
        structural_input_dof=structural,
        bound_input_dof=bound_required,
        unresolved_input_dof=unresolved,
        invalid_binding_count=invalid_count,
        state=preview_state,
        variables=variable_results,
        errors=global_errors,
        normalized_input_set=normalized if preview_state == "ready" else None,
    )


def _finite_parameter_value(value: object) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return number if isfinite(number) else None


def _domain_errors(domain: NumericDomain | None, value: float) -> list[str]:
    if domain is None:
        return []
    if domain.min is not None and value < domain.min:
        return ["binding_domain_violation"]
    if domain.max is not None and value > domain.max:
        return ["binding_domain_violation"]
    if domain.exclusive_min is not None and value <= domain.exclusive_min:
        return ["binding_domain_violation"]
    if domain.exclusive_max is not None and value >= domain.exclusive_max:
        return ["binding_domain_violation"]
    return []
