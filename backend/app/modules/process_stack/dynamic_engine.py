"""Coupled Tier 1 transient photobioreactor engine (spec 172)."""

from __future__ import annotations

import bisect
import hashlib
import json
import math
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Literal

import numpy as np

from app.modules.process_stack import draft, pbr_unit
from app.modules.process_stack.dynamic_models import (
    MAX_CONTROLLERS,
    MAX_DURATION_S,
    MAX_EVENTS,
    MAX_OUTPUT_POINTS,
    Controller,
    Scenario,
    Schedule,
)

EVALUATOR_VERSION = "process_dynamic_t1/1"
MAX_DWSIM_SAMPLES = 200


class DynamicError(ValueError):
    def __init__(self, code: str, message: str, detail: dict[str, Any] | None = None) -> None:
        super().__init__(message[:600])
        self.code, self.message, self.detail = code, message[:600], detail or {}


@dataclass(frozen=True)
class Snapshot:
    payload: dict[str, Any]
    digest: str


@dataclass(frozen=True)
class EngineResult:
    status: Literal["succeeded", "failed", "cancelled"]
    error: dict[str, Any] | None
    series: dict[str, np.ndarray]
    manifest: dict[str, Any]


def _validate_downstream_boundary_specs(
    boundary_streams: dict[str, dict[str, Any]], carrier_spec: dict[str, Any],
) -> None:
    missing_by_stream: dict[str, list[str]] = {}
    for boundary in boundary_streams.values():
        spec = boundary.get("spec", {})
        missing = [field for field in ("temperature", "pressure", "composition")
                   if not spec.get(field) and not carrier_spec.get(field)]
        if missing:
            missing_by_stream[boundary["tag"]] = missing
    if missing_by_stream:
        raise DynamicError(
            "DOWNSTREAM_BOUNDARY_STATE_UNDECLARED",
            "Downstream boundary streams require declared temperature, pressure and composition.",
            {"streams": missing_by_stream},
        )


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def _stamp(value: str) -> float:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("timestamp must include an offset")
    return parsed.astimezone(UTC).timestamp()


def _stream_flow(stream: dict[str, Any], declared: dict[str, float]) -> float | None:
    """Resolve a boundary culture feed's m³/s flow from an explicit override or kg/s."""
    tag = stream["tag"]
    if tag in declared:
        value = float(declared[tag])
    else:
        mass = (stream.get("spec", {}).get("mass_flow") or {}).get("si")
        value = float(mass) / 1000.0 if mass is not None else math.nan
    return value if math.isfinite(value) and value >= 0 else None


def _splitter_ratios(unit: dict[str, Any], outlet_count: int) -> list[float]:
    params = unit.get("params", {})
    if "split_ratios" in params:
        values = params["split_ratios"]
        ratios = [float(value.get("si", value)) if isinstance(value, dict) else float(value)
                  for _, value in sorted(values.items())]
    else:
        ratios = [float((params.get(f"split_ratio_{index}") or {}).get("si", 0.5)) for index in (1, 2)]
        if outlet_count == 3:
            ratios.append(1.0 - sum(ratios))
    if (len(ratios) != outlet_count or any(value < 0 or value > 1 for value in ratios)
            or abs(sum(ratios) - 1.0) > 1e-6):
        raise DynamicError("SPLITTER_RATIOS_INVALID", "Splitter ratios must be nonnegative and sum to one.",
                           {"unit": unit.get("tag")})
    return ratios


def _validate_events(
    events: list[dict[str, Any]], units: list[dict[str, Any]], topology: dict[str, Any],
    controller_ids: list[str],
) -> None:
    unit_tags = {item["tag"] for item in units}
    feeds = {stream["tag"] for stream in topology["streams"] if stream.get("source") is None}
    splitters = {unit["tag"] for unit in topology["units"] if unit.get("type") == "Splitter"}
    for event in events:
        observed = event.get("observed")
        if observed:
            parts = observed.split(".")
            if len(parts) != 2 or parts[0] not in unit_tags or parts[1] not in {"X", "N", "O2"}:
                raise DynamicError("UNSUPPORTED_MEASUREMENT", "Conditional event observes an unsupported channel.",
                                   {"observed": observed})
            if event.get("threshold_unit") != "kg/m3" or event.get("direction") not in {"above", "below"}:
                raise DynamicError("EVENT_UNIT_INVALID", "Conditional threshold requires kg/m3 and a direction.")
        kind = event["type"]
        if kind in {"inoculation", "harvest"}:
            if event.get("unit") not in unit_tags:
                raise DynamicError("EVENT_TARGET_INVALID", "Event unit is not participating.",
                                   {"unit": event.get("unit")})
        if kind == "harvest":
            if event.get("fraction") is None:
                raise DynamicError("EVENT_VALUE_INVALID", "Harvest requires a fraction.")
        elif kind == "inoculation":
            if event.get("value_unit") != "kg/m3":
                raise DynamicError("EVENT_UNIT_INVALID", "Inoculation concentration requires kg/m3.")
            value = event.get("value")
            if isinstance(value, dict) and (not value or set(value) - {"X", "N", "O2"}):
                raise DynamicError("EVENT_VALUE_INVALID", "Inoculation has unsupported concentration fields.")
            values = value.values() if isinstance(value, dict) else [value]
            if any(not isinstance(v, (int, float)) or not math.isfinite(v) or v < 0 for v in values):
                raise DynamicError("EVENT_VALUE_INVALID", "Inoculation requires finite nonnegative concentrations.")
        elif kind in {"feed_change", "dilution"}:
            target = event.get("target") or ""
            if target.startswith("splitter:"):
                if target.partition(":")[2] not in splitters or kind != "dilution":
                    raise DynamicError("EVENT_TARGET_INVALID", "Event splitter is not participating.")
            elif (event.get("stream") or target.removeprefix("feed:")) not in feeds:
                raise DynamicError("EVENT_TARGET_INVALID", "Event feed is not a participating boundary stream.")
            value = event.get("value")
            expected_unit = "1" if target.startswith("splitter:") else "m3/s"
            if not isinstance(value, dict) and event.get("value_unit") != expected_unit:
                raise DynamicError("EVENT_UNIT_INVALID", f"Event value requires {expected_unit}.")
            if isinstance(value, dict):
                if set(value) - {"flow_m3_s", "culture", "culture_unit"} or not value:
                    raise DynamicError("EVENT_VALUE_INVALID", "Feed change has unsupported fields.")
                values = [value["flow_m3_s"]] if "flow_m3_s" in value else []
                culture = value.get("culture", {})
                if not isinstance(culture, dict) or set(culture) - {"X", "N", "O2"}:
                    raise DynamicError("EVENT_VALUE_INVALID", "Feed culture has unsupported fields.")
                if culture and value.get("culture_unit") != "kg/m3":
                    raise DynamicError("EVENT_UNIT_INVALID", "Feed culture requires kg/m3.")
                values.extend(culture.values())
            else:
                values = [value]
            if any(not isinstance(v, (int, float)) or not math.isfinite(v) or v < 0 for v in values):
                raise DynamicError("EVENT_VALUE_INVALID", "Feed/dilution values must be finite and nonnegative.")
            if target.startswith("splitter:") and not 0 <= float(value) <= 1:
                raise DynamicError("EVENT_VALUE_INVALID", "Splitter ratio must be in [0,1].")
        elif kind == "setpoint_change":
            if event.get("value_unit") != "kg/m3":
                raise DynamicError("EVENT_UNIT_INVALID", "Controller setpoint requires kg/m3.")
            if event.get("target") not in controller_ids:
                raise DynamicError("EVENT_TARGET_INVALID", "Setpoint controller is not participating.")
            value = event.get("value")
            if not isinstance(value, (int, float)) or not math.isfinite(value):
                raise DynamicError("EVENT_VALUE_INVALID", "Setpoint must be finite.")


