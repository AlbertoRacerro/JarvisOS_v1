"""Deterministic DWSIM materialization of one Jarvis draft revision, verified by read-back (spec 155).

``expected`` derives the normalized materialization from the draft alone. ``plan`` lists the
exact MCP calls. ``materialize`` executes the plan in a fresh flowsheet, reads the result back
from the live MCP and the saved native case, normalizes it, and compares field by field. Any
difference refuses the solve with per-path diagnostics; the fingerprint is the digest of the
normalized read-back, so the same revision and tool versions give the same fingerprint.
"""

from __future__ import annotations

import hashlib
import json
import math
import shutil
import tempfile
import time
from pathlib import Path
from typing import Any
from uuid import uuid4
from xml.etree import ElementTree

from app.modules.process_stack.draft_models import COMPILER_VERSION, STREAM_SPECS, UNIT_REGISTRY
from app.modules.process_stack.dwsim import _mass_balance
from app.modules.process_stack.dwsim_mcp import DwsimMcpClient, DwsimMcpError

_REL_TOL = 1e-7
_ABS_TOL = 1e-9
_NATIVE_TO_TYPE = {native: spec.type for spec in UNIT_REGISTRY.values() for native in spec.native_types}


class MaterializationError(RuntimeError):
    def __init__(self, code: str, message: str, **detail: Any):
        super().__init__(message)
        self.code, self.detail = code, detail


def _streams(document: dict[str, Any]) -> list[dict[str, Any]]:
    return sorted((item for item in document["objects"].values() if item["kind"] == "stream"),
                  key=lambda item: item["tag"])


def _units(document: dict[str, Any]) -> list[dict[str, Any]]:
    return sorted((item for item in document["objects"].values() if item["kind"] == "unit"),
                  key=lambda item: item["tag"])


def _composition(document: dict[str, Any], stream: dict[str, Any]) -> dict[str, float]:
    given = stream["spec"].get("composition", {})
    return {name: float(given.get(name, 0.0)) for name in document["compounds"]}


def _unit_properties(unit: dict[str, Any]) -> dict[str, Any]:
    spec = UNIT_REGISTRY[unit["type"]]
    if not spec.modes:
        return {}
    properties: dict[str, Any] = {"CalcMode": spec.modes[unit["mode"]]}
    for param in spec.params_for(unit["mode"]):
        properties[param.dwsim_property] = float(unit["params"][param.key]["si"])
    return properties


def expected(document: dict[str, Any]) -> dict[str, Any]:
    """The normalized materialization the compiler must produce for this draft document."""
    by_id = document["objects"]
    connections = []
    for stream in _streams(document):
        if stream["target"]:
            connections.append(f"{stream['tag']}>{by_id[stream['target']['unit']]['tag']}:in{stream['target']['port']}")
        if stream["source"]:
            connections.append(f"{by_id[stream['source']['unit']]['tag']}:out{stream['source']['port']}>{stream['tag']}")
    return {
        "compounds": sorted(document["compounds"]),
        "property_package": document["property_package"],
        "objects": {item["tag"]: {"type": item["type"], "x": item["x"], "y": item["y"]}
                    for item in document["objects"].values()},
        "connections": sorted(connections),
        "feeds": {
            stream["tag"]: {
                **{arg: float(stream["spec"][key]["si"]) for key, (_kind, arg, _label) in STREAM_SPECS.items()},
                "composition": _composition(document, stream),
            }
            for stream in _streams(document) if stream["source"] is None
        },
        "units": {unit["tag"]: _unit_properties(unit) for unit in _units(document)},
    }


