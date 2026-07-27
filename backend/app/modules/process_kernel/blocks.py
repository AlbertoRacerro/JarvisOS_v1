from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from types import MappingProxyType

from .contracts import BlockResult, MaterialPort, ScalarPort
from .errors import ProcessKernelError
from .streams import MaterialStream


def _ports(values: Mapping[str, object]) -> Mapping[str, object]:
    return MappingProxyType(dict(values))


def _require_exact_keys(values: Mapping[str, object], expected: set[str], code: str) -> None:
    if set(values) != expected:
        raise ProcessKernelError(code, "Block inputs do not match the declared contract.")


def _finite_number(values: Mapping[str, object], name: str, code: str) -> float:
    value = values[name]
    if isinstance(value, bool) or not isinstance(value, int | float) or not math.isfinite(float(value)):
        raise ProcessKernelError(code, f"Block scalar must be finite: {name}.")
    return float(value)


@dataclass(frozen=True, slots=True)
class Reservoir:
    block_id: str = "reservoir"
    material_inlets: Mapping[str, MaterialPort] = field(
        default_factory=lambda: _ports({"inlet": MaterialPort("inlet")})
    )
    scalar_inlets: Mapping[str, ScalarPort] = field(default_factory=lambda: _ports({}))
    material_outlets: Mapping[str, MaterialPort] = field(
        default_factory=lambda: _ports({"outlet": MaterialPort("outlet")})
    )
    scalar_outlets: Mapping[str, ScalarPort] = field(
        default_factory=lambda: _ports(
            {"reservoir_liquid_volume_m3": ScalarPort("reservoir_liquid_volume_m3", "m3", "volume")}
        )
    )
    caller_parameters: tuple[str, ...] = ("reservoir_liquid_volume",)
    profile_constants: tuple[str, ...] = ()

    def solve(
        self,
        material_inputs: Mapping[str, MaterialStream],
        scalar_inputs: Mapping[str, float],
        caller_parameter_values: Mapping[str, float],
        profile_constant_values: Mapping[str, float],
    ) -> BlockResult:
        _require_exact_keys(material_inputs, {"inlet"}, "reservoir_material_inputs_invalid")
        _require_exact_keys(scalar_inputs, set(), "reservoir_scalar_inputs_invalid")
        _require_exact_keys(caller_parameter_values, {"reservoir_liquid_volume"}, "reservoir_parameters_invalid")
        _require_exact_keys(profile_constant_values, set(), "reservoir_constants_invalid")
        reservoir_liquid_volume = _finite_number(
            caller_parameter_values,
            "reservoir_liquid_volume",
            "reservoir_parameters_invalid",
        )
        if reservoir_liquid_volume < 0:
            raise ProcessKernelError("reservoir_parameters_invalid", "Reservoir volume must be nonnegative.")
        reservoir_volume = reservoir_liquid_volume / 1000.0
        return BlockResult(
            material_outputs={"outlet": replace(material_inputs["inlet"])},
            scalar_outputs={"reservoir_liquid_volume_m3": reservoir_volume},
        )


