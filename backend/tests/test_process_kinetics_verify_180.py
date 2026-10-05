"""Independent checks on the stream data shapes that DWSIM reports for reactors."""

import math

from app.modules.process_stack.draft import result_findings
from app.modules.process_stack.kinetics_verify import verify_rate_law_reactor


def _quantity(value: float, unit: str) -> dict:
    return {"value": value, "unit": unit}


def _reaction(**law_changes: object) -> dict:
    law = {"form": "monod", "substrate": "A", "v_max": _quantity(5, "kmol/(m3.h)"),
           "k_s": _quantity(2, "kmol/m3"), "inhibitions": []}
    law.update(law_changes)
    return {"base_reactant": "A", "stoichiometry": {"A": -1, "B": 1}, "rate_law": law}


def _stream(a: float, b: float, *, q: float = 1, vapor: float = 0, temperature: float = 300) -> dict:
    total = a + b
    return {"molar_flow_mol_s": total / 3.6, "mass_flow_kg_s": 1.0, "temperature_K": temperature,
            "phases": [{"name": "Mixture", "density_kg_m3": 3600 / q,
                        "compounds": {"A": {"mole_fraction": a / total},
                                      "B": {"mole_fraction": b / total}}},
                       {"name": "Vapor", "fraction": vapor}]}


def _cstr_outlet() -> float:
    # (10-Aout) = 5*Aout/(2+Aout), at V=Q=1.
    return (3 + math.sqrt(89)) / 2


def test_cstr_passes_from_measured_outlet_without_dwsim_rate() -> None:
    outlet_a = _cstr_outlet()
    result = verify_rate_law_reactor(reactor_type="CSTR", reaction=_reaction(), volume_m3=1,
                                     inlet=_stream(10, 0), outlet={"reported": _stream(outlet_a, 10 - outlet_a)})
    assert result["ok"] is True
    assert result["residual"] < 1e-12
    assert math.isclose(result["rate_outlet"], 10 - outlet_a)
    assert result["rate_inlet"] is None
    assert result["summary"]["residence_time_h"] == 1


def test_cstr_catches_silent_no_reaction_and_wrong_rate_units() -> None:
    feed = _stream(10, 0)
    silent = verify_rate_law_reactor(reactor_type="CSTR", reaction=_reaction(), volume_m3=1,
                                    inlet=feed, outlet=_stream(10, 0))
    assert silent["ok"] is False
    assert silent["code"] == "KINETICS_VERIFICATION_FAILED"
    assert silent["residual"] == 1
    wrong_unit = verify_rate_law_reactor(reactor_type="CSTR", reaction=_reaction(), volume_m3=1,
                                        inlet=feed, outlet=_stream(9.99, 0.01))
    assert wrong_unit["ok"] is False
    assert wrong_unit["residual"] > 0.9


def test_failed_verification_is_visible_without_blocking_a_repaired_run() -> None:
    document = {"objects": {}}
    failed = {"status": "failed", "solve": {"failed_objects": [{"tag": "CSTR-1",
              "code": "KINETICS_VERIFICATION_FAILED", "error": "Measured conversion disagrees with the rate law."}]}}
    finding, = result_findings(document, None, failed)
    assert finding["code"] == "KINETICS_VERIFICATION_FAILED"
    assert finding["severity"] == "warning"
    assert finding["message"].startswith("Last Run: ")


def test_zero_rate_accepts_roundoff_scale_flow_change() -> None:
    reaction = _reaction(v_max=_quantity(0, "kmol/(m3.h)"))
    result = verify_rate_law_reactor(reactor_type="CSTR", reaction=reaction, volume_m3=1,
                                     inlet=_stream(10, 0), outlet=_stream(10 - 1e-10, 1e-10))
    assert result["ok"] is True


