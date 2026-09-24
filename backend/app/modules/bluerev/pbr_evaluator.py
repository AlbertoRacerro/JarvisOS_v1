"""107 PBR-EVALUATOR-1: lumped day/night tubular photobioreactor evaluator.

Model form (reduced order, one well-mixed liquid volume; every coefficient is an input):

* incident PAR ``I0(h) = peak_par * sin(pi * (h - sunrise) / photoperiod)`` during daylight, 0 at night;
* local light ``I(z) = I0 * exp(-specific_light_extinction * X * z)`` across the tube diameter
  (Beer-Lambert, slab approximation); gross growth is the depth average of the Haldane response
  ``mu_max * I / (K_s + I + I**2 / K_i)`` (8-point Gauss-Legendre), so self-shading and
  photoinhibition act locally rather than on an averaged irradiance;
* temperature factor: cardinal temperature model with inflexion (Rosso 1993, as used by
  Bernard & Remond 2012), zero outside (T_min, T_max); liquid temperature follows a prescribed
  diel sinusoid (no heat balance in this slice);
* nitrogen limitation ``N / (K_N + N)`` with a fixed biomass N quota, so dissolved plus biomass
  nitrogen is conserved except for harvest/replenishment;
* respiration ``r * X`` day and night; net O2 production ``Y_O2 * dX/dt`` minus
  ``kLa * (O2 - O2_sat)`` degassing;
* daily semi-continuous harvest at ``harvest_hour``: a fraction of the culture is replaced by
  medium (``medium_nitrogen``, air-saturated O2), applied between CVODE segments so CVODE stays
  the single time/state owner;
* loop hydraulics through the 104 CoolProp (pure water, a screening stand-in for seawater) and
  fluids evaluators.

Every biological and gas-transfer coefficient must carry a ``basis_ref`` (its provenance) or the
request is refused: the evaluator never supplies default biology. A successful run means the model
ran, not that it is qualified; qualification lives in the 102 ledger.
"""

from __future__ import annotations

import math
from collections.abc import Callable, Mapping
from datetime import UTC, datetime
from typing import Final

from app.modules.engineering.evaluator_contracts import (
    EvaluationRequest,
    EvaluationResult,
    EvaluatorAvailability,
    EvaluatorDescriptor,
    NamedQuantity,
    NumericalDiagnostics,
)
from app.modules.engineering.refs import EvaluationRequestRef, MaterialStateRef
from app.modules.process_stack._common import (
    EvaluationRefusal,
    descriptor_version,
    evaluate_with,
    import_availability,
    magnitude,
    quantities,
)
from app.modules.process_stack.correlations import PIPE_EVALUATOR_ID, PipePressureDropEvaluator
from app.modules.process_stack.dynamics import integrate_ode
from app.modules.process_stack.properties import EVALUATOR_ID as PROPERTY_EVALUATOR_ID
from app.modules.process_stack.properties import CoolPropPropertyEvaluator

EVALUATOR_ID: Final = "bluerev.pbr_day_night"
MODEL_VERSION: Final = "pbr_day_night.v1"
MAX_DAYS: Final = 366
_SAMPLES_PER_HOUR: Final = 4

# Coefficients that describe the organism or gas transfer: provenance (basis_ref) is mandatory.
SOURCED: Final[Mapping[str, str]] = {
    "max_specific_growth_rate": "1/h",
    "light_saturation_constant": "umol/(m**2*s)",
    "light_inhibition_constant": "umol/(m**2*s)",
    "specific_light_extinction": "m**2/kg",
    "respiration_rate": "1/h",
    "nitrogen_half_saturation": "kg/m3",
    "biomass_nitrogen_fraction": "1",
    "oxygen_yield": "1",
    "temperature_min": "K",
    "temperature_opt": "K",
    "temperature_max": "K",
    "oxygen_kla": "1/h",
    "oxygen_saturation": "kg/m3",
}
# Design, operation, scenario and initial-state variables chosen by the study.
DESIGN: Final[Mapping[str, str]] = {
    "initial_biomass": "kg/m3",
    "initial_nitrogen": "kg/m3",
    "initial_dissolved_oxygen": "kg/m3",
    "peak_par": "umol/(m**2*s)",
    "photoperiod": "h",
    "temperature_mean": "K",
    "temperature_amplitude": "K",
    "duration": "d",
    "tube_inner_diameter": "m",
    "loop_length": "m",
    "liquid_velocity": "m/s",
    "pump_efficiency": "1",
    "harvest_fraction": "1",
    "harvest_hour": "h",
    "medium_nitrogen": "kg/m3",
}
_GAUSS_POINTS: Final = 8


