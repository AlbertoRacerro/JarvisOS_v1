"""Strict, bounded content models for Process dynamic scenarios (spec 172)."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

MAX_DURATION_S = 120 * 86400
MAX_OUTPUT_POINTS = 20_000
MAX_EVENTS = 1_000
MAX_CONTROLLERS = 16
MAX_PARTICIPATING_PBRS = 8
MAX_DWSIM_SAMPLES = 200
MIN_CADENCE_S = 60


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, allow_inf_nan=False)


class ScheduleEvent(StrictModel):
    type: Literal["inoculation", "feed_change", "setpoint_change", "harvest", "dilution"]
    time_s: float = Field(ge=0)
    unit: str | None = None
    stream: str | None = None
    target: str | None = None
    value: float | str | dict[str, Any] | None = None
    value_unit: Literal["kg/m3", "m3/s", "1"] | None = None
    fraction: float | None = Field(default=None, ge=0, le=1)
    medium: dict[str, float] | None = None
    observed: str | None = None
    threshold: float | None = None
    threshold_unit: Literal["kg/m3"] | None = None
    direction: Literal["above", "below"] | None = None
    hysteresis: float | None = Field(default=None, ge=0)
    every_s: float | None = Field(default=None, gt=0)
    count: int | None = Field(default=None, ge=1, le=MAX_EVENTS)
    end_s: float | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def repeated_bounded(self) -> ScheduleEvent:
        if self.every_s is not None and self.count is None and self.end_s is None:
            raise ValueError("repeated event requires count or end_s")
        if (self.observed is None) != (self.threshold is None):
            raise ValueError("conditional event requires observed and threshold")
        if self.observed is not None and (self.direction is None or self.hysteresis is None):
            raise ValueError("conditional event requires direction and hysteresis")
        if self.observed is not None and self.threshold_unit != "kg/m3":
            raise ValueError("conditional threshold requires kg/m3 unit")
        return self


class Schedule(StrictModel):
    id: str = Field(pattern=r"^[a-z][a-z0-9_-]{0,39}$")
    events: list[ScheduleEvent] = Field(default_factory=list, max_length=MAX_EVENTS)


class Controller(StrictModel):
    id: str = Field(pattern=r"^[a-z][a-z0-9_-]{0,39}$")
    type: Literal["onoff", "pi", "turbidostat"]
    measurement: str
    unit: str
    actuator: str
    cadence_s: float = Field(ge=MIN_CADENCE_S)
    setpoint: float
    lower: float = 0
    upper: float = 1
    hysteresis: float = Field(default=0, ge=0)
    kp: float = 0
    ki: float = 0
    output: float = 0
    direction: Literal["above", "below"] = "above"

    @model_validator(mode="after")
    def output_bounds(self) -> Controller:
        if self.lower > self.upper or not self.lower <= self.output <= self.upper:
            raise ValueError("controller output and bounds are inconsistent")
        return self


class Scenario(StrictModel):
    id: str = Field(pattern=r"^[a-z][a-z0-9_-]{0,39}$")
    units: list[str] = Field(min_length=1, max_length=MAX_PARTICIPATING_PBRS)
    profiles: list[dict[str, str]] = Field(min_length=1, max_length=8)
    schedule_id: str | None = None
    controllers: list[str] = Field(default_factory=list, max_length=MAX_CONTROLLERS)
    start_utc: str
    end_utc: str
    output_cadence_s: float = Field(ge=MIN_CADENCE_S)
    controller_cadence_s: float = Field(default=300, ge=MIN_CADENCE_S)
    fidelity: Literal["T1"] = "T1"
    solver_method: Literal["BDF", "Adams"] = "BDF"
    rtol: float = Field(default=1e-6, gt=0, lt=1)
    atol: float = Field(default=1e-9, gt=0)
    temperature_source: Literal["sea_temperature", "air_temperature", "unit_mean"]
    par_scale: float = Field(default=1.0, ge=0)
    par_from_ghi_factor: float | None = Field(default=None, gt=0)
    downstream_cadence_s: float | None = Field(default=None, ge=MIN_CADENCE_S)
    initial: dict[str, dict[str, float]] = Field(default_factory=dict)
    feed_flows: dict[str, float] = Field(default_factory=dict)

    @field_validator("start_utc", "end_utc")
    @classmethod
    def utc_aware(cls, value: str) -> str:
        from datetime import datetime

        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            raise ValueError("timestamps must include a UTC offset")
        return value
