"""Deterministic unit coverage for spec 172's bounded dynamic contracts."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import TypeAdapter, ValidationError

from app.modules.process_stack.dynamic_models import Scenario, Schedule
from app.modules.process_stack.draft import apply_ops, content_digest, empty_document
from app.modules.process_stack.draft_models import DraftOp


def test_dynamic_draft_ops_are_semantic_and_legacy_documents_remain_valid() -> None:
    adapter = TypeAdapter(DraftOp)
    legacy = empty_document("legacy")
    legacy["objects"]["pbr"] = {"id": "pbr", "kind": "unit", "type": "PhotobioreactorT1", "tag": "PBR1",
                                 "x": 1, "y": 2}
    semantic = apply_ops(legacy, [adapter.validate_python(op) for op in (
        {"op": "set_schedule", "id": "feed", "value": {"events": []}},
        {"op": "set_controller", "id": "loop", "value": {"type": "pi", "measurement": "X",
                                                                   "unit": "PBR1", "actuator": "feed:Feed",
                                                                   "cadence_s": 60, "setpoint": 1}},
        {"op": "set_scenario", "id": "run", "value": {"units": ["PBR1"],
                                                             "profiles": [{"profile_id": "p", "digest": "d"}],
                                                             "start_utc": "2026-01-01T00:00:00Z",
                                                             "end_utc": "2026-01-01T01:00:00Z",
                                                             "output_cadence_s": 3600,
                                                             "temperature_source": "unit_mean",
                                                             "schedule_id": "feed", "controllers": ["loop"]}},
    )])
    assert legacy.get("schedules", {}) == {}
    assert semantic["schedules"]["feed"]["id"] == "feed"
    assert content_digest(semantic) != content_digest(legacy)
    moved = {**semantic, "objects": {"unit": {"kind": "unit", "tag": "PBR1", "x": 900, "y": -300}}}
    semantic_layout = {**semantic, "objects": {"unit": {"kind": "unit", "tag": "PBR1", "x": 1, "y": 2}}}
    assert content_digest(moved) == content_digest(semantic_layout)


def test_dynamic_operation_union_is_closed_and_delete_is_idempotent() -> None:
    adapter = TypeAdapter(DraftOp)
    operation = adapter.validate_python({"op": "delete_scenario", "id": "run"})
    document = apply_ops({"objects": {}, "schedules": {}, "controllers": {}, "scenarios": {}}, [operation])
    assert document["scenarios"] == {}
    with pytest.raises(ValidationError):
        adapter.validate_python({"op": "execute_python", "code": "pass"})


def test_scenario_utc_offsets_and_duration_limits_are_explicit() -> None:
    base = {"id": "run", "units": ["PBR1"], "profiles": [{"profile_id": "p", "digest": "d"}],
            "start_utc": "2026-10-25T00:00:00Z", "end_utc": "2026-10-25T02:00:00+01:00",
            "output_cadence_s": 3600, "temperature_source": "unit_mean"}
    scenario = Scenario.model_validate(base)
    start = datetime.fromisoformat(scenario.start_utc.replace("Z", "+00:00")).astimezone(UTC)
    end = datetime.fromisoformat(scenario.end_utc).astimezone(UTC)
    assert (end - start).total_seconds() == 10_800
    with pytest.raises(ValidationError):
        Scenario.model_validate({**base, "output_cadence_s": 30})


def test_repeated_schedule_requires_a_finite_bound() -> None:
    with pytest.raises(ValidationError):
        Schedule.model_validate({"id": "daily", "events": [{"type": "harvest", "time_s": 0,
                                                               "unit": "PBR1", "fraction": 0.1,
                                                               "every_s": 86400}]})
