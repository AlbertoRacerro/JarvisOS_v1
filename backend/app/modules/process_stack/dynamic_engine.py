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
            endpoints = [stream.get("source"), stream.get("target")]
            ids = [endpoint.get("unit") for endpoint in endpoints if endpoint]
            if current not in ids:
                continue
            for neighbor in ids:
                if neighbor == current:
                    continue
                candidate = by_id.get(neighbor, {})
                if candidate.get("type") not in {"PhotobioreactorT1", "Mixer", "Splitter"}:
                    raise DynamicError(
                        "UNSUPPORTED_TOPOLOGY",
                        "A non-participating unit lies on the T1 network.",
                        {"unit": candidate.get("tag")},
                    )
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
        if not incoming or not outgoing:
            if key in selected:
                raise DynamicError(
                    "ZERO_THROUGHFLOW", "Participating PBR must have inlet and outlet streams.", {"unit": unit["tag"]}
                )
            continue
        row = np.zeros(n)
        for stream in incoming:
            row[index[stream["id"]]] += 1
        for stream in outgoing:
            row[index[stream["id"]]] -= 1
        equations.append(row)
        rhs.append(0.0)
        if unit.get("type") == "Splitter":
            ratios = unit.get("params", {}).get("split_ratios", {})
            ratio_values = [
                float(v.get("si", v)) if isinstance(v, dict) else float(v) for _, v in sorted(ratios.items())
            ]
            if not ratio_values or len(ratio_values) != len(outgoing):
                raise DynamicError(
                    "SPLITTER_RATIOS_INVALID", "Splitter requires one declared ratio per outlet.", {"unit": unit["tag"]}
                )
            if any(v < 0 or v > 1 for v in ratio_values) or abs(sum(ratio_values) - 1.0) > 1e-6:
                raise DynamicError(
                    "SPLITTER_RATIOS_INVALID",
                    "Splitter ratios must be nonnegative and sum to one.",
                    {"unit": unit["tag"]},
                )
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
            if controller.measurement.split(".")[-1] not in {"X", "N", "O2"}:
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
                if src.get("type") in {"Mixer", "Splitter"} and dst.get("type") in {"Mixer", "Splitter"}:
                    algebraic.setdefault(src["id"], set()).add(dst["id"])
                if (source.get("unit") in selected or target.get("unit") in selected) and (
                    src.get("type") not in {"PhotobioreactorT1", "Mixer", "Splitter"}
                    or dst.get("type") not in {"PhotobioreactorT1", "Mixer", "Splitter"}
                ):
                    foreign = (
                        src if src.get("id") not in selected and src.get("type") not in {"Mixer", "Splitter"} else dst
                    )
                    raise DynamicError(
                        "UNSUPPORTED_TOPOLOGY",
                        "A non-T1 unit is connected to participating topology.",
                        {"unit": foreign.get("tag")},
                    )
            if source and source.get("unit") in selected and target and target.get("unit") not in selected:
                foreign = objects.get(target["unit"], {})
                if foreign.get("type") in {"Mixer", "Splitter"}:
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


def _profile_values(snapshot: Snapshot, epoch: float) -> tuple[float, float]:
    item = snapshot.payload["profiles"][0]
    profile, times = item["profile"], item["times"]
    channels = profile["channels"]
    import bisect

    ix = bisect.bisect_left(times, epoch)
    # Interval-end values are held over the preceding interval, including the right endpoint.
    par_ix = max(0, bisect.bisect_left(times, epoch + 1e-9))
    raw_par = channels[item["par_name"]][par_ix]
    if raw_par is None:
        raise DynamicError(
            "PROFILE_GAP",
            "Null PAR value blocks the consumed interval.",
            {"channel": item["par_name"], "time_utc": datetime.fromtimestamp(times[par_ix], UTC).isoformat()},
        )
    factor = snapshot.payload["scenario"].get("par_from_ghi_factor") if item["par_name"] == "ghi" else 1.0
    par = float(raw_par) * float(factor or 1.0) * snapshot.payload["scenario"].get("par_scale", 1.0)
    if item["temp_name"] == "unit_mean":
        temperature = float(snapshot.payload["units"][0]["params"]["temperature_mean"])
    else:
        j = min(max(ix, 1), len(times) - 1)
        before, after = channels[item["temp_name"]][j - 1], channels[item["temp_name"]][j]
        if before is None or after is None:
            bad = j - 1 if before is None else j
            raise DynamicError(
                "PROFILE_GAP",
                "Null temperature value blocks the interpolation bracket.",
                {"channel": item["temp_name"], "time_utc": datetime.fromtimestamp(times[bad], UTC).isoformat()},
            )
        weight = (epoch - times[j - 1]) / (times[j] - times[j - 1])
        temperature = float(before) + weight * (float(after) - float(before))
    return par, temperature


