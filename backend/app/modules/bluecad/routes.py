"""Workspace-scoped BLUECAD candidate API routes."""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.core.database import open_sqlite_connection
from app.core.paths import build_paths
from app.modules.bluecad.cad_link import (
    CadLinkError,
    CadLinkExecuteRequest,
    CadLinkExecuteResponse,
    CadLinkPreviewRequest,
    execute_cad_link_047,
    preview_cad_link_047,
)
from app.modules.bluecad.cad_link_topology import (
    CadLink072ExecuteRequest,
    CadLink072PreviewRequest,
    preview_cad_link_072,
)
from app.modules.bluecad.cad_link_topology_execute import execute_cad_link_072
from app.modules.bluecad.ledger import archive_candidate, get_candidate, list_candidates, mark_promoted
from app.modules.bluecad.loop import _external_blocked_reason, create_bluecad_candidate
from app.modules.bluecad.models import BluecadCandidateCreate, BluecadCandidateRead
from app.modules.bluecad.read_model import BluecadCandidateAggregateRead, get_bluecad_candidate_aggregate
from app.modules.bluecad.template import BluecadTemplateCreate, TemplateError, create_template_candidate
from app.modules.modeling.models import DecisionCreate
from app.modules.modeling.service import create_decision

router = APIRouter(prefix="/workspaces/{workspace_id}/bluecad", tags=["bluecad"])

_EXPORT_MEDIA_TYPES = {"bluecad_stl": ("model/stl", ".stl"), "bluecad_step": ("model/step", ".step")}
_CANDIDATE_SOURCE_REF = re.compile(r"^bluecad_candidate:([0-9a-f-]{36}):attempt:(\d+)$")


def _bluecad_artifact_path(workspace_id: str, artifact_id: str) -> tuple[Path, str, str]:
    with open_sqlite_connection() as connection:
        row = connection.execute(
            """
            SELECT stored_path, artifact_type, mime_type, source_ref
            FROM artifacts
            WHERE id = ? AND workspace_id = ?
            """,
            (artifact_id, workspace_id),
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail={"error": "BLUECAD artifact not found."})

    artifact_type = str(row["artifact_type"] or "")
    if not artifact_type.startswith("bluecad_"):
        raise HTTPException(status_code=404, detail={"error": "BLUECAD artifact not found."})

    try:
        stored_path = Path(str(row["stored_path"])).resolve()
        data_root = build_paths().data_root.resolve()
        stored_path.relative_to(data_root)
    except (OSError, RuntimeError, ValueError):
        raise HTTPException(status_code=404, detail={"error": "BLUECAD artifact not found."}) from None

    if not stored_path.exists() or not stored_path.is_file():
        raise HTTPException(status_code=404, detail={"error": "BLUECAD artifact not found."})

    media_type = str(row["mime_type"] or "application/octet-stream")
    download_name = stored_path.name
    if artifact_type == "bluecad_glb":
        media_type = "model/gltf-binary"
    elif artifact_type in _EXPORT_MEDIA_TYPES:
        media_type, suffix = _EXPORT_MEDIA_TYPES[artifact_type]
        match = _CANDIDATE_SOURCE_REF.match(str(row["source_ref"] or ""))
        if match:
            download_name = f"bluecad-{match.group(1)[:8]}-attempt{match.group(2)}{suffix}"
    return stored_path, media_type, download_name


def _cad_link_error(exc: CadLinkError) -> HTTPException:
    return HTTPException(
        status_code=exc.status_code,
        detail={"code": exc.code, "message": exc.message},
    )


def _domain_error(exc: Exception) -> HTTPException:
    if isinstance(exc, ValueError):
        return HTTPException(status_code=400, detail={"error": str(exc)})
    if isinstance(exc, sqlite3.IntegrityError):
        return HTTPException(status_code=400, detail={"error": "Related record was not found."})
    return HTTPException(status_code=500, detail={"error": "Unexpected BLUECAD persistence error."})


@router.post("/candidates", response_model=BluecadCandidateRead, status_code=201)
def create_candidate_endpoint(workspace_id: str, payload: BluecadCandidateCreate) -> BluecadCandidateRead:
    try:
        return create_bluecad_candidate(workspace_id, payload)
    except (ValueError, sqlite3.IntegrityError) as exc:
        raise _domain_error(exc) from exc


@router.post("/candidates/from-template", response_model=BluecadCandidateRead, status_code=201)
def create_template_candidate_endpoint(workspace_id: str, payload: BluecadTemplateCreate) -> BluecadCandidateRead:
    try:
        return create_template_candidate(workspace_id, payload)
    except TemplateError as exc:
        raise HTTPException(status_code=exc.status_code, detail={"code": exc.code, "message": exc.message}) from exc


