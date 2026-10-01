"""166: the one Jarvis-owned workspace-action executor (contract stub; lane A implements).

Callers: Hermes tool dispatch (origin local), Relay result ingestion (origin relay) and the
Sidecar HTTP routes (operator apply/dismiss/undo). Owners re-validate everything; no caller
mutates a draft or candidate directly.
"""
from __future__ import annotations

from app.modules.workspace_actions.models import ActionOrigin, ActionOutcome, ActionRequest, SurfaceBrief, SurfaceRef


class ActionError(RuntimeError):
    def __init__(self, code: str, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.code = code
        self.status_code = status_code


def surface_brief(workspace_id: str, ref: SurfaceRef | None) -> SurfaceBrief:
    """Owner-derived bounded brief for the route. ``surface='none'`` off Process/BLUECAD or without objects."""
    raise NotImplementedError


def submit(workspace_id: str, request: ActionRequest, origin: ActionOrigin) -> ActionOutcome:
    """Validate at ``base_revision`` (dry run), classify the tier, then apply or record a proposal.

    Never raises for model mistakes: invalid, unsupported or stale requests return a ``refused``
    or ``stale`` outcome with a plain-text reason so the agent can explain or retry.
    """
    raise NotImplementedError


def apply(workspace_id: str, action_id: str) -> ActionOutcome:
    """Operator approval of a ``proposed`` outcome; re-validated against the current head."""
    raise NotImplementedError


def dismiss(workspace_id: str, action_id: str) -> ActionOutcome:
    raise NotImplementedError


def undo(workspace_id: str, action_id: str) -> ActionOutcome:
    """Process: restore the parent revision if the head is still the action's result.
    BLUECAD: archive the child candidate."""
    raise NotImplementedError


def get(workspace_id: str, action_id: str) -> ActionOutcome:
    raise NotImplementedError


def list_for(workspace_id: str, *, thread_id: str, interaction_id: str | None = None,
             relay_run_id: str | None = None) -> list[ActionOutcome]:
    raise NotImplementedError
