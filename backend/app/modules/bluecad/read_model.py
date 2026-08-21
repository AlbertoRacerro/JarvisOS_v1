"""Read-only BLUECAD candidate aggregate assembled from canonical owner services."""

from __future__ import annotations  # noqa: I001

import collections
from decimal import Decimal, InvalidOperation
import json
import math
from pathlib import Path
import sqlite3
import typing
import urllib.parse

from pydantic import BaseModel, Field

from app.core.database import open_sqlite_connection
from app.core.paths import build_paths
from app.modules.bluecad.cad_link import (
    CadLinkError,
    GEOMETRY_INPUTS,
    TRANSFORMATION_VERSION,
    _digest,
    _verify_model_identity,
)
from app.modules.bluecad.evidence import EvidenceRecord, select_candidate_evidence_records
from app.modules.bluecad.ledger import get_candidate_from_connection
from app.modules.bluecad.models import BluecadCandidateRead
from app.modules.flowsheet.freshness import get_resolved_node_stale_states_from_connection
from app.modules.flowsheet.models import FlowsheetGraphRead, FlowsheetNodeRead
from app.modules.flowsheet.service import FlowsheetError, build_flowsheet_graph_from_connection


ReadDiagnosticCode = typing.Literal[
    "missing_reference",
    "malformed_reference",
    "inaccessible_reference",
    "unsupported_reference",
]
AggregateFreshness = typing.Literal["fresh", "stale", "unknown", "mixed"]


class BluecadArtifactRefRead(BaseModel):
    id: str
    roles: list[str]
    filename: str
    mime_type: str
    sha256: str
    status: str
    source_ref: str | None = None
    created_at: str
    content_url: str


class BluecadEvidenceRefRead(BaseModel):
    ref: str
    kind: str
    subject_ref: str
    status: str
    stale: bool | None = None
    created_at: str | None = None
    summary: str | None = None


class BluecadRunRefRead(BaseModel):
    ref: str
    kind: typing.Literal["simulation_run", "runner_job"]
    status: str | None = None
    stale: bool | None = None
    created_at: str | None = None
    source_ref: str | None = None


class BluecadReadDiagnostic(BaseModel):
    code: ReadDiagnosticCode
    source: str
    reference: str
    message: str


class BluecadSemanticBindingRead(BaseModel):
    value: float
    unit: typing.Literal["m", "mm"]
    source_parameter_id: str


class BluecadSemanticSourceRead(BaseModel):
    schema_version: typing.Literal[1] = 1
    kind: typing.Literal["cad_link_047_m0"]
    transformation_version: typing.Literal["bluerev_047_m0_tube_proxy_v0_1"]
    source_simulation_run_id: str
    source_model_version_id: str
    geometry_bindings: dict[str, BluecadSemanticBindingRead]


class BluecadCandidateAggregateRead(BaseModel):
    candidate: BluecadCandidateRead
    artifacts: list[BluecadArtifactRefRead] = Field(default_factory=list)
    evidence: list[BluecadEvidenceRefRead] = Field(default_factory=list)
    runs: list[BluecadRunRefRead] = Field(default_factory=list)
    semantic_source: BluecadSemanticSourceRead | None = None
    freshness: AggregateFreshness
    diagnostics: list[BluecadReadDiagnostic] = Field(default_factory=list)


_ARTIFACT_ROLE_FIELDS = (
    ("candidate.spec_artifact_id", "spec_artifact_id"),
    ("candidate.glb_artifact_id", "glb_artifact_id"),
    ("candidate.report_artifact_id", "report_artifact_id"),
)
_ATTEMPT_ARTIFACT_ROLE_FIELDS = (
    ("attempt.spec_artifact_id", "spec_artifact_id"),
    ("attempt.report_artifact_id", "report_artifact_id"),
    ("attempt.manifest_artifact_id", "manifest_artifact_id"),
)
_GRAPH_DIAGNOSTIC_MAP: dict[str, ReadDiagnosticCode] = {
    "dangling_reference": "missing_reference",
    "unsupported_reference": "unsupported_reference",
    "malformed_reference": "malformed_reference",
    "payload_invalid": "malformed_reference",
    "payload_reference_invalid": "malformed_reference",
    "context_manifest_invalid": "malformed_reference",
}
_SEMANTIC_SOURCE_MESSAGES: dict[ReadDiagnosticCode, str] = {
    "missing_reference": "Reviewed-047 semantic source references a missing canonical record.",
    "inaccessible_reference": "Reviewed-047 semantic source references data inaccessible in this workspace.",
    "malformed_reference": "Reviewed-047 semantic source provenance is malformed or ambiguous.",
    "unsupported_reference": "",
}
_SEMANTIC_SOURCE_PRECEDENCE: tuple[ReadDiagnosticCode, ...] = (
    "inaccessible_reference",
    "missing_reference",
    "malformed_reference",
)


