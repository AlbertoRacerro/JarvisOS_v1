"""Jarvis-owned process draft: revisions, typed edits, validation and proposals (spec 155).

The draft is the authoritative editable flowsheet. Edits never contact DWSIM; they apply
typed operations to a canonical JSON document and write an immutable revision under
compare-and-swap. DWSIM is reached only through ``draft_compiler`` on Validate/Run.
"""

from __future__ import annotations

import copy
import hashlib
import json
import math
import os
import re
from datetime import UTC, datetime
from functools import lru_cache
from pathlib import Path
from typing import Any
from uuid import uuid4

from pydantic import BaseModel

from app.core.paths import build_paths
from app.modules.engineering.refs import Quantity
from app.modules.process_stack._common import EvaluationRefusal, magnitude
from app.modules.process_stack.draft_models import (
    COMPILER_VERSION,
    COMPOUNDS,
    MAX_OBJECTS,
    PROPERTY_PACKAGES,
    QUANTITY_UNITS,
    STREAM_SPECS,
    UNIT_REGISTRY,
    UNSUPPORTED_TYPES,
    AddStream,
    AddUnit,
    Connect,
    Delete,
    Disconnect,
    DraftQuantity,
    Move,
    ParamSpec,
    ProposalRequest,
    Rename,
    SetReactions,
    SetRoute,
    SetStreamSpec,
    SetThermo,
    SetUnitParams,
    UnitSpec,
)
from app.modules.process_stack.editor import _lock
from app.modules.workspaces.service import get_workspace

_COMPOSITION_TOL = 1e-6


@lru_cache(maxsize=1)
def _capability_manifest() -> dict[str, Any]:
    path = Path(__file__).with_name("dwsim_10_2_9_manifest.json")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:  # a missing checked-in contract is a packaging defect
        raise RuntimeError("DWSIM 10.2.9 capability manifest is unavailable") from exc
    if value.get("runtime") != "DWSIM 10.2.9" or not isinstance(value.get("objects"), dict):
        raise RuntimeError("DWSIM capability manifest has an invalid identity")
    return value


class DraftError(RuntimeError):
    def __init__(self, code: str, message: str, status: int = 422, **detail: Any):
        super().__init__(message)
        self.code, self.status, self.detail = code, status, detail


def _now() -> str:
    return datetime.now(UTC).isoformat()


def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
    tmp.write_text(json.dumps(value, sort_keys=True, indent=1), encoding="utf-8")
    with tmp.open("rb") as stream:
        os.fsync(stream.fileno())
    os.replace(tmp, path)


def _read_json(path: Path, code: str, message: str) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DraftError(code, message, 404) from exc


def drafts_root(workspace_id: str) -> Path:
    if not re.fullmatch(r"[A-Za-z0-9_.-]{1,128}", workspace_id) or workspace_id in {".", ".."} or (
        get_workspace(workspace_id) is None
    ):
        raise DraftError("workspace_not_found", "Workspace was not found", 404)
    return build_paths().workspaces_dir / workspace_id / "process" / "drafts"


def draft_dir(workspace_id: str, draft_id: str) -> Path:
    if not re.fullmatch(r"[a-f0-9-]{36}", draft_id):
        raise DraftError("draft_not_found", "Process draft was not found", 404)
    path = drafts_root(workspace_id) / draft_id
    if not (path / "head.json").exists():
        raise DraftError("draft_not_found", "Process draft was not found", 404)
    return path


# ---------------------------------------------------------------- quantities


def _si(quantity: DraftQuantity, kind: str, field: str) -> dict[str, Any]:
    si_unit, allowed = QUANTITY_UNITS[kind]
    if quantity.unit not in allowed:
        raise DraftError("unit_unsupported", f"{field}: unit {quantity.unit!r} is not offered; use one of {list(allowed)}",
                         field=field)
    if kind == "percent" or quantity.unit == si_unit:
        value = quantity.value
    else:
        try:
            value = magnitude(Quantity(value=quantity.value, unit=quantity.unit), si_unit)
        except (EvaluationRefusal, ValueError) as exc:
            raise DraftError("quantity_invalid", f"{field}: {quantity.unit} is not a {kind}", field=field) from exc
    if not math.isfinite(value):
        raise DraftError("quantity_invalid", f"{field}: value is not finite", field=field)
    return {"si": value, "value": quantity.value, "unit": quantity.unit}


def convert_si(value_si: float, kind: str, unit: str) -> float:
    """Server-side presentation conversion from SI storage into a display unit."""
    si_unit, _allowed = QUANTITY_UNITS[kind]
    if kind == "percent" or unit == si_unit:
        return value_si
    return magnitude(Quantity(value=value_si, unit=si_unit), unit)


# ---------------------------------------------------------------- document ops


def empty_document(name: str) -> dict[str, Any]:
    return {"schema_version": 1, "name": name, "compounds": [], "property_package": None,
            "objects": {}, "reactions": {}}


def _by_tag(document: dict[str, Any], tag: str) -> dict[str, Any] | None:
    return next((item for item in document["objects"].values() if item["tag"] == tag), None)


def _object(document: dict[str, Any], object_id: str, kind: str | None = None) -> dict[str, Any]:
    item = document["objects"].get(object_id)
    if item is None or (kind and item["kind"] != kind):
        raise DraftError("object_not_found", f"{kind or 'object'} {object_id!r} is not in the draft", field=object_id)
    return item


def _new_id(document: dict[str, Any], prefix: str, requested: str | None) -> str:
    if requested:
        if requested in document["objects"]:
            raise DraftError("id_conflict", f"id {requested!r} already exists")
        return requested
    index = len(document["objects"]) + 1
    while f"{prefix}{index}" in document["objects"]:
        index += 1
    return f"{prefix}{index}"


