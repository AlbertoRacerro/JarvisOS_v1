from __future__ import annotations

from copy import deepcopy

import pytest

from scripts.router_policy_external_budget_gate import evaluate_external_budget_gate


NOW = 1_710_003_600
STARTED = 1_710_000_000


def valid_request(**overrides):
    data = {
        "request_text_bytes": 12_000,
        "estimated_input_tokens": 4_000,
        "requested_max_output_tokens": 2_000,
    }
    data.update(overrides)
    return data


def valid_session(**overrides):
    data = {
        "session_calls_used": 0,
        "session_estimated_tokens_used": 0,
        "session_started_at": STARTED,
    }
    data.update(overrides)
    return data


def valid_policy(**overrides):
    data = {
        "external_budget_enabled": True,
        "max_input_bytes": 12_000,
        "max_estimated_input_tokens": 4_000,
        "max_output_tokens": 2_000,
        "max_session_estimated_tokens": 30_000,
        "max_calls_per_session": 5,
        "max_session_ttl_seconds": 3_600,
        "bytes_per_token": 3,
    }
    data.update(overrides)
    return data


def assert_denied_with(decision, code):
    assert decision["allowed"] is False
    assert code in decision["reason_codes"]


def test_e3_allowed_path_returns_remaining_budget_and_next_usage():
    decision = evaluate_external_budget_gate(
        valid_request(),
        valid_session(),
        valid_policy(),
        NOW,
    )

    assert decision["allowed"] is True
    assert decision["reason_codes"] == []
    assert decision["estimated_input_tokens"] == 4_000
    assert decision["estimated_request_tokens"] == 6_000
    assert decision["approved_max_output_tokens"] == 2_000
    assert decision["remaining_calls"] == 4
    assert decision["remaining_session_tokens"] == 24_000
    assert decision["next_session_usage"] == {
        "session_calls_used": 1,
        "session_estimated_tokens_used": 6_000,
        "session_started_at": STARTED,
    }


@pytest.mark.parametrize("bad_policy", [None, [], "policy"])
def test_e3_policy_not_dict_denies_cleanly(bad_policy):
    decision = evaluate_external_budget_gate(
        valid_request(),
        valid_session(),
        bad_policy,
        NOW,
    )
    assert_denied_with(decision, "budget_policy_not_dict")


@pytest.mark.parametrize("bad_request", [None, [], "request"])
def test_e3_request_not_dict_denies_cleanly_and_skips_fields(bad_request):
    decision = evaluate_external_budget_gate(
        bad_request,
        valid_session(),
        valid_policy(),
        NOW,
    )
    assert_denied_with(decision, "request_not_dict")
    assert "request_text_bytes_missing" not in decision["reason_codes"]


@pytest.mark.parametrize("bad_session", [None, [], "session"])
def test_e3_session_not_dict_denies_cleanly_and_skips_fields(bad_session):
    decision = evaluate_external_budget_gate(
        valid_request(),
        bad_session,
        valid_policy(),
        NOW,
    )
    assert_denied_with(decision, "session_usage_not_dict")
    assert "session_calls_used_missing" not in decision["reason_codes"]


@pytest.mark.parametrize("value", [False, None, 1, "true", "yes", [], {}])
def test_e3_external_budget_enabled_must_be_exactly_true(value):
    decision = evaluate_external_budget_gate(
        valid_request(),
        valid_session(),
        valid_policy(external_budget_enabled=value),
        NOW,
    )
    assert_denied_with(decision, "external_budget_disabled")


@pytest.mark.parametrize(
    "cap",
    [
        "max_input_bytes",
        "max_estimated_input_tokens",
        "max_output_tokens",
        "max_session_estimated_tokens",
        "max_calls_per_session",
        "max_session_ttl_seconds",
    ],
)
def test_e3_missing_required_policy_cap_denies(cap):
    policy = valid_policy()
    policy.pop(cap)
    decision = evaluate_external_budget_gate(
        valid_request(),
        valid_session(),
        policy,
        NOW,
    )
    assert_denied_with(decision, "policy_required_cap_missing")


@pytest.mark.parametrize("bad_value", [0, -1, True, 1.5, "100"])
def test_e3_invalid_policy_cap_denies(bad_value):
    decision = evaluate_external_budget_gate(
        valid_request(),
        valid_session(),
        valid_policy(max_input_bytes=bad_value),
        NOW,
    )
    assert_denied_with(decision, "policy_required_cap_invalid")


@pytest.mark.parametrize("bad_value", [0, -1, True, 1.5, "3"])
def test_e3_invalid_bytes_per_token_denies_when_provided(bad_value):
    decision = evaluate_external_budget_gate(
        valid_request(),
        valid_session(),
        valid_policy(bytes_per_token=bad_value),
        NOW,
    )
    assert_denied_with(decision, "bytes_per_token_invalid")