def test_pfr_integrates_independent_monod_reference() -> None:
    # For Q=1, V = [2 ln(10/Aout) + (10-Aout)] / 5.
    lower, upper = 0.1, 10.0
    for _ in range(80):
        middle = (lower + upper) / 2
        required_volume = (2 * math.log(10 / middle) + 10 - middle) / 5
        if required_volume > 1:
            lower = middle
        else:
            upper = middle
    outlet_a = (lower + upper) / 2
    result = verify_rate_law_reactor(reactor_type="PFR", reaction=_reaction(), volume_m3=1,
                                     inlet=_stream(10, 0), outlet=_stream(outlet_a, 10 - outlet_a))
    assert result["ok"] is True
    assert result["residual"] < 1e-6
    assert result["rate_inlet"] > result["rate_outlet"] > 0


def test_pfr_uses_measured_liquid_flow_change() -> None:
    # Independent integral for Monod with Q(x)=Q0+(Q1-Q0)x/Xout.
    x = 0.3
    q_in, q_out = 1.0, 0.9
    logarithm = -math.log1p(-x)
    volume = (10 * x + 2 * (q_in * logarithm + (q_out - q_in) * (logarithm - x) / x)) / 5
    result = verify_rate_law_reactor(reactor_type="PFR", reaction=_reaction(), volume_m3=volume,
                                     inlet=_stream(10, 0, q=q_in),
                                     outlet=_stream(10 * (1 - x), 10 * x, q=q_out))
    assert result["ok"] is True
    assert result["residual"] < 1e-6


def test_haldane_competitive_and_normalized_si_parameters() -> None:
    law = {"form": "haldane", "substrate": "A", "v_max": {"si": 5 / 3.6},
           "k_s": {"si": 2000}, "k_i": {"si": 10000},
           "inhibitions": [{"kind": "competitive", "inhibitor": "B", "k_i": {"si": 4000}}]}
    reaction = _reaction(**law)
    lower, upper = 0.0, 10.0
    for _ in range(80):
        x = (lower + upper) / 2
        a, b = 10 - x, x
        rate = 5 * a / (2 * (1 + b / 4) + a + a * a / 10)
        if rate > x:
            lower = x
        else:
            upper = x
    extent = (lower + upper) / 2
    result = verify_rate_law_reactor(reactor_type="CSTR", reaction=reaction, volume_m3=1,
                                     inlet=_stream(10, 0), outlet=_stream(10 - extent, extent))
    assert result["ok"] is True


def test_two_phase_and_outside_validity_are_distinct() -> None:
    outlet_a = _cstr_outlet()
    reaction = _reaction()
    reaction["validity"] = {"temperature_max": _quantity(290, "K"),
                            "substrate_max": _quantity(8, "kmol/m3")}
    warning = verify_rate_law_reactor(reactor_type="CSTR", reaction=reaction, volume_m3=1,
                                      inlet=_stream(10, 0), outlet=_stream(outlet_a, 10 - outlet_a))
    assert warning["ok"] is True
    assert [item["code"] for item in warning["findings"]] == ["KINETICS_OUTSIDE_VALIDITY"]
    phase = verify_rate_law_reactor(reactor_type="CSTR", reaction=reaction, volume_m3=1,
                                    inlet=_stream(10, 0), outlet=_stream(outlet_a, 10 - outlet_a, vapor=1e-7))
    assert phase["code"] == "KINETICS_TWO_PHASE_UNSUPPORTED"
    assert phase["summary"] == {}


def test_inhibition_and_temperature_factor_use_declared_units() -> None:
    law = {"inhibitions": [{"kind": "noncompetitive", "inhibitor": "B",
                             "k_i": _quantity(4, "kmol/m3")}],
           "temperature": {"activation_energy": _quantity(8.31446261815324, "kJ/mol"),
                           "reference_temperature": _quantity(300, "K")}}
    reaction = _reaction(**law)
    # At Tref, noncompetitive factor = 4/(4+Bout). Solve CSTR numerically.
    lower, upper = 0.0, 10.0
    for _ in range(80):
        x = (lower + upper) / 2
        a, b = 10 - x, x
        rate = 5 * a / (2 + a) * 4 / (4 + b)
        if rate > x:
            lower = x
        else:
            upper = x
    extent = (lower + upper) / 2
    result = verify_rate_law_reactor(reactor_type="CSTR", reaction=reaction, volume_m3=1,
                                     inlet=_stream(10, 0), outlet=_stream(10 - extent, extent))
    assert result["ok"] is True
