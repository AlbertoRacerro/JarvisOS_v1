from __future__ import annotations

from typing import Iterable


VALID_EXTERNAL_TARGETS = {
    "external:cheap",
    "external:scientific_medium",
    "external:frontier",
}


def _normalize_allowed_targets(allowed_targets: Iterable[str] | None) -> tuple[str, ...]:
    if allowed_targets is None:
        return ()
    normalized = []
    for value in allowed_targets:
        if value in VALID_EXTERNAL_TARGETS and value not in normalized:
            normalized.append(value)
    return tuple(sorted(normalized))


def evaluate_external_egress_scope(
    proposed_external_target: str | None,
    allowed_targets: set[str] | list[str] | tuple[str, ...] | None,
) -> dict[str, object]:
    """Evaluate deterministic egress scope for an already-proposed external target.

    This helper is intentionally pure and side-effect-free. It does not inspect
    environment variables, network state, provider registries, or model output.
    It only answers whether the provided target is contained in a deterministic
    allow-list.
    """

    normalized_allowed_targets = _normalize_allowed_targets(allowed_targets)

    if proposed_external_target is None:
        return {
            "allowed": False,
            "proposed_external_target": None,
            "normalized_allowed_targets": normalized_allowed_targets,
            "reason_code": "missing_target",
            "reason_codes": ["missing_target"],
        }

    if proposed_external_target not in VALID_EXTERNAL_TARGETS:
        return {
            "allowed": False,
            "proposed_external_target": proposed_external_target,
            "normalized_allowed_targets": normalized_allowed_targets,
            "reason_code": "invalid_target",
            "reason_codes": ["invalid_target"],
        }

    if proposed_external_target not in normalized_allowed_targets:
        return {
            "allowed": False,
            "proposed_external_target": proposed_external_target,
            "normalized_allowed_targets": normalized_allowed_targets,
            "reason_code": "target_not_in_allowed_targets",
            "reason_codes": ["target_not_in_allowed_targets"],
        }

    return {
        "allowed": True,
        "proposed_external_target": proposed_external_target,
        "normalized_allowed_targets": normalized_allowed_targets,
        "reason_code": "target_allowed",
        "reason_codes": [],
    }