def run(
    snapshot: Snapshot,
    *,
    cancelled: Callable[[], bool],
    progress: Callable[[float], None],
    sampler: Callable[..., dict] | None = None,
) -> EngineResult:
    """Integrate a pinned scenario. All rates stay hourly in the 170 seam and convert once to SI seconds."""
    started = time.perf_counter()
    scenario, units = snapshot.payload["scenario"], snapshot.payload["units"]
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
    unit_by_id = {item["id"]: item for item in topology["units"]}
    q_in = {
        item["unit"]["id"]: sum(
            topology["flows"].get(s["id"], 0.0)
            for s in topology["streams"]
            if (s.get("target") or {}).get("unit") == item["unit"]["id"]
        )
        for item in units
    }
    # Per unit: X,N,O2 plus integrated net growth, oxygen transfer, harvest X and N.
    initial = np.zeros(n * 7, dtype=np.float64)
    for i, unit in enumerate(units):
        initial[i * 7 : i * 7 + 3] = unit["state"]
    rows: list[np.ndarray] = [initial.copy()]
    times_out = [0.0]
    event_log: list[dict[str, Any]] = []
    controller_log: list[dict[str, Any]] = []
    downstream: list[dict[str, Any]] = []
    events = sorted(
        enumerate(snapshot.payload["schedule"].get("events", [])), key=lambda pair: (pair[1]["time_s"], pair[0])
    )
    boundaries = sorted(
        set(float(v) for v in outputs)
        | {float(t - start) for t in snapshot.payload["profiles"][0]["times"] if start < t < end}
        | {float(event["time_s"]) for _, event in events if 0 < event["time_s"] < duration}
    )
    current = initial
    try:
        event_cursor = 0
        while event_cursor < len(events) and float(events[event_cursor][1]["time_s"]) == 0:
            current, event_cursor = _apply_event(current, events[event_cursor], units, event_log, event_cursor)
        rows[0] = current.copy()
        for left, right in zip(boundaries, boundaries[1:], strict=False):
            if cancelled():
                return EngineResult(
                    "cancelled",
                    {"code": "CANCELLED", "message": "Run cancelled.", "detail": {}},
                    {"t_s": np.asarray(times_out), "state": np.asarray(rows)},
                    _manifest(snapshot, started, event_log, controller_log, downstream),
                )

            def rhs(elapsed: float, state: tuple[float, ...]) -> list[float]:
                par, temperature = _profile_values(snapshot, start + elapsed)
                result = [0.0] * len(state)
                concentrations: dict[str, tuple[float, float, float]] = {}
                # Algebraic units carry no inventory. Evaluate them in stream order, with PBR states
                # breaking recycle loops and all mixers using their solved volumetric flow weights.
                for i, item in enumerate(units):
                    concentrations[item["unit"]["id"]] = tuple(float(v) for v in state[i * 7 : i * 7 + 3])
                pending = {key for key, value in unit_by_id.items() if value.get("type") in {"Mixer", "Splitter"}}
                while pending:
                    progressed = False
                    for key in list(pending):
                        incoming = [s for s in topology["streams"] if (s.get("target") or {}).get("unit") == key]
                        sources = [(s, (s.get("source") or {}).get("unit")) for s in incoming]
                        if any(source in pending for _, source in sources):
                            continue
                        total = sum(topology["flows"].get(s["id"], 0.0) for s in incoming)
                        if total <= 0:
                            raise DynamicError(
                                "ZERO_THROUGHFLOW",
                                "Mixer or splitter has zero throughflow.",
                                {"unit": unit_by_id[key].get("tag")},
                            )
                        mixed = np.zeros(3, dtype=np.float64)
                        for stream, source in sources:
                            flow = topology["flows"].get(stream["id"], 0.0)
                            value = (
                                topology["feeds"].get(stream["id"]) if source is None else concentrations.get(source)
                            )
                            if value is None:
                                raise DynamicError(
                                    "TOPOLOGY_UNRESOLVED", "A stream concentration could not be resolved."
                                )
                            mixed += flow * np.asarray(value, dtype=np.float64)
                        concentrations[key] = tuple((mixed / total).tolist())
                        pending.remove(key)
                        progressed = True
                    if not progressed:
                        raise DynamicError("ALGEBRAIC_CYCLE", "Mixer/Splitter concentration graph contains a cycle.")
                for i, item in enumerate(units):
                    off = i * 7
                    x, nitrogen, oxygen = state[off : off + 3]
                    growth = pbr_unit.build_growth(item["params"], item["model"], (0, 0, 0), 0)
                    mu, loss = growth.rates_at(par, temperature, x, nitrogen)
                    rx = (mu - loss) * x / 3600.0
                    transfer = growth.kla_h * (growth.oxygen_saturation - oxygen) / 3600.0
                    incoming = [
                        s for s in topology["streams"] if (s.get("target") or {}).get("unit") == item["unit"]["id"]
                    ]
                    total = q_in[item["unit"]["id"]]
                    mixed = np.zeros(3, dtype=np.float64)
                    for stream in incoming:
                        source = (stream.get("source") or {}).get("unit")
                        value = topology["feeds"].get(stream["id"]) if source is None else concentrations.get(source)
                        if value is None:
                            raise DynamicError(
                                "TOPOLOGY_UNRESOLVED", "A PBR inlet concentration could not be resolved."
                            )
                        mixed += topology["flows"].get(stream["id"], 0.0) * np.asarray(value)
                    inlet = mixed / total
                    dilution = total / item["volume_m3"]
                    net_x = rx + dilution * (inlet[0] - x)
                    net_n = -growth.nitrogen_quota * rx + dilution * (inlet[1] - nitrogen)
                    net_o = growth.oxygen_yield * rx + transfer + dilution * (inlet[2] - oxygen)
                    result[off : off + 7] = [net_x, net_n, net_o, rx, -growth.nitrogen_quota * rx, transfer, 0.0]
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
                _valid_state(state, units)
                if any(abs(float(t) - float(out)) <= 1e-7 for out in outputs):
                    times_out.append(float(t))
                    rows.append(np.asarray(state, dtype=np.float64))
            current = np.asarray(solved.states[-1], dtype=np.float64)
            while event_cursor < len(events) and abs(float(events[event_cursor][1]["time_s"]) - right) < 1e-7:
                current, event_cursor = _apply_event(current, events[event_cursor], units, event_log, event_cursor)
                if times_out and abs(times_out[-1] - right) < 1e-7:
                    rows[-1] = current.copy()
            if (
                sampler
                and scenario.get("downstream_cadence_s")
                and abs(right % scenario["downstream_cadence_s"]) < 1e-7
            ):
                if cancelled():
                    return EngineResult(
                        "cancelled",
                        {"code": "CANCELLED", "message": "Run cancelled.", "detail": {}},
                        {"t_s": np.asarray(times_out), "state": np.asarray(rows)},
                        _manifest(snapshot, started, event_log, controller_log, downstream),
                    )
                try:
                    result = sampler(
                        {
                            "time_s": right,
                            "units": {u["tag"]: current[i * 7 : i * 7 + 3].tolist() for i, u in enumerate(units)},
                        }
                    )
                    downstream.append({"time_s": right, **result})
                except Exception as exc:
                    downstream.append({"time_s": right, "status": "downstream_unconverged", "error": str(exc)[:300]})
                if downstream[-1].get("status") == "unconverged":
                    downstream[-1]["status"] = "downstream_unconverged"
            progress(min(1.0, right / duration))
        series: dict[str, np.ndarray] = {"t_s": np.asarray(times_out, dtype=np.float64)}
        forcing = [_profile_values(snapshot, start + float(t)) for t in times_out]
        series["par"] = np.asarray([value[0] for value in forcing], dtype=np.float64)
        series["temperature"] = np.asarray([value[1] for value in forcing], dtype=np.float64)
        matrix = np.asarray(rows, dtype=np.float64)
        for i, unit in enumerate(units):
            for j, channel in enumerate(("X", "N", "O2")):
                series[f"{unit['tag']}_{channel}"] = matrix[:, i * 7 + j]
        manifest = _manifest(snapshot, started, event_log, controller_log, downstream)
        manifest["balances"] = {
            unit["tag"]: {
                "biomass_generation_kg_m3": float(current[i * 7 + 3]),
                "nitrogen_consumption_kg_m3": float(current[i * 7 + 4]),
                "oxygen_transfer_kg_m3": float(current[i * 7 + 5]),
            }
            for i, unit in enumerate(units)
        }
        return EngineResult("succeeded", None, series, manifest)
    except DynamicError as exc:
        return EngineResult(
            "failed",
            {"code": exc.code, "message": exc.message, "detail": exc.detail},
            {"t_s": np.asarray(times_out), "state": np.asarray(rows)},
            _manifest(snapshot, started, event_log, controller_log, downstream),
        )
    except Exception as exc:
        error = {"code": "DYNAMIC_FAILED", "message": str(exc)[:600], "detail": {}}
        return EngineResult(
            "failed",
            error,
            {"t_s": np.asarray(times_out), "state": np.asarray(rows)},
            _manifest(snapshot, started, event_log, controller_log, downstream),
        )


def _valid_state(state: tuple[float, ...], units: list[dict[str, Any]]) -> None:
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
            if value < 0:
                # Tiny roundoff is tolerated; CVODE state is not altered mid-segment.
                continue
        growth = pbr_unit.build_growth(item["params"], item["model"], (0, 0, 0), 0)
        if growth.extinction * max(0.0, float(state[i * 7])) * growth.diameter > 1e6:
            raise DynamicError("OPTICS_TAU_MAX", "Optical depth exceeds the model limit.", {"unit": item["tag"]})


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
