import sqlite3

from fastapi import APIRouter, HTTPException, Query

from app.modules.memory.models import MemoryProposalCreate, MemoryRecordKind, MemoryRecordRead, MemoryStatus
from app.modules.memory.service import create_proposal, list_proposals, promote_record, reject_record

router = APIRouter(prefix="/memory", tags=["memory"])


def _domain_error(exc: Exception) -> HTTPException:
    if isinstance(exc, ValueError):
        message = str(exc)
        status_code = 404 if "not found" in message.lower() else 400
        return HTTPException(status_code=status_code, detail=message)
    if isinstance(exc, sqlite3.IntegrityError):
        return HTTPException(status_code=400, detail="Related record was not found.")
    return HTTPException(status_code=500, detail="Unexpected persistence error.")


@router.post("/proposals", response_model=MemoryRecordRead, status_code=201)
def create_memory_proposal_endpoint(payload: MemoryProposalCreate) -> MemoryRecordRead:
    try:
        return create_proposal(payload)
    except (ValueError, sqlite3.IntegrityError) as exc:
        raise _domain_error(exc) from exc


@router.get("/proposals", response_model=list[MemoryRecordRead])
def list_memory_proposals_endpoint(
    workspace_id: str = Query(min_length=1),
    status: MemoryStatus | None = None,
) -> list[MemoryRecordRead]:
    try:
        return list_proposals(workspace_id, status)
    except ValueError as exc:
        raise _domain_error(exc) from exc


@router.post("/{record_kind}/{record_id}/promote", response_model=MemoryRecordRead)
def promote_memory_record_endpoint(record_kind: MemoryRecordKind, record_id: str) -> MemoryRecordRead:
    try:
        return promote_record(record_kind, record_id)
    except (ValueError, sqlite3.IntegrityError) as exc:
        raise _domain_error(exc) from exc


@router.post("/{record_kind}/{record_id}/reject", response_model=MemoryRecordRead)
def reject_memory_record_endpoint(record_kind: MemoryRecordKind, record_id: str) -> MemoryRecordRead:
    try:
        return reject_record(record_kind, record_id)
    except (ValueError, sqlite3.IntegrityError) as exc:
        raise _domain_error(exc) from exc
