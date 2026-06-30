"""POS-1 — minimal positive AI execution spine.

run_ai_task resolves a route_class to a provider binding, executes through the
provider-neutral adapter interface (contracts.AIProviderAdapter), and writes one
ai_jobs ledger row per attempt — success AND pre-provider failure (malformed
route, unbound route, missing config/credentials).

Deliberately NOT here (later slices): economic routing, LLM judge/grading,
retrieval/domain-DB context injection, broad route catalog, provider SDKs beyond
the existing Scaleway/fake paths. The ledger stores only digests + metadata,
never prompt/output content or any secret.
"""

from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass
from uuid import uuid4

from app.core.database import open_sqlite_connection
from app.modules.ai.context_builder import (
    DEFAULT_CONTEXT_BUDGET_CHARS,
    ContextBlockError,
    assemble_prompt,
    canonical_digest,
    canonicalize_blocks,
    context_sources_manifest,
)
from app.modules.ai.contracts import (
    AIProviderAdapter,
    AIRequest,
    AIResponse,
    AITaskType,
    RoutingDecision,
)
from app.modules.ai.providers.fake_adapter import FAKE_PROVIDER_ID, FakeProviderAdapter
from app.modules.ai.providers.scaleway_adapter import (
    SCALEWAY_PROVIDER_ID,
    ScalewayProviderAdapter,
)
from app.modules.events.service import utc_now

ROUTE_CLASS_RE = re.compile(r"^[a-z][a-z0-9_]*:[a-z][a-z0-9_]*$")


@dataclass(frozen=True)
class ProviderBinding:
    route_class: str
    provider_id: str
    model_id: str
    requires_network: bool
    max_output_tokens: int


@dataclass
class AiTaskOutcome:
    status: str  # success | provider_error | route_unavailable | validation_error | config_error
    ledger_id: str
    selected_route_class: str | None
    decision: RoutingDecision
    response: AIResponse | None = None
    error_type: str | None = None
    context_digest: str | None = None
    context_sources_count: int = 0


# task_kind -> default route. Cloud calls must be opted into explicitly through
# route_class so task selection cannot silently spend tokens.
TASK_KIND_DEFAULT_ROUTE: dict[str, str] = {
    "general": "local:fake",
    "test": "local:fake",
    "synthesis": "local:fake",
    "code_review": "local:fake",
    "architecture_review": "local:fake",
}

_TASK_KIND_TO_AI_TASK_TYPE: dict[str, AITaskType] = {
    "code_review": AITaskType.code_review,
    "architecture_review": AITaskType.code_review,
    "synthesis": AITaskType.synthesis,
    "decision_support": AITaskType.decision_support,
}


def _default_bindings() -> dict[str, ProviderBinding]:
    """Bindings are config-driven (env), not scattered runtime constants."""
    return {
        "local:fake": ProviderBinding(
            "local:fake", FAKE_PROVIDER_ID, os.getenv("AI_ROUTE_FAKE_MODEL", "fake-deterministic-v1"), False, 256
        ),
        "external:cheap": ProviderBinding(
            "external:cheap",
            SCALEWAY_PROVIDER_ID,
            os.getenv("AI_ROUTE_CHEAP_MODEL", os.getenv("SCALEWAY_MODEL", "llama-3.1-8b-instruct")),
            True,
            512,
        ),
        "external:reasoning": ProviderBinding(
            "external:reasoning",
            SCALEWAY_PROVIDER_ID,
            os.getenv("AI_ROUTE_REASONING_MODEL", "qwen3-235b-a22b-instruct-2507"),
            True,
            1024,
        ),
    }


def _default_adapters() -> dict[str, AIProviderAdapter]:
    return {FAKE_PROVIDER_ID: FakeProviderAdapter(), SCALEWAY_PROVIDER_ID: ScalewayProviderAdapter()}