def _cardinal_temperature(t: float, t_min: float, t_opt: float, t_max: float) -> float:
    if not t_min < t < t_max:
        return 0.0
    numerator = (t - t_max) * (t - t_min) ** 2
    denominator = (t_opt - t_min) * ((t_opt - t_min) * (t - t_opt) - (t_opt - t_max) * (t_opt + t_min - 2.0 * t))
    return max(0.0, numerator / denominator)


class PbrDayNightEvaluator:
    def descriptor(self) -> EvaluatorDescriptor:
        return EvaluatorDescriptor(
            evaluator_id=EVALUATOR_ID, backend_kind="dynamic_simulator", backend_name="scikit-sundae",
            backend_version=f"{MODEL_VERSION}+sksundae-{descriptor_version('sksundae')}",
            fidelity="reduced_order",
            capabilities=("day_night_light", "self_shading", "photoinhibition", "cardinal_temperature",
                          "nitrogen_limitation", "oxygen_degassing", "semi_continuous_harvest", "loop_hydraulics"),
        )

    def availability(self) -> EvaluatorAvailability:
        stack = (PipePressureDropEvaluator(), CoolPropPropertyEvaluator())
        missing = next((item.availability() for item in stack if item.availability().state != "available"), None)
        if missing is not None:
            return missing.model_copy(update={"evaluator_id": EVALUATOR_ID})
        return import_availability(EVALUATOR_ID, "sksundae", lambda: self.descriptor().backend_version)

    def evaluate(self, request: EvaluationRequest) -> EvaluationResult:
        return evaluate_with(self, request, lambda: _simulate(request))


def _inputs(request: EvaluationRequest) -> dict[str, float]:
    if request.subject_ref.object_type != "dynamic_model":
        raise EvaluationRefusal("unsupported_request", "subject_unsupported", "subject must be a dynamic model")
    if request.backend_options:
        raise EvaluationRefusal("unsupported_request", "option_unsupported", "no backend options are supported")
    given = {item.name: item.value for item in request.inputs}
    expected = {**SOURCED, **DESIGN}
    unknown, missing = sorted(set(given) - set(expected)), sorted(set(expected) - set(given))
    if unknown or missing:
        raise EvaluationRefusal("invalid_input", "input_names_invalid", f"missing={missing} unknown={unknown}")
    unsourced = sorted(name for name in SOURCED if given[name].basis_ref is None)
    if unsourced:
        raise EvaluationRefusal("invalid_input", "parameter_provenance_missing",
                                f"coefficients without basis_ref: {unsourced}")
    x = {name: magnitude(given[name], unit) for name, unit in expected.items()}
    non_negative = [name for name in expected if name not in {"temperature_amplitude"}]
    if any(x[name] < 0.0 for name in non_negative):
        raise EvaluationRefusal("invalid_input", "input_negative",
                                f"negative: {sorted(name for name in non_negative if x[name] < 0.0)}")
    positive = ("max_specific_growth_rate", "light_saturation_constant", "light_inhibition_constant",
                "specific_light_extinction", "nitrogen_half_saturation", "oxygen_kla", "oxygen_saturation",
                "tube_inner_diameter", "loop_length", "liquid_velocity", "pump_efficiency", "duration",
                "initial_biomass")
    if any(x[name] <= 0.0 for name in positive):
        raise EvaluationRefusal("invalid_input", "input_non_positive",
                                f"must be positive: {sorted(name for name in positive if x[name] <= 0.0)}")
    if not x["temperature_min"] < x["temperature_opt"] < x["temperature_max"]:
        raise EvaluationRefusal("invalid_input", "temperature_cardinals_invalid", "need T_min < T_opt < T_max")
    if not (0.0 < x["photoperiod"] <= 24.0 and 0.0 <= x["harvest_hour"] < 24.0 and x["harvest_fraction"] < 1.0
            and x["pump_efficiency"] <= 1.0 and x["biomass_nitrogen_fraction"] < 1.0):
        raise EvaluationRefusal("invalid_input", "input_range_invalid",
                                "photoperiod in (0, 24] h, harvest_hour in [0, 24) h, fractions/efficiency < 1")
    if x["duration"] > MAX_DAYS:
        raise EvaluationRefusal("unsupported_request", "duration_too_long", f"at most {MAX_DAYS} days")
    return x


