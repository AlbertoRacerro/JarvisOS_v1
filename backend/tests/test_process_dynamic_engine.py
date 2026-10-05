"""Deterministic unit coverage for spec 172's bounded dynamic contracts."""

from __future__ import annotations

import math
from datetime import UTC, datetime

import numpy as np
import pytest
from pydantic import TypeAdapter, ValidationError

from app.modules.process_stack import dynamic_engine
from app.modules.process_stack.draft import apply_ops, content_digest, empty_document
from app.modules.process_stack.draft_models import DraftOp
from app.modules.process_stack.dynamic_models import Scenario, Schedule


def test_dynamic_draft_ops_are_semantic_and_legacy_documents_remain_valid() -> None:
    adapter = TypeAdapter(DraftOp)
    legacy = empty_document("legacy")
    legacy["objects"]["pbr"] = {"id": "pbr", "kind": "unit", "type": "PhotobioreactorT1", "tag": "PBR1", "x": 1, "y": 2}
    semantic = apply_ops(
        legacy,
        [
            adapter.validate_python(op)
            for op in (
                {"op": "set_schedule", "id": "feed", "value": {"events": []}},
                {
                    "op": "set_controller",
                    "id": "loop",
                    "value": {
                        "type": "pi",
                        "measurement": "X",
                        "unit": "PBR1",
                        "actuator": "feed:Feed",
                        "cadence_s": 60,
                        "setpoint": 1,
                    },
                },
                {
                    "op": "set_scenario",
                    "id": "run",
                    "value": {
                        "units": ["PBR1"],
                        "profiles": [{"profile_id": "p", "digest": "d"}],
                        "start_utc": "2026-01-01T00:00:00Z",
                        "end_utc": "2026-01-01T01:00:00Z",
                        "output_cadence_s": 3600,
                        "temperature_source": "unit_mean",
                        "schedule_id": "feed",
                        "controllers": ["loop"],
                    },
                },
            )
        ],
    )
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
    base = {
        "id": "run",
        "units": ["PBR1"],
        "profiles": [{"profile_id": "p", "digest": "d"}],
        "start_utc": "2026-10-25T00:00:00Z",
        "end_utc": "2026-10-25T02:00:00+01:00",
        "output_cadence_s": 3600,
        "temperature_source": "unit_mean",
    }
    scenario = Scenario.model_validate(base)
    start = datetime.fromisoformat(scenario.start_utc.replace("Z", "+00:00")).astimezone(UTC)
    end = datetime.fromisoformat(scenario.end_utc).astimezone(UTC)
    # Offsets define instants; a local clock's DST fold never enters the scenario time base.
    assert (end - start).total_seconds() == 3_600
    with pytest.raises(ValidationError):
        Scenario.model_validate({**base, "output_cadence_s": 30})


def test_repeated_schedule_requires_a_finite_bound() -> None:
    with pytest.raises(ValidationError):
        Schedule.model_validate(
            {
                "id": "daily",
                "events": [{"type": "harvest", "time_s": 0, "unit": "PBR1", "fraction": 0.1, "every_s": 86400}],
            }
        )


def _minimal_snapshot(**scenario_changes):
    start = datetime(2026, 1, 1, tzinfo=UTC).timestamp()
    scenario = {
        "output_cadence_s": 60.0, "controller_cadence_s": 60.0, "rtol": 1e-9, "atol": 1e-12,
        "solver_method": "BDF", "downstream_cadence_s": None, "temperature_source": "unit_mean",
        **scenario_changes,
    }
    unit = {"tag": "PBR1", "unit": {"id": "p1"}, "params": {}, "model": {}, "volume_m3": 1.0,
            "state": [1.0, 0.2, 0.01], "card_qualification": "unqualified"}
    payload = {
        "scenario": scenario, "units": [unit], "start_epoch": start, "end_epoch": start + 120,
        "profiles": [{"times": [start, start + 120], "ref": {"profile_id": "p", "digest": "p"}}],
        "schedule": {"events": []}, "controllers": [], "draft_id": "draft", "revision": 1,
        "content_digest": "digest", "scenario_id": "run", "topology": {"units": [], "streams": [],
            "flows": {}, "feeds": {}},
    }
    feed = {"id": "feed", "tag": "Feed", "source": None, "target": {"unit": "p1"}}
    product = {"id": "product", "tag": "Product", "source": {"unit": "p1"}, "target": None}
    payload["topology"] = {"units": [], "streams": [feed, product],
                           "flows": {"feed": 1e-20, "product": 1e-20},
                           "feeds": {"feed": [1.0, 0.2, 0.01]}}
    return dynamic_engine.Snapshot(payload, "snapshot")