def _topology(document: dict[str, Any], units: list[dict[str, Any]], scenario: dict[str, Any]) -> dict[str, Any]:
    """Build a bounded T1 stream network and solve its steady volumetric flow balance."""
    objects = document["objects"]
    selected = {item["unit"]["id"] for item in units}
    streams = [
        value for value in objects.values() if value.get("kind") == "stream" and value.get("type") != "EnergyStream"
    ]
    by_id = {key: value for key, value in objects.items() if value.get("kind") == "unit"}
    active_ids = set(selected)
    frontier = list(selected)
    while frontier:
        current = frontier.pop()
        for stream in streams:
            source = (stream.get("source") or {}).get("unit")
            target = (stream.get("target") or {}).get("unit")
            if current == source:
                neighbor = target
            elif current == target:
                neighbor = source
            else:
                continue
            if neighbor is None or neighbor == current:
                continue
            candidate = by_id.get(neighbor, {})
            if candidate.get("type") not in {
                "PhotobioreactorT1", "Mixer", "Splitter", "Pump", "Recycle", "SpecifiedSeparator"
            }:
                if current == target:
                    raise DynamicError(
                        "UNSUPPORTED_TOPOLOGY",
                        "A non-participating unit cannot feed the T1 network.",
                        {"unit": candidate.get("tag")},
                    )
                # A product stream can cross into the optional downstream DWSIM sampler.
                continue
            if neighbor not in active_ids:
                active_ids.add(neighbor)
                frontier.append(neighbor)
    active_units = {key: by_id[key] for key in active_ids}
    relevant: list[dict[str, Any]] = []
    for stream in streams:
        source, target = stream.get("source"), stream.get("target")
        if (source and source.get("unit") in active_units) or (target and target.get("unit") in active_units):
            relevant.append(stream)
    for item in active_units.values():
        if item.get("type") == "Splitter" and item.get("mode") != "split_ratios":
            raise DynamicError(
                "SPLITTER_FLOW_SPEC_UNSUPPORTED",
                "Dynamic T1 supports split_ratios mode only.",
                {"unit": item.get("tag")},
            )
    # Unknown stream Q values obey unit balances; splitter outlet ratios add independent equations.
    n = len(relevant)
    index = {stream["id"]: i for i, stream in enumerate(relevant)}
    equations: list[np.ndarray] = []
    rhs: list[float] = []
    feeds: dict[str, dict[str, float]] = {}
    for stream in relevant:
        if stream.get("source") is None:
            culture = stream.get("spec", {}).get("culture")
            if culture is None:
                raise DynamicError(
                    "CULTURE_FEED_REQUIRED",
                    "Every dynamic boundary feed needs a culture composition.",
                    {"stream": stream["tag"]},
                )
            flow = _stream_flow(stream, scenario.get("feed_flows", {}))
            if flow is None:
                raise DynamicError(
                    "FEED_FLOW_REQUIRED",
                    "Boundary feed needs a declared volumetric flow or mass flow.",
                    {"stream": stream["tag"]},
                )
            row = np.zeros(n)
            row[index[stream["id"]]] = 1
            equations.append(row)
            rhs.append(flow)
            feeds[stream["id"]] = {
                name: float((culture.get(key) or {}).get("si", 0.0))
                for name, key in (("X", "biomass"), ("N", "nitrogen"), ("O2", "oxygen"))
            }
        elif stream.get("source", {}).get("unit") not in active_units:
            raise DynamicError("UNSUPPORTED_TOPOLOGY", "A boundary product cannot be reintroduced as an internal feed.")
    for key, unit in active_units.items():
        incoming = [s for s in relevant if (s.get("target") or {}).get("unit") == key]
        outgoing = [s for s in relevant if (s.get("source") or {}).get("unit") == key]
        outgoing.sort(key=lambda stream: (stream.get("source") or {}).get("port", 0))
        if not incoming or not outgoing:
            if key in selected:
                raise DynamicError(
                    "ZERO_THROUGHFLOW", "Participating PBR must have inlet and outlet streams.", {"unit": unit["tag"]}
                )
            continue
        if unit.get("type") in {"Pump", "Recycle"} and (len(incoming) != 1 or len(outgoing) != 1):
            raise DynamicError("UNIT_TOPOLOGY_INVALID", "Pump and Recycle require one inlet and one outlet.",
                               {"unit": unit["tag"]})
        row = np.zeros(n)
        for stream in incoming:
            row[index[stream["id"]]] += 1
        for stream in outgoing:
            row[index[stream["id"]]] -= 1
        equations.append(row)
        rhs.append(0.0)
        if unit.get("type") == "SpecifiedSeparator":
            params = unit.get("params", {})
            recovery = float((params.get("biomass_recovery") or {}).get("si", 90.0)) / 100.0
            factor = float((params.get("concentration_factor") or {}).get("si", 10.0))
            if len(incoming) != 1 or len(outgoing) != 2 or not 0 < recovery <= 1 or factor <= 1:
                raise DynamicError(
                    "SEPARATOR_TOPOLOGY_INVALID",
                    "Dynamic SpecifiedSeparator requires one inlet, two outlets, valid recovery and factor.",
                    {"unit": unit["tag"]},
                )
            for stream, ratio in zip(outgoing, (recovery / factor, 1.0 - recovery / factor), strict=True):
                row = np.zeros(n)
                row[index[stream["id"]]] = 1
                row[index[incoming[0]["id"]]] = -ratio
                equations.append(row)
                rhs.append(0.0)
        elif unit.get("type") == "Splitter":
            ratio_values = _splitter_ratios(unit, len(outgoing))
            for stream, ratio in zip(outgoing, ratio_values, strict=True):
                row = np.zeros(n)
                row[index[stream["id"]]] = 1
                for inlet in incoming:
                    row[index[inlet["id"]]] -= ratio
                equations.append(row)
                rhs.append(0.0)
    if not equations:
        raise DynamicError("TOPOLOGY_EMPTY", "No dynamic T1 stream topology is connected.")
    matrix, values = np.vstack(equations), np.asarray(rhs)
    flows, *_ = np.linalg.lstsq(matrix, values, rcond=None)
    if np.max(np.abs(matrix @ flows - values)) > 1e-8 or np.any(flows < -1e-10):
        raise DynamicError("FLOW_BALANCE_UNSOLVED", "Dynamic volumetric flow balance is inconsistent.")
    flow_map = {stream["id"]: max(0.0, float(flows[index[stream["id"]]])) for stream in relevant}
    for item in units:
        key = item["unit"]["id"]
        qin = sum(flow_map[s["id"]] for s in relevant if (s.get("target") or {}).get("unit") == key)
        if qin <= 0:
            raise DynamicError("ZERO_THROUGHFLOW", "Participating PBR has zero throughflow.", {"unit": item["tag"]})
    return {"units": list(active_units.values()), "streams": relevant, "flows": flow_map, "feeds": feeds}


