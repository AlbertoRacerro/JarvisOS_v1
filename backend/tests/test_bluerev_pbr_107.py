"""107 PBR-EVALUATOR-1: dynamic day/night PBR evaluator over the 104 stack.

The parameter set is an explicitly labelled synthetic fixture (not N. gaditana
biology); these tests check conservation, limiting cases, provenance
enforcement and the single time/state owner, not biological validity.
"""

from __future__ import annotations

import json
import math
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from app.modules.bluerev.pbr_evaluator import EVALUATOR_ID, PbrDayNightEvaluator
from app.modules.engineering.evaluator_contracts import (
    EvaluationFailure,
    EvaluationRequest,
    EvaluationResult,
    validate_evaluation_result,
)
from app.modules.process_stack.correlations import PipePressureDropEvaluator

FIXTURE = json.loads((Path(__file__).resolve().parents[2] / "scripts" / "qualification" / "107"
                      / "synthetic-parameters.json").read_text(encoding="utf-8"))
MODEL = {"authority_owner": "bluerev", "object_type": "dynamic_model", "object_id": "pbr-loop-a",
         "workspace_id": "bluerev", "revision": "1"}


def _request(*, design: dict[str, Any] | None = None, sourced: dict[str, Any] | None = None,
             unsourced: tuple[str, ...] = (), subject: dict[str, str] = MODEL,
             backend_options: dict[str, str] | None = None) -> EvaluationRequest:
    now = datetime.now(UTC)
    inputs = []
    coefficients = dict(FIXTURE["coefficients"])
    if backend_options and backend_options.get("nitrogen_response") == "replete":
        coefficients.pop("nitrogen_half_saturation")
    for name, (value, unit) in {**coefficients, **(sourced or {})}.items():
        quantity: dict[str, Any] = {"value": value, "unit": unit}
        if name not in unsourced:
            quantity["basis_ref"] = FIXTURE["basis_ref"]
        inputs.append({"name": name, "value": quantity})
    inputs += [{"name": name, "value": {"value": value, "unit": unit}}
               for name, (value, unit) in {**FIXTURE["design"], **(design or {})}.items()]
    return EvaluationRequest.model_validate({
        "request_ref": {"authority_owner": "bluerev", "object_type": "evaluation_request", "object_id": "pbr-run-1",
                        "workspace_id": "bluerev", "revision": "1"},
        "evaluator_id": EVALUATOR_ID, "subject_ref": subject, "inputs": inputs,
        "backend_options": backend_options or {},
        "requested_at": now - timedelta(seconds=1), "deadline_at": now + timedelta(minutes=5),
    })


def _run(request: EvaluationRequest) -> EvaluationResult:
    result = PbrDayNightEvaluator().evaluate(request)
    validate_evaluation_result(request, result)
    return result


def _out(result: EvaluationResult) -> dict[str, float]:
    assert result.status == "succeeded", result.failure
    return {item.name: item.value.value for item in result.outputs}


def test_periodic_day_night_run_conserves_nitrogen_and_reports_units() -> None:
    result = _run(_request())
    out = _out(result)
    assert result.fidelity == "reduced_order"
    assert result.validity is not None and result.validity.qualification_status == "unqualified"
    assert result.qualification_record_ref is not None
    assert result.qualification_record_ref.object_id == "scripts/qualification/107/pbr_day_night.v2.ledger.json"
    assert result.numerical.converged is True and (result.numerical.iterations or 0) > 0
    units = {item.name: item.value.unit for item in result.outputs}
    assert units["volumetric_productivity"] == "kg/(m**3*d)" and units["pumping_power"] == "W"
    total_nitrogen = 0.05 + 0.07 * 0.5
    assert out["nitrogen_balance_error"] < 1e-7 * total_nitrogen * 10
    assert out["oxygen_balance_error"] < 1e-7
    assert out["harvested_biomass"] > 0 and out["volumetric_productivity"] > 0
    assert out["max_oxygen_saturation_ratio"] > 1.0  # daytime photosynthesis supersaturates
    assert _out(_run(_request())) == out  # deterministic reproduction


def test_fixture_units_match_declared_coefficient_and_design_units() -> None:
    from app.modules.bluerev.pbr_evaluator import DESIGN, SOURCED_ALWAYS, SOURCED_BY_OPTION

    coefficients = {**SOURCED_ALWAYS, **SOURCED_BY_OPTION[("light_response", "haldane")],
                    **SOURCED_BY_OPTION[("temperature_response", "cardinal")],
                    **SOURCED_BY_OPTION[("nitrogen_response", "monod")]}
    assert {name: unit for name, (_, unit) in FIXTURE["coefficients"].items()} == coefficients
    assert {name: unit for name, (_, unit) in FIXTURE["design"].items()} == dict(DESIGN)


def test_dimensionality_errors_are_refused() -> None:
    result = _run(_request(sourced={"max_specific_growth_rate": [1.0, "kg"]}))
    assert result.status == "refused" and result.failure is not None
    assert result.failure.backend_code == "unit_dimension_mismatch"


