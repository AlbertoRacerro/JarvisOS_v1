"""Fresh-flowsheet sequential modular execution for mixed Process drafts."""

from __future__ import annotations

import copy
import math
import tempfile
import time
from pathlib import Path
from typing import Any

from app.modules.process_stack import culture, draft_compiler, mixed
from app.modules.process_stack.dwsim_mcp import DwsimMcpClient


class SegmentFailure(RuntimeError):
    def __init__(self, segment: str, detail: Any) -> None:
        super().__init__(str(detail))
        self.segment = segment
        self.detail = detail


class _ClosingClient:
    """Keep the unchanged compiler path while closing the mixed path's fresh handle."""

    def __init__(self, client: DwsimMcpClient) -> None:
        self.client = client
        self.flowsheets: list[str] = []

    def call(self, name: str, args: dict[str, Any], timeout: float) -> Any:
        result = self.client.call(name, args, timeout)
        if name == "dwsim_flowsheet_create":
            self.flowsheets.append(result["flowsheet_id"])
        elif name == "dwsim_flowsheet_load":
            self.flowsheets.append(result["flowsheet_id"])
        return result

    def close(self) -> None:
        for flow in self.flowsheets:
            try:
                self.client.call("dwsim_flowsheet_close", {"flowsheet_id": flow}, 30)
            except Exception:  # noqa: BLE001 - the process closes after the Run
                pass


def _light(document: dict[str, Any], client: DwsimMcpClient, *, label: str,
           remaining_s: float) -> dict[str, Any]:
    """Same verified build as materialize, skipping only full result catalogue work."""
    wrapper = _ClosingClient(client)
    exp = draft_compiler.expected(document)
    flow = ""
    started = time.monotonic()
    try:
        with tempfile.TemporaryDirectory(prefix="jarvis-mixed-") as temp:
            case = Path(temp) / "segment.dwxml"
            flow = wrapper.call("dwsim_flowsheet_create", {"name": label}, min(30, remaining_s))["flowsheet_id"]
            for name, args in draft_compiler.plan(document):
                wrapper.call(name, {"flowsheet_id": flow, **args}, min(60, max(0.1, remaining_s - (time.monotonic() - started))))
            wrapper.call("dwsim_flowsheet_save", {"flowsheet_id": flow, "filepath": str(case),
                                                       "compressed": False}, min(60, remaining_s))
            actual = draft_compiler.read_back(wrapper, flow, case, exp)
            diffs = draft_compiler.compare(exp, actual)
            if diffs:
                raise SegmentFailure(label, {"code": "materialization_mismatch", "diffs": diffs})
            check = wrapper.call("dwsim_flowsheet_check", {"flowsheet_id": flow}, min(30, remaining_s))
            if not check.get("ready"):
                raise SegmentFailure(label, {"code": "check_failed", "findings": check.get("findings", [])})
            solve = wrapper.call("dwsim_solve_run", {"flowsheet_id": flow,
                                                      "timeout_s": min(120, max(1, remaining_s))},
                                 min(150, max(1, remaining_s)))
            if solve.get("ok") is not True or solve.get("errors"):
                raise SegmentFailure(label, {"code": "solve_failed", "errors": solve.get("errors", [])})
            streams = {stream["tag"]: draft_compiler._stream_result(wrapper.call(
                "dwsim_stream_get_results", {"flowsheet_id": flow, "name": stream["tag"]},
                min(30, remaining_s))) for stream in document["objects"].values()
                if stream["kind"] == "stream" and stream["type"] != "EnergyStream"}
            return {"status": "completed", "streams": streams,
                    "materialization_fingerprint": draft_compiler.fingerprint(actual, dwsim_version="10.2.9",
                                                                            mcp_sha256=""),
                    "elapsed_s": time.monotonic() - started}
    finally:
        wrapper.close()