def prepare(workspace_id: str, draft_id: str, scenario_id: str) -> Snapshot:
    """Resolve immutable draft/card/profile inputs and reject unsupported topology pre-worker."""
    try:
        directory = draft.draft_dir(workspace_id, draft_id)
        head = draft._head(directory)
        revision = draft.load_revision(directory, head["revision"])
        document = revision["document"]
        scenario_raw = document.get("scenarios", {}).get(scenario_id)
        if not scenario_raw:
            raise DynamicError("SCENARIO_NOT_FOUND", "Dynamic scenario was not found.")
        scenario = Scenario.model_validate(scenario_raw)
        start, end = _stamp(scenario.start_utc), _stamp(scenario.end_utc)
        duration = end - start
        if duration <= 0 or duration > MAX_DURATION_S:
            raise DynamicError("DURATION_LIMIT", "Scenario duration must be positive and at most 120 days.")
        if math.ceil(duration / scenario.output_cadence_s) + 1 > MAX_OUTPUT_POINTS:
            raise DynamicError("OUTPUT_LIMIT", "Scenario exceeds the output point limit.")
        schedule_id = scenario_raw.get("schedule_id")
        if schedule_id and schedule_id not in document.get("schedules", {}):
            raise DynamicError("SCHEDULE_NOT_FOUND", "Dynamic schedule was not found.", {"schedule_id": schedule_id})
        schedule_raw = document.get("schedules", {}).get(schedule_id, {"id": "implicit", "events": []})
        schedule = Schedule.model_validate(schedule_raw)
        expanded_events: list[dict[str, Any]] = []
        for order, event in enumerate(schedule.events):
            event_time = float(event.time_s)
            if event_time > duration or (event.end_s is not None and event.end_s > duration):
                raise DynamicError("EVENT_TIME_INVALID", "Schedule event is outside the scenario interval.")
            count = event.count or (
                int(math.floor((min(event.end_s or duration, duration) - event_time) / event.every_s)) + 1
                if event.every_s
                else 1
            )
            for repeat in range(count):
                item = event.model_dump(mode="json")
                item["time_s"] = event_time + repeat * float(event.every_s or 0)
                if item["time_s"] > duration:
                    break
                item["declared_order"] = order
                expanded_events.append(item)
        if len(expanded_events) > MAX_EVENTS:
            raise DynamicError("EVENT_LIMIT", "Expanded schedule exceeds 1000 events.")
        controllers_raw = document.get("controllers", {})
        controller_ids = scenario_raw.get("controllers", [])
        if len(controller_ids) > MAX_CONTROLLERS:
            raise DynamicError("CONTROLLER_LIMIT", "At most 16 controllers may participate.")
        controller_items = []
        known_tags = {item.get("tag"): item for item in document["objects"].values()}
        for controller_id in controller_ids:
            raw = controllers_raw.get(controller_id)
            if raw is None:
                raise DynamicError("CONTROLLER_NOT_FOUND", f"Controller {controller_id!r} was not found.")
            controller = Controller.model_validate(raw)
            measurement_parts = controller.measurement.split(".")
            if (len(measurement_parts) not in {1, 2}
                    or measurement_parts[-1] not in {"X", "N", "O2"}
                    or (len(measurement_parts) == 2 and measurement_parts[0] != controller.unit)):
                raise DynamicError(
                    "UNSUPPORTED_MEASUREMENT",
                    "Only T1 X, N and O2 measurements are supported.",
                    {"measurement": controller.measurement},
                )
            if controller.unit not in scenario.units:
                raise DynamicError(
                    "UNSUPPORTED_MEASUREMENT",
                    "Controller measurement unit is not participating.",
                    {"unit": controller.unit},
                )
            actuator_kind, separator, actuator_tag = controller.actuator.partition(":")
            target = known_tags.get(actuator_tag)
            supported = (
                separator
                and target
                and (
                    (actuator_kind == "feed" and target.get("kind") == "stream" and target.get("source") is None)
                    or (
                        actuator_kind == "splitter"
                        and target.get("type") == "Splitter"
                        and target.get("mode") == "split_ratios"
                    )
                )
            )
            if not supported:
                raise DynamicError(
                    "UNSUPPORTED_ACTUATOR",
                    "Only boundary feed flow and splitter ratio actuators are supported.",
                    {"actuator": controller.actuator},
                )
            controller_items.append(controller.model_dump(mode="json"))
        by_tag = {item["tag"]: item for item in document["objects"].values()}
        units = []
        for tag in scenario.units:
            unit = by_tag.get(tag)
            if unit is None or unit.get("type") != "PhotobioreactorT1":
                raise DynamicError("UNIT_NOT_FOUND", f"Participating T1 unit {tag!r} was not found.")
            params = pbr_unit._parameters(unit)
            model = pbr_unit._resolve(workspace_id, unit.get("model") or {})
            volume = params["tube_count"] * math.pi * params["tube_inner_diameter"] ** 2 * params["tube_length"] / 4
            initial = scenario.initial.get(tag, {})
            if set(initial) != {"X", "N", "O2"}:
                raise DynamicError("INITIAL_STATE_REQUIRED", "Each T1 unit requires explicit X, N and O2 initial state.",
                                   {"unit": tag})
            state = [float(initial.get(k, 0.0)) for k in ("X", "N", "O2")]
            if any(not math.isfinite(v) or v < 0 for v in state):
                raise DynamicError(
                    "INITIAL_STATE_INVALID", f"Initial concentrations for {tag} must be finite and nonnegative."
                )
            units.append(
                {
                    "tag": tag,
                    "unit": unit,
                    "params": params,
                    "model": model,
                    "volume_m3": volume,
                    "state": state,
                    "card_qualification": model.get("card", {}).get("qualification_status", "unknown"),
                }
            )
        if len(units) > 8:
            raise DynamicError("UNIT_LIMIT", "At most 8 T1 units may participate.")
        # Reject unsupported connected equipment rather than silently dropping its physics.
        selected = {u["unit"]["id"] for u in units}
        objects = document["objects"]
        algebraic: dict[str, set[str]] = {}
        for stream in objects.values():
            if stream.get("kind") != "stream":
                continue
            source, target = stream.get("source"), stream.get("target")
            if source and target:
                src, dst = objects.get(source.get("unit"), {}), objects.get(target.get("unit"), {})
                supported_algebraic = {"Mixer", "Splitter", "Pump", "Recycle", "SpecifiedSeparator"}
                if src.get("type") in supported_algebraic and dst.get("type") in supported_algebraic:
                    algebraic.setdefault(src["id"], set()).add(dst["id"])
                if (target.get("unit") in selected and source.get("unit") not in selected
                        and src.get("type") not in supported_algebraic):
                    raise DynamicError(
                        "UNSUPPORTED_TOPOLOGY",
                        "A non-participating unit cannot feed the T1 network.",
                        {"unit": src.get("tag")},
                    )
            if source and source.get("unit") in selected and target and target.get("unit") not in selected:
                foreign = objects.get(target["unit"], {})
                if foreign.get("type") in {
                    "Mixer", "Splitter", "Pump", "Recycle", "SpecifiedSeparator"
                }:
                    continue
            if source and target and source.get("unit") in selected and target.get("unit") in selected:
                pass  # Native PBR-to-PBR recycle coupling is represented by the ODE below.
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(node: str) -> None:
            if node in visiting:
                raise DynamicError(
                    "ALGEBRAIC_CYCLE", "A Mixer/Splitter cycle has no dynamic PBR state.", {"unit_id": node}
                )
            if node in visited:
                return
            visiting.add(node)
            for target in algebraic.get(node, set()):
                visit(target)
            visiting.remove(node)
            visited.add(node)

        for node in algebraic:
            visit(node)
        topology = _topology(document, units, scenario.model_dump(mode="json"))
        _validate_events(expanded_events, units, topology, controller_ids)
        downstream_data = None
        if scenario.downstream_cadence_s:
            samples = math.floor(duration / scenario.downstream_cadence_s)
            if samples > MAX_DWSIM_SAMPLES:
                raise DynamicError("DWSIM_SAMPLE_LIMIT", "Scenario exceeds 200 downstream samples.")
            from app.modules.process_stack.dynamic_downstream import downstream_document

            downstream_data = downstream_document(Snapshot(
                {"document": document, "units": units, "topology": topology}, ""))
            if downstream_data[0] is None:
                raise DynamicError(
                    "DOWNSTREAM_UNITS_REQUIRED",
                    "Downstream sampling requires at least one reachable DWSIM-owned unit.",
                )
            participating_ids = {item["unit"]["id"] for item in units}
            carrier_specs = [
                stream.get("spec", {}) for stream in document["objects"].values()
                if stream.get("kind") == "stream" and stream.get("source") is None
                and (stream.get("target") or {}).get("unit") in participating_ids
            ]
            carrier_spec = carrier_specs[0] if carrier_specs else {}
            _validate_downstream_boundary_specs(downstream_data[1], carrier_spec)
        for obj in document["objects"].values():
            if obj.get("type") == "Splitter" and obj.get("mode") != "split_ratios":
                raise DynamicError(
                    "SPLITTER_FLOW_SPEC_UNSUPPORTED",
                    "Dynamic T1 supports split_ratios mode only.",
                    {"unit": obj.get("tag")},
                )
        from app.modules.environment import profiles

        resolved_profiles = []
        for ref in scenario.profiles:
            try:
                profile = profiles._read(workspace_id, ref["digest"])
            except profiles.EnvironmentIntegrityError as exc:
                raise DynamicError(
                    "PROFILE_DIGEST_INVALID",
                    "Environment profile digest verification failed.",
                    {"profile_id": ref.get("profile_id")},
                ) from exc
            if ref["profile_id"] != ref["digest"]:
                raise DynamicError("PROFILE_ID_MISMATCH", "Profile id must equal its immutable digest.")
            times = [_stamp(s) for s in profile["timestamps"]]
            channels = profile["channels"]
            par_name = "par" if "par" in channels else "ghi"
            if par_name == "ghi" and scenario.par_from_ghi_factor is None:
                raise DynamicError("PAR_UNAVAILABLE", "Profile has GHI but no declared PAR conversion factor.")
            temp_name = scenario.temperature_source
            if temp_name != "unit_mean" and temp_name not in channels:
                raise DynamicError("TEMPERATURE_UNAVAILABLE", f"Profile has no {temp_name} channel.")
            if par_name not in channels or times[0] > start or times[-1] < end:
                raise DynamicError("PROFILE_COVERAGE", "Profile does not cover the full scenario time range.")
            if temp_name != "unit_mean" and (times[0] > start or times[-1] < end):
                raise DynamicError("PROFILE_COVERAGE", "Temperature profile lacks required interpolation brackets.")
            par_first = max(0, bisect.bisect_left(times, start))
            par_last = min(len(times), bisect.bisect_left(times, end) + 1)
            for index in range(par_first, par_last):
                if channels[par_name][index] is None:
                    raise DynamicError(
                        "PROFILE_GAP",
                        "Null PAR value blocks a consumed interval.",
                        {"channel": par_name, "time_utc": profile["timestamps"][index]},
                    )
            if temp_name != "unit_mean":
                first = max(0, bisect.bisect_right(times, start) - 1)
                last = min(len(times), bisect.bisect_left(times, end) + 2)
                for index in range(first, last):
                    if channels[temp_name][index] is None:
                        raise DynamicError(
                            "PROFILE_GAP",
                            "Null temperature value blocks an interpolation bracket.",
                            {"channel": temp_name, "time_utc": profile["timestamps"][index]},
                        )
            resolved_profiles.append(
                {"ref": ref, "profile": profile, "times": times, "par_name": par_name, "temp_name": temp_name}
            )
        payload = {
            "workspace_id": workspace_id,
            "draft_id": draft_id,
            "revision": revision["revision"],
            "content_digest": draft.content_digest(document),
            "scenario_id": scenario_id,
            "scenario": scenario.model_dump(mode="json"),
            "units": units,
            "profiles": resolved_profiles,
            "start_epoch": start,
            "end_epoch": end,
            "document": document,
            "schedule": {"id": schedule.id, "events": expanded_events},
            "controllers": controller_items,
            "downstream": ({"document": downstream_data[0], "boundary_streams": downstream_data[1]}
                           if downstream_data is not None else None),
        }
        payload["topology"] = topology
        digest = hashlib.sha256(
            _canonical(
                {k: v for k, v in payload.items() if k not in {"units", "profiles"}}
                | {"unit_tags": [u["tag"] for u in units], "profiles": [p["ref"] for p in resolved_profiles]}
            )
        ).hexdigest()
        payload["snapshot_digest"] = digest
        return Snapshot(payload=payload, digest=digest)
    except DynamicError:
        raise
    except Exception as exc:
        code = getattr(exc, "code", None) or "INPUT_INVALID"
        raise DynamicError(str(code), str(exc), getattr(exc, "detail", {})) from exc


