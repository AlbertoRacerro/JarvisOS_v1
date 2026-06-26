from __future__ import annotations

from typing import Any


DEFAULT_BYTES_PER_TOKEN = 3

REQUIRED_POLICY_CAPS = (
    "max_input_bytes",
    "max_estimated_input_tokens",
    "max_output_tokens",
    "max_session_estimated_tokens",
    "max_calls_per_session",
    "max_session_ttl_seconds",
)

REASON_ORDER = (
    "request_not_dict",
    "session_usage_not_dict",
    "budget_policy_not_dict",
    "external_budget_disabled",
    "policy_required_cap_missing",
    "policy_required_cap_invalid",
    "bytes_per_token_invalid",
    "policy_session_token_cap_incoherent",
    "request_text_bytes_missing",
    "request_text_bytes_invalid",
    "request_text_bytes_exceed_cap",
    "estimated_input_tokens_invalid",
    "estimated_input_tokens_exceed_cap",
    "requested_output_tokens_missing",
    "requested_output_tokens_invalid",
    "requested_output_tokens_exceed_cap",
    "session_calls_used_missing",
    "session_calls_used_invalid",
    "session_calls_exhausted",
    "session_estimated_tokens_used_missing",
    "session_estimated_tokens_used_invalid",
    "session_token_budget_exceeded",
    "session_started_at_missing",
    "session_started_at_invalid",
    "now_epoch_invalid",
    "session_started_at_in_future",
    "session_ttl_exceeded",
)


def _is_strict_int(value: Any) -> bool:
    """Return True for int, but reject bool.

    Python bool is a subclass of int, so isinstance(True, int) is unsafe for
    numeric budget gates.
    """

    return type(value) is int


def _is_strict_nonnegative_int(value: Any) -> bool:
    return _is_strict_int(value) and value >= 0


def _is_strict_positive_int(value: Any) -> bool:
    return _is_strict_int(value) and value > 0


def _stable_reason_codes(reason_codes: list[str]) -> list[str]:
    seen = set(reason_codes)
    return [code for code in REASON_ORDER if code in seen]


def _ceil_div(numerator: int, denominator: int) -> int:
    return (numerator + denominator - 1) // denominator