def _full(document: dict[str, Any], client: DwsimMcpClient, *, label: str, keep_case: Path | None,
          dwsim_version: str, mcp_sha256: str, action: str = "run") -> dict[str, Any]:
    wrapper = _ClosingClient(client)
    try:
        result = draft_compiler.materialize(document, action=action, client=wrapper,
                                            dwsim_version=dwsim_version, mcp_sha256=mcp_sha256,
                                            label=label, keep_case=keep_case)
        if result["status"] not in {"completed", "validated"}:
            raise SegmentFailure(label, result)
        return result
    finally:
        wrapper.close()


def _feeds(document: dict[str, Any]) -> list[dict[str, Any]]:
    return sorted((stream for stream in document["objects"].values() if stream["kind"] == "stream"
                   and stream["type"] != "EnergyStream" and stream.get("source") is None),
                  key=lambda item: item["tag"])


def _state_from_spec(feed: dict[str, Any]) -> dict[str, Any]:
    spec = feed["spec"]
    fractions = copy.deepcopy(spec["composition"])
    if spec.get("composition_basis") == "mole":
        fractions = {name: value * culture.MOLECULAR_WEIGHT_KG_PER_KMOL[name]
                     for name, value in fractions.items()}
        total = sum(fractions.values())
        fractions = {name: value / total for name, value in fractions.items()}
    return {"temperature_K": spec.get("temperature", {}).get("si", 298.15),
            "pressure_Pa": spec["pressure"]["si"], "mass_flow_kg_s": spec.get("mass_flow", {}).get("si", 0.0),
            "mass_fractions": fractions, "vapor_fraction": 0.0,
            "culture": {field: None for field in mixed.CULTURE_FIELDS} |
                       {"ph": (spec.get("culture") or {}).get("ph", {}).get("si")}}


def _feed_spec(state: dict[str, Any]) -> dict[str, Any]:
    fractions = state["mass_fractions"]
    total = sum(fractions.values())
    return {"temperature": {"si": float(state["temperature_K"])},
            "pressure": {"si": float(state["pressure_Pa"])},
            "mass_flow": {"si": float(state["mass_flow_kg_s"])},
            "composition_basis": "mass", "composition": {key: float(value) / total
                                                           for key, value in fractions.items()}}


def _segment_document(document: dict[str, Any], ids: list[str], known: dict[str, dict[str, Any]]) -> dict[str, Any]:
    selected = set(ids)
    objects: dict[str, dict[str, Any]] = {uid: copy.deepcopy(document["objects"][uid]) for uid in ids}
    for original in document["objects"].values():
        if original["kind"] != "stream":
            continue
        source = (original.get("source") or {}).get("unit")
        target = (original.get("target") or {}).get("unit")
        if source not in selected and target not in selected:
            continue
        stream = copy.deepcopy(original)
        if source is None:
            stream["_original_feed"] = True
        elif source not in selected:
            stream["source"] = None
            if original["tag"] not in known:
                raise SegmentFailure("boundary", f"Missing state for boundary feed {original['tag']}")
            stream["spec"] = _feed_spec(known[original["tag"]])
        if target not in selected:
            stream["target"] = None
        objects[stream["id"]] = stream
    return {"schema_version": document["schema_version"], "name": document.get("name", ""),
            "compounds": document["compounds"], "property_package": document["property_package"],
            "objects": objects, "reactions": document.get("reactions", {})}


