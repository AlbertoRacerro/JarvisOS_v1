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
    manifest = {"runtime": "DWSIM 10.2.9", "probe_sha256": "d20f9742", "source": "evidence/158/units.json",
                "objects": objects,
                "verified": {"energy_stream": "ports.json: energy port 1 and EnergyFlow setter",
                             "pfr_heat_exchange_reaction": "pfr_ok.json: native reaction-set reload and solve",
                             "distillation_column": "column2.json: condenser/reboiler connection rejected; solve missing streams"}}
    OUT.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
