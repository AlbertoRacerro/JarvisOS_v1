from dataclasses import dataclass

from app.core.database import open_sqlite_connection
from app.modules.ai.budget import evaluate_ai_status, evaluate_live_scaleway_smoke_gate
from app.modules.ai.contracts import AIPrivacyClass, AIRequest, AITaskType
from app.modules.ai.models import SmokeTestResponse, SmokeTestResult, SmokeTestTokenMetadata
from app.modules.ai.privacy import PrivacyPolicyEngine
from app.modules.ai.providers.fake import FakeModelingProvider
from app.modules.ai.providers.scaleway_adapter import SCALEWAY_ADAPTER_INTERFACE, ScalewayProviderAdapter
from app.modules.ai.settings import get_ai_settings, record_scaleway_token_usage
from app.modules.ai.token_guard import evaluate_token_guard, metadata_with_reported_usage
from app.modules.events.service import log_event


@dataclass(frozen=True)
class SmokeCase:
    case_id: str
    text: str
    expected_classes: tuple[str, ...]
    live_allowed: bool = False


SMOKE_CASES = [
    SmokeCase(
        "public_research_request",
        "Public research request: summarize published literature on algae photobioreactor mixing.",
        ("public", "internal"),
        True,
    ),
    SmokeCase(
        "generic_engineering_note",
        "Generic engineering note for rough sizing of a floating structure.",
        ("internal", "confidential"),
        True,
    ),
    SmokeCase(
        "smart_joint_geometry",
        "Smart Joint proprietary geometry with patent-like dimensions for a connector.",
        ("sensitive_ip",),
    ),
    SmokeCase(
        "api_key_example",
        "Example .env content: API key and password for a private service.",
        ("secret",),
    ),
    SmokeCase(
        "ambiguous_bluerev_brainstorming",
        "Ambiguous BlueRev brainstorming about a novel floating cultivation layout.",
        ("confidential", "sensitive_ip"),
    ),
]


