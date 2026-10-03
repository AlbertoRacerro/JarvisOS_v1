from __future__ import annotations

import copy
import time

import pytest

from app.modules.process_stack import draft, draft_compiler, mixed, mixed_runtime


def _unit(uid: str, tag: str, kind: str) -> dict:
    return {"id": uid, "kind": "unit", "tag": tag, "type": kind,
            "mode": "specified" if kind == "SpecifiedSeparator" else None,
            "params": ({"biomass_recovery": {"si": 90.0}, "concentration_factor": {"si": 10.0}}
                       if kind == "SpecifiedSeparator" else {}), "options": {}, "reactions": []}


def _stream(uid: str, tag: str, source: str | None = None,
            target: str | None = None, source_port: int = 0, target_port: int = 0) -> dict:
    return {"id": uid, "kind": "stream", "tag": tag, "type": "MaterialStream",
            "source": {"unit": source, "port": source_port} if source else None,
            "target": {"unit": target, "port": target_port} if target else None,
            "spec": {"temperature": {"si": 298.15}, "pressure": {"si": 101325.0},
                     "mass_flow": {"si": 1.0}, "composition_basis": "mass", "composition": {"Water": 1.0},
                     "culture": {"biomass": {"si": 1.0}, "salinity": {"si": 35.0}}}
            if source is None else {}}


def _tear_document() -> dict:
    objects = {
        "feed": _stream("feed", "Feed", target="m"),
        "m": _unit("m", "Mixer", "Mixer"),
        "m_j": _stream("m_j", "M_to_J", "m", "j"),
        "j": _unit("j", "Separator", "SpecifiedSeparator"),
        "j_s": _stream("j_s", "Concentrate", "j", "s", source_port=0),
        "s": _unit("s", "Splitter", "Splitter"),
        "j_b": _stream("j_b", "Clarified", "j", "s", source_port=1, target_port=0),
        "s_r": _stream("s_r", "Return", "s", "r", source_port=1),
        "r": _unit("r", "Recycle", "Recycle"),
        "r_m": _stream("r_m", "Tear", "r", "m"),
        "product": _stream("product", "Product", "s", None, source_port=0),
    }
    return {"schema_version": 1, "name": "mixed test", "compounds": ["Water"],
            "property_package": "NRTL", "objects": objects, "reactions": {}}


def _state(value: float = 0.0) -> dict:
    return {"temperature_K": 298.15, "pressure_Pa": 200000.0, "mass_flow_kg_s": 1.0,
            "mass_fractions": {"Water": value}, "vapor_fraction": 0.0,
            "culture": {field: 0.0 for field in mixed.CULTURE_FIELDS}}


def test_jarvis_evaluator_interface_keeps_separator_behavior_and_run_context() -> None:
    unit = _unit("j", "Separator", "SpecifiedSeparator")
    inlet = _state()
    inlet["culture"]["biomass"] = 0.001
    inlet["density_kg_m3"] = 1000.0
    context = mixed_runtime.JarvisUnitContext(1000.0, time.monotonic() + 10, {})
    evaluation = mixed_runtime.JARVIS_EVALUATORS["SpecifiedSeparator"](unit, inlet, context)
    expected = mixed.separator(inlet, 90.0, 10.0)
    assert evaluation.outlets == {"concentrate": expected[0], "clarified": expected[1]}
    assert evaluation.culture_generation == {}
    assert evaluation.result["evaluator"] == "jarvis.specified_separator"
    assert 0 < context.remaining_s() <= 10
    context.cache["per_run_key"] = 1
    assert context.cache["per_run_key"] == 1


