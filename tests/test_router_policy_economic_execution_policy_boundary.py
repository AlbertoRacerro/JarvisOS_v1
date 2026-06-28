from __future__ import annotations

import copy
import inspect
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import router_policy_semantic_validator as validator  # noqa: E402


def consumed_ticket() -> dict:
    return {
        "schema_version": "v1",
        "consumption_key": "consent-alpha-001",
        "economic_envelope_complete": True,
        "automatic_execution_eligible": True,
        "economic_envelope": {
            "route_tier": "SCIENTIFIC_MEDIUM",
            "provider_candidate": "external:scientific_medium",
            "budget_class": "medium",
            "max_tokens_allowed": 1200,
            "dry_run_required": False,
            "allowed_execution_mode": "execute_after_confirm",
        },
    }


def requested_execution_plan() -> dict:
    return {
        "provider_candidate": "external:cheap",
        "budget_class": "cheap",
        "max_tokens_requested": 800,
        "execution_mode": "execute_after_confirm",
        "dry_run": False,
        "history_mode": "off",
        "max_retries_allowed": 0,
        "max_tool_calls_allowed": 0,
        "fallback_provider_allowed": False,
    }


def evaluate(ticket: dict, plan: dict) -> dict:
    return validator.evaluate_economic_execution_policy_boundary(ticket, plan)


def codes(result: dict) -> set[str]:
    return {violation["code"] for violation in result["violations"]}


def test_valid_consumed_envelope_and_bounded_requested_plan_pass():
    result = evaluate(consumed_ticket(), requested_execution_plan())

    assert result["execution_policy_allowed"] is True
    assert result["violations"] == []
    assert result["policy_scope"] == "economic_execution_precheck_only"
    assert result["provider_class_ordering"] == "abstract_only"
    assert result["budget_class_ordering"] == "abstract_only"


def test_consumed_economic_envelope_complete_false_fails():
    ticket = consumed_ticket()
    ticket["economic_envelope_complete"] = False

    result = evaluate(ticket, requested_execution_plan())

    assert result["execution_policy_allowed"] is False
    assert "INVALID_CONSUMED_TICKET" in codes(result)


def test_consumed_automatic_execution_eligible_false_fails():
    ticket = consumed_ticket()
    ticket["automatic_execution_eligible"] = False

    result = evaluate(ticket, requested_execution_plan())

    assert result["execution_policy_allowed"] is False
    assert "CONSUMED_TICKET_NOT_AUTOMATICALLY_EXECUTABLE" in codes(result)


def test_missing_or_invalid_consumed_schema_version_fails():
    for invalid in (None, "v2"):
        ticket = consumed_ticket()
        ticket["schema_version"] = invalid

        result = evaluate(ticket, requested_execution_plan())

        assert result["execution_policy_allowed"] is False
        assert "INVALID_CONSUMED_TICKET" in codes(result)


def test_unknown_provider_class_fails():
    ticket = consumed_ticket()
    ticket["economic_envelope"]["provider_candidate"] = "external:brandx"

    result = evaluate(ticket, requested_execution_plan())

    assert result["execution_policy_allowed"] is False
    assert "UNKNOWN_PROVIDER_CLASS" in codes(result)


def test_unknown_budget_class_fails():
    ticket = consumed_ticket()
    ticket["economic_envelope"]["budget_class"] = "premium-plus"

    result = evaluate(ticket, requested_execution_plan())

    assert result["execution_policy_allowed"] is False
    assert "UNKNOWN_BUDGET_CLASS" in codes(result)


def test_requested_provider_class_above_consumed_fails():
    ticket = consumed_ticket()
    ticket["economic_envelope"]["provider_candidate"] = "external:cheap"
    plan = requested_execution_plan()
    plan["provider_candidate"] = "external:frontier"

    result = evaluate(ticket, plan)

    assert result["execution_policy_allowed"] is False
    assert "REQUESTED_PROVIDER_EXCEEDS_CONSUMED_ENVELOPE" in codes(result)


def test_requested_budget_class_above_consumed_fails():
    ticket = consumed_ticket()
    ticket["economic_envelope"]["budget_class"] = "cheap"
    plan = requested_execution_plan()
    plan["budget_class"] = "frontier"

    result = evaluate(ticket, plan)

    assert result["execution_policy_allowed"] is False
    assert "REQUESTED_BUDGET_EXCEEDS_CONSUMED_ENVELOPE" in codes(result)


def test_requested_max_tokens_above_consumed_fails():
    plan = requested_execution_plan()
    plan["max_tokens_requested"] = 1300

    result = evaluate(consumed_ticket(), plan)

    assert result["execution_policy_allowed"] is False
    assert "REQUESTED_MAX_TOKENS_EXCEEDS_CONSUMED_ENVELOPE" in codes(result)


def test_requested_max_tokens_missing_or_invalid_fails():
    for invalid in (None, "100", 0, -1, True):
        plan = requested_execution_plan()
        plan["max_tokens_requested"] = invalid

        result = evaluate(consumed_ticket(), plan)

        assert result["execution_policy_allowed"] is False
        assert "INVALID_REQUESTED_MAX_TOKENS" in codes(result)


def test_dry_run_required_true_blocks_requested_dry_run_false():
    ticket = consumed_ticket()
    ticket["economic_envelope"]["dry_run_required"] = True

    result = evaluate(ticket, requested_execution_plan())

    assert result["execution_policy_allowed"] is False
    assert "DRY_RUN_REQUIRED_BLOCKS_REAL_EXECUTION" in codes(result)


def test_dry_run_required_true_allows_requested_dry_run_true_when_otherwise_valid():
    ticket = consumed_ticket()
    ticket["economic_envelope"]["dry_run_required"] = True
    plan = requested_execution_plan()
    plan["dry_run"] = True
    plan["execution_mode"] = "dry_run"

    result = evaluate(ticket, plan)

    assert result["execution_policy_allowed"] is True
    assert result["violations"] == []


