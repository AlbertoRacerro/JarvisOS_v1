from fastapi import APIRouter

from app.modules.ai.gateway import AIGateway
from app.modules.ai.models import (
    AISettingsRead,
    AISettingsUpdate,
    AIStatusRead,
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