def resolve_binding(
    route_class: str, bindings: dict[str, ProviderBinding] | None = None
) -> tuple[ProviderBinding | None, RoutingDecision]:
    table = bindings if bindings is not None else _default_bindings()
    if not ROUTE_CLASS_RE.match(route_class):
        return None, RoutingDecision(
            blocked=True,
            blocked_reason="route_class_malformed",
            decision_reason=f"route_class '{route_class}' is not namespace:name",
        )
    binding = table.get(route_class)
    if binding is None:
        return None, RoutingDecision(
            blocked=True,
            blocked_reason="route_unavailable",
            decision_reason=f"no binding configured for {route_class}",
            considered_models=sorted(table),
        )
    return binding, RoutingDecision(
        provider_id=binding.provider_id, model_id=binding.model_id, decision_reason=f"bound:{route_class}"
    )


def _scaleway_ready() -> bool:
    from app.modules.secrets.storage import get_effective_scaleway_api_key

    return get_effective_scaleway_api_key().key_present


def _ai_task_type_for(task_kind: str) -> AITaskType:
    return _TASK_KIND_TO_AI_TASK_TYPE.get(task_kind, AITaskType.synthesis)


def _elapsed_ms(started: float) -> int:
    return int((time.perf_counter() - started) * 1000)