def _rhs(x: Mapping[str, float]) -> Callable[[float, tuple[float, ...]], list[float]]:
    import numpy as np

    nodes, weights = np.polynomial.legendre.leggauss(_GAUSS_POINTS)
    depths = 0.5 * (nodes + 1.0)  # fraction of the diameter
    half_weights = 0.5 * weights
    sunrise = 12.0 - x["photoperiod"] / 2.0

    def growth(hour: float, biomass: float) -> float:
        day_hour = hour % 24.0
        if not sunrise < day_hour < sunrise + x["photoperiod"]:
            return 0.0
        surface = x["peak_par"] * math.sin(math.pi * (day_hour - sunrise) / x["photoperiod"])
        optical_depth = x["specific_light_extinction"] * max(biomass, 0.0) * x["tube_inner_diameter"]
        light = surface * np.exp(-optical_depth * depths)
        local = light / (x["light_saturation_constant"] + light + light**2 / x["light_inhibition_constant"])
        temperature = x["temperature_mean"] + x["temperature_amplitude"] * math.sin(2 * math.pi * (day_hour - 9.0) / 24)
        thermal = _cardinal_temperature(temperature, x["temperature_min"], x["temperature_opt"], x["temperature_max"])
        return float(x["max_specific_growth_rate"] * thermal * np.dot(half_weights, local))

    def rhs(hour: float, y: tuple[float, ...]) -> list[float]:
        biomass, nitrogen, oxygen = y
        available = max(nitrogen, 0.0)
        gross = growth(hour, biomass) * available / (x["nitrogen_half_saturation"] + available)
        d_biomass = (gross - x["respiration_rate"]) * biomass
        return [
            d_biomass,
            -x["biomass_nitrogen_fraction"] * d_biomass,
            x["oxygen_yield"] * d_biomass - x["oxygen_kla"] * (oxygen - x["oxygen_saturation"]),
        ]

    return rhs


def _hydraulics(request: EvaluationRequest, x: Mapping[str, float]) -> dict[str, float]:
    """Loop pressure drop and pump power through the 104 evaluators (water at mean temperature)."""
    now = datetime.now(UTC)
    ref = request.request_ref

    def sub_request(evaluator_id: str, suffix: str, inputs: Mapping[str, tuple[float, str]]) -> EvaluationRequest:
        return EvaluationRequest(
            request_ref=EvaluationRequestRef(authority_owner=ref.authority_owner, object_id=f"{ref.object_id}/{suffix}",
                                             workspace_id=ref.workspace_id, revision=ref.revision),
            evaluator_id=evaluator_id,
            subject_ref=MaterialStateRef(authority_owner="bluerev", object_id=f"{ref.object_id}/culture",
                                         workspace_id=ref.workspace_id, revision=ref.revision),
            inputs=quantities(inputs), requested_at=now, deadline_at=request.deadline_at,
        )

    def outputs(result: EvaluationResult) -> dict[str, float]:
        if result.status != "succeeded":
            failure = result.failure
            raise EvaluationRefusal(
                failure.category if failure else "internal_error",
                f"stack:{failure.backend_code}" if failure else "stack:failed",
                f"{result.evaluator_id}: {failure.message if failure else result.status}",
            )
        return {item.name: item.value.value for item in result.outputs}

    water = outputs(CoolPropPropertyEvaluator().evaluate(sub_request(PROPERTY_EVALUATOR_ID, "water", {
        "temperature": (x["temperature_mean"], "K"), "pressure": (101325.0, "Pa")})))
    pipe = outputs(PipePressureDropEvaluator().evaluate(sub_request(PIPE_EVALUATOR_ID, "loop", {
        "density": (water["density"], "kg/m3"), "dynamic_viscosity": (water["dynamic_viscosity"], "Pa*s"),
        "velocity": (x["liquid_velocity"], "m/s"), "diameter": (x["tube_inner_diameter"], "m"),
        "length": (x["loop_length"], "m"), "roughness": (0.0, "m")})))
    flow = x["liquid_velocity"] * math.pi * x["tube_inner_diameter"] ** 2 / 4.0
    return {"reynolds_number": pipe["reynolds_number"], "pressure_drop": pipe["pressure_drop"],
            "pumping_power": pipe["pressure_drop"] * flow / x["pump_efficiency"]}