def get_bluecad_candidate_aggregate(
    workspace_id: str,
    candidate_id: str,
) -> BluecadCandidateAggregateRead | None:
    """Return one coherent read-only candidate aggregate or ``None`` for an inaccessible candidate."""
    with open_sqlite_connection() as connection:
        connection.execute("PRAGMA query_only = ON")
        connection.execute("BEGIN")
        try:
            return _aggregate_from_connection(connection, workspace_id, candidate_id)
        finally:
            connection.rollback()


def _aggregate_from_connection(
    connection: sqlite3.Connection,
    workspace_id: str,
    candidate_id: str,
) -> BluecadCandidateAggregateRead | None:
    candidate = get_candidate_from_connection(connection, workspace_id, candidate_id)
    if candidate is None:
        return None

    diagnostics: list[BluecadReadDiagnostic] = []
    semantic_source = _load_semantic_source(connection, workspace_id, candidate.id, diagnostics)
    artifact_roles = _collect_artifact_roles(candidate)
    artifact_ids = set(artifact_roles)
    artifacts = _load_artifacts(connection, workspace_id, artifact_roles, diagnostics)
    evidence_records = select_candidate_evidence_records(
        connection,
        workspace_id=workspace_id,
        candidate_id=candidate.id,
        attempt_ids=[attempt.id for attempt in candidate.attempts],
    )
    evidence = _build_evidence(candidate, evidence_records)

    graph: FlowsheetGraphRead | None
    try:
        graph = build_flowsheet_graph_from_connection(connection, workspace_id)
    except (FlowsheetError, ValueError) as exc:
        graph = None
        diagnostics.append(
            BluecadReadDiagnostic(
                code="inaccessible_reference",
                source="flowsheet.graph",
                reference=f"bluecad_candidate:{candidate.id}",
                message=f"Flowsheet provenance is unavailable: {type(exc).__name__}.",
            )
        )

    runs: list[BluecadRunRefRead] = []
    freshness_states: list[str] = []
    if graph is not None:
        runs = _build_runs(candidate, artifact_ids, evidence, graph)
        freshness_states = _apply_freshness(connection, workspace_id, graph, evidence, runs)
        _append_graph_diagnostics(graph, candidate, artifact_ids, evidence, runs, diagnostics)

    return BluecadCandidateAggregateRead(
        candidate=candidate,
        artifacts=artifacts,
        evidence=evidence,
        runs=runs,
        semantic_source=semantic_source,
        freshness=_aggregate_freshness(freshness_states),
        diagnostics=sorted(
            _dedupe_diagnostics(diagnostics),
            key=lambda item: (item.source, item.reference, item.code, item.message),
        ),
    )


def _semantic_source_diagnostic(
    diagnostics: list[BluecadReadDiagnostic],
    candidate_id: str,
    defects: set[ReadDiagnosticCode],
) -> None:
    for code in _SEMANTIC_SOURCE_PRECEDENCE:
        if code not in defects:
            continue
        diagnostics.append(
            BluecadReadDiagnostic(
                code=code,
                source="bluecad.semantic_source",
                reference=f"bluecad_candidate:{candidate_id}",
                message=_SEMANTIC_SOURCE_MESSAGES[code],
            )
        )
        return


def _decimal_snapshot_value(value: object) -> tuple[float, Decimal] | None:
    if not isinstance(value, str) or not value or value.strip() != value:
        return None
    try:
        parsed = Decimal(value)
    except (InvalidOperation, ValueError):
        return None
    if not parsed.is_finite():
        return None
    number = float(parsed)
    if not math.isfinite(number) or (parsed != 0 and number == 0.0):
        return None
    return number, parsed


