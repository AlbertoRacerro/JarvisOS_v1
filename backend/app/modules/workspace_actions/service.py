"""Governed Process and BLUECAD actions with durable outcomes."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import UTC, datetime
from typing import Literal
from uuid import uuid4

from app.core.database import open_sqlite_connection
from app.modules.bluecad.ledger import get_candidate
from app.modules.bluecad.spec import SUPPORTED_PART_KINDS, canonicalize_geometry_spec
from app.modules.process_stack import draft
from app.modules.process_stack.draft_models import (
    QUANTITY_UNITS,
    STREAM_SPECS,
    UNIT_REGISTRY,
    AddStream,
    AddUnit,
    Delete,
    Disconnect,
    DraftOp,
    DraftQuantity,
    Move,
    Rename,
    SetOrientation,
    SetStreamSpec,
    SetUnitParams,
)
from app.modules.process_stack.draft_models import Connect as DraftConnect
from app.modules.workspace_actions.models import (
    ActionOrigin,
    ActionOutcome,
    ActionRequest,
    BluecadAction,
    ChangeLine,
    ProcessAction,
    Quantity,
    SurfaceBrief,
    SurfaceRef,
)


class ActionError(RuntimeError):
    def __init__(self, code: str, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.code = code
        self.status_code = status_code


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def _digest(value: object) -> str:
    return "sha256:" + hashlib.sha256(_canonical(value).encode()).hexdigest()


def _find_draft(workspace_id: str, revision: str | None = None, draft_id: str | None = None) -> tuple[str, dict] | None:
    matches = []
    for item in draft.list_drafts(workspace_id):
        if draft_id and item["draft_id"] != draft_id:
            continue
        if revision is None or item["revision"] == revision:
            record = draft.load_revision(draft.draft_dir(workspace_id, item["draft_id"]), item["revision"])
            matches.append((item["draft_id"], record))
    return matches[0] if len(matches) == 1 else None


def _brief_none(workspace_id: str, ref: SurfaceRef | None, summary: str) -> SurfaceBrief:
    route = ref.route_id if ref else "unknown"
    payload: dict[str, object] = {
        "surface": "none", "route_id": route, "workspace_id": workspace_id,
        "base_revision": None, "draft_id": None, "candidate_id": None, "selected": [],
        "summary": summary, "text": summary, "actions": [], "limits": [],
    }
    return SurfaceBrief(
        surface="none",
        route_id=route,
        workspace_id=workspace_id,
        summary=summary,
        text=summary,
        digest=_digest(payload),
    )


def surface_brief(workspace_id: str, ref: SurfaceRef | None) -> SurfaceBrief:
    if ref is None or ref.route_id not in {"design-process", "design-bluecad"}:
        return _brief_none(workspace_id, ref, "No Process or BLUECAD surface is active.")
    if ref.route_id == "design-process":
        found = _find_draft(workspace_id, draft_id=ref.draft_id) if ref.draft_id else None
        if ref.draft_id and not found:
            return _brief_none(
                workspace_id,
                ref,
                "The referenced Process draft is unknown or belongs to another workspace; no surface object was selected.",
            )
        if not ref.draft_id:
            latest = draft.list_drafts(workspace_id)
            found = _find_draft(workspace_id, draft_id=latest[0]["draft_id"]) if latest else None
        if not found:
            return _brief_none(workspace_id, ref, "No Process draft is available in this workspace.")
        draft_id, record = found
        document = record["document"]
        objects = list(document["objects"].values())
        by_tag = {item["tag"]: item for item in objects}
        selected = []
        ignored = False
        for selection in ref.process_selection:
            item = document["objects"].get(selection.id or "") if selection.id else None
            item = item or by_tag.get(selection.tag or "")
            if item is None or item["kind"] != selection.kind:
                ignored = True
                continue
            selected.append(_process_object_brief(item))
        projection = draft.projection(workspace_id, draft_id)
        summary = f"Process: {_safe_surface_label(document.get('name'), 'Process draft')} · revision {record['revision']}"
        if selected:
            selected_object = selected[0]
            summary += f" · selected: {selected_object['kind'].capitalize()} {selected_object['tag']}"
        if ignored:
            summary += "; unknown or foreign selection ignored"
        selected_names = ", ".join(f"{item['type']} `{item['tag']}`" for item in selected)
        selected_stream = next((item for item in selected if item["kind"] == "stream"), None)
        selected_unit = next((item for item in selected if item["kind"] == "unit"), None)
        first_stream = next((item for item in objects if item["kind"] == "stream"), None)
        first_unit = next((item for item in objects if item["kind"] == "unit"), None)
        stream_tag = (selected_stream or first_stream or {"tag": "<stream tag from read>"})["tag"]
        unit_tag = (selected_unit or first_unit or {"tag": "<unit tag from read>"})["tag"]
        unit_tags = [item["tag"] for item in objects if item["kind"] == "unit"]
        next_unit_tag = next((f"P{index}" for index in range(1, len(unit_tags) + 2)
                              if f"P{index}" not in unit_tags), "<new tag>")
        text = (
            f"Process workspace {workspace_id}; draft {draft_id}; head revision {record['revision']}\n"
            f"Results: {projection['results']['state']}\nObjects ({len(objects)}): "
            f"{_compact_objects(objects, document)}\nSelected: {selected_names or 'none'}\n"
            "Action JSON examples (submit one or more objects in actions): "
            f'{{"op":"set_value","target":"{stream_tag}","property":"pressure","value":{{"value":2,"unit":"bar"}}}}; '
            f'{{"op":"add_unit","type":"Pump","tag":"{next_unit_tag}","near":"{unit_tag}"}}; '
            f'{{"op":"insert_unit_after","type":"Pump","after":"{unit_tag}","tag":"{next_unit_tag}"}}; '
            f'{{"op":"connect","from":"{unit_tag}","from_port":"outlet","to":"{next_unit_tag}","to_port":"inlet"}}; '
            f'{{"op":"disconnect","stream":"{stream_tag}"}}; '
            f'{{"op":"mirror","target":"{unit_tag}","axis":"horizontal"}}; '
            f'{{"op":"move","target":"{unit_tag}","dx":20,"dy":0}}; '
            f'{{"op":"rename","target":"{unit_tag}","new_tag":"{next_unit_tag}"}}; '
            f'{{"op":"delete","target":"{unit_tag}"}}.\n'
            "Limits: reactions are Arrhenius power-law only; Monod/custom rate laws unsupported. "
            "Reactions and thermo are edited in the operator editor. DWSIM runs only from the operator Run button."
        )
        bounded_text = text[:6000]
        actions = ["set_value", "add_unit", "insert_unit_after", "connect", "disconnect", "mirror", "move", "rename", "delete"]
        limits = ["Arrhenius power-law only; no Monod/custom laws", "DWSIM Run is operator-only"]
        payload = {
            "surface": "process",
            "route_id": ref.route_id,
            "workspace_id": workspace_id,
            "base_revision": record["revision"],
            "draft_id": draft_id,
            "candidate_id": None,
            "selected": selected,
            "summary": summary,
            "text": bounded_text,
            "actions": actions,
            "limits": limits,
        }
        return SurfaceBrief(
            surface="process",
            route_id=ref.route_id,
            workspace_id=workspace_id,
            base_revision=record["revision"],
            draft_id=draft_id,
            selected=selected,
            summary=summary,
            text=bounded_text,
            actions=actions,
            limits=limits,
            digest=_digest(payload),
        )

    candidate = get_candidate(workspace_id, ref.candidate_id) if ref.candidate_id else None
    if ref.candidate_id and candidate is None:
        return _brief_none(
            workspace_id,
            ref,
            "The referenced BLUECAD candidate is unknown or belongs to another workspace; no surface object was selected.",
        )
    if not ref.candidate_id:
        with open_sqlite_connection() as connection:
            row = connection.execute(
                "SELECT id FROM bluecad_candidates WHERE workspace_id=? AND status='valid' ORDER BY created_at DESC LIMIT 1",
                (workspace_id,),
            ).fetchone()
        candidate = get_candidate(workspace_id, str(row["id"])) if row else None
    if candidate is None or candidate.status != "valid" or not candidate.spec_artifact_id:
        return _brief_none(workspace_id, ref, "No valid BLUECAD candidate is available in this workspace.")
    spec = _load_candidate_spec(candidate.spec_artifact_id, workspace_id)
    part_by_id = {item["part_id"]: item for item in spec["parts"]}
    selected = [_bluecad_part_brief(part_by_id[item]) for item in ref.bluecad_part_ids if item in part_by_id]
    ignored = len(selected) != len(ref.bluecad_part_ids)
    summary = f"BLUECAD: {_safe_surface_label(candidate.brief_text, 'candidate')} · {len(spec['parts'])} part(s)"
    if selected:
        part = selected[0]
        summary += f" · selected: {part['part_id']} ({part['kind']})"
    if ignored:
        summary += "; unknown or foreign part selection ignored"
    display_parts = [_bluecad_part_brief(item) for item in spec["parts"][:20]]
    example_part = (selected[0] if selected else _bluecad_part_brief(spec["parts"][0]))["part_id"]
    text = (
        f"BLUECAD workspace {workspace_id}; candidate {candidate.id}; parts: "
        f"{json.dumps({'count': len(spec['parts']), 'items': display_parts}, separators=(',', ':'))}; selected: "
        f"{json.dumps(selected, separators=(',', ':'))}\nAction JSON examples: "
        f'{{"op":"duplicate_part","part":{json.dumps(example_part)},"placement":"beside","gap_mm":25}}; '
        f'{{"op":"set_part_param","part":{json.dumps(example_part)},"param":"length","value":2,"unit":"m"}}; '
        f'{{"op":"move_part","part":{json.dumps(example_part)},"dx":10,"dy":0,"dz":0,"unit":"mm"}}; '
        f'{{"op":"delete_part","part":{json.dumps(example_part)}}}.\n'
        f"Limits: supported part kinds {sorted(SUPPORTED_PART_KINDS)}; per-part supported parameters are listed above; "
        "base candidate is never modified; "
        "each action creates a child candidate."
    )
    bounded_text = text[:6000]
    actions = ["duplicate_part", "set_part_param", "move_part", "delete_part"]
    limits = [f"Supported GeometrySpec kinds: {', '.join(sorted(SUPPORTED_PART_KINDS))}",
              "base candidate is immutable; actions derive children"]
    payload = {
        "surface": "bluecad",
        "route_id": ref.route_id,
        "workspace_id": workspace_id,
        "base_revision": candidate.id,
        "draft_id": None,
        "candidate_id": candidate.id,
        "selected": selected,
        "summary": summary,
        "text": bounded_text,
        "actions": actions,
        "limits": limits,
    }
    return SurfaceBrief(
        surface="bluecad",
        route_id=ref.route_id,
        workspace_id=workspace_id,
        base_revision=candidate.id,
        candidate_id=candidate.id,
        selected=selected,
        summary=summary,
        text=bounded_text,
        actions=actions,
        limits=limits,
        digest=_digest(payload),
    )


def _process_object_brief(item: dict) -> dict:
    if item["kind"] == "stream":
        properties = {}
        if item["type"] == "EnergyStream":
            current = item.get("spec", {}).get("duty")
            properties["duty"] = _property_brief(current, "power")
        else:
            for key, (kind, _storage_key, _label) in STREAM_SPECS.items():
                properties[key] = _property_brief(item.get("spec", {}).get(key), kind)
            properties["composition"] = {
                "kind": "composition",
                "unit": item.get("spec", {}).get("composition_basis", "mass"),
                "value": item.get("spec", {}).get("composition"),
            }
        return {
            "kind": item["kind"],
            "type": item["type"],
            "id": item["id"],
            "tag": item["tag"],
            "properties": properties,
        }
    unit_spec = UNIT_REGISTRY[item["type"]]
    properties = {
        param.key: _property_brief(item.get("params", {}).get(param.key), param.kind)
        for param in unit_spec.params_for(item.get("mode"))
    }
    return {
        "kind": item["kind"],
        "type": item["type"],
        "id": item["id"],
        "tag": item["tag"],
        "mode": item.get("mode"),
        "properties": properties,
    }


def _property_brief(current: dict | None, kind: str) -> dict:
    display_unit = current.get("unit") if current else QUANTITY_UNITS[kind][1][0]
    return {
        "kind": kind,
        "si_unit": QUANTITY_UNITS[kind][0],
        "unit": display_unit,
        "value": current.get("value") if current else None,
        "si_value": current.get("si") if current else None,
    }


def _bluecad_part_brief(part: dict) -> dict:
    return {
        "part_id": part["part_id"],
        "kind": part["kind"],
        "params": {
            key: {
                "value": value,
                "unit": "deg" if key == "angle" else "unitless" if key in {"n_out", "n_mounts", "branch_count"} else "mm",
            }
            for key, value in part["params"].items()
        },
        "frame": part.get("frame", {"origin": [0.0, 0.0, 0.0], "direction": [1.0, 0.0, 0.0]}),
    }


def _safe_surface_label(value: object, fallback: str) -> str:
    """Keep owner labels readable without echoing paths or credential-like text."""
    if not isinstance(value, str):
        return fallback
    label = re.sub(r"(?:[A-Za-z]:\\|/)[^\s,;]+", "[path]", value)
    label = re.sub(r"(?i)\b(api[_ -]?key|token|password|secret)\s*[:=]\s*\S+", r"\1=[redacted]", label)
    label = " ".join(label.split())[:80].strip(" .,:;-")
    return label or fallback


def _compact_objects(objects: list[dict], document: dict) -> str:
    by_id = document["objects"]
    rows = []
    for item in objects[:35]:
        row = f"{item['tag']}:{item['type']}"
        if item["kind"] == "stream":
            source = by_id.get((item.get("source") or {}).get("unit"), {}).get("tag", "external")
            target = by_id.get((item.get("target") or {}).get("unit"), {}).get("tag", "external")
            row += f" ({source} → {target})"
        rows.append(row)
    if len(objects) > 35:
        rows.append(f"… {len(objects) - 35} more")
    return ", ".join(rows) or "none"


def _load_candidate_spec(artifact_id: str, workspace_id: str) -> dict:
    with open_sqlite_connection() as connection:
        row = connection.execute(
            "SELECT stored_path FROM artifacts WHERE id=? AND workspace_id=? AND status='registered'",
            (artifact_id, workspace_id),
        ).fetchone()
    if not row:
        raise ActionError("candidate_artifact_missing", "Candidate geometry artifact is unavailable.", 404)
    from pathlib import Path

    path = Path(row["stored_path"])
    spec = json.loads(path.read_text(encoding="utf-8"))
    return canonicalize_geometry_spec(spec)


def _store(outcome: ActionOutcome, request: ActionRequest, origin: ActionOrigin) -> ActionOutcome:
    now = outcome.updated_at
    with open_sqlite_connection() as connection:
        connection.execute(
            """INSERT INTO workspace_actions
            (id,workspace_id,surface,state,tier,origin_json,thread_id,interaction_id,relay_run_id,request_json,request_digest,outcome_json,created_at,updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                outcome.action_id,
                outcome.workspace_id,
                outcome.surface,
                outcome.state,
                outcome.tier,
                origin.model_dump_json(),
                origin.thread_id,
                origin.interaction_id,
                origin.relay_run_id,
                _canonical(request.model_dump(mode="json")),
                outcome.request_digest,
                outcome.model_dump_json(),
                outcome.created_at,
                now,
            ),
        )
        connection.commit()
    return outcome