def _seed(document: dict[str, Any], part: dict[str, Any]) -> dict[str, dict[str, Any]]:
    feeds = _feeds(document)
    if not feeds:
        raise SegmentFailure("initial_guess", "A mixed draft needs a feed")
    preferred = next((item for item in feeds if item.get("spec", {}).get("culture") is not None), feeds[0])
    base = _state_from_spec(preferred)
    total = sum(float(item["spec"].get("mass_flow", {}).get("si", 0)) for item in feeds)
    units = document["objects"]
    result = {}
    for uid in part["consumed"]:
        stream = next(item for item in document["objects"].values() if item["kind"] == "stream"
                      and (item.get("source") or {}).get("unit") == uid)
        target = (stream.get("target") or {}).get("unit")
        scale = 1e-3 if target is not None and units[target]["type"] == "HeatExchanger" else 1e-6
        state = copy.deepcopy(base)
        state["mass_flow_kg_s"] = scale * total
        for field in mixed.CULTURE_FIELDS:
            state["culture"][field] = 0.0
        for feed in feeds:
            culture_spec = feed.get("spec", {}).get("culture")
            if culture_spec is not None:
                for field in mixed.CULTURE_FIELDS:
                    if field not in culture_spec:
                        state["culture"][field] = None
        state["culture"]["ph"] = base["culture"].get("ph")
        result[stream["tag"]] = state
    return result


def _flatten(state: dict[str, Any]) -> dict[str, float | None]:
    row = {name: state.get(name) for name in ("temperature_K", "pressure_Pa", "mass_flow_kg_s")}
    row.update({"mass_fraction." + name: value for name, value in state.get("mass_fractions", {}).items()})
    row.update({name: state.get("culture", {}).get(name) for name in mixed.CULTURE_FIELDS})
    return row


def _from_stream(result: dict[str, Any], prior: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"temperature_K": result.get("temperature_K"), "pressure_Pa": result.get("pressure_Pa"),
            "mass_flow_kg_s": result.get("mass_flow_kg_s"), "mass_fractions": result.get("mass_fractions", {}),
            "vapor_fraction": result.get("vapor_fraction"),
            "culture": copy.deepcopy((prior or {}).get("culture") or {})}


def _culture_for_feed(feed: dict[str, Any], result: dict[str, Any], prior: dict[str, Any] | None) -> dict[str, Any]:
    if prior is not None:
        return copy.deepcopy(prior.get("culture") or {})
    specification = feed.get("spec", {}).get("culture")
    if specification is None:
        return {}
    density = culture._density(result)
    if density is None:
        raise SegmentFailure(feed["tag"], "CULTURE_DENSITY_UNAVAILABLE")
    result_state = {name: (float(specification[name]["si"]) / density if name not in {"salinity", "ph"}
                           else float(specification[name]["si"])) if name in specification else None
                    for name in (*mixed.CULTURE_FIELDS, "ph")}
    return result_state