def evaluate_external_budget_gate(
    request: dict[str, Any] | None,
    session_usage: dict[str, Any] | None,
    budget_policy: dict[str, Any] | None,
    now_epoch: int,
) -> dict[str, Any]:
    """Evaluate deterministic budget/session limits for a future external call.

    This is a pure, provider-agnostic gate.

    Important boundaries:
    - `request_text_bytes` must be computed server-side by the caller from the
      exact text-bearing payload that would be sent externally.
    - This function does not render, hash, canonicalize, or inspect provider
      payloads.
    - This function does not persist session counters. On allowed execution, the
      caller must persist `next_session_usage` after a successful external call.
    - Output budget is conservatively counted using requested_max_output_tokens,
      because real output token usage is unknown before the provider call.
    """

    reason_codes: list[str] = []

    request_is_dict = isinstance(request, dict)
    session_is_dict = isinstance(session_usage, dict)
    policy_is_dict = isinstance(budget_policy, dict)

    if not request_is_dict:
        reason_codes.append("request_not_dict")
    if not session_is_dict:
        reason_codes.append("session_usage_not_dict")
    if not policy_is_dict:
        reason_codes.append("budget_policy_not_dict")

    policy_values: dict[str, int] = {}
    bytes_per_token = DEFAULT_BYTES_PER_TOKEN
    policy_caps_valid = False

    if policy_is_dict:
        if budget_policy.get("external_budget_enabled") is not True:
            reason_codes.append("external_budget_disabled")

        caps_present = True
        caps_valid = True

        for cap in REQUIRED_POLICY_CAPS:
            if cap not in budget_policy:
                caps_present = False
            elif not _is_strict_positive_int(budget_policy.get(cap)):
                caps_valid = False
            else:
                policy_values[cap] = budget_policy[cap]

        if not caps_present:
            reason_codes.append("policy_required_cap_missing")
        if not caps_valid:
            reason_codes.append("policy_required_cap_invalid")

        if "bytes_per_token" in budget_policy:
            if not _is_strict_positive_int(budget_policy.get("bytes_per_token")):
                reason_codes.append("bytes_per_token_invalid")
            else:
                bytes_per_token = budget_policy["bytes_per_token"]

        policy_caps_valid = (
            caps_present
            and caps_valid
            and "bytes_per_token_invalid" not in reason_codes
        )

        if policy_caps_valid:
            max_full_request = (
                policy_values["max_estimated_input_tokens"]
                + policy_values["max_output_tokens"]
            )
            if policy_values["max_session_estimated_tokens"] < max_full_request:
                reason_codes.append("policy_session_token_cap_incoherent")
                policy_caps_valid = False

    request_text_bytes: int | None = None
    provided_estimated_input_tokens: int | None = None
    requested_max_output_tokens: int | None = None

    request_text_bytes_valid = False
    estimated_input_tokens_valid = False
    requested_output_tokens_valid = False

    if request_is_dict:
        if "request_text_bytes" not in request:
            reason_codes.append("request_text_bytes_missing")
        elif not _is_strict_positive_int(request.get("request_text_bytes")):
            reason_codes.append("request_text_bytes_invalid")
        else:
            request_text_bytes = request["request_text_bytes"]
            request_text_bytes_valid = True

        if "estimated_input_tokens" not in request or request.get("estimated_input_tokens") is None:
            provided_estimated_input_tokens = None
            estimated_input_tokens_valid = True
        elif not _is_strict_nonnegative_int(request.get("estimated_input_tokens")):
            reason_codes.append("estimated_input_tokens_invalid")
        else:
            provided_estimated_input_tokens = request["estimated_input_tokens"]
            estimated_input_tokens_valid = True

        if "requested_max_output_tokens" not in request:
            reason_codes.append("requested_output_tokens_missing")
        elif not _is_strict_positive_int(request.get("requested_max_output_tokens")):
            reason_codes.append("requested_output_tokens_invalid")
        else:
            requested_max_output_tokens = request["requested_max_output_tokens"]
            requested_output_tokens_valid = True

    session_calls_used: int | None = None
    session_estimated_tokens_used: int | None = None
    session_started_at: int | None = None

    session_calls_valid = False
    session_tokens_valid = False
    session_started_valid = False

    if session_is_dict:
        if "session_calls_used" not in session_usage:
            reason_codes.append("session_calls_used_missing")
        elif not _is_strict_nonnegative_int(session_usage.get("session_calls_used")):
            reason_codes.append("session_calls_used_invalid")
        else:
            session_calls_used = session_usage["session_calls_used"]
            session_calls_valid = True

        if "session_estimated_tokens_used" not in session_usage:
            reason_codes.append("session_estimated_tokens_used_missing")
        elif not _is_strict_nonnegative_int(session_usage.get("session_estimated_tokens_used")):
            reason_codes.append("session_estimated_tokens_used_invalid")
        else:
            session_estimated_tokens_used = session_usage["session_estimated_tokens_used"]
            session_tokens_valid = True

        if "session_started_at" not in session_usage:
            reason_codes.append("session_started_at_missing")
        elif not _is_strict_nonnegative_int(session_usage.get("session_started_at")):
            reason_codes.append("session_started_at_invalid")
        else:
            session_started_at = session_usage["session_started_at"]
            session_started_valid = True

    now_valid = _is_strict_nonnegative_int(now_epoch)
    if not now_valid:
        reason_codes.append("now_epoch_invalid")

    if (
        policy_caps_valid
        and request_text_bytes_valid
        and request_text_bytes is not None
        and request_text_bytes > policy_values["max_input_bytes"]
    ):
        reason_codes.append("request_text_bytes_exceed_cap")

    final_estimated_input_tokens: int | None = None
    estimated_request_tokens: int | None = None

    if request_text_bytes_valid and estimated_input_tokens_valid and request_text_bytes is not None:
        derived_token_estimate = _ceil_div(request_text_bytes, bytes_per_token)
        if provided_estimated_input_tokens is None:
            final_estimated_input_tokens = derived_token_estimate
        else:
            final_estimated_input_tokens = max(
                provided_estimated_input_tokens,
                derived_token_estimate,
            )

        if (
            policy_caps_valid
            and final_estimated_input_tokens > policy_values["max_estimated_input_tokens"]
        ):
            reason_codes.append("estimated_input_tokens_exceed_cap")

    if (
        policy_caps_valid
        and requested_output_tokens_valid
        and requested_max_output_tokens is not None
        and requested_max_output_tokens > policy_values["max_output_tokens"]
    ):
        reason_codes.append("requested_output_tokens_exceed_cap")

    if (
        final_estimated_input_tokens is not None
        and requested_output_tokens_valid
        and requested_max_output_tokens is not None
    ):
        estimated_request_tokens = final_estimated_input_tokens + requested_max_output_tokens

    if policy_caps_valid and session_calls_valid and session_calls_used is not None:
        if session_calls_used >= policy_values["max_calls_per_session"]:
            reason_codes.append("session_calls_exhausted")

    if (
        policy_caps_valid
        and session_tokens_valid
        and estimated_request_tokens is not None
        and session_estimated_tokens_used is not None
    ):
        if (
            session_estimated_tokens_used + estimated_request_tokens
            > policy_values["max_session_estimated_tokens"]
        ):
            reason_codes.append("session_token_budget_exceeded")

    if (
        policy_caps_valid
        and now_valid
        and session_started_valid
        and session_started_at is not None
    ):
        if now_epoch < session_started_at:
            reason_codes.append("session_started_at_in_future")
        else:
            elapsed = now_epoch - session_started_at
            if elapsed > policy_values["max_session_ttl_seconds"]:
                reason_codes.append("session_ttl_exceeded")

    stable_reason_codes = _stable_reason_codes(reason_codes)
    allowed = len(stable_reason_codes) == 0

    remaining_calls: int | None = None
    remaining_session_tokens: int | None = None
    next_session_usage: dict[str, int] | None = None

    if allowed:
        # These values are guaranteed to be non-None by the validation gates.
        assert session_calls_used is not None
        assert session_estimated_tokens_used is not None
        assert session_started_at is not None
        assert estimated_request_tokens is not None

        remaining_calls = policy_values["max_calls_per_session"] - session_calls_used - 1
        remaining_session_tokens = (
            policy_values["max_session_estimated_tokens"]
            - session_estimated_tokens_used
            - estimated_request_tokens
        )
        next_session_usage = {
            "session_calls_used": session_calls_used + 1,
            "session_estimated_tokens_used": (
                session_estimated_tokens_used + estimated_request_tokens
            ),
            "session_started_at": session_started_at,
        }

    return {
        "allowed": allowed,
        "reason_codes": stable_reason_codes,
        "estimated_input_tokens": final_estimated_input_tokens,
        "estimated_request_tokens": estimated_request_tokens,
        "approved_max_output_tokens": requested_max_output_tokens if allowed else None,
        "remaining_calls": remaining_calls,
        "remaining_session_tokens": remaining_session_tokens,
        "next_session_usage": next_session_usage,
    }
