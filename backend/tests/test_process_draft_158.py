"""Evidence-derived DWSIM capability contract for process drafts (spec 158)."""

from pydantic import TypeAdapter

from app.modules.process_stack import draft_compiler
from app.modules.process_stack.draft import apply_ops, empty_document, registry_projection
from app.modules.process_stack.draft_compiler import _stream_result
from app.modules.process_stack.draft_models import UNIT_REGISTRY, UNSUPPORTED_TYPES, DraftOp


def test_registry_modes_and_ports_are_present_in_pinned_manifest() -> None:
    projection = registry_projection()
    manifest = projection["dwsim_capabilities"]
    assert manifest["runtime"] == "DWSIM 10.2.9"
    for unit in UNIT_REGISTRY.values():
        capability = manifest["objects"][unit.dwsim_type]
        assert set(unit.modes.values()) <= set(capability["modes"])
        assert capability["native_type"] in unit.native_types


def test_manifest_exposes_reported_property_catalogue_and_column_limit() -> None:
    projection = registry_projection()
    entries = {item["type"]: item for item in projection["units"]}
    assert entries["Heater"]["result_properties"]
    assert {item["classification"] for item in entries["Heater"]["result_properties"]} <= {"input", "result"}
    assert "DistillationColumn" in UNIT_REGISTRY
    assert "DistillationColumn" not in UNSUPPORTED_TYPES


def test_stream_result_keeps_dwsim_report_without_recalculation() -> None:
    reported = {
        "temperature_K": 300.0,
        "properties": {"Cp": {"value": "4.2", "units": "kJ/kg.K", "specification": False}},
        "phases": [{"name": "Mixture", "compounds": {"Water": {"mass_fraction": 1.0}}}],
    }
    result = _stream_result(reported)
    assert result["reported"] == reported
    assert result["temperature_K"] == 300.0


def test_energy_stream_and_layout_routes_compile_orthogonally() -> None:
    document = empty_document("Energy train")
    ops = [
        {"op": "set_thermo", "compounds": ["Water"], "property_package": "NRTL"},
        {"op": "add_unit", "id": "heater", "type": "Heater", "tag": "H1", "x": 0, "y": 0},
        {"op": "add_stream", "id": "feed", "tag": "F", "x": 0, "y": 0},
        {"op": "add_stream", "id": "product", "tag": "P", "x": 0, "y": 0},
        {"op": "add_stream", "id": "duty", "tag": "Q", "stream_type": "energy", "x": 0, "y": 0},
        {"op": "set_stream_spec", "stream": "feed", "temperature": {"value": 25, "unit": "degC"},
         "pressure": {"value": 1, "unit": "bar"}, "mass_flow": {"value": 1, "unit": "kg/s"},
         "composition": {"Water": 1.0}},
        {"op": "connect", "stream": "feed", "end": "target", "unit": "heater", "port": 0},
        {"op": "connect", "stream": "product", "end": "source", "unit": "heater", "port": 0},
        {"op": "connect", "stream": "duty", "end": "target", "unit": "heater", "port": 0},
        {"op": "set_unit_params", "unit": "heater", "mode": "energy_stream"},
        {"op": "set_stream_spec", "stream": "duty", "duty": {"value": 50, "unit": "kW"}},
    ]
    adapter = TypeAdapter(DraftOp)
    canonical = apply_ops(document, [adapter.validate_python(op) for op in ops])
    calls = draft_compiler.plan(canonical)
    assert ("dwsim_stream_add_energy", {"name": "Q"}) in calls
    assert ("dwsim_unitop_connect", {"unitop": "H1", "energy_feed": "Q", "energy_feed_port": 1}) in calls
    assert ("dwsim_unitop_set", {"name": "Q", "properties": {"EnergyFlow": 50.0}}) in calls
    expected = draft_compiler.expected(canonical)
    routed = apply_ops(canonical, [adapter.validate_python({
        "op": "set_route", "stream": "duty", "points": [{"x": 0, "y": 0}, {"x": 10, "y": 0}],
    })])
    assert draft_compiler.expected(routed) == expected
    assert draft_compiler._native_energy_port({"type": "PFR"}, 0) == 1


