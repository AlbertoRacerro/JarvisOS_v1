from fastapi import APIRouter, HTTPException, Query, Request

from app.modules.ai.thread_models import (
    AIConversationOptions,
    AIConversationRoute,
    AIConversationRouteAvailability,
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


@router.get("/conversation-options", response_model=AIConversationOptions)
def read_conversation_options() -> AIConversationOptions:
    """Project local route availability without dispatching or exposing configuration."""
    from app.modules.ai.provider_registry import registry_bindings

    try:
        bindings = registry_bindings()
    except (OSError, ValueError):
        return AIConversationOptions(routes=[], availability="unavailable")
    routes: list[AIConversationRoute] = []
    probes = {"local_ollama": _ollama_route_availability}
    for route, label in (
        ("local:general", "Local assistant"),
        ("local:fast", "Local fast assistant"),
        ("local:coder", "Local coding assistant"),
        ("local:fake", "Test responder (synthetic)"),
    ):
        binding = bindings.get(route)
        if not binding or binding.requires_network or binding.execution_class not in {"local_compute", "synthetic"}:
            continue
        if binding.execution_class == "synthetic":
            availability = AIConversationRouteAvailability(
                configured=True, runtime_reachable=None, model_installed=None, model_loaded=None,
                qualified="unknown", reason_code="TEST_ONLY", message="Synthetic test responder; not a real model.",
            )
        else:
            probe = probes.get(binding.provider_id)
            try:
                availability = probe(route, binding.model_id) if probe else AIConversationRouteAvailability(
                    configured=True, runtime_reachable=None, model_installed=None, model_loaded=None,
                    qualified="unknown", reason_code="AVAILABILITY_UNSUPPORTED",
                    message="This local runtime does not report availability yet.",
                )
            except Exception:
                availability = AIConversationRouteAvailability(
                    configured=True, runtime_reachable=None, model_installed=None, model_loaded=None,
                    qualified="unknown", reason_code="AVAILABILITY_PROBE_FAILED",
                    message="Local model availability could not be checked.",
                )
        routes.append(AIConversationRoute(
            route_class=route, label=label, model_id=binding.model_id,
            execution_class=binding.execution_class, availability=availability,
        ))
    return AIConversationOptions(routes=routes, availability="configured" if routes else "unavailable")


def _ollama_route_availability(route: str, model_id: str) -> AIConversationRouteAvailability:
    from app.modules.local_ai.runtime.status import get_local_ai_runtime_status

    status = get_local_ai_runtime_status()
    reachable = bool(status.get("ollama_reachable"))
    installed: bool | None = None
    loaded: bool | None = None
    if reachable and not status.get("tags_error_type"):
        installed_names = set(status.get("installed_models", []))
        installed = model_id in installed_names
        loaded_names = {
            item.get("name") for item in status.get("loaded_models", []) if isinstance(item, dict)
        }
        if not status.get("ps_error_type"):
            loaded = model_id in loaded_names
    reason = None
    message = "Local model is available."
    if not reachable:
        reason, message = "RUNTIME_UNREACHABLE", "Ollama is not reachable; start the configured local runtime."
    elif installed is False:
        reason, message = "MODEL_NOT_INSTALLED", f"{model_id} is not installed in Ollama."
    elif installed is None:
        reason, message = "MODEL_STATUS_UNKNOWN", "Ollama responds, but installed model status is unavailable."
    return AIConversationRouteAvailability(
        configured=True,
        runtime_reachable=reachable,
        model_installed=installed,
        model_loaded=loaded,
        qualified="unknown",
        reason_code=reason,
        message=message,
    )


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
    request: Request,
) -> AIThreadSubmitRead:
    try:
        return submit_interaction(
            workspace_id=workspace_id,
            thread_id=thread_id,
            payload=payload,
            app_state=request.app.state,
            route_availability=[route.model_dump() for route in read_conversation_options().routes],
        )
    except AIThreadNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except AIThreadConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except AIThreadError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
