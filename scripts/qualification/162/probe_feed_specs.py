"""Probe which material-feed specifications the pinned DWSIM 10.2.9 MCP really accepts (spec 162).

Each case builds a water/ethanol feed -> Heater -> product flowsheet, applies one ordered set of
feed calls, then records the raw MCP responses, the saved native stream specification
(``SpecType``/``DefinedFlow``), the pre-solve read-back, the check and the solve. The editor
exposes only alternatives this evidence proves; ``draft_compiler.plan`` uses the proven calls.

    JARVISOS_DWSIM_MCP_PATH=... JARVISOS_DWSIM_MCP_SHA256=... \\
        backend/.venv/bin/python scripts/qualification/162/probe_feed_specs.py
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "backend"))

from app.modules.process_stack.dwsim_mcp import DwsimMcpClient

OUT = ROOT / "backend/app/modules/process_stack/evidence/162/feed_specs.json"
COMPOSITION = {"Water": 0.6, "Ethanol": 0.4}
ADD = "dwsim_stream_add_material"
SET = "dwsim_stream_set_conditions"
UNITOP_SET = "dwsim_unitop_set"
T_P = {"temperature_K": 330.0, "pressure_Pa": 101325.0, "composition": COMPOSITION}
# Each case: ordered calls on feed "F". Arguments are exactly what the MCP received.
CASES: dict[str, list[tuple[str, dict[str, Any]]]] = {
    "mass_flow_in_add": [(ADD, {**T_P, "mass_flow_kg_s": 1.5})],
    "molar_flow_in_add": [(ADD, {**T_P, "molar_flow_mol_s": 40.0})],
    "mass_and_molar_in_add": [(ADD, {**T_P, "mass_flow_kg_s": 1.5, "molar_flow_mol_s": 40.0})],
    "molar_flow_set_conditions": [(ADD, T_P), (SET, {"molar_flow_mol_s": 40.0})],
    "molar_then_mass_set_conditions": [(ADD, T_P), (SET, {"molar_flow_mol_s": 40.0}), (SET, {"mass_flow_kg_s": 2.0})],
    "molar_flow_unitop_PROP_MS_3": [(ADD, T_P), (UNITOP_SET, {"properties": {"PROP_MS_3": 40.0}})],
    "zero_mass_in_add": [(ADD, {**T_P, "mass_flow_kg_s": 0.0})],
    "zero_mass_set_conditions": [(ADD, T_P), (SET, {"mass_flow_kg_s": 0.0})],
    "zero_mass_unitop_PROP_MS_2": [(ADD, T_P), (UNITOP_SET, {"properties": {"PROP_MS_2": 0.0}})],
    "zero_molar_unitop_PROP_MS_3": [(ADD, T_P), (UNITOP_SET, {"properties": {"PROP_MS_3": 0.0}})],
    "no_flow_given": [(ADD, T_P)],
    "vapor_fraction_in_add_only": [(ADD, {"pressure_Pa": 101325.0, "composition": COMPOSITION, "vapor_fraction": 0.3,
                                         "mass_flow_kg_s": 2.0})],
    "vapor_fraction_in_add_spec_PVF": [(ADD, {"pressure_Pa": 101325.0, "composition": COMPOSITION,
                                             "vapor_fraction": 0.3, "mass_flow_kg_s": 2.0}),
                                       (UNITOP_SET, {"properties": {"SpecType": "Pressure_and_VaporFraction"}})],
    "vapor_fraction_PROP_MS_27_spec_PVF_after_flow": [
        (ADD, {"pressure_Pa": 101325.0, "composition": COMPOSITION, "mass_flow_kg_s": 2.0}),
        (UNITOP_SET, {"properties": {"SpecType": "Pressure_and_VaporFraction", "PROP_MS_27": 0.3}})],
    "vapor_fraction_PROP_MS_27_then_set_conditions": [
        (ADD, {"pressure_Pa": 101325.0, "composition": COMPOSITION}),
        (UNITOP_SET, {"properties": {"SpecType": "Pressure_and_VaporFraction", "PROP_MS_27": 0.3}}),
        (SET, {"molar_flow_mol_s": 40.0})],
    "molar_flow_then_vapor_fraction": [
        (ADD, {"pressure_Pa": 101325.0, "composition": COMPOSITION}), (SET, {"molar_flow_mol_s": 40.0}),
        (UNITOP_SET, {"properties": {"SpecType": "Pressure_and_VaporFraction", "PROP_MS_27": 0.3}})],
    "mole_fractions_PROP_MS_102": [
        (ADD, {"temperature_K": 330.0, "pressure_Pa": 101325.0, "mass_flow_kg_s": 1.0}),
        (UNITOP_SET, {"properties": {"PROP_MS_102/Water": 0.5, "PROP_MS_102/Ethanol": 0.5}})],
    "mole_fractions_then_molar_flow": [
        (ADD, {"temperature_K": 330.0, "pressure_Pa": 101325.0}),
        (UNITOP_SET, {"properties": {"PROP_MS_102/Water": 0.5, "PROP_MS_102/Ethanol": 0.5}}),
        (SET, {"molar_flow_mol_s": 40.0})],
    "mass_flow_set_conditions": [(ADD, T_P), (SET, {"mass_flow_kg_s": 1.5})],
    "mole_fractions_then_mass_set_conditions": [
        (ADD, {"temperature_K": 330.0, "pressure_Pa": 101325.0}),
        (UNITOP_SET, {"properties": {"PROP_MS_102/Water": 0.5, "PROP_MS_102/Ethanol": 0.5}}),
        (SET, {"mass_flow_kg_s": 1.5})],
    "mole_fractions_mass_flow_vapor_fraction": [
        (ADD, {"pressure_Pa": 101325.0}),
        (UNITOP_SET, {"properties": {"PROP_MS_102/Water": 0.5, "PROP_MS_102/Ethanol": 0.5}}),
        (SET, {"mass_flow_kg_s": 1.5}),
        (UNITOP_SET, {"properties": {"SpecType": "Pressure_and_VaporFraction", "PROP_MS_27": 0.3}})],
    "invalid_spec_type": [(ADD, T_P), (UNITOP_SET, {"properties": {"SpecType": "Bogus"}})],
}


def _raw(client: DwsimMcpClient, name: str, args: dict[str, Any], timeout: float = 60) -> Any:
    response = client._request("tools/call", {"name": name, "arguments": args}, timeout)
    if response.get("isError"):
        text = " ".join(block.get("text", "") for block in response.get("content", []) if isinstance(block, dict))
        return {"__error__": text, "structured": response.get("structuredContent")}
    if response.get("structuredContent") is not None:
        return response["structuredContent"]
    text = response["content"][0]["text"]
    try:
        return json.loads(text)
    except ValueError:
        return {"text": text}


def _native_feed(path: Path, tag: str) -> dict[str, Any]:
    root = ElementTree.parse(path).getroot()
    names = {node.findtext("Name"): node.findtext("Tag") for node in root.findall("./GraphicObjects/GraphicObject")}
    for node in root.findall("./SimulationObjects/SimulationObject"):
        if names.get(node.findtext("Name")) == tag:
            return {key: node.findtext(key) for key in ("SpecType", "DefinedFlow", "CompositionBasis")}
    return {"__missing__": tag}


def _summary(result: Any) -> Any:
    if not isinstance(result, dict) or "phases" not in result:
        return result
    phases = {phase.get("name"): phase for phase in result["phases"]}
    return {**{key: result.get(key) for key in ("temperature_K", "pressure_Pa", "mass_flow_kg_s", "molar_flow_mol_s")},
            "vapor_fraction": phases.get("Vapor", {}).get("fraction"),
            "mixture": phases.get("Mixture", {}).get("compounds")}


def _case(client: DwsimMcpClient, name: str, steps: list[tuple[str, dict[str, Any]]], tmp: Path) -> dict[str, Any]:
    out: dict[str, Any] = {"steps": []}
    flow = _raw(client, "dwsim_flowsheet_create", {"name": f"probe-{name}"})["flowsheet_id"]
    _raw(client, "dwsim_thermo_add_compounds", {"flowsheet_id": flow, "names": list(COMPOSITION)})
    _raw(client, "dwsim_thermo_set_property_package", {"flowsheet_id": flow, "name": "NRTL"})
    for tool, args in steps:
        out["steps"].append({"tool": tool, "args": args,
                             "response": _raw(client, tool, {"flowsheet_id": flow, "name": "F", **args})})
    _raw(client, ADD, {"flowsheet_id": flow, "name": "P"})
    _raw(client, "dwsim_unitop_add", {"flowsheet_id": flow, "type": "Heater", "name": "H"})
    _raw(client, "dwsim_unitop_connect", {"flowsheet_id": flow, "unitop": "H", "feed_stream": "F", "feed_port": 0})
    _raw(client, "dwsim_unitop_connect", {"flowsheet_id": flow, "unitop": "H", "product_stream": "P", "product_port": 0})
    _raw(client, UNITOP_SET, {"flowsheet_id": flow, "name": "H",
                              "properties": {"CalcMode": "OutletTemperature", "OutletTemperature": 380.0}})
    out["feed_before_solve"] = _summary(_raw(client, "dwsim_stream_get_results", {"flowsheet_id": flow, "name": "F"}))
    case = tmp / f"{name}.dwxml"
    _raw(client, "dwsim_flowsheet_save", {"flowsheet_id": flow, "filepath": str(case), "compressed": False})
    out["native_feed_before_solve"] = _native_feed(case, "F")
    out["check"] = _raw(client, "dwsim_flowsheet_check", {"flowsheet_id": flow})
    solve = _raw(client, "dwsim_solve_run", {"flowsheet_id": flow, "timeout_s": 60}, 90)
    out["solve"] = {key: solve.get(key) for key in ("ok", "errors", "error_count")} if isinstance(solve, dict) else solve
    out["feed_after_solve"] = _summary(_raw(client, "dwsim_stream_get_results", {"flowsheet_id": flow, "name": "F"}))
    out["product_after_solve"] = _summary(_raw(client, "dwsim_stream_get_results", {"flowsheet_id": flow, "name": "P"}))
    _raw(client, "dwsim_flowsheet_close", {"flowsheet_id": flow})
    return out


def main() -> None:
    executable = Path(os.environ["JARVISOS_DWSIM_MCP_PATH"])
    digest = os.environ["JARVISOS_DWSIM_MCP_SHA256"]
    results: dict[str, Any] = {"runtime_sha256": digest, "composition_input": COMPOSITION, "cases": {}}
    with tempfile.TemporaryDirectory(prefix="probe162-") as tmp, DwsimMcpClient(executable, digest) as client:
        tools = client._request("tools/list", {}, 30).get("tools", [])
        results["tool_schemas"] = {tool["name"]: tool.get("inputSchema") for tool in tools
                                   if tool["name"] in {"dwsim_stream_add_material", "dwsim_stream_set_conditions"}}
        for name, steps in CASES.items():
            try:
                results["cases"][name] = _case(client, name, steps, Path(tmp))
            except Exception as exc:  # noqa: BLE001 - a refused case is itself evidence
                results["cases"][name] = {"steps": steps, "__exception__": f"{type(exc).__name__}: {exc}"}
            print(name, "done", flush=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(results, indent=1, sort_keys=True), encoding="utf-8")
    print(OUT)


if __name__ == "__main__":
    main()
