"""Draft authoring and immutable publication for Studio calculations."""

import hashlib
import json
from math import isfinite
from pathlib import Path
from uuid import uuid4

from app.core.database import open_sqlite_connection
from app.modules.events.service import utc_now
from app.modules.modeling.models import ModelSpecCreate, ModelSpecProjectUpdate
from app.modules.modeling.project_knowledge_owner import update_model_spec_in_transaction
from app.modules.modeling.service import create_model_spec
from app.modules.process_kernel.units import parse_unit_token, resolve_unit, unit_registry
from app.modules.runner.input_contracts import canonicalize_input_contract
from app.modules.runner.safety import model_implementation_root
from app.modules.studio.derive import derive_documentation
from app.modules.studio.models import StudioCreate, StudioError, StudioUpdate, TestRequest, model_payload
from app.modules.studio_runtime.runtime import RunRequest, run, status


def _json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def scaffold(contract: dict) -> str:
    """Contract-only deterministic source; user edits the placeholder."""
    names = [item["name"] for item in contract["inputs"]]
    signature = ", ".join(f"{name}: float" for name in names)
    arguments = ", ".join(f"{name}=inputs[{name!r}]" for name in names)
    lines = ["# Studio calculation. Magnitudes use the declared contract units.",
             f"def evaluate({signature}) -> dict[str, float]:",
             '    """Return every declared output from the declared inputs.', "", "    Inputs:",
             *(f"        {item['name']} [{item['unit']}]" for item in contract["inputs"]), "    Outputs:",
             *(f"        {item['name']} [{item['unit']}]" for item in contract["outputs"]), '    """',
             '    raise NotImplementedError("Complete evaluate before testing")', "",
             "", "def main(inputs: dict[str, float]) -> dict[str, float]:",
             f"    return evaluate({arguments})", ""]
    return "\n".join(lines)


def _contract(data: StudioCreate) -> tuple[dict, str]:
    contract = model_payload(data)
    return contract, _sha(_json(contract))


def _input_contract(contract: dict) -> tuple[str, str]:
    variables = []
    for item in contract["inputs"]:
        try:
            resolved = resolve_unit(item["unit"])
            physical_dimension = resolved.physical_dimension
            semantic_basis = resolved.semantic_basis
        except Exception:
            # Studio's runner path understands Pint's general dimensionality string.
            physical_dimension = str(unit_registry().Unit(parse_unit_token(item["unit"])).dimensionality)
            semantic_basis = None
        domain = {name: item[name] for name in ("min", "max") if name in item}
        variable = {"name": item["name"], "label": item["label"], "unit": item["unit"],
                    "required": True, "category": "model_parameter", "description": item["description"],
                    "physical_dimension": physical_dimension}
        if semantic_basis:
            variable["semantic_basis"] = semantic_basis
        if domain:
            variable["domain"] = domain
        variables.append(variable)
    payload, digest, _ = canonicalize_input_contract(
        {"schema_version": 2, "evaluation_mode": "forward", "variables": variables})
    return payload, digest


def _require_workspace(connection, workspace_id: str) -> None:
    if connection.execute("SELECT 1 FROM workspaces WHERE id = ?", (workspace_id,)).fetchone() is None:
        raise StudioError("studio_workspace_not_found", "Workspace not found.")


def _draft_row(connection, workspace_id: str, model_spec_id: str):
    row = connection.execute("""SELECT d.*, m.title, m.engineering_question, m.status AS model_status FROM studio_drafts d
        JOIN model_specs m ON m.id = d.model_spec_id
        WHERE d.workspace_id = ? AND d.model_spec_id = ?""", (workspace_id, model_spec_id)).fetchone()
    if row is None:
        raise StudioError("studio_model_not_found", "Studio model not found.")
    return row


def _versions(connection, model_spec_id: str) -> list[dict]:
    rows = connection.execute("""SELECT mv.id, mv.version_label, sp.source_sha256, sp.contract_sha256, mv.created_at
        FROM studio_published_versions sp JOIN model_versions mv ON mv.id = sp.version_id
        WHERE sp.model_spec_id = ? ORDER BY sp.rowid""", (model_spec_id,)).fetchall()
    return [dict(row) for row in rows]


