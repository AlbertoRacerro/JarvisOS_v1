from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if text.count(old) != 1:
        raise RuntimeError(f"{label} shape drifted")
    return text.replace(old, new)


egress_path = Path("backend/app/modules/ai/egress_persistence.py")
text = egress_path.read_text(encoding="utf-8")

text = replace_once(
    text,
    '''        if not provider.enabled:\n            blocking_reason = "provider_disabled"\n        elif not provider.requires_network:\n            blocking_reason = None\n        else:\n            blocking_reason = _hard_blocking_reason(\n                connection,\n                material=_AvailabilityMaterial(provider_id=provider_id),\n                projection=_AvailabilityProjectionInputs(),\n                registry=registry,\n                snapshot=snapshot,\n            )\n''',
    '''        if not provider.enabled:\n            blocking_reason = "provider_disabled"\n        else:\n            blocking_reason = _hard_blocking_reason(\n                connection,\n                material=_AvailabilityMaterial(provider_id=provider_id),\n                projection=_AvailabilityProjectionInputs(),\n                registry=registry,\n                snapshot=snapshot,\n            )\n''',
    "availability caller",
)

text = replace_once(
    text,
    '''    if settings["policy_mode"] == AIPolicyMode.DISABLED.value:\n        return "ai_policy_disabled"\n    if not bool(settings["paid_ai_enabled"]):\n        return "paid_ai_disabled"\n''',
    '''    if settings["policy_mode"] == AIPolicyMode.DISABLED.value:\n        return "ai_policy_disabled"\n\n    provider = registry.providers[material.provider_id]\n    if not provider.requires_network:\n        return None\n\n    if not bool(settings["paid_ai_enabled"]):\n        return "paid_ai_disabled"\n''',
    "policy/non-network blocker",
)

text = replace_once(
    text,
    '''    provider = registry.providers[material.provider_id]\n    try:\n        credential = resolve_secret_ref(provider.api_key_ref)\n''',
    '''    try:\n        credential = resolve_secret_ref(provider.api_key_ref)\n''',
    "provider lookup",
)

text = replace_once(
    text,
    '''    global_actual = snapshot.global_actual_cost_usd\n    if not isinstance(material, _AvailabilityMaterial):\n        configured_global_spend = float(settings["api_spend_month_to_date_usd"])\n        global_actual = max(configured_global_spend, global_actual)\n    if (\n        global_actual\n        + snapshot.global_reserved_cost_usd\n        + projection.projected_cost_upper_usd\n        > monthly_budget\n    ):\n        return "global_monthly_cost_cap_exceeded"\n''',
    '''    is_availability_projection = isinstance(material, _AvailabilityMaterial)\n    configured_global_spend = float(settings["api_spend_month_to_date_usd"])\n    global_actual = max(configured_global_spend, snapshot.global_actual_cost_usd)\n    projected_global_cost = (\n        global_actual\n        + snapshot.global_reserved_cost_usd\n        + projection.projected_cost_upper_usd\n    )\n    if projected_global_cost > monthly_budget or (\n        is_availability_projection and projected_global_cost >= monthly_budget\n    ):\n        return "global_monthly_cost_cap_exceeded"\n''',
    "global budget blocker",
)

text = replace_once(
    text,
    '''        if projected_scaleway_tokens > monthly_cap:\n            return "scaleway_monthly_token_cap_exceeded"\n        if projected_scaleway_tokens > hard_stop_cap:\n            return "scaleway_hard_stop_token_cap_exceeded"\n''',
    '''        if projected_scaleway_tokens > monthly_cap or (\n            is_availability_projection and projected_scaleway_tokens >= monthly_cap\n        ):\n            return "scaleway_monthly_token_cap_exceeded"\n        if projected_scaleway_tokens > hard_stop_cap or (\n            is_availability_projection and projected_scaleway_tokens >= hard_stop_cap\n        ):\n            return "scaleway_hard_stop_token_cap_exceeded"\n''',
    "scaleway cap blocker",
)

text = replace_once(
    text,
    '''    if (\n        provider.monthly_token_cap > 0\n        and projected_provider_tokens > provider.monthly_token_cap\n    ):\n        return "provider_monthly_token_cap_exceeded"\n''',
    '''    if provider.monthly_token_cap > 0 and (\n        projected_provider_tokens > provider.monthly_token_cap\n        or (\n            is_availability_projection\n            and projected_provider_tokens >= provider.monthly_token_cap\n        )\n    ):\n        return "provider_monthly_token_cap_exceeded"\n''',
    "provider token blocker",
)

text = replace_once(
    text,
    '''    if (\n        provider.monthly_cost_cap_usd > 0\n        and projected_provider_cost > provider.monthly_cost_cap_usd\n    ):\n        return "provider_monthly_cost_cap_exceeded"\n''',
    '''    if provider.monthly_cost_cap_usd > 0 and (\n        projected_provider_cost > provider.monthly_cost_cap_usd\n        or (\n            is_availability_projection\n            and projected_provider_cost >= provider.monthly_cost_cap_usd\n        )\n    ):\n        return "provider_monthly_cost_cap_exceeded"\n''',
    "provider cost blocker",
)

egress_path.write_text(text, encoding="utf-8")

test_path = Path("backend/tests/test_provider_settings.py")
tests = test_path.read_text(encoding="utf-8")
marker = "def test_read_availability_honors_configured_spend_floor_124("
if marker in tests:
    raise RuntimeError("bounded 124 repair tests already present")