def _profile_par(snapshot: Snapshot, elapsed_s: float) -> float:
    item = snapshot.payload["profiles"][0]
    channels = item["profile"]["channels"]
    elapsed_edges = [value - snapshot.payload["start_epoch"] for value in item["times"]]
    par_ix = max(0, bisect.bisect_left(elapsed_edges, elapsed_s))
    raw_par = channels[item["par_name"]][par_ix]
    if raw_par is None:
        raise DynamicError("PROFILE_GAP", "Null PAR value blocks the consumed interval.",
                           {"channel": item["par_name"], "time_utc": datetime.fromtimestamp(item["times"][par_ix], UTC).isoformat()})
    factor = snapshot.payload["scenario"].get("par_from_ghi_factor") if item["par_name"] == "ghi" else 1.0
    return float(raw_par) * float(factor or 1.0) * snapshot.payload["scenario"].get("par_scale", 1.0)


def _profile_temperature(snapshot: Snapshot, elapsed_s: float, unit_index: int = 0) -> float:
    item = snapshot.payload["profiles"][0]
    if item["temp_name"] == "unit_mean":
        return float(snapshot.payload["units"][unit_index]["params"]["temperature_mean"])
    times = item["times"]
    epoch = snapshot.payload["start_epoch"] + elapsed_s
    channels = item["profile"]["channels"]
    j = min(max(bisect.bisect_left(times, epoch), 1), len(times) - 1)
    before, after = channels[item["temp_name"]][j - 1], channels[item["temp_name"]][j]
    if before is None or after is None:
        bad = j - 1 if before is None else j
        raise DynamicError("PROFILE_GAP", "Null temperature value blocks an interpolation bracket.",
                           {"channel": item["temp_name"], "time_utc": datetime.fromtimestamp(times[bad], UTC).isoformat()})
    weight = (epoch - times[j - 1]) / (times[j] - times[j - 1])
    return float(before) + weight * (float(after) - float(before))


def _profile_values(snapshot: Snapshot, epoch: float) -> tuple[float, float]:
    elapsed = epoch - snapshot.payload["start_epoch"]
    return _profile_par(snapshot, elapsed), _profile_temperature(snapshot, elapsed)


def _network_runtime(topology: dict[str, Any], flows: dict[str, float], units: list[dict[str, Any]]) -> dict[str, Any]:
    """Precompute inlet flow weights and algebraic evaluation order for one flow state."""
    streams = topology["streams"]
    by_id = {unit["id"]: unit for unit in topology["units"]}
    quota_by_id = {item["unit"]["id"]: item["growth"].nitrogen_quota for item in units}
    incoming: dict[str, list[tuple[dict[str, Any], float]]] = {}
    for item in units:
        key = item["unit"]["id"]
        inlet = [stream for stream in streams if (stream.get("target") or {}).get("unit") == key]
        total = sum(flows.get(stream["id"], 0.0) for stream in inlet)
        incoming[key] = [(stream, flows.get(stream["id"], 0.0) / total) for stream in inlet]
    algebraic_types = {"Mixer", "Splitter", "Pump", "Recycle", "SpecifiedSeparator"}
    pending = {key for key, unit in by_id.items() if unit.get("type") in algebraic_types}
    algebraic_incoming = {key: [stream for stream in streams if (stream.get("target") or {}).get("unit") == key]
                          for key in pending}
    order = []
    while pending:
        ready = sorted(key for key in pending if not any(
            (stream.get("source") or {}).get("unit") in pending
            for stream in streams if (stream.get("target") or {}).get("unit") == key
        ))
        if not ready:
            raise DynamicError("ALGEBRAIC_CYCLE", "Mixer/Splitter concentration graph contains a cycle.")
        order.extend(ready)
        pending.difference_update(ready)
    feed_quota = {
        stream["id"]: quota_by_id.get((stream.get("target") or {}).get("unit"), 0.0)
        for stream in streams if stream.get("source") is None
    }
    return {"incoming": incoming, "algebraic_order": order, "algebraic_incoming": algebraic_incoming,
            "feed_quota": feed_quota}


def _network_concentrations(topology: dict[str, Any], runtime: dict[str, Any], state: tuple[float, ...],
                            units: list[dict[str, Any]], flows: dict[str, float]) -> dict[str, tuple[float, ...]]:
    concentrations: dict[str, tuple[float, ...]] = {}
    for i, item in enumerate(units):
        x, nitrogen, oxygen = (float(v) for v in state[i * 7:i * 7 + 3])
        value = (x, nitrogen, oxygen, item["growth"].nitrogen_quota * x)
        concentrations[item["unit"]["id"]] = value
        for stream in topology["streams"]:
            if (stream.get("source") or {}).get("unit") == item["unit"]["id"]:
                concentrations[f"stream:{stream['id']}"] = value
    for key in runtime["algebraic_order"]:
        inlet = runtime["algebraic_incoming"][key]
        total = sum(flows.get(stream["id"], 0.0) for stream in inlet)
        if total <= 0:
            raise DynamicError("ZERO_THROUGHFLOW", "Algebraic unit has zero throughflow.", {"unit_id": key})
        mixed = np.zeros(4, dtype=np.float64)
        for stream in inlet:
            source = (stream.get("source") or {}).get("unit")
            value = topology["feeds"].get(stream["id"]) if source is None else concentrations.get(
                f"stream:{stream['id']}"
            )
            if value is None:
                raise DynamicError("TOPOLOGY_UNRESOLVED", "A stream concentration could not be resolved.")
            if source is None:
                quota = runtime["feed_quota"].get(stream["id"], 0.0)
                value = (*value[:3], quota * value[0])
            mixed += flows.get(stream["id"], 0.0) * np.asarray(value)
        inlet_value = mixed / total
        unit = next(item for item in topology["units"] if item["id"] == key)
        kind = unit.get("type")
        outgoing = sorted(
            (stream for stream in topology["streams"] if (stream.get("source") or {}).get("unit") == key),
            key=lambda stream: (stream.get("source") or {}).get("port", 0),
        )
        if kind in {"Pump", "Recycle"} and len(outgoing) != 1:
            raise DynamicError("UNIT_TOPOLOGY_INVALID", "Pump and Recycle require one outlet.",
                               {"unit": unit.get("tag")})
        if kind == "SpecifiedSeparator":
            if len(outgoing) != 2:
                raise DynamicError("SEPARATOR_TOPOLOGY_INVALID", "SpecifiedSeparator requires two outlets.",
                                   {"unit": unit.get("tag")})
            params = unit.get("params", {})
            recovery = float((params.get("biomass_recovery") or {}).get("si", 90.0)) / 100.0
            factor = float((params.get("concentration_factor") or {}).get("si", 10.0))
            concentrate = recovery / factor
            clarified = 1.0 - concentrate
            # The ratio-weighted biomass and quota-N concentrations conserve their flow rates.
            outlet_values = (
                (inlet_value[0] * factor, inlet_value[1], inlet_value[2], inlet_value[3] * factor),
                (inlet_value[0] * (1.0 - recovery) / clarified, inlet_value[1], inlet_value[2],
                 inlet_value[3] * (1.0 - recovery) / clarified),
            )
        else:
            outlet_values = (tuple(inlet_value.tolist()),) * len(outgoing)
        for stream, value in zip(outgoing, outlet_values, strict=False):
            concentrations[f"stream:{stream['id']}"] = value
    return concentrations