def _outcome(
    workspace_id: str,
    request: ActionRequest,
    origin: ActionOrigin,
    state: Literal["applied", "proposed", "refused", "stale", "dismissed", "undone"],
    tier: Literal["immediate", "confirm", "none"],
    summary: str,
    *,
    changes: list[ChangeLine] | None = None,
    reason: str | None = None,
    reason_code: str | None = None,
    draft_id: str | None = None,
) -> ActionOutcome:
    now = _now()
    return ActionOutcome(
        action_id=str(uuid4()),
        workspace_id=workspace_id,
        surface=request.surface,
        state=state,
        tier=tier,
        summary=summary,
        changes=changes or [],
        base_revision=request.base_revision,
        draft_id=draft_id,
        reason_code=reason_code,
        reason=reason,
        origin=origin,
        request_digest=_digest(request.model_dump(mode="json")),
        request=request.model_dump(mode="json"),
        created_at=now,
        updated_at=now,
    )


def _action_summary(request: ActionRequest, changes: list[ChangeLine]) -> str:
    """Turn validated requests and their resolved changes into concise card text."""
    summaries = []
    resolved_unit_tags: set[str] = set()
    for action in request.actions:
        if action.op == "set_value":
            line = next((item for item in changes if item.label == f"{action.target} {action.property}"), None)
            value = re.sub(r"(?<=\d)\.0(?=\s|$)", "", line.after) if line and line.after else None
            summaries.append(f"Set {action.target} {action.property} to {value}" if value else
                             f"Set {action.target} {action.property}")
        elif action.op == "add_unit":
            tag = action.tag
            if tag is None:
                line = next((item for item in changes
                             if item.label.endswith(f"— new {action.type}")
                             and item.label.split(" — ", 1)[0] not in resolved_unit_tags), None)
                tag = line.label.split(" — ", 1)[0] if line else action.type
            resolved_unit_tags.add(tag)
            summaries.append(f"Add {action.type} {tag}" + (f" near {action.near}" if action.near else ""))
        elif action.op == "insert_unit_after":
            tag = action.tag
            if tag is None:
                line = next((item for item in changes
                             if (item.label.endswith(f"— new {action.type}")
                                 or item.label.endswith(f" — inserted after {action.after}"))
                             and item.label.split(" — ", 1)[0] not in resolved_unit_tags), None)
                tag = line.label.split(" — ", 1)[0] if line else action.type
            resolved_unit_tags.add(tag)
            summaries.append(f"Add {action.type} {tag} after {action.after}")
        elif action.op == "mirror":
            summaries.append(f"Mirror {action.target} {action.axis}ly" if action.axis == "horizontal"
                             else f"Mirror {action.target} vertically")
        elif action.op == "move":
            summaries.append(f"Move {action.target} by ({action.dx:g}, {action.dy:g})")
        elif action.op == "connect":
            summaries.append(f"Connect {action.source} to {action.to}")
        elif action.op == "disconnect":
            summaries.append(f"Disconnect {action.stream}")
        elif action.op == "rename":
            summaries.append(f"Rename {action.target} to {action.new_tag}")
        elif action.op == "delete":
            summaries.append(f"Delete {action.target}")
    return "; ".join(summaries)[:400] or "Workspace action"


