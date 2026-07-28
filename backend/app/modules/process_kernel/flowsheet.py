from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from math import isfinite
from types import MappingProxyType

try:
    from app.core.topology import TopologyError, deterministic_topological_order
except ModuleNotFoundError:  # bundled runner package
    from .topology import TopologyError, deterministic_topological_order
from .contracts import BlockResult, UnitOperation
from .errors import ProcessKernelError
from .streams import MaterialStream

MAX_PROCESS_BLOCKS = 64
MAX_PROCESS_CONNECTIONS = 256
_MATERIAL_STREAM_FIELDS = frozenset(
    {
        "id",
        "composition",
        "density_kg_m3",
        "dynamic_viscosity_Pa_s",
        "mass_flow_kg_s",
        "volumetric_flow_m3_s",
        "temperature_K",
        "pressure_Pa",
    }
)


@dataclass(frozen=True, slots=True)
class MaterialConnection:
    source_block_id: str
    source_port: str
    target_block_id: str
    target_port: str


@dataclass(frozen=True, slots=True)
class ScalarConnection:
    source_block_id: str
    source_port: str
    target_block_id: str
    target_port: str


@dataclass(frozen=True, slots=True)
class ExternalMaterialInput:
    target_block_id: str
    target_port: str
    stream_id: str


@dataclass(frozen=True, slots=True)
class ProcessExecutionResult:
    order: tuple[str, ...]
    block_results: Mapping[str, BlockResult]

    def __post_init__(self) -> None:
        object.__setattr__(self, "block_results", MappingProxyType(dict(self.block_results)))