def test_readback_comparison_covers_energy_duty_and_reaction_configuration() -> None:
    expected = {
        "compounds": [], "property_package": None, "objects": {}, "connections": [], "feeds": {},
        "energy_streams": {"Q": {"EnergyFlow": 12.0}},
        "reactions": {"R1": {"name": "hydration", "stoichiometry": {"A": -1.0, "B": 1.0},
                              "orders": {"A": 1.0, "B": 0.0}, "base_reactant": "A", "phase": "Mixture",
                              "basis": "MolarConc", "A_forward": 0.005, "A_forward_unit": "kmol/[m3.h]",
                              "E_forward": 1000.0, "E_forward_unit": "J/mol"}},
        "reaction_sets": {"JARVIS_R": ["R1"]}, "units": {},
    }
    actual = {**expected, "energy_streams": {"Q": {"EnergyFlow": 11.0}},
              "reactions": {"R1": {**expected["reactions"]["R1"], "A_forward": 0.006}}}
    paths = {item["path"] for item in draft_compiler.compare(expected, actual)}
    assert "energy_streams.Q.EnergyFlow" in paths
    assert "reactions.R1.A_forward" in paths


def test_kinetic_reaction_is_typed_attached_and_materialized_by_native_set() -> None:
    adapter = TypeAdapter(DraftOp)
    document = apply_ops(empty_document("Reactive train"), [
        adapter.validate_python({"op": "set_thermo", "compounds": ["Water", "Ethylene oxide", "Ethylene glycol"],
                                 "property_package": "NRTL"}),
        adapter.validate_python({"op": "set_reactions", "reactions": {
            "R1": {"name": "Hydration", "stoichiometry": {"Ethylene oxide": -1, "Water": -1,
                                                                      "Ethylene glycol": 1},
                   "orders": {"Ethylene oxide": 1}, "base_reactant": "Ethylene oxide", "phase": "Mixture",
                   "basis": "MolarConc", "A_forward": {"value": 0.005, "unit": "kmol/[m3.h]"},
                   "E_forward": {"value": 0, "unit": "J/mol"}},
        }}),
        adapter.validate_python({"op": "add_unit", "id": "pfr", "type": "PFR", "tag": "R", "x": 0, "y": 0}),
        adapter.validate_python({"op": "set_unit_params", "unit": "pfr", "mode": "heat_exchange",
                                 "reactions": ["R1"], "values": {
                                     "volume": {"value": 2, "unit": "m3"}, "length": {"value": 4, "unit": "m"},
                                     "overall_coefficient": {"value": 400, "unit": "W/[m2.K]"},
                                     "heat_exchange_area": {"value": 12, "unit": "m2"},
                                     "coolant_inlet_temperature": {"value": 26.85, "unit": "degC"},
                                     "coolant_mass_flow": {"value": 2, "unit": "kg/s"},
                                     "coolant_specific_heat": {"value": 4180, "unit": "J/kg.K"},
                                 }}),
    ])
    normalized = draft_compiler.expected(document)
    assert normalized["units"]["R"]["ReactorOperationMode"] == "HeatExchange"
    assert normalized["units"]["R"]["__ReactionSetID"] == "JARVIS_R"
    assert draft_compiler.plan(document)[-1] == ("dwsim_unitop_set", {"name": "R", "properties": {
        "ReactorOperationMode": "HeatExchange", "Volume": 2.0, "Length": 4.0, "DeltaP": 0.0,
        "OverallHeatTransferCoefficient": 400.0, "HeatExchangeArea": 12.0,
        "CoolantInletTemperature": 300.0, "CoolantMassFlowRate": 2.0,
        "CoolantSpecificHeat": 4180.0,
    }})
