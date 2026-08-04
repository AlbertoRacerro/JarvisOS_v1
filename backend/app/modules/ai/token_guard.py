from dataclasses import dataclass
from datetime import UTC, datetime
from math import ceil

from app.core.database import open_sqlite_connection
from app.modules.ai.contracts import AIPolicyMode
from app.modules.ai.models import AISettingsRead, SmokeTestTokenMetadata


@dataclass(frozen=True)
class TokenGuardDecision:
    allowed: bool
    reason: str | None
    metadata: SmokeTestTokenMetadata


def estimate_tokens(text: str) -> int:
    return max(1, ceil(len(text) / 4))


def evaluate_token_guard(
    settings: AISettingsRead,
    *,
    input_text: str,
    estimated_output_tokens: int = 80,
) -> TokenGuardDecision:
    estimated_input = estimate_tokens(input_text)
    current_usage = (
        settings.scaleway_input_tokens_month_to_date
        + settings.scaleway_output_tokens_month_to_date
    )
    projected_usage = current_usage + estimated_input + estimated_output_tokens

    reason: str | None = None
    if projected_usage > settings.scaleway_monthly_token_cap:
        reason = "scaleway_monthly_token_cap_exceeded"
    elif projected_usage > settings.scaleway_hard_stop_token_cap:
        reason = "scaleway_hard_stop_token_cap_exceeded"

    return TokenGuardDecision(
        allowed=reason is None,
        reason=reason,
        metadata=_metadata(
            blocked=reason is not None,
            estimated_input=estimated_input,
            estimated_output=estimated_output_tokens,
            monthly_cap=settings.scaleway_monthly_token_cap,
            hard_stop_cap=settings.scaleway_hard_stop_token_cap,
            current_usage=current_usage,
        ),
    )


def reserve_scaleway_smoke_tokens(
    *,
    input_text: str,
    estimated_output_tokens: int = 80,
    now: datetime | None = None,
) -> TokenGuardDecision:
    """Atomically reserve one live-smoke projection against all Scaleway usage.

    Legacy smoke usage is stored in ``ai_settings``. Normal routed usage is
    stored in ``ai_jobs`` and its not-yet-finalized authority is represented by
    active/in-flight 059b reservations. The transaction combines all three
    sources plus the current request before incrementing the legacy counters by
    the conservative projection. This prevents concurrent smoke and routed
    calls from dispatching through the same remaining headroom.
    """

    estimated_input = estimate_tokens(input_text)
    now_dt = now or datetime.now(UTC)
    if now_dt.tzinfo is None:
        raise ValueError("now must include timezone information")
    now_dt = now_dt.astimezone(UTC)
    month_start = now_dt.strftime("%Y-%m-01")
    now_iso = now_dt.isoformat()

    with open_sqlite_connection() as connection:
        connection.execute("BEGIN IMMEDIATE")
        try:
            settings = connection.execute(
                """
                SELECT policy_mode, provider_mode, paid_ai_enabled,
                       monthly_api_budget_usd, api_spend_month_to_date_usd,
                       scaleway_enabled, scaleway_smoke_test_enabled,
                       scaleway_live_smoke_test_enabled,
                       scaleway_monthly_token_cap,
                       scaleway_hard_stop_token_cap,
                       scaleway_input_tokens_month_to_date,
                       scaleway_output_tokens_month_to_date
                FROM ai_settings WHERE id = 'default'
                """
            ).fetchone()
            if settings is None:
                raise RuntimeError("missing_ai_settings")

            routed = connection.execute(
                """
                SELECT COALESCE(
                    SUM(COALESCE(input_tokens, 0) + COALESCE(output_tokens, 0)),
                    0
                ) AS tokens
                FROM ai_jobs
                WHERE provider_id = 'scaleway' AND created_at >= ?
                """,
                (month_start,),
            ).fetchone()
            reserved = connection.execute(
                """
                SELECT COALESCE(
                    SUM(projected_input_tokens + projected_output_tokens),
                    0
                ) AS tokens
                FROM egress_budget_reservations
                WHERE provider_id = 'scaleway'
                  AND (
                    state = 'in_flight'
                    OR (state = 'active' AND expires_at > ?)
                  )
                """,
                (now_iso,),
            ).fetchone()

            legacy_usage = int(
                settings["scaleway_input_tokens_month_to_date"]
            ) + int(settings["scaleway_output_tokens_month_to_date"])
            current_usage = (
                legacy_usage + int(routed["tokens"]) + int(reserved["tokens"])
            )
            monthly_cap = int(settings["scaleway_monthly_token_cap"])
            hard_stop_cap = int(settings["scaleway_hard_stop_token_cap"])
            projected_usage = (
                current_usage + estimated_input + estimated_output_tokens
            )

            reason = _atomic_smoke_blocking_reason(
                settings=settings,
                monthly_cap=monthly_cap,
                hard_stop_cap=hard_stop_cap,
                projected_usage=projected_usage,
            )
            if reason is None:
                updated = connection.execute(
                    """
                    UPDATE ai_settings
                    SET scaleway_input_tokens_month_to_date =
                            scaleway_input_tokens_month_to_date + ?,
                        scaleway_output_tokens_month_to_date =
                            scaleway_output_tokens_month_to_date + ?
                    WHERE id = 'default'
                    """,
                    (estimated_input, estimated_output_tokens),
                )
                if updated.rowcount != 1:
                    raise RuntimeError("missing_ai_settings")
            connection.commit()
        except Exception:
            connection.rollback()
            raise

    return TokenGuardDecision(
        allowed=reason is None,
        reason=reason,
        metadata=_metadata(
            blocked=reason is not None,
            estimated_input=estimated_input,
            estimated_output=estimated_output_tokens,
            monthly_cap=monthly_cap,
            hard_stop_cap=hard_stop_cap,
            current_usage=current_usage,
        ),
    )


