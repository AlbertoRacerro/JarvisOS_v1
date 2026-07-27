from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace
from types import MappingProxyType

import pytest

from app.modules.process_kernel.contracts import BlockResult, MaterialPort, ScalarPort
from app.modules.process_kernel.errors import ProcessKernelError
from app.modules.process_kernel.flowsheet import (
    ExternalMaterialInput,
    MaterialConnection,
    ProcessFlowsheet,
)
from app.modules.process_kernel.streams import MaterialStream


class _CountingPassThrough:
    def __init__(
        self,
        block_id: str,
        calls: list[str],
        *,
        required_stream_fields: tuple[str, ...] = (),
    ) -> None:
        self.block_id = block_id
        self.calls = calls
        self.material_inlets: Mapping[str, MaterialPort] = MappingProxyType(
            {
                "inlet": MaterialPort(
                    "inlet",
                    required_stream_fields=required_stream_fields,
                )
            }
        )
        self.scalar_inlets: Mapping[str, ScalarPort] = MappingProxyType({})
        self.material_outlets: Mapping[str, MaterialPort] = MappingProxyType(
            {"outlet": MaterialPort("outlet", source_input_port="inlet")}
        )
        self.scalar_outlets: Mapping[str, ScalarPort] = MappingProxyType({})
        self.caller_parameters: tuple[str, ...] = ()
        self.profile_constants: tuple[str, ...] = ()

    def solve(
        self,
        material_inputs: Mapping[str, MaterialStream],
        scalar_inputs: Mapping[str, float],
        caller_parameter_values: Mapping[str, float],
        profile_constant_values: Mapping[str, float],
    ) -> BlockResult:
        self.calls.append(self.block_id)
        return BlockResult(material_outputs={"outlet": replace(material_inputs["inlet"])})


def test_late_material_requirement_fails_before_any_block_solves() -> None:
    calls: list[str] = []
    flowsheet = ProcessFlowsheet(
        schema_version=1,
        model_identity="material-preflight-test",
        semantic_unit_registry_identity="registry-test",
        blocks={
            "first": _CountingPassThrough("first", calls),
            "sink": _CountingPassThrough(
                "sink",
                calls,
                required_stream_fields=("density_kg_m3",),
            ),
        },
        material_connections=(MaterialConnection("first", "outlet", "sink", "inlet"),),
        scalar_connections=(),
        external_material_inputs=(ExternalMaterialInput("first", "inlet", "feed"),),
        profile_constants={},
        result_assembler_identity="test-assembler",
    )

    with pytest.raises(ProcessKernelError) as exc_info:
        flowsheet.execute(
            external_streams={"feed": MaterialStream(id="feed")},
            caller_parameters={"first": {}, "sink": {}},
        )

    assert exc_info.value.code == "stream_requirement_missing"
    assert exc_info.value.context == {"field": "density_kg_m3"}
    assert calls == []
