"""Revisioned biological parameter sets and growth cards (spec 169)."""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
from datetime import UTC, datetime
from pathlib import Path
from threading import RLock
from typing import Any
from uuid import uuid4

from app.core.paths import build_paths
from app.modules.memory.literature_service import LiteratureError, get_literature_entry, get_literature_source
from app.modules.process_kernel.units import unit_registry
from app.modules.workspaces.service import get_workspace

from . import forms

_ID = re.compile(r"^[A-Za-z0-9_.-]{1,128}$")
_lock = RLock()
_SYMBOL_UNITS = {
    "mu_max": "1/hour", "k_d": "1/hour", "m_L": "1/hour", "m_D": "1/hour",
    "I": "umol/(m**2*s)", "I0": "umol/(m**2*s)", "I₀": "umol/(m**2*s)",
    "K_I": "umol/(m**2*s)", "K_i": "umol/(m**2*s)", "I_opt": "umol/(m**2*s)",
    "I_dark": "umol/(m**2*s)", "beta": "1", "β": "1", "k_X": "m**2/kg",
    "X": "kg/m**3", "L": "m", "T": "K", "T_min": "K", "T_opt": "K", "T_max": "K", "T_ref": "K",
    "E_a": "J/mol", "S": "kg/m**3", "S_j": "kg/m**3", "K": "kg/m**3", "K_j": "kg/m**3",
    "Q": "kg/kg", "Q_j": "kg/kg", "Q_min": "kg/kg", "Q_min,j": "kg/kg",
    "a": "1", "b": "1", "c": "1", "d": "1", "w_ash": "1",
}
_SYMBOL_RANGES = {
    "mu_max": "> 0", "k_d": "≥ 0", "m_L": "≥ 0", "m_D": "≥ 0", "I": "≥ 0", "I0": "≥ 0", "I₀": "≥ 0",
    "K_I": "> 0", "K_i": "> 0", "I_opt": "> 0", "I_dark": "≥ 0", "beta": "≥ 0", "β": "≥ 0",
    "k_X": "≥ 0", "X": "≥ 0", "L": "> 0", "T": "> 0", "T_min": "> 0", "T_opt": "> 0", "T_max": "> 0",
    "T_ref": "> 0", "E_a": "≥ 0", "S": "≥ 0", "S_j": "≥ 0", "K": "> 0", "K_j": "> 0", "Q": "≥ 0",
    "Q_j": "≥ 0", "Q_min": "> 0", "Q_min,j": "> 0", "a": "≥ 0", "b": "≥ 0", "c": "≥ 0", "d": "≥ 0",
    "w_ash": "[0, 1)",
}


def _unit_token(unit: str) -> str:
    return {"µmol m⁻² s⁻¹": "umol/(m**2*s)", "m² kg⁻¹": "m**2/kg", "kg m⁻³": "kg/m**3", "kg/m3": "kg/m**3",
            "kg element kg⁻¹ dry biomass": "kg/kg", "J mol⁻¹": "J/mol", "h⁻¹": "1/hour"}.get(unit, unit)


def _quantity_value(quantity: Any, name: str, unit: str) -> float:
    if not isinstance(quantity, dict) or "value" not in quantity or "unit" not in quantity:
        raise BioModelError("evaluation_input_unit_required", f"{name} must include a value and unit", field=name)
    value, supplied_unit = quantity["value"], quantity["unit"]
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise BioModelError("evaluation_input_invalid", f"{name} must be a finite number", field=name)
    try:
        registry = unit_registry()
        amount = registry.Quantity(float(value), _unit_token(str(supplied_unit)))
        target = registry.Quantity(1.0, unit)
        if amount.dimensionality != target.dimensionality:
            raise BioModelError("unit_incompatible", f"{name}: {supplied_unit} is not compatible with {unit}", field=name)
        return float(amount.to(unit).magnitude)
    except BioModelError:
        raise
    except Exception as exc:
        raise BioModelError("unit_invalid", f"{name}: unsupported unit {supplied_unit!r}", field=name) from exc


