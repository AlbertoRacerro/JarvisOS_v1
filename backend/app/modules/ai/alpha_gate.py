"""Deterministic alpha-gate checks for runtime execution boundaries."""

from __future__ import annotations

from dataclasses import dataclass

from app.modules.ai.budget import evaluate_ai_status
from app.modules.ai.models import AISettingsRead


@dataclass(frozen=True)
class AlphaGateDecision:
    allowed: bool
    reason: str


def evaluate_alpha_execution_gate(
    *,
    settings: AISettingsRead | None,
    provider_mode: str | None,
    operation: str,
    side_effectful: bool,
) -> AlphaGateDecision:
    """Return whether a runtime operation may cross the alpha execution gate.

    The decision is based only on server-side settings/status supplied by the
    caller. Request-payload flags are intentionally not accepted here.
    """
    if not side_effectful:
        return AlphaGateDecision(True, "alpha_gate_safe_read_only")
    if settings is None:
        return AlphaGateDecision(False, f"alpha_gate_missing_context:{operation}")
    if not provider_mode:
        return AlphaGateDecision(False, f"alpha_gate_missing_provider_mode:{operation}")

    status = evaluate_ai_status(settings, provider_mode)
    if not status.external_calls_allowed:
        return AlphaGateDecision(False, status.blocking_reason or f"alpha_gate_closed:{operation}")
    return AlphaGateDecision(True, "alpha_gate_open")
