from __future__ import annotations

import hashlib
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
PAYLOAD_ID = 456
PAYLOAD_BODY = "<!-- jarvis-cloud-delivery:v1 -->\nimmutable payload bytes"
PAYLOAD_SHA256 = hashlib.sha256(PAYLOAD_BODY.encode("utf-8")).hexdigest()


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
        self.delivery_dispatches: list[mod.DeliveryRequest] = []
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

    def dispatch_delivery(self, delivery: mod.DeliveryRequest) -> None:
        self.delivery_dispatches.append(delivery)

    def record(self, number: int, body: str) -> None:
        self.recorded.append((number, body))


def comment(body: str, *, login: str, comment_id: int) -> dict:
    return {"id": comment_id, "body": body, "user": {"login": login}}


def bot_comment(body: str, *, comment_id: int = 900) -> dict:
    return comment(body, login="github-actions[bot]", comment_id=comment_id)


def owner_comment(body: str, *, comment_id: int = 901) -> dict:
    return comment(body, login="AlbertoRacerro", comment_id=comment_id)


def other_comment(body: str, *, comment_id: int = 902) -> dict:
    return comment(body, login="someone-else", comment_id=comment_id)


def payload_comment(*, body: str = PAYLOAD_BODY) -> dict:
    return comment(body, login="model-worker[bot]", comment_id=PAYLOAD_ID)


def delivery_request(
    *,
    head: str = HEAD,
    pr: int = 77,
    payload: int = PAYLOAD_ID,
    payload_sha256: str = PAYLOAD_SHA256,
) -> str:
    return (
        f"<!-- jarvis-cloud-delivery:dispatch:v1 pr={pr} head={head} "
        f"payload_comment_id={payload} payload_body_sha256={payload_sha256} -->"
    )


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
    assert client.delivery_dispatches == []


def test_owner_exact_head_and_payload_bytes_dispatch_fixed_cloud_bridge() -> None:
    comments = [payload_comment(), owner_comment(delivery_request())]
    client = FakeClient([pull(), pull()], comments)
    assert mod.run(event(), repository=REPOSITORY, client=client) == "dispatched"
    delivery = mod.DeliveryRequest(77, HEAD, PAYLOAD_ID, PAYLOAD_SHA256)
    assert client.delivery_dispatches == [delivery]
    assert client.dispatches == [(77, HEAD)]
    assert client.recorded[0] == (
        77,
        mod.delivery_marker_text(mod.WakeRequest("CI", 123, 2, 77, HEAD), delivery),
    )


def test_delivery_request_is_owner_exact_pr_head_and_payload_digest_bound() -> None:
    changed_body = PAYLOAD_BODY + " edited"
    comments = [
        payload_comment(body=changed_body),
        other_comment(delivery_request(), comment_id=910),
        owner_comment(delivery_request(pr=78), comment_id=911),
        owner_comment(delivery_request(head="b" * 40), comment_id=912),
        owner_comment("prefix " + delivery_request(), comment_id=913),
        owner_comment(delivery_request(), comment_id=914),
    ]
    assert (
        mod.requested_delivery(comments, repository=REPOSITORY, pr_number=77, head_sha=HEAD)
        is None
    )


def test_latest_valid_owner_delivery_request_wins() -> None:
    second_body = PAYLOAD_BODY + " second"
    second_sha = hashlib.sha256(second_body.encode("utf-8")).hexdigest()
    comments = [
        payload_comment(body=second_body),
        owner_comment(delivery_request(payload_sha256=PAYLOAD_SHA256), comment_id=920),
        owner_comment(delivery_request(payload_sha256=second_sha), comment_id=921),
    ]
    assert mod.requested_delivery(
        comments, repository=REPOSITORY, pr_number=77, head_sha=HEAD
    ) == mod.DeliveryRequest(77, HEAD, PAYLOAD_ID, second_sha)


def test_malformed_zero_payload_request_is_ignored_without_poisoning_valid_request() -> None:
    comments = [
        payload_comment(),
        owner_comment(delivery_request(payload=0), comment_id=922),
        owner_comment(delivery_request(), comment_id=923),
    ]
    assert mod.requested_delivery(
        comments, repository=REPOSITORY, pr_number=77, head_sha=HEAD
    ) == mod.DeliveryRequest(77, HEAD, PAYLOAD_ID, PAYLOAD_SHA256)


def test_auto_digest_is_valid_only_for_payload_unchanged_before_owner_attestation() -> None:
    payload = payload_comment()
    payload["updated_at"] = "2026-09-09T14:00:00Z"
    request = owner_comment(delivery_request(payload_sha256="auto"), comment_id=924)
    request["created_at"] = "2026-09-09T14:01:00Z"
    comments = [payload, request]
    assert mod.requested_delivery(
        comments, repository=REPOSITORY, pr_number=77, head_sha=HEAD
    ) == mod.DeliveryRequest(77, HEAD, PAYLOAD_ID, PAYLOAD_SHA256)

    payload["updated_at"] = "2026-09-09T14:02:00Z"
    assert (
        mod.requested_delivery(comments, repository=REPOSITORY, pr_number=77, head_sha=HEAD)
        is None
    )


def test_auto_digest_fails_closed_when_comment_timestamps_are_missing_or_equal() -> None:
    payload = payload_comment()
    request = owner_comment(delivery_request(payload_sha256="auto"), comment_id=925)
    assert (
        mod.requested_delivery([payload, request], repository=REPOSITORY, pr_number=77, head_sha=HEAD)
        is None
    )
    payload["updated_at"] = "2026-09-09T14:01:00Z"
    request["created_at"] = "2026-09-09T14:01:00Z"
    assert (
        mod.requested_delivery([payload, request], repository=REPOSITORY, pr_number=77, head_sha=HEAD)
        is None
    )


def test_missing_referenced_payload_comment_is_not_actionable() -> None:
    comments = [owner_comment(delivery_request())]
    assert (
        mod.requested_delivery(comments, repository=REPOSITORY, pr_number=77, head_sha=HEAD)
        is None
    )


def test_duplicate_delivery_dispatch_for_same_ci_attempt_is_collapsed() -> None:
    wake = mod.WakeRequest("CI", 123, 2, 77, HEAD)
    delivery = mod.DeliveryRequest(77, HEAD, PAYLOAD_ID, PAYLOAD_SHA256)
    comments = [
        payload_comment(),
        owner_comment(delivery_request()),
        bot_comment(mod.delivery_marker_text(wake, delivery)),
    ]
    client = FakeClient([pull(), pull()], comments)
    assert mod.run(event(), repository=REPOSITORY, client=client) == "dispatched"
    assert client.delivery_dispatches == []
    assert client.dispatches == [(77, HEAD)]


def test_stale_head_noops_before_dispatch() -> None:
    client = FakeClient([pull(head="b" * 40)])
    assert mod.run(event(), repository=REPOSITORY, client=client) == "noop:stale_head"
    assert client.dispatches == []
    assert client.delivery_dispatches == []
    assert client.recorded == []


def test_head_movement_between_validation_and_dispatch_noops() -> None:
    comments = [payload_comment(), owner_comment(delivery_request())]
    client = FakeClient([pull(), pull(head="b" * 40)], comments)
    assert mod.run(event(), repository=REPOSITORY, client=client) == "noop:stale_head"
    assert client.dispatches == []
    assert client.delivery_dispatches == []
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