def submit(workspace_id: str, request: ActionRequest, origin: ActionOrigin) -> ActionOutcome:
    request = request.model_copy(update={"actions": _unique_actions(request)})
    digest = _digest(request.model_dump(mode="json"))
    if origin.kind == "relay" and not origin.relay_run_id:
        return _store(
            _outcome(
                workspace_id,
                request,
                origin,
                "refused",
                "none",
                "Relay action provenance is incomplete.",
                reason="A relay_run_id is required for Relay-origin actions.",
                reason_code="origin_invalid",
            ),
            request,
            origin,
        )
    if origin.kind == "local" and not origin.interaction_id:
        return _store(
            _outcome(
                workspace_id,
                request,
                origin,
                "refused",
                "none",
                "Local action provenance is incomplete.",
                reason="An interaction_id is required for local actions.",
                reason_code="origin_invalid",
            ),
            request,
            origin,
        )
    if request.surface == "bluecad":
        base_candidate = get_candidate(workspace_id, request.base_revision)
        if base_candidate is None or base_candidate.status != "valid":
            return _store(
                _outcome(
                    workspace_id,
                    request,
                    origin,
                    "stale",
                    "none",
                    "Base BLUECAD candidate is no longer valid.",
                    reason="The referenced base candidate is unavailable or archived.",
                    reason_code="stale",
                ),
                request,
                origin,
            )
        try:
            from app.modules.workspace_actions.bluecad_actions import apply_bluecad_request

            outcome = apply_bluecad_request(workspace_id, request, origin, digest)
        except (ValueError, KeyError) as exc:
            outcome = _outcome(
                workspace_id,
                request,
                origin,
                "refused",
                "none",
                "Action was refused.",
                reason=str(exc),
                reason_code="invalid_action",
            )
        return _store(outcome, request, origin)

    found = _find_draft(workspace_id, revision=request.base_revision, draft_id=request.draft_id)
    if not found:
        return _store(
            _outcome(
                workspace_id,
                request,
                origin,
                "stale",
                "none",
                "Process draft changed or could not be uniquely resolved; refresh the brief.",
                reason="No unique current Process draft matches this base revision. Include draft_id from the surface brief and retry.",
                reason_code="stale",
            ),
            request,
            origin,
        )
    draft_id, record = found
    try:
        ops, changes = _process_ops(record["document"], request)
        after = draft.apply_ops(record["document"], ops)
        if any(op.op == "delete" for op in ops):
            before_blockers = {
                (item["code"], item["object"], item["field"])
                for item in draft.validate_document(record["document"])
                if item["severity"] == "blocker"
            }
            after_blockers = {
                (item["code"], item["object"], item["field"])
                for item in draft.validate_document(after)
                if item["severity"] == "blocker"
            }
            if after_blockers - before_blockers:
                raise ValueError(
                    "Delete would leave required Process data invalid: "
                    + ", ".join(sorted(code for code, _obj, _field in after_blockers - before_blockers))
                )
    except Exception as exc:
        return _store(
            _outcome(
                workspace_id,
                request,
                origin,
                "refused",
                "none",
                "Action was refused.",
                reason=str(exc),
                reason_code="invalid_action",
                draft_id=draft_id,
            ),
            request,
            origin,
        )
    tier: Literal["immediate", "confirm"] = (
        "confirm"
        if origin.kind == "relay" or any(op.op not in {"move", "set_orientation"} for op in ops)
        else "immediate"
    )
    result = _outcome(
        workspace_id,
        request,
        origin,
        "proposed" if tier == "confirm" else "applied",
        tier,
        _action_summary(request, changes),
        changes=changes,
        draft_id=draft_id,
    )
    if tier == "immediate":
        try:
            updated = draft.patch(
                workspace_id,
                draft_id,
                request.base_revision,
                ops,
                actor=_actor(origin),
                provenance={"action_request_digest": digest},
            )
            result.result_revision = updated["revision"]
            result.undo_available = True
        except draft.DraftError as exc:
            result.state, result.reason_code, result.reason = "stale", exc.code, str(exc)
    return _store(result, request, origin)


