from fastapi import APIRouter, HTTPException, Query

from app.modules.ai.thread_models import (
    AIThreadCreate,
    AIThreadDetail,
    AIThreadList,
    AIThreadSubmit,
    AIThreadSubmitRead,
    AIThreadSummary,
)
from app.modules.ai.thread_service import (
    AIThreadConflictError,
    AIThreadError,
    AIThreadNotFoundError,
    create_thread,
    get_thread,
    list_threads,
    submit_interaction,
)

router = APIRouter(prefix="/threads", tags=["ai-threads"])


@router.post("", response_model=AIThreadSummary)
def create_ai_thread(payload: AIThreadCreate) -> AIThreadSummary:
    try:
        return create_thread(payload)
    except AIThreadNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except AIThreadError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("", response_model=AIThreadList)
def list_ai_threads(
    workspace_id: str,
    limit: int = Query(default=25, ge=1, le=50),
) -> AIThreadList:
    try:
        return list_threads(workspace_id=workspace_id, limit=limit)
    except AIThreadNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except AIThreadError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/{thread_id}", response_model=AIThreadDetail)
def read_ai_thread(
    thread_id: str,
    workspace_id: str,
    interaction_limit: int = Query(default=50, ge=1, le=100),
) -> AIThreadDetail:
    try:
        return get_thread(
            workspace_id=workspace_id,
            thread_id=thread_id,
            interaction_limit=interaction_limit,
        )
    except AIThreadNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except AIThreadError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/{thread_id}/interactions", response_model=AIThreadSubmitRead)
def submit_ai_thread_interaction(
    thread_id: str,
    payload: AIThreadSubmit,
    workspace_id: str,
) -> AIThreadSubmitRead:
    try:
        return submit_interaction(
            workspace_id=workspace_id,
            thread_id=thread_id,
            payload=payload,
        )
    except AIThreadNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except AIThreadConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except AIThreadError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
