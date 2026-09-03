from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "event_driven_continuation.py"
SPEC = importlib.util.spec_from_file_location("event_driven_continuation", SCRIPT)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = mod
SPEC.loader.exec_module(mod)

DAILY_SCRIPT = ROOT / "scripts" / "daily_development_continuation.py"
DAILY_SPEC = importlib.util.spec_from_file_location(
    "daily_development_continuation_for_e1", DAILY_SCRIPT
)
assert DAILY_SPEC and DAILY_SPEC.loader
daily = importlib.util.module_from_spec(DAILY_SPEC)
sys.modules[DAILY_SPEC.name] = daily
DAILY_SPEC.loader.exec_module(daily)

REPOSITORY = "AlbertoRacerro/JarvisOS_v1"
HEAD = "a" * 40


def event(*, workflow: str = "CI", head: str = HEAD, pulls: list[dict] | None = None) -> dict:
    return {
        "workflow_run": {
            "name": workflow,
            "conclusion": "success",
            "id": 123,
            "run_attempt": 2,
            "head_sha": head,
            "pull_requests": [{"number": 77}] if pulls is None else pulls,
        }
    }


def pull(*, head: str = HEAD, state: str = "open", draft: bool = False) -> dict:
    return {
        "state": state,
        "draft": draft,
        "base": {"ref": "master"},
        "head": {"sha": head, "repo": {"full_name": REPOSITORY}},
    }


class FakeClient:
    def __init__(
        self,
        pulls: list[dict],
        comments: list[object] | None = None,
    ) -> None:
        self.pulls = list(pulls)
        self._comments = list(comments or [])
        self.dispatches: list[tuple[int, str]] = []
        self.recorded: list[tuple[int, str]] = []

    def pull(self, number: int) -> dict:
        assert number == 77
        if len(self.pulls) > 1:
            return self.pulls.pop(0)
        return self.pulls[0]

    def comments(self, number: int) -> list[object]:
        assert number == 77
        return self._comments

    def dispatch(self, pr_number: int, head_sha: str) -> None:
        self.dispatches.append((pr_number, head_sha))

    def record(self, number: int, body: str) -> None:
        self.recorded.append((number, body))


def bot_comment(body: str) -> dict:
    return {"body": body, "user": {"login": "github-actions[bot]"}}


def test_parse_terminal_ci_event() -> None:
    assert mod.parse_event(event()) == mod.WakeRequest("CI", 123, 2, 77, HEAD)


def test_non_pr_and_unrelated_workflow_noop() -> None:
    assert mod.parse_event(event(pulls=[])) is None
    assert mod.parse_event(event(workflow="Manual Expert Review")) is None
    assert mod.parse_event(event(workflow="Daily Development Continuation")) is None


def test_ci_dispatches_bound_exact_head() -> None:
    client = FakeClient([pull(), pull()])
    assert mod.run(event(), repository=REPOSITORY, client=client) == "dispatched"
    assert client.dispatches == [(77, HEAD)]


def test_stale_head_noops_before_dispatch() -> None:
    client = FakeClient([pull(head="b" * 40)])
    assert mod.run(event(), repository=REPOSITORY, client=client) == "noop:stale_head"
    assert client.dispatches == []
    assert client.recorded == []


def test_head_movement_between_validation_and_dispatch_noops() -> None:
    client = FakeClient([pull(), pull(head="b" * 40)])
    assert mod.run(event(), repository=REPOSITORY, client=client) == "noop:stale_head"
    assert client.dispatches == []
    assert client.recorded == []


def test_duplicate_exact_terminal_event_is_collapsed() -> None:
    request = mod.parse_event(event())
    assert request is not None
    client = FakeClient([pull()], [bot_comment(mod.marker_text(request))])
    assert mod.run(event(), repository=REPOSITORY, client=client) == "noop:duplicate"
    assert client.dispatches == []


def test_same_run_new_attempt_is_not_duplicate() -> None:
    previous = mod.WakeRequest("CI", 123, 1, 77, HEAD)
    client = FakeClient([pull(), pull()], [bot_comment(mod.marker_text(previous))])
    assert mod.run(event(), repository=REPOSITORY, client=client) == "dispatched"
    assert client.dispatches == [(77, HEAD)]
    assert client.recorded == [(77, mod.marker_text(mod.WakeRequest("CI", 123, 2, 77, HEAD)))]


def test_dispatch_preserves_validated_pr_and_exact_head() -> None:
    client = FakeClient([pull(), pull()])
    assert mod.run(event(), repository=REPOSITORY, client=client) == "dispatched"
    assert client.dispatches == [(77, HEAD)]
    assert len(client.recorded) == 1


def test_malformed_exact_head_fails_closed() -> None:
    with pytest.raises(mod.WakeError, match="exact head"):
        mod.parse_event(event(head="not-a-sha"))


@pytest.mark.parametrize(
    "path",
    [
        "scripts/event_bound_continuation_plan.py",
        "scripts/event_driven_continuation.py",
        "backend/tests/test_event_bound_continuation_plan.py",
        "backend/tests/test_event_driven_continuation.py",
    ],
)
def test_e1_control_paths_are_immutable_under_spec_079(path: str) -> None:
    with pytest.raises(daily.ContinuationError, match="protected path"):
        daily.validate_changed_paths([path], "079")