def test_e3_missing_bytes_per_token_uses_default():
    policy = valid_policy()
    policy.pop("bytes_per_token")
    decision = evaluate_external_budget_gate(
        valid_request(estimated_input_tokens=None),
        valid_session(),
        policy,
        NOW,
    )
    assert decision["allowed"] is True
    assert decision["estimated_input_tokens"] == 4_000


def test_e3_policy_session_cap_must_allow_one_max_request():
    decision = evaluate_external_budget_gate(
        valid_request(),
        valid_session(),
        valid_policy(max_session_estimated_tokens=5_999),
        NOW,
    )
    assert_denied_with(decision, "policy_session_token_cap_incoherent")


@pytest.mark.parametrize("bad_value", [None, 0, -1, True, 1.5, "12000"])
def test_e3_invalid_request_text_bytes_denies(bad_value):
    request = valid_request(request_text_bytes=bad_value)
    decision = evaluate_external_budget_gate(
        request,
        valid_session(),
        valid_policy(),
        NOW,
    )
    assert_denied_with(decision, "request_text_bytes_invalid")


def test_e3_missing_request_text_bytes_denies():
    request = valid_request()
    request.pop("request_text_bytes")
    decision = evaluate_external_budget_gate(
        request,
        valid_session(),
        valid_policy(),
        NOW,
    )
    assert_denied_with(decision, "request_text_bytes_missing")


def test_e3_request_text_bytes_over_cap_denies():
    decision = evaluate_external_budget_gate(
        valid_request(request_text_bytes=12_001),
        valid_session(),
        valid_policy(),
        NOW,
    )
    assert_denied_with(decision, "request_text_bytes_exceed_cap")


def test_e3_none_estimated_input_tokens_derives_from_bytes():
    decision = evaluate_external_budget_gate(
        valid_request(estimated_input_tokens=None),
        valid_session(),
        valid_policy(),
        NOW,
    )
    assert decision["allowed"] is True
    assert decision["estimated_input_tokens"] == 4_000


def test_e3_absent_estimated_input_tokens_derives_from_bytes():
    request = valid_request()
    request.pop("estimated_input_tokens")
    decision = evaluate_external_budget_gate(
        request,
        valid_session(),
        valid_policy(),
        NOW,
    )
    assert decision["allowed"] is True
    assert decision["estimated_input_tokens"] == 4_000


def test_e3_estimated_input_tokens_below_derived_uses_derived():
    decision = evaluate_external_budget_gate(
        valid_request(estimated_input_tokens=1),
        valid_session(),
        valid_policy(),
        NOW,
    )
    assert decision["allowed"] is True
    assert decision["estimated_input_tokens"] == 4_000


@pytest.mark.parametrize("bad_value", [-1, True, 1.5, "1000"])
def test_e3_invalid_estimated_input_tokens_denies_and_skips_arithmetic(bad_value):
    decision = evaluate_external_budget_gate(
        valid_request(estimated_input_tokens=bad_value),
        valid_session(),
        valid_policy(),
        NOW,
    )
    assert_denied_with(decision, "estimated_input_tokens_invalid")
    assert decision["estimated_input_tokens"] is None
    assert decision["estimated_request_tokens"] is None
    assert "session_token_budget_exceeded" not in decision["reason_codes"]


def test_e3_final_estimated_input_tokens_over_cap_denies():
    decision = evaluate_external_budget_gate(
        valid_request(estimated_input_tokens=4_001),
        valid_session(),
        valid_policy(),
        NOW,
    )
    assert_denied_with(decision, "estimated_input_tokens_exceed_cap")


@pytest.mark.parametrize("bad_value", [None, 0, -1, True, 1.5, "2000"])
def test_e3_invalid_requested_output_tokens_denies_and_skips_request_total(bad_value):
    decision = evaluate_external_budget_gate(
        valid_request(requested_max_output_tokens=bad_value),
        valid_session(),
        valid_policy(),
        NOW,
    )
    assert_denied_with(decision, "requested_output_tokens_invalid")
    assert decision["estimated_request_tokens"] is None


def test_e3_missing_requested_output_tokens_denies():
    request = valid_request()
    request.pop("requested_max_output_tokens")
    decision = evaluate_external_budget_gate(
        request,
        valid_session(),
        valid_policy(),
        NOW,
    )
    assert_denied_with(decision, "requested_output_tokens_missing")