def _load_semantic_source(
    connection: sqlite3.Connection,
    workspace_id: str,
    candidate_id: str,
    diagnostics: list[BluecadReadDiagnostic],
) -> BluecadSemanticSourceRead | None:
    """Project exact candidate-level reviewed-047 provenance; selected-part eligibility remains frontend-owned."""
    rows = connection.execute(
        """
        SELECT *
        FROM bluecad_cad_links
        WHERE workspace_id = ?
          AND child_candidate_id = ?
          AND transformation_version = ?
        ORDER BY created_at, id
        """,
        (workspace_id, candidate_id, TRANSFORMATION_VERSION),
    ).fetchall()
    if not rows:
        return None
    if len(rows) != 1:
        _semantic_source_diagnostic(diagnostics, candidate_id, {"malformed_reference"})
        return None

    link = rows[0]
    defects: set[ReadDiagnosticCode] = set()

    source_run_id = str(link["source_simulation_run_id"] or "")
    source_job_id = str(link["source_runner_job_id"] or "")
    if not source_run_id or not source_job_id:
        defects.add("missing_reference")

    run = None
    if source_run_id:
        run = connection.execute(
            "SELECT * FROM simulation_runs WHERE id = ?",
            (source_run_id,),
        ).fetchone()
        if run is None:
            defects.add("missing_reference")
        elif str(run["workspace_id"]) != workspace_id:
            defects.add("inaccessible_reference")
        elif str(run["status"]) != "succeeded":
            defects.add("malformed_reference")

    job = None
    if source_job_id:
        job = connection.execute(
            "SELECT * FROM runner_jobs WHERE id = ?",
            (source_job_id,),
        ).fetchone()
        if job is None:
            defects.add("missing_reference")
        elif str(job["workspace_id"]) != workspace_id:
            defects.add("inaccessible_reference")
        else:
            if source_run_id and str(job["simulation_run_id"]) != source_run_id:
                defects.add("malformed_reference")
            if str(job["status"]) != "succeeded":
                defects.add("malformed_reference")

    model_version_id = ""
    if run is not None:
        model_version_id = str(run["model_version_id"] or "")
        if not model_version_id:
            defects.add("missing_reference")

    model = None
    model_with_digest = None
    if model_version_id:
        model = connection.execute(
            "SELECT * FROM model_versions WHERE id = ?",
            (model_version_id,),
        ).fetchone()
        if model is None:
            defects.add("missing_reference")
        elif str(model["workspace_id"]) != workspace_id:
            defects.add("inaccessible_reference")
        else:
            implementation_artifact_id = str(model["implementation_artifact_id"] or "")
            if not implementation_artifact_id:
                defects.add("missing_reference")
            else:
                artifact = connection.execute(
                    "SELECT id, workspace_id, sha256 FROM artifacts WHERE id = ?",
                    (implementation_artifact_id,),
                ).fetchone()
                if artifact is None:
                    defects.add("missing_reference")
                elif str(artifact["workspace_id"]) != workspace_id:
                    defects.add("inaccessible_reference")
                else:
                    model_with_digest = connection.execute(
                        """
                        SELECT mv.*, a.sha256 AS script_sha256
                        FROM model_versions mv
                        JOIN artifacts a ON a.id = mv.implementation_artifact_id
                        WHERE mv.id = ? AND mv.workspace_id = ? AND a.workspace_id = ?
                        """,
                        (model_version_id, workspace_id, workspace_id),
                    ).fetchone()

    current_identity: dict[str, typing.Any] | None = None
    if model_with_digest is not None and job is not None and str(job["workspace_id"]) == workspace_id:
        try:
            current_identity = _verify_model_identity(model_with_digest, job)
        except CadLinkError:
            defects.add("malformed_reference")

    stored_identity: object = None
    snapshot: object = None
    try:
        stored_identity = json.loads(str(link["source_model_identity_json"]))
        snapshot = json.loads(str(link["source_snapshot_json"]))
    except (json.JSONDecodeError, TypeError, ValueError):
        defects.add("malformed_reference")

    if not isinstance(stored_identity, dict):
        defects.add("malformed_reference")
    else:
        if current_identity is not None and stored_identity != current_identity:
            defects.add("malformed_reference")
        if str(link["source_model_identity_digest"] or "") != _digest(stored_identity):
            defects.add("malformed_reference")

    geometry_bindings: dict[str, BluecadSemanticBindingRead] = {}
    if not isinstance(snapshot, dict) or set(snapshot) != set(GEOMETRY_INPUTS):
        defects.add("malformed_reference")
    else:
        if str(link["source_snapshot_digest"] or "") != _digest(snapshot):
            defects.add("malformed_reference")
        parameter_ids: set[str] = set()
        for name in GEOMETRY_INPUTS:
            item = snapshot.get(name)
            if not isinstance(item, dict):
                defects.add("malformed_reference")
                continue
            parameter_ref = item.get("parameter_ref")
            if not isinstance(parameter_ref, str) or not parameter_ref.startswith("parameter:"):
                defects.add("malformed_reference")
                continue
            parameter_id = parameter_ref.removeprefix("parameter:")
            if not parameter_id or parameter_id in parameter_ids:
                defects.add("malformed_reference")
                continue
            parameter_ids.add(parameter_id)

            expected_unit = "m" if name == "tube_length" else "mm"
            if item.get("unit") != expected_unit or item.get("status") != "accepted" or item.get("freshness") != "fresh":
                defects.add("malformed_reference")

            executed = _decimal_snapshot_value(item.get("executed_value"))
            current = _decimal_snapshot_value(item.get("current_value"))
            if executed is None or current is None or executed[1] != current[1]:
                defects.add("malformed_reference")

            parameter = connection.execute(
                "SELECT id, workspace_id, unit FROM parameters WHERE id = ?",
                (parameter_id,),
            ).fetchone()
            if parameter is None:
                defects.add("missing_reference")
            elif str(parameter["workspace_id"]) != workspace_id:
                defects.add("inaccessible_reference")
            elif str(parameter["unit"]) != expected_unit:
                defects.add("malformed_reference")

            if executed is not None:
                geometry_bindings[name] = BluecadSemanticBindingRead(
                    value=executed[0],
                    unit=expected_unit,
                    source_parameter_id=parameter_id,
                )

    if defects:
        _semantic_source_diagnostic(diagnostics, candidate_id, defects)
        return None
    if run is None or model is None or len(geometry_bindings) != len(GEOMETRY_INPUTS):
        _semantic_source_diagnostic(diagnostics, candidate_id, {"malformed_reference"})
        return None

    return BluecadSemanticSourceRead(
        schema_version=1,
        kind="cad_link_047_m0",
        transformation_version=TRANSFORMATION_VERSION,
        source_simulation_run_id=source_run_id,
        source_model_version_id=model_version_id,
        geometry_bindings=geometry_bindings,
    )