def _unique_actions(request: ActionRequest) -> list[ProcessAction | BluecadAction]:
    """Drop repeated idempotent assignments, preserving repeated additive actions."""
    actions: list[ProcessAction | BluecadAction] = []
    seen: set[str] = set()
    for action in request.actions:
        if action.op not in {"set_value", "set_part_param"}:
            actions.append(action)
            continue
        encoded = _canonical(action.model_dump(mode="json", by_alias=False))
        if encoded not in seen:
            seen.add(encoded)
            actions.append(action)
    return actions


def _target(document: dict, tag: str, kind: str | None = None) -> dict:
    item = document["objects"].get(tag) or next(
        (obj for obj in document["objects"].values() if obj["tag"] == tag), None
    )
    if item is None or kind and item["kind"] != kind:
        raise ValueError(f"Unknown {kind or 'Process object'} {tag!r}.")
    return item


def _port_index(unit_type: str, port_name: str | None, end: str) -> int:
    spec = draft.UNIT_REGISTRY[unit_type]
    ports = spec.outlets if end == "outlet" else spec.inlets
    if port_name is None:
        return 0
    if port_name not in ports:
        raise ValueError(f"{unit_type} {end} port must be one of: {', '.join(ports)}.")
    return ports.index(port_name)


def _next_id(objects: dict, prefix: str, ops: list | None = None) -> str:
    index = len(objects) + 1
    used = set(objects)
    for op in ops or []:
        if getattr(op, "id", None):
            used.add(op.id)
    while f"{prefix}{index}" in used:
        index += 1
    return f"{prefix}{index}"


