from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.modules.ai import sensitivity
from app.modules.ai.contracts import AIPolicyMode, AIProviderAdapter
from app.modules.ai.egress_policy import EgressPolicyConfig, load_default_egress_policy
from app.modules.ai.egress_sanitizer import (
    PromptDerivative,
    create_prompt_derivative,
    get_prompt_derivative,
    resolve_approved_prompt_derivative,
)
from app.modules.ai.egress_service import EgressContractError, canonical_json, sha256_text

_AUTHORITY_RESULTS = frozenset({"eligible", "pause", "deny"})
_LOCAL_SANITIZER_VERSION = "prompt-local-sanitizer-v1"
_LOCAL_SANITIZER_TEMPLATE = (
    "Rewrite the task so it contains no project identity, confidential detail, "
    "proprietary geometry, unpublished parameter, credential, or secret. Preserve only "
    "the generic technical question. Return only the rewritten task, without commentary."
)
_LEVEL_RANK = {"S0": 0, "S1": 1}


@dataclass(frozen=True)
class PromptAuthority:
    result: str
    reason_code: str
    task_kind: str
    raw_prompt_digest: str
    prompt_level: str | None
    effective_prompt: str | None = field(default=None, repr=False)
    prompt_derivative_id: str | None = None
    prompt_derivative_digest: str | None = None
    classification_source: str | None = None
    sanitizer_kind: str | None = None
    sanitizer_version: str | None = None
    sanitizer_config_digest: str | None = None
    sanitizer_ai_job_id: str | None = None

    def __post_init__(self) -> None:
        if self.result not in _AUTHORITY_RESULTS:
            raise ValueError(f"unsupported prompt authority result: {self.result}")
        if self.result == "eligible":
            if self.effective_prompt is None or self.prompt_level not in {"S0", "S1"}:
                raise ValueError("eligible prompt authority requires an S0/S1 prompt")
        elif self.effective_prompt is not None:
            raise ValueError("non-eligible prompt authority must not expose a prompt body")


@dataclass(frozen=True)
class ManualContextAuthority:
    result: str
    reason_code: str
    context_level: str | None
    context_digest: str | None
    included_manifest: tuple[dict[str, Any], ...]
    withheld_manifest: tuple[dict[str, Any], ...]
    budget_dropped_manifest: tuple[dict[str, Any], ...]
    source_digests: tuple[tuple[str, str], ...]
    blocks: tuple[dict[str, Any], ...] = field(repr=False)

    def __post_init__(self) -> None:
        if self.result not in _AUTHORITY_RESULTS:
            raise ValueError(f"unsupported context authority result: {self.result}")
        if self.result == "eligible":
            if self.context_level not in {"S0", "S1"}:
                raise ValueError("eligible context authority requires S0/S1")
        elif self.blocks:
            raise ValueError("non-eligible context authority must not expose context bodies")


def authorize_prompt(
    *,
    raw_prompt: str,
    task_kind: str,
    policy_mode: AIPolicyMode | str,
    workspace_id: str | None = None,
    local_sanitizer_route: str | None = None,
    adapters: dict[str, AIProviderAdapter] | None = None,
    policy: EgressPolicyConfig | None = None,
) -> PromptAuthority:
    """Resolve one exact prompt into an external-eligible body or fail closed.

    S4 input is never sent to a sanitizer. S2/S3 input may use an already-approved
    prompt derivative or one explicit local-only sanitizer attempt. Ordinary marker-free
    input is treated as S1 only in FAST_DEV mode.
    """

    policy = policy or load_default_egress_policy()
    raw_prompt = _bounded_exact_text(raw_prompt, "raw_prompt", policy.max_prompt_chars)
    task_kind = _required_text(task_kind, "task_kind")
    raw_digest = sha256_text(raw_prompt)
    floor = sensitivity.deterministic_floor(raw_prompt)

    if floor == "S4":
        return PromptAuthority(
            result="deny",
            reason_code="prompt_secret_detected",
            task_kind=task_kind,
            raw_prompt_digest=raw_digest,
            prompt_level="S4",
            classification_source="deterministic_floor",
        )

    if floor in {"S2", "S3"}:
        derivative = resolve_approved_prompt_derivative(
            raw_prompt=raw_prompt,
            workspace_id=workspace_id,
            policy=policy,
        )
        if derivative is None and local_sanitizer_route is not None:
            derivative = sanitize_prompt_with_local_model(
                raw_prompt=raw_prompt,
                task_kind=task_kind,
                workspace_id=workspace_id,
                route_class=local_sanitizer_route,
                adapters=adapters,
                policy=policy,
            )
        if derivative is None:
            return PromptAuthority(
                result="pause",
                reason_code="prompt_sanitization_required",
                task_kind=task_kind,
                raw_prompt_digest=raw_digest,
                prompt_level=floor,
                classification_source="deterministic_floor",
            )
        return _prompt_authority_from_derivative(
            raw_digest=raw_digest,
            task_kind=task_kind,
            derivative=derivative,
        )

    if _policy_mode_value(policy_mode) != AIPolicyMode.FAST_DEV.value:
        return PromptAuthority(
            result="pause",
            reason_code="prompt_classification_required",
            task_kind=task_kind,
            raw_prompt_digest=raw_digest,
            prompt_level=None,
            classification_source="unclassified",
        )

    return PromptAuthority(
        result="eligible",
        reason_code="prompt_fast_dev_default_s1",
        task_kind=task_kind,
        raw_prompt_digest=raw_digest,
        prompt_level="S1",
        effective_prompt=raw_prompt,
        classification_source="fast_dev_default",
    )