def _unique_tag(document: dict[str, Any], tag: str, own_id: str | None = None) -> None:
    other = _by_tag(document, tag)
    if other is not None and other["id"] != own_id:
        raise DraftError("tag_conflict", f"tag {tag!r} is already used", field=tag)


def _unit_spec(unit: dict[str, Any]) -> UnitSpec:
    return UNIT_REGISTRY[unit["type"]]


def _occupant(document: dict[str, Any], unit_id: str, end: str, port: int, *, energy: bool = False) -> dict[str, Any] | None:
    return next(
        (item for item in document["objects"].values() if item["kind"] == "stream"
         and (item["type"] == "EnergyStream") is energy
         and (item.get(end) or {}).get("unit") == unit_id and item[end]["port"] == port),
        None,
    )


def _default_param(param: ParamSpec) -> dict[str, Any]:
    assert param.default is not None
    unit = QUANTITY_UNITS[param.kind][1][0]
    return {"si": param.default, "value": convert_si(param.default, param.kind, unit), "unit": unit}


def apply_op(document: dict[str, Any], op: Any) -> None:
    objects = document["objects"]
    if isinstance(op, AddUnit | AddStream) and len(objects) >= MAX_OBJECTS:
        raise DraftError("draft_too_large", f"A draft holds at most {MAX_OBJECTS} objects")
    if isinstance(op, AddUnit):
        if op.type not in UNIT_REGISTRY:
            reason = UNSUPPORTED_TYPES.get(op.type, "This equipment type is not in the supported registry.")
            raise DraftError("unsupported_type", f"{op.type}: {reason}", field="type")
        _unique_tag(document, op.tag)
        spec = UNIT_REGISTRY[op.type]
        object_id = _new_id(document, "u", op.id)
        params = {item.key: _default_param(item) for item in spec.params_for(spec.default_mode)
                  if item.default is not None}
        objects[object_id] = {"id": object_id, "kind": "unit", "type": op.type, "tag": op.tag, "x": op.x, "y": op.y,
                              "mode": spec.default_mode, "params": params, "options": {}, "reactions": []}
    elif isinstance(op, AddStream):
        _unique_tag(document, op.tag)
        object_id = _new_id(document, "s", op.id)
        stream_type = "EnergyStream" if op.stream_type == "energy" else "MaterialStream"
        objects[object_id] = {"id": object_id, "kind": "stream", "type": stream_type, "tag": op.tag,
                              "x": op.x, "y": op.y, "source": None, "target": None, "spec": {}}
    elif isinstance(op, Delete):
        item = _object(document, op.id)
        del objects[op.id]
        if item["kind"] == "unit":
            for stream in objects.values():
                for end in ("source", "target"):
                    if stream["kind"] == "stream" and (stream.get(end) or {}).get("unit") == op.id:
                        stream[end] = None
    elif isinstance(op, Move):
        item = _object(document, op.id)
        item["x"], item["y"] = op.x, op.y
    elif isinstance(op, Rename):
        item = _object(document, op.id)
        _unique_tag(document, op.tag, op.id)
        item["tag"] = op.tag
    elif isinstance(op, Connect):
        stream = _object(document, op.stream, "stream")
        unit = _object(document, op.unit, "unit")
        spec = _unit_spec(unit)
        stream_is_energy = stream["type"] == "EnergyStream"
        ports = ((spec.energy_outlets if op.end == "source" else spec.energy_inlets) if stream_is_energy
                 else (spec.outlets if op.end == "source" else spec.inlets))
        if op.port >= len(ports):
            raise DraftError("port_invalid", f"{spec.label} has no {'energy ' if stream_is_energy else ''}{'outlet' if op.end == 'source' else 'inlet'} "
                             f"port {op.port}", field="port")
        other_end = "target" if op.end == "source" else "source"
        if (stream.get(other_end) or {}).get("unit") == op.unit:
            raise DraftError("port_invalid", "A stream cannot leave and enter the same unit (recycles are unsupported)")
        occupant = _occupant(document, op.unit, op.end, op.port, energy=stream_is_energy)
        if occupant is not None and occupant["id"] != op.stream:
            raise DraftError("port_occupied", f"{unit['tag']} {ports[op.port]} is already connected to "
                             f"{occupant['tag']}", field="port")
        stream[op.end] = {"unit": op.unit, "port": op.port}
        if op.end == "source":
            # A stream with a source is computed by DWSIM; a feed specification would not be materialized.
            stream["spec"] = {}
    elif isinstance(op, Disconnect):
        stream = _object(document, op.stream, "stream")
        stream[op.end] = None
    elif isinstance(op, SetRoute):
        stream = _object(document, op.stream, "stream")
        points = [{"x": point.x, "y": point.y} for point in op.points]
        if any(a == b for a, b in zip(points, points[1:], strict=False)) or any(
            a["x"] != b["x"] and a["y"] != b["y"] for a, b in zip(points, points[1:], strict=False)
        ):
            raise DraftError("route_invalid", "Route points must form nonzero axis-parallel segments", field="points")
        stream["route"] = points
    elif isinstance(op, SetStreamSpec):
        stream = _object(document, op.stream, "stream")
        if stream["type"] == "EnergyStream":
            if any((op.temperature, op.pressure, op.mass_flow, op.composition is not None)):
                raise DraftError("spec_on_energy_stream", "Energy streams accept only duty", field="spec")
            if "duty" in op.clear:
                stream["spec"].pop("duty", None)
            if op.duty is not None:
                stream["spec"]["duty"] = _si(op.duty, "power", "Energy flow")
            return
        if stream.get("source") is not None and (
            op.temperature or op.pressure or op.mass_flow or op.composition is not None
        ):
            raise DraftError("spec_on_product", f"{stream['tag']} is computed by its upstream unit; only feed "
                             "streams (no source) take specifications", field="spec")
        for cleared in op.clear:
            stream["spec"].pop(cleared, None)
        if op.duty is not None:
            raise DraftError("spec_unsupported", "Material streams do not accept a duty", field="duty")
        for spec_key, (kind, _arg, label) in STREAM_SPECS.items():
            value = getattr(op, spec_key)
            if value is not None:
                converted = _si(value, kind, label)
                if converted["si"] <= 0:
                    raise DraftError("quantity_invalid", f"{label} must be positive", field=spec_key)
                stream["spec"][spec_key] = converted
        if op.composition is not None:
            unknown = sorted(set(op.composition) - set(document["compounds"]))
            if unknown:
                raise DraftError("compound_undeclared", f"compounds {unknown} are not declared in the draft thermo",
                                 field="composition")
            stream["spec"]["composition"] = {name: float(value) for name, value in sorted(op.composition.items())
                                             if value > 0}
    elif isinstance(op, SetUnitParams):
        unit = _object(document, op.unit, "unit")
        spec = _unit_spec(unit)
        if op.mode is not None:
            if op.mode not in spec.modes:
                raise DraftError("mode_unsupported", f"{spec.label} mode {op.mode!r} is not supported; use one of "
                                 f"{list(spec.modes)}", field="mode")
            unit["mode"] = op.mode
            active = {param_spec.key for param_spec in spec.params_for(op.mode)}
            unit["params"] = {name: value for name, value in unit["params"].items() if name in active}
            for param_spec in spec.params_for(op.mode):
                if param_spec.key not in unit["params"] and param_spec.default is not None:
                    unit["params"][param_spec.key] = _default_param(param_spec)
        for key, quantity in op.values.items():
            param = next((item for item in spec.params if item.key == key), None)
            if param is None:
                raise DraftError("param_unsupported", f"{spec.label} has no supported parameter {key!r}", field=key)
            if unit["mode"] not in param.modes:
                raise DraftError("param_inactive", f"{param.label} is not used in {spec.label} mode "
                                 f"{unit['mode']!r}", field=key)
            converted = _si(quantity, param.kind, param.label)
            if (param.minimum_si is not None and converted["si"] < param.minimum_si) or (
                param.maximum_si is not None and converted["si"] > param.maximum_si
            ):
                raise DraftError("quantity_out_of_range", f"{param.label} is outside its supported range", field=key)
            unit["params"][key] = converted
        if op.options:
            raise DraftError("option_unsupported", f"{spec.label} does not expose verified enum/boolean inputs", field="options")
        if op.reactions is not None:
            missing = sorted(set(op.reactions) - set(document.get("reactions", {})))
            if missing:
                raise DraftError("reaction_not_found", f"Reaction ids {missing} are not defined", field="reactions")
            unit["reactions"] = list(dict.fromkeys(op.reactions))
    elif isinstance(op, SetReactions):
        reactions = {}
        for reaction_id, reaction in op.reactions.items():
            if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]{0,31}", reaction_id):
                raise DraftError("reaction_id_invalid", f"Reaction id {reaction_id!r} is invalid", field="reactions")
            item = reaction.model_dump(mode="json")
            compounds = set(item["stoichiometry"]) | set(item["orders"])
            unknown = sorted(compounds - set(document["compounds"]))
            if unknown:
                raise DraftError("compound_undeclared", f"Reaction compounds {unknown} are not declared in Thermo",
                                 field="reactions")
            base = item["base_reactant"]
            if base not in item["stoichiometry"] or item["stoichiometry"][base] >= 0:
                raise DraftError("reaction_base_invalid", "Base reactant must have a negative stoichiometric coefficient",
                                 field="base_reactant")
            if item["A_forward"]["unit"] != "kmol/[m3.h]" or item["E_forward"]["unit"] not in {"J/mol", "kJ/mol"}:
                raise DraftError("reaction_unit_unsupported", "Use A in kmol/[m3.h] and activation energy in J/mol or kJ/mol",
                                 field="A_forward")
            reactions[reaction_id] = item
        document["reactions"] = reactions
    elif isinstance(op, SetThermo):
        if op.compounds is not None:
            unknown = [name for name in op.compounds if name not in COMPOUNDS]
            if unknown or len(set(op.compounds)) != len(op.compounds):
                raise DraftError("compound_unsupported", f"compounds {unknown or 'duplicated'} are not in the supported "
                                 "list", field="compounds")
            document["compounds"] = list(op.compounds)
            for stream in objects.values():
                composition = stream.get("spec", {}).get("composition")
                if composition and set(composition) - set(op.compounds):
                    stream["spec"].pop("composition")
        if op.property_package is not None:
            if op.property_package not in PROPERTY_PACKAGES:
                raise DraftError("package_unsupported", f"{op.property_package!r} is not a supported property package",
                                 field="property_package")
            document["property_package"] = op.property_package
    else:  # pragma: no cover - the discriminated union is closed
        raise DraftError("op_unsupported", "Unsupported draft operation")