@dataclass(frozen=True, slots=True)
class ProcessFlowsheet:
    schema_version: int
    model_identity: str
    semantic_unit_registry_identity: str
    blocks: Mapping[str, UnitOperation]
    material_connections: tuple[MaterialConnection, ...]
    scalar_connections: tuple[ScalarConnection, ...]
    external_material_inputs: tuple[ExternalMaterialInput, ...]
    profile_constants: Mapping[str, float]
    result_assembler_identity: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "blocks", MappingProxyType(dict(self.blocks)))
        object.__setattr__(self, "profile_constants", MappingProxyType(dict(self.profile_constants)))
        self.validate()

    def validate(self) -> tuple[str, ...]:
        if self.schema_version != 1:
            raise ProcessKernelError("flowsheet_schema_invalid", "Unsupported process flowsheet schema.")
        if not self.model_identity or not self.semantic_unit_registry_identity or not self.result_assembler_identity:
            raise ProcessKernelError("flowsheet_identity_invalid", "Flowsheet identities must be non-empty.")
        if not self.blocks or len(self.blocks) > MAX_PROCESS_BLOCKS:
            raise ProcessKernelError("flowsheet_block_limit", "Flowsheet block count is outside bounds.")
        for block_id, block in self.blocks.items():
            if block_id != block.block_id:
                raise ProcessKernelError("flowsheet_block_identity_mismatch", "Block map key must equal block id.")
            self._validate_material_port_contract(block)

        declared_constants = {
            constant_name
            for block in self.blocks.values()
            for constant_name in block.profile_constants
        }
        if set(self.profile_constants) != declared_constants:
            raise ProcessKernelError(
                "flowsheet_constants_invalid",
                "Profile constants must match the exact declared block constant set.",
            )
        _require_finite_scalars(self.profile_constants, "flowsheet_constants_invalid")

        total_connections = (
            len(self.material_connections) + len(self.scalar_connections) + len(self.external_material_inputs)
        )
        if total_connections > MAX_PROCESS_CONNECTIONS:
            raise ProcessKernelError("flowsheet_connection_limit", "Flowsheet connection count exceeds bounds.")

        material_drivers: dict[tuple[str, str], str] = {}
        scalar_drivers: dict[tuple[str, str], str] = {}
        graph_edges: list[tuple[str, str]] = []

        for connection in self.material_connections:
            source = self._block(connection.source_block_id)
            target = self._block(connection.target_block_id)
            source_port = source.material_outlets.get(connection.source_port)
            target_port = target.material_inlets.get(connection.target_port)
            if source_port is None or target_port is None:
                raise ProcessKernelError("flowsheet_material_port_unknown", "Material connection references an unknown port.")
            key = (connection.target_block_id, connection.target_port)
            _record_driver(material_drivers, key, f"{connection.source_block_id}.{connection.source_port}")
            graph_edges.append((connection.source_block_id, connection.target_block_id))

        external_stream_ids: set[str] = set()
        for external in self.external_material_inputs:
            target = self._block(external.target_block_id)
            if external.target_port not in target.material_inlets:
                raise ProcessKernelError("flowsheet_material_port_unknown", "External material input targets an unknown port.")
            if not external.stream_id or external.stream_id in external_stream_ids:
                raise ProcessKernelError("flowsheet_external_stream_invalid", "External stream ids must be unique.")
            external_stream_ids.add(external.stream_id)
            _record_driver(material_drivers, (external.target_block_id, external.target_port), external.stream_id)

        for connection in self.scalar_connections:
            source = self._block(connection.source_block_id)
            target = self._block(connection.target_block_id)
            source_port = source.scalar_outlets.get(connection.source_port)
            target_port = target.scalar_inlets.get(connection.target_port)
            if source_port is None or target_port is None:
                raise ProcessKernelError("flowsheet_scalar_port_unknown", "Scalar connection references an unknown port.")
            if (
                source_port.unit != target_port.unit
                or source_port.physical_dimension != target_port.physical_dimension
                or source_port.semantic_basis != target_port.semantic_basis
            ):
                raise ProcessKernelError("flowsheet_scalar_port_incompatible", "Connected scalar ports are incompatible.")
            key = (connection.target_block_id, connection.target_port)
            _record_driver(scalar_drivers, key, f"{connection.source_block_id}.{connection.source_port}")
            graph_edges.append((connection.source_block_id, connection.target_block_id))

        for block_id, block in self.blocks.items():
            for port_name in block.material_inlets:
                if (block_id, port_name) not in material_drivers:
                    raise ProcessKernelError("flowsheet_driver_missing", "Material inlet has no driver.")
            for port_name in block.scalar_inlets:
                if (block_id, port_name) not in scalar_drivers:
                    raise ProcessKernelError("flowsheet_driver_missing", "Scalar inlet has no driver.")

        try:
            return deterministic_topological_order(
                self.blocks,
                graph_edges,
                max_nodes=MAX_PROCESS_BLOCKS,
                max_edges=MAX_PROCESS_CONNECTIONS,
            )
        except TopologyError as exc:
            raise ProcessKernelError(exc.code, exc.message) from exc

    def execute(
        self,
        *,
        external_streams: Mapping[str, MaterialStream],
        caller_parameters: Mapping[str, Mapping[str, float]],
    ) -> ProcessExecutionResult:
        order = self.validate()
        expected_external = {item.stream_id for item in self.external_material_inputs}
        if set(external_streams) != expected_external:
            raise ProcessKernelError("flowsheet_external_inputs_invalid", "External stream set does not match the profile.")
        if any(not isinstance(stream, MaterialStream) for stream in external_streams.values()):
            raise ProcessKernelError("flowsheet_external_inputs_invalid", "External inputs must be material streams.")
        if set(caller_parameters) != set(self.blocks):
            raise ProcessKernelError("flowsheet_parameters_invalid", "Caller parameter block set does not match the profile.")
        for block_id, block in self.blocks.items():
            values = caller_parameters[block_id]
            if set(values) != set(block.caller_parameters):
                raise ProcessKernelError(
                    "flowsheet_parameters_invalid",
                    "Caller parameters must match each block's exact declared set.",
                )
            _require_finite_scalars(values, "flowsheet_parameters_invalid")

        self._preflight_material_requirements(order, external_streams)

        results: dict[str, BlockResult] = {}
        for block_id in order:
            block = self.blocks[block_id]
            material_inputs: dict[str, MaterialStream] = {}
            scalar_inputs: dict[str, float] = {}

            for external in self.external_material_inputs:
                if external.target_block_id == block_id:
                    material_inputs[external.target_port] = external_streams[external.stream_id]
            for connection in self.material_connections:
                if connection.target_block_id == block_id:
                    source_result = results[connection.source_block_id]
                    material_inputs[connection.target_port] = source_result.material_outputs[connection.source_port]
            for connection in self.scalar_connections:
                if connection.target_block_id == block_id:
                    source_result = results[connection.source_block_id]
                    scalar_inputs[connection.target_port] = source_result.scalar_outputs[connection.source_port]

            for port_name, port in block.material_inlets.items():
                stream = material_inputs[port_name]
                stream.require(*port.required_stream_fields)
                if port.composition_required and stream.composition is None:
                    raise ProcessKernelError(
                        "stream_composition_required",
                        "Block requires a known material composition.",
                    )

            constants = {name: self.profile_constants[name] for name in block.profile_constants}
            result = block.solve(material_inputs, scalar_inputs, caller_parameters[block_id], constants)
            if set(result.material_outputs) != set(block.material_outlets):
                raise ProcessKernelError("block_material_outputs_invalid", "Block material outputs do not match its contract.")
            if set(result.scalar_outputs) != set(block.scalar_outlets):
                raise ProcessKernelError("block_scalar_outputs_invalid", "Block scalar outputs do not match its contract.")
            if any(not isinstance(stream, MaterialStream) for stream in result.material_outputs.values()):
                raise ProcessKernelError("block_material_outputs_invalid", "Block material outputs must be material streams.")
            self._validate_material_outputs(block, material_inputs, result.material_outputs)
            _require_finite_scalars(result.scalar_outputs, "block_scalar_outputs_invalid")
            results[block_id] = result

        return ProcessExecutionResult(order=order, block_results=results)

    def _validate_material_port_contract(self, block: UnitOperation) -> None:
        for name, port in block.material_inlets.items():
            if port.name != name or port.source_input_port is not None or port.provided_stream_fields:
                raise ProcessKernelError(
                    "flowsheet_material_port_invalid",
                    "Material inlet metadata is invalid.",
                )
            _validate_stream_field_names(port.required_stream_fields)
        for name, port in block.material_outlets.items():
            if port.name != name:
                raise ProcessKernelError("flowsheet_material_port_invalid", "Material output metadata is invalid.")
            _validate_stream_field_names(port.required_stream_fields)
            _validate_stream_field_names(port.provided_stream_fields)
            if port.source_input_port is not None and port.source_input_port not in block.material_inlets:
                raise ProcessKernelError(
                    "flowsheet_material_port_invalid",
                    "Material output source input port is unknown.",
                )

    def _preflight_material_requirements(
        self,
        order: tuple[str, ...],
        external_streams: Mapping[str, MaterialStream],
    ) -> None:
        output_fields: dict[tuple[str, str], frozenset[str]] = {}
        for block_id in order:
            block = self.blocks[block_id]
            input_fields: dict[str, frozenset[str]] = {}
            for external in self.external_material_inputs:
                if external.target_block_id == block_id:
                    input_fields[external.target_port] = _known_stream_fields(external_streams[external.stream_id])
            for connection in self.material_connections:
                if connection.target_block_id == block_id:
                    input_fields[connection.target_port] = output_fields[
                        (connection.source_block_id, connection.source_port)
                    ]

            for port_name, port in block.material_inlets.items():
                known = input_fields[port_name]
                missing = set(port.required_stream_fields) - known
                if missing:
                    field_name = sorted(missing)[0]
                    raise ProcessKernelError(
                        "stream_requirement_missing",
                        f"Stream field is required: {field_name}.",
                        context={"field": field_name},
                    )
                if port.composition_required and "composition" not in known:
                    raise ProcessKernelError(
                        "stream_composition_required",
                        "Block requires a known material composition.",
                    )

            for output_name, port in block.material_outlets.items():
                known = set(port.provided_stream_fields)
                if port.source_input_port is not None:
                    known.update(input_fields[port.source_input_port])
                output_fields[(block_id, output_name)] = frozenset(known)

    def _validate_material_outputs(
        self,
        block: UnitOperation,
        material_inputs: Mapping[str, MaterialStream],
        material_outputs: Mapping[str, MaterialStream],
    ) -> None:
        for output_name, port in block.material_outlets.items():
            output_fields = _known_stream_fields(material_outputs[output_name])
            missing_provided = set(port.provided_stream_fields) - output_fields
            if missing_provided:
                raise ProcessKernelError(
                    "block_material_outputs_invalid",
                    "Block material output omitted a declared provided stream field.",
                )
            if port.source_input_port is not None:
                source_fields = _known_stream_fields(material_inputs[port.source_input_port])
                if not source_fields.issubset(output_fields):
                    raise ProcessKernelError(
                        "block_material_outputs_invalid",
                        "Block material output did not preserve its declared source stream fields.",
                    )

    def _block(self, block_id: str) -> UnitOperation:
        block = self.blocks.get(block_id)
        if block is None:
            raise ProcessKernelError("flowsheet_block_unknown", "Connection references an unknown block.")
        return block


def _known_stream_fields(stream: MaterialStream) -> frozenset[str]:
    fields = {"id"}
    for name in _MATERIAL_STREAM_FIELDS - {"id"}:
        if getattr(stream, name) is not None:
            fields.add(name)
    return frozenset(fields)


def _validate_stream_field_names(field_names: tuple[str, ...]) -> None:
    if len(field_names) != len(set(field_names)) or any(name not in _MATERIAL_STREAM_FIELDS for name in field_names):
        raise ProcessKernelError("flowsheet_material_port_invalid", "Material port stream fields are invalid.")


def _record_driver(drivers: dict[tuple[str, str], str], key: tuple[str, str], driver: str) -> None:
    if key in drivers:
        raise ProcessKernelError("flowsheet_driver_duplicate", "Input port has more than one driver.")
    drivers[key] = driver


def _require_finite_scalars(values: Mapping[str, object], code: str) -> None:
    for name, value in values.items():
        if isinstance(value, bool) or not isinstance(value, int | float) or not isfinite(float(value)):
            raise ProcessKernelError(code, f"Scalar value must be finite: {name}.")
