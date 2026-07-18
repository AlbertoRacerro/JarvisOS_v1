import sqlite3

from app.core.database import open_sqlite_connection
from app.modules.ai.contracts import AIPolicyMode
from app.modules.ai.models import AISettingsRead, AISettingsUpdate
from app.modules.events.service import utc_now

SETTINGS_ID = "default"


def _to_bool(value: int | bool) -> bool:
    return bool(value)


def _policy_mode(value: object) -> AIPolicyMode:
    try:
        return AIPolicyMode(str(value or AIPolicyMode.FAST_DEV.value))
    except ValueError:
        return AIPolicyMode.FAST_DEV


def _policy_mode_value(value: object) -> str:
    if isinstance(value, AIPolicyMode):
        return value.value
    return _policy_mode(value).value


def _row_to_settings(row: sqlite3.Row) -> AISettingsRead:
    data = dict(row)
    input_tokens = int(data["scaleway_input_tokens_month_to_date"])
    output_tokens = int(data["scaleway_output_tokens_month_to_date"])
    return AISettingsRead(
        policy_mode=_policy_mode(data.get("policy_mode")),
        monthly_api_budget_usd=float(data["monthly_api_budget_usd"]),
        api_spend_month_to_date_usd=float(data["api_spend_month_to_date_usd"]),
        paid_ai_enabled=_to_bool(data["paid_ai_enabled"]),
        default_ai_provider=data["default_ai_provider"],
        default_ai_model=data["default_ai_model"],
        provider_mode=data["provider_mode"],
        use_fake_provider_when_budget_zero=_to_bool(data["use_fake_provider_when_budget_zero"]),
        scaleway_enabled=_to_bool(data["scaleway_enabled"]),
        scaleway_smoke_test_enabled=_to_bool(data["scaleway_smoke_test_enabled"]),
        scaleway_live_smoke_test_enabled=_to_bool(data.get("scaleway_live_smoke_test_enabled", 0)),
        scaleway_monthly_token_cap=int(data["scaleway_monthly_token_cap"]),
        scaleway_hard_stop_token_cap=int(data["scaleway_hard_stop_token_cap"]),
        scaleway_free_tier_reference_tokens=int(data["scaleway_free_tier_reference_tokens"]),
        scaleway_input_tokens_month_to_date=input_tokens,
        scaleway_output_tokens_month_to_date=output_tokens,
        usage_total_tokens=input_tokens + output_tokens,
        smoke_test_mode_enabled=_to_bool(data["smoke_test_mode_enabled"]),
        max_direct_continuations=int(data["max_direct_continuations"]),
        direct_continuation_policy_version=str(data["direct_continuation_policy_version"]),
        updated_at=data["updated_at"],
    )


def ensure_ai_settings() -> AISettingsRead:
    now = utc_now()
    with open_sqlite_connection() as connection:
        connection.execute(
            """
            INSERT OR IGNORE INTO ai_settings (
                id, policy_mode, monthly_api_budget_usd, api_spend_month_to_date_usd,
                paid_ai_enabled, default_ai_provider, default_ai_model,
                provider_mode, use_fake_provider_when_budget_zero,
                scaleway_enabled, scaleway_token_cap,
                scaleway_tokens_month_to_date, scaleway_smoke_test_enabled,
                scaleway_live_smoke_test_enabled,
                scaleway_monthly_token_cap, scaleway_hard_stop_token_cap,
                scaleway_free_tier_reference_tokens, scaleway_input_tokens_month_to_date,
                scaleway_output_tokens_month_to_date, smoke_test_mode_enabled, updated_at
            ) VALUES (?, 'FAST_DEV', 0, 0, 0, 'fake', 'fake-modeling-draft-v1', 'fake', 1, 0, 0, 0, 0, 0, 500000, 800000, 1000000, 0, 0, 0, ?)
            """,
            (SETTINGS_ID, now),
        )
        connection.commit()
    return get_ai_settings()


def get_ai_settings() -> AISettingsRead:
    with open_sqlite_connection() as connection:
        row = connection.execute("SELECT * FROM ai_settings WHERE id = ?", (SETTINGS_ID,)).fetchone()
    if row is None:
        return ensure_ai_settings()
    return _row_to_settings(row)


def update_ai_settings(payload: AISettingsUpdate) -> AISettingsRead:
    current = get_ai_settings()
    values = current.model_dump()
    updates = payload.model_dump(exclude_unset=True)
    values.update({key: value for key, value in updates.items() if value is not None})

    now = utc_now()
    with open_sqlite_connection() as connection:
        connection.execute(
            """
            UPDATE ai_settings
            SET policy_mode = ?, monthly_api_budget_usd = ?, paid_ai_enabled = ?,
                default_ai_provider = ?, default_ai_model = ?, provider_mode = ?,
                use_fake_provider_when_budget_zero = ?, scaleway_enabled = ?,
                scaleway_smoke_test_enabled = ?, scaleway_live_smoke_test_enabled = ?,
                scaleway_monthly_token_cap = ?, scaleway_hard_stop_token_cap = ?,
                scaleway_input_tokens_month_to_date = ?,
                scaleway_output_tokens_month_to_date = ?,
                smoke_test_mode_enabled = ?, max_direct_continuations = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                _policy_mode_value(values["policy_mode"]),
                float(values["monthly_api_budget_usd"]),
                int(bool(values["paid_ai_enabled"])),
                str(values["default_ai_provider"]),
                str(values["default_ai_model"]),
                str(values["provider_mode"]),
                int(bool(values["use_fake_provider_when_budget_zero"])),
                int(bool(values["scaleway_enabled"])),
                int(bool(values["scaleway_smoke_test_enabled"])),
                int(bool(values["scaleway_live_smoke_test_enabled"])),
                int(values["scaleway_monthly_token_cap"]),
                int(values["scaleway_hard_stop_token_cap"]),
                int(values["scaleway_input_tokens_month_to_date"]),
                int(values["scaleway_output_tokens_month_to_date"]),
                int(bool(values["smoke_test_mode_enabled"])),
                int(values["max_direct_continuations"]),
                now,
                SETTINGS_ID,
            ),
        )
        connection.commit()
    return get_ai_settings()


def record_scaleway_token_usage(*, input_tokens: int, output_tokens: int) -> AISettingsRead:
    with open_sqlite_connection() as connection:
        connection.execute(
            """
            UPDATE ai_settings
            SET scaleway_input_tokens_month_to_date = scaleway_input_tokens_month_to_date + ?,
                scaleway_output_tokens_month_to_date = scaleway_output_tokens_month_to_date + ?,
                updated_at = ?
            WHERE id = ?
            """,
            (input_tokens, output_tokens, utc_now(), SETTINGS_ID),
        )
        connection.commit()
    return get_ai_settings()