def sanitize_prompt_with_local_model(
    *,
    raw_prompt: str,
    task_kind: str,
    route_class: str = "local:fast",
    workspace_id: str | None = None,
    adapters: dict[str, AIProviderAdapter] | None = None,
    policy: EgressPolicyConfig | None = None,
) -> PromptDerivative:
    """Run exactly one registry-owned local sanitizer binding through run_ai_task."""

    policy = policy or load_default_egress_policy()
    raw_prompt = _bounded_exact_text(raw_prompt, "raw_prompt", policy.max_prompt_chars)
    task_kind = _required_text(task_kind, "task_kind")
    route_class = _required_text(route_class, "route_class")
    floor = sensitivity.deterministic_floor(raw_prompt)
    if floor == "S4":
        raise sensitivity.SensitivityPolicyError(
            "Secret-bearing raw prompts cannot enter model-backed sanitization."
        )
    if floor not in {"S2", "S3"}:
        raise sensitivity.SensitivityPolicyError(
            "Model-backed prompt sanitization is only valid for S2/S3 input."
        )
    if not route_class.startswith("local:"):
        raise sensitivity.SensitivityPolicyError(
            "Model-backed sanitizer route must be explicitly local."
        )

    from app.modules.ai.execution import resolve_binding, run_ai_task

    binding, decision = resolve_binding(route_class)
    if binding is None:
        raise sensitivity.SensitivityPolicyError(
            f"Local sanitizer route is unavailable: {decision.blocked_reason or 'unbound'}"
        )
    if binding.requires_network:
        raise sensitivity.SensitivityPolicyError(
            "Model-backed sanitizer binding must not require network access."
        )

    sanitizer_input = (
        f"{_LOCAL_SANITIZER_TEMPLATE}\n\n"
        f"TASK_KIND: {task_kind}\n"
        "RAW_TASK_BEGIN\n"
        f"{raw_prompt}\n"
        "RAW_TASK_END"
    )
    config_digest = sha256_text(
        canonical_json(
            {
                "egress_config_digest": policy.config_digest,
                "route_class": route_class,
                "template": _LOCAL_SANITIZER_TEMPLATE,
                "version": _LOCAL_SANITIZER_VERSION,
            }
        )
    )

    outcome = run_ai_task(
        user_prompt=sanitizer_input,
        task_kind="synthesis",
        route_class=route_class,
        context_blocks=None,
        max_output_tokens=min(256, binding.max_output_tokens),
        adapters=adapters,
        bindings={route_class: binding},
        workspace_id=workspace_id,
    )
    response = outcome.response
    if outcome.status != "success" or response is None or response.text is None:
        raise sensitivity.SensitivityPolicyError(
            f"Local sanitizer failed: {outcome.error_type or outcome.status}"
        )
    if (
        outcome.selected_route_class != route_class
        or response.provider_id != binding.provider_id
        or response.model_id != binding.model_id
    ):
        raise sensitivity.SensitivityPolicyError(
            "Local sanitizer response binding does not match the selected local route."
        )

    derivative_content = _bounded_exact_text(
        response.text,
        "sanitizer_output",
        policy.max_prompt_chars,
    )
    surviving_floor = sensitivity.deterministic_floor(derivative_content)
    if surviving_floor is not None:
        raise sensitivity.SensitivityPolicyError(
            "Local sanitizer output remains external-ineligible at deterministic floor "
            f"{surviving_floor}."
        )

    approval = create_prompt_derivative(
        raw_prompt=raw_prompt,
        derivative_content=derivative_content,
        final_level="S1",
        transformations=[
            "local_model_generic_rewrite",
            "deterministic_post_scan",
        ],
        sanitizer_kind="model_local",
        sanitizer_version=_LOCAL_SANITIZER_VERSION,
        sanitizer_config_digest=config_digest,
        sanitizer_ai_job_id=outcome.ledger_id,
        workspace_id=workspace_id,
        policy=policy,
    )
    return get_prompt_derivative(
        approval.derivative_id,
        workspace_id=workspace_id,
    )