def _write_ai_job(
    *,
    status: str,
    task_kind: str,
    requested_route_class: str | None,
    selected_route_class: str | None,
    decision: RoutingDecision,
    prompt_digest: str | None,
    context_digest: str | None,
    context_sources: list[dict] | None,
    response: AIResponse | None,
    latency_ms: int,
    error_type: str | None,
) -> str:
    job_id = str(uuid4())
    provider_id = response.provider_id if response is not None else decision.provider_id
    model_id = response.model_id if response is not None else decision.model_id
    output_digest = (
        canonical_digest({"text": response.text}) if response is not None and response.text is not None else None
    )
    input_tokens = response.usage.input_tokens if response is not None else None
    output_tokens = response.usage.output_tokens if response is not None else None
    cost_estimate = response.usage.provider_cost_estimate if response is not None else None
    route_reason_json = json.dumps(
        {"decision_reason": decision.decision_reason, "blocked_reason": decision.blocked_reason}
    )
    context_sources_json = json.dumps(context_sources) if context_sources else None
    with open_sqlite_connection() as connection:
        connection.execute(
            """
            INSERT INTO ai_jobs (
                id, created_at, status, task_kind, requested_route_class, selected_route_class,
                provider_id, model_id, route_reason_json, prompt_digest, context_digest,
                context_sources_json, output_digest, input_tokens, output_tokens, cost_estimate,
                latency_ms, error_type
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                job_id,
                utc_now(),
                status,
                task_kind,
                requested_route_class,
                selected_route_class,
                provider_id,
                model_id,
                route_reason_json,
                prompt_digest,
                context_digest,
                context_sources_json,
                output_digest,
                input_tokens,
                output_tokens,
                cost_estimate,
                latency_ms,
                error_type,
            ),
        )
        connection.commit()
    return job_id


def _config_reason(adapter: AIProviderAdapter | None, binding: ProviderBinding, effective_max: int | None) -> str:
    if adapter is None:
        return f"no adapter registered for provider {binding.provider_id}"
    if binding.requires_network and effective_max is None:
        return "max_output_tokens required for network route"
    return f"provider {binding.provider_id} not configured (missing credentials)"


def run_ai_task(
    *,
    user_prompt: str,
    task_kind: str = "general",
    route_class: str | None = None,
    context_blocks: list[dict[str, object]] | None = None,
    max_output_tokens: int | None = None,
    adapters: dict[str, AIProviderAdapter] | None = None,
    bindings: dict[str, ProviderBinding] | None = None,
    external_blocked_reason: str | None = None,
    context_build_error: str | None = None,
) -> AiTaskOutcome:
    started = time.perf_counter()
    adapters = adapters if adapters is not None else _default_adapters()
    requested_route_class = route_class
    selected_route_class = route_class or TASK_KIND_DEFAULT_ROUTE.get(task_kind, "local:fake")
    prompt_digest = canonical_digest({"prompt": user_prompt})

    # Context assembly upstream (e.g. workspace builder) failed: fail closed before
    # any provider call and record it. No partial/uncontexted call is made.
    if context_build_error is not None:
        bad = RoutingDecision(
            blocked=True, blocked_reason="context_build_error", decision_reason=context_build_error
        )
        ledger_id = _write_ai_job(
            status="config_error",
            task_kind=task_kind,
            requested_route_class=requested_route_class,
            selected_route_class=selected_route_class,
            decision=bad,
            prompt_digest=prompt_digest,
            context_digest=None,
            context_sources=None,
            response=None,
            latency_ms=_elapsed_ms(started),
            error_type="context_build_error",
        )
        return AiTaskOutcome("config_error", ledger_id, selected_route_class, bad, error_type="context_build_error")

    # Normalize + budget context in the spine (not only the HTTP layer) so direct
    # and script callers cannot bypass it. Fail closed before any provider call.
    try:
        blocks = canonicalize_blocks(context_blocks)
    except ContextBlockError as exc:
        bad = RoutingDecision(blocked=True, blocked_reason="context_malformed", decision_reason=str(exc))
        ledger_id = _write_ai_job(
            status="validation_error",
            task_kind=task_kind,
            requested_route_class=requested_route_class,
            selected_route_class=selected_route_class,
            decision=bad,
            prompt_digest=prompt_digest,
            context_digest=None,
            context_sources=None,
            response=None,
            latency_ms=_elapsed_ms(started),
            error_type="context_malformed",
        )
        return AiTaskOutcome("validation_error", ledger_id, selected_route_class, bad, error_type="context_malformed")

    serialized_context_len = (
        len(json.dumps(blocks, sort_keys=True, separators=(",", ":"), ensure_ascii=False)) if blocks else 0
    )
    if serialized_context_len > DEFAULT_CONTEXT_BUDGET_CHARS:
        bad = RoutingDecision(
            blocked=True,
            blocked_reason="context_budget_exceeded",
            decision_reason=f"context {serialized_context_len} chars exceeds budget {DEFAULT_CONTEXT_BUDGET_CHARS}",
        )
        ledger_id = _write_ai_job(
            status="validation_error",
            task_kind=task_kind,
            requested_route_class=requested_route_class,
            selected_route_class=selected_route_class,
            decision=bad,
            prompt_digest=prompt_digest,
            context_digest=None,
            context_sources=None,
            response=None,
            latency_ms=_elapsed_ms(started),
            error_type="context_budget_exceeded",
        )
        return AiTaskOutcome(
            "validation_error", ledger_id, selected_route_class, bad, error_type="context_budget_exceeded"
        )

    context_digest = canonical_digest(blocks) if blocks else None
    context_sources = context_sources_manifest(blocks) if blocks else None
    context_sources_count = len(context_sources) if context_sources else 0

    binding, decision = resolve_binding(selected_route_class, bindings)
    if binding is None:
        status = "validation_error" if decision.blocked_reason == "route_class_malformed" else "route_unavailable"
        ledger_id = _write_ai_job(
            status=status,
            task_kind=task_kind,
            requested_route_class=requested_route_class,
            selected_route_class=selected_route_class,
            decision=decision,
            prompt_digest=prompt_digest,
            context_digest=context_digest,
            context_sources=context_sources,
            response=None,
            latency_ms=_elapsed_ms(started),
            error_type=status,
        )
        return AiTaskOutcome(
            status,
            ledger_id,
            selected_route_class,
            decision,
            error_type=status,
            context_digest=context_digest,
            context_sources_count=context_sources_count,
        )

    adapter = adapters.get(binding.provider_id)
    effective_max = max_output_tokens if max_output_tokens is not None else None
    if not binding.requires_network and effective_max is None:
        effective_max = binding.max_output_tokens
    if binding.requires_network and external_blocked_reason is not None:
        config_decision = RoutingDecision(
            provider_id=binding.provider_id,
            model_id=binding.model_id,
            blocked=True,
            blocked_reason="config_error",
            decision_reason=f"external provider execution disabled by settings/gate: {external_blocked_reason}",
        )
        ledger_id = _write_ai_job(
            status="config_error",
            task_kind=task_kind,
            requested_route_class=requested_route_class,
            selected_route_class=selected_route_class,
            decision=config_decision,
            prompt_digest=prompt_digest,
            context_digest=context_digest,
            context_sources=context_sources,
            response=None,
            latency_ms=_elapsed_ms(started),
            error_type="config_error",
        )
        return AiTaskOutcome(
            "config_error",
            ledger_id,
            selected_route_class,
            config_decision,
            error_type="config_error",
            context_digest=context_digest,
            context_sources_count=context_sources_count,
        )

    not_ready_scaleway = (
        binding.provider_id == SCALEWAY_PROVIDER_ID and binding.requires_network and not _scaleway_ready()
    )
    if adapter is None or (binding.requires_network and effective_max is None) or not_ready_scaleway:
        config_decision = RoutingDecision(
            provider_id=binding.provider_id,
            model_id=binding.model_id,
            blocked=True,
            blocked_reason="config_error",
            decision_reason=_config_reason(adapter, binding, effective_max),
        )
        ledger_id = _write_ai_job(
            status="config_error",
            task_kind=task_kind,
            requested_route_class=requested_route_class,
            selected_route_class=selected_route_class,
            decision=config_decision,
            prompt_digest=prompt_digest,
            context_digest=context_digest,
            context_sources=context_sources,
            response=None,
            latency_ms=_elapsed_ms(started),
            error_type="config_error",
        )
        return AiTaskOutcome(
            "config_error",
            ledger_id,
            selected_route_class,
            config_decision,
            error_type="config_error",
            context_digest=context_digest,
            context_sources_count=context_sources_count,
        )

    request = AIRequest(
        task_type=_ai_task_type_for(task_kind),
        prompt=assemble_prompt(blocks, user_prompt),
        model_preference=binding.model_id,
        max_output_tokens=effective_max,
        metadata={"context_digest": context_digest, "selected_route_class": selected_route_class},
    )
    try:
        response = adapter.complete(request)
    except Exception as exc:  # adapter/provider raised before/within the call
        err_decision = RoutingDecision(
            provider_id=binding.provider_id, model_id=binding.model_id, decision_reason=f"bound:{selected_route_class}"
        )
        ledger_id = _write_ai_job(
            status="provider_error",
            task_kind=task_kind,
            requested_route_class=requested_route_class,
            selected_route_class=selected_route_class,
            decision=err_decision,
            prompt_digest=prompt_digest,
            context_digest=context_digest,
            context_sources=context_sources,
            response=None,
            latency_ms=_elapsed_ms(started),
            error_type=type(exc).__name__,
        )
        return AiTaskOutcome(
            "provider_error",
            ledger_id,
            selected_route_class,
            err_decision,
            error_type=type(exc).__name__,
            context_digest=context_digest,
            context_sources_count=context_sources_count,
        )

    if response.error is None and response.text is not None:
        status = "success"
        error_type = None
    else:
        status = "provider_error"
        error_type = response.error.code.value if response.error is not None else "empty_response"
    ledger_id = _write_ai_job(
        status=status,
        task_kind=task_kind,
        requested_route_class=requested_route_class,
        selected_route_class=selected_route_class,
        decision=decision,
        prompt_digest=prompt_digest,
        context_digest=context_digest,
        context_sources=context_sources,
        response=response,
        latency_ms=_elapsed_ms(started),
        error_type=error_type,
    )
    return AiTaskOutcome(
        status,
        ledger_id,
        selected_route_class,
        decision,
        response,
        error_type=error_type,
        context_digest=context_digest,
        context_sources_count=context_sources_count,
    )
