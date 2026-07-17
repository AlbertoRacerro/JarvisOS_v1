from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

ExecutionClass = Literal["synthetic", "local_compute", "external_provider"]


@dataclass(frozen=True)
class ProviderBinding:
    route_class: str
    provider_id: str
    model_id: str
    requires_network: bool
    max_output_tokens: int
    execution_class: ExecutionClass | None = None
    context_window_tokens: int | None = None