def plan(document: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    """Exact ordered MCP calls (without the flowsheet handle) that materialize the draft."""
    calls: list[tuple[str, dict[str, Any]]] = [
        ("dwsim_thermo_add_compounds", {"names": list(document["compounds"])}),
        ("dwsim_thermo_set_property_package", {"name": document["property_package"]}),
    ]
    for stream in _streams(document):
        args: dict[str, Any] = {"name": stream["tag"]}
        if stream["source"] is None:
            for key, (_kind, arg, _label) in STREAM_SPECS.items():
                args[arg] = float(stream["spec"][key]["si"])
            args["composition"] = _composition(document, stream)
        calls.append(("dwsim_stream_add_material", args))
    for unit in _units(document):
        calls.append(("dwsim_unitop_add", {"type": UNIT_REGISTRY[unit["type"]].dwsim_type, "name": unit["tag"]}))
    for item in sorted(document["objects"].values(), key=lambda value: value["tag"]):
        calls.append(("dwsim_graphic_edit", {"name": item["tag"], "x": item["x"], "y": item["y"]}))
    by_id = document["objects"]
    for stream in _streams(document):
        if stream["target"]:
            calls.append(("dwsim_unitop_connect", {"unitop": by_id[stream["target"]["unit"]]["tag"],
                                                   "feed_stream": stream["tag"], "feed_port": stream["target"]["port"]}))
        if stream["source"]:
            calls.append(("dwsim_unitop_connect", {"unitop": by_id[stream["source"]["unit"]]["tag"],
                                                   "product_stream": stream["tag"],
                                                   "product_port": stream["source"]["port"]}))
    for unit in _units(document):
        properties = _unit_properties(unit)
        if properties:
            calls.append(("dwsim_unitop_set", {"name": unit["tag"], "properties": properties}))
    return calls


def _xml_root(path: Path) -> ElementTree.Element:
    import zipfile

    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as archive:
            name = next(item for item in archive.namelist() if item.lower().endswith(".xml"))
            return ElementTree.fromstring(archive.read(name))
    return ElementTree.parse(path).getroot()


def _float(text: str | None) -> float | str | None:
    if text is None:
        return None
    try:
        return float(text)
    except ValueError:
        return text


def read_back(client: DwsimMcpClient, flow: str, case_path: Path, exp: dict[str, Any]) -> dict[str, Any]:
    """Normalized materialization as DWSIM actually holds it (live MCP + saved native case)."""
    root = _xml_root(case_path)
    native_types = {node.findtext("ComponentName"): (node.findtext("Type") or "").rsplit(".", 1)[-1]
                    for node in root.findall("./SimulationObjects/SimulationObject")}
    sim_nodes = {node.findtext("ComponentName"): node for node in root.findall("./SimulationObjects/SimulationObject")}
    tags: dict[str, str] = {}
    objects: dict[str, Any] = {}
    for node in root.findall("./GraphicObjects/GraphicObject"):
        native_id, tag = node.findtext("Name"), node.findtext("Tag")
        if not native_id or native_id not in native_types or not tag:
            continue
        tags[native_id] = tag
        native = native_types[native_id]
        objects[tag] = {"type": _NATIVE_TO_TYPE.get(native, native), "x": round(float(node.findtext("X") or 0)),
                        "y": round(float(node.findtext("Y") or 0))}
    # Native connectors: a unit input names its stream in AttachedFromObjID, an output in AttachedToObjID.
    # Both the unit side and the stream side are read; a one-sided attachment is itself a mismatch.
    unit_side: set[str] = set()
    stream_side: set[str] = set()
    for node in root.findall("./GraphicObjects/GraphicObject"):
        tag = tags.get(node.findtext("Name") or "")
        if tag is None:
            continue
        is_stream = objects[tag]["type"] == "MaterialStream"
        for direction in ("Input", "Output"):
            for index, conn in enumerate(node.findall(f"./{direction}Connectors/Connector")):
                if conn.get("IsAttached", "false").lower() != "true":
                    continue
                other_id = conn.get("AttachedFromObjID") if direction == "Input" else conn.get("AttachedToObjID")
                other = tags.get(other_id or "", "?")
                other_port = conn.get("AttachedFromConnIndex") if direction == "Input" else conn.get("AttachedToConnIndex")
                if not is_stream:
                    unit_side.add(f"{other}>{tag}:in{index}" if direction == "Input" else f"{tag}:out{index}>{other}")
                elif direction == "Input":
                    stream_side.add(f"{other}:out{other_port}>{tag}")
                else:
                    stream_side.add(f"{tag}>{other}:in{other_port}")
    if not tags:
        raise MaterializationError("connector_readback_unavailable", "Saved DWSIM case has no graphic objects")
    connections = sorted(unit_side | stream_side | {f"one-sided:{item}" for item in unit_side ^ stream_side})
    package_node = root.find("./PropertyPackages/PropertyPackage")
    package = None if package_node is None else (package_node.findtext("ComponentName") or package_node.findtext("Tag"))
    compounds = sorted(name.text for name in root.findall("./Compounds/Compound/Name") if name.text)
    feeds: dict[str, Any] = {}
    for tag in exp["feeds"]:
        if tag not in objects:
            continue
        result = client.call("dwsim_stream_get_results", {"flowsheet_id": flow, "name": tag}, 30)
        mixture: dict[str, Any] = next(
            (phase for phase in result.get("phases", []) if phase.get("name") == "Mixture"), {})
        feeds[tag] = {
            **{arg: result.get(arg) for _key, (_kind, arg, _label) in STREAM_SPECS.items()},
            "composition": {name: value.get("mass_fraction")
                            for name, value in sorted((mixture.get("compounds") or {}).items())},
        }
    units: dict[str, Any] = {}
    for native_id, tag in tags.items():
        if objects[tag]["type"] in UNIT_REGISTRY:
            wanted = exp["units"].get(tag) or {}
            node = sim_nodes[native_id]
            units[tag] = {name: _float(node.findtext(name)) if name != "CalcMode" else node.findtext(name)
                          for name in wanted}
    return {"compounds": compounds, "property_package": package, "objects": objects,
            "connections": sorted(connections), "feeds": feeds, "units": units}


def _same(actual: Any, wanted: Any) -> bool:
    if isinstance(wanted, float) or isinstance(actual, float):
        try:
            return math.isclose(float(actual), float(wanted), rel_tol=_REL_TOL, abs_tol=_ABS_TOL)
        except (TypeError, ValueError):
            return False
    return actual == wanted


def compare(exp: dict[str, Any], actual: dict[str, Any]) -> list[dict[str, Any]]:
    """Field-by-field differences between expected and read-back materializations."""
    diffs: list[dict[str, Any]] = []

    def walk(path: str, wanted: Any, got: Any) -> None:
        if isinstance(wanted, dict) and isinstance(got, dict):
            for key in sorted(set(wanted) | set(got), key=str):
                if key not in got:
                    diffs.append({"path": f"{path}.{key}", "expected": wanted[key], "actual": "<missing>"})
                elif key not in wanted:
                    diffs.append({"path": f"{path}.{key}", "expected": "<absent>", "actual": got[key]})
                else:
                    walk(f"{path}.{key}", wanted[key], got[key])
        elif isinstance(wanted, list) and isinstance(got, list):
            for item in sorted(set(map(str, wanted)) - set(map(str, got))):
                diffs.append({"path": f"{path}[{item}]", "expected": item, "actual": "<missing>"})
            for item in sorted(set(map(str, got)) - set(map(str, wanted))):
                diffs.append({"path": f"{path}[{item}]", "expected": "<absent>", "actual": item})
        elif not _same(got, wanted):
            diffs.append({"path": path, "expected": wanted, "actual": got})

    for section in ("compounds", "property_package", "objects", "connections", "feeds", "units"):
        walk(section, exp[section], actual.get(section))
    return diffs


def _stable(value: Any) -> Any:
    if isinstance(value, float):
        return format(value, ".9g")
    if isinstance(value, dict):
        return {str(key): _stable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_stable(item) for item in value]
    return value


def fingerprint(normalized: dict[str, Any], *, dwsim_version: str, mcp_sha256: str) -> str:
    payload = {"compiler_version": COMPILER_VERSION, "dwsim_version": dwsim_version, "mcp_sha256": mcp_sha256,
               "materialization": _stable(normalized)}
    return "sha256:" + hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _stream_result(result: dict[str, Any]) -> dict[str, Any]:
    phases = {phase.get("name"): phase for phase in result.get("phases", []) if isinstance(phase, dict)}
    mixture = phases.get("Mixture", {})
    return {
        "temperature_K": result.get("temperature_K"),
        "pressure_Pa": result.get("pressure_Pa"),
        "mass_flow_kg_s": result.get("mass_flow_kg_s"),
        "molar_flow_mol_s": result.get("molar_flow_mol_s"),
        "vapor_fraction": phases.get("Vapor", {}).get("fraction"),
        "mass_fractions": {name: value.get("mass_fraction")
                           for name, value in sorted((mixture.get("compounds") or {}).items())},
    }


def materialize(document: dict[str, Any], *, action: str, client: DwsimMcpClient, dwsim_version: str,
                mcp_sha256: str, label: str, keep_case: Path | None = None) -> dict[str, Any]:
    """Compile, read back, compare; then check (validate) or check+solve (run). Refuses on mismatch."""
    started = time.perf_counter()
    exp = expected(document)
    outcome: dict[str, Any] = {"expected_fingerprint": fingerprint(exp, dwsim_version=dwsim_version,
                                                                   mcp_sha256=mcp_sha256)}
    with tempfile.TemporaryDirectory(prefix="jarvis-draft-") as tmp:
        case = Path(tmp) / "materialized.dwxml"
        step = "dwsim_flowsheet_create"
        try:
            created = client.call("dwsim_flowsheet_create", {"name": label}, 30)
            flow = created.get("flowsheet_id")
            if not isinstance(flow, str):
                raise MaterializationError("materialization_failed", "DWSIM did not create a flowsheet")
            for step, args in plan(document):
                client.call(step, {"flowsheet_id": flow, **args}, 60)
            step = "dwsim_flowsheet_save"
            client.call("dwsim_flowsheet_save", {"flowsheet_id": flow, "filepath": str(case), "compressed": False}, 60)
            step = "read_back"
            actual = read_back(client, flow, case, exp)
        except DwsimMcpError as exc:
            raise MaterializationError("materialization_failed", f"DWSIM refused {step}",
                                       step=step, dwsim_code=getattr(exc, "code", None)) from exc
        diffs = compare(exp, actual)
        outcome.update(materialization_fingerprint=fingerprint(actual, dwsim_version=dwsim_version,
                                                                mcp_sha256=mcp_sha256),
                       materialization_diffs=diffs, materialized_object_count=len(actual["objects"]))
        if diffs:
            outcome.update(status="materialization_mismatch", compile_seconds=round(time.perf_counter() - started, 3))
            return outcome
        check = client.call("dwsim_flowsheet_check", {"flowsheet_id": flow}, 30)
        outcome["dwsim_check"] = {
            "ready": check.get("ready"),
            "findings": [{"severity": item.get("severity"), "code": item.get("code"), "object": item.get("object"),
                          "message": item.get("message"), "fix": item.get("fix"), "source": "dwsim"}
                         for item in check.get("findings", []) if isinstance(item, dict)][:40],
        }
        if action == "validate":
            outcome.update(status="validated" if check.get("ready") else "check_failed",
                           compile_seconds=round(time.perf_counter() - started, 3))
            return outcome
        if not check.get("ready"):
            outcome.update(status="check_failed", compile_seconds=round(time.perf_counter() - started, 3))
            return outcome
        solve = client.call("dwsim_solve_run", {"flowsheet_id": flow, "timeout_s": 120}, 150)
        solved_case = Path(tmp) / "solved.dwxmz"
        client.call("dwsim_flowsheet_save", {"flowsheet_id": flow, "filepath": str(solved_case), "compressed": True}, 60)
        listed = client.call("dwsim_flowsheet_list_objects", {"flowsheet_id": flow}, 30).get("objects", [])
        object_status = [{"tag": item.get("name"), "calculated": item.get("calculated"), "error": item.get("error", "")}
                         for item in listed if isinstance(item, dict)]
        streams = {stream["tag"]: _stream_result(client.call("dwsim_stream_get_results",
                                                              {"flowsheet_id": flow, "name": stream["tag"]}, 30))
                   for stream in _streams(document)}
        units = {}
        for unit in _units(document):
            reported = client.call("dwsim_unitop_get_results", {"flowsheet_id": flow, "name": unit["tag"]}, 30)
            units[unit["tag"]] = {"calculated": reported.get("calculated"), "error": reported.get("error", ""),
                                  "reported": reported.get("properties", {})}
        try:
            tagged = [{**item, "tag": item.get("name")} for item in listed if isinstance(item, dict)]
            residual, boundary = _mass_balance(client, flow, solved_case, tagged)
            balance = {"status": "calculated", "residual_kg_s": residual, "boundary_kg_s": boundary}
        except Exception as exc:  # noqa: BLE001 - balance is reported, never invented
            balance = {"status": "unavailable", "error": getattr(exc, "code", type(exc).__name__)}
        errors = solve.get("errors") if isinstance(solve.get("errors"), list) else []
        failed = [item for item in object_status if item["calculated"] is False or item["error"]]
        outcome.update(
            status="completed" if solve.get("ok") is True and not errors and not failed else "failed",
            solve={"ok": solve.get("ok"), "errors": errors[:20], "failed_objects": failed[:20]},
            streams=streams, units=units, mass_balance=balance,
            solved_case_sha256=hashlib.sha256(solved_case.read_bytes()).hexdigest(),
            compile_seconds=round(time.perf_counter() - started, 3),
        )
        if keep_case is not None:
            keep_case.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(solved_case, keep_case)
    return outcome


def new_run_id() -> str:
    return uuid4().hex