def _result_series(snapshot: Snapshot, times: list[float], rows: list[np.ndarray], units: list[dict[str, Any]],
                   controllers: list[dict[str, Any]], controller_log: list[dict[str, Any]],
                   flow_log: list[dict[str, Any]] | None = None) -> dict[str, np.ndarray]:
    elapsed = np.asarray(times, dtype=np.float64)
    matrix = np.asarray(rows, dtype=np.float64)
    result = {"t_s": elapsed, "par": np.asarray([_profile_par(snapshot, float(t)) for t in elapsed])}
    result["temperature"] = np.asarray([_profile_temperature(snapshot, float(t)) for t in elapsed])
    for i, unit in enumerate(units):
        for j, name in enumerate(("X", "N", "O2")):
            result[f"{unit['tag']}_{name}"] = matrix[:, i * 7 + j]
        result[f"{unit['tag']}_temperature"] = np.asarray(
            [_profile_temperature(snapshot, float(t), i) for t in elapsed]
        )
        result[f"{unit['tag']}_harvest_X_kg"] = matrix[:, i * 7 + 6] * unit["volume_m3"]
    result["harvest_X_kg"] = matrix[:, len(units) * 7 + 3] + sum(
        result[f"{unit['tag']}_harvest_X_kg"] for unit in units
    )
    for controller in controllers:
        result[f"controller_{controller['id']}"] = np.asarray([
            next((entry["output"] for entry in reversed(controller_log)
                  if entry["controller"] == controller["id"] and entry["time_s"] <= t),
                 float(controller["_initial_output"])) for t in times
        ], dtype=np.float64)
    if flow_log:
        topology = snapshot.payload["topology"]
        flows_at = [next(entry["flows"] for entry in reversed(flow_log) if entry["time_s"] <= t)
                    for t in times]
        for stream in topology["streams"]:
            if stream.get("source") is None:
                result[f"feed_{stream['tag']}_Q_m3_s"] = np.asarray(
                    [item[stream["id"]] for item in flows_at], dtype=np.float64
                )
        for unit in topology["units"]:
            if unit.get("type") != "Splitter":
                continue
            outlets = sorted(
                (stream for stream in topology["streams"]
                 if (stream.get("source") or {}).get("unit") == unit["id"]),
                key=lambda stream: (stream.get("source") or {}).get("port", 0),
            )
            for stream in outlets:
                result[f"splitter_{unit['tag']}_{stream['tag']}_ratio"] = np.asarray(
                    [item[stream["id"]] / total if total > 0 else math.nan
                     for item in flows_at
                     for total in [sum(item[out["id"]] for out in outlets)]], dtype=np.float64
                )
    return result