def _read(connection, workspace_id: str, model_spec_id: str) -> dict:
    row = _draft_row(connection, workspace_id, model_spec_id)
    contract = json.loads(row["contract_json"])
    report = json.loads(row["test_report_json"]) if row["test_report_json"] else None
    return {"id": row["model_spec_id"], "workspace_id": workspace_id, "name": row["title"],
            "engineering_question": row["engineering_question"], "category": "calculation",
            **contract, "source": row["source"], "source_sha256": row["source_sha256"],
            "contract_sha256": row["contract_sha256"], "annotations": row["annotations"],
            "assumptions": row["assumption_notes"],
            "annotations_stale": bool(row["annotations"] and row["annotations_source_sha256"] != row["source_sha256"]),
            "status": row["model_status"],
            "documentation": {"derived": derive_documentation(row["source"]), **contract},
            "test_cases": json.loads(row["test_cases_json"]), "last_test_report": report,
            "versions": _versions(connection, model_spec_id), "created_at": row["created_at"],
            "updated_at": row["updated_at"]}


def create(workspace_id: str, data: StudioCreate) -> dict:
    contract, contract_sha = _contract(data)
    _input_contract(contract)
    source = scaffold(contract)
    now = utc_now()
    model_id = create_model_spec(workspace_id, ModelSpecCreate(
        title=data.name, engineering_question=data.engineering_question)).id
    with open_sqlite_connection() as connection:
        _require_workspace(connection, workspace_id)
        connection.execute("""INSERT INTO studio_drafts
            (model_spec_id, workspace_id, contract_json, source, source_sha256, contract_sha256, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (model_id, workspace_id, _json(contract), source, _sha(source), contract_sha, now, now))
        connection.commit()
        return _read(connection, workspace_id, model_id)


def get(workspace_id: str, model_spec_id: str) -> dict:
    with open_sqlite_connection() as connection:
        return _read(connection, workspace_id, model_spec_id)


def list_models(workspace_id: str) -> list[dict]:
    with open_sqlite_connection() as connection:
        _require_workspace(connection, workspace_id)
        ids = [row["model_spec_id"] for row in connection.execute(
            "SELECT model_spec_id FROM studio_drafts WHERE workspace_id = ? ORDER BY updated_at DESC", (workspace_id,))]
        return [_read(connection, workspace_id, model_id) for model_id in ids]


def update(workspace_id: str, model_spec_id: str, data: StudioUpdate) -> dict:
    with open_sqlite_connection() as connection:
        row = _draft_row(connection, workspace_id, model_spec_id)
        if row["model_status"] != "draft":
            raise StudioError("studio_revision_required", "Revise the published model before editing.")
        old_contract = json.loads(row["contract_json"])
        validated = StudioCreate.model_validate({
            "name": data.name or row["title"],
            "engineering_question": data.engineering_question or row["engineering_question"],
            "inputs": data.inputs if data.inputs is not None else old_contract["inputs"],
            "outputs": data.outputs if data.outputs is not None else old_contract["outputs"],
        })
        contract, contract_sha = _contract(validated)
        _input_contract(contract)
        source = data.source if data.source is not None else row["source"]
        annotations = data.annotations if data.annotations is not None else row["annotations"]
        assumptions = data.assumptions if data.assumptions is not None else row["assumption_notes"]
        annotation_hash = _sha(source) if data.annotations is not None else row["annotations_source_sha256"]
        changed = _sha(source) != row["source_sha256"] or contract_sha != row["contract_sha256"]
        now = utc_now()
        spec_row = connection.execute("SELECT updated_at FROM model_specs WHERE id = ?", (model_spec_id,)).fetchone()
        update_model_spec_in_transaction(connection, model_spec_id, ModelSpecProjectUpdate(
            workspace_id=workspace_id, expected_updated_at=spec_row["updated_at"],
            title=validated.name, engineering_question=validated.engineering_question))
        connection.execute("""UPDATE studio_drafts SET contract_json = ?, source = ?, source_sha256 = ?,
            contract_sha256 = ?, annotations = ?, assumption_notes = ?, annotations_source_sha256 = ?,
            test_report_json = ?, updated_at = ? WHERE model_spec_id = ?""",
            (_json(contract), source, _sha(source), contract_sha, annotations, assumptions, annotation_hash,
             None if changed else row["test_report_json"], now, model_spec_id))
        connection.commit()
        return _read(connection, workspace_id, model_spec_id)


def test(workspace_id: str, model_spec_id: str, data: TestRequest) -> dict:
    with open_sqlite_connection() as connection:
        row = _draft_row(connection, workspace_id, model_spec_id)
        if row["model_status"] != "draft":
            raise StudioError("studio_revision_required", "Revise the published model before testing.")
        source, contract = row["source"], json.loads(row["contract_json"])
        input_names = {item["name"] for item in contract["inputs"]}
        output_names = {item["name"] for item in contract["outputs"]}
        cases = []
        for case in data.cases:
            errors = []
            if set(case.inputs) != input_names:
                errors.append("Input names do not match the contract.")
            if case.expected_outputs is not None and not set(case.expected_outputs).issubset(output_names):
                errors.append("Expected output names do not match the contract.")
            if not errors:
                for item in contract["inputs"]:
                    value = case.inputs[item["name"]]
                    if item.get("min") is not None and value < item["min"] or item.get("max") is not None and value > item["max"]:
                        errors.append(f"Input {item['name']} is outside its bounds.")
            result = run(RunRequest(source=source, inputs=case.inputs)) if not errors else None
            outputs = result.result if result and result.classification == "ok" else None
            if result and result.classification != "ok":
                errors.append(f"Runtime {result.classification}: {result.stderr.strip() or status()['reason'] or 'execution failed'}")
            if outputs is not None:
                if not isinstance(outputs, dict) or set(outputs) != output_names or any(
                    isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value)
                    for value in outputs.values()
                ):
                    errors.append("Every declared output must be present and finite numeric data.")
                elif case.expected_outputs is not None:
                    for name, expected in case.expected_outputs.items():
                        if abs(outputs[name] - expected) > case.tolerance:
                            errors.append(f"Output {name} differs from expected by more than tolerance.")
            cases.append({"passed": not errors, "classification": result.classification if result else "invalid_case",
                          "outputs": outputs, "errors": errors})
        report = {"source_sha256": row["source_sha256"], "contract_sha256": row["contract_sha256"],
                  "passed": all(case["passed"] for case in cases), "cases": cases}
        connection.execute("""UPDATE studio_drafts SET test_cases_json = ?, test_report_json = ?, updated_at = ?
            WHERE model_spec_id = ?""", (_json([case.model_dump() for case in data.cases]), _json(report), utc_now(), model_spec_id))
        connection.commit()
        return report


def publish(workspace_id: str, model_spec_id: str) -> dict:
    with open_sqlite_connection() as connection:
        row = _draft_row(connection, workspace_id, model_spec_id)
        if row["model_status"] != "draft":
            raise StudioError("studio_revision_required", "Revise the published model before publishing again.")
        report = json.loads(row["test_report_json"]) if row["test_report_json"] else None
        if not report or not report["passed"] or not report["cases"] or report["source_sha256"] != row["source_sha256"] or report["contract_sha256"] != row["contract_sha256"]:
            raise StudioError("studio_publish_report_required", "A passing test report for the current source and contract is required.")
        contract = json.loads(row["contract_json"])
        input_payload, input_sha = _input_contract(contract)
        next_number = len(_versions(connection, model_spec_id)) + 1
        version_id, artifact_id, now = str(uuid4()), str(uuid4()), utc_now()
        version_label = f"v{next_number}"
        directory = model_implementation_root(workspace_id) / version_id
        directory.mkdir(parents=True, exist_ok=False)
        artifact_path = directory / "studio_calc.py"
        try:
            artifact_path.write_bytes(row["source"].encode("utf-8"))
            connection.execute("""INSERT INTO artifacts (id, workspace_id, filename, stored_path, artifact_type,
                mime_type, sha256, source_ref, status, created_at) VALUES (?, ?, ?, ?, 'python_script',
                'text/x-python', ?, ?, 'registered', ?)""",
                (artifact_id, workspace_id, artifact_path.name, str(artifact_path), row["source_sha256"],
                 f"model_spec:{model_spec_id}", now))
            connection.execute("""INSERT INTO model_versions (id, workspace_id, model_spec_id, version_label,
                implementation_artifact_id, implementation_kind, status, changelog, input_contract_payload,
                input_contract_sha256, created_at, notes) VALUES (?, ?, ?, ?, ?, 'studio_calc_v1', 'published',
                'Studio calculation publication', ?, ?, ?, 'Scientifically unqualified')""",
                (version_id, workspace_id, model_spec_id, version_label, artifact_id, input_payload, input_sha, now))
            connection.execute("""INSERT INTO studio_published_versions
                (version_id, model_spec_id, contract_json, source_sha256, contract_sha256, created_at)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (version_id, model_spec_id, row["contract_json"], row["source_sha256"], row["contract_sha256"], now))
            spec_row = connection.execute("SELECT updated_at FROM model_specs WHERE id = ?", (model_spec_id,)).fetchone()
            update_model_spec_in_transaction(connection, model_spec_id, ModelSpecProjectUpdate(
                workspace_id=workspace_id, expected_updated_at=spec_row["updated_at"], status="published"))
            connection.commit()
        except Exception:
            artifact_path.unlink(missing_ok=True)
            directory.rmdir()
            raise
        return {"id": version_id, "model_spec_id": model_spec_id, "name": row["title"],
                "version_label": version_label, "source_sha256": row["source_sha256"],
                "contract_sha256": row["contract_sha256"], "created_at": now,
                "scientific_status": "unqualified"}