def _collect_artifact_roles(candidate: BluecadCandidateRead) -> dict[str, set[str]]:
    roles: dict[str, set[str]] = collections.defaultdict(set)
    for role, field_name in _ARTIFACT_ROLE_FIELDS:
        reference = getattr(candidate, field_name)
        if reference:
            roles[str(reference)].add(role)
    for attempt in candidate.attempts:
        for role, field_name in _ATTEMPT_ARTIFACT_ROLE_FIELDS:
            reference = getattr(attempt, field_name)
            if reference:
                roles[str(reference)].add(role)
    return roles


def _artifact_content_is_accessible(stored_path_value: object) -> bool:
    try:
        stored_path = Path(str(stored_path_value)).resolve()
        data_root = build_paths().data_root.resolve()
        stored_path.relative_to(data_root)
    except (OSError, RuntimeError, ValueError):
        return False
    return stored_path.exists() and stored_path.is_file()


def _load_artifacts(
    connection: sqlite3.Connection,
    workspace_id: str,
    artifact_roles: dict[str, set[str]],
    diagnostics: list[BluecadReadDiagnostic],
) -> list[BluecadArtifactRefRead]:
    if not artifact_roles:
        return []
    artifact_ids = sorted(artifact_roles)
    placeholders = ", ".join("?" for _ in artifact_ids)
    rows = connection.execute(
        f"""
        SELECT id, artifact_type, filename, stored_path, mime_type, sha256, status, source_ref, created_at
        FROM artifacts
        WHERE workspace_id = ? AND id IN ({placeholders})
        """,
        (workspace_id, *artifact_ids),
    ).fetchall()
    rows_by_id = {str(row["id"]): row for row in rows}
    result: list[BluecadArtifactRefRead] = []
    for artifact_id in artifact_ids:
        row = rows_by_id.get(artifact_id)
        if row is None:
            diagnostics.append(
                BluecadReadDiagnostic(
                    code="missing_reference",
                    source="bluecad.artifact",
                    reference=artifact_id,
                    message="Referenced BLUECAD artifact is missing or inaccessible in this workspace.",
                )
            )
            continue
        if not str(row["artifact_type"] or "").startswith("bluecad_"):
            diagnostics.append(
                BluecadReadDiagnostic(
                    code="inaccessible_reference",
                    source="bluecad.artifact",
                    reference=artifact_id,
                    message="Referenced artifact is not accessible through the BLUECAD artifact surface.",
                )
            )
            continue
        if not _artifact_content_is_accessible(row["stored_path"]):
            diagnostics.append(
                BluecadReadDiagnostic(
                    code="inaccessible_reference",
                    source="bluecad.artifact.content",
                    reference=artifact_id,
                    message="Referenced BLUECAD artifact content is not accessible through the content route.",
                )
            )
            continue
        if row["sha256"] is None:
            diagnostics.append(
                BluecadReadDiagnostic(
                    code="malformed_reference",
                    source="bluecad.artifact.sha256",
                    reference=artifact_id,
                    message="Referenced BLUECAD artifact has no canonical content digest.",
                )
            )
            continue
        result.append(
            BluecadArtifactRefRead(
                id=artifact_id,
                roles=sorted(artifact_roles[artifact_id]),
                filename=str(row["filename"]),
                mime_type=str(row["mime_type"] or "application/octet-stream"),
                sha256=str(row["sha256"]),
                status=str(row["status"]),
                source_ref=None if row["source_ref"] is None else str(row["source_ref"]),
                created_at=str(row["created_at"]),
                content_url=(
                    f"/workspaces/{urllib.parse.quote(workspace_id, safe='')}/bluecad/artifacts/"
                    f"{urllib.parse.quote(artifact_id, safe='')}/content"
                ),
            )
        )
    return sorted(result, key=lambda item: (item.id, tuple(item.roles)))