@dataclass(frozen=True, slots=True)
class Pipe:
    block_id: str = "pipe"
    material_inlets: Mapping[str, MaterialPort] = field(
        default_factory=lambda: _ports(
            {"inlet": MaterialPort("inlet", required_stream_fields=("density_kg_m3", "dynamic_viscosity_Pa_s"))}
        )
    )
    scalar_inlets: Mapping[str, ScalarPort] = field(default_factory=lambda: _ports({}))
    material_outlets: Mapping[str, MaterialPort] = field(
        default_factory=lambda: _ports({"outlet": MaterialPort("outlet")})
    )
    scalar_outlets: Mapping[str, ScalarPort] = field(
        default_factory=lambda: _ports(
            {
                "hydraulic_area": ScalarPort("hydraulic_area", "m2", "area"),
                "tube_volume": ScalarPort("tube_volume", "m3", "volume"),
                "external_area": ScalarPort("external_area", "m2", "area"),
                "internal_area_to_volume": ScalarPort("internal_area_to_volume", "1/m", "inverse_length"),
                "external_area_to_volume": ScalarPort("external_area_to_volume", "1/m", "inverse_length"),
                "circulation_flow": ScalarPort("circulation_flow", "m3/s", "volumetric_flow"),
                "tube_transit_time": ScalarPort("tube_transit_time", "s", "time"),
                "reynolds_number": ScalarPort("reynolds_number", "1", "dimensionless"),
                "friction_factor": ScalarPort("friction_factor", "1", "dimensionless"),
                "dynamic_pressure": ScalarPort("dynamic_pressure", "Pa", "pressure"),
                "major_pressure_loss": ScalarPort("major_pressure_loss", "Pa", "pressure"),
            }
        )
    )
    caller_parameters: tuple[str, ...] = (
        "tube_length",
        "tube_inner_diameter",
        "tube_outer_diameter",
        "target_liquid_velocity",
    )
    profile_constants: tuple[str, ...] = ()

    def solve(
        self,
        material_inputs: Mapping[str, MaterialStream],
        scalar_inputs: Mapping[str, float],
        caller_parameter_values: Mapping[str, float],
        profile_constant_values: Mapping[str, float],
    ) -> BlockResult:
        _require_exact_keys(material_inputs, {"inlet"}, "pipe_material_inputs_invalid")
        _require_exact_keys(scalar_inputs, set(), "pipe_scalar_inputs_invalid")
        _require_exact_keys(caller_parameter_values, set(self.caller_parameters), "pipe_parameters_invalid")
        _require_exact_keys(profile_constant_values, set(), "pipe_constants_invalid")
        stream = material_inputs["inlet"]
        stream.require("density_kg_m3", "dynamic_viscosity_Pa_s")
        density = stream.density_kg_m3
        viscosity = stream.dynamic_viscosity_Pa_s
        assert density is not None and viscosity is not None

        tube_length = _finite_number(caller_parameter_values, "tube_length", "pipe_parameters_invalid")
        diameter_inner_mm = _finite_number(
            caller_parameter_values,
            "tube_inner_diameter",
            "pipe_parameters_invalid",
        )
        diameter_outer_mm = _finite_number(
            caller_parameter_values,
            "tube_outer_diameter",
            "pipe_parameters_invalid",
        )
        velocity = _finite_number(caller_parameter_values, "target_liquid_velocity", "pipe_parameters_invalid")
        if tube_length <= 0 or diameter_inner_mm <= 0 or velocity <= 0:
            raise ProcessKernelError("pipe_parameters_invalid", "Pipe length, inner diameter, and velocity must be positive.")
        if diameter_outer_mm < diameter_inner_mm:
            raise ProcessKernelError("pipe_parameters_invalid", "Pipe outer diameter must not be smaller than inner diameter.")
        diameter_inner = diameter_inner_mm / 1000.0
        diameter_outer = diameter_outer_mm / 1000.0

        hydraulic_area = math.pi * diameter_inner**2 / 4.0
        tube_volume = hydraulic_area * tube_length
        external_area = math.pi * diameter_outer * tube_length
        internal_area = math.pi * diameter_inner * tube_length
        internal_area_to_volume = internal_area / tube_volume
        external_area_to_volume = external_area / tube_volume
        circulation_flow = velocity * hydraulic_area
        tube_transit_time = tube_length / velocity
        reynolds_number = density * velocity * diameter_inner / viscosity
        if reynolds_number < 2300.0:
            friction_factor = 64.0 / reynolds_number
            friction_correlation = "laminar_64_over_Re"
        elif 4000.0 <= reynolds_number <= 100000.0:
            friction_factor = 0.3164 * reynolds_number**-0.25
            friction_correlation = "blasius_smooth_pipe_v0"
        else:
            raise ProcessKernelError("correlation_not_qualified", "Hydraulic correlation is not qualified.")
        dynamic_pressure = density * velocity**2 / 2.0
        major_pressure_loss = friction_factor * (tube_length / diameter_inner) * dynamic_pressure

        return BlockResult(
            material_outputs={"outlet": stream.with_flow(volumetric_flow_m3_s=circulation_flow)},
            scalar_outputs={
                "hydraulic_area": hydraulic_area,
                "tube_volume": tube_volume,
                "external_area": external_area,
                "internal_area_to_volume": internal_area_to_volume,
                "external_area_to_volume": external_area_to_volume,
                "circulation_flow": circulation_flow,
                "tube_transit_time": tube_transit_time,
                "reynolds_number": reynolds_number,
                "friction_factor": friction_factor,
                "dynamic_pressure": dynamic_pressure,
                "major_pressure_loss": major_pressure_loss,
            },
            diagnostics={
                "hydraulic_regime": "laminar" if reynolds_number < 2300.0 else "turbulent",
                "friction_correlation": friction_correlation,
                "friction_factor_convention": "Darcy",
            },
        )