def _propagate_culture(segment: dict[str, Any], result: dict[str, Any],
                       boundary: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    states: dict[str, dict[str, Any]] = {}
    streams = result["streams"]
    for feed in _feeds(segment):
        states[feed["tag"]] = _culture_for_feed(
            feed, streams[feed["tag"]], None if feed.get("_original_feed") else boundary.get(feed["tag"]))
    units = sorted((unit for unit in segment["objects"].values() if unit["kind"] == "unit"),
                   key=lambda item: item["tag"])
    for _ in range(10000):
        changed = False
        for unit in units:
            incoming = sorted((stream for stream in segment["objects"].values() if stream["kind"] == "stream"
                               and (stream.get("target") or {}).get("unit") == unit["id"]
                               and stream["type"] != "EnergyStream"), key=lambda item: item["target"]["port"])
            outgoing = sorted((stream for stream in segment["objects"].values() if stream["kind"] == "stream"
                               and (stream.get("source") or {}).get("unit") == unit["id"]
                               and stream["type"] != "EnergyStream"), key=lambda item: item["source"]["port"])
            if any(stream["tag"] not in states for stream in incoming):
                continue
            values = [states[stream["tag"]] for stream in incoming]
            if not any(values):
                continue
            if unit["type"] == "Mixer":
                flows = [float(streams[stream["tag"]]["mass_flow_kg_s"]) for stream in incoming]
                total = sum(flows)
                if total <= 0:
                    raise SegmentFailure(unit["tag"], "CULTURE_MIXER_FLOW_INVALID")
                result_culture = {field: (None if any(value.get(field) is None for value in values if value)
                                          else sum(flow * float(value.get(field, 0.0) or 0.0)
                                                   for flow, value in zip(flows, values, strict=True)) / total)
                                  for field in mixed.CULTURE_FIELDS}
                ph_values = [value.get("ph") for value in values]
                result_culture["ph"] = (ph_values[0] if all(value is not None for value in ph_values)
                                        and max(ph_values) - min(ph_values) <= 0.01 else None)
                output_values = [result_culture] * len(outgoing)
            elif unit["type"] == "HeatExchanger":
                output_values = values
            else:
                output_values = [values[0]] * len(outgoing)
            for stream, value in zip(outgoing, output_values, strict=True):
                tag = stream["tag"]
                vapor = streams[tag].get("vapor_fraction")
                if vapor is None or vapor > 1e-6 or culture._density(streams[tag]) is None:
                    raise SegmentFailure(tag, "CULTURE_PHASE_NOT_LIQUID" if vapor is not None else
                                         "CULTURE_DENSITY_UNAVAILABLE")
                if tag not in states or states[tag] != value:
                    states[tag] = copy.deepcopy(value)
                    changed = True
        if not changed:
            return states
    raise SegmentFailure("culture", "culture native recycle did not converge in 10000 sweeps")


def _evaluate(document: dict[str, Any], part: dict[str, Any], tear: dict[str, dict[str, Any]],
              *, client: DwsimMcpClient, full: bool, run_dir: Path, iteration: int,
              dwsim_version: str, mcp_sha256: str, remaining_s: float) -> dict[str, Any]:
    objects = document["objects"]
    known = {**{feed["tag"]: _state_from_spec(feed) for feed in _feeds(document)}, **copy.deepcopy(tear)}
    stream_results: dict[str, Any] = {}
    unit_results: dict[str, Any] = {}
    segment_records: list[dict[str, Any]] = []
    segments = part["segments"]
    max_level = max(part["levels"].values(), default=0)
    for level in range(max_level + 1):
        for index, ids in enumerate(segments):
            if part["levels"][ids[0]] != level:
                continue
            segment = _segment_document(document, ids, known)
            label = f"mixed-{iteration}-{index}"
            try:
                if full:
                    outcome = _full(segment, client, label=label,
                                    keep_case=run_dir / f"segment-{index}.dwxmz",
                                    dwsim_version=dwsim_version, mcp_sha256=mcp_sha256)
                else:
                    outcome = _light(segment, client, label=label, remaining_s=remaining_s)
            except Exception as exc:
                if isinstance(exc, SegmentFailure):
                    raise
                raise SegmentFailure(label, {"code": type(exc).__name__, "message": str(exc)}) from exc
            states = _propagate_culture(segment, outcome, known)
            for tag, result in outcome["streams"].items():
                original = next((item for item in objects.values() if item["kind"] == "stream" and item["tag"] == tag), None)
                if original is None:
                    continue
                prior = known.get(tag)
                state = _from_stream(result, prior)
                if tag in states:
                    state["culture"] = states[tag]
                known[tag] = state
                stream_results[tag] = {**result, "owner": "dwsim"}
            unit_results.update({tag: {**value, "owner": "dwsim"}
                                 for tag, value in outcome.get("units", {}).items()})
            segment_records.append({"id": index, "units": [objects[uid]["tag"] for uid in ids],
                                    "level": level, "materialization_fingerprint": outcome.get("materialization_fingerprint"),
                                    "solved_case_sha256": outcome.get("solved_case_sha256")})
        for uid in part["jarvis_units"]:
            if part["levels"][uid] != level:
                continue
            unit = objects[uid]
            incoming = next(stream for stream in objects.values() if stream["kind"] == "stream"
                            and (stream.get("target") or {}).get("unit") == uid)
            if incoming["tag"] not in known:
                raise SegmentFailure(unit["tag"], "Jarvis inlet has no DWSIM state")
            inlet = known[incoming["tag"]]
            if unit["type"] != "SpecifiedSeparator":
                raise SegmentFailure(unit["tag"], "Unknown Jarvis evaluator")
            outputs = mixed.separator(inlet,
                                      float(unit["params"]["biomass_recovery"]["si"]),
                                      float(unit["params"]["concentration_factor"]["si"]))
            streams = sorted((stream for stream in objects.values() if stream["kind"] == "stream"
                              and (stream.get("source") or {}).get("unit") == uid),
                             key=lambda item: item["source"]["port"])
            for stream, state in zip(streams, outputs, strict=True):
                known[stream["tag"]] = state
                stream_results[stream["tag"]] = {**state, "state_source": "jarvis_unit",
                                                  "owner": "jarvis_bio"}
            unit_results[unit["tag"]] = {"owner": "jarvis_bio", "calculated": True,
                                         "evaluator": "jarvis.specified_separator", "version": 1,
                                         "fidelity": "screening — specified performance, not a mechanistic separator",
                                         "caveats": ["Dissolved species follow the carrier.",
                                                     "No energy or pressure effect."],
                                         "reported": {"concentrate_flow_kg_s": outputs[0]["mass_flow_kg_s"],
                                                      "clarified_flow_kg_s": outputs[1]["mass_flow_kg_s"]}}
    produced: dict[str, dict[str, Any]] = {}
    for uid in part["consumed"]:
        unit = objects[uid]
        inlet = next(stream for stream in objects.values() if stream["kind"] == "stream"
                     and (stream.get("target") or {}).get("unit") == uid)
        outlet = next(stream for stream in objects.values() if stream["kind"] == "stream"
                      and (stream.get("source") or {}).get("unit") == uid)
        if inlet["tag"] not in known:
            raise SegmentFailure(unit["tag"], "Consumed tear inlet has no solved state")
        produced[outlet["tag"]] = known[inlet["tag"]]
        unit_results[unit["tag"]] = {"owner": "jarvis_bio", "calculated": True,
                                     "label": "Converged by Jarvis (cross-engine tear)",
                                     "reported": {"Mass Flow Error": (known[inlet["tag"]]["mass_flow_kg_s"]
                                                                      - tear[outlet["tag"]]["mass_flow_kg_s"]) * 3600,
                                                  "Temperature Error": known[inlet["tag"]]["temperature_K"]
                                                                       - tear[outlet["tag"]]["temperature_K"],
                                                  "Pressure Error": known[inlet["tag"]]["pressure_Pa"]
                                                                    - tear[outlet["tag"]]["pressure_Pa"]}}
    return {"produced": produced, "streams": stream_results, "units": unit_results,
            "segments": segment_records, "known": known}


def run(document: dict[str, Any], *, action: str, client: DwsimMcpClient,
        dwsim_version: str, mcp_sha256: str, run_dir: Path) -> dict[str, Any]:
    part = mixed.partition(document)
    initial = _seed(document, part)
    started = time.monotonic()
    if action == "validate":
        try:
            for index, ids in enumerate(part["segments"]):
                segment = _segment_document(document, ids, initial | {feed["tag"]: _state_from_spec(feed)
                                                                    for feed in _feeds(document)})
                _full(segment, client, label=f"mixed-validate-{index}", keep_case=None,
                      dwsim_version=dwsim_version, mcp_sha256=mcp_sha256, action="validate")
        except SegmentFailure as exc:
            return {"status": "segment_failed", "mixed_solve": {"status": "segment_failed",
                    "failed_segment": exc.segment, "errors": exc.detail}}
        return {"status": "validated", "mixed_solve": {"status": "validated", "partition": part}}
    tear = initial
    best_tear = copy.deepcopy(tear)
    best_residual = math.inf
    omega = 1.0
    growth_events = 0
    history: list[dict[str, Any]] = []
    reason = "max_iterations"
    status = "unconverged"
    last: dict[str, Any] | None = None
    for iteration in range(1, mixed.MAX_ITERATIONS + 1):
        remaining = mixed.WALL_BUDGET_S - (time.monotonic() - started)
        reserve = max(3.0, len(part["segments"]) * 4.5)
        if remaining < len(part["segments"]) * 3 + reserve:
            reason = "wall_budget"
            break
        try:
            candidate = _evaluate(document, part, tear, client=client, full=False, run_dir=run_dir,
                                  iteration=iteration, dwsim_version=dwsim_version,
                                  mcp_sha256=mcp_sha256, remaining_s=remaining)
        except SegmentFailure as exc:
            return {"status": "segment_failed", "mixed_solve": {"status": "segment_failed",
                    "reason": "segment_failed", "iteration": iteration, "failed_segment": exc.segment,
                    "errors": exc.detail, "history": history, "partition": part}}
        last = candidate
        per_tear = {tag: mixed.residual(_flatten(tear[tag]), _flatten(output))
                    for tag, output in candidate["produced"].items()}
        max_residual, worst_tag = max(((item[0], tag) for tag, item in per_tear.items()), default=(0.0, ""))
        worst_field = per_tear[worst_tag][1] if worst_tag else ""
        history.append({"iteration": iteration, "omega": omega, "max_normalized_residual": max_residual,
                        "worst_tear": worst_tag, "worst_field": worst_field,
                        "residuals": {tag: item[2] for tag, item in per_tear.items()}})
        if max_residual <= 1:
            status = "completed"
            reason = "converged"
            break
        if max_residual > 1.5 * best_residual:
            growth_events += 1
            if growth_events >= 4:
                reason = "damping_exhausted"
                break
            omega = max(omega / 2, 0.125)
            tear = copy.deepcopy(best_tear)
            continue
        if max_residual < best_residual:
            best_residual = max_residual
            best_tear = copy.deepcopy(tear)
        updated = copy.deepcopy(tear)
        for tag, output in candidate["produced"].items():
            for name in ("temperature_K", "pressure_Pa", "mass_flow_kg_s"):
                updated[tag][name] += omega * (output[name] - tear[tag][name])
            for name, value in output["mass_fractions"].items():
                updated[tag]["mass_fractions"][name] += omega * (value - tear[tag]["mass_fractions"][name])
            for name in mixed.CULTURE_FIELDS:
                a, b = tear[tag]["culture"].get(name), output.get("culture", {}).get(name)
                updated[tag]["culture"][name] = (a + omega * (b - a)) if a is not None and b is not None else b
            updated[tag]["culture"]["ph"] = output.get("culture", {}).get("ph")
        tear = updated
    try:
        final = _evaluate(document, part, tear, client=client, full=True, run_dir=run_dir,
                          iteration=len(history), dwsim_version=dwsim_version,
                          mcp_sha256=mcp_sha256,
                          remaining_s=mixed.WALL_BUDGET_S - (time.monotonic() - started))
    except SegmentFailure as exc:
        return {"status": "segment_failed", "mixed_solve": {"status": "segment_failed",
                "reason": "full_path_failed", "iteration": len(history), "failed_segment": exc.segment,
                "errors": exc.detail, "history": history, "partition": part}}
    if last is not None:
        for tag, output in final["produced"].items():
            if mixed.residual(_flatten(last["produced"][tag]), _flatten(output))[0] > 1:
                status, reason = "segment_failed", "light_full_mismatch"
                break
    return {"status": status, "streams": final["streams"], "units": final["units"],
            "process_fingerprint": mixed.fingerprint(document, part),
            "mixed_solve": {"status": status, "reason": reason, "version": mixed.MIXED_SOLVE_VERSION,
                            "method": "direct_substitution", "history": history,
                            "partition": {**part, "segments": final["segments"]},
                            "limits": {"iterations": mixed.MAX_ITERATIONS, "wall_s": mixed.WALL_BUDGET_S},
                            "elapsed_s": time.monotonic() - started},
            "materialization_fingerprint": "mixed-segments"}