tests += '''\n\n\ndef _set_availability_settings_124(**values: object) -> None:\n    from app.core.database import open_sqlite_connection\n\n    allowed = {\n        "policy_mode",\n        "paid_ai_enabled",\n        "monthly_api_budget_usd",\n        "api_spend_month_to_date_usd",\n        "provider_mode",\n        "scaleway_enabled",\n        "scaleway_monthly_token_cap",\n        "scaleway_hard_stop_token_cap",\n        "scaleway_input_tokens_month_to_date",\n        "scaleway_output_tokens_month_to_date",\n    }\n    assert values and set(values) <= allowed\n    assignments = ", ".join(f"{name} = ?" for name in values)\n    with open_sqlite_connection() as connection:\n        connection.execute(\n            f"UPDATE ai_settings SET {assignments} WHERE id = 'default'",\n            tuple(values.values()),\n        )\n        connection.commit()\n\n\ndef test_unknown_provider_availability_fails_closed_124(client: TestClient) -> None:\n    from app.modules.ai.egress_persistence import project_egress_availability\n\n    projection = project_egress_availability("definitely-unknown-provider")\n    assert projection.available is False\n    assert projection.blocking_reason == "provider_unknown"\n\n\ndef test_read_availability_honors_configured_spend_floor_124(\n    client: TestClient,\n    monkeypatch: pytest.MonkeyPatch,\n) -> None:\n    from app.modules.ai import egress_persistence\n\n    _set_availability_settings_124(\n        policy_mode="FAST_DEV",\n        paid_ai_enabled=1,\n        monthly_api_budget_usd=5.0,\n        api_spend_month_to_date_usd=5.0,\n    )\n    monkeypatch.setattr(\n        egress_persistence,\n        "resolve_secret_ref",\n        lambda ref: SimpleNamespace(key_present=True),\n    )\n    monkeypatch.setattr(\n        egress_persistence,\n        "_budget_snapshot",\n        lambda *args, **kwargs: _snapshot(global_actual=1.25),\n    )\n\n    projection = egress_persistence.project_egress_availability("deepseek")\n    assert projection.global_actual_cost_usd == 1.25\n    assert projection.available is False\n    assert projection.blocking_reason == "global_monthly_cost_cap_exceeded"\n\n\ndef test_read_availability_blocks_exact_provider_caps_124(\n    client: TestClient,\n    monkeypatch: pytest.MonkeyPatch,\n) -> None:\n    from app.modules.ai import egress_persistence\n    from app.modules.ai.provider_registry import load_default_provider_registry\n\n    _set_availability_settings_124(\n        policy_mode="FAST_DEV",\n        paid_ai_enabled=1,\n        monthly_api_budget_usd=1000.0,\n        api_spend_month_to_date_usd=0.0,\n    )\n    monkeypatch.setattr(\n        egress_persistence,\n        "resolve_secret_ref",\n        lambda ref: SimpleNamespace(key_present=True),\n    )\n    provider = load_default_provider_registry().providers["deepseek"]\n\n    monkeypatch.setattr(\n        egress_persistence,\n        "_budget_snapshot",\n        lambda *args, **kwargs: _snapshot(provider_tokens=provider.monthly_token_cap),\n    )\n    token_projection = egress_persistence.project_egress_availability("deepseek")\n    assert token_projection.blocking_reason == "provider_monthly_token_cap_exceeded"\n\n    monkeypatch.setattr(\n        egress_persistence,\n        "_budget_snapshot",\n        lambda *args, **kwargs: _snapshot(provider_cost=provider.monthly_cost_cap_usd),\n    )\n    cost_projection = egress_persistence.project_egress_availability("deepseek")\n    assert cost_projection.blocking_reason == "provider_monthly_cost_cap_exceeded"\n\n\ndef test_read_availability_blocks_exact_scaleway_caps_124(\n    client: TestClient,\n    monkeypatch: pytest.MonkeyPatch,\n) -> None:\n    from app.modules.ai import egress_persistence\n\n    _set_availability_settings_124(\n        policy_mode="FAST_DEV",\n        paid_ai_enabled=1,\n        monthly_api_budget_usd=1000.0,\n        api_spend_month_to_date_usd=0.0,\n        provider_mode="scaleway",\n        scaleway_enabled=1,\n        scaleway_monthly_token_cap=10,\n        scaleway_hard_stop_token_cap=20,\n        scaleway_input_tokens_month_to_date=0,\n        scaleway_output_tokens_month_to_date=0,\n    )\n    monkeypatch.setattr(\n        egress_persistence,\n        "resolve_secret_ref",\n        lambda ref: SimpleNamespace(key_present=True),\n    )\n    monkeypatch.setattr(\n        egress_persistence,\n        "_budget_snapshot",\n        lambda *args, **kwargs: _snapshot(provider_tokens=10),\n    )\n    monthly_projection = egress_persistence.project_egress_availability("scaleway")\n    assert monthly_projection.blocking_reason == "scaleway_monthly_token_cap_exceeded"\n\n    _set_availability_settings_124(\n        scaleway_monthly_token_cap=20,\n        scaleway_hard_stop_token_cap=10,\n    )\n    hard_stop_projection = egress_persistence.project_egress_availability("scaleway")\n    assert hard_stop_projection.blocking_reason == "scaleway_hard_stop_token_cap_exceeded"\n\n\ndef test_disabled_policy_blocks_credential_free_providers_124(client: TestClient) -> None:\n    from app.modules.ai.egress_persistence import project_egress_availability\n\n    _set_availability_settings_124(policy_mode="DISABLED")\n    for provider_id in ("fake", "local_ollama"):\n        projection = project_egress_availability(provider_id)\n        assert projection.available is False\n        assert projection.blocking_reason == "ai_policy_disabled"\n'''

test_path.write_text(tests, encoding="utf-8")