@dataclass(frozen=True, slots=True)
class Fitting:
    block_id: str = "fitting"
    material_inlets: Mapping[str, MaterialPort] = field(
        default_factory=lambda: _ports({"inlet": MaterialPort("inlet")})
    )
    scalar_inlets: Mapping[str, ScalarPort] = field(
        default_factory=lambda: _ports({"dynamic_pressure": ScalarPort("dynamic_pressure", "Pa", "pressure")})
    )
    material_outlets: Mapping[str, MaterialPort] = field(
        default_factory=lambda: _ports({"outlet": MaterialPort("outlet")})
    )
    scalar_outlets: Mapping[str, ScalarPort] = field(
        default_factory=lambda: _ports(
            {"minor_pressure_loss": ScalarPort("minor_pressure_loss", "Pa", "pressure")}
        )
    )
    caller_parameters: tuple[str, ...] = ("minor_loss_coefficient",)
    profile_constants: tuple[str, ...] = ()

    def solve(
        self,
        material_inputs: Mapping[str, MaterialStream],
        scalar_inputs: Mapping[str, float],
        caller_parameter_values: Mapping[str, float],
        profile_constant_values: Mapping[str, float],
    ) -> BlockResult:
        _require_exact_keys(material_inputs, {"inlet"}, "fitting_material_inputs_invalid")
        _require_exact_keys(scalar_inputs, {"dynamic_pressure"}, "fitting_scalar_inputs_invalid")
        _require_exact_keys(caller_parameter_values, {"minor_loss_coefficient"}, "fitting_parameters_invalid")
        _require_exact_keys(profile_constant_values, set(), "fitting_constants_invalid")
        dynamic_pressure = _finite_number(scalar_inputs, "dynamic_pressure", "fitting_scalar_inputs_invalid")
        loss_coefficient = _finite_number(
            caller_parameter_values,
            "minor_loss_coefficient",
            "fitting_parameters_invalid",
        )
        if dynamic_pressure < 0:
            raise ProcessKernelError("fitting_scalar_inputs_invalid", "Dynamic pressure must be nonnegative.")
        if loss_coefficient < 0:
            raise ProcessKernelError("fitting_parameters_invalid", "Minor-loss coefficient must be nonnegative.")
        minor_pressure_loss = loss_coefficient * dynamic_pressure
        return BlockResult(
            material_outputs={"outlet": replace(material_inputs["inlet"])},
            scalar_outputs={"minor_pressure_loss": minor_pressure_loss},
        )