def _simulate(request: EvaluationRequest) -> tuple[tuple[NamedQuantity, ...], NumericalDiagnostics]:
    x = _inputs(request)
    hydraulics = _hydraulics(request, x)
    rhs = _rhs(x)
    end = x["duration"] * 24.0
    boundaries = [0.0]
    harvest = x["harvest_hour"] if x["harvest_hour"] > 0.0 else 24.0
    while harvest < end:
        boundaries.append(harvest)
        harvest += 24.0
    boundaries.append(end)

    state: tuple[float, ...] = (x["initial_biomass"], x["initial_nitrogen"], x["initial_dissolved_oxygen"])
    harvested_biomass = harvested_nitrogen = fed_nitrogen = 0.0
    samples: list[tuple[float, ...]] = [state]
    evaluations = 0
    for start, stop in zip(boundaries, boundaries[1:], strict=False):
        count = max(2, math.ceil((stop - start) * _SAMPLES_PER_HOUR) + 1)
        grid = [start + (stop - start) * i / (count - 1) for i in range(count)]
        solution = integrate_ode(rhs, state, grid, rtol=1e-8, atol=1e-10)
        evaluations += solution.diagnostics.iterations or 0
        if not solution.success:
            raise EvaluationRefusal("did_not_converge", "cvode_failed", solution.message)
        samples.extend(solution.states[1:])
        state = solution.states[-1]
        if stop < end:  # harvest and replenish between segments
            fraction = x["harvest_fraction"]
            harvested_biomass += fraction * state[0]
            harvested_nitrogen += fraction * state[1]
            fed_nitrogen += fraction * x["medium_nitrogen"]
            state = (state[0] * (1.0 - fraction),
                     state[1] * (1.0 - fraction) + fraction * x["medium_nitrogen"],
                     state[2] * (1.0 - fraction) + fraction * x["oxygen_saturation"])
    if any(value < -1e-9 for sample in samples for value in sample):
        raise EvaluationRefusal("numerical_error", "negative_state", "integrated state became negative")

    quota = x["biomass_nitrogen_fraction"]
    nitrogen_in = x["initial_nitrogen"] + quota * x["initial_biomass"] + fed_nitrogen
    nitrogen_out = state[1] + quota * state[0] + harvested_nitrogen + quota * harvested_biomass
    days = x["duration"]
    return quantities({
        "final_biomass": (state[0], "kg/m3"),
        "mean_biomass": (sum(sample[0] for sample in samples) / len(samples), "kg/m3"),
        "harvested_biomass": (harvested_biomass, "kg/m3"),
        "volumetric_productivity": ((harvested_biomass + state[0] - x["initial_biomass"]) / days, "kg/(m**3*d)"),
        "final_nitrogen": (state[1], "kg/m3"),
        "nitrogen_balance_error": (abs(nitrogen_in - nitrogen_out), "kg/m3"),
        "max_dissolved_oxygen": (max(sample[2] for sample in samples), "kg/m3"),
        "max_oxygen_saturation_ratio": (max(sample[2] for sample in samples) / x["oxygen_saturation"], "1"),
        **{name: (value, unit) for name, value, unit in (
            ("reynolds_number", hydraulics["reynolds_number"], "1"),
            ("pressure_drop", hydraulics["pressure_drop"], "Pa"),
            ("pumping_power", hydraulics["pumping_power"], "W"),
        )},
    }), NumericalDiagnostics(converged=True, iterations=evaluations,
                             final_residual=abs(nitrogen_in - nitrogen_out))

