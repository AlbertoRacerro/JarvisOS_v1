SAFE_LOCAL_ROUTE_ACTIONS = {"answer_local", "route_local"}
SAFE_LOCAL_PROVIDERS = {"local:gemma", "local:qwen"}


def is_safe_local_execution(decision: dict) -> bool:
    """Return true only for validator-valid, no-side-effect LOCAL_FAST answers."""

    return all(
        (
            decision.get("route_action") in SAFE_LOCAL_ROUTE_ACTIONS,
            decision.get("route_tier") == "LOCAL_FAST",
            decision.get("provider_candidate") in SAFE_LOCAL_PROVIDERS,
            decision.get("response_allowed_now") is True,
            decision.get("external_allowed") is False,
            decision.get("provider_call_allowed_now") is False,
            decision.get("external_network_allowed_now") is False,
            decision.get("tool_execution_allowed_now") is False,
            decision.get("state_change_allowed_now") is False,
            decision.get("allowed_execution_mode") == "answer_only",
            decision.get("modifies_state") is False,
            decision.get("side_effect_level") == "none",
            decision.get("environment_type") == "chat",
        )
    )