@dataclass(frozen=True, slots=True)
class Pump:
    block_id: str = "pump"
    material_inlets: Mapping[str, MaterialPort] = field(
        default_factory=lambda: _ports(
            {"inlet": MaterialPort("inlet", required_stream_fields=("density_kg_m3", "volumetric_flow_m3_s"))}
        )
    )
    scalar_inlets: Mapping[str, ScalarPort] = field(
        default_factory=lambda: _ports(
            {
                "major_pressure_loss": ScalarPort("major_pressure_loss", "Pa", "pressure"),
                "minor_pressure_loss": ScalarPort("minor_pressure_loss", "Pa", "pressure"),
            }
        )
    )
    material_outlets: Mapping[str, MaterialPort] = field(
        default_factory=lambda: _ports({"outlet": MaterialPort("outlet")})
    )
    scalar_outlets: Mapping[str, ScalarPort] = field(
        default_factory=lambda: _ports(
            {
                "total_pressure_loss": ScalarPort("total_pressure_loss", "Pa", "pressure"),
                "equivalent_static_head": ScalarPort("equivalent_static_head", "m", "length"),
                "hydraulic_power": ScalarPort("hydraulic_power", "W", "power"),
                "pump_electric_power": ScalarPort("pump_electric_power", "W", "power"),
            }
        )
    )
    caller_parameters: tuple[str, ...] = ("pump_efficiency",)
    profile_constants: tuple[str, ...] = ("standard_gravity",)

    def solve(
        self,
        material_inputs: Mapping[str, MaterialStream],
        scalar_inputs: Mapping[str, float],
        caller_parameter_values: Mapping[str, float],
        profile_constant_values: Mapping[str, float],
    ) -> BlockResult:
        _require_exact_keys(material_inputs, {"inlet"}, "pump_material_inputs_invalid")
        _require_exact_keys(
            scalar_inputs,
            {"major_pressure_loss", "minor_pressure_loss"},
            "pump_scalar_inputs_invalid",
        )
        _require_exact_keys(caller_parameter_values, {"pump_efficiency"}, "pump_parameters_invalid")
        _require_exact_keys(profile_constant_values, {"standard_gravity"}, "pump_constants_invalid")
        stream = material_inputs["inlet"]
        stream.require("density_kg_m3", "volumetric_flow_m3_s")
        density = stream.density_kg_m3
        volumetric_flow = stream.volumetric_flow_m3_s
        assert density is not None and volumetric_flow is not None

        major_pressure_loss = _finite_number(
            scalar_inputs,
            "major_pressure_loss",
            "pump_scalar_inputs_invalid",
        )
        minor_pressure_loss = _finite_number(
            scalar_inputs,
            "minor_pressure_loss",
            "pump_scalar_inputs_invalid",
        )
        pump_efficiency = _finite_number(
            caller_parameter_values,
            "pump_efficiency",
            "pump_parameters_invalid",
        )
        standard_gravity = _finite_number(
            profile_constant_values,
            "standard_gravity",
            "pump_constants_invalid",
        )
        if major_pressure_loss < 0 or minor_pressure_loss < 0:
            raise ProcessKernelError("pump_scalar_inputs_invalid", "Pump pressure losses must be nonnegative.")
        if pump_efficiency <= 0 or pump_efficiency > 1:
            raise ProcessKernelError("pump_parameters_invalid", "Pump efficiency must be in (0, 1].")
        if standard_gravity <= 0:
            raise ProcessKernelError("pump_constants_invalid", "Standard gravity must be positive.")

        total_pressure_loss = major_pressure_loss + minor_pressure_loss
        equivalent_static_head = total_pressure_loss / (density * standard_gravity)
        hydraulic_power = total_pressure_loss * volumetric_flow
        pump_electric_power = hydraulic_power / pump_efficiency
        return BlockResult(
            material_outputs={"outlet": replace(stream)},
            scalar_outputs={
                "total_pressure_loss": total_pressure_loss,
                "equivalent_static_head": equivalent_static_head,
                "hydraulic_power": hydraulic_power,
                "pump_electric_power": pump_electric_power,
            },
        )
