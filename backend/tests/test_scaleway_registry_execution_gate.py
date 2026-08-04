from types import SimpleNamespace

import pytest

from app.modules.ai import budget
from app.modules.ai.contracts import AIPolicyMode


def _settings(**overrides: object) -> SimpleNamespace:
    values: dict[str, object] = {
        "policy_mode": AIPolicyMode.FAST_DEV,
        "paid_ai_enabled": True,
        "monthly_api_budget_usd": 10.0,
        "api_spend_month_to_date_usd": 0.0,
        "provider_mode": "scaleway",
        "scaleway_enabled": True,
        "scaleway_smoke_test_enabled": True,
        "scaleway_live_smoke_test_enabled": True,
        "scaleway_monthly_token_cap": 1_000,
        "scaleway_hard_stop_token_cap": 1_000,
        "scaleway_input_tokens_month_to_date": 0,
        "scaleway_output_tokens_month_to_date": 0,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def _allow_registry_scaleway(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(budget, "scaleway_api_key_configured", lambda: True)
    monkeypatch.setattr(
        budget,
        "resolve_secret_ref",
        lambda _ref: SimpleNamespace(key_present=True),
    )
    monkeypatch.setattr(
        budget,
        "_registry_provider",
        lambda _provider_id: SimpleNamespace(
            enabled=True,
            api_key_ref="env:SCALEWAY_API_KEY",
            monthly_token_cap=1_000_000,
            monthly_cost_cap_usd=25.0,
        ),
    )
    monkeypatch.setattr(
        budget,
        "provider_month_to_date_usage",
        lambda _provider_id: (0, 0.0),
    )


@pytest.mark.parametrize(
    ("setting_name", "blocking_reason"),
    [
        ("scaleway_enabled", "scaleway_disabled"),
        ("scaleway_smoke_test_enabled", "scaleway_smoke_test_disabled"),
        (
            "scaleway_live_smoke_test_enabled",
            "scaleway_live_smoke_test_disabled",
        ),
    ],
)
def test_registry_scaleway_preserves_execution_flags(
    monkeypatch: pytest.MonkeyPatch,
    setting_name: str,
    blocking_reason: str,
) -> None:
    _allow_registry_scaleway(monkeypatch)

    gate = budget.evaluate_provider_budget_gate(
        _settings(**{setting_name: False}),
        "scaleway",
    )

    assert gate.allowed is False
    assert gate.blocking_reason == blocking_reason


def test_registry_scaleway_requires_scaleway_provider_mode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _allow_registry_scaleway(monkeypatch)

    gate = budget.evaluate_provider_budget_gate(
        _settings(provider_mode="fake"),
        "scaleway",
    )

    assert gate.allowed is False
    assert gate.blocking_reason == "scaleway_provider_mode_required"


@pytest.mark.parametrize(
    ("overrides", "blocking_reason"),
    [
        (
            {"scaleway_monthly_token_cap": 0},
            "scaleway_monthly_token_cap_zero",
        ),
        (
            {"scaleway_hard_stop_token_cap": 0},
            "scaleway_hard_stop_token_cap_zero",
        ),
        (
            {
                "scaleway_input_tokens_month_to_date": 100,
                "scaleway_monthly_token_cap": 100,
                "scaleway_hard_stop_token_cap": 200,
            },
            "scaleway_monthly_token_cap_exhausted",
        ),
        (
            {
                "scaleway_input_tokens_month_to_date": 100,
                "scaleway_monthly_token_cap": 200,
                "scaleway_hard_stop_token_cap": 100,
            },
            "scaleway_hard_stop_token_cap_exhausted",
        ),
    ],
)
def test_registry_scaleway_preserves_legacy_token_caps(
    monkeypatch: pytest.MonkeyPatch,
    overrides: dict[str, object],
    blocking_reason: str,
) -> None:
    _allow_registry_scaleway(monkeypatch)

    gate = budget.evaluate_provider_budget_gate(
        _settings(**overrides),
        "scaleway",
    )

    assert gate.allowed is False
    assert gate.blocking_reason == blocking_reason


def test_registry_scaleway_still_applies_registry_cost_cap(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _allow_registry_scaleway(monkeypatch)
    monkeypatch.setattr(
        budget,
        "provider_month_to_date_usage",
        lambda _provider_id: (1, 25.0),
    )

    gate = budget.evaluate_provider_budget_gate(_settings(), "scaleway")

    assert gate.allowed is False
    assert gate.blocking_reason == "scaleway_monthly_cost_cap_exhausted"


def test_registry_scaleway_opens_only_after_both_gate_layers_pass(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _allow_registry_scaleway(monkeypatch)

    gate = budget.evaluate_provider_budget_gate(_settings(), "scaleway")

    assert gate.allowed is True
    assert gate.blocking_reason is None
    assert gate.provider_id == "scaleway"