def apply_ops(document: dict[str, Any], ops: list[Any]) -> dict[str, Any]:
    result = copy.deepcopy(document)
    for index, op in enumerate(ops):
        try:
            apply_op(result, op)
        except DraftError as exc:
            exc.detail.setdefault("op_index", index)
            raise
    return result


# ---------------------------------------------------------------- validation


def validate_document(document: dict[str, Any]) -> list[dict[str, Any]]:
    """Instant Jarvis-side pre-run findings; DWSIM's own check runs only on Validate."""
    findings: list[dict[str, Any]] = []

    def add(severity: str, code: str, message: str, tag: str = "", field: str = "") -> None:
        findings.append({"severity": severity, "code": code, "object": tag, "field": field, "message": message,
                         "source": "jarvis"})

    objects = document["objects"]
    if not objects:
        add("blocker", "DRAFT_EMPTY", "Add streams and equipment to build the flowsheet.")
    if not document["compounds"]:
        add("blocker", "NO_COMPOUNDS", "Declare the compounds in Thermo.", field="compounds")
    if not document["property_package"]:
        add("blocker", "NO_PROPERTY_PACKAGE", "Choose a property package in Thermo.", field="property_package")
    for unit in sorted((item for item in objects.values() if item["kind"] == "unit"), key=lambda item: item["tag"]):
        spec = _unit_spec(unit)
        inlets = [port for port in range(len(spec.inlets)) if _occupant(document, unit["id"], "target", port)]
        if len(inlets) < spec.required_inlets:
            add("blocker", "UNIT_INLET_MISSING",
                f"{spec.label} needs {spec.required_inlets} connected inlet(s); {len(inlets)} connected.", unit["tag"],
                "inlets")
        for param in spec.params_for(unit["mode"]):
            if param.key not in unit["params"]:
                add("blocker", "UNIT_PARAM_MISSING", f"Set {param.label}.", unit["tag"], param.key)
        if unit["type"] == "PFR" and not unit.get("reactions"):
            add("blocker", "REACTION_SET_MISSING", "Assign at least one kinetic reaction to the PFR.", unit["tag"],
                "reactions")
        needs_energy = (unit["type"] == "DistillationColumn" or
                        unit["type"] == "PFR" and unit["mode"] == "heat_exchange" or
                        unit["type"] in {"Heater", "Cooler"} and unit["mode"] == "energy_stream")
        if needs_energy and not any(_occupant(document, unit["id"], "target", port, energy=True)
                                    for port in range(len(spec.energy_inlets))):
            add("blocker", "UNIT_ENERGY_INLET_MISSING", f"Connect an energy stream to {spec.label}.", unit["tag"],
                "energy_inlets")
        if unit["type"] == "DistillationColumn" and not any(
            _occupant(document, unit["id"], "source", port, energy=True) for port in range(len(spec.energy_outlets))
        ):
            add("blocker", "UNIT_ENERGY_OUTLET_MISSING", "Connect the condenser duty energy stream.", unit["tag"],
                "energy_outlets")
        outlet_count = sum(bool(_occupant(document, unit["id"], "source", port))
                           for port in range(len(spec.outlets)))
        for port, name in enumerate(spec.outlets):
            if unit["type"] == "Splitter" and port == 2:
                continue
            if not _occupant(document, unit["id"], "source", port):
                add("blocker", "UNIT_OUTLET_MISSING", f"Connect a stream to the {name} outlet.", unit["tag"], name)
        if unit["type"] == "Splitter" and unit["mode"] == "split_ratios":
            ratio1 = unit["params"].get("split_ratio_1", {}).get("si")
            ratio2 = unit["params"].get("split_ratio_2", {}).get("si")
            if ratio1 is not None and ratio2 is not None:
                total = float(ratio1) + float(ratio2)
                invalid = total > 1.0 + _COMPOSITION_TOL or outlet_count == 2 and abs(total - 1.0) > _COMPOSITION_TOL
                if invalid:
                    add("blocker", "SPLIT_RATIOS_INVALID", "Split ratios must sum to 1 for two outlets and at most 1 for three.",
                        unit["tag"], "split_ratios")
    for stream in sorted((item for item in objects.values() if item["kind"] == "stream"), key=lambda item: item["tag"]):
        if stream["source"] is None and stream["target"] is None:
            add("blocker", "STREAM_DANGLING", "This stream is connected to nothing.", stream["tag"])
            continue
        if stream["type"] == "EnergyStream":
            if "duty" in stream["spec"]:
                consumer = objects.get(stream["target"]["unit"]) if stream.get("target") else None
                if consumer is None or consumer["mode"] != "energy_stream":
                    add("blocker", "ENERGY_DUTY_MODE_MISMATCH", "A specified energy duty requires a connected unit in EnergyStream mode.", stream["tag"], "duty")
            continue
        if stream["source"] is None:
            for key, (_kind, _arg, label) in STREAM_SPECS.items():
                if key not in stream["spec"]:
                    add("blocker", "FEED_SPEC_MISSING", f"Feed needs {label.lower()}.", stream["tag"], key)
            composition = stream["spec"].get("composition")
            if not composition:
                add("blocker", "FEED_COMPOSITION_MISSING", "Feed needs a composition.", stream["tag"], "composition")
            else:
                total = sum(composition.values())
                if abs(total - 1.0) > _COMPOSITION_TOL:
                    add("blocker", "COMPOSITION_SUM", f"Mass fractions sum to {total:.6g}, not 1.", stream["tag"],
                        "composition")
                undeclared = sorted(set(composition) - set(document["compounds"]))
                if undeclared:
                    add("blocker", "COMPOUND_UNDECLARED", f"{undeclared} are not declared in Thermo.", stream["tag"],
                        "composition")
    graph: dict[str, list[str]] = {}
    for stream in objects.values():
        if stream["kind"] == "stream" and stream.get("source") and stream.get("target"):
            graph.setdefault(stream["source"]["unit"], []).append(stream["target"]["unit"])
    visiting: list[str] = []
    visited: set[str] = set()
    reported_cycles: set[frozenset[str]] = set()

    def visit(unit_id: str) -> None:
        if unit_id in visiting:
            cycle = visiting[visiting.index(unit_id):]
            if not any(objects.get(item, {}).get("type") == "Recycle" for item in cycle):
                cycle_key = frozenset(cycle)
                if cycle_key not in reported_cycles:
                    reported_cycles.add(cycle_key)
                    tags = [objects[item]["tag"] for item in cycle]
                    add("blocker", "RECYCLE_REQUIRED", f"Process loop {tags} requires a Recycle block.", tags[0],
                        "connections")
            return
        if unit_id in visited:
            return
        visiting.append(unit_id)
        for next_id in graph.get(unit_id, []):
            visit(next_id)
        visiting.pop()
        visited.add(unit_id)

    for unit_id in graph:
        visit(unit_id)
    return findings