def test_internal_feed_flash_exception_requires_exact_one_feed_and_one_finding() -> None:
    feed = _stream("f", "FlashFeed")
    document = {"objects": {"f": feed}}
    check = {"ready": False, "blockers": 1, "warnings": 0,
             "findings": [{"code": "STREAM_DANGLING", "severity": "blocker", "object": "FlashFeed"}]}
    allowed = draft_compiler.isolated_feed_flash_check
    assert allowed(document, "run", check, allowed=True)
    assert not allowed(document, "run", check, allowed=False)
    assert not allowed(document, "validate", check, allowed=True)
    assert not allowed({"objects": {"f": feed, "extra": _stream("extra", "Extra")}}, "run", check, allowed=True)
    assert not allowed(document, "run", {**check, "findings": [*check["findings"],
                                                         {"code": "PROPERTY_INVALID", "object": "FlashFeed"}]}, allowed=True)
    assert not allowed(document, "run", {**check, "findings": [{**check["findings"][0],
                                                                   "object": "Other"}]}, allowed=True)


@pytest.mark.parametrize("full", [False, True])
def test_flash_opts_in_and_retains_real_unready_check(full: bool, monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_path(document: dict, _client: object, **kwargs: object) -> dict:
        assert kwargs["allow_isolated_feed_flash"] is True
        assert len(document["objects"]) == 1
        return {"status": "completed", "streams": {"FlashFeed": {"mass_flow_kg_s": 1.0}},
                "dwsim_check": {"ready": False, "intentional_isolated_feed_exception": True}}

    monkeypatch.setattr(mixed_runtime, "_full" if full else "_light", fake_path)
    result = mixed_runtime._flash(_state(1.0), "FlashFeed", None, label="test", dwsim_version="10.2.9",
                                  mcp_sha256="test", property_package="NRTL", full=full, remaining_s=10)
    assert result["flash_check_exception"] == "STREAM_DANGLING"


def test_jarvis_declared_generation_closes_unit_culture_balance() -> None:
    document = _tear_document()
    # A productive Jarvis unit can declare the growth rate instead of being
    # rejected by the separator's strictly conserved biomass balance.
    document["objects"] = {key: value for key, value in document["objects"].items()
                           if key in {"feed", "j", "j_s", "j_b"}}
    document["objects"]["feed"]["target"] = {"unit": "j", "port": 0}
    document["objects"]["j_s"]["target"] = None
    document["objects"]["j_b"]["target"] = None
    inlet = _state()
    inlet["culture"]["biomass"] = 1.0
    concentrate = copy.deepcopy(inlet)
    concentrate["mass_flow_kg_s"] = 0.5
    concentrate["culture"]["biomass"] = 3.0
    clarified = copy.deepcopy(inlet)
    clarified["mass_flow_kg_s"] = 0.5
    clarified["culture"]["biomass"] = 1.0
    known = {"Feed": inlet, "Concentrate": concentrate, "Clarified": clarified}
    balance = mixed_runtime._culture_balances(document, known, {"Separator": {"biomass": 1.0}})
    assert balance["Separator"]["biomass"]["passed"]
    assert balance["Separator"]["biomass"]["generated"] == 1.0


@pytest.mark.parametrize("flow,concentration", [(1e6, 1e-6), (1e-9, 100.0)])
def test_whole_graph_tear_culture_tolerance_has_flux_units(flow: float, concentration: float) -> None:
    feed = _stream("f", "Feed")
    product = _stream("p", "Product", source="u")
    document = {"objects": {"f": feed, "p": product, "u": _unit("u", "Unit", "Heater")}}
    state = _state()
    state["mass_flow_kg_s"] = flow
    state["culture"]["biomass"] = concentration
    final = {"known": {"Feed": state, "Product": state}, "units": {}, "culture_generation": {}}
    result = mixed_runtime._whole_graph_balances(document, final, {"Tear": state})
    delta_m = mixed.tolerance("mass_flow_kg_s", flow)
    delta_c = mixed.tolerance("biomass", concentration)
    expected = flow * delta_c + concentration * delta_m + delta_m * delta_c
    baseline = 1e-9 * abs(flow * concentration) + 1e-12
    assert result["balances"]["biomass"]["tolerance"] == pytest.approx(expected + baseline)
    if flow < 1e-6:
        assert result["balances"]["biomass"]["tolerance"] < 1e-6


def test_whole_graph_salinity_tear_tolerance_converts_g_per_kg_to_kg_per_s() -> None:
    feed = _stream("f", "Feed")
    product = _stream("p", "Product", source="u")
    document = {"objects": {"f": feed, "p": product, "u": _unit("u", "Unit", "Heater")}}
    state = _state()
    state["culture"]["salinity"] = 35.0
    final = {"known": {"Feed": state, "Product": state}, "units": {}, "culture_generation": {}}
    row = mixed_runtime._whole_graph_balances(document, final, {"Tear": state})["balances"]["salinity"]
    delta_m = mixed.tolerance("mass_flow_kg_s", 1.0)
    delta_c = mixed.tolerance("salinity", 35.0)
    expected = (delta_c + 35.0 * delta_m + delta_m * delta_c) * 0.001 + 1e-9 * 0.035 + 1e-12
    assert row["tolerance"] == pytest.approx(expected)


def test_jarvis_outlet_culture_shows_evaluator_fidelity_in_operator_result() -> None:
    feed = _stream("f", "Feed", target="j")
    jarvis = _unit("j", "Separator", "SpecifiedSeparator")
    outlet = _stream("o", "Concentrate", source="j")
    document = {"objects": {"f": feed, "j": jarvis, "o": outlet}}
    state = _state()
    state["culture"]["biomass"] = 0.001
    dwsim_stream = {"phases": [{"name": "Mixture", "density_kg_m3": 1000.0}]}
    final = {"known": {"Feed": state, "Concentrate": state},
             "streams": {"Feed": dwsim_stream, "Concentrate": dwsim_stream},
             "units": {"Separator": {"fidelity": "screening — specified performance",
                                     "caveats": ["Dissolved species follow the carrier."],
                                     "evaluator": "jarvis.specified_separator", "version": 1}},
             "culture_balances": {}}
    culture_results = mixed_runtime._culture_results(document, final)
    assert culture_results["Concentrate"]["fidelity"] == "screening — specified performance"
    assert "Dissolved species follow the carrier." in culture_results["Concentrate"]["caveats"]
    assert culture_results["Concentrate"]["evaluator"] == "jarvis.specified_separator"
    assert culture_results["Feed"]["fidelity"] == mixed_runtime.culture.FIDELITY


def test_jarvis_generation_declares_field_specific_rate_units() -> None:
    unit = _unit("j", "Separator", "SpecifiedSeparator")
    outlet = _state()
    result = mixed_runtime.JarvisUnitEvaluation(
        {"concentrate": outlet, "clarified": outlet}, {},
        {"biomass": 1.0, "dic": 2.0}, {"biomass": "kg/s", "dic": "mol/s"})
    mixed_runtime._check_evaluation(unit, result)
    result.culture_generation_units["dic"] = "kg/s"
    with pytest.raises(mixed_runtime.SegmentFailure, match="JARVIS_GENERATION_INVALID"):
        mixed_runtime._check_evaluation(unit, result)


def test_culture_native_recycle_uses_seed_and_reaches_fixed_point() -> None:
    objects = {
        "f1": _stream("f1", "FeedA", target="m"),
        "f2": _stream("f2", "FeedB", target="m", target_port=1),
        "m": _unit("m", "Mixer", "Mixer"),
        "m_s": _stream("m_s", "Mixed", "m", "s"),
        "s": _unit("s", "Splitter", "Splitter"),
        "s_p": _stream("s_p", "Product", "s", None),
        "s_r": _stream("s_r", "ToRecycle", "s", "r", source_port=1),
        "r": _unit("r", "Recycle", "Recycle"),
        "r_m": _stream("r_m", "Return", "r", "m", target_port=2),
    }
    objects["f1"]["spec"]["culture"]["biomass"]["si"] = 1.0
    objects["f2"]["spec"]["culture"]["biomass"]["si"] = 3.0
    segment = {"objects": objects}
    flows = {"FeedA": 0.5, "FeedB": 0.5, "Mixed": 2.0, "Product": 1.0,
             "ToRecycle": 1.0, "Return": 1.0}
    result = {"streams": {tag: {"mass_flow_kg_s": flow, "vapor_fraction": 0.0,
                               "phases": [{"name": "Mixture", "density_kg_m3": 1000.0}]}
                          for tag, flow in flows.items()}}
    states = mixed_runtime._propagate_culture(segment, result, {})
    assert states["Return"]["biomass"] == pytest.approx(0.002, rel=2e-5)
    assert states["Product"]["biomass"] == pytest.approx(0.002, rel=2e-5)


def test_failed_latest_mixed_run_does_not_reuse_old_current_results() -> None:
    revision = "1:" + "a" * 16
    prior = {"run_id": "prior", "action": "run", "status": "completed", "draft_revision": revision,
             "materialization_fingerprint": None}
    failed = {"run_id": "failed", "action": "run", "status": "unconverged", "draft_revision": revision}
    state = draft.results_state({"revision": revision, "seq": 1}, [failed, prior], _tear_document())
    assert state["state"] == "stale"
    assert state["last_attempt"]["status"] == "unconverged"


def test_final_status_preserves_stronger_failure_and_original_nonconvergence() -> None:
    failed_balance = {"status": "failed"}
    mismatch = {"code": "light_full_mismatch"}
    assert mixed_runtime._final_status("completed", "converged", mismatch, failed_balance) == (
        "segment_failed", "light_full_mismatch")
    assert mixed_runtime._final_status("unconverged", "max_iterations", None, failed_balance) == (
        "unconverged", "max_iterations")
    assert mixed_runtime._final_status("unconverged", "wall_budget", None, failed_balance) == (
        "unconverged", "wall_budget")
    assert mixed_runtime._final_status("completed", "converged", None, failed_balance) == (
        "unconverged", "balance")


def test_jarvis_evaluator_typed_failure_keeps_unit_identity(monkeypatch: pytest.MonkeyPatch) -> None:
    class BiologyFailure(RuntimeError):
        code = "PBR_NO_STEADY_ROOT"
        detail = {"branch": "none"}

    def failing(_unit: dict, _inlet: dict, _context: mixed_runtime.JarvisUnitContext) -> None:
        raise BiologyFailure("no productive branch")

    monkeypatch.setitem(mixed_runtime.JARVIS_EVALUATORS, "SpecifiedSeparator", failing)
    context = mixed_runtime.JarvisUnitContext(1000.0, time.monotonic() + 10, {})
    with pytest.raises(mixed_runtime.SegmentFailure) as captured:
        mixed_runtime._call_evaluator(_unit("j", "Separator", "SpecifiedSeparator"), _state(), context)
    assert captured.value.segment == "Separator"
    assert captured.value.detail == {"code": "PBR_NO_STEADY_ROOT", "error_type": "BiologyFailure",
                                     "message": "no productive branch", "detail": {"branch": "none"}}


def test_partition_consumes_cross_engine_recycle_and_keeps_jarvis_free_loop_native() -> None:
    document = _tear_document()
    part = mixed.partition(document)
    assert part["consumed"] == ["r"]
    assert part["segments"] == [["m"], ["s"]]
    assert "TEAR_CONSUMED" in {row["code"] for row in mixed.validation_findings(document)}
    assert mixed.recycle_free_cycles(document) == []


def test_recycle_free_cycle_is_reported_after_cutting_all_recycle_outputs() -> None:
    document = _tear_document()
    document["objects"].update({
        "s_m": _stream("s_m", "Bypass", "s", "m", source_port=0),
    })
    assert mixed.recycle_free_cycles(document) == [["Mixer", "Separator", "Splitter"]]


def test_native_recycle_side_loop_stays_in_its_dwsim_segment() -> None:
    document = _tear_document()
    document["objects"].update({
        "side_feed": _stream("side_feed", "SideFeed", target="h"),
        "h": _unit("h", "SideHeater", "Heater"),
        "h_r": _stream("h_r", "HeaterToRecycle", "h", "nr"),
        "nr": _unit("nr", "NativeRecycle", "Recycle"),
        "r_h": _stream("r_h", "RecycleToHeater", "nr", "h"),
        "side_product": _stream("side_product", "SideProduct", "h"),
    })
    part = mixed.partition(document)
    assert part["consumed"] == ["r"]
    assert ["nr", "h"] in part["segments"]


def test_native_recycle_connected_to_consumed_loop_segment_is_refused_as_finding() -> None:
    document = _tear_document()
    document["objects"].update({
        "side": _unit("side", "SideMixer", "Mixer"),
        "side_in": _stream("side_in", "SideIn", "s", "side"),
        "side_recycle": _unit("side_recycle", "SideRecycle", "Recycle"),
        "side_back": _stream("side_back", "SideBack", "side_recycle", "side"),
        "side_out": _stream("side_out", "SideOut", "side", "side_recycle", source_port=1),
    })
    codes = {row["code"] for row in mixed.validation_findings(document)}
    assert "NATIVE_RECYCLE_IN_JARVIS_LOOP" in codes
    assert "NATIVE_RECYCLE_IN_JARVIS_LOOP" in {row["code"] for row in draft.validate_document(document)}


def test_separator_findings_require_culture_and_screen_implausible_concentrate() -> None:
    document = _tear_document()
    document["objects"]["feed"]["spec"].pop("culture")
    codes = {row["code"] for row in mixed.validation_findings(document)}
    assert "SEPARATOR_REQUIRES_CULTURE" in codes
    document["objects"]["feed"]["spec"]["culture"] = {"biomass": {"si": 1.0}, "salinity": {"si": 35.0}}
    document["objects"]["j"]["params"]["concentration_factor"]["si"] = 300.0
    codes = {row["code"] for row in mixed.validation_findings(document)}
    assert "SEPARATOR_CONCENTRATE_IMPLAUSIBLE" in codes


def test_energy_stream_cannot_bridge_different_jarvis_levels() -> None:
    document = _tear_document()
    document["objects"]["energy"] = {
        "id": "energy", "kind": "stream", "tag": "Heat", "type": "EnergyStream",
        "source": {"unit": "m", "port": 0}, "target": {"unit": "s", "port": 0}, "spec": {},
    }
    assert "ENERGY_STREAM_CROSSES_JARVIS_LEVEL" in {
        row["code"] for row in mixed.validation_findings(document)}


def test_specified_separator_equations_and_zero_flow() -> None:
    inlet = _state()
    inlet["mass_flow_kg_s"] = 10.0
    inlet["culture"]["biomass"] = 0.001
    concentrate, clarified = mixed.separator(inlet, 90.0, 10.0)
    assert concentrate["mass_flow_kg_s"] == pytest.approx(0.9)
    assert clarified["mass_flow_kg_s"] == pytest.approx(9.1)
    assert concentrate["culture"]["biomass"] == pytest.approx(0.01)
    assert clarified["culture"]["biomass"] == pytest.approx(0.1 * 0.001 * 10 / 9.1)
    concentrate, clarified = mixed.separator(inlet | {"mass_flow_kg_s": 0.0}, 100.0, 1.000001)
    assert concentrate["mass_flow_kg_s"] == clarified["mass_flow_kg_s"] == 0
    assert concentrate["culture"]["biomass"] == clarified["culture"]["biomass"] == 0.001
    with pytest.raises(ValueError, match="liquid"):
        mixed.separator(inlet | {"vapor_fraction": 0.01}, 90, 10)
    concentrate, clarified = mixed.separator(inlet, 100.0, 1.000001)
    assert concentrate["mass_flow_kg_s"] > 0
    assert clarified["mass_flow_kg_s"] == pytest.approx(1e-5, abs=2e-11)
    assert concentrate["culture"]["biomass"] == pytest.approx(0.001000001)
    assert clarified["culture"]["biomass"] == 0


def test_heat_exchanger_first_tear_consumer_uses_large_seed_and_finding() -> None:
    document = _tear_document()
    document["objects"]["feed"]["spec"].update({"pressure": {"si": 101325.0}, "mass_flow": {"si": 2.0},
                                                    "composition": {"Water": 1.0}})
    document["objects"].update({
        "hx": _unit("hx", "HeatExchanger", "HeatExchanger"),
        "r_hx": _stream("r_hx", "TearToHX", "r", "hx"),
        "hx_m": _stream("hx_m", "HXToMixer", "hx", "m"),
    })
    document["objects"].pop("r_m")
    document["objects"]["feed"]["target"] = {"unit": "m", "port": 0}
    document["objects"]["hx_m"]["target"] = {"unit": "m", "port": 1}
    finding_codes = {item["code"] for item in mixed.validation_findings(document)}
    assert "TEAR_CONSUMER_ZERO_FLOW" in finding_codes
    part = mixed.partition(document)
    initial = mixed_runtime._seed(document, part)
    assert initial["TearToHX"]["mass_flow_kg_s"] == pytest.approx(0.002)


def test_mixed_validate_builds_jarvis_boundaries_without_solving(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    document = _tear_document()
    built: list[dict] = []
    def capture(segment, _client, **kwargs):
        assert kwargs["action"] == "validate"
        built.append(segment)
        return {"status": "validated"}
    monkeypatch.setattr(mixed_runtime, "_full", capture)
    result = mixed_runtime.run(document, action="validate", client=object(), dwsim_version="10.2.9",
                               mcp_sha256="a" * 64, run_dir=tmp_path)
    assert result["status"] == "validated"
    after_jarvis = next(segment for segment in built if "s" in segment["objects"])
    boundary = after_jarvis["objects"]["j_s"]
    assert boundary["source"] is None
    assert boundary["spec"]["mass_flow"]["si"] > 0


def test_residual_uses_field_tolerances_and_keeps_undamped_signed_values() -> None:
    before = {"temperature_K": 300.0, "pressure_Pa": 1e5, "mass_flow_kg_s": 1.0,
              "mass_fraction.Water": 0.5, "biomass": 0.01}
    after = before | {"temperature_K": 300.01, "pressure_Pa": 1e5 + 0.1,
                      "mass_flow_kg_s": 1.00001, "mass_fraction.Water": 0.5000001,
                      "biomass": 0.0100001}
    _, _, normalized = mixed.residual(before, after)
    assert normalized["temperature_K"] == pytest.approx(1)
    assert normalized["mass_fraction.Water"] == pytest.approx(1)
    assert mixed.residual_values(before, after)["pressure_Pa"] == pytest.approx(0.1)
    assert mixed.tolerance("biomass", 0.0) == pytest.approx(1e-12)
    assert mixed.residual({"biomass": None}, {"biomass": None})[0] == 0
    assert mixed.residual({"biomass": None}, {"biomass": 0.0})[0] == float("inf")


def test_engine_neutral_controller_converges_gain_0455_in_expected_range() -> None:
    initial = {"Tear": _state(0.9)}

    def evaluate(guess: dict[str, dict], _iteration: int) -> dict[str, dict]:
        output = copy.deepcopy(guess["Tear"])
        current = output["mass_fractions"]["Water"]
        output["mass_fractions"]["Water"] = 0.455 * current + 0.545
        return {"Tear": output}

    result = mixed.iterate(initial, evaluate)
    assert result["status"] == "completed"
    assert 8 <= len(result["history"]) <= 20
    assert result["history"][-1]["max_normalized_residual"] <= 1


def test_spurious_growth_below_one_point_five_does_not_damp_and_real_growth_does() -> None:
    def run_with_residuals(values: list[float]) -> dict:
        seen = 0
        def evaluate(guess: dict[str, dict], _iteration: int) -> dict[str, dict]:
            nonlocal seen
            target = copy.deepcopy(guess["Tear"])
            current = target["mass_fractions"]["Water"]
            target["mass_fractions"]["Water"] = current + values[min(seen, len(values) - 1)] * 1e-7
            seen += 1
            return {"Tear": target}
        return mixed.iterate({"Tear": _state()}, evaluate)

    spurious = run_with_residuals([2.0, 2.8, 3.8])
    assert [row["omega"] for row in spurious["history"][:3]] == [1.0, 1.0, 1.0]
    growing = run_with_residuals([2.0, 4.0, 3.0])
    assert growing["history"][2]["omega"] == 0.5


def test_controller_damping_exhaustion_and_iteration_cap() -> None:
    seen = 0
    def growing(guess: dict[str, dict], _iteration: int) -> dict[str, dict]:
        nonlocal seen
        target = copy.deepcopy(guess["Tear"])
        target["mass_fractions"]["Water"] += 2.0 ** (seen + 1) * 1e-7
        seen += 1
        return {"Tear": target}
    exhausted = mixed.iterate({"Tear": _state()}, growing)
    assert exhausted["reason"] == "damping_exhausted"
    assert exhausted["omega"] == 0.125

    constant = mixed.iterate({"Tear": _state()}, lambda guess, _iteration: {
        "Tear": {**guess["Tear"], "mass_fractions": {"Water": guess["Tear"]["mass_fractions"]["Water"] + 2e-7}}
    })
    assert constant["reason"] == "max_iterations"
    assert len(constant["history"]) == 25


def test_controller_wall_budget_stops_before_building_an_iteration() -> None:
    called = False
    def evaluate(guess: dict[str, dict], _iteration: int) -> dict[str, dict]:
        nonlocal called
        called = True
        return guess
    result = mixed.iterate({"Tear": _state()}, evaluate,
                           before_iteration=lambda _index: "wall_budget")
    assert result["reason"] == "wall_budget"
    assert not called


def test_light_full_mismatch_and_pressure_drop_diagnosis() -> None:
    light = {"Tear": _state()}
    full = copy.deepcopy(light)
    full["Tear"]["pressure_Pa"] += 1.0
    mismatch = mixed_runtime._light_full_mismatch(light, full)
    assert mismatch and mismatch["code"] == "light_full_mismatch"
    history = [{"residuals": {"Tear": {"pressure_Pa": -20.0 - index}}} for index in range(3)]
    assert mixed_runtime._pressure_diagnosis(history) == (
        "pressure falls by 22 Pa per pass around the loop; add a pump")
    history[-1]["residuals"]["Tear"]["pressure_Pa"] = 1.0
    assert mixed_runtime._pressure_diagnosis(history) is None


def test_mixed_fingerprint_ignores_layout_but_includes_culture_and_partition() -> None:
    document = _tear_document()
    part = mixed.partition(document)
    original = mixed.fingerprint(document, part)
    moved = copy.deepcopy(document)
    moved["objects"]["m"]["x"] = 400
    assert mixed.fingerprint(moved, mixed.partition(moved)) == original
    edited = copy.deepcopy(document)
    edited["objects"]["feed"]["spec"]["culture"]["biomass"]["si"] = 2
    assert mixed.fingerprint(edited, mixed.partition(edited)) != original


@pytest.mark.parametrize("unit_result,expected", [
    ({"reported": {"Mass Flow Error": {"units": "kg/h", "value": "0"}}}, 0.0),
    ({"reported": {"Mass Flow Error": {"units": "kg/h", "value": "-36"}}}, 0.01),
    ({"reported": {}, "properties": [{"name": "Mass Flow Error", "unit": "kg/h", "value": 7.2}]}, 0.002),
    ({"reported": {"Mass Flow Error": {"units": "kg/h", "value": "NaN"}}}, None),
    ({"reported": {"Mass Flow Error": {"units": "lbm/h", "value": "1"}}}, None),
    ({}, None),
])
def test_native_recycle_mass_flow_error_parses_dwsim_string_values(unit_result: dict,
                                                                    expected: float | None) -> None:
    value = mixed_runtime._native_mass_flow_error_kg_s(unit_result)
    assert value == (pytest.approx(expected) if expected is not None else None)


def _run_document(document: dict, tmp_path, action: str = "run") -> dict:
    return mixed_runtime.run(document, action=action, client=object(), dwsim_version="10.2.9",
                             mcp_sha256="a" * 64, run_dir=tmp_path)


def test_failure_record_partition_has_the_tag_based_shape_of_a_success_record(
        monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    """B1: a failed segment must store {id, level, units: [tags]} segments, never raw id lists."""
    document = _tear_document()

    def failing_light(*_args, **_kwargs):
        raise mixed_runtime.SegmentFailure("mixed-1-0", {"code": "check_failed", "findings": [
            {"object": "Mixer", "message": "Mixer has no outlet"}]})

    monkeypatch.setattr(mixed_runtime, "_light", failing_light)
    record = _run_document(document, tmp_path)["mixed_solve"]
    assert record["status"] == "segment_failed"
    part = record["partition"]
    assert part["consumed"] == [document["objects"]["r"]["tag"]]
    assert part["segments"] == [{"id": 0, "units": ["Mixer"], "level": 0},
                                {"id": 1, "units": ["Splitter"], "level": 1}]
    assert part["jarvis_units"] == ["Separator"]
    success_shape = mixed_runtime._partition_record(document, mixed.partition(document), [
        {"id": 0, "units": ["Mixer"], "level": 0, "materialization_fingerprint": None}])
    assert set(success_shape) == set(part)
    # M7: the label maps to unit tags, and the check finding is surfaced as a message.
    assert record["failed_units"] == ["Mixer"]
    assert "Mixer has no outlet" in record["message"]


def test_non_finite_residual_is_serialised_as_null_with_an_explicit_flag(
        monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    """M2: infinity stays internal; stored and served records contain only finite numbers."""
    import json

    document = _tear_document()
    calls = {"n": 0}

    def evaluate(tear, iteration, **_kwargs):
        calls["n"] += 1
        if calls["n"] > 1:
            raise mixed_runtime.SegmentFailure("Separator", {"code": "JARVIS_UNIT_FAILED"})
        output = copy.deepcopy(tear)
        for state in output.values():
            state["culture"]["biomass"] = None  # null/value mismatch -> infinite residual
        return {"produced": output, "elapsed_s_by_phase": {"build": 0.0, "solve": 0.0, "culture": 0.0},
                "max_build_seconds": 0.0}

    monkeypatch.setattr(mixed_runtime, "_evaluate", lambda document, part, tear, **kwargs: evaluate(
        tear, kwargs["iteration"]))
    record = _run_document(document, tmp_path)["mixed_solve"]
    row = record["history"][0]
    assert row["max_normalized_residual"] is None
    assert row["non_finite"] == "inf"
    assert row["pattern_mismatch_fields"] == [f"{document['objects']['r_m']['tag']}.biomass"]
    json.dumps(record, allow_nan=False)


def test_mid_iteration_failure_carries_the_pressure_per_pass_diagnosis(
        monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    """M7: the diagnosis is attached to a segment_failed that follows three one-sided passes."""
    document = _tear_document()
    calls = {"n": 0}

    def fake(_document, _part, tear, **_kwargs):
        calls["n"] += 1
        if calls["n"] == 4:
            raise mixed_runtime.SegmentFailure("Separator", {"code": "JARVIS_UNIT_FAILED"})
        output = copy.deepcopy(tear)
        for state in output.values():
            state["pressure_Pa"] -= 100.0
        return {"produced": output, "elapsed_s_by_phase": {"build": 0.0, "solve": 0.0, "culture": 0.0},
                "max_build_seconds": 0.0}

    monkeypatch.setattr(mixed_runtime, "_evaluate", fake)
    record = _run_document(document, tmp_path)["mixed_solve"]
    assert record["status"] == "segment_failed"
    assert record["failed_units"] == []
    assert "pressure falls by" in record["diagnosis"]
