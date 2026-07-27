from __future__ import annotations

import hashlib
import math
from collections.abc import Mapping
from dataclasses import FrozenInstanceError, dataclass, field, replace
from types import MappingProxyType

import pytest

from app.modules.process_kernel.blocks import Fitting, Pump
from app.modules.process_kernel.components import (
    COMPONENT_CATALOG,
    SCREENING_MASS_CONSTANTS_V0,
    Component,
)
from app.modules.process_kernel.contracts import BlockResult, MaterialPort, ScalarPort
from app.modules.process_kernel.errors import ProcessKernelError
from app.modules.process_kernel.flowsheet import (
    ExternalMaterialInput,
    MaterialConnection,
    ProcessFlowsheet,
    ScalarConnection,
)
from app.modules.process_kernel.profile_047 import build_047_flowsheet
from app.modules.process_kernel.streams import MaterialStream
from app.modules.process_kernel.units import (
    SEMANTIC_UNITS,
    normalize_magnitude,
    semantic_registry_bytes,
    semantic_registry_sha256,
)
from app.modules.runner.process_kernel_047 import normalize_input_set
from app.modules.runner.safety import RunnerSafetyError


def _canonical_input() -> dict[str, dict[str, object]]:
    return {
        "tube_length": {"value": 20.0, "unit": "m"},
        "tube_inner_diameter": {"value": 30.0, "unit": "mm"},
        "tube_outer_diameter": {"value": 36.0, "unit": "mm"},
        "reservoir_liquid_volume": {"value": 5.0, "unit": "L"},
        "target_liquid_velocity": {"value": 0.25, "unit": "m/s"},
        "liquid_density": {"value": 1025.0, "unit": "kg/m3"},
        "dynamic_viscosity": {"value": 0.0011, "unit": "Pa*s"},
        "minor_loss_coefficient": {"value": 8.0, "unit": "1"},
        "pump_efficiency": {"value": 0.35, "unit": "1"},
    }


def _caller_parameters() -> dict[str, dict[str, float]]:
    return {
        "reservoir": {"reservoir_liquid_volume": 5.0},
        "pipe": {
            "tube_length": 20.0,
            "tube_inner_diameter": 30.0,
            "tube_outer_diameter": 36.0,
            "target_liquid_velocity": 0.25,
        },
        "fitting": {"minor_loss_coefficient": 8.0},
        "pump": {"pump_efficiency": 0.35},
    }


def _stream(*, composition: Mapping[str, float] | None = None) -> MaterialStream:
    return MaterialStream(
        id="loop_liquid",
        composition=composition,
        density_kg_m3=1025.0,
        dynamic_viscosity_Pa_s=0.0011,
    )


def _assert_kernel_error(code: str, operation) -> None:
    with pytest.raises(ProcessKernelError) as exc_info:
        operation()
    assert exc_info.value.code == code


def test_semantic_registry_has_exact_closed_scales_and_digest() -> None:
    expected = {
        "gDW": ("gram", 0.001, "mass", "dry_biomass"),
        "kgDW": ("kilogram", 1.0, "mass", "dry_biomass"),
        "mgN": ("milligram", 0.000001, "mass", "nitrogen"),
        "gN": ("gram", 0.001, "mass", "nitrogen"),
        "mgP": ("milligram", 0.000001, "mass", "phosphorus"),
        "gP": ("gram", 0.001, "mass", "phosphorus"),
        "gC": ("gram", 0.001, "mass", "carbon"),
        "kgC": ("kilogram", 1.0, "mass", "carbon"),
        "mLCO2": ("milliliter", 0.000001, "volume", "carbon_dioxide"),
        "LCO2": ("liter", 0.001, "volume", "carbon_dioxide"),
        "EUR": ("EUR", 1.0, "currency", "EUR"),
    }

    assert set(SEMANTIC_UNITS) == set(expected)
    for token, values in expected.items():
        definition = SEMANTIC_UNITS[token]
        assert (
            definition.pint_unit,
            definition.scale_to_si,
            definition.physical_dimension,
            definition.semantic_basis,
        ) == values
    payload = semantic_registry_bytes()
    assert payload == semantic_registry_bytes()
    assert semantic_registry_sha256() == hashlib.sha256(payload).hexdigest()