@router.get("/generation-availability")
def generation_availability_endpoint(workspace_id: str) -> dict[str, object]:
    """Report whether the AI loop's first external tier may run; makes no AI call."""
    blocked_reason = _external_blocked_reason()
    return {
        "route_class": "external:cheap",
        "external_calls_allowed": blocked_reason is None,
        "blocking_reason": blocked_reason,
    }


@router.post("/cad-link/047/preview")
def preview_cad_link_047_endpoint(
    workspace_id: str, payload: CadLinkPreviewRequest
) -> dict[str, object]:
    try:
        return preview_cad_link_047(workspace_id, payload)
    except CadLinkError as exc:
        raise _cad_link_error(exc) from exc


@router.post("/cad-link/047/execute", response_model=CadLinkExecuteResponse)
def execute_cad_link_047_endpoint(
    workspace_id: str, payload: CadLinkExecuteRequest
) -> CadLinkExecuteResponse:
    try:
        return execute_cad_link_047(workspace_id, payload)
    except CadLinkError as exc:
        raise _cad_link_error(exc) from exc


@router.post("/cad-link/072/preview")
def preview_cad_link_072_endpoint(
    workspace_id: str, payload: CadLink072PreviewRequest
) -> dict[str, object]:
    try:
        return preview_cad_link_072(workspace_id, payload)
    except CadLinkError as exc:
        raise _cad_link_error(exc) from exc


@router.post("/cad-link/072/execute", response_model=CadLinkExecuteResponse)
def execute_cad_link_072_endpoint(
    workspace_id: str, payload: CadLink072ExecuteRequest
) -> CadLinkExecuteResponse:
    try:
        return execute_cad_link_072(workspace_id, payload)
    except CadLinkError as exc:
        raise _cad_link_error(exc) from exc


@router.get("/candidates", response_model=list[BluecadCandidateRead])
def list_candidates_endpoint(workspace_id: str) -> list[BluecadCandidateRead]:
    try:
        return list_candidates(workspace_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail={"error": str(exc)}) from exc


@router.get("/candidates/{candidate_id}/aggregate", response_model=BluecadCandidateAggregateRead)
def get_candidate_aggregate_endpoint(workspace_id: str, candidate_id: str) -> BluecadCandidateAggregateRead:
    candidate = get_bluecad_candidate_aggregate(workspace_id, candidate_id)
    if candidate is None:
        raise HTTPException(status_code=404, detail={"error": "BLUECAD candidate not found."})
    return candidate


@router.get("/candidates/{candidate_id}", response_model=BluecadCandidateRead)
def get_candidate_endpoint(workspace_id: str, candidate_id: str) -> BluecadCandidateRead:
    candidate = get_candidate(workspace_id, candidate_id)
    if candidate is None:
        raise HTTPException(status_code=404, detail={"error": "BLUECAD candidate not found."})
    return candidate


@router.post("/candidates/{candidate_id}/promote", response_model=BluecadCandidateRead)
def promote_candidate_endpoint(workspace_id: str, candidate_id: str) -> BluecadCandidateRead:
    candidate = get_candidate(workspace_id, candidate_id)
    if candidate is None:
        raise HTTPException(status_code=404, detail={"error": "BLUECAD candidate not found."})
    if candidate.status != "valid":
        raise HTTPException(
            status_code=409,
            detail={"error": "Only valid BLUECAD candidates may be promoted.", "status": candidate.status},
        )
    decision = create_decision(
        workspace_id,
        DecisionCreate(
            title=f"Promote BLUECAD candidate {candidate.id}",
            decision_text="Promote validated BLUECAD GeometrySpec candidate.",
            rationale=f"BLUECAD candidate {candidate.id}; spec_artifact_id={candidate.spec_artifact_id}; report_artifact_id={candidate.report_artifact_id}; glb_artifact_id={candidate.glb_artifact_id}",
            notes="Created by human-triggered BLUECAD promote endpoint.",
        ),
    )
    return mark_promoted(workspace_id, candidate_id, decision.id)


@router.post("/candidates/{candidate_id}/archive", response_model=BluecadCandidateRead)
def archive_candidate_endpoint(workspace_id: str, candidate_id: str) -> BluecadCandidateRead:
    try:
        candidate = archive_candidate(workspace_id, candidate_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=409,
            detail={"error": str(exc)},
        ) from exc
    if candidate is None:
        raise HTTPException(status_code=404, detail={"error": "BLUECAD candidate not found."})
    return candidate


@router.get("/artifacts/{artifact_id}/content")
def get_bluecad_artifact_content(workspace_id: str, artifact_id: str) -> FileResponse:
    stored_path, media_type, download_name = _bluecad_artifact_path(workspace_id, artifact_id)
    return FileResponse(stored_path, media_type=media_type, filename=download_name)