def test_dark_decay_is_analytic_and_runs_are_bit_identical(monkeypatch):
    class Growth:
        nitrogen_quota = 0.05
        oxygen_yield = 1.0
        kla_h = 0.0
        oxygen_saturation = 0.01
        extinction = 0.0
        diameter = 0.05

        @staticmethod
        def rates_at(_par, _temperature, _x, _n):
            return 0.0, 0.01

    monkeypatch.setattr(dynamic_engine.pbr_unit, "build_growth", lambda *_args: Growth())
    monkeypatch.setattr(dynamic_engine, "_profile_values", lambda *_args: (0.0, 298.15))
    snapshot = _minimal_snapshot()
    first = dynamic_engine.run(snapshot, cancelled=lambda: False, progress=lambda _p: None)
    second = dynamic_engine.run(snapshot, cancelled=lambda: False, progress=lambda _p: None)
    assert first.status == "succeeded", first.error
    assert first.series["PBR1_X"][-1] == pytest.approx(math.exp(-0.01 * 120 / 3600), rel=1e-7)
    assert first.series["PBR1_X"].tobytes() == second.series["PBR1_X"].tobytes()


def test_constant_rate_limit_matches_closed_form(monkeypatch):
    class Growth:
        nitrogen_quota = 0.0
        oxygen_yield = 0.0
        kla_h = 0.0
        oxygen_saturation = 0.0
        extinction = 0.0
        diameter = 0.05

        @staticmethod
        def rates_at(_par, _temperature, _x, _n):
            return 0.02, 0.0

    monkeypatch.setattr(dynamic_engine.pbr_unit, "build_growth", lambda *_args: Growth())
    monkeypatch.setattr(dynamic_engine, "_profile_values", lambda *_args: (0.0, 298.15))
    result = dynamic_engine.run(_minimal_snapshot(), cancelled=lambda: False, progress=lambda _p: None)
    assert result.status == "succeeded"
    assert result.series["PBR1_X"][-1] == pytest.approx(math.exp(0.02 * 120 / 3600), rel=1e-7)


def test_sampler_failure_is_recorded_without_changing_trajectory_and_cancel_keeps_computed_rows(monkeypatch):
    class Growth:
        nitrogen_quota = 0.0
        oxygen_yield = 0.0
        kla_h = 0.0
        oxygen_saturation = 0.01
        extinction = 0.0
        diameter = 0.05

        @staticmethod
        def rates_at(_par, _temperature, _x, _n):
            return 0.0, 0.0

    monkeypatch.setattr(dynamic_engine.pbr_unit, "build_growth", lambda *_args: Growth())
    monkeypatch.setattr(dynamic_engine, "_profile_values", lambda *_args: (0.0, 298.15))
    snapshot = _minimal_snapshot(downstream_cadence_s=60.0)
    baseline = dynamic_engine.run(snapshot, cancelled=lambda: False, progress=lambda _p: None)
    calls = []

    def sampler(boundary):
        calls.append(boundary["time_s"])
        if len(calls) == 1:
            raise RuntimeError("sample failed")
        return {"status": "unconverged"}

    sampled = dynamic_engine.run(snapshot, cancelled=lambda: False, progress=lambda _p: None, sampler=sampler)
    assert calls == [60.0, 120.0]
    assert sampled.manifest["downstream_outcomes"][0]["status"] == "downstream_unconverged"
    assert sampled.series["PBR1_X"].tobytes() == baseline.series["PBR1_X"].tobytes()
    cancelled = dynamic_engine.run(snapshot, cancelled=lambda: True, progress=lambda _p: None)
    assert cancelled.status == "cancelled"
    assert len(cancelled.series["t_s"]) == 1