def revise(workspace_id: str, model_spec_id: str) -> dict:
    with open_sqlite_connection() as connection:
        _draft_row(connection, workspace_id, model_spec_id)
        versions = _versions(connection, model_spec_id)
        if not versions:
            raise StudioError("studio_no_published_version", "Publish a version before revising.")
        version = versions[-1]
        artifact = connection.execute("""SELECT a.stored_path FROM artifacts a
            JOIN model_versions mv ON mv.implementation_artifact_id = a.id WHERE mv.id = ?""", (version["id"],)).fetchone()
        if artifact is None:
            raise StudioError("studio_artifact_missing", "Published artifact is missing.")
        path = Path(artifact["stored_path"])
        if path != model_implementation_root(workspace_id) / version["id"] / "studio_calc.py" or _sha(path.read_text(encoding="utf-8")) != version["source_sha256"]:
            raise StudioError("studio_artifact_hash_mismatch", "Published source artifact is invalid.")
        published = connection.execute("SELECT contract_json FROM studio_published_versions WHERE version_id = ?", (version["id"],)).fetchone()
        now = utc_now()
        connection.execute("""UPDATE studio_drafts SET contract_json = ?, source = ?, source_sha256 = ?,
            contract_sha256 = ?, test_cases_json = '[]', test_report_json = NULL, revision_of_version_id = ?,
            updated_at = ? WHERE model_spec_id = ?""",
            (published["contract_json"], path.read_text(encoding="utf-8"), version["source_sha256"],
             version["contract_sha256"], version["id"], now, model_spec_id))
        spec_row = connection.execute("SELECT updated_at FROM model_specs WHERE id = ?", (model_spec_id,)).fetchone()
        update_model_spec_in_transaction(connection, model_spec_id, ModelSpecProjectUpdate(
            workspace_id=workspace_id, expected_updated_at=spec_row["updated_at"], status="draft"))
        connection.commit()
        return _read(connection, workspace_id, model_spec_id)


def library(workspace_id: str) -> list[dict]:
    with open_sqlite_connection() as connection:
        _require_workspace(connection, workspace_id)
        rows = connection.execute("""SELECT mv.id, mv.model_spec_id, m.title AS name, mv.version_label,
            sp.source_sha256, sp.contract_sha256, mv.created_at FROM studio_published_versions sp
            JOIN model_versions mv ON mv.id = sp.version_id JOIN model_specs m ON m.id = mv.model_spec_id
            WHERE mv.workspace_id = ? ORDER BY sp.rowid DESC""", (workspace_id,)).fetchall()
        return [{**dict(row), "scientific_status": "unqualified"} for row in rows]