def test_execution_mode_dry_run_with_dry_run_false_fails_closed():
    plan = requested_execution_plan()
    plan["execution_mode"] = "dry_run"
    plan["dry_run"] = False

    result = evaluate(consumed_ticket(), plan)

    assert result["execution_policy_allowed"] is False
    assert "EXECUTION_MODE_DRY_RUN_FLAG_MISMATCH" in codes(result)


def test_execute_after_confirm_with_dry_run_true_is_diagnostic_only():
    plan = requested_execution_plan()
    plan["dry_run"] = True
    plan.pop("history_mode")
    plan.pop("max_retries_allowed")
    plan.pop("max_tool_calls_allowed")
    plan.pop("fallback_provider_allowed")

    result = evaluate(consumed_ticket(), plan)

    assert result["execution_policy_allowed"] is True
    assert "POLICY_GAP_HISTORY_MODE" not in codes(result)
    assert "POLICY_GAP_MAX_RETRIES" not in codes(result)
    assert "POLICY_GAP_MAX_TOOL_CALLS" not in codes(result)
    assert "POLICY_GAP_FALLBACK_PROVIDER" not in codes(result)


def test_allowed_execution_mode_answer_only_propose_only_dry_run_and_blocked_fail_real_execution():
    for mode in ("answer_only", "propose_only", "dry_run", "blocked"):
        ticket = consumed_ticket()
        ticket["economic_envelope"]["allowed_execution_mode"] = mode

        result = evaluate(ticket, requested_execution_plan())

        assert result["execution_policy_allowed"] is False
        assert "EXECUTION_MODE_NOT_ALLOWED" in codes(result)


def test_allowed_execution_mode_execute_after_confirm_passes_when_otherwise_valid():
    result = evaluate(consumed_ticket(), requested_execution_plan())

    assert result["execution_policy_allowed"] is True


def test_history_not_off_fails_real_automatic_execution():
    plan = requested_execution_plan()
    plan["history_mode"] = "on"

    result = evaluate(consumed_ticket(), plan)

    assert result["execution_policy_allowed"] is False
    assert "POLICY_GAP_HISTORY_MODE" in codes(result)


def test_missing_history_mode_fails_real_automatic_execution():
    plan = requested_execution_plan()
    plan.pop("history_mode")

    result = evaluate(consumed_ticket(), plan)

    assert result["execution_policy_allowed"] is False
    assert "POLICY_GAP_HISTORY_MODE" in codes(result)


def test_missing_retry_cap_fails_real_automatic_execution():
    plan = requested_execution_plan()
    plan.pop("max_retries_allowed")

    result = evaluate(consumed_ticket(), plan)

    assert result["execution_policy_allowed"] is False
    assert "POLICY_GAP_MAX_RETRIES" in codes(result)


def test_missing_tool_cap_fails_real_automatic_execution():
    plan = requested_execution_plan()
    plan.pop("max_tool_calls_allowed")

    result = evaluate(consumed_ticket(), plan)

    assert result["execution_policy_allowed"] is False
    assert "POLICY_GAP_MAX_TOOL_CALLS" in codes(result)


def test_fallback_provider_missing_or_true_fails_unless_explicitly_disabled():
    for fallback in (None, True):
        plan = requested_execution_plan()
        if fallback is None:
            plan.pop("fallback_provider_allowed")
        else:
            plan["fallback_provider_allowed"] = fallback

        result = evaluate(consumed_ticket(), plan)

        assert result["execution_policy_allowed"] is False
        assert "POLICY_GAP_FALLBACK_PROVIDER" in codes(result)


def test_route_tier_alone_cannot_rescue_invalid_provider_budget_token_state():
    ticket = consumed_ticket()
    ticket["economic_envelope"] = {
        "route_tier": "FRONTIER",
        "provider_candidate": "unknown-provider",
        "budget_class": "unknown-budget",
        "max_tokens_allowed": 0,
        "dry_run_required": False,
        "allowed_execution_mode": "execute_after_confirm",
    }

    result = evaluate(ticket, requested_execution_plan())

    assert result["execution_policy_allowed"] is False
    assert "UNKNOWN_PROVIDER_CLASS" in codes(result)
    assert "UNKNOWN_BUDGET_CLASS" in codes(result)
    assert "INVALID_CONSUMED_TICKET" in codes(result)


def test_helper_does_not_mutate_consumed_ticket_or_requested_execution_plan():
    ticket = consumed_ticket()
    plan = requested_execution_plan()
    ticket_before = copy.deepcopy(ticket)
    plan_before = copy.deepcopy(plan)

    result = evaluate(ticket, plan)

    assert result["execution_policy_allowed"] is True
    assert ticket == ticket_before
    assert plan == plan_before


def test_helper_does_not_grant_provider_or_external_network_permissions():
    result = evaluate(consumed_ticket(), requested_execution_plan())

    assert result["execution_policy_allowed"] is True
    assert "provider_call_allowed_now" not in result
    assert "external_network_allowed_now" not in result
    assert "tool_execution_allowed_now" not in result


def test_helper_contains_no_provider_network_env_or_wall_clock_usage():
    source = inspect.getsource(validator.evaluate_economic_execution_policy_boundary)

    assert "EXECUTION_MODE_DRY_RUN_FLAG_MISMATCH" in source
    assert "requests" not in source
    assert "httpx" not in source
    assert "openai" not in source
    assert "anthropic" not in source
    assert "datetime.now" not in source
    assert "time.time" not in source
    assert "utcnow(" not in source
    assert "os.environ" not in source
