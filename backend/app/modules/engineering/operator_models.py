"""Small operator read projections for engineering capability discovery."""

from typing import Literal

from pydantic import BaseModel


class EvaluatorRead(BaseModel):
    evaluator_id: str
    backend_kind: str | None
    backend_name: str | None
    backend_version: str | None
    fidelity: str | None
    state: str
    reason_code: str | None


class CapabilityRead(BaseModel):
    capability_id: str
    state: Literal["available", "unavailable", "not_configured"]
    reason_code: str | None

