from __future__ import annotations

import math
from types import MappingProxyType
from typing import Mapping

from .blocks import Fitting, Pipe, Pump, Reservoir
from .errors import ProcessKernelError
from .flowsheet import (
    ExternalMaterialInput,
    MaterialConnection,
    ProcessFlowsheet,
    ScalarConnection,
)
from .streams import MaterialStream
from .units import semantic_registry_sha256

MODEL_ID = "bluerev_geometry_hydraulics_v0"
PROFILE_ID = "bluerev_geometry_hydraulics_process_kernel_v1"
ASSEMBLER_ID = "bluerev_geometry_hydraulics_047_exact_assembler_v1"
STANDARD_GRAVITY = 9.80665
EXPECTED_UNITS = MappingProxyType(
    {
        "tube_length": "m",
        "tube_inner_diameter": "mm",
        "tube_outer_diameter": "mm",
        "reservoir_liquid_volume": "L",
        "target_liquid_velocity": "m/s",
        "liquid_density": "kg/m3",
        "dynamic_viscosity": "Pa*s",
        "minor_loss_coefficient": "1",
        "pump_efficiency": "1",
    }
)


def build_047_flowsheet() -> ProcessFlowsheet:
    blocks = {
        "reservoir": Reservoir(),
        "pipe": Pipe(),
        "fitting": Fitting(),
        "pump": Pump(),
    }
    return ProcessFlowsheet(
        schema_version=1,
        model_identity=PROFILE_ID,
        semantic_unit_registry_identity=semantic_registry_sha256(),
        blocks=blocks,
        material_connections=(
            MaterialConnection("reservoir", "outlet", "pipe", "inlet"),
            MaterialConnection("pipe", "outlet", "fitting", "inlet"),
            MaterialConnection("fitting", "outlet", "pump", "inlet"),
        ),
        scalar_connections=(
            ScalarConnection("pipe", "dynamic_pressure", "fitting", "dynamic_pressure"),
            ScalarConnection("pipe", "major_pressure_loss", "pump", "major_pressure_loss"),
            ScalarConnection("fitting", "minor_pressure_loss", "pump", "minor_pressure_loss"),
        ),
        external_material_inputs=(ExternalMaterialInput("reservoir", "inlet", "loop_liquid"),),
        profile_constants={"standard_gravity": STANDARD_GRAVITY},
        result_assembler_identity=ASSEMBLER_ID,
    )


def execute_047_process_kernel(values: Mapping[str, float]) -> dict[str, object]:
    normalized = _validate_values(values)
    stream = MaterialStream(
        id="loop_liquid",
        composition=None,
        density_kg_m3=normalized["liquid_density"],
        dynamic_viscosity_Pa_s=normalized["dynamic_viscosity"],
    )
    execution = build_047_flowsheet().execute(
        external_streams={"loop_liquid": stream},
        caller_parameters={
            "reservoir": {"reservoir_liquid_volume": normalized["reservoir_liquid_volume"]},
            "pipe": {
                "tube_length": normalized["tube_length"],
                "tube_inner_diameter": normalized["tube_inner_diameter"],
                "tube_outer_diameter": normalized["tube_outer_diameter"],
                "target_liquid_velocity": normalized["target_liquid_velocity"],
            },
            "fitting": {"minor_loss_coefficient": normalized["minor_loss_coefficient"]},
            "pump": {"pump_efficiency": normalized["pump_efficiency"]},
        },
    )
    return assemble_047_result(execution.block_results)