@pytest.mark.parametrize(
    ("value", "source", "target", "dimension", "basis", "expected"),
    [
        (1000.0, "gDW", "kgDW", "mass", "dry_biomass", 1.0),
        (1000.0, "mgN", "gN", "mass", "nitrogen", 1.0),
        (1000.0, "mLCO2", "LCO2", "volume", "carbon_dioxide", 1.0),
    ],
)
def test_same_basis_semantic_conversions_are_exact(
    value: float,
    source: str,
    target: str,
    dimension: str,
    basis: str,
    expected: float,
) -> None:
    assert normalize_magnitude(
        value,
        source_unit=source,
        target_unit=target,
        physical_dimension=dimension,
        semantic_basis=basis,
    ) == pytest.approx(expected, rel=0.0, abs=1e-15)


@pytest.mark.parametrize(
    ("source", "target", "dimension", "basis", "expected_code"),
    [
        ("mgN", "mgP", "mass", "phosphorus", "quantity_semantic_basis_mismatch"),
        ("kg", "kgDW", "mass", "dry_biomass", "quantity_semantic_basis_mismatch"),
        ("mL", "mLCO2", "volume", "carbon_dioxide", "quantity_semantic_basis_mismatch"),
        ("gDw", "kgDW", "mass", "dry_biomass", "unit_unknown"),
        ("cm", "kg", "mass", None, "quantity_dimension_mismatch"),
    ],
)
def test_cross_basis_lookalike_and_dimension_mismatch_fail_closed(
    source: str,
    target: str,
    dimension: str,
    basis: str | None,
    expected_code: str,
) -> None:
    _assert_kernel_error(
        expected_code,
        lambda: normalize_magnitude(
            1.0,
            source_unit=source,
            target_unit=target,
            physical_dimension=dimension,
            semantic_basis=basis,
        ),
    )


def test_v2_domain_is_applied_after_unit_conversion() -> None:
    valid = _canonical_input()
    valid["pump_efficiency"] = {"value": 35.0, "unit": "percent"}
    assert normalize_input_set(valid)["pump_efficiency"] == {"value": 0.35, "unit": "1"}

    invalid = _canonical_input()
    invalid["pump_efficiency"] = {"value": 101.0, "unit": "percent"}
    with pytest.raises(RunnerSafetyError) as exc_info:
        normalize_input_set(invalid)
    assert exc_info.value.code == "runner_input_invalid"


def test_components_keep_molecules_and_fixture_pseudocomponent_distinct() -> None:
    assert COMPONENT_CATALOG["water"].molecular_formula == {"H": 2.0, "O": 1.0}
    biomass = COMPONENT_CATALOG["fixture_biomass"]
    assert biomass.molecular_formula is None
    assert biomass.scientific_molar_mass_kg_per_mol is None
    assert SCREENING_MASS_CONSTANTS_V0.authority == "merged 048 rounded screening constants"
    _assert_kernel_error(
        "component_molar_mass_invalid",
        lambda: Component(
            id="unsupported",
            name="Unsupported",
            scientific_molar_mass_kg_per_mol=0.044,
        ),
    )


def test_material_stream_composition_flow_and_immutability_contract() -> None:
    stream = MaterialStream(
        id="known",
        composition={"water": 0.75, "carbon_dioxide": 0.25},
        density_kg_m3=1000.0,
        volumetric_flow_m3_s=0.002,
    )
    assert stream.composition == {"carbon_dioxide": 0.25, "water": 0.75}
    assert stream.mass_flow_kg_s == 2.0
    assert MaterialStream(id="unknown").composition is None
    with pytest.raises(FrozenInstanceError):
        stream.mass_flow_kg_s = 3.0  # type: ignore[misc]
    _assert_kernel_error(
        "stream_component_unknown",
        lambda: MaterialStream(id="bad", composition={"unregistered": 1.0}),
    )
    _assert_kernel_error(
        "stream_composition_invalid",
        lambda: MaterialStream(id="bad", composition={"water": 0.9}),
    )
    _assert_kernel_error(
        "stream_flow_inconsistent",
        lambda: MaterialStream(
            id="bad",
            density_kg_m3=1000.0,
            volumetric_flow_m3_s=0.002,
            mass_flow_kg_s=3.0,
        ),
    )