def test_darkness_gives_analytic_respiration_decay() -> None:
    days = 3.0
    out = _out(_run(_request(design={"peak_par": [0.0, "umol/(m**2*s)"], "harvest_fraction": [0.0, "1"],
                                     "duration": [days, "d"]})))
    assert out["final_biomass"] == pytest.approx(0.5 * math.exp(-0.1 * days), rel=1e-6)
    assert out["harvested_biomass"] == 0.0
    too_hot = _out(_run(_request(design={"temperature_mean": [45.0, "degC"], "harvest_fraction": [0.0, "1"],
                                         "duration": [days, "d"]})))
    assert too_hot["final_biomass"] == pytest.approx(out["final_biomass"], rel=1e-6)  # outside (T_min, T_max)


def test_segment_boundaries_do_not_change_the_trajectory() -> None:
    no_harvest = {"harvest_fraction": [0.0, "1"], "duration": [4.0, "d"]}
    early = _out(_run(_request(design={**no_harvest, "harvest_hour": [3.0, "h"]})))
    late = _out(_run(_request(design={**no_harvest, "harvest_hour": [17.5, "h"]})))
    assert early["final_biomass"] == pytest.approx(late["final_biomass"], rel=1e-6)
    assert early["final_nitrogen"] == pytest.approx(late["final_nitrogen"], rel=1e-6, abs=1e-9)


def test_self_shading_photoinhibition_and_nitrogen_starvation_act_in_the_right_direction() -> None:
    base = _out(_run(_request()))["volumetric_productivity"]
    shaded = _out(_run(_request(sourced={"specific_light_extinction": [600.0, "m**2/kg"]})))
    assert shaded["volumetric_productivity"] < base
    inhibited = _out(_run(_request(sourced={"light_inhibition_constant": [50.0, "umol/(m**2*s)"]})))
    assert inhibited["volumetric_productivity"] < base
    starved = _out(_run(_request(design={"initial_nitrogen": [0.0, "mg/L"], "medium_nitrogen": [0.0, "mg/L"]})))
    assert starved["volumetric_productivity"] < 0  # respiration only
    assert starved["final_nitrogen"] >= 0.0


def test_replete_nitrogen_mode_refuses_exhaustion() -> None:
    result = _run(_request(design={"initial_nitrogen": [0.0, "kg/m3"], "medium_nitrogen": [0.0, "kg/m3"]},
                           backend_options={"nitrogen_response": "replete"}))
    assert result.status == "refused" and result.failure is not None
    assert result.failure.backend_code == "nitrogen_exhausted"


def test_nested_adapter_failure_is_mapped(monkeypatch: pytest.MonkeyPatch) -> None:
    successful = _run(_request())
    failed = successful.model_copy(update={
        "evaluator_id": "fluids.pipe_pressure_drop",
        "status": "refused",
        "failure": EvaluationFailure(category="not_available", backend_code="fluids_missing"),
        "outputs": (),
    })
    monkeypatch.setattr(PipePressureDropEvaluator, "evaluate", lambda self, request: failed)
    result = _run(_request())
    assert result.status == "refused" and result.failure is not None
    assert result.failure.category == "not_available"
    assert result.failure.backend_code == "stack:fluids_missing"


def test_loop_hydraulics_come_from_the_104_stack() -> None:
    out = _out(_run(_request()))
    flow = 0.5 * math.pi * 0.05**2 / 4
    assert out["pumping_power"] == pytest.approx(out["pressure_drop"] * flow / 0.6, rel=1e-12)
    assert out["reynolds_number"] > 4000  # turbulent loop at 0.5 m/s, 50 mm
    assert PipePressureDropEvaluator().descriptor().backend_name == "fluids"


@pytest.mark.parametrize(("kwargs", "expected"), [
    ({"unsourced": ("biomass_loss_rate",)}, ("invalid_input", "parameter_provenance_missing")),
    ({"subject": {**MODEL, "object_type": "material_state"}}, ("unsupported_request", "subject_unsupported")),
    ({"sourced": {"temperature_opt": [40.0, "degC"]}}, ("invalid_input", "temperature_cardinals_invalid")),
    ({"design": {"harvest_fraction": [1.0, "1"]}}, ("invalid_input", "input_range_invalid")),
    ({"design": {"duration": [400.0, "d"]}}, ("unsupported_request", "duration_too_long")),
    ({"design": {"liquid_velocity": [0.04, "m/s"]}}, ("outside_validity_domain", "stack:transitional_regime")),
])
def test_refusals_are_typed_and_never_fall_back_to_default_biology(
    kwargs: dict[str, Any], expected: tuple[str, str],
) -> None:
    result = _run(_request(**kwargs))
    assert result.status == "refused" and result.failure is not None and not result.outputs
    assert (result.failure.category, result.failure.backend_code) == expected