def _next_tag(objects: dict, prefix: str, ops: list | None = None) -> str:
    used = {item["tag"] for item in objects.values()}
    used.update(tag for op in ops or [] if (tag := getattr(op, "tag", None)))
    index = 1
    while f"{prefix}{index}" in used:
        index += 1
    return f"{prefix}{index}"


def _process_ops(document: dict, request: ActionRequest) -> tuple[list[DraftOp], list[ChangeLine]]:
    ops: list[DraftOp] = []
    changes: list[ChangeLine] = []
    objects = document["objects"]
    for action in request.actions:
        if action.op in {"duplicate_part", "set_part_param", "move_part", "delete_part"}:
            raise ValueError("BLUECAD actions cannot execute on the Process surface.")
        if action.op == "set_value":
            target = _target(document, action.target)
            if target["kind"] == "stream":
                supported = {"temperature", "pressure", "mass_flow", "molar_flow", "vapor_fraction", "composition"}
                if action.property not in supported:
                    raise ValueError(
                        "Streams support temperature, pressure, mass_flow, molar_flow, vapor_fraction, and composition."
                    )
                value = action.value
                if action.property == "composition":
                    if not isinstance(value, dict):
                        raise ValueError("Stream composition must be a compound fraction map.")
                    ops.append(SetStreamSpec(op="set_stream_spec", stream=target["id"], composition=value))
                elif isinstance(value, Quantity):
                    quantity = DraftQuantity(value=value.value, unit=value.unit)
                    if action.property == "temperature":
                        ops.append(SetStreamSpec(op="set_stream_spec", stream=target["id"], temperature=quantity))
                    elif action.property == "pressure":
                        ops.append(SetStreamSpec(op="set_stream_spec", stream=target["id"], pressure=quantity))
                    elif action.property == "mass_flow":
                        ops.append(SetStreamSpec(op="set_stream_spec", stream=target["id"], mass_flow=quantity))
                    elif action.property == "molar_flow":
                        ops.append(SetStreamSpec(op="set_stream_spec", stream=target["id"], molar_flow=quantity))
                    elif action.property == "vapor_fraction":
                        ops.append(SetStreamSpec(op="set_stream_spec", stream=target["id"], vapor_fraction=quantity))
                else:
                    raise ValueError("Stream values must include a numeric value and unit.")
                before = target.get("spec", {}).get(action.property)
                after = value.model_dump() if isinstance(value, Quantity) else value
            elif target["kind"] == "unit":
                supported = {p.key for p in UNIT_REGISTRY[target["type"]].params}
                if action.property not in supported:
                    raise ValueError(
                        f"{target['type']} supports parameters: {', '.join(sorted(supported)) or 'none'}; kinetics is unsupported."
                    )
                if not isinstance(action.value, Quantity):
                    raise ValueError("Unit parameter values must include a numeric value and unit.")
                quantity = DraftQuantity(value=action.value.value, unit=action.value.unit)
                ops.append(SetUnitParams(op="set_unit_params", unit=target["id"], values={action.property: quantity}))
                before = target.get("params", {}).get(action.property)
                after = quantity.model_dump()
            else:
                raise ValueError("This Process object cannot be edited.")
            changes.append(
                ChangeLine(
                    label=f"{target['tag']} {action.property}",
                    before=_display(before),
                    after=_display(after) or str(after),
                )
            )
        elif action.op == "add_unit":
            if action.type not in draft.UNIT_REGISTRY:
                raise ValueError(
                    f"Unsupported unit type {action.type!r}; supported types: {', '.join(sorted(draft.UNIT_REGISTRY))}."
                )
            near = _target(document, action.near, "unit") if action.near else None
            tag = action.tag or _next_tag(objects, f"{action.type}_", ops)
            ops.append(
                AddUnit(
                    op="add_unit",
                    type=action.type,
                    tag=tag,
                    x=(near or {"x": max((o["x"] for o in objects.values()), default=0) + 160})["x"] + 120,
                    y=(near or {"y": 0})["y"],
                )
            )
            changes.append(ChangeLine(label=f"{tag} — new {action.type}", after="added"))
        elif action.op == "insert_unit_after":
            if action.type not in draft.UNIT_REGISTRY:
                raise ValueError(
                    f"Unsupported unit type {action.type!r}; supported types: {', '.join(sorted(draft.UNIT_REGISTRY))}."
                )
            upstream = _target(document, action.after, "unit")
            outlets = [
                stream
                for stream in objects.values()
                if stream["kind"] == "stream"
                and stream["type"] != "EnergyStream"
                and (stream.get("source") or {}).get("unit") == upstream["id"]
            ]
            if len(outlets) != 1:
                raise ValueError(
                    f"Cannot insert after {upstream['tag']}: expected one material outlet stream, found {len(outlets)}."
                )
            outlet = outlets[0]
            target_end = outlet.get("target")
            new_tag = action.tag or _next_tag(objects, f"{action.type}_", ops)
            new_unit_id = _next_id(objects, "u", ops)
            stream_tag = _next_tag(objects, "S_auto", ops)
            stream_id = _next_id(objects, "s", ops)
            near = {"x": upstream["x"], "y": upstream["y"]}
            ops.extend(
                [
                    AddUnit(
                        op="add_unit", id=new_unit_id, type=action.type, tag=new_tag, x=near["x"] + 160, y=near["y"]
                    ),
                    AddStream(op="add_stream", id=stream_id, tag=stream_tag, x=near["x"] + 80, y=near["y"]),
                    Disconnect(op="disconnect", stream=outlet["id"], end="source"),
                    DraftConnect(
                        op="connect",
                        stream=stream_id,
                        end="source",
                        unit=upstream["id"],
                        port=(outlet.get("source") or {}).get("port", 0),
                    ),
                    DraftConnect(op="connect", stream=stream_id, end="target", unit=new_unit_id, port=0),
                    DraftConnect(op="connect", stream=outlet["id"], end="source", unit=new_unit_id, port=0),
                ]
            )
            if target_end:
                ops.append(
                    DraftConnect(
                        op="connect",
                        stream=outlet["id"],
                        end="target",
                        unit=target_end["unit"],
                        port=target_end["port"],
                    )
                )
            changes.append(
                ChangeLine(
                    label=f"{new_tag} — inserted after {upstream['tag']}",
                    after=f"{stream_tag} → {new_tag} → {outlet['tag']}",
                )
            )
        elif action.op == "connect":
            source = _target(document, action.source, "unit")
            target = _target(document, action.to, "unit")
            source_port = _port_index(source["type"], action.source_port, "outlet")
            target_port = _port_index(target["type"], action.to_port, "inlet")
            tag = _next_tag(objects, "S_auto", ops)
            stream_id = _next_id(objects, "s", ops)
            ops.extend(
                [
                    AddStream(
                        op="add_stream",
                        id=stream_id,
                        tag=tag,
                        x=(source["x"] + target["x"]) // 2,
                        y=(source["y"] + target["y"]) // 2,
                    ),
                    DraftConnect(op="connect", stream=stream_id, end="source", unit=source["id"], port=source_port),
                    DraftConnect(op="connect", stream=stream_id, end="target", unit=target["id"], port=target_port),
                ]
            )
            changes.append(ChangeLine(label=f"{tag} — connection", after=f"{source['tag']} → {target['tag']}"))
        elif action.op == "disconnect":
            stream = _target(document, action.stream, "stream")
            for end in ("source", "target"):
                if stream.get(end):
                    ops.append(Disconnect(op="disconnect", stream=stream["id"], end=end))
            changes.append(ChangeLine(label=f"{stream['tag']} connection", after="disconnected"))
        elif action.op == "mirror":
            target = _target(document, action.target, "unit")
            ops.append(
                SetOrientation(
                    op="set_orientation",
                    id=target["id"],
                    flip_y=action.axis == "horizontal",
                    flip_x=action.axis == "vertical",
                )
            )
            changes.append(ChangeLine(label=f"{target['tag']} orientation", after=f"mirrored {action.axis}"))
        elif action.op == "move":
            target = _target(document, action.target)
            ops.append(
                Move(
                    op="move",
                    id=target["id"],
                    x=max(-5000, min(5000, int(target["x"] + action.dx))),
                    y=max(-5000, min(5000, int(target["y"] + action.dy))),
                )
            )
            changes.append(
                ChangeLine(
                    label=f"{target['tag']} position",
                    after=f"({int(target['x'] + action.dx)}, {int(target['y'] + action.dy)})",
                )
            )
        elif action.op == "rename":
            target = _target(document, action.target)
            ops.append(Rename(op="rename", id=target["id"], tag=action.new_tag))
            changes.append(ChangeLine(label=f"{target['tag']} tag", before=target["tag"], after=action.new_tag))
        elif action.op == "delete":
            target = _target(document, action.target)
            ops.append(Delete(op="delete", id=target["id"]))
            changes.append(
                ChangeLine(label=f"{target['tag']} — delete {target['type']}", before="present", after="deleted")
            )
    if not ops:
        raise ValueError("No supported Process operations were supplied.")
    return ops, changes