def run_smoke_tests(provider_mode: str | None = None, smoke_mode: str = "synthetic") -> SmokeTestResponse:
    settings = get_ai_settings()
    mode = provider_mode or settings.provider_mode
    selected_smoke_mode = "live" if smoke_mode == "live" else "synthetic"
    fake_provider = FakeModelingProvider()
    scaleway_adapter = ScalewayProviderAdapter()
    scaleway_provider = scaleway_adapter.provider
    policy = PrivacyPolicyEngine()
    external_attempted = False
    external_succeeded = False

    _log_smoke_event(
        "AISmokeTestStarted",
        provider_mode=mode,
        smoke_mode=selected_smoke_mode,
        provider=_event_provider_for_mode(mode),
        model=_event_model_for_mode(mode, settings.default_ai_model, scaleway_provider.status().model),
        reason=None,
        external_call_attempted=False,
        external_call_succeeded=False,
    )

    results: list[SmokeTestResult] = []
    for case in SMOKE_CASES:
        if selected_smoke_mode == "synthetic" and mode == "fake":
            local_decision = policy.decide_for_external_smoke_test(
                case.text,
                confidential_allowed=settings.scaleway_smoke_test_enabled,
            )
            token_decision = evaluate_token_guard(settings, input_text=case.text)
            fake_class = fake_provider.classify_smoke_case(case.text)
            results.append(
                _result(
                    case,
                    provider_mode=mode,
                    smoke_mode=selected_smoke_mode,
                    provider="fake",
                    local_privacy_class=local_decision.privacy_class,
                    token_metadata=token_decision.metadata,
                    fake_classification=fake_class,
                    provider_reported_class=fake_class,
                    passed=fake_class in case.expected_classes,
                    blocking_reason=None,
                    external_call_attempted=False,
                    external_call_succeeded=False,
                    response_text=None,
                    provider_metadata={"implementation": "deterministic_fake"},
                )
            )
            continue

        if mode != "scaleway":
            local_decision = policy.decide_for_external_smoke_test(
                case.text,
                confidential_allowed=False,
            )
            token_decision = evaluate_token_guard(settings, input_text=case.text)
            reason = "scaleway_provider_mode_required" if selected_smoke_mode == "live" else "unsupported_provider_mode"
            results.append(
                _blocked_result(case, mode, selected_smoke_mode, reason, local_decision.privacy_class, token_decision.metadata)
            )
            continue

        if selected_smoke_mode == "live":
            gate_reason = evaluate_live_scaleway_smoke_gate(settings, mode)
            if gate_reason:
                local_decision = policy.decide_for_external_smoke_test(
                    case.text,
                    confidential_allowed=False,
                )
                token_decision = evaluate_token_guard(settings, input_text=case.text)
                results.append(
                    _blocked_result(case, mode, selected_smoke_mode, gate_reason, local_decision.privacy_class, token_decision.metadata)
                )
                continue

            local_decision = policy.decide_for_external_smoke_test(
                case.text,
                confidential_allowed=False,
            )
            token_decision = evaluate_token_guard(settings, input_text=case.text)

            if not local_decision.external_allowed:
                results.append(
                    _blocked_result(case, mode, selected_smoke_mode, local_decision.blocking_reason or "privacy_policy_blocked", local_decision.privacy_class, token_decision.metadata)
                )
                continue

            if not case.live_allowed:
                results.append(
                    _blocked_result(case, mode, selected_smoke_mode, "live_smoke_case_not_allowed", local_decision.privacy_class, token_decision.metadata)
                )
                continue

            if not token_decision.allowed:
                results.append(
                    _blocked_result(case, mode, selected_smoke_mode, token_decision.reason or "scaleway_monthly_token_cap_exceeded", local_decision.privacy_class, token_decision.metadata)
                )
                continue

            live_response = scaleway_adapter.complete(
                AIRequest(
                    task_type=AITaskType.smoke_test,
                    privacy_class=AIPrivacyClass(local_decision.privacy_class),
                    prompt=case.text,
                    model_preference=scaleway_provider.model(),
                    max_output_tokens=token_decision.metadata.estimated_output_tokens,
                    metadata={"case_id": case.case_id, "mode": selected_smoke_mode},
                )
            )
            live_attempted = bool(live_response.raw_provider_metadata.get("external_call_attempted", True))
            external_attempted = external_attempted or live_attempted
            if live_response.error:
                results.append(
                    _blocked_result(
                        case,
                        mode,
                        selected_smoke_mode,
                        live_response.blocked_reason or "scaleway_live_call_failed",
                        local_decision.privacy_class,
                        token_decision.metadata,
                        external_call_attempted=live_attempted,
                        provider_metadata=live_response.raw_provider_metadata,
                    )
                )
                continue

            external_succeeded = True
            usage_metadata = metadata_with_reported_usage(
                token_decision.metadata,
                reported_input_tokens=_reported_token(live_response.raw_provider_metadata.get("reported_input_tokens")),
                reported_output_tokens=_reported_token(live_response.raw_provider_metadata.get("reported_output_tokens")),
            )
            input_tokens_to_record = (
                usage_metadata.reported_input_tokens
                if usage_metadata.reported_input_tokens is not None
                else token_decision.metadata.estimated_input_tokens
            )
            output_tokens_to_record = (
                usage_metadata.reported_output_tokens
                if usage_metadata.reported_output_tokens is not None
                else token_decision.metadata.estimated_output_tokens
            )
            settings = record_scaleway_token_usage(
                input_tokens=input_tokens_to_record,
                output_tokens=output_tokens_to_record,
            )
            results.append(
                _result(
                    case,
                    provider_mode=mode,
                    smoke_mode=selected_smoke_mode,
                    provider=live_response.provider_id,
                    local_privacy_class=local_decision.privacy_class,
                    token_metadata=usage_metadata,
                    fake_classification=None,
                    provider_reported_class=None,
                    passed=True,
                    blocking_reason=None,
                    external_call_attempted=live_attempted,
                    external_call_succeeded=True,
                    response_text=live_response.text,
                    provider_metadata=live_response.raw_provider_metadata,
                )
            )
            continue

        status = evaluate_ai_status(settings, "scaleway")
        if status.blocking_reason and status.blocking_reason != "scaleway_provider_stub_no_external_call":
            local_decision = policy.decide_for_external_smoke_test(
                case.text,
                confidential_allowed=settings.scaleway_smoke_test_enabled,
            )
            token_decision = evaluate_token_guard(settings, input_text=case.text)
            results.append(
                _blocked_result(case, mode, selected_smoke_mode, status.blocking_reason, local_decision.privacy_class, token_decision.metadata)
            )
            continue

        local_decision = policy.decide_for_external_smoke_test(
            case.text,
            confidential_allowed=settings.scaleway_smoke_test_enabled,
        )
        token_decision = evaluate_token_guard(settings, input_text=case.text)

        if not local_decision.external_allowed:
            results.append(
                _blocked_result(case, mode, selected_smoke_mode, local_decision.blocking_reason or "privacy_policy_blocked", local_decision.privacy_class, token_decision.metadata)
            )
            continue

        if not token_decision.allowed:
            results.append(
                _blocked_result(case, mode, selected_smoke_mode, token_decision.reason or "scaleway_monthly_token_cap_exceeded", local_decision.privacy_class, token_decision.metadata)
            )
            continue

        provider_status = scaleway_provider.status()
        results.append(
            _blocked_result(
                case,
                mode,
                selected_smoke_mode,
                provider_status.implementation,
                local_decision.privacy_class,
                token_decision.metadata,
                provider_metadata={"implementation": provider_status.implementation},
            )
        )

    event_type = "AISmokeTestBlocked" if any(result.blocking_reason for result in results) and mode == "scaleway" else "AISmokeTestCompleted"
    _log_smoke_event(
        event_type,
        provider_mode=mode,
        smoke_mode=selected_smoke_mode,
        provider=_event_provider_for_mode(mode),
        model=_event_model_for_mode(mode, settings.default_ai_model, scaleway_provider.status().model),
        reason="blocked_results_present" if event_type == "AISmokeTestBlocked" else None,
        result_count=len(results),
        external_call_attempted=external_attempted,
        external_call_succeeded=external_succeeded,
        results=results,
    )
    return SmokeTestResponse(
        provider_mode=mode,
        smoke_mode=selected_smoke_mode,
        external_call_attempted=external_attempted,
        external_call_succeeded=external_succeeded,
        results=results,
    )


