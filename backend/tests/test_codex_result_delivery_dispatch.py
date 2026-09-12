from __future__ import annotations

import hashlib
import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "codex_result_delivery_dispatch.py"
SPEC = importlib.util.spec_from_file_location("codex_result_delivery_dispatch", SCRIPT)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = mod
SPEC.loader.exec_module(mod)


def _event(*, association: str = "OWNER", body: str | None = None, is_pr: bool = True) -> dict:
    payload = body or (
        f"{mod.CODEX_MARKER}\n"
        f"{mod.DELIVERY_MARKER}\n"
        "```json\n{}\n```\n"
        "```diff\nx\n```"
    )
    issue = {"number": 628}
    if is_pr:
        issue["pull_request"] = {"url": "https://api.github.test/pr/628"}
    return {
        "action": "created",
        "issue": issue,
        "comment": {
            "id": 12345,
            "author_association": association,
            "body": payload,
        },
    }


def test_owner_pr_comment_with_both_markers_is_bound_to_exact_body() -> None:
    event = _event()
    request = mod.request_from_event(event)
    assert request.pr == 628
    assert request.comment_id == 12345
    assert request.payload_body_sha256 == hashlib.sha256(
        event["comment"]["body"].encode("utf-8")
    ).hexdigest()


@pytest.mark.parametrize("association", ["MEMBER", "COLLABORATOR", "CONTRIBUTOR", "NONE"])
def test_non_owner_comment_is_refused(association: str) -> None:
    with pytest.raises(mod.DispatchError, match="not an admitted maintainer"):
        mod.request_from_event(_event(association=association))


def test_non_pr_comment_is_refused() -> None:
    with pytest.raises(mod.DispatchError, match="not attached to a pull request"):
        mod.request_from_event(_event(is_pr=False))


def test_missing_or_ambiguous_codex_marker_is_refused() -> None:
    body = f"{mod.DELIVERY_MARKER}\n```json\n{{}}\n```\n```diff\nx\n```"
    with pytest.raises(mod.DispatchError, match="exactly one Codex result marker"):
        mod.request_from_event(_event(body=body))
    with pytest.raises(mod.DispatchError, match="exactly one Codex result marker"):
        mod.request_from_event(
            _event(body=f"{mod.CODEX_MARKER}\n{mod.CODEX_MARKER}\n{mod.DELIVERY_MARKER}")
        )


def test_missing_or_ambiguous_cloud_marker_is_refused() -> None:
    with pytest.raises(mod.DispatchError, match="exactly one cloud delivery marker"):
        mod.request_from_event(_event(body=mod.CODEX_MARKER))
    with pytest.raises(mod.DispatchError, match="exactly one cloud delivery marker"):
        mod.request_from_event(
            _event(body=f"{mod.CODEX_MARKER}\n{mod.DELIVERY_MARKER}\n{mod.DELIVERY_MARKER}")
        )


def test_only_created_events_are_eligible() -> None:
    event = _event()
    event["action"] = "edited"
    with pytest.raises(mod.DispatchError, match="newly created"):
        mod.request_from_event(event)