def test_onoff_hysteresis_and_pi_anti_windup(monkeypatch):
    unit = {"tag": "PBR1", "unit": {"id": "p1"}}
    topology = {"units": [], "streams": [{"id": "feed", "tag": "Feed", "source": None}], "flows": {}, "feeds": {}}
    state = [0.0] * 10
    onoff = {"id": "switch", "type": "onoff", "measurement": "X", "unit": "PBR1", "actuator": "feed:Feed",
             "cadence_s": 60.0, "setpoint": 1.0, "lower": 0.0, "upper": 1.0, "hysteresis": 0.2,
             "direction": "above", "output": 0.0, "_active": False, "_integral": 0.0}
    flows, log = {}, []
    for time_s, value in ((60, 0.9), (120, 1.1), (180, 1.21)):
        state[0] = value
        dynamic_engine._sample_controllers(np.asarray(state), [unit], [onoff], topology, flows,
                                           {"switch": 1.0}, time_s, log)
    assert [entry["output"] for entry in log] == [1.0, 1.0, 0.0]
    assert flows["feed"] == 0.0

    pi = {"id": "pi", "type": "pi", "measurement": "X", "unit": "PBR1", "actuator": "feed:Feed",
          "cadence_s": 60.0, "setpoint": 1.0, "lower": 0.0, "upper": 1.0, "kp": 2.0, "ki": 1.0,
          "output": 0.0, "_bias": 0.0, "_integral": 0.0}
    state[0] = 0.0
    dynamic_engine._sample_controllers(np.asarray(state), [unit], [pi], topology, flows, {"pi": 1.0}, 60, [])
    assert pi["output"] == 1.0
    assert pi["_integral"] == 0.0


def test_feed_dilution_and_setpoint_events_mutate_runtime_state():
    unit = {"tag": "PBR1", "unit": {"id": "p1"}}
    feed = {"id": "f", "tag": "Feed", "source": None, "target": {"unit": "s"}}
    splitter = {"id": "s", "tag": "Split", "type": "Splitter"}
    outlets = [{"id": "o1", "tag": "one", "source": {"unit": "s"}},
               {"id": "o2", "tag": "two", "source": {"unit": "s"}}]
    topology = {"units": [splitter], "streams": [feed, *outlets], "flows": {"f": 1.0, "o1": 0.4, "o2": 0.6},
                "feeds": {"f": [0.0, 1.0, 0.0]}}
    flows, feeds, setpoints, ctrls = topology["flows"], topology["feeds"], {"c": 1.0}, {"c": {"id": "c"}}
    state = np.zeros(10)
    args = ([unit], [], 0, topology, flows, feeds, setpoints, ctrls)
    dynamic_engine._apply_dynamic_event(state, (0, {"type": "feed_change", "time_s": 1, "stream": "Feed", "value": 2}),
                                        *args)
    dynamic_engine._apply_dynamic_event(state, (0, {"type": "dilution", "time_s": 2, "target": "splitter:Split", "value": 0.7}),
                                        *args)
    dynamic_engine._apply_dynamic_event(state, (0, {"type": "setpoint_change", "time_s": 3, "target": "c", "value": 4}),
                                        *args)
    assert flows["f"] == pytest.approx(2.0)
    assert flows["o1"] == pytest.approx(1.4)
    assert flows["o2"] == pytest.approx(0.6)
    assert setpoints["c"] == 4.0


def test_conditional_event_fires_at_sample_cadence_and_applies_feed_change():
    unit = {"tag": "PBR1", "unit": {"id": "p1"}}
    feed = {"id": "f", "tag": "Feed", "source": None}
    topology = {"units": [], "streams": [feed], "flows": {"f": 0.5}, "feeds": {"f": [0.0, 0.0, 0.0]}}
    state = np.zeros(10)
    state[0] = 2.0
    event = {"type": "feed_change", "time_s": 0.0, "stream": "Feed", "value": 1.5,
             "observed": "PBR1.X", "threshold": 1.0, "direction": "above", "hysteresis": 0.1}
    log, active = [], {}
    dynamic_engine._conditional_events(state, [unit], [(0, event)], active, log, 60.0,
                                       topology, topology["flows"], topology["feeds"], {}, {})
    assert topology["flows"]["f"] == 1.5
    assert log[0]["conditional"] is True
    assert log[0]["time_s"] == 60.0