def run(
    snapshot: Snapshot,
    *,
    cancelled: Callable[[], bool],
    progress: Callable[[float], None],
    sampler: Callable[..., dict] | None = None,
) -> EngineResult:
    """Integrate a pinned scenario. All rates stay hourly in the 170 seam and convert once to SI seconds."""
    started = time.perf_counter()
    scenario = snapshot.payload["scenario"]
    units = [dict(unit) for unit in snapshot.payload["units"]]
    start, end = snapshot.payload["start_epoch"], snapshot.payload["end_epoch"]
    duration = end - start
    cadence = float(scenario["output_cadence_s"])
    outputs = np.arange(0.0, duration, cadence, dtype=np.float64)
    if not len(outputs) or outputs[-1] != duration:
        outputs = np.append(outputs, duration)
    if outputs[0] != 0:
        outputs = np.insert(outputs, 0, 0.0)
    n = len(units)
    topology = snapshot.payload.get("topology", {"units": [], "streams": [], "flows": {}, "feeds": {}})
    topology = dict(topology, feeds={
        key: ([value.get("X", 0.0), value.get("N", 0.0), value.get("O2", 0.0)]
              if isinstance(value, dict) else value)
        for key, value in topology["feeds"].items()
    })
    growths = [pbr_unit.build_growth(item["params"], item["model"], (0, 0, 0), 0) for item in units]
    for item, growth in zip(units, growths, strict=True):
        item["growth"] = growth
    # Per unit: X,N,O2 plus integrated generation, transfer and discrete harvest.
    # Global states: boundary X/N/O2 balance and continuous harvested biomass mass.
    initial = np.zeros(n * 7 + 4, dtype=np.float64)
    for i, unit in enumerate(units):
        initial[i * 7 : i * 7 + 3] = unit["state"]
    rows: list[np.ndarray] = [initial.copy()]
    times_out = [0.0]
    event_log: list[dict[str, Any]] = []
    controller_log: list[dict[str, Any]] = []
    flow_log: list[dict[str, Any]] = []
    downstream: list[dict[str, Any]] = []
    events = sorted(
        enumerate(snapshot.payload["schedule"].get("events", [])), key=lambda pair: (pair[1]["time_s"], pair[0])
    )
    controllers = [dict(value, _integral=0.0, _active=False, _bias=float(value["output"]),
                        _initial_output=float(value["output"]))
                   for value in snapshot.payload.get("controllers", [])]
    controller_cadence = float(scenario.get("controller_cadence_s", 300))
    has_conditional_events = any(event.get("observed") for _, event in events)
    controller_times = (
        set(float(t) for t in np.arange(controller_cadence, duration, controller_cadence))
        if controllers or has_conditional_events else set()
    )
    for item in controllers:
        cadence_i = float(item["cadence_s"])
        controller_times.update(float(t) for t in np.arange(cadence_i, duration, cadence_i))
    flows, feeds = topology["flows"], topology["feeds"]
    setpoints = {value["id"]: float(value["setpoint"]) for value in controllers}
    controller_by_id = {item["id"]: item for item in controllers}
    conditional_state: dict[int, bool] = {}
    roundoff_clips: list[dict[str, Any]] = []
    boundaries = sorted(
        set(float(v) for v in outputs)
        | {float(t - start) for t in snapshot.payload["profiles"][0]["times"] if start < t < end}
        | {float(event["time_s"]) for _, event in events if 0 < event["time_s"] < duration}
        | controller_times
        | (set(float(t) for t in np.arange(float(scenario["downstream_cadence_s"]), duration,
                                           float(scenario["downstream_cadence_s"])))
           if scenario.get("downstream_cadence_s") else set())
    )
    current = initial
    try:
        event_cursor = 0
        while event_cursor < len(events) and float(events[event_cursor][1]["time_s"]) == 0:
            current, event_cursor = _apply_dynamic_event(
                current, events[event_cursor], units, event_log, event_cursor,
                topology, flows, feeds, setpoints, {item["id"]: item for item in controllers},
            )
        flow_log.append({"time_s": 0.0, "flows": dict(flows)})
        rows[0] = current.copy()
        for left, right in zip(boundaries, boundaries[1:], strict=False):
            if cancelled():
                return EngineResult(
                    "cancelled",
                    {"code": "CANCELLED", "message": "Run cancelled.", "detail": {}},
                    _result_series(snapshot, times_out, rows, units, controllers, controller_log, flow_log),
                    _manifest(snapshot, started, event_log, controller_log, downstream),
                )

            par_segment = _profile_par(snapshot, (left + right) / 2.0)
            network = _network_runtime(topology, flows, units)

            def rhs(elapsed: float, state: tuple[float, ...], network_state: dict[str, Any] = network,
                    par_value: float = par_segment) -> list[float]:
                result = [0.0] * len(state)
                concentrations = _network_concentrations(topology, network_state, state, units, flows)
                for i, item in enumerate(units):
                    off = i * 7
                    x, nitrogen, oxygen = state[off:off + 3]
                    growth = growths[i]
                    temperature = _profile_temperature(snapshot, elapsed, i)
                    mu, loss = growth.rates_at(par_value, temperature, x, nitrogen)
                    rx = (mu - loss) * x / 3600.0
                    transfer = growth.kla_h * (growth.oxygen_saturation - oxygen) / 3600.0
                    inlet = np.zeros(3, dtype=np.float64)
                    qin = 0.0
                    for stream, weight in network_state["incoming"][item["unit"]["id"]]:
                        flow = flows.get(stream["id"], 0.0)
                        source = (stream.get("source") or {}).get("unit")
                        value = feeds.get(stream["id"]) if source is None else concentrations.get(
                            f"stream:{stream['id']}"
                        )
                        if value is None:
                            raise DynamicError("TOPOLOGY_UNRESOLVED", "A PBR inlet concentration could not be resolved.")
                        inlet += weight * np.asarray(value[:3])
                        qin += flow
                    dilution = qin / item["volume_m3"]
                    net_x = rx + dilution * (inlet[0] - x)
                    net_n = -growth.nitrogen_quota * rx + dilution * (inlet[1] - nitrogen)
                    net_o = growth.oxygen_yield * rx + transfer + dilution * (inlet[2] - oxygen)
                    result[off:off + 7] = [net_x, net_n, net_o, rx, -growth.nitrogen_quota * rx, transfer, 0.0]
                # Boundary terms are inventory rates in kg/s. Fourth concentration is q*X,
                # propagated independently through algebraic mixers/splitters.
                active_ids = {unit["id"] for unit in topology["units"]}
                for stream in topology["streams"]:
                    source, target = stream.get("source"), stream.get("target")
                    if source is not None and (target or {}).get("unit") in active_ids:
                        continue
                    value = feeds.get(stream["id"]) if source is None else concentrations.get(
                        f"stream:{stream['id']}"
                    )
                    if value is None:
                        continue
                    if source is None:
                        quota_x = network_state["feed_quota"].get(stream["id"], 0.0) * value[0]
                    else:
                        quota_x = value[3]
                    q = flows.get(stream["id"], 0.0) * (1.0 if source is None else -1.0)
                    result[n * 7:n * 7 + 3] += q * np.asarray([value[0], value[1] + quota_x, value[2]])
                    if source is not None:
                        result[n * 7 + 3] += flows.get(stream["id"], 0.0) * value[0]
                return result

            grid = [left, *[float(t) for t in outputs if left < t < right], right]
            from app.modules.process_stack.dynamics import integrate_ode

            solved = integrate_ode(
                rhs,
                current,
                grid,
                rtol=float(scenario["rtol"]),
                atol=float(scenario["atol"]),
                method=scenario["solver_method"],
            )
            if not solved.success:
                raise DynamicError("SOLVER_FAILED", solved.message, {"segment_s": [left, right]})
            for t, state in zip(solved.times[1:], solved.states[1:], strict=True):
                state = np.asarray(state, dtype=np.float64)
                _valid_state(state, units, growths)
                _clip_tiny_negatives(state, units, roundoff_clips, float(t))
                if any(abs(float(t) - float(out)) <= 1e-7 for out in outputs):
                    times_out.append(float(t))
                    rows.append(np.asarray(state, dtype=np.float64))
            current = np.asarray(solved.states[-1], dtype=np.float64)
            _clip_tiny_negatives(current, units, roundoff_clips, right)
            while event_cursor < len(events) and abs(float(events[event_cursor][1]["time_s"]) - right) < 1e-7:
                current, event_cursor = _apply_dynamic_event(
                    current, events[event_cursor], units, event_log, event_cursor,
                    topology, flows, feeds, setpoints, {item["id"]: item for item in controllers},
                )
                if times_out and abs(times_out[-1] - right) < 1e-7:
                    rows[-1] = current.copy()
            if any(abs(right % float(item["cadence_s"])) < 1e-7 for item in controllers) or (
                controller_cadence and abs(right % controller_cadence) < 1e-7
            ):
                _sample_controllers(current, units, controllers, topology, flows, setpoints, right, controller_log)
                _conditional_events(current, units, events, conditional_state, event_log, right,
                                    topology, flows, feeds, setpoints, controller_by_id)
                if times_out and abs(times_out[-1] - right) < 1e-7:
                    rows[-1] = current.copy()
            flow_log.append({"time_s": right, "flows": dict(flows)})
            if (
                sampler
                and scenario.get("downstream_cadence_s")
                and abs(right % scenario["downstream_cadence_s"]) < 1e-7
            ):
                if cancelled():
                    return EngineResult(
                        "cancelled",
                        {"code": "CANCELLED", "message": "Run cancelled.", "detail": {}},
                        _result_series(snapshot, times_out, rows, units, controllers, controller_log, flow_log),
                        _manifest(snapshot, started, event_log, controller_log, downstream),
                    )
                try:
                    result = sampler(
                        {
                            "time_s": right,
                            "units": {u["tag"]: current[i * 7 : i * 7 + 3].tolist() for i, u in enumerate(units)},
                            "streams": _boundary_streams(topology, current, units, flows, feeds),
                        }
                    )
                    downstream.append({"time_s": right, **result})
                except Exception as exc:
                    downstream.append({"time_s": right, "status": "downstream_unconverged",
                                       "error_type": type(exc).__name__})
                if downstream[-1].get("status") == "unconverged":
                    downstream[-1]["status"] = "downstream_unconverged"
                if cancelled():
                    return EngineResult(
                        "cancelled",
                        {"code": "CANCELLED", "message": "Run cancelled.", "detail": {}},
                        _result_series(snapshot, times_out, rows, units, controllers, controller_log, flow_log),
                        _manifest(snapshot, started, event_log, controller_log, downstream),
                    )
            progress(min(1.0, right / duration))
        series = _result_series(snapshot, times_out, rows, units, controllers, controller_log, flow_log)
        manifest = _manifest(snapshot, started, event_log, controller_log, downstream)
        manifest["channels"] = {
            name: (
                "s" if name == "t_s" else
                "umol/(m2*s)" if name == "par" else
                "K" if name == "temperature" or name.endswith("_temperature") else
                "kg" if name == "harvest_X_kg" or name.endswith("_harvest_X_kg") else
                "m3/s" if name.endswith("_Q_m3_s") else
                "1" if name.endswith("_ratio") else
                "kg/m3" if name.endswith(("_X", "_N", "_O2")) else
                ("m3/s" if next(c for c in controllers if name == f"controller_{c['id']}")
                 ["actuator"].startswith("feed:") else "1")
                if name.startswith("controller_") else "unknown"
            ) for name in series
        }
        manifest["diagnostics"]["roundoff_clips"] = roundoff_clips
        net_boundary = current[n * 7 : n * 7 + 3]
        initial_inventory = np.zeros(3, dtype=np.float64)
        final_inventory = np.zeros(3, dtype=np.float64)
        for i, unit in enumerate(units):
            growth = growths[i]
            initial_inventory += unit["volume_m3"] * np.asarray(
                [unit["state"][0], unit["state"][1] + growth.nitrogen_quota * unit["state"][0], unit["state"][2]])
            final_inventory += unit["volume_m3"] * np.asarray(
                [current[i * 7], current[i * 7 + 1] + growth.nitrogen_quota * current[i * 7], current[i * 7 + 2]])
        generated = np.asarray([
            sum(current[i * 7 + 3] * unit["volume_m3"] for i, unit in enumerate(units)),
            0.0,
            sum((growths[i].oxygen_yield
                 * current[i * 7 + 3] + current[i * 7 + 5]) * unit["volume_m3"]
                for i, unit in enumerate(units)),
        ])
        impulses = np.zeros(3, dtype=np.float64)
        for entry in event_log:
            if entry.get("impulse_inventory"):
                impulses += np.asarray(entry["impulse_inventory"], dtype=np.float64)
        residual = initial_inventory + net_boundary + generated + impulses - final_inventory
        manifest["balances"] = {
            "sign_conventions": {"oxygen_transfer": "positive means oxygen absorption into liquid"},
            "units": {
                unit["tag"]: {
                    "biomass_generation_kg": float(current[i * 7 + 3] * unit["volume_m3"]),
                    "nitrogen_total_generation_kg": 0.0,
                    "oxygen_transfer_kg": float(current[i * 7 + 5] * unit["volume_m3"]),
                }
                for i, unit in enumerate(units)
            },
            "aggregate": {name: {"residual_abs_kg": float(abs(residual[i]),),
                                  "residual_rel": float(abs(residual[i]) / max(1e-12, abs(initial_inventory[i]) + abs(net_boundary[i]) + abs(generated[i]) + abs(impulses[i])))}
                           for i, name in enumerate(("biomass", "total_nitrogen", "oxygen"))},
        }
        harvest_kg = float(series["harvest_X_kg"][-1])
        volume_m3 = sum(unit["volume_m3"] for unit in units)
        area_m2 = (
            sum(math.pi * unit["params"]["tube_inner_diameter"] * unit["params"]["tube_length"]
                * unit["params"]["tube_count"] for unit in units)
            if all({"tube_inner_diameter", "tube_length", "tube_count"} <= unit["params"].keys()
                   for unit in units) else None
        )
        days = duration / 86400.0
        manifest["productivity"] = {
            "harvest_kg": harvest_kg,
            "volumetric_kg_m3_day": harvest_kg / volume_m3 / days,
            "areal_kg_m2_day": harvest_kg / area_m2 / days if area_m2 else None,
            "areal_unavailable_reason": None if area_m2 else "Illuminated tube geometry is unavailable.",
            "energy_per_kg": None,
            "energy_per_kg_unavailable_reason": "No dynamic pump or aeration energy input is declared.",
        }
        return EngineResult("succeeded", None, series, manifest)
    except DynamicError as exc:
        return EngineResult(
            "failed",
            {"code": exc.code, "message": exc.message, "detail": exc.detail},
            _result_series(snapshot, times_out, rows, units, controllers, controller_log, flow_log),
            _manifest(snapshot, started, event_log, controller_log, downstream),
        )
    except Exception as exc:
        error = {"code": "DYNAMIC_FAILED", "message": str(exc)[:600], "detail": {}}
        return EngineResult(
            "failed",
            error,
            _result_series(snapshot, times_out, rows, units, controllers, controller_log, flow_log),
            _manifest(snapshot, started, event_log, controller_log, downstream),
        )