# ---------------------------------------------------------------- revisions


def _digest(document: dict[str, Any]) -> str:
    return hashlib.sha256(canonical(document).encode()).hexdigest()


def _write_revision(directory: Path, document: dict[str, Any], *, parent: str | None, actor: str,
                    ops: list[dict[str, Any]]) -> dict[str, Any]:
    head = _read_json(directory / "head.json", "draft_not_found", "missing") if (directory / "head.json").exists() \
        else None
    seq = head["seq"] + 1 if head else 1
    digest = _digest(document)
    record = {"seq": seq, "revision": f"{seq}:{digest[:16]}", "document_sha256": digest, "parent_revision": parent,
              "actor": actor, "ops": ops, "created_at": _now(), "document": document}
    _write_json(directory / "revisions" / f"{seq}.json", record)
    _write_json(directory / "head.json", {key: value for key, value in record.items() if key != "document"}
                | {"name": document["name"]})
    return record


def _head(directory: Path) -> dict[str, Any]:
    return _read_json(directory / "head.json", "draft_not_found", "Process draft was not found")


def load_revision(directory: Path, revision: str) -> dict[str, Any]:
    match = re.fullmatch(r"(\d+):([0-9a-f]{16})", revision)
    if not match:
        raise DraftError("revision_not_found", "Draft revision was not found", 404)
    record = _read_json(directory / "revisions" / f"{int(match.group(1))}.json", "revision_not_found",
                        "Draft revision was not found")
    if record["revision"] != revision or _digest(record["document"]) != record["document_sha256"]:
        raise DraftError("revision_integrity_error", "Draft revision failed its content check", 409)
    return record