def assemble_047_result(block_results: Mapping[str, object]) -> dict[str, object]:
    reservoir = block_results["reservoir"]
    pipe = block_results["pipe"]
    fitting = block_results["fitting"]
    pump = block_results["pump"]

    tube_volume = pipe.scalar_outputs["tube_volume"]
    reservoir_volume = reservoir.scalar_outputs["reservoir_liquid_volume_m3"]
    total_inventory = tube_volume + reservoir_volume
    circulation_flow = pipe.scalar_outputs["circulation_flow"]
    inventory_turnover_time = total_inventory / circulation_flow

    outputs = {
        "tube_hydraulic_cross_section_area": {"value": pipe.scalar_outputs["hydraulic_area"], "unit": "m2"},
        "tube_liquid_volume": {"value": tube_volume, "unit": "m3"},
        "total_liquid_inventory": {"value": total_inventory, "unit": "m3"},
        "external_illuminated_area_proxy": {"value": pipe.scalar_outputs["external_area"], "unit": "m2"},
        "internal_wetted_area_to_tube_volume": {
            "value": pipe.scalar_outputs["internal_area_to_volume"],
            "unit": "1/m",
        },
        "external_area_to_tube_volume_proxy": {
            "value": pipe.scalar_outputs["external_area_to_volume"],
            "unit": "1/m",
        },
        "circulation_flow_rate": {"value": circulation_flow, "unit": "m3/s"},
        "tube_nominal_transit_time": {"value": pipe.scalar_outputs["tube_transit_time"], "unit": "s"},
        "total_inventory_turnover_time": {"value": inventory_turnover_time, "unit": "s"},
        "reynolds_number": {"value": pipe.scalar_outputs["reynolds_number"], "unit": "1"},
        "darcy_friction_factor": {"value": pipe.scalar_outputs["friction_factor"], "unit": "1"},
        "major_pressure_loss": {"value": pipe.scalar_outputs["major_pressure_loss"], "unit": "Pa"},
        "minor_pressure_loss": {"value": fitting.scalar_outputs["minor_pressure_loss"], "unit": "Pa"},
        "total_pressure_loss": {"value": pump.scalar_outputs["total_pressure_loss"], "unit": "Pa"},
        "equivalent_static_head": {"value": pump.scalar_outputs["equivalent_static_head"], "unit": "m"},
        "hydraulic_power": {"value": pump.scalar_outputs["hydraulic_power"], "unit": "W"},
        "pump_electric_power": {"value": pump.scalar_outputs["pump_electric_power"], "unit": "W"},
    }
    return {
        "schema_version": 1,
        "status": "succeeded",
        "outputs": outputs,
        "diagnostics": {
            "model_id": MODEL_ID,
            "model_fidelity": "M0_static_screening",
            "friction_factor_convention": "Darcy",
            "friction_correlation": pipe.diagnostics["friction_correlation"],
            "circulation_semantics": "closed_loop_recirculation",
            "time_semantics": ["tube_nominal_transit_time", "total_inventory_turnover_time"],
            "external_area_is_proxy": True,
            "pump_curve_not_applied": True,
            "npsh_not_evaluated": True,
            "transient_pressure_not_evaluated": True,
            "minor_loss_coefficient_provisional": True,
            "workbook_runtime_dependency": False,
        },
    }


def _validate_values(values: Mapping[str, float]) -> dict[str, float]:
    if set(values) != set(EXPECTED_UNITS):
        raise ProcessKernelError("input_contract_invalid", "Input set does not match the 047 contract.")
    normalized: dict[str, float] = {}
    for name in EXPECTED_UNITS:
        value = values[name]
        if isinstance(value, bool) or not isinstance(value, int | float) or not math.isfinite(value):
            raise ProcessKernelError("input_contract_invalid", f"Input is not finite: {name}.")
        normalized[name] = float(value)
    for name in (
        "tube_length",
        "tube_inner_diameter",
        "target_liquid_velocity",
        "liquid_density",
        "dynamic_viscosity",
    ):
        if normalized[name] <= 0:
            raise ProcessKernelError("input_domain_invalid", f"Input must be positive: {name}.")
    if normalized["tube_outer_diameter"] < normalized["tube_inner_diameter"]:
        raise ProcessKernelError("input_domain_invalid", "Outer diameter must not be smaller than inner diameter.")
    if normalized["reservoir_liquid_volume"] < 0 or normalized["minor_loss_coefficient"] < 0:
        raise ProcessKernelError("input_domain_invalid", "Inventory and loss coefficient must be nonnegative.")
    if normalized["pump_efficiency"] <= 0 or normalized["pump_efficiency"] > 1:
        raise ProcessKernelError("input_domain_invalid", "Pump efficiency must be in (0, 1].")
    return normalized