def _valid_state(state: tuple[float, ...], units: list[dict[str, Any]], growths: list[Any] | None = None) -> None:
    if not all(math.isfinite(float(v)) for v in state):
        raise DynamicError("STATE_NONFINITE", "CVODE produced a nonfinite state.")
    for i, item in enumerate(units):
        for name, value in zip(("X", "N", "O2"), state[i * 7 : i * 7 + 3], strict=True):
            tolerance = max(1e-9, 1e-6 * max(1.0, abs(float(value))))
            if value < -tolerance:
                raise DynamicError(
                    "STATE_NEGATIVE",
                    f"{name} concentration became materially negative.",
                    {"unit": item["tag"], "channel": name, "value": value},
                )
        growth = growths[i] if growths is not None else pbr_unit.build_growth(item["params"], item["model"], (0, 0, 0), 0)
        if growth.extinction * max(0.0, float(state[i * 7])) * growth.diameter > 1e6:
            raise DynamicError("OPTICS_TAU_MAX", "Optical depth exceeds the model limit.", {"unit": item["tag"]})


def _clip_tiny_negatives(
    state: np.ndarray, units: list[dict[str, Any]], clips: list[dict[str, Any]], time_s: float,
) -> None:
    for i, unit in enumerate(units):
        for offset, channel in enumerate(("X", "N", "O2")):
            index = i * 7 + offset
            if state[index] < 0:
                clips.append({"time_s": time_s, "unit": unit["tag"], "channel": channel,
                              "value_before": float(state[index]), "value_after": 0.0})
                state[index] = 0.0


def _boundary_streams(
    topology: dict[str, Any], state: np.ndarray, units: list[dict[str, Any]],
    flows: dict[str, float], feeds: dict[str, list[float]],
) -> dict[str, dict[str, Any]]:
    for unit in units:
        if "growth" not in unit:
            unit["growth"] = pbr_unit.build_growth(unit["params"], unit["model"], (0, 0, 0), 0)
    runtime = _network_runtime(topology, flows, units)
    concentrations = _network_concentrations(topology, runtime, tuple(state), units, flows)
    dynamic_ids = {item["id"] for item in topology["units"]}
    output = {}
    for stream in topology["streams"]:
        source, target = stream.get("source"), stream.get("target")
        if (source is None or target is None
                or (source.get("unit") in dynamic_ids and target.get("unit") not in dynamic_ids)):
            concentration = feeds.get(stream["id"]) if source is None else concentrations.get(
                f"stream:{stream['id']}"
            )
            output[stream["tag"]] = {
                "flow_m3_s": float(flows.get(stream["id"], 0.0)),
                "X_kg_m3": concentration[0] if concentration is not None else None,
                "N_kg_m3": concentration[1] if concentration is not None else None,
                "O2_kg_m3": concentration[2] if concentration is not None else None,
            }
    return output


def _apply_event(
    state: np.ndarray,
    indexed: tuple[int, dict[str, Any]],
    units: list[dict[str, Any]],
    log: list[dict[str, Any]],
    order: int,
) -> tuple[np.ndarray, int]:
    index, event = indexed
    tag = event.get("unit")
    found = next((i for i, unit in enumerate(units) if unit["tag"] == tag), None)
    if event["type"] in {"inoculation", "harvest"} and found is None:
        raise DynamicError("EVENT_TARGET_INVALID", f"Event target unit {tag!r} is not participating.")
    before = state.copy()
    if event["type"] == "inoculation":
        value = event.get("value")
        if isinstance(value, dict):
            for name, channel in (("X", 0), ("N", 1), ("O2", 2)):
                if name in value:
                    state[found * 7 + channel] = float(value[name])
        else:
            state[found * 7] = float(value)
    elif event["type"] == "harvest":
        fraction = float(event.get("fraction", 0.0))
        if not 0 <= fraction <= 1:
            raise DynamicError("EVENT_VALUE_INVALID", "Harvest fraction must be between 0 and 1.")
        state[found * 7 : found * 7 + 3] *= 1.0 - fraction
        state[found * 7 + 6] += before[found * 7] * fraction
    elif event["type"] in {"feed_change", "dilution", "setpoint_change"}:
        # These actions affect flow/controller state; the current snapshot does not infer missing actuators.
        raise DynamicError(
            "EVENT_ACTUATOR_UNSUPPORTED", f"{event['type']} requires an explicitly bound dynamic actuator."
        )
    _valid_state(tuple(state), units)
    log.append(
        {
            "order": order,
            "time_s": event["time_s"],
            "type": event["type"],
            "target": tag,
            "pre_state": before.tolist(),
            "post_state": state.tolist(),
            "fraction": event.get("fraction"),
        }
    )
    return state, index + 1


def _apply_dynamic_event(
    state: np.ndarray,
    indexed: tuple[int, dict[str, Any]],
    units: list[dict[str, Any]],
    log: list[dict[str, Any]],
    order: int,
    topology: dict[str, Any],
    flows: dict[str, float],
    feeds: dict[str, list[float]],
    setpoints: dict[str, float],
    controllers: dict[str, dict[str, Any]],
) -> tuple[np.ndarray, int]:
    index, event = indexed
    if event.get("observed"):
        return state, index + 1
    if event["type"] in {"inoculation", "harvest"}:
        before = state.copy()
        state, _ = _apply_event(state, indexed, units, [], order)
        unit_index = next(i for i, unit in enumerate(units) if unit["tag"] == event["unit"])
        growth = pbr_unit.build_growth(units[unit_index]["params"], units[unit_index]["model"], (0, 0, 0), 0)
        volume = units[unit_index]["volume_m3"]
        delta = state[unit_index * 7 : unit_index * 7 + 3] - before[unit_index * 7 : unit_index * 7 + 3]
        impulse = [delta[0] * volume, (delta[1] + growth.nitrogen_quota * delta[0]) * volume, delta[2] * volume]
        entry = {"order": order, "time_s": event["time_s"], "type": event["type"], "target": event.get("unit"),
                 "pre_state": before.tolist(), "post_state": state.tolist(), "impulse_inventory": impulse}
        log.append(entry)
        return state, index + 1
    kind, target = (event.get("target") or "").split(":", 1) if ":" in (event.get("target") or "") else ("", "")
    if event["type"] in {"feed_change", "dilution"}:
        stream_tag = event.get("stream") or (target if kind == "feed" else None)
        value = event.get("value")
        if kind == "splitter" or (event["type"] == "dilution" and event.get("target", "").startswith("splitter:")):
            splitter_tag = target or event["target"].split(":", 1)[1]
            splitter = next((u for u in topology["units"] if u.get("tag") == splitter_tag and u.get("type") == "Splitter"), None)
            if splitter is None:
                raise DynamicError("EVENT_TARGET_INVALID", "Dilution splitter is not participating.", {"target": splitter_tag})
            outgoing = [s for s in topology["streams"] if (s.get("source") or {}).get("unit") == splitter["id"]]
            total = sum(flows[s["id"]] for s in outgoing)
            ratio = float(value)
            if not 0 <= ratio <= 1 or len(outgoing) < 2:
                raise DynamicError("EVENT_VALUE_INVALID", "Splitter ratio must be in [0,1] and have at least two outlets.")
            flows[outgoing[0]["id"]] = total * ratio
            for outlet in outgoing[1:]:
                flows[outlet["id"]] = total * (1 - ratio) / (len(outgoing) - 1)
            _rebalance_flows(topology, flows)
        else:
            stream = next((item for item in topology["streams"] if item["tag"] == stream_tag), None)
            if stream is None or stream.get("source") is not None:
                raise DynamicError("EVENT_TARGET_INVALID", "Feed event must name a boundary feed stream.", {"stream": stream_tag})
            if isinstance(value, dict):
                flows[stream["id"]] = float(value.get("flow_m3_s", flows[stream["id"]]))
                if "culture" in value:
                    feeds[stream["id"]] = [float(value["culture"].get(k, 0.0)) for k in ("X", "N", "O2")]
            elif value is not None:
                flows[stream["id"]] = float(value)
            if flows[stream["id"]] < 0 or not math.isfinite(flows[stream["id"]]):
                raise DynamicError("EVENT_VALUE_INVALID", "Feed flow must be finite and nonnegative.")
            _rebalance_flows(topology, flows)
    elif event["type"] == "setpoint_change":
        controller_id = event.get("target")
        if controller_id not in controllers:
            raise DynamicError("EVENT_TARGET_INVALID", "Setpoint event must target a participating controller.", {"target": controller_id})
        setpoints[controller_id] = float(event["value"])
    log.append({"order": order, "time_s": event["time_s"], "type": event["type"], "target": event.get("target"),
                "value": event.get("value")})
    return state, index + 1