def reconcile_scaleway_smoke_reservation(
    metadata: SmokeTestTokenMetadata,
    *,
    reported_input_tokens: int | None,
    reported_output_tokens: int | None,
) -> None:
    """Replace a conservative smoke reservation with reported usage.

    A missing component remains conservatively reserved at its estimate. Zero
    is treated as real reported usage, not as missing data.
    """

    actual_input = (
        metadata.estimated_input_tokens
        if reported_input_tokens is None
        else reported_input_tokens
    )
    actual_output = (
        metadata.estimated_output_tokens
        if reported_output_tokens is None
        else reported_output_tokens
    )
    if actual_input < 0 or actual_output < 0:
        raise ValueError("reported token usage must be non-negative")

    input_delta = actual_input - metadata.estimated_input_tokens
    output_delta = actual_output - metadata.estimated_output_tokens
    if input_delta == 0 and output_delta == 0:
        return

    with open_sqlite_connection() as connection:
        connection.execute("BEGIN IMMEDIATE")
        try:
            row = connection.execute(
                """
                SELECT scaleway_input_tokens_month_to_date,
                       scaleway_output_tokens_month_to_date
                FROM ai_settings WHERE id = 'default'
                """
            ).fetchone()
            if row is None:
                raise RuntimeError("missing_ai_settings")
            next_input = int(row["scaleway_input_tokens_month_to_date"]) + input_delta
            next_output = int(row["scaleway_output_tokens_month_to_date"]) + output_delta
            if next_input < 0 or next_output < 0:
                raise RuntimeError("scaleway_smoke_reservation_underflow")
            connection.execute(
                """
                UPDATE ai_settings
                SET scaleway_input_tokens_month_to_date = ?,
                    scaleway_output_tokens_month_to_date = ?
                WHERE id = 'default'
                """,
                (next_input, next_output),
            )
            connection.commit()
        except Exception:
            connection.rollback()
            raise


def metadata_with_reported_usage(
    metadata: SmokeTestTokenMetadata,
    *,
    reported_input_tokens: int | None,
    reported_output_tokens: int | None,
) -> SmokeTestTokenMetadata:
    usage_source = (
        "actual"
        if reported_input_tokens is not None or reported_output_tokens is not None
        else "estimated"
    )
    return SmokeTestTokenMetadata(
        blocked_by_token_cap=metadata.blocked_by_token_cap,
        estimated_input_tokens=metadata.estimated_input_tokens,
        estimated_output_tokens=metadata.estimated_output_tokens,
        reported_input_tokens=reported_input_tokens,
        reported_output_tokens=reported_output_tokens,
        monthly_token_cap=metadata.monthly_token_cap,
        hard_stop_token_cap=metadata.hard_stop_token_cap,
        token_usage_month_to_date=metadata.token_usage_month_to_date,
        usage_source=usage_source,
    )


def _atomic_smoke_blocking_reason(
    *,
    settings,
    monthly_cap: int,
    hard_stop_cap: int,
    projected_usage: int,
) -> str | None:
    if settings["policy_mode"] == AIPolicyMode.DISABLED.value:
        return "ai_policy_disabled"
    if settings["provider_mode"] != "scaleway":
        return "scaleway_provider_mode_required"
    if not bool(settings["paid_ai_enabled"]):
        return "paid_ai_disabled"
    if float(settings["monthly_api_budget_usd"]) <= 0:
        return "monthly_budget_zero"
    if float(settings["api_spend_month_to_date_usd"]) >= float(
        settings["monthly_api_budget_usd"]
    ):
        return "monthly_budget_exhausted"
    if not bool(settings["scaleway_enabled"]):
        return "scaleway_disabled"
    if not bool(settings["scaleway_smoke_test_enabled"]):
        return "scaleway_smoke_test_disabled"
    if not bool(settings["scaleway_live_smoke_test_enabled"]):
        return "scaleway_live_smoke_test_disabled"
    if monthly_cap <= 0:
        return "scaleway_monthly_token_cap_zero"
    if hard_stop_cap <= 0:
        return "scaleway_hard_stop_token_cap_zero"
    if projected_usage > monthly_cap:
        return "scaleway_monthly_token_cap_exceeded"
    if projected_usage > hard_stop_cap:
        return "scaleway_hard_stop_token_cap_exceeded"
    return None


def _metadata(
    *,
    blocked: bool,
    estimated_input: int,
    estimated_output: int,
    monthly_cap: int,
    hard_stop_cap: int,
    current_usage: int,
) -> SmokeTestTokenMetadata:
    return SmokeTestTokenMetadata(
        blocked_by_token_cap=blocked,
        estimated_input_tokens=estimated_input,
        estimated_output_tokens=estimated_output,
        reported_input_tokens=None,
        reported_output_tokens=None,
        monthly_token_cap=monthly_cap,
        hard_stop_token_cap=hard_stop_cap,
        token_usage_month_to_date=current_usage,
    )
