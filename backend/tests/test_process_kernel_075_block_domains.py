from __future__ import annotations

import math

import pytest

from app.modules.process_kernel.blocks import Fitting, Pipe, Pump, Reservoir
from app.modules.process_kernel.errors import ProcessKernelError
from app.modules.process_kernel.streams import MaterialStream


def _stream() -> MaterialStream:
    return MaterialStream(
        id="loop_liquid",
        density_kg_m3=1000.0,
        dynamic_viscosity_Pa_s=0.001,
        volumetric_flow_m3_s=0.001,
    )


def _assert_error(code: str, operation) -> None:
    with pytest.raises(ProcessKernelError) as exc_info:
        operation()
    assert exc_info.value.code == code


@pytest.mark.parametrize("value", [-1.0, math.inf, True])
def test_reservoir_rejects_invalid_volume(value: object) -> None:
    _assert_error(
        "reservoir_parameters_invalid",
        lambda: Reservoir().solve(
            {"inlet": _stream()},
            {},
            {"reservoir_liquid_volume": value},
            {},
        ),
    )


@pytest.mark.parametrize(
    "parameters",
    [
        {
            "tube_length": 0.0,
            "tube_inner_diameter": 30.0,
            "tube_outer_diameter": 36.0,
            "target_liquid_velocity": 0.25,
        },
        {
            "tube_length": 20.0,
            "tube_inner_diameter": 0.0,
            "tube_outer_diameter": 36.0,
            "target_liquid_velocity": 0.25,
        },
        {
            "tube_length": 20.0,
            "tube_inner_diameter": 30.0,
            "tube_outer_diameter": 25.0,
            "target_liquid_velocity": 0.25,
        },
        {
            "tube_length": 20.0,
            "tube_inner_diameter": 30.0,
            "tube_outer_diameter": 36.0,
            "target_liquid_velocity": 0.0,
        },
        {
            "tube_length": math.nan,
            "tube_inner_diameter": 30.0,
            "tube_outer_diameter": 36.0,
            "target_liquid_velocity": 0.25,
        },
    ],
)
def test_pipe_rejects_invalid_geometry_and_operating_values(parameters: dict[str, float]) -> None:
    _assert_error(
        "pipe_parameters_invalid",
        lambda: Pipe().solve({"inlet": _stream()}, {}, parameters, {}),
    )


@pytest.mark.parametrize(
    ("dynamic_pressure", "coefficient", "expected_code"),
    [
        (-1.0, 1.0, "fitting_scalar_inputs_invalid"),
        (1.0, -1.0, "fitting_parameters_invalid"),
        (math.inf, 1.0, "fitting_scalar_inputs_invalid"),
    ],
)
def test_fitting_rejects_negative_or_nonfinite_inputs(
    dynamic_pressure: float,
    coefficient: float,
    expected_code: str,
) -> None:
    _assert_error(
        expected_code,
        lambda: Fitting().solve(
            {"inlet": _stream()},
            {"dynamic_pressure": dynamic_pressure},
            {"minor_loss_coefficient": coefficient},
            {},
        ),
    )


@pytest.mark.parametrize(
    ("major_loss", "minor_loss", "efficiency", "gravity", "expected_code"),
    [
        (-1.0, 1.0, 0.5, 9.80665, "pump_scalar_inputs_invalid"),
        (1.0, -1.0, 0.5, 9.80665, "pump_scalar_inputs_invalid"),
        (1.0, 1.0, 0.0, 9.80665, "pump_parameters_invalid"),
        (1.0, 1.0, 1.1, 9.80665, "pump_parameters_invalid"),
        (1.0, 1.0, 0.5, 0.0, "pump_constants_invalid"),
        (math.inf, 1.0, 0.5, 9.80665, "pump_scalar_inputs_invalid"),
    ],
)
def test_pump_rejects_invalid_losses_efficiency_and_gravity(
    major_loss: float,
    minor_loss: float,
    efficiency: float,
    gravity: float,
    expected_code: str,
) -> None:
    _assert_error(
        expected_code,
        lambda: Pump().solve(
            {"inlet": _stream()},
            {"major_pressure_loss": major_loss, "minor_pressure_loss": minor_loss},
            {"pump_efficiency": efficiency},
            {"standard_gravity": gravity},
        ),
    )
