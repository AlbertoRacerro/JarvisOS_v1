"""Synchronous BLUECAD AI loop entry points.

Stage 1 intentionally implements only fail-closed candidate creation under the
existing external-call safety gates. Stage 2 adds provider orchestration,
build/validate repair attempts, and artifact promotion.
"""

from __future__ import annotations

from app.modules.ai.budget import evaluate_ai_status
from app.modules.ai.settings import get_ai_settings
from app.modules.bluecad.ledger import create_candidate_record, park_candidate
from app.modules.bluecad.models import BluecadCandidateCreate, BluecadCandidateRead, BluecadLoopConfig


def create_bluecad_candidate(workspace_id: str, payload: BluecadCandidateCreate) -> BluecadCandidateRead:
    loop_config = payload.loop_config or BluecadLoopConfig()
    _validate_loop_config(loop_config)
    candidate = create_candidate_record(workspace_id, payload.brief_text, loop_config)

    status = evaluate_ai_status(get_ai_settings(), "scaleway")
    if not status.external_calls_allowed:
        blocked_reason = status.blocking_reason or "external_calls_blocked"
        park_candidate(candidate.id, "budget_blocked", notes=f"external_blocked_reason={blocked_reason}")
        from app.modules.bluecad.ledger import get_candidate

        parked = get_candidate(workspace_id, candidate.id)
        if parked is None:  # pragma: no cover - defensive persistence guard
            raise RuntimeError("BLUECAD candidate disappeared after parking")
        return parked

    # Stage 1 stop point: do not call providers before review. Paid/external-enabled
    # environments park instead of spending until Stage 2 orchestration lands.
    park_candidate(candidate.id, "policy_blocked", notes="stage1_loop_orchestration_pending")
    from app.modules.bluecad.ledger import get_candidate

    parked = get_candidate(workspace_id, candidate.id)
    if parked is None:  # pragma: no cover
        raise RuntimeError("BLUECAD candidate disappeared after stage1 parking")
    return parked


def _validate_loop_config(loop_config: BluecadLoopConfig) -> None:
    if not loop_config.tier_ladder:
        raise ValueError("tier_ladder must not be empty")
    for route_class in loop_config.tier_ladder:
        if route_class not in {"external:cheap", "external:reasoning"}:
            raise ValueError("BLUECAD loop route classes must be explicit external tiers")
