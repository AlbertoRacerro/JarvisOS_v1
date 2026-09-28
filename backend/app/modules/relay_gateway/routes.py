from fastapi import APIRouter, HTTPException

from app.modules.relay_gateway.service import (
    ContextReleaseCreate,
    ContextReleaseRead,
    RelayGatewayError,
    RelayRunRead,
    RelayRunRequest,
    RelayStatusRead,
    create_context_release,
    get_relay_run,
    list_context_releases,
    list_relay_runs,
    relay_status,
    revoke_context_release,
    submit_relay_run,
)

router = APIRouter(prefix="/ai", tags=["relay-gateway"])


@router.get("/relay/status", response_model=RelayStatusRead)
def read_relay_status() -> RelayStatusRead:
    return relay_status()


@router.post("/threads/{thread_id}/relay-runs", response_model=RelayRunRead)
def submit_thread_relay_run(thread_id: str, workspace_id: str, payload: RelayRunRequest) -> RelayRunRead:
    try:
        return submit_relay_run(workspace_id, thread_id, payload)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RelayGatewayError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/threads/{thread_id}/relay-runs", response_model=list[RelayRunRead])
def read_thread_relay_runs(thread_id: str, workspace_id: str) -> list[RelayRunRead]:
    return list_relay_runs(workspace_id, thread_id)


@router.get("/threads/{thread_id}/relay-runs/{run_id}", response_model=RelayRunRead)
def read_thread_relay_run(thread_id: str, run_id: str, workspace_id: str) -> RelayRunRead:
    try:
        return get_relay_run(workspace_id, thread_id, run_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/relay/context-releases", response_model=ContextReleaseRead, status_code=201)
def release_relay_context(workspace_id: str, payload: ContextReleaseCreate) -> ContextReleaseRead:
    try:
        return create_context_release(workspace_id, payload)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RelayGatewayError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/relay/context-releases", response_model=list[ContextReleaseRead])
def read_relay_context_releases(workspace_id: str) -> list[ContextReleaseRead]:
    return list_context_releases(workspace_id)


@router.post("/relay/context-releases/{release_id}/revoke", response_model=ContextReleaseRead)
def revoke_relay_context(release_id: str, workspace_id: str, reason: str) -> ContextReleaseRead:
    try:
        return revoke_context_release(workspace_id, release_id, reason)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