def _build_evidence(
    candidate: BluecadCandidateRead,
    records: list[EvidenceRecord],
) -> list[BluecadEvidenceRefRead]:
    attempt_refs = {attempt.id: f"bluecad_attempt:{attempt.id}" for attempt in candidate.attempts}
    candidate_ref = f"bluecad_candidate:{candidate.id}"
    result: list[BluecadEvidenceRefRead] = []
    for record in records:
        subject_refs: set[str] = set()
        if record.candidate_id == candidate.id:
            subject_refs.add(candidate_ref)
        if record.attempt_id in attempt_refs:
            subject_refs.add(attempt_refs[str(record.attempt_id)])
        for subject_ref in sorted(subject_refs):
            result.append(
                BluecadEvidenceRefRead(
                    ref=f"evidence:{record.id}",
                    kind=record.kind,
                    subject_ref=subject_ref,
                    status=record.verdict,
                    created_at=record.created_at,
                    summary=None,
                )
            )
    return sorted(result, key=lambda item: (item.ref, item.subject_ref))


def _build_runs(
    candidate: BluecadCandidateRead,
    artifact_ids: set[str],
    evidence: list[BluecadEvidenceRefRead],
    graph: FlowsheetGraphRead,
) -> list[BluecadRunRefRead]:
    nodes = {node.ref: node for node in graph.nodes}
    subject_refs = {f"bluecad_candidate:{candidate.id}"}
    subject_refs.update(f"bluecad_attempt:{attempt.id}" for attempt in candidate.attempts)
    artifact_refs = {f"artifact:{artifact_id}" for artifact_id in artifact_ids}
    bridge_refs = set(subject_refs)
    bridge_refs.update(artifact_refs)
    bridge_refs.update(item.ref for item in evidence)
    if candidate.promoted_decision_id:
        decision_ref = f"decision:{candidate.promoted_decision_id}"
        if decision_ref in nodes:
            bridge_refs.add(decision_ref)

    associations: set[tuple[str, str | None]] = set()
    for edge in graph.edges:
        upstream = nodes.get(edge.upstream_ref)
        downstream = nodes.get(edge.downstream_ref)
        if upstream is None or downstream is None:
            continue
        if edge.upstream_ref in bridge_refs and downstream.kind in {"simulation_run", "runner_job"}:
            associations.add((downstream.ref, edge.upstream_ref))
        if edge.downstream_ref in bridge_refs and upstream.kind in {"simulation_run", "runner_job"}:
            associations.add((upstream.ref, edge.downstream_ref))

    # Follow only accepted forward provenance/dependency paths rooted in candidate-owned
    # artifacts. Restrict intermediate kinds so shared model-spec or unrelated workspace
    # nodes cannot pull in runs heuristically.
    forward_refs = set(artifact_refs)
    frontier = sorted(artifact_refs)
    safe_intermediate_kinds = {"artifact", "model_version"}
    while frontier:
        current_ref = frontier.pop(0)
        for edge in graph.edges:
            if edge.upstream_ref != current_ref:
                continue
            downstream = nodes.get(edge.downstream_ref)
            if downstream is None:
                continue
            if downstream.kind in {"simulation_run", "runner_job"}:
                associations.add((downstream.ref, current_ref))
                continue
            if downstream.kind not in safe_intermediate_kinds or downstream.ref in forward_refs:
                continue
            forward_refs.add(downstream.ref)
            frontier.append(downstream.ref)

    associated_refs = {ref for ref, _source in associations}
    for edge in graph.edges:
        upstream = nodes.get(edge.upstream_ref)
        downstream = nodes.get(edge.downstream_ref)
        if upstream is None or downstream is None:
            continue
        if upstream.kind != "simulation_run" or downstream.kind != "runner_job":
            continue
        if upstream.ref in associated_refs:
            associations.add((downstream.ref, upstream.ref))
        if downstream.ref in associated_refs:
            associations.add((upstream.ref, downstream.ref))

    return [
        BluecadRunRefRead(
            ref=ref,
            kind=nodes[ref].kind,
            status=nodes[ref].status,
            created_at=nodes[ref].created_at,
            source_ref=source_ref,
        )
        for ref, source_ref in sorted(associations, key=lambda item: (item[0], item[1] or ""))
    ]


