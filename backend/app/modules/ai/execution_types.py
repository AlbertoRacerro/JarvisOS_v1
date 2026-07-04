from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProviderBinding:
    route_class: str
    provider_id: str
    model_id: str
    requires_network: bool
    max_output_tokens: int
