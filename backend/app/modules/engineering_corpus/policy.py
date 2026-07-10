from __future__ import annotations

from dataclasses import dataclass

ALWAYS_DENIED_ROLES = frozenset(
    {
        "benchmark_gold",
        "evaluator_log",
        "previous_model_answer",
        "private_gold",
    }
)
EVALUATION_DENIED_ROLES = ALWAYS_DENIED_ROLES | frozenset(
    {
        "answer_key",
        "solution",
        "solution_record",
    }
)


class CorpusPolicyError(ValueError):
    """Raised when a retrieval request violates a fail-closed corpus policy."""


@dataclass(frozen=True)
class RolePolicyDecision:
    requested_roles: tuple[str, ...]
    excluded_roles: tuple[str, ...]


def _normalize_roles(values: list[str] | tuple[str, ...] | set[str]) -> tuple[str, ...]:
    normalized: set[str] = set()
    for value in values:
        role = value.strip().lower()
        if not role:
            raise CorpusPolicyError("roles cannot contain blank values")
        normalized.add(role)
    return tuple(sorted(normalized))


def resolve_role_policy(
    *,
    requested_roles: list[str],
    excluded_roles: list[str],
    evaluation_mode: bool,
) -> RolePolicyDecision:
    requested = set(_normalize_roles(requested_roles))
    excluded = set(_normalize_roles(excluded_roles))
    denied = EVALUATION_DENIED_ROLES if evaluation_mode else ALWAYS_DENIED_ROLES

    forbidden_requests = requested & denied
    if forbidden_requests:
        roles = ", ".join(sorted(forbidden_requests))
        raise CorpusPolicyError(f"requested roles are forbidden in this mode: {roles}")

    excluded.update(denied)
    return RolePolicyDecision(
        requested_roles=tuple(sorted(requested)),
        excluded_roles=tuple(sorted(excluded)),
    )