_EMPTY_NODE = FlowsheetNodeRead(
    ref="unsupported:missing",
    kind="artifact",
    id="missing",
    label="missing",
)


def _apply_freshness(
    connection: sqlite3.Connection,
    workspace_id: str,
    graph: FlowsheetGraphRead,
    evidence: list[BluecadEvidenceRefRead],
    runs: list[BluecadRunRefRead],
) -> list[str]:
    resolved_refs = {node.ref for node in graph.nodes}
    freshness_refs = ({item.ref for item in evidence} | {item.ref for item in runs}) & resolved_refs
    stale_by_ref = get_resolved_node_stale_states_from_connection(connection, workspace_id, freshness_refs)
    states: list[str] = []
    for item in evidence:
        if item.ref not in stale_by_ref:
            continue
        item.stale = stale_by_ref[item.ref]
        states.append("stale" if item.stale else "fresh")
    for item in runs:
        if item.ref not in stale_by_ref:
            continue
        item.stale = stale_by_ref[item.ref]
        states.append("stale" if item.stale else "fresh")
    return states


def _append_graph_diagnostics(
    graph: FlowsheetGraphRead,
    candidate: BluecadCandidateRead,
    artifact_ids: set[str],
    evidence: list[BluecadEvidenceRefRead],
    runs: list[BluecadRunRefRead],
    diagnostics: list[BluecadReadDiagnostic],
) -> None:
    subject_refs = {f"bluecad_candidate:{candidate.id}"}
    subject_refs.update(f"bluecad_attempt:{attempt.id}" for attempt in candidate.attempts)
    relevant_refs = set(subject_refs)
    relevant_refs.update(f"artifact:{artifact_id}" for artifact_id in artifact_ids)
    relevant_refs.update(item.ref for item in evidence)
    relevant_refs.update(item.ref for item in runs)
    if candidate.promoted_decision_id:
        relevant_refs.add(f"decision:{candidate.promoted_decision_id}")
    for item in graph.diagnostics.unresolved_references:
        raw_ref = item.raw_ref
        raw_subject_match = raw_ref is not None and any(
            raw_ref == subject_ref or raw_ref.startswith(f"{subject_ref}:") for subject_ref in subject_refs
        )
        if item.owner_ref not in relevant_refs and not raw_subject_match:
            continue
        code = _GRAPH_DIAGNOSTIC_MAP.get(item.code, "malformed_reference")
        diagnostics.append(
            BluecadReadDiagnostic(
                code=code,
                source=item.source_field,
                reference=raw_ref or item.owner_ref,
                message=f"Flowsheet reference could not be resolved ({item.code}).",
            )
        )


def _aggregate_freshness(states: list[str]) -> AggregateFreshness:
    unique = set(states)
    if unique == {"fresh"}:
        return "fresh"
    if unique == {"stale"}:
        return "stale"
    if unique == {"fresh", "stale"}:
        return "mixed"
    return "unknown"


def _dedupe_diagnostics(items: list[BluecadReadDiagnostic]) -> list[BluecadReadDiagnostic]:
    seen: set[tuple[str, str, str, str]] = set()
    result: list[BluecadReadDiagnostic] = []
    for item in items:
        key = (item.source, item.reference, item.code, item.message)
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result
