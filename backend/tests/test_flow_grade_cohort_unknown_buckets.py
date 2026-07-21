from __future__ import annotations

from app.modules.ai.flow_grade_cohorts import _bucket


def test_missing_and_unrecognized_values_use_explicit_fallback() -> None:
    allowed = {"actual": object(), "legacy_unknown": object()}

    assert _bucket(None, allowed, "legacy_unknown") == "legacy_unknown"
    assert _bucket("old_value", allowed, "legacy_unknown") == "legacy_unknown"
    assert _bucket("actual", allowed, "legacy_unknown") == "actual"
