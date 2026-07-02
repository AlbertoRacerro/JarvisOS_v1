from uuid import uuid4

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from app.modules.dev_message_route.smoke_adapter import (
    MAX_HISTORY_TURN_CHARS,
    MAX_HISTORY_TURNS,
    MAX_MESSAGE_CHARS,
    dev_message_route_enabled,
    disabled_response,
    internal_error_response,
    run_dev_local_chat,
    run_dev_message_route_smoke,
    validation_error_response,
)

router = APIRouter(prefix="/api/dev", tags=["dev"])


class DevMessageRouteSmokeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str = Field(min_length=1, max_length=MAX_MESSAGE_CHARS)
    run_local_responder: bool = False

    @field_validator("message")
    @classmethod
    def message_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("message must not be blank")
        return value


class DevLocalChatHistoryTurn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: str
    content: str = Field(min_length=1, max_length=MAX_HISTORY_TURN_CHARS)

    @field_validator("role")
    @classmethod
    def role_must_be_supported(cls, value: str) -> str:
        if value not in {"user", "assistant"}:
            raise ValueError("role must be user or assistant")
        return value

    @field_validator("content")
    @classmethod
    def content_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("content must not be blank")
        return value


class DevLocalChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str = Field(min_length=1, max_length=MAX_MESSAGE_CHARS)
    history: list[DevLocalChatHistoryTurn] = Field(default_factory=list, max_length=MAX_HISTORY_TURNS)
    run_local_responder: bool = True

    @field_validator("message")
    @classmethod
    def message_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("message must not be blank")
        return value


async def _read_validated_body(
    request: Request,
    *,
    trace_id: str,
    model: type[BaseModel],
) -> tuple[JSONResponse | None, BaseModel | None]:
    try:
        raw_body = await request.json()
    except Exception:
        body = validation_error_response(trace_id=trace_id, error_type="InvalidJSON")
        return JSONResponse(status_code=422, content=body), None

    try:
        return None, model.model_validate(raw_body)
    except ValidationError as exc:
        body = validation_error_response(
            trace_id=trace_id,
            error_type="ValidationError",
            validation_error_count=len(exc.errors()),
        )
        return JSONResponse(status_code=422, content=body), None


@router.post("/message-route-smoke")
async def run_dev_message_route_smoke_endpoint(request: Request) -> JSONResponse:
    trace_id = str(uuid4())

    if not dev_message_route_enabled():
        status_code, body = disabled_response(trace_id=trace_id)
        return JSONResponse(status_code=status_code, content=body)

    validation_response, parsed = await _read_validated_body(
        request,
        trace_id=trace_id,
        model=DevMessageRouteSmokeRequest,
    )
    if validation_response is not None:
        return validation_response
    assert isinstance(parsed, DevMessageRouteSmokeRequest)

    try:
        status_code, body = run_dev_message_route_smoke(
            message=parsed.message,
            run_local_responder=parsed.run_local_responder,
            trace_id=trace_id,
        )
    except Exception as exc:
        body = internal_error_response(trace_id=trace_id, error_type=type(exc).__name__)
        status_code = 500
    return JSONResponse(status_code=status_code, content=body)


@router.post("/local-chat")
async def run_dev_local_chat_endpoint(request: Request) -> JSONResponse:
    trace_id = str(uuid4())

    if not dev_message_route_enabled():
        status_code, body = disabled_response(trace_id=trace_id)
        return JSONResponse(status_code=status_code, content=body)

    validation_response, parsed = await _read_validated_body(
        request,
        trace_id=trace_id,
        model=DevLocalChatRequest,
    )
    if validation_response is not None:
        return validation_response
    assert isinstance(parsed, DevLocalChatRequest)

    try:
        status_code, body = run_dev_local_chat(
            message=parsed.message,
            history=[turn.model_dump() for turn in parsed.history],
            run_local_responder=parsed.run_local_responder,
            trace_id=trace_id,
        )
    except Exception as exc:
        body = internal_error_response(trace_id=trace_id, error_type=type(exc).__name__)
        status_code = 500
    return JSONResponse(status_code=status_code, content=body)