def _result(
    case: SmokeCase,
    *,
    provider_mode: str,
    smoke_mode: str,
    provider: str,
    local_privacy_class: str,
    token_metadata: SmokeTestTokenMetadata,
    fake_classification: str | None,
    provider_reported_class: str | None,
    passed: bool,
    blocking_reason: str | None,
    external_call_attempted: bool,
    external_call_succeeded: bool,
    response_text: str | None,
    provider_metadata: dict[str, object] | None,
) -> SmokeTestResult:
    return SmokeTestResult(
        case_id=case.case_id,
        input_excerpt=case.text[:120],
        expected_class="/".join(case.expected_classes),
        local_privacy_class=local_privacy_class,
        provider_reported_class=provider_reported_class,
        fake_classification=fake_classification,
        passed=passed,
        provider_mode=provider_mode,
        provider=provider,
        smoke_mode=smoke_mode,
        external_call_attempted=external_call_attempted,
        external_call_succeeded=external_call_succeeded,
        blocking_reason=blocking_reason,
        response_text=response_text,
        usage_source=token_metadata.usage_source,
        provider_metadata=provider_metadata,
        token_metadata=token_metadata,
    )


def _blocked_result(
    case: SmokeCase,
    provider_mode: str,
    smoke_mode: str,
    reason: str,
    local_privacy_class: str,
    token_metadata: SmokeTestTokenMetadata,
    external_call_attempted: bool = False,
    provider_metadata: dict[str, object] | None = None,
) -> SmokeTestResult:
    passed = reason.startswith("privacy_policy") and local_privacy_class in case.expected_classes
    return _result(
        case,
        provider_mode=provider_mode,
        smoke_mode=smoke_mode,
        provider=provider_mode,
        local_privacy_class=local_privacy_class,
        token_metadata=token_metadata,
        fake_classification=None,
        provider_reported_class=None,
        passed=passed,
        blocking_reason=reason,
        external_call_attempted=external_call_attempted,
        external_call_succeeded=False,
        response_text=None,
        provider_metadata=provider_metadata,
    )


def _reported_token(value: object) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _log_smoke_event(
    event_type: str,
    *,
    provider_mode: str,
    smoke_mode: str,
    provider: str,
    model: str,
    reason: str | None,
    result_count: int | None = None,
    external_call_attempted: bool,
    external_call_succeeded: bool,
    results: list[SmokeTestResult] | None = None,
) -> None:
    result_summary = [_event_result_summary(result) for result in results or []]
    with open_sqlite_connection() as connection:
        log_event(
            connection,
            event_type=event_type,
            actor="local-user",
            target_type="AISmokeTest",
            workspace_id=None,
            payload={
                "provider_mode": provider_mode,
                "mode": smoke_mode,
                "provider": provider,
                "provider_id": provider,
                "model": model,
                "model_id": model,
                "adapter_interface": SCALEWAY_ADAPTER_INTERFACE if provider == "scaleway" else None,
                "reason": reason,
                "result_count": result_count,
                "external_call_attempted": external_call_attempted,
                "external_call_succeeded": external_call_succeeded,
                "synthetic_only": smoke_mode == "synthetic",
                "results": result_summary,
            },
        )
        connection.commit()


def _event_result_summary(result: SmokeTestResult) -> dict[str, object]:
    provider_metadata = result.provider_metadata or {}
    return {
        "case_id": result.case_id,
        "provider": result.provider,
        "provider_id": result.provider,
        "provider_mode": result.provider_mode,
        "mode": result.smoke_mode,
        "adapter_interface": provider_metadata.get("adapter_interface"),
        "privacy_class": result.local_privacy_class,
        "blocked_reason": result.blocking_reason,
        "blocked_by_token_cap": result.token_metadata.blocked_by_token_cap,
        "estimated_input_tokens": result.token_metadata.estimated_input_tokens,
        "estimated_output_tokens": result.token_metadata.estimated_output_tokens,
        "reported_input_tokens": result.token_metadata.reported_input_tokens,
        "reported_output_tokens": result.token_metadata.reported_output_tokens,
        "usage_source": result.token_metadata.usage_source,
        "token_usage_month_to_date": result.token_metadata.token_usage_month_to_date,
        "external_call_attempted": result.external_call_attempted,
        "external_call_succeeded": result.external_call_succeeded,
    }


def _event_provider_for_mode(provider_mode: str) -> str:
    if provider_mode == "fake":
        return "fake"
    if provider_mode == "scaleway":
        return "scaleway"
    return "none"


def _event_model_for_mode(provider_mode: str, default_model: str, scaleway_model: str) -> str:
    if provider_mode == "fake":
        return default_model
    if provider_mode == "scaleway":
        return scaleway_model
    return "none"
