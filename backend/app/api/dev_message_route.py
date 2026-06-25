from uuid import uuid4

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.modules.dev_message_route.smoke_adapter import (
    MAX_MESSAGE_CHARS,
    internal_error_response,
    run_dev_message_route_smoke,
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
def run_dev_message_route_smoke_endpoint(payload: DevMessageRouteSmokeRequest) -> JSONResponse:
    try:
        status_code, body = run_dev_message_route_smoke(
            message=payload.message,
            run_local_responder=payload.run_local_responder,
        )
    except Exception as exc:
        body = internal_error_response(trace_id=str(uuid4()), error_type=type(exc).__name__)
        status_code = 500
    return JSONResponse(status_code=status_code, content=body)