def create_draft(workspace_id: str, name: str) -> dict[str, Any]:
    draft_id = str(uuid4())
    directory = drafts_root(workspace_id) / draft_id
    with _lock(directory):
        _write_revision(directory, empty_document(name), parent=None, actor="operator", ops=[])
    return projection(workspace_id, draft_id)


def list_drafts(workspace_id: str) -> list[dict[str, Any]]:
    root = drafts_root(workspace_id)
    rows = []
    for directory in sorted(root.iterdir() if root.exists() else []):
        if (directory / "head.json").exists():
            head = _head(directory)
            rows.append({"draft_id": directory.name, "name": head.get("name"), "revision": head["revision"],
                         "updated_at": head["created_at"]})
    return sorted(rows, key=lambda row: row["updated_at"], reverse=True)


def patch(workspace_id: str, draft_id: str, expected_revision: str, ops: list[Any], *,
          actor: str = "operator") -> dict[str, Any]:
    directory = draft_dir(workspace_id, draft_id)
    with _lock(directory):
        head = _head(directory)
        if expected_revision != head["revision"]:
            raise DraftError("revision_conflict", "Expected revision is stale", 409, current_revision=head["revision"])
        current = load_revision(directory, head["revision"])
        document = apply_ops(current["document"], ops)
        _write_revision(directory, document, parent=head["revision"], actor=actor,
                        ops=[op.model_dump(mode="json") if isinstance(op, BaseModel) else op for op in ops])
    return projection(workspace_id, draft_id)


def restore(workspace_id: str, draft_id: str, expected_revision: str, source_revision: str) -> dict[str, Any]:
    directory = draft_dir(workspace_id, draft_id)
    with _lock(directory):
        head = _head(directory)
        if expected_revision != head["revision"]:
            raise DraftError("revision_conflict", "Expected revision is stale", 409, current_revision=head["revision"])
        source = load_revision(directory, source_revision)
        _write_revision(directory, source["document"], parent=head["revision"], actor="operator",
                        ops=[{"op": "restore", "source_revision": source_revision}])
    return projection(workspace_id, draft_id)


def list_revisions(workspace_id: str, draft_id: str) -> list[dict[str, Any]]:
    directory = draft_dir(workspace_id, draft_id)
    rows = []
    for seq in range(_head(directory)["seq"], 0, -1):
        path = directory / "revisions" / f"{seq}.json"
        if path.exists():
            record = json.loads(path.read_text(encoding="utf-8"))
            rows.append({key: record[key] for key in ("seq", "revision", "parent_revision", "actor", "created_at")}
                        | {"ops": [op.get("op") for op in record["ops"]]})
    return rows


# ---------------------------------------------------------------- runs


def runs_dir(directory: Path) -> Path:
    return directory / "runs"


