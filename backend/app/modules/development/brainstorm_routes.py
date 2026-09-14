from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.core.errors import WORKSPACE_NOT_FOUND_CODE, workspace_not_found_http_error
from app.modules.development.brainstorm_models import (
    BrainstormDiscussionRecord,
    BrainstormPromotionCreate,
    BrainstormRawCreate,
    BrainstormReconcileCreate,
    BrainstormSupersedeRequest,
)
from app.modules.development.brainstorm_service import (
    create_promotion,
    create_raw,
    get_idea,
    list_ideas,
    list_promotions,
    list_raw,
    reconcile,
    record_discussion,
    supersede,
)
from app.modules.development.service import DevelopmentError

router = APIRouter(prefix="/development/brainstorm", tags=["development-brainstorm"])


def _http_error(exc: DevelopmentError) -> HTTPException:
    if exc.code == WORKSPACE_NOT_FOUND_CODE:
        return workspace_not_found_http_error()
    missing = {
        "brainstorm_raw_not_found",
        "brainstorm_idea_not_found",
        "brainstorm_revision_not_found",
        "brainstorm_ref_not_found",
        "brainstorm_promotion_not_found",
    }
    conflict = {
        "brainstorm_idempotency_mismatch",
        "brainstorm_idea_stale",
        "brainstorm_successor_stale",
        "brainstorm_idea_superseded",
        "brainstorm_lineage_self",
        "brainstorm_lineage_cycle",
        "brainstorm_promotion_stale",
        "brainstorm_promotion_superseded",
    }
    status_code = 404 if exc.code in missing else 409 if exc.code in conflict else 400
    return HTTPException(status_code=status_code, detail={"code": exc.code, "message": exc.message})


@router.post("/raw", status_code=201)
def create_raw_endpoint(payload: BrainstormRawCreate) -> dict[str, object]:
    try:
        return create_raw(payload)
    except DevelopmentError as exc:
        raise _http_error(exc) from exc


@router.get("/raw")
def list_raw_endpoint(workspace_id: str = Query(min_length=1)) -> list[dict[str, object]]:
    try:
        return list_raw(workspace_id)
    except DevelopmentError as exc:
        raise _http_error(exc) from exc


@router.post("/discussions", status_code=201)
def record_discussion_endpoint(payload: BrainstormDiscussionRecord) -> dict[str, object]:
    try:
        return record_discussion(payload)
    except DevelopmentError as exc:
        raise _http_error(exc) from exc


@router.post("/ideas/reconcile", status_code=201)
def reconcile_endpoint(payload: BrainstormReconcileCreate) -> dict[str, object]:
    try:
        return reconcile(payload)
    except DevelopmentError as exc:
        raise _http_error(exc) from exc


@router.get("/ideas")
def list_ideas_endpoint(workspace_id: str = Query(min_length=1)) -> list[dict[str, object]]:
    try:
        return list_ideas(workspace_id)
    except DevelopmentError as exc:
        raise _http_error(exc) from exc


@router.get("/ideas/{idea_id}")
def get_idea_endpoint(idea_id: str, workspace_id: str = Query(min_length=1)) -> dict[str, object]:
    try:
        return get_idea(workspace_id, idea_id)
    except DevelopmentError as exc:
        raise _http_error(exc) from exc


@router.post("/ideas/{idea_id}/supersede")
def supersede_endpoint(idea_id: str, payload: BrainstormSupersedeRequest) -> dict[str, object]:
    if payload.idea_id != idea_id:
        raise HTTPException(
            status_code=400,
            detail={"code": "brainstorm_idea_mismatch", "message": "Path and payload idea identities must match."},
        )
    try:
        return supersede(payload)
    except DevelopmentError as exc:
        raise _http_error(exc) from exc


@router.post("/promotions", status_code=201)
def create_promotion_endpoint(payload: BrainstormPromotionCreate) -> dict[str, object]:
    try:
        return create_promotion(payload)
    except DevelopmentError as exc:
        raise _http_error(exc) from exc


@router.get("/promotions")
def list_promotions_endpoint(
    workspace_id: str = Query(min_length=1), idea_id: str | None = Query(default=None)
) -> list[dict[str, object]]:
    try:
        return list_promotions(workspace_id, idea_id)
    except DevelopmentError as exc:
        raise _http_error(exc) from exc