def _sample_controllers(
    state: np.ndarray, units: list[dict[str, Any]], controllers: list[dict[str, Any]], topology: dict[str, Any],
    flows: dict[str, float], setpoints: dict[str, float], time_s: float, log: list[dict[str, Any]],
) -> None:
    for controller in controllers:
        if abs(time_s % float(controller["cadence_s"])) >= 1e-7:
            continue
        unit_index = next(i for i, unit in enumerate(units) if unit["tag"] == controller["unit"])
        channel = controller["measurement"].split(".")[-1]
        if channel not in {"X", "N", "O2"}:
            raise DynamicError("UNSUPPORTED_MEASUREMENT", "Only X, N, and O2 can be measured.")
        measurement = float(state[unit_index * 7 + {"X": 0, "N": 1, "O2": 2}[channel]])
        error = setpoints[controller["id"]] - measurement
        if controller["type"] == "onoff":
            if controller["direction"] == "above":
                active = measurement <= setpoints[controller["id"]] + controller["hysteresis"] if controller["_active"] else measurement < setpoints[controller["id"]]
            else:
                active = measurement >= setpoints[controller["id"]] - controller["hysteresis"] if controller["_active"] else measurement > setpoints[controller["id"]]
            output = controller["upper"] if active else controller["lower"]
            controller["_active"] = active
        elif controller["type"] == "pi":
            dt = float(controller["cadence_s"])
            raw = controller["_bias"] + controller["kp"] * error + controller["ki"] * controller["_integral"]
            output = min(controller["upper"], max(controller["lower"], raw))
            if output == raw or (output >= controller["upper"] and error < 0) or (output <= controller["lower"] and error > 0):
                controller["_integral"] += error * dt
        else:
            harvest_fraction = max(0.0, 1.0 - setpoints[controller["id"]] / max(measurement, 1e-12))
            output = min(controller["upper"], max(controller["lower"], harvest_fraction))
        controller["output"] = float(output)
        actuator = controller["actuator"]
        kind, tag = actuator.split(":", 1)
        if kind == "feed":
            stream = next((s for s in topology["streams"] if s["tag"] == tag), None)
            if stream is None or stream.get("source") is not None:
                raise DynamicError("UNSUPPORTED_ACTUATOR", "Feed actuator must target a boundary feed.")
            flows[stream["id"]] = float(output)
            _rebalance_flows(topology, flows)
        elif kind == "splitter":
            splitter = next((u for u in topology["units"] if u.get("tag") == tag and u.get("type") == "Splitter"), None)
            if splitter is None:
                raise DynamicError("UNSUPPORTED_ACTUATOR", "Splitter actuator must target a participating splitter.")
            outlets = [s for s in topology["streams"] if (s.get("source") or {}).get("unit") == splitter["id"]]
            total = sum(flows[s["id"]] for s in outlets)
            flows[outlets[0]["id"]] = total * output
            for stream in outlets[1:]:
                flows[stream["id"]] = total * (1 - output) / (len(outlets) - 1)
            _rebalance_flows(topology, flows)
        log.append({"controller": controller["id"], "time_s": time_s, "measurement": measurement, "output": float(output)})


def _conditional_events(
    state: np.ndarray, units: list[dict[str, Any]], events: list[tuple[int, dict[str, Any]]],
    active: dict[int, bool], log: list[dict[str, Any]], time_s: float, topology: dict[str, Any],
    flows: dict[str, float], feeds: dict[str, list[float]], setpoints: dict[str, float],
    controllers: dict[str, dict[str, Any]],
) -> None:
    for order, event in events:
        if not event.get("observed") or event.get("_fired") or float(event["time_s"]) > time_s:
            continue
        unit_tag, _, channel = event["observed"].partition(".")
        unit_index = next((i for i, unit in enumerate(units) if unit["tag"] == unit_tag), None)
        if unit_index is None or channel not in {"X", "N", "O2"}:
            continue
        value = float(state[unit_index * 7 + {"X": 0, "N": 1, "O2": 2}[channel]])
        threshold, band = float(event["threshold"]), float(event.get("hysteresis") or 0)
        is_active = value >= threshold if event.get("direction") == "above" else value <= threshold
        was_active = active.get(order, False)
        if is_active and not was_active:
            event["_fired"] = True
            log.append({"order": order, "time_s": time_s, "type": event["type"], "conditional": True,
                        "observed": event["observed"], "measurement": value, "threshold": threshold,
                        "hysteresis": band, "direction": event["direction"]})
            action = dict(event, time_s=time_s)
            action.pop("observed", None)
            action.pop("threshold", None)
            action.pop("direction", None)
            action.pop("hysteresis", None)
            if action["type"] in {"inoculation", "harvest"}:
                state, _ = _apply_dynamic_event(state, (order, action), units, log, order,
                                                topology, flows, feeds, setpoints, controllers)
            else:
                _apply_dynamic_event(state, (order, action), units, log, order,
                                     topology, flows, feeds, setpoints, controllers)
        active[order] = is_active if (not was_active or abs(value - threshold) > band) else was_active


def _rebalance_flows(topology: dict[str, Any], flows: dict[str, float]) -> None:
    """Re-solve network continuity after a boundary feed actuator changes Q."""
    streams, units = topology["streams"], topology["units"]
    if not units:
        return
    index = {stream["id"]: i for i, stream in enumerate(streams)}
    rows: list[np.ndarray] = []
    rhs: list[float] = []
    for stream in streams:
        if stream.get("source") is None:
            row = np.zeros(len(streams))
            row[index[stream["id"]]] = 1.0
            rows.append(row)
            rhs.append(float(flows[stream["id"]]))
    for unit in units:
        key = unit["id"]
        incoming = [s for s in streams if (s.get("target") or {}).get("unit") == key]
        outgoing = [s for s in streams if (s.get("source") or {}).get("unit") == key]
        outgoing.sort(key=lambda stream: (stream.get("source") or {}).get("port", 0))
        if not incoming or not outgoing:
            continue
        row = np.zeros(len(streams))
        for stream in incoming:
            row[index[stream["id"]]] += 1.0
        for stream in outgoing:
            row[index[stream["id"]]] -= 1.0
        rows.append(row)
        rhs.append(0.0)
        if unit.get("type") == "Splitter":
            total = sum(flows[s["id"]] for s in outgoing)
            if total <= 0:
                raise DynamicError("ZERO_THROUGHFLOW", "Splitter has zero flow after an actuator change.", {"unit": unit.get("tag")})
            ratios = [flows[s["id"]] / total for s in outgoing]
            for stream, ratio in zip(outgoing, ratios, strict=True):
                split_row = np.zeros(len(streams))
                split_row[index[stream["id"]]] = 1.0
                for inlet in incoming:
                    split_row[index[inlet["id"]]] -= ratio
                rows.append(split_row)
                rhs.append(0.0)
        elif unit.get("type") == "SpecifiedSeparator":
            if len(incoming) != 1 or len(outgoing) != 2:
                raise DynamicError("SEPARATOR_TOPOLOGY_INVALID", "Separator needs one inlet and two outlets.")
            params = unit.get("params", {})
            recovery = float((params.get("biomass_recovery") or {}).get("si", 90.0)) / 100.0
            factor = float((params.get("concentration_factor") or {}).get("si", 10.0))
            for stream, ratio in zip(outgoing, (recovery / factor, 1.0 - recovery / factor), strict=True):
                sep_row = np.zeros(len(streams))
                sep_row[index[stream["id"]]] = 1.0
                sep_row[index[incoming[0]["id"]]] = -ratio
                rows.append(sep_row)
                rhs.append(0.0)
    solved, *_ = np.linalg.lstsq(np.vstack(rows), np.asarray(rhs), rcond=None)
    if np.any(solved < -1e-10) or np.max(np.abs(np.vstack(rows) @ solved - rhs)) > 1e-8:
        raise DynamicError("FLOW_BALANCE_UNSOLVED", "Feed actuator produced inconsistent network flows.")
    flows.update({stream["id"]: max(0.0, float(solved[index[stream["id"]]])) for stream in streams})


def _manifest(
    snapshot: Snapshot,
    started: float,
    events: list[dict[str, Any]],
    controllers: list[dict[str, Any]],
    downstream: list[dict[str, Any]],
) -> dict[str, Any]:
    p = snapshot.payload
    return {
        "fidelity": "T1",
        "evaluator_version": EVALUATOR_VERSION,
        "snapshot_digest": snapshot.digest,
        "draft_id": p["draft_id"],
        "draft_revision": p["revision"],
        "content_digest": p["content_digest"],
        "scenario_id": p["scenario_id"],
        "profiles": [item["ref"] for item in p["profiles"]],
        "units": [{"tag": u["tag"], "model_card_qualification": u["card_qualification"]} for u in p["units"]],
        "solver": {
            "method": p["scenario"]["solver_method"],
            "rtol": p["scenario"]["rtol"],
            "atol": p["scenario"]["atol"],
            "owner": "scikit-sundae CVODE",
        },
        "rate_time_convention": "170 hourly rates divided by 3600 exactly once for SI-second integration",
        "temporal_rules": {
            "par": "interval-end held over preceding interval; no interpolation",
            "temperature": "linear between UTC point samples; no extrapolation",
        },
        "event_log": events,
        "controller_log": controllers,
        "diagnostics": {"wall_time_s": time.perf_counter() - started},
        "downstream_outcomes": downstream,
    }
