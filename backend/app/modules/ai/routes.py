import json
import sqlite3

from fastapi import APIRouter, HTTPException

from app.modules.ai.context_builder import ContextSelectionSpec, build_workspace_context_bundle
from app.modules.ai.escalations import confirm_escalation
from app.modules.ai.gateway import AIGateway
from app.modules.ai.models import (
    AISettingsRead,
    AISettingsUpdate,
    AIStatusRead,
    AITaskRunRequest,
    AITaskRunResponse,
    ContextPackPreviewRequest,
    ContextPackPreviewResponse,
    EscalationConfirmRequest,
    EscalationConfirmResponse,
    ModelingDraftRequest,
    ModelingDraftResponse,
    ProviderSmokeRequest,
    ProviderSmokeResponse,
    SmokeConsoleRequest,
    SmokeConsoleResponse,
    SmokeTestRequest,
    SmokeTestResponse,
    SupervisorPublicTestRequest,
    SupervisorPublicTestResponse,
)
from app.modules.ai.settings import ensure_ai_settings, update_ai_settings

router = APIRouter(prefix="/ai", tags=["ai"])


@router.get("/settings", response_model=AISettingsRead)
def read_ai_settings() -> AISettingsRead:
    return ensure_ai_settings()


@router.put("/settings", response_model=AISettingsRead)
def update_ai_settings_endpoint(payload: AISettingsUpdate) -> AISettingsRead:
    return update_ai_settings(payload)


@router.get("/status", response_model=AIStatusRead)
def read_ai_status() -> AIStatusRead:
    ensure_ai_settings()
    return AIGateway().status()


@router.post("/modeling/draft", response_model=ModelingDraftResponse)
def create_modeling_draft(payload: ModelingDraftRequest) -> ModelingDraftResponse:
    ensure_ai_settings()
    return AIGateway().create_modeling_draft(payload)


@router.post("/tasks/run", response_model=AITaskRunResponse)
def run_ai_task_endpoint(payload: AITaskRunRequest) -> AITaskRunResponse:
    ensure_ai_settings()
    return AIGateway().run_task(payload)


@router.post("/context/packs/preview", response_model=ContextPackPreviewResponse)
def preview_context_pack(payload: ContextPackPreviewRequest) -> ContextPackPreviewResponse:
    selection = ContextSelectionSpec(**payload.selection.model_dump())
    try:
        bundle = build_workspace_context_bundle(
            payload.workspace_id, budget_chars=payload.budget_chars, selection=selection
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except sqlite3.IntegrityError as exc:
        raise HTTPException(status_code=400, detail="Related record was not found.") from exc
    char_count = len(json.dumps(bundle.blocks, sort_keys=True, separators=(",", ":"), ensure_ascii=False))
    return ContextPackPreviewResponse(
        blocks=bundle.blocks,
        context_digest=bundle.context_digest,
        context_sources_manifest=bundle.sources,
        char_count=char_count,
        estimated_token_count=char_count // 4,
        included_count=bundle.included_count,
        dropped_count=bundle.dropped_count,
        budget_chars=bundle.budget_chars,
    )


@router.post("/tasks/escalations/confirm", response_model=EscalationConfirmResponse)
def confirm_ai_task_escalation(payload: EscalationConfirmRequest) -> EscalationConfirmResponse:
    ensure_ai_settings()
    return confirm_escalation(payload)


@router.post("/smoke-tests/run", response_model=SmokeTestResponse)
def run_ai_smoke_tests(payload: SmokeTestRequest) -> SmokeTestResponse:
    ensure_ai_settings()
    return AIGateway().run_smoke_tests(payload)


@router.post("/smoke-console/run", response_model=SmokeConsoleResponse)
def run_ai_smoke_console(payload: SmokeConsoleRequest) -> SmokeConsoleResponse:
    ensure_ai_settings()
    return AIGateway().run_smoke_console(payload)


@router.post("/provider-smoke/run", response_model=ProviderSmokeResponse)
def run_ai_provider_smoke(payload: ProviderSmokeRequest) -> ProviderSmokeResponse:
    ensure_ai_settings()
    return AIGateway().run_provider_smoke(payload)


@router.post("/supervisor/public-test", response_model=SupervisorPublicTestResponse)
def run_ai_supervisor_public_test(payload: SupervisorPublicTestRequest) -> SupervisorPublicTestResponse:
    ensure_ai_settings()
    return AIGateway().run_supervisor_public_test(payload)