@dataclass(frozen=True, slots=True)
class _CompositionSink:
    block_id: str = "sink"
    material_inlets: Mapping[str, MaterialPort] = field(
        default_factory=lambda: MappingProxyType(
            {"inlet": MaterialPort("inlet", composition_required=True)}
        )
    )
    scalar_inlets: Mapping[str, ScalarPort] = field(default_factory=lambda: MappingProxyType({}))
    material_outlets: Mapping[str, MaterialPort] = field(
        default_factory=lambda: MappingProxyType({"outlet": MaterialPort("outlet")})
    )
    scalar_outlets: Mapping[str, ScalarPort] = field(default_factory=lambda: MappingProxyType({}))
    caller_parameters: tuple[str, ...] = ()
    profile_constants: tuple[str, ...] = ()

    def solve(self, material_inputs, scalar_inputs, caller_parameter_values, profile_constant_values) -> BlockResult:
        return BlockResult(material_outputs={"outlet": material_inputs["inlet"]})


def test_composition_requirement_is_explicit_and_047_remains_unknown() -> None:
    sink_flowsheet = ProcessFlowsheet(
        schema_version=1,
        model_identity="composition-test",
        semantic_unit_registry_identity="registry-test",
        blocks={"sink": _CompositionSink()},
        material_connections=(),
        scalar_connections=(),
        external_material_inputs=(ExternalMaterialInput("sink", "inlet", "feed"),),
        profile_constants={},
        result_assembler_identity="test-assembler",
    )
    _assert_kernel_error(
        "stream_composition_required",
        lambda: sink_flowsheet.execute(
            external_streams={"feed": MaterialStream(id="feed")},
            caller_parameters={"sink": {}},
        ),
    )

    execution = build_047_flowsheet().execute(
        external_streams={"loop_liquid": _stream(composition=None)},
        caller_parameters=_caller_parameters(),
    )
    assert execution.block_results["pump"].material_outputs["outlet"].composition is None


def test_047_graph_requires_dynamic_pressure_and_rejects_bad_ports_and_cycles() -> None:
    flowsheet = build_047_flowsheet()
    without_dynamic_pressure = tuple(
        connection
        for connection in flowsheet.scalar_connections
        if not (
            connection.source_block_id == "pipe"
            and connection.source_port == "dynamic_pressure"
            and connection.target_block_id == "fitting"
        )
    )
    _assert_kernel_error(
        "flowsheet_driver_missing",
        lambda: replace(flowsheet, scalar_connections=without_dynamic_pressure),
    )
    _assert_kernel_error(
        "flowsheet_scalar_port_unknown",
        lambda: replace(
            flowsheet,
            scalar_connections=(
                ScalarConnection("pipe", "not_a_port", "fitting", "dynamic_pressure"),
                *flowsheet.scalar_connections[1:],
            ),
        ),
    )
    _assert_kernel_error(
        "flowsheet_driver_duplicate",
        lambda: replace(
            flowsheet,
            scalar_connections=(
                *flowsheet.scalar_connections,
                ScalarConnection("pipe", "dynamic_pressure", "fitting", "dynamic_pressure"),
            ),
        ),
    )
    _assert_kernel_error(
        "topology_cycle",
        lambda: replace(
            flowsheet,
            material_connections=(
                *flowsheet.material_connections,
                MaterialConnection("pump", "outlet", "reservoir", "inlet"),
            ),
            external_material_inputs=(),
        ),
    )


def test_scalar_port_dimension_and_profile_constant_sets_are_exact() -> None:
    flowsheet = build_047_flowsheet()
    bad_fitting = Fitting(
        scalar_inlets=MappingProxyType(
            {"dynamic_pressure": ScalarPort("dynamic_pressure", "W", "power")}
        )
    )
    _assert_kernel_error(
        "flowsheet_scalar_port_incompatible",
        lambda: replace(
            flowsheet,
            blocks={**flowsheet.blocks, "fitting": bad_fitting},
        ),
    )
    _assert_kernel_error(
        "flowsheet_constants_invalid",
        lambda: replace(
            flowsheet,
            profile_constants={"standard_gravity": 9.80665, "hidden_constant": 1.0},
        ),
    )


