from __future__ import annotations

from decimal import Decimal, InvalidOperation

GRADE_BUCKETS = ("useful", "partly", "rework", "failed", "ungraded")
EXECUTION_CLASSES = (
    "none",
    "synthetic",
    "local_compute",
    "external_provider",
    "legacy_unknown",
)
DISPATCH_STATES = ("not_applicable", "not_started", "started", "unknown")
USAGE_SOURCES = ("actual", "mixed", "estimated", "none", "legacy_unknown")
ACCOUNTING_BASES = (
    "no_execution",
    "synthetic_not_economic",
    "local_compute_unpriced",
    "external_not_sent",
    "provider_exact",
    "conservative_standard_input",
    "conservative_estimated_usage",
    "legacy_unknown",
)
EXECUTION_COMPOSITIONS = (
    "no_adapter_execution",
    "synthetic_only",
    "local_compute_only",
    "external_provider_only",
    "mixed_executed_classes",
)
DISPATCH_QUALITY_BUCKETS = (
    "no_external_dispatch",
    "external_started_only",
    "external_unknown_present",
)
PROVIDER_QUALITY_BUCKETS = (
    "no_external_provider_consumption",
    "provider_exact_only",
    "conservative_only",
    "mixed_provider_basis",
)
NON_EMPIRICAL_TASK_KINDS = frozenset(
    {
        "internal",
        "sanitizer",
        "smoke_console",
        "smoke_test",
        "provider_smoke",
        "supervisor_public_test",
    }
)


def decimal_value(value: object) -> Decimal:
    if value is None:
        return Decimal("0")
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError("provider spend evidence is malformed") from exc
    if not result.is_finite() or result < 0:
        raise ValueError("provider spend evidence is malformed")
    return result


def decimal_text(value: Decimal) -> str:
    normalized = value.normalize()
    text = format(normalized, "f")
    return "0" if text in {"-0", ""} else text


def execution_composition(classes: set[str]) -> str:
    if "legacy_unknown" in classes:
        return "mixed_executed_classes"
    known = classes & {"synthetic", "local_compute", "external_provider"}
    if not known:
        return "no_adapter_execution"
    if known == {"synthetic"} and "legacy_unknown" not in classes:
        return "synthetic_only"
    if known == {"local_compute"} and "legacy_unknown" not in classes:
        return "local_compute_only"
    if known == {"external_provider"} and "legacy_unknown" not in classes:
        return "external_provider_only"
    return "mixed_executed_classes"


def dispatch_quality(states: set[str]) -> str:
    if "unknown" in states:
        return "external_unknown_present"
    if "started" in states:
        return "external_started_only"
    return "no_external_dispatch"


def provider_quality(rows: list[dict[str, object]]) -> str:
    consumed = [
        row
        for row in rows
        if row["external_dispatch_state"] in {"started", "unknown"}
    ]
    if not consumed:
        return "no_external_provider_consumption"
    bases = {str(row["accounting_basis"]) for row in consumed}
    exact = "provider_exact" in bases
    conservative = bool(
        bases
        & {
            "conservative_standard_input",
            "conservative_estimated_usage",
            "legacy_unknown",
            "None",
        }
    )
    if exact and not conservative:
        return "provider_exact_only"
    if conservative and not exact:
        return "conservative_only"
    return "mixed_provider_basis"


def exclusion_reasons(
    *,
    flow: dict[str, object],
    attempts: list[dict[str, object]],
    current_subject_id: str | None,
) -> list[str]:
    reasons: list[str] = []
    raw_classes = {row["execution_class"] for row in attempts}
    raw_bases = {row["accounting_basis"] for row in attempts}
    classes = {str(value) for value in raw_classes}
    if bool(flow["synthetic_evidence_present"]) or "synthetic" in classes:
        reasons.append("synthetic_evidence")
    if str(flow["task_kind"]) in NON_EMPIRICAL_TASK_KINDS:
        reasons.append("non_empirical_task_kind")
    if (
        any(value not in EXECUTION_CLASSES for value in raw_classes)
        or any(value not in ACCOUNTING_BASES for value in raw_bases)
        or "legacy_unknown" in raw_classes
        or "legacy_unknown" in raw_bases
    ):
        reasons.append("ambiguous_legacy_evidence")
    if not flow["final_accounting_digest"] or current_subject_id is None:
        reasons.append("incomplete_finalized_provenance")
    return reasons