def authorize_manual_context(
    *,
    workspace_id: str,
    raw_blocks: list[dict[str, Any]],
    budget_chars: int,
) -> ManualContextAuthority:
    """Accept only exact current 059a derivative blocks as manual external context."""

    workspace_id = _required_text(workspace_id, "workspace_id")
    if isinstance(budget_chars, bool) or not isinstance(budget_chars, int) or budget_chars <= 0:
        raise EgressContractError("budget_chars must be a positive integer")

    preview = sensitivity.preview_manual_context(
        workspace_id,
        raw_blocks,
        budget_chars,
    )
    included_manifest = tuple(preview.included_sources_manifest)
    withheld_manifest = tuple(preview.withheld_sources_manifest)
    dropped_manifest = tuple(preview.dropped_sources_manifest)

    if preview.withheld_count:
        return ManualContextAuthority(
            result="pause",
            reason_code="manual_context_not_authorized",
            context_level=None,
            context_digest=None,
            included_manifest=included_manifest,
            withheld_manifest=withheld_manifest,
            budget_dropped_manifest=dropped_manifest,
            source_digests=(),
            blocks=(),
        )

    source_digests: dict[str, str] = {}
    levels: list[str] = []
    for manifest in included_manifest:
        derivative_id = manifest.get("derivative_id")
        if not isinstance(derivative_id, str) or not derivative_id:
            raise sensitivity.SensitivityPolicyError(
                "Manual external context must resolve only to approved derivatives."
            )
        derivative = sensitivity.get_sanitized_derivative(
            workspace_id,
            derivative_id,
        )
        if (
            derivative.status != "approved"
            or derivative.content_digest != manifest.get("content_digest")
            or derivative.effective_level != manifest.get("effective_level")
        ):
            raise sensitivity.SensitivityPolicyError(
                "Manual derivative authority changed after preview."
            )
        for source_ref, digest in derivative.source_digests.items():
            prior = source_digests.get(source_ref)
            if prior is not None and prior != digest:
                raise sensitivity.SensitivityPolicyError(
                    "Manual derivative source digests conflict."
                )
            source_digests[source_ref] = digest
        levels.append(derivative.effective_level)

    context_level = max(levels, key=_LEVEL_RANK.__getitem__) if levels else "S0"
    return ManualContextAuthority(
        result="eligible",
        reason_code="manual_context_eligible",
        context_level=context_level,
        context_digest=preview.context_digest,
        included_manifest=included_manifest,
        withheld_manifest=withheld_manifest,
        budget_dropped_manifest=dropped_manifest,
        source_digests=tuple(sorted(source_digests.items())),
        blocks=tuple(preview.blocks),
    )


def _prompt_authority_from_derivative(
    *,
    raw_digest: str,
    task_kind: str,
    derivative: PromptDerivative,
) -> PromptAuthority:
    if derivative.status != "approved" or derivative.final_level not in {"S0", "S1"}:
        raise sensitivity.SensitivityPolicyError(
            "Prompt derivative is not current external-eligible authority."
        )
    return PromptAuthority(
        result="eligible",
        reason_code="prompt_approved_derivative",
        task_kind=task_kind,
        raw_prompt_digest=raw_digest,
        prompt_level=derivative.final_level,
        effective_prompt=derivative.derivative_content,
        prompt_derivative_id=derivative.id,
        prompt_derivative_digest=derivative.derivative_digest,
        classification_source="approved_derivative",
        sanitizer_kind=derivative.sanitizer_kind,
        sanitizer_version=derivative.sanitizer_version,
        sanitizer_config_digest=derivative.sanitizer_config_digest,
        sanitizer_ai_job_id=derivative.sanitizer_ai_job_id,
    )


def _policy_mode_value(value: AIPolicyMode | str) -> str:
    if isinstance(value, AIPolicyMode):
        return value.value
    if not isinstance(value, str):
        raise EgressContractError("policy_mode must be text")
    cleaned = value.strip()
    if cleaned not in {mode.value for mode in AIPolicyMode}:
        raise EgressContractError("unsupported policy_mode")
    return cleaned


def _bounded_exact_text(value: str, field_name: str, maximum: int) -> str:
    if not isinstance(value, str) or not value.strip():
        raise EgressContractError(f"{field_name} must be non-empty text")
    if len(value) > maximum:
        raise EgressContractError(f"{field_name} exceeds configured character cap")
    return value


def _required_text(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise EgressContractError(f"{field_name} must be non-empty text")
    return value.strip()
