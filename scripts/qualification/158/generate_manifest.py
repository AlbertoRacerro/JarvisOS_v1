"""Normalize checked-in DWSIM 10.2.9 probe captures into the 158 capability manifest."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
EVIDENCE = ROOT / "backend/app/modules/process_stack/evidence/158"
OUT = ROOT / "backend/app/modules/process_stack/dwsim_10_2_9_manifest.json"
TYPES = ("Heater", "Cooler", "Pump", "Valve", "Mixer", "Vessel", "Splitter", "HeatExchanger",
         "Recycle", "PFR", "DistillationColumn")


def main() -> None:
    evidence = json.loads((EVIDENCE / "units.json").read_text(encoding="utf-8"))
    objects = {}
    for name in TYPES:
        probe = evidence[name]
        results = probe["results"]
        dof = probe.get("dof", {})
        slots = dof.get("slots", [])
        spec_props = {slot["property"] for slot in slots}
        objects[name] = {
            "native_type": probe["add"].get("type", name),
            "modes": results.get("calculation_modes", []),
            "observed_mode": results.get("calculation_mode"),
            "settable_properties": sorted(spec_props),
            "dof": {"mode": dof.get("mode"), "supported": bool(dof.get("supported")),
                    "slots": [{"property": row.get("property"), "units": row.get("units"),
                               "required": bool(row.get("required"))} for row in slots]},
            "result_properties": [{"name": key, "unit": value.get("units", ""),
                                   "classification": "input" if key in spec_props else "result"}
                                  for key, value in sorted(results.get("properties", {}).items())],
        }
        if name == "DistillationColumn" and dof.get("mode"):
            objects[name]["modes"] = [dof["mode"]]
    # ReactorOperationMode is an enum on the native object rather than a calculation-mode
    # list returned by dwsim_unitop_get_results; these alternatives came from the accepted
    # pinned-runtime probe and are retained explicitly instead of inferred from labels.
    objects["PFR"]["modes"] = ["Isothermic", "Adiabatic", "OutletTemperature",
                                "NonIsothermalNonAdiabatic", "HeatExchange"]
    pfr_applied = json.loads((EVIDENCE / "pfr_ok.json").read_text(encoding="utf-8"))["set"]["applied"]
    objects["PFR"]["settable_properties"] = sorted(set(objects["PFR"]["settable_properties"])
                                                    | {row.split(" = ", 1)[0] for row in pfr_applied})
    column_probe = json.loads((EVIDENCE / "column2.json").read_text(encoding="utf-8"))
    column_applied = column_probe.get("set", {}).get("applied", [])
    objects["DistillationColumn"]["settable_properties"] = sorted(
        set(objects["DistillationColumn"]["settable_properties"])
        | {row.split(" = ", 1)[0] for row in column_applied}
    )
    energy = json.loads((EVIDENCE / "ports.json").read_text(encoding="utf-8"))
    energy_result = energy.get("h_Q", {})
    objects["EnergyStream"] = {
        "native_type": "EnergyStream", "modes": [], "observed_mode": None,
        "settable_properties": ["EnergyFlow"], "dof": {"mode": None, "supported": True, "slots": []},
        "result_properties": [{"name": key, "unit": value.get("units", ""), "classification": "result"}
                              for key, value in sorted(energy_result.get("properties", {}).items())],
    }
    manifest = {"runtime": "DWSIM 10.2.9", "probe_sha256": "d20f9742", "source": "evidence/158/units.json",
                "objects": objects,
                "verified": {"energy_stream": "ports.json: energy port 1 and EnergyFlow setter",
                             "pfr_heat_exchange_reaction": "pfr_ok.json: native reaction-set reload and solve",
                             "distillation_column": "column2.json: condenser/reboiler connection rejected; solve missing streams"}}
    OUT.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