def _display(value: object) -> str | None:
    if value is None:
        return None
    if isinstance(value, dict) and "value" in value and "unit" in value:
        return f"{value['value']} {value['unit']}"
    return str(value)


def _actor(origin: ActionOrigin) -> str:
    if origin.kind == "relay":
        return f"agent:relay:{origin.relay_run_id}"
    return f"agent:local:{origin.thread_id}/{origin.interaction_id}"


def apply(workspace_id: str, action_id: str) -> ActionOutcome:
    row = _row(workspace_id, action_id)
    outcome = ActionOutcome.model_validate_json(row["outcome_json"])
    if outcome.state != "proposed":
        raise ActionError("action_not_proposed", "Only proposed actions can be applied.", 409)
    # Claim the proposal before any owner mutation. The outcome JSON remains proposed
    # during execution; the durable state column prevents another request from racing.
    with open_sqlite_connection() as connection:
        claimed = connection.execute(
            "UPDATE workspace_actions SET state='applying' WHERE id=? AND workspace_id=? AND state='proposed'",
            (action_id, workspace_id),
        ).rowcount == 1
        connection.commit()
    if not claimed:
        raise ActionError("action_not_proposed", "Action is not proposed or is already being applied.", 409)
    request = ActionRequest.model_validate_json(row["request_json"])
    origin = ActionOrigin.model_validate_json(row["origin_json"])
    if outcome.surface == "bluecad":
        try:
            candidate = get_candidate(workspace_id, request.base_revision)
            if candidate is None or candidate.status != "valid":
                outcome.state, outcome.reason_code, outcome.reason = (
                    "stale",
                    "stale",
                    "Base candidate is no longer valid.",
                )
                _save_outcome(outcome)
                return outcome
            from app.modules.workspace_actions.bluecad_actions import execute_bluecad

            outcome.child_candidate_id = execute_bluecad(workspace_id, request, origin, outcome.request_digest)
            outcome.state, outcome.undo_available = "applied", True
        except Exception as exc:
            outcome.state, outcome.reason_code, outcome.reason = "refused", "build_failed", str(exc)
        _save_outcome(outcome)
        return outcome
    found = _find_draft(workspace_id, revision=request.base_revision, draft_id=request.draft_id)
    if not found:
        outcome.state, outcome.reason_code, outcome.reason = "stale", "stale", "Process draft head has moved."
    else:
        draft_id, record = found
        try:
            ops, _ = _process_ops(record["document"], request)
            updated = draft.patch(
                workspace_id,
                draft_id,
                request.base_revision,
                ops,
                actor=_actor(origin),
                provenance={"action_request_digest": outcome.request_digest},
            )
            outcome.state, outcome.result_revision, outcome.draft_id = "applied", updated["revision"], draft_id
            outcome.undo_available = True
        except draft.DraftError as exc:
            outcome.state, outcome.reason_code, outcome.reason = "stale", exc.code, str(exc)
        except Exception as exc:
            outcome.state, outcome.reason_code, outcome.reason = "refused", "apply_failed", str(exc)[:500]
    _save_outcome(outcome)
    return outcome


