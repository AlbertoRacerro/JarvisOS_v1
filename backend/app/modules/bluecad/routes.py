"""Workspace-scoped BLUECAD candidate API routes."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.core.database import open_sqlite_connection
from app.core.paths import build_paths
from app.modules.bluecad.ledger import archive_candidate, get_candidate, list_candidates, mark_promoted
from app.modules.bluecad.loop import create_bluecad_candidate
from app.modules.bluecad.models import BluecadCandidateCreate, BluecadCandidateRead
from app.modules.modeling.models import DecisionCreate
from app.modules.modeling.service import create_decision

router = APIRouter(prefix="/workspaces/{workspace_id}/bluecad", tags=["bluecad"])


def _bluecad_artifact_path(workspace_id: str, artifact_id: str) -> tuple[Path, str]:
    with open_sqlite_connection() as connection:
        row = connection.execute(
            """
            SELECT stored_path, artifact_type, mime_type
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
    if artifact_type == "bluecad_glb":
        media_type = "model/gltf-binary"
    return stored_path, media_type


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


@router.get("/candidates", response_model=list[BluecadCandidateRead])
def list_candidates_endpoint(workspace_id: str) -> list[BluecadCandidateRead]:
    try:
        return list_candidates(workspace_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail={"error": str(exc)}) from exc


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
    candidate = archive_candidate(workspace_id, candidate_id)
    if candidate is None:
        raise HTTPException(status_code=404, detail={"error": "BLUECAD candidate not found."})
    return candidate


@router.get("/artifacts/{artifact_id}/content")
def get_bluecad_artifact_content(workspace_id: str, artifact_id: str) -> FileResponse:
    stored_path, media_type = _bluecad_artifact_path(workspace_id, artifact_id)
    return FileResponse(stored_path, media_type=media_type, filename=stored_path.name)