def test_all_caller_scalars_are_validated_before_first_block_executes() -> None:
    calls: list[str] = []

    @dataclass(frozen=True, slots=True)
    class CountingBlock:
        block_id: str
        caller_parameters: tuple[str, ...]
        material_inlets: Mapping[str, MaterialPort] = field(default_factory=lambda: MappingProxyType({}))
        scalar_inlets: Mapping[str, ScalarPort] = field(default_factory=lambda: MappingProxyType({}))
        material_outlets: Mapping[str, MaterialPort] = field(default_factory=lambda: MappingProxyType({}))
        scalar_outlets: Mapping[str, ScalarPort] = field(default_factory=lambda: MappingProxyType({}))
        profile_constants: tuple[str, ...] = ()

        def solve(self, material_inputs, scalar_inputs, caller_parameter_values, profile_constant_values) -> BlockResult:
            calls.append(self.block_id)
            return BlockResult()

    flowsheet = ProcessFlowsheet(
        schema_version=1,
        model_identity="prevalidation-test",
        semantic_unit_registry_identity="registry-test",
        blocks={
            "first": CountingBlock("first", ()),
            "late": CountingBlock("late", ("value",)),
        },
        material_connections=(),
        scalar_connections=(),
        external_material_inputs=(),
        profile_constants={},
        result_assembler_identity="test-assembler",
    )
    _assert_kernel_error(
        "flowsheet_parameters_invalid",
        lambda: flowsheet.execute(
            external_streams={},
            caller_parameters={"first": {}, "late": {"value": math.inf}},
        ),
    )
    assert calls == []


def test_047_intermediates_are_owned_by_named_blocks() -> None:
    execution = build_047_flowsheet().execute(
        external_streams={"loop_liquid": _stream()},
        caller_parameters=_caller_parameters(),
    )
    assert execution.order == ("reservoir", "pipe", "fitting", "pump")

    pipe = execution.block_results["pipe"]
    fitting = execution.block_results["fitting"]
    pump = execution.block_results["pump"]
    diameter = 30.0 / 1000.0
    area = math.pi * diameter**2 / 4.0
    flow = 0.25 * area
    reynolds = 1025.0 * 0.25 * diameter / 0.0011
    friction = 0.3164 * reynolds**-0.25
    dynamic_pressure = 1025.0 * 0.25**2 / 2.0
    major_loss = friction * (20.0 / diameter) * dynamic_pressure
    minor_loss = 8.0 * dynamic_pressure

    assert pipe.scalar_outputs["hydraulic_area"].hex() == area.hex()
    assert pipe.scalar_outputs["circulation_flow"].hex() == flow.hex()
    assert pipe.scalar_outputs["reynolds_number"].hex() == reynolds.hex()
    assert pipe.scalar_outputs["dynamic_pressure"].hex() == dynamic_pressure.hex()
    assert pipe.scalar_outputs["major_pressure_loss"].hex() == major_loss.hex()
    assert pipe.diagnostics["friction_correlation"] == "blasius_smooth_pipe_v0"
    assert "friction_correlation" not in pipe.scalar_outputs
    assert fitting.scalar_outputs["minor_pressure_loss"].hex() == minor_loss.hex()
    assert pump.scalar_outputs["total_pressure_loss"].hex() == (major_loss + minor_loss).hex()
    assert build_047_flowsheet().profile_constants == {"standard_gravity": 9.80665}


@pytest.mark.parametrize(
    "stream",
    [
        MaterialStream(id="missing-density", volumetric_flow_m3_s=0.001),
        MaterialStream(id="missing-flow", density_kg_m3=1000.0),
    ],
)
def test_pump_requires_density_and_volumetric_flow(stream: MaterialStream) -> None:
    pump = Pump()
    _assert_kernel_error(
        "stream_requirement_missing",
        lambda: pump.solve(
            {"inlet": stream},
            {"major_pressure_loss": 1.0, "minor_pressure_loss": 1.0},
            {"pump_efficiency": 0.5},
            {"standard_gravity": 9.80665},
        ),
    )
