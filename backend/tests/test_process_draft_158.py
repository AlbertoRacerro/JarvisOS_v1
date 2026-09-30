"""Evidence-derived DWSIM capability contract for process drafts (spec 158)."""

import importlib.util
from pathlib import Path
from typing import Any

from pydantic import TypeAdapter

from app.modules.process_stack import draft_compiler
from app.modules.process_stack.draft import _capability_manifest, apply_ops, empty_document, registry_projection
from app.modules.process_stack.draft_compiler import _native_energy_port, _stream_result, _unit_properties
from app.modules.process_stack.draft_models import UNIT_REGISTRY, UNSUPPORTED_TYPES, DraftOp

_ROOT = Path(__file__).resolve().parents[2]
_GENERATOR = _ROOT / "scripts" / "qualification" / "158" / "generate_manifest.py"
_MANIFEST = _ROOT / "backend" / "app" / "modules" / "process_stack" / "dwsim_10_2_9_manifest.json"
_CONNECT_ROLES = {"feed_port": "feed", "product_port": "product",
                  "energy_feed_port": "energy_feed", "energy_product_port": "energy_product"}
# Properties Jarvis writes through dwsim_unitop_set that no checked-in 158 probe capture proves
# settable on the pinned runtime. Heater OutletTemperature/CalcMode, Pump CalcMode/Pout/Efficiency
# and Valve CalcMode/OutletPressure were exercised by the 155 host acceptance, whose capture is not
# checked in; the others have no capture at all. This set must equal the observed gap exactly, so
# it can only shrink as probe evidence is recaptured or the fields are withdrawn.
_UNCAPTURED_INPUTS = {
    ("Heater", "OutletTemperature"), ("Heater", "DeltaT"), ("Heater", "OutletVaporFraction"),
    ("Cooler", "CalcMode"), ("Cooler", "OutletTemperature"), ("Cooler", "DeltaT"),
    ("Cooler", "OutletVaporFraction"),
    ("Pump", "CalcMode"), ("Pump", "Pout"), ("Pump", "Efficiency"),
    ("Valve", "CalcMode"), ("Valve", "OutletPressure"),
}


def _modes(unit_type: str) -> tuple[str | None, ...]:
    return tuple(UNIT_REGISTRY[unit_type].modes) or (None,)


def _synthetic_document(unit_type: str, mode: str | None) -> dict[str, Any]:
    """A compile-ready draft with every parameter of ``mode`` set and every port occupied."""
    spec = UNIT_REGISTRY[unit_type]
    objects: dict[str, Any] = {"u": {
        "id": "u", "kind": "unit", "type": unit_type, "tag": "U", "x": 0, "y": 0, "mode": mode,
        "params": {item.key: {"si": 1.0} for item in spec.params_for(mode)}, "options": {},
        "reactions": ["R1"] if unit_type == "PFR" else []}}

    def stream(tag: str, kind: str, end: str, port: int) -> None:
        feed = {"temperature": {"si": 300.0}, "pressure": {"si": 1e5}, "mass_flow": {"si": 1.0}}
        objects[tag.lower()] = {"id": tag.lower(), "kind": "stream", "type": kind, "tag": tag, "x": 0, "y": 0,
                                "source": {"unit": "u", "port": port} if end == "source" else None,
                                "target": {"unit": "u", "port": port} if end == "target" else None,
                                "spec": {"duty": {"si": 1.0}} if kind == "EnergyStream" else
                                feed if end == "target" else {}}

    for port in range(len(spec.inlets)):
        stream(f"F{port}", "MaterialStream", "target", port)
    for port in range(len(spec.outlets)):
        stream(f"P{port}", "MaterialStream", "source", port)
    for port in range(len(spec.energy_inlets)):
        stream(f"QF{port}", "EnergyStream", "target", port)
    for port in range(len(spec.energy_outlets)):
        stream(f"QP{port}", "EnergyStream", "source", port)
    return {"compounds": [], "property_package": "NRTL", "objects": objects, "reactions": {}}


def _compiled_writes() -> tuple[set[tuple[str, str]], set[tuple[str, str, int]]]:
    """Every (type, property) the compiler sets and every (type, role, port) it connects over MCP."""
    written: set[tuple[str, str]] = set()
    connected: set[tuple[str, str, int]] = set()
    for unit_type in UNIT_REGISTRY:
        for mode in _modes(unit_type):
            for name, args in draft_compiler.plan(_synthetic_document(unit_type, mode)):
                owner = unit_type if args.get("name", args.get("unitop")) == "U" else "EnergyStream"
                if name == "dwsim_unitop_set":
                    written |= {(owner, key) for key in args["properties"]}
                elif name == "dwsim_unitop_connect":
                    connected |= {(unit_type, role, args[key]) for key, role in _CONNECT_ROLES.items() if key in args}
    return written, connected