def dismiss(workspace_id: str, action_id: str) -> ActionOutcome:
    row = _row(workspace_id, action_id)
    outcome = ActionOutcome.model_validate_json(row["outcome_json"])
    with open_sqlite_connection() as connection:
        claimed = connection.execute(
            "UPDATE workspace_actions SET state='dismissing' WHERE id=? AND workspace_id=? AND state='proposed'",
            (action_id, workspace_id),
        ).rowcount == 1
        connection.commit()
    if not claimed or outcome.state != "proposed":
        raise ActionError("action_not_proposed", "Only proposed actions can be dismissed.", 409)
    outcome.state = "dismissed"
    outcome.updated_at = _now()
    _save_outcome(outcome)
    return outcome


def undo(workspace_id: str, action_id: str) -> ActionOutcome:
    row = _row(workspace_id, action_id)
    outcome = ActionOutcome.model_validate_json(row["outcome_json"])
    if outcome.state != "applied" or not outcome.undo_available:
        raise ActionError("undo_unavailable", "This action has no available undo.", 409)
    with open_sqlite_connection() as connection:
        claimed = connection.execute(
            "UPDATE workspace_actions SET state='undoing' WHERE id=? AND workspace_id=? AND state='applied'",
            (action_id, workspace_id),
        ).rowcount == 1
        connection.commit()
    if not claimed:
        raise ActionError("undo_unavailable", "This action is already being undone.", 409)
    if outcome.surface == "bluecad":
        from app.modules.bluecad.ledger import archive_candidate

        try:
            archive_candidate(workspace_id, outcome.child_candidate_id or "")
        except ValueError as exc:
            _save_outcome(outcome)
            raise ActionError("undo_conflict", str(exc), 409) from exc
        except Exception as exc:
            _save_outcome(outcome)
            raise ActionError("undo_failed", str(exc)[:500], 409) from exc
    else:
        if not outcome.result_revision or not outcome.draft_id:
            _save_outcome(outcome)
            raise ActionError("undo_unavailable", "Action revision details are unavailable.", 409)
        try:
            head = draft.projection(workspace_id, outcome.draft_id)["revision"]
            if head != outcome.result_revision:
                _save_outcome(outcome)
                raise ActionError("stale", "Draft head moved after this action; undo is no longer safe.", 409)
            draft.restore(workspace_id, outcome.draft_id, head, outcome.base_revision)
        except ActionError:
            raise
        except Exception as exc:
            _save_outcome(outcome)
            raise ActionError("undo_failed", str(exc)[:500], 409) from exc
    outcome.state, outcome.undo_available = "undone", False
    outcome.updated_at = _now()
    _save_outcome(outcome)
    return outcome