class BioModelError(ValueError):
    def __init__(self, code: str, message: str, status: int = 422, **detail: Any) -> None:
        super().__init__(message)
        self.code, self.status, self.detail = code, status, detail


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _root(workspace_id: str, aggregate: str) -> Path:
    if not _ID.fullmatch(workspace_id) or workspace_id in {".", ".."} or get_workspace(workspace_id) is None:
        raise BioModelError("workspace_not_found", "Workspace was not found", 404)
    return build_paths().bio_models_workspace_dir(workspace_id) / aggregate


def _path(workspace_id: str, aggregate: str, object_id: str) -> Path:
    if not _ID.fullmatch(object_id) or object_id in {".", ".."}:
        raise BioModelError("bio_model_not_found", "Biological model record was not found", 404)
    return _root(workspace_id, aggregate) / object_id


def _write(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
    temp.write_bytes(json.dumps(data, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False).encode())
    with temp.open("rb") as stream:
        os.fsync(stream.fileno())
    os.replace(temp, path)


def _read(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BioModelError("bio_model_not_found", "Biological model record was not found", 404) from exc
    if not isinstance(value, dict):
        raise BioModelError("bio_model_corrupt", "Biological model record is invalid", 500)
    return value


def _revision(doc: dict[str, Any], parent: str | None, actor: str, action: str) -> dict[str, Any]:
    body = {key: value for key, value in doc.items() if key not in {"revision", "digest", "history"}}
    digest = _digest(body)
    rev = {"revision": f"r-{uuid4().hex[:16]}", "digest": digest, "parent_revision": parent,
           "actor": actor, "created_at": _now(), "action": action, "document": body}
    return rev


def _head(path: Path) -> dict[str, Any]:
    return _read(path / "head.json")


def _current(path: Path) -> dict[str, Any]:
    head = _head(path)
    revision = _read(path / "revisions" / f"{head['revision']}.json")
    if revision.get("digest") != head.get("digest"):
        raise BioModelError("bio_model_corrupt", "Biological model head digest does not match its revision", 500)
    doc = dict(revision["document"])
    doc.update({"revision": revision["revision"], "digest": revision["digest"], "history": head.get("history", [])})
    return doc


def _commit(path: Path, doc: dict[str, Any], expected_revision: str, expected_digest: str, actor: str, action: str) -> dict[str, Any]:
    with _lock:
        current = _current(path)
        if current["revision"] != expected_revision or current["digest"] != expected_digest:
            raise BioModelError("revision_conflict", "This record changed; reload before saving.", 409,
                                current_revision=current["revision"], current_digest=current["digest"])
        doc = _reset_stale_values(path.parents[2].name, doc)
        revision = _revision(doc, current["revision"], actor, action)
        _write(path / "revisions" / f"{revision['revision']}.json", revision)
        history = list(current["history"]) + [{key: revision[key] for key in ("revision", "digest", "parent_revision", "actor", "created_at", "action")}]
        _write(path / "head.json", {"revision": revision["revision"], "digest": revision["digest"], "history": history})
        result = dict(revision["document"])
        result.update({"revision": revision["revision"], "digest": revision["digest"], "history": history})
        return _decorate_staleness(path.parents[2].name, result)


def _literature_snapshot(workspace_id: str, basis_ref: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Resolve an exact literature record and return its digest payload and source metadata."""
    try:
        if basis_ref.get("object_type") == "literature_entry":
            entry = get_literature_entry(workspace_id, str(basis_ref.get("object_id", "")))
            source = get_literature_source(workspace_id, entry.source_id)
            locator_confirmed = basis_ref.get("locator_confirmed") is True
        elif basis_ref.get("object_type") == "literature_source":
            source = get_literature_source(workspace_id, str(basis_ref.get("object_id", "")))
            locator = str(basis_ref.get("locator", "")).strip()
            locator_kind = basis_ref.get("locator_kind")
            if locator_kind not in {"page", "line", "section"} or not locator:
                raise BioModelError("locator_confirmation_required", "Confirm the source locator (page, line or section).", 422)
            entry = None
            locator_confirmed = basis_ref.get("locator_confirmed") is True
            if not locator_confirmed:
                raise BioModelError("locator_confirmation_required", f"Confirm the shown locator: {locator}.", 422, locator=locator)
        else:
            raise BioModelError("basis_ref_invalid", "basis_ref must identify a literature_entry or literature_source")
    except LiteratureError as exc:
        raise BioModelError(exc.code, exc.message, exc.status_code) from exc
    if entry is not None:
        locator_kind = entry.locator_kind
        if locator_kind is None and entry.value_number is None:
            raise BioModelError("literature_locator_missing", "The literature entry has no supported page, line or section locator.")
        if entry.value_number is None and not locator_confirmed:
            raise BioModelError("locator_confirmation_required", f"Confirm the shown {locator_kind} locator before verifying.", 422,
                                locator_kind=locator_kind, locator_start=entry.locator_start, locator_end=entry.locator_end)
        entry_data = {"id": entry.id, "value": entry.value_number, "unit": entry.unit, "text": entry.value_text or entry.statement,
                      "locator_kind": entry.locator_kind, "locator_start": entry.locator_start, "locator_end": entry.locator_end,
                      "context": entry.context_text}
    else:
        entry_data = {"id": None, "value": None, "unit": None, "text": None, "locator_kind": basis_ref["locator_kind"],
                      "locator_start": None, "locator_end": None, "context": basis_ref.get("locator")}
    backing_hash = source.backing.sha256 if source.backing else None
    if source.backing is not None and backing_hash is None:
        raise BioModelError("backing_digest_missing", "The registered literature artifact has no SHA-256 digest.")
    snapshot = {"source": {"id": source.id, "title": source.title, "source_kind": source.source_kind,
                           "state": source.state, "citation": source.citation, "publisher": source.publisher,
                           "published_year": source.published_year}, "entry": entry_data,
                "backing_sha256": backing_hash}
    return snapshot, {"source": source.model_dump(mode="json"), "entry": entry_data, "backing_sha256": backing_hash,
                      "backing_document_present": source.backing is not None}


def _snapshot_current(workspace_id: str, value: dict[str, Any]) -> str | None:
    basis = value.get("basis_ref")
    if not basis:
        return None
    try:
        snapshot, _metadata = _literature_snapshot(workspace_id, basis)
    except (BioModelError, LiteratureError):
        return None
    return _digest(snapshot)


def _decorate_staleness(workspace_id: str, doc: dict[str, Any]) -> dict[str, Any]:
    for value in doc.get("values", {}).values():
        stored = (value.get("verification") or {}).get("snapshot_digest")
        if stored and _snapshot_current(workspace_id, value) != stored:
            value["display_state"] = "source_changed_since_verification"
        else:
            value["display_state"] = value.get("state", "candidate")
    return doc


def _reset_stale_values(workspace_id: str, doc: dict[str, Any]) -> dict[str, Any]:
    for value in doc.get("values", {}).values():
        stored = (value.get("verification") or {}).get("snapshot_digest")
        if stored and _snapshot_current(workspace_id, value) != stored:
            value["state"] = "candidate"
            value["state_changed_by"] = "source-change-detected"
            value["state_changed_at"] = _now()
    return doc


def list_forms() -> list[dict[str, Any]]:
    return [dict(card) for card in forms.FORM_CARDS]


def create_set(workspace_id: str, name: str, species: str = "", strain: str = "", actor: str = "local-user") -> dict[str, Any]:
    path_root = _root(workspace_id, "sets")
    set_id = str(uuid4())
    doc = {"schema_version": 1, "id": set_id, "name": name, "species": species, "strain": strain,
           "conditions": "", "values": {}, "template": "N. gaditana T1 — empty"}
    revision = _revision(doc, None, actor, "create")
    _write(path_root / set_id / "revisions" / f"{revision['revision']}.json", revision)
    history = [{key: revision[key] for key in ("revision", "digest", "parent_revision", "actor", "created_at", "action")}]
    _write(path_root / set_id / "head.json", {"revision": revision["revision"], "digest": revision["digest"], "history": history})
    return {**doc, "revision": revision["revision"], "digest": revision["digest"], "history": history}


def get_set(workspace_id: str, set_id: str) -> dict[str, Any]:
    return _decorate_staleness(workspace_id, _current(_path(workspace_id, "sets", set_id)))


def list_sets(workspace_id: str) -> list[dict[str, Any]]:
    root = _root(workspace_id, "sets")
    return [get_set(workspace_id, path.name) for path in sorted(root.iterdir()) if path.is_dir() and (path / "head.json").exists()] if root.exists() else []


def duplicate_set(workspace_id: str, set_id: str, expected_revision: str, expected_digest: str,
                  actor: str = "local-user") -> dict[str, Any]:
    source = get_set(workspace_id, set_id)
    if source["revision"] != expected_revision or source["digest"] != expected_digest:
        raise BioModelError("revision_conflict", "The source set changed; reload before duplicating.", 409,
                            current_revision=source["revision"], current_digest=source["digest"])
    duplicate = {key: value for key, value in source.items() if key not in {"revision", "digest", "history"}}
    duplicate.update({"id": str(uuid4()), "name": f"{source['name']} copy", "values": json.loads(json.dumps(source["values"])),
                      "duplicated_from": {"set_id": set_id, "revision": source["revision"], "digest": source["digest"]}})
    duplicate = _reset_stale_values(workspace_id, duplicate)
    root = _root(workspace_id, "sets") / duplicate["id"]
    revision = _revision(duplicate, None, actor, "duplicate")
    _write(root / "revisions" / f"{revision['revision']}.json", revision)
    history = [{key: revision[key] for key in ("revision", "digest", "parent_revision", "actor", "created_at", "action")}]
    _write(root / "head.json", {"revision": revision["revision"], "digest": revision["digest"], "history": history})
    return {**duplicate, "revision": revision["revision"], "digest": revision["digest"], "history": history}


def edit_set_value(workspace_id: str, set_id: str, symbol: str, payload: dict[str, Any], expected_revision: str,
                   expected_digest: str, actor: str = "local-user") -> dict[str, Any]:
    if not symbol or len(symbol) > 128:
        raise BioModelError("symbol_invalid", "A valid model symbol is required")
    if symbol not in _SYMBOL_UNITS:
        raise BioModelError("symbol_unknown", f"{symbol} is not declared by a biological form", field=symbol)
    value, unit = payload.get("value"), payload.get("unit")
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise BioModelError("value_invalid", f"{symbol} must be a finite numeric value", field=symbol)
    if not isinstance(unit, str) or not unit:
        raise BioModelError("unit_invalid", f"{symbol} requires a unit", field=symbol)
    expected_unit = payload.get("expected_unit")
    canonical_unit = _SYMBOL_UNITS.get(symbol)
    if canonical_unit is not None:
        canonical_unit = _unit_token(canonical_unit)
        if expected_unit is not None and _unit_token(str(expected_unit)) != canonical_unit:
            raise BioModelError("symbol_unit_mismatch", f"{symbol} requires {canonical_unit}", field=symbol)
        expected_unit = canonical_unit
    try:
        registry = unit_registry()
        given = registry.Quantity(float(value), _unit_token(unit))
        if expected_unit:
            target = registry.Quantity(1.0, expected_unit)
            if given.dimensionality != target.dimensionality:
                raise BioModelError("unit_incompatible", f"{symbol}: {unit} is not compatible with {expected_unit}", field=symbol)
            canonical_value = float(given.to(expected_unit).magnitude)
            canonical_unit = expected_unit
        else:
            canonical_value, canonical_unit = float(value), _unit_token(unit)
    except Exception as exc:
        if isinstance(exc, BioModelError):
            raise
        raise BioModelError("unit_invalid", f"{symbol}: unsupported unit {unit!r}", field=symbol) from exc
    root = _path(workspace_id, "sets", set_id)
    doc = get_set(workspace_id, set_id)
    previous = doc["values"].get(symbol, {})
    record = {"value": canonical_value, "unit": canonical_unit, "basis_ref": payload.get("basis_ref", previous.get("basis_ref")),
              "species": payload.get("species", doc.get("species", "")), "strain": payload.get("strain", doc.get("strain", "")),
              "conditions": payload.get("conditions", doc.get("conditions", "")), "validity_range": _SYMBOL_RANGES[symbol],
              "state": "candidate", "verification": None, "state_changed_by": actor, "state_changed_at": _now()}
    doc["values"][symbol] = record
    return _commit(root, doc, expected_revision, expected_digest, actor, f"edit:{symbol}")


def verify_value(workspace_id: str, set_id: str, symbol: str, expected_revision: str, expected_digest: str,
                 actor: str = "local-user", locator_confirmed: bool = False) -> dict[str, Any]:
    root = _path(workspace_id, "sets", set_id)
    doc = get_set(workspace_id, set_id)
    value = doc["values"].get(symbol)
    if value is None or value.get("basis_ref") is None:
        raise BioModelError("basis_ref_required", f"{symbol} needs a literature basis_ref before verification", field=symbol)
    basis = dict(value["basis_ref"])
    basis["locator_confirmed"] = locator_confirmed or basis.get("locator_confirmed")
    snapshot, metadata = _literature_snapshot(workspace_id, basis)
    if snapshot["entry"]["value"] is not None and snapshot["entry"]["unit"]:
        source_value, source_unit = snapshot["entry"]["value"], snapshot["entry"]["unit"]
        try:
            registry = unit_registry()
            v = float(registry.Quantity(value["value"], value["unit"]).to_base_units().magnitude)
            v_src = float(registry.Quantity(source_value, _unit_token(source_unit)).to_base_units().magnitude)
        except Exception as exc:
            raise BioModelError("unit_incompatible", f"Cannot compare {symbol} in {value['unit']} with source unit {source_unit}") from exc
        if abs(v - v_src) > 1e-6 * max(abs(v), abs(v_src)) + 1e-12:
            raise BioModelError("literature_value_mismatch", f"{symbol}: entered {value['value']} {value['unit']}; source reports {source_value} {source_unit}",
                                entered=f"{value['value']} {value['unit']}", source=f"{source_value} {source_unit}")
    value["basis_ref"] = basis
    value["state"] = "source_verified"
    value["state_changed_by"], value["state_changed_at"] = actor, _now()
    value["verification"] = {"snapshot_digest": _digest(snapshot), "snapshot": snapshot, "resolved": metadata,
                              "no_backing_document": not metadata["backing_document_present"], "actor": actor, "verified_at": _now()}
    return _commit(root, doc, expected_revision, expected_digest, actor, f"verify:{symbol}")


def review_value(workspace_id: str, set_id: str, symbol: str, reviewer: str, note: str, expected_revision: str,
                 expected_digest: str, actor: str = "local-user") -> dict[str, Any]:
    root = _path(workspace_id, "sets", set_id)
    doc = get_set(workspace_id, set_id)
    value = doc["values"].get(symbol)
    if value is None or value.get("state") != "source_verified":
        raise BioModelError("source_verification_required", f"{symbol} must be source_verified before expert review", field=symbol)
    if not reviewer.strip() or not note.strip():
        raise BioModelError("review_details_required", "A reviewer name and note are required")
    value["state"] = "expert_reviewed"
    value["state_changed_by"], value["state_changed_at"] = actor, _now()
    value["review"] = {"reviewer": reviewer.strip(), "note": note.strip(), "actor": actor, "reviewed_at": _now()}
    return _commit(root, doc, expected_revision, expected_digest, actor, f"review:{symbol}")


def history(workspace_id: str, set_id: str) -> list[dict[str, Any]]:
    return list(get_set(workspace_id, set_id)["history"])


def _get_set_revision(workspace_id: str, set_id: str, revision_id: str) -> dict[str, Any]:
    path = _path(workspace_id, "sets", set_id)
    revision = _read(path / "revisions" / f"{revision_id}.json")
    if revision.get("revision") != revision_id or _digest(revision.get("document")) != revision.get("digest"):
        raise BioModelError("bio_model_corrupt", "Parameter set revision digest is invalid", 500)
    doc = dict(revision["document"])
    doc.update({"revision": revision_id, "digest": revision["digest"], "history": []})
    return _decorate_staleness(workspace_id, doc)


def create_card(workspace_id: str, name: str, set_id: str, factors: dict[str, Any], mu_max: dict[str, Any],
                actor: str = "local-user", n_source: str = "NH3") -> dict[str, Any]:
    if n_source not in {"NH3", "HNO3"}:
        raise BioModelError("nitrogen_source_invalid", "Nitrogen source must be NH3 or HNO3")
    parameter_set = get_set(workspace_id, set_id)
    form_ids: list[str] = []
    for field, form_id in factors.items():
        if field not in {"light", "optics", "temperature", "nutrients", "combination", "loss", "stoichiometry"}:
            raise BioModelError("factor_family_invalid", f"Unknown factor family {field}")
        selected = form_id if isinstance(form_id, list) else [form_id]
        for selected_form in selected:
            if not isinstance(selected_form, str):
                raise BioModelError("form_not_found", f"Factor {field} must select a biological form")
            try:
                forms.form_card(selected_form)
            except forms.FormRefusal as exc:
                raise BioModelError("form_not_found", str(exc)) from exc
            form_ids.append(selected_form)
    if _quantity_value(mu_max, "mu_max", "1/hour") <= 0:
        raise BioModelError("evaluation_value_invalid", "mu_max must be > 0", field="mu_max")
    normalized_mu_max = {"value": _quantity_value(mu_max, "mu_max", "1/hour"), "unit": "1/hour"}
    form_versions = {form_id: forms.form_card(form_id)["version"] for form_id in form_ids}
    card_id = str(uuid4())
    doc = {"schema_version": 1, "id": card_id, "name": name, "mu_max": normalized_mu_max,
           "factors": factors, "parameter_set_id": set_id, "parameter_set_revision": parameter_set["revision"],
           "parameter_set_digest": parameter_set["digest"], "form_versions": form_versions, "n_source": n_source}
    root = _root(workspace_id, "cards") / card_id
    revision = _revision(doc, None, actor, "create")
    _write(root / "revisions" / f"{revision['revision']}.json", revision)
    history_items = [{key: revision[key] for key in ("revision", "digest", "parent_revision", "actor", "created_at", "action")}]
    _write(root / "head.json", {"revision": revision["revision"], "digest": revision["digest"], "history": history_items})
    return {**doc, "revision": revision["revision"], "digest": revision["digest"], "history": history_items}


def list_cards(workspace_id: str) -> list[dict[str, Any]]:
    root = _root(workspace_id, "cards")
    if not root.exists():
        return []
    output = []
    for folder in sorted(root.iterdir()):
        if folder.is_dir() and (folder / "head.json").exists():
            current = _current(folder)
            output.append({**current, "history": current["history"]})
    return output


def evaluate_card(workspace_id: str, card_id: str, operating: dict[str, Any]) -> dict[str, Any]:
    path = _path(workspace_id, "cards", card_id)
    doc = _current(path)
    parameter_set = _get_set_revision(workspace_id, doc["parameter_set_id"], doc["parameter_set_revision"])
    if parameter_set["digest"] != doc["parameter_set_digest"]:
        raise BioModelError("parameter_set_revision_mismatch", "Pinned parameter set revision digest changed", 409)
    params = parameter_set["values"]
    factors = doc["factors"]
    for form_id, version in doc["form_versions"].items():
        if forms.form_card(form_id)["version"] != version:
            raise BioModelError("form_version_unavailable", f"Pinned form {form_id} v{version} is unavailable", 409)
    def required(symbol: str, unit: str) -> float:
        if symbol not in operating:
            raise BioModelError("evaluation_input_missing", f"{symbol} is required", field=symbol)
        return _quantity_value(operating[symbol], symbol, unit)
    def parameter(symbol: str) -> float:
        if symbol not in params:
            raise BioModelError("evaluation_value_missing", f"{symbol} is required", field=symbol)
        return float(params[symbol]["value"])
    try:
        light_form = factors["light"]
        light_fn = {"light.monod": forms.light_monod, "light.haldane": forms.light_haldane,
                    "light.steele": forms.light_steele, "light.eilers_peeters_steady": forms.light_eilers_peeters_steady}[light_form]
        light_arg_names = {"light.monod": ["K_I"], "light.haldane": ["K_I", "K_i"], "light.steele": ["I_opt"], "light.eilers_peeters_steady": ["I_opt", "beta"]}[light_form]
        light_args = {name: parameter(name) for name in light_arg_names}
        average = forms.slab_response_average(light_fn, required("I0", "umol/(m**2*s)"), required("k_X", "m**2/kg"),
                                              required("X", "kg/m**3"), required("L", "m"), **light_args)
        temp_form = factors["temperature"]
        if temp_form == "temperature.isothermal":
            thermal = forms.temperature_isothermal(required("T", "K"))
        elif temp_form == "temperature.ctmi":
            thermal = forms.temperature_ctmi(required("T", "K"), parameter("T_min"), parameter("T_opt"), parameter("T_max"))
        else:
            thermal = forms.temperature_arrhenius_ref(required("T", "K"), parameter("T_ref"), parameter("E_a"))
        nutrient_forms = factors["nutrients"]
        if not isinstance(nutrient_forms, list) or not nutrient_forms:
            raise BioModelError("evaluation_form_invalid", "At least one nutrient form is required")
        nutrient_values = []
        for index, nutrient_form in enumerate(nutrient_forms):
            suffix = f"_{index}" if len(nutrient_forms) > 1 else ""
            if nutrient_form == "nutrient.monod":
                nutrient_values.append(forms.nutrient_monod(required(f"S{suffix}" if suffix else "S", "kg/m**3"), parameter(f"K_j{suffix}" if suffix else "K_j")))
            elif nutrient_form == "nutrient.droop":
                nutrient_values.append(forms.nutrient_droop(required(f"Q{suffix}" if suffix else "Q", "kg/kg"), parameter(f"Q_min{suffix}" if suffix else "Q_min,j")))
            else:
                raise BioModelError("form_not_found", f"Unsupported nutrient form {nutrient_form}")
        nutrient = forms.combine_liebig(nutrient_values) if factors["combination"] == "combine.liebig" else forms.combine_multiplicative(nutrient_values)
        loss_form = factors["loss"]
        loss = forms.loss_first_order(parameter("k_d")) if loss_form == "loss.first_order" else forms.loss_light_dark(required("I0", "umol/(m**2*s)"), parameter("I_dark"), parameter("m_L"), parameter("m_D"))
        mu_max = _quantity_value(doc["mu_max"], "mu_max", "1/hour")
        if mu_max <= 0:
            raise BioModelError("evaluation_value_invalid", "mu_max must be > 0", field="mu_max")
        net = mu_max * average * thermal * nutrient - loss
        return {"model_card_id": card_id, "parameter_set_id": doc["parameter_set_id"], "mu_net": {"value": net, "unit": "h⁻¹"},
                "breakdown": {"mu_max": {"value": mu_max, "unit": "h⁻¹"}, "light_average": {"value": average, "unit": "1"},
                              "temperature": {"value": thermal, "unit": "1"}, "nutrients": {"value": nutrient, "unit": "1"},
                              "loss": {"value": loss, "unit": "h⁻¹"}}}
    except KeyError as exc:
        raise BioModelError("evaluation_form_invalid", f"Missing or unsupported form family: {exc.args[0]}") from exc
    except forms.FormRefusal as exc:
        raise BioModelError("evaluation_refused", str(exc)) from exc
