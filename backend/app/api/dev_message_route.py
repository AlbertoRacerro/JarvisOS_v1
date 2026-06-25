from uuid import uuid4

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from app.modules.dev_message_route.smoke_adapter import (
    MAX_MESSAGE_CHARS,
    dev_message_route_enabled,
    disabled_response,
    internal_error_response,
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


@router.post("/message-route-smoke")
async def run_dev_message_route_smoke_endpoint(request: Request) -> JSONResponse:
    trace_id = str(uuid4())

    if not dev_message_route_enabled():
        status_code, body = disabled_response(trace_id=trace_id)
        return JSONResponse(status_code=status_code, content=body)

    try:
        raw_body = await request.json()
    except Exception:
        body = validation_error_response(trace_id=trace_id, error_type="InvalidJSON")
        return JSONResponse(status_code=422, content=body)

    try:
        parsed = DevMessageRouteSmokeRequest.model_validate(raw_body)
    except ValidationError as exc:
        body = validation_error_response(
            trace_id=trace_id,
            error_type="ValidationError",
            validation_error_count=len(exc.errors()),
        )
        return JSONResponse(status_code=422, content=body)

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