def _row(workspace_id: str, action_id: str):
    with open_sqlite_connection() as connection:
        row = connection.execute(
            "SELECT * FROM workspace_actions WHERE workspace_id=? AND id=?", (workspace_id, action_id)
        ).fetchone()
    if row is None:
        raise ActionError("action_not_found", "Workspace action was not found.", 404)
    return row


def get(workspace_id: str, action_id: str) -> ActionOutcome:
    return ActionOutcome.model_validate_json(_row(workspace_id, action_id)["outcome_json"])


def _save_outcome(outcome: ActionOutcome) -> None:
    outcome.updated_at = _now()
    with open_sqlite_connection() as connection:
        connection.execute(
            "UPDATE workspace_actions SET state=?,outcome_json=?,updated_at=? WHERE id=? AND workspace_id=?",
            (outcome.state, outcome.model_dump_json(), outcome.updated_at, outcome.action_id, outcome.workspace_id),
        )
        connection.commit()


def list_for(
    workspace_id: str, *, thread_id: str, interaction_id: str | None = None, relay_run_id: str | None = None
) -> list[ActionOutcome]:
    clauses, args = ["workspace_id=?", "thread_id=?"], [workspace_id, thread_id]
    if interaction_id:
        clauses.append("interaction_id=?")
        args.append(interaction_id)
    if relay_run_id:
        clauses.append("relay_run_id=?")
        args.append(relay_run_id)
    with open_sqlite_connection() as connection:
        rows = connection.execute(
            "SELECT outcome_json FROM workspace_actions WHERE " + " AND ".join(clauses) + " ORDER BY created_at", args
        ).fetchall()
    return [ActionOutcome.model_validate_json(row["outcome_json"]) for row in rows]