def list_runs(directory: Path) -> list[dict[str, Any]]:
    root = runs_dir(directory)
    rows = []
    for path in root.glob("*/run.json") if root.exists() else []:
        try:
            rows.append(json.loads(path.read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError):
            continue
    return sorted(rows, key=lambda row: row["started_at"], reverse=True)


def record_run(directory: Path, run: dict[str, Any]) -> None:
    _write_json(runs_dir(directory) / run["run_id"] / "run.json", run)


def results_state(head: dict[str, Any], runs: list[dict[str, Any]], document: dict[str, Any] | None = None,
                  edits_since: int | None = None) -> dict[str, Any]:
    solved = next((run for run in runs if run["action"] == "run" and run["status"] == "completed"), None)
    last = runs[0] if runs else None
    if solved is None:
        return {"state": "none", "last_attempt": _attempt(last)}
    seq = int(solved["draft_revision"].split(":", 1)[0])
    current = solved["draft_revision"] == head["revision"]
    if not current and document is not None:
        from app.modules.process_stack.draft_compiler import expected, fingerprint
        current = fingerprint(expected(document), dwsim_version=solved["dwsim_version"],
                             mcp_sha256=solved["mcp_sha256"]) == solved["materialization_fingerprint"]
    return {"state": "current" if current else "stale", "run_id": solved["run_id"],
            "draft_revision": solved["draft_revision"],
            "edits_since": 0 if current else edits_since if edits_since is not None else head["seq"] - seq,
            "materialization_fingerprint": solved["materialization_fingerprint"], "last_attempt": _attempt(last)}


def _attempt(run: dict[str, Any] | None) -> dict[str, Any] | None:
    if run is None:
        return None
    return {key: run.get(key) for key in ("run_id", "action", "status", "draft_revision", "started_at")}


# ---------------------------------------------------------------- projection


def registry_projection() -> dict[str, Any]:
    capabilities = _capability_manifest()
    return {
        "compiler_version": COMPILER_VERSION,
        "compounds": list(COMPOUNDS),
        "property_packages": list(PROPERTY_PACKAGES),
        "quantity_units": {kind: {"si": si, "display": list(display)} for kind, (si, display) in QUANTITY_UNITS.items()},
        "stream_specs": [{"key": key, "label": label, "kind": kind} for key, (kind, _arg, label) in STREAM_SPECS.items()],
        "units": [
            {"type": spec.type, "label": spec.label, "inlets": list(spec.inlets), "outlets": list(spec.outlets),
             "energy_inlets": list(spec.energy_inlets), "energy_outlets": list(spec.energy_outlets),
             "energy_spec_modes": [], "required_inlets": spec.required_inlets, "modes": list(spec.modes),
             "params": [{"key": item.key, "label": item.label, "kind": item.kind, "modes": list(item.modes),
                         "default": item.default, "classification": "input", "minimum": item.minimum_si,
                         "maximum": item.maximum_si} for item in spec.params],
             "reactions": spec.type == "PFR",
             "result_properties": capabilities["objects"].get(spec.dwsim_type, {}).get("result_properties", [])}
            for spec in UNIT_REGISTRY.values()
        ],
        "dwsim_capabilities": capabilities,
        "unsupported": UNSUPPORTED_TYPES,
    }


def _display(document: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for item in sorted(document["objects"].values(), key=lambda value: (value["kind"], value["tag"])):
        rows.append(copy.deepcopy(item))
    return rows


def projection(workspace_id: str, draft_id: str) -> dict[str, Any]:
    directory = draft_dir(workspace_id, draft_id)
    head = _head(directory)
    record = load_revision(directory, head["revision"])
    document = record["document"]
    runs = list_runs(directory)
    solved = next((run for run in runs if run["action"] == "run" and run["status"] == "completed"), None)
    edits_since = None
    if solved is not None:
        solved_seq = int(solved["draft_revision"].split(":", 1)[0])
        edits_since = 0
        for seq in range(solved_seq + 1, head["seq"] + 1):
            revision = _read_json(directory / "revisions" / f"{seq}.json", "revision_not_found", "Draft revision was not found")
            edits_since += sum(1 for op in revision.get("ops", []) if op.get("op") != "set_route")
    return {
        "workspace_id": workspace_id,
        "draft_id": draft_id,
        "name": document["name"],
        "revision": head["revision"],
        "seq": head["seq"],
        "compounds": document["compounds"],
        "property_package": document["property_package"],
        "objects": _display(document),
        "reactions": copy.deepcopy(document.get("reactions", {})),
        "findings": validate_document(document),
        "results": results_state(head, runs, document, edits_since),
        "proposals": [proposal for proposal in list_proposals(workspace_id, draft_id) if proposal["state"] == "pending"
                      or proposal["state"] == "stale"],
    }


# ---------------------------------------------------------------- proposals


def _current_value(item: dict[str, Any], prop: str, unit: str | None) -> Any:
    if item["kind"] == "stream":
        if prop == "composition":
            return item["spec"].get("composition")
        stored = item["spec"].get(prop)
        kind = STREAM_SPECS[prop][0]
    else:
        if prop == "mode":
            return item["mode"]
        stored = item["params"].get(prop)
        spec = _unit_spec(item)
        kind = next(param.kind for param in spec.params if param.key == prop)
    if stored is None:
        return None
    if unit is None:
        return {"value": stored["value"], "unit": stored["unit"]}
    return {"value": float(f"{convert_si(stored['si'], kind, unit):.12g}"), "unit": unit}


def _change_ops(document: dict[str, Any], changes: list[dict[str, Any]]) -> list[Any]:
    ops: list[Any] = []
    unit_ops: dict[str, SetUnitParams] = {}
    for change in changes:
        item = document["objects"][change["target_id"]]
        prop, proposed = change["property"], change["proposed"]
        if item["kind"] == "stream":
            if prop == "composition":
                ops.append(SetStreamSpec(op="set_stream_spec", stream=item["id"], composition=proposed))
            else:
                ops.append(SetStreamSpec.model_validate({"op": "set_stream_spec", "stream": item["id"], prop: proposed}))
        else:
            op = unit_ops.setdefault(item["id"], SetUnitParams(op="set_unit_params", unit=item["id"]))
            if prop == "mode":
                op.mode = proposed
            else:
                op.values[prop] = DraftQuantity.model_validate(proposed)
    # A mode change must precede its parameters, so unit ops carry both in one operation.
    return ops + list(unit_ops.values())


def _resolve_change(document: dict[str, Any], change: Any) -> dict[str, Any]:
    item = _by_tag(document, change.target)
    if item is None:
        raise DraftError("proposal_target_unknown", f"No object is tagged {change.target!r}", field=change.target)
    prop = change.property
    proposed = change.proposed
    if item["kind"] == "stream":
        if prop == "composition":
            if not isinstance(proposed, dict):
                raise DraftError("proposal_value_invalid", "composition takes {compound: mass fraction}", field=prop)
            unit = None
        elif prop in STREAM_SPECS:
            if not isinstance(proposed, DraftQuantity):
                raise DraftError("proposal_value_invalid", f"{prop} takes a value and unit", field=prop)
            unit = proposed.unit
        else:
            raise DraftError("proposal_property_unsupported", f"streams accept {[*STREAM_SPECS, 'composition']}",
                             field=prop)
    else:
        spec = _unit_spec(item)
        if prop == "mode":
            if not isinstance(proposed, str):
                raise DraftError("proposal_value_invalid", "mode takes a mode name", field=prop)
            unit = None
        elif any(param.key == prop for param in spec.params):
            if not isinstance(proposed, DraftQuantity):
                raise DraftError("proposal_value_invalid", f"{prop} takes a value and unit", field=prop)
            unit = proposed.unit
        else:
            raise DraftError("proposal_property_unsupported",
                             f"{spec.label} accepts {['mode', *[param.key for param in spec.params]]}", field=prop)
    try:
        current = _current_value(item, prop, unit)
    except (EvaluationRefusal, ValueError) as exc:
        raise DraftError("proposal_value_invalid", f"{prop}: unit {unit!r} does not fit", field=prop) from exc
    return {"target": item["tag"], "target_id": item["id"], "kind": item["kind"], "property": prop,
            "current": current,
            "proposed": proposed.model_dump() if isinstance(proposed, DraftQuantity) else proposed}


def _proposal_path(directory: Path, proposal_id: str) -> Path:
    if not re.fullmatch(r"[a-f0-9]{32}", proposal_id):
        raise DraftError("proposal_not_found", "Proposal was not found", 404)
    return directory / "proposals" / f"{proposal_id}.json"


def create_proposal(workspace_id: str, draft_id: str, request: ProposalRequest) -> dict[str, Any]:
    """Validate and store a pending change set; the draft itself never changes here."""
    directory = draft_dir(workspace_id, draft_id)
    with _lock(directory):
        head = _head(directory)
        if request.base_revision != head["revision"]:
            raise DraftError("revision_conflict", "Proposal base revision is not the current draft revision", 409,
                             current_revision=head["revision"])
        document = load_revision(directory, head["revision"])["document"]
        changes = [_resolve_change(document, change) for change in request.changes]
        apply_ops(document, _change_ops(document, changes))  # dry run: refuse anything the owner would refuse
        proposal = {"proposal_id": uuid4().hex, "draft_id": draft_id, "base_revision": head["revision"],
                    "status": "pending", "changes": changes, "rationale": request.rationale,
                    "source": request.source, "created_at": _now(), "applied_revision": None}
        _write_json(_proposal_path(directory, proposal["proposal_id"]), proposal)
    return _proposal_view(proposal, head)


def _proposal_view(proposal: dict[str, Any], head: dict[str, Any]) -> dict[str, Any]:
    state = proposal["status"]
    if state == "pending" and proposal["base_revision"] != head["revision"]:
        state = "stale"
    return {**proposal, "state": state}


def list_proposals(workspace_id: str, draft_id: str) -> list[dict[str, Any]]:
    directory = draft_dir(workspace_id, draft_id)
    head = _head(directory)
    rows = []
    for path in (directory / "proposals").glob("*.json") if (directory / "proposals").exists() else []:
        rows.append(_proposal_view(json.loads(path.read_text(encoding="utf-8")), head))
    return sorted(rows, key=lambda row: row["created_at"], reverse=True)


def decide_proposal(workspace_id: str, draft_id: str, proposal_id: str, *, approve: bool,
                    accepted_changes: list[int] | None = None) -> dict[str, Any]:
    directory = draft_dir(workspace_id, draft_id)
    path = _proposal_path(directory, proposal_id)
    with _lock(directory):
        proposal = _read_json(path, "proposal_not_found", "Proposal was not found")
        if proposal["status"] != "pending":
            raise DraftError("proposal_decided", f"Proposal is already {proposal['status']}", 409)
        head = _head(directory)
        if not approve:
            proposal.update(status="rejected", decided_at=_now())
            _write_json(path, proposal)
            return {"proposal": _proposal_view(proposal, head), "draft": None}
        if proposal["base_revision"] != head["revision"]:
            raise DraftError("proposal_stale", "The draft changed after this proposal; it cannot be applied", 409,
                             current_revision=head["revision"])
        indices = list(range(len(proposal["changes"]))) if accepted_changes is None else sorted(set(accepted_changes))
        if not indices or any(index < 0 or index >= len(proposal["changes"]) for index in indices):
            raise DraftError("proposal_selection_invalid", "Select at least one listed change")
        selected = [proposal["changes"][index] for index in indices]
        document = load_revision(directory, head["revision"])["document"]
        ops = _change_ops(document, selected)
        updated = apply_ops(document, ops)
        record = _write_revision(directory, updated, parent=head["revision"],
                                 actor=f"hermes_proposal:{proposal_id}" if proposal["source"].startswith("hermes")
                                 else f"proposal:{proposal_id}",
                                 ops=[op.model_dump(mode="json") for op in ops])
        proposal.update(status="approved", decided_at=_now(), applied_revision=record["revision"],
                        accepted_changes=indices)
        _write_json(path, proposal)
        head = _head(directory)
    return {"proposal": _proposal_view(proposal, head), "draft": projection(workspace_id, draft_id)}


def latest_draft_id(workspace_id: str) -> str | None:
    if not re.fullmatch(r"[A-Za-z0-9_.-]{1,128}", workspace_id) or not (
        build_paths().workspaces_dir / workspace_id / "process" / "drafts"
    ).is_dir():
        return None
    rows = list_drafts(workspace_id)
    return rows[0]["draft_id"] if rows else None


def agent_view(workspace_id: str, draft_id: str | None) -> dict[str, Any]:
    """Compact read projection for Hermes: tags, typed parameters in their entered units, results state."""
    draft_id = draft_id or latest_draft_id(workspace_id)
    if draft_id is None:
        raise DraftError("draft_not_found", "This workspace has no process draft", 404)
    view = projection(workspace_id, draft_id)
    objects = []
    for item in view["objects"]:
        row: dict[str, Any] = {"tag": item["tag"], "type": item["type"]}
        if item["kind"] == "stream":
            row["from"] = _endpoint_tag(view, item["source"])
            row["to"] = _endpoint_tag(view, item["target"])
            row["spec"] = {key: ({"value": value["value"], "unit": value["unit"]} if key != "composition" else value)
                           for key, value in item["spec"].items()}
        else:
            row["mode"] = item["mode"]
            row["params"] = {key: {"value": value["value"], "unit": value["unit"]}
                             for key, value in item["params"].items()}
        objects.append(row)
    return {"draft_id": view["draft_id"], "revision": view["revision"], "compounds": view["compounds"],
            "property_package": view["property_package"], "objects": objects,
            "findings": [f"{item['object']}: {item['message']}" for item in view["findings"]][:12],
            "results": view["results"],
            "to_change_values": (f"call jarvis_process_propose with base_revision '{view['revision']}' and changes "
                                 "[{target: <tag>, property: <name from proposable>, proposed: {value, unit}}]; "
                                 "the operator approves before anything changes"),
            "proposable": {"stream": [*STREAM_SPECS, "composition"],
                           **{spec.type: ["mode", *[param.key for param in spec.params]]
                              for spec in UNIT_REGISTRY.values() if spec.params}}}


def _endpoint_tag(view: dict[str, Any], endpoint: dict[str, Any] | None) -> str | None:
    if endpoint is None:
        return None
    unit = next((item for item in view["objects"] if item["id"] == endpoint["unit"]), None)
    return f"{unit['tag']}:{endpoint['port']}" if unit else None


# ---------------------------------------------------------------- validate / run (the only DWSIM contact)


def execute(workspace_id: str, draft_id: str, revision: str, action: str) -> dict[str, Any]:
    """Compile the exact revision into DWSIM; validate, or solve only after a verified materialization."""
    from app.modules.process_stack import draft_compiler, editor

    if action not in {"validate", "run"}:
        raise DraftError("action_invalid", "action must be validate or run")
    directory = draft_dir(workspace_id, draft_id)
    record = load_revision(directory, revision)
    blockers = [item for item in validate_document(record["document"]) if item["severity"] == "blocker"]
    if blockers:
        raise DraftError("draft_invalid", "Resolve the draft findings before DWSIM can materialize it", 422,
                         findings=blockers)
    try:
        client, mcp_sha256, dwsim_version = editor._client()
    except editor.EditorError as exc:
        raise DraftError(exc.code, "DWSIM runtime is unavailable", 503) from exc
    run_id = draft_compiler.new_run_id()
    started = _now()
    run: dict[str, Any] = {"run_id": run_id, "action": action, "draft_id": draft_id, "draft_revision": revision,
                           "draft_document_sha256": record["document_sha256"],
                           "compiler_version": COMPILER_VERSION, "dwsim_version": dwsim_version,
                           "mcp_sha256": mcp_sha256, "started_at": started}
    try:
        with client:
            outcome = draft_compiler.materialize(
                record["document"], action=action, client=client, dwsim_version=dwsim_version,
                mcp_sha256=mcp_sha256, label=f"jarvis-draft-{draft_id[:8]}-{revision}",
                keep_case=runs_dir(directory) / run_id / "solved.dwxmz" if action == "run" else None)
        run.update(outcome)
    except draft_compiler.MaterializationError as exc:
        run.update(status=exc.code, error=str(exc), error_detail=exc.detail)
    except Exception as exc:  # noqa: BLE001 - DWSIM process failures become a recorded, truthful attempt
        run.update(status="runtime_failed", error=type(exc).__name__)
    run["finished_at"] = _now()
    for result in (run.get("streams") or {}).values():
        result["display"] = _stream_display(result)
    with _lock(directory):
        record_run(directory, run)
    return {"run": run, "draft": projection(workspace_id, draft_id)}


def _stream_display(result: dict[str, Any]) -> dict[str, Any]:
    """Operator-unit presentation of DWSIM SI results, converted server-side (no frontend math)."""
    display: dict[str, Any] = {}
    for key, si_key, kind, unit in (("temperature", "temperature_K", "temperature", "degC"),
                                    ("pressure", "pressure_Pa", "pressure", "bar"),
                                    ("mass_flow", "mass_flow_kg_s", "mass_flow", "kg/h")):
        value = result.get(si_key)
        if isinstance(value, (int, float)) and math.isfinite(value):
            display[key] = {"value": float(f"{convert_si(float(value), kind, unit):.6g}"), "unit": unit}
    return display


def get_run(workspace_id: str, draft_id: str, run_id: str) -> dict[str, Any]:
    directory = draft_dir(workspace_id, draft_id)
    if not re.fullmatch(r"[a-f0-9]{32}", run_id):
        raise DraftError("run_not_found", "Run was not found", 404)
    return _read_json(runs_dir(directory) / run_id / "run.json", "run_not_found", "Run was not found")


def run_summaries(workspace_id: str, draft_id: str) -> list[dict[str, Any]]:
    directory = draft_dir(workspace_id, draft_id)
    return [{key: run.get(key) for key in ("run_id", "action", "status", "draft_revision", "started_at",
                                           "materialization_fingerprint", "compile_seconds")}
            for run in list_runs(directory)]