def test_e3_requested_output_tokens_over_cap_denies_not_clamp():
    decision = evaluate_external_budget_gate(
        valid_request(requested_max_output_tokens=2_001),
        valid_session(),
        valid_policy(),
        NOW,
    )
    assert_denied_with(decision, "requested_output_tokens_exceed_cap")
    assert decision["approved_max_output_tokens"] is None


def test_e3_session_token_budget_exceeded_denies():
    decision = evaluate_external_budget_gate(
        valid_request(),
        valid_session(session_estimated_tokens_used=24_001),
        valid_policy(),
        NOW,
    )
    assert_denied_with(decision, "session_token_budget_exceeded")


def test_e3_session_calls_exhausted_denies():
    decision = evaluate_external_budget_gate(
        valid_request(),
        valid_session(session_calls_used=5),
        valid_policy(),
        NOW,
    )
    assert_denied_with(decision, "session_calls_exhausted")


@pytest.mark.parametrize(
    "field",
    [
        "session_calls_used",
        "session_estimated_tokens_used",
        "session_started_at",
    ],
)
@pytest.mark.parametrize("bad_value", [-1, True, 1.5, "0", None])
def test_e3_invalid_session_fields_deny(field, bad_value):
    session = valid_session(**{field: bad_value})
    decision = evaluate_external_budget_gate(
        valid_request(),
        session,
        valid_policy(),
        NOW,
    )
    expected = {
        "session_calls_used": "session_calls_used_invalid",
        "session_estimated_tokens_used": "session_estimated_tokens_used_invalid",
        "session_started_at": "session_started_at_invalid",
    }[field]
    assert_denied_with(decision, expected)


def test_e3_missing_session_fields_deny():
    for field, expected in [
        ("session_calls_used", "session_calls_used_missing"),
        ("session_estimated_tokens_used", "session_estimated_tokens_used_missing"),
        ("session_started_at", "session_started_at_missing"),
    ]:
        session = valid_session()
        session.pop(field)
        decision = evaluate_external_budget_gate(
            valid_request(),
            session,
            valid_policy(),
            NOW,
        )
        assert_denied_with(decision, expected)


def test_e3_ttl_exact_boundary_allows():
    decision = evaluate_external_budget_gate(
        valid_request(),
        valid_session(session_started_at=NOW - 3_600),
        valid_policy(max_session_ttl_seconds=3_600),
        NOW,
    )
    assert decision["allowed"] is True


def test_e3_ttl_one_second_under_allows():
    decision = evaluate_external_budget_gate(
        valid_request(),
        valid_session(session_started_at=NOW - 3_599),
        valid_policy(max_session_ttl_seconds=3_600),
        NOW,
    )
    assert decision["allowed"] is True


def test_e3_ttl_one_second_over_denies():
    decision = evaluate_external_budget_gate(
        valid_request(),
        valid_session(session_started_at=NOW - 3_601),
        valid_policy(max_session_ttl_seconds=3_600),
        NOW,
    )
    assert_denied_with(decision, "session_ttl_exceeded")


def test_e3_session_started_at_in_future_denies():
    decision = evaluate_external_budget_gate(
        valid_request(),
        valid_session(session_started_at=NOW + 1),
        valid_policy(),
        NOW,
    )
    assert_denied_with(decision, "session_started_at_in_future")


@pytest.mark.parametrize("bad_now", [-1, True, 1.5, "now", None])
def test_e3_invalid_now_epoch_denies_and_skips_ttl(bad_now):
    decision = evaluate_external_budget_gate(
        valid_request(),
        valid_session(),
        valid_policy(),
        bad_now,
    )
    assert_denied_with(decision, "now_epoch_invalid")
    assert "session_ttl_exceeded" not in decision["reason_codes"]


def test_e3_multi_error_reason_codes_are_stable_and_dependency_aware():
    decision = evaluate_external_budget_gate(
        valid_request(
            request_text_bytes=-1,
            requested_max_output_tokens=True,
        ),
        valid_session(session_calls_used=5),
        valid_policy(external_budget_enabled=1),
        NOW,
    )

    assert decision["allowed"] is False
    assert decision["reason_codes"] == [
        "external_budget_disabled",
        "request_text_bytes_invalid",
        "requested_output_tokens_invalid",
        "session_calls_exhausted",
    ]
    assert "session_token_budget_exceeded" not in decision["reason_codes"]


def test_e3_pure_idempotent_and_does_not_mutate_inputs():
    request = valid_request()
    session = valid_session()
    policy = valid_policy()

    request_before = deepcopy(request)
    session_before = deepcopy(session)
    policy_before = deepcopy(policy)

    first = evaluate_external_budget_gate(request, session, policy, NOW)
    second = evaluate_external_budget_gate(request, session, policy, NOW)

    assert first == second
    assert request == request_before
    assert session == session_before
    assert policy == policy_before