def _manifest_object(unit_type: str) -> dict[str, Any]:
    manifest = _capability_manifest()
    native = UNIT_REGISTRY[unit_type].dwsim_type if unit_type in UNIT_REGISTRY else unit_type
    return manifest["objects"][native]


def test_checked_in_manifest_equals_generator_output() -> None:
    spec = importlib.util.spec_from_file_location("generate_manifest_158", _GENERATOR)
    assert spec and spec.loader
    generator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(generator)
    assert _MANIFEST.read_text(encoding="utf-8") == generator.render()


def test_every_compiled_input_property_is_settable_in_the_manifest() -> None:
    written, _connected = _compiled_writes()
    assert ("EnergyStream", "EnergyFlow") in written
    missing = {(unit_type, prop) for unit_type, prop in written
               if prop not in _manifest_object(unit_type)["settable_properties"]}
    assert missing == _UNCAPTURED_INPUTS
    for unit_type, prop in written - _UNCAPTURED_INPUTS:
        assert _manifest_object(unit_type)["settable_property_evidence"][prop]
    for unit_type, spec in UNIT_REGISTRY.items():
        native_xml = _manifest_object(unit_type)["native_xml_inputs"]
        registry_native = {item.dwsim_property for item in spec.params if item.dwsim_property.startswith("__")}
        compiled_native = {key for mode in _modes(unit_type)
                           for key in _unit_properties(_synthetic_document(unit_type, mode)["objects"]["u"])
                           if key.startswith("__") and not key.startswith("__SplitRatio")}
        assert registry_native | compiled_native <= set(native_xml), unit_type


def test_every_registry_mode_and_enum_value_is_in_the_manifest() -> None:
    for unit_type, spec in UNIT_REGISTRY.items():
        capability = _manifest_object(unit_type)
        assert set(spec.modes.values()) <= set(capability["modes"]), unit_type
        assert all(capability["mode_evidence"][mode] for mode in spec.modes.values())
        for mode in _modes(unit_type):
            properties = _unit_properties(_synthetic_document(unit_type, mode)["objects"]["u"])
            for key in {"CalcMode", "CalculationMode", "OperationMode", "ReactorOperationMode"} & set(properties):
                assert properties[key] in capability["modes"], (unit_type, key)
            if "CondenserType" in properties:
                assert properties["CondenserType"] in capability["enum_values"]["CondenserType"]


def test_every_registry_and_compiled_port_is_a_manifest_native_port() -> None:
    _written, connected = _compiled_writes()
    used = set(connected)
    for unit_type, spec in UNIT_REGISTRY.items():
        unit = {"type": unit_type}
        used |= {(unit_type, "feed", port) for port in range(len(spec.inlets))}
        used |= {(unit_type, "product", port) for port in range(len(spec.outlets))}
        used |= {(unit_type, "energy_feed", _native_energy_port(unit, port)) for port in range(len(spec.energy_inlets))}
        used |= {(unit_type, "energy_product", _native_energy_port(unit, port))
                 for port in range(len(spec.energy_outlets))}
    for unit_type, role, port in used:
        entries = {item["port"]: item for item in _manifest_object(unit_type)["ports"].get(role, [])}
        assert port in entries, (unit_type, role, port)
        assert entries[port]["evidence"], (unit_type, role, port)
    evidence_dir = _MANIFEST.parent / "evidence" / "158"
    for capability in _capability_manifest()["objects"].values():
        for entries in capability["ports"].values():
            for entry in entries:
                if entry["captured"]:
                    assert all((evidence_dir / source.split(":", 1)[0]).is_file() for source in entry["evidence"])


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
    assert draft_compiler._NATIVE_TO_TYPE["Reactor_PFR"] == "PFR"


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


def test_heat_exchanger_and_two_outlet_splitter_use_native_mode_fields() -> None:
    adapter = TypeAdapter(DraftOp)
    document = apply_ops(empty_document("Verified operation modes"), [
        adapter.validate_python({"op": "set_thermo", "compounds": ["Water"], "property_package": "NRTL"}),
        adapter.validate_python({"op": "add_unit", "id": "hx", "type": "HeatExchanger", "tag": "HX", "x": 0, "y": 0}),
        adapter.validate_python({"op": "set_unit_params", "unit": "hx", "mode": "calc_both_temp_ua",
                                "values": {"overall_coefficient": {"value": 1000, "unit": "W/[m2.K]"},
                                           "area": {"value": 1, "unit": "m2"}}}),
    ])
    assert draft_compiler.expected(document)["units"]["HX"]["CalculationMode"] == "CalcBothTemp_UA"
    unitop_set = next(args for name, args in draft_compiler.plan(document) if name == "dwsim_unitop_set")
    assert unitop_set["properties"]["CalculationMode"] == "CalcBothTemp_UA"
    assert "CalcMode" not in unitop_set["properties"]


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
