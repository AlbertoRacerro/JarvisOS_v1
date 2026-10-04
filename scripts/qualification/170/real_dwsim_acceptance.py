"""Exact-head, real-DWSIM Process acceptance for the Spec 170 Photobioreactor.

Run only against an integrated candidate with the 170 scientific evaluator. This script
creates an isolated data root, a synthetic-unqualified 169 card, fresh Process drafts,
and calls the actual FastAPI routes and configured DWSIM MCP. Evidence is written on
failure as well as success. It contains measured values only, never a golden result.

Example:
  JARVISOS_DWSIM_MCP_PATH=/path/to/dwsim-mcp \
  JARVISOS_170_EVIDENCE=/tmp/170-acceptance.json \
  backend/.venv/bin/python scripts/qualification/170/real_dwsim_acceptance.py
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "backend"))
OUTPUT = Path(os.environ.get("JARVISOS_170_EVIDENCE", "/tmp/jarvisos-170-real-dwsim.json"))
FIXTURE_PATH = ROOT / "scripts" / "qualification" / "107" / "synthetic-parameters.json"
FIXTURE = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))["coefficients"]


def Q(value: float, unit: str) -> dict[str, Any]:  # noqa: N802 - short quantity builder used throughout the cases
    return {"value": value, "unit": unit}


def _fixture(name: str) -> tuple[float, str]:
    value, unit = FIXTURE[name]
    return float(value), str(unit)


# The 107 synthetic fixture supplies the growth coefficients (read from the JSON, never copied). The Monod
# card, feed, continuous dilution and cylindrical optics are 170 cases, not 107 validation data.
SYNTHETIC_VALUES = {
    "K_I": _fixture("light_saturation_constant"), "k_X": _fixture("specific_light_extinction"),
    "T_min": _fixture("temperature_min"), "T_opt": _fixture("temperature_opt"), "T_max": _fixture("temperature_max"),
    "K_j_0": _fixture("nitrogen_half_saturation"),
    "k_d": (_fixture("biomass_loss_rate")[0], "1/hour"),
    # Algebraically fitted synthetic formula: 169 NH3 stoichiometry gives the fixture's
    # q = biomass_nitrogen_fraction and Y_O2 = oxygen_yield (checked in main). It is not measured.
    "a": (1.8, "1"), "b": (0.5129883263806922, "1"), "c": (0.12688224202537762, "1"),
    "d": (0.01, "1"), "w_ash": (0.05, "1"),
}
OXYGEN_YIELD = FIXTURE["oxygen_yield"][0]
FIXTURE_KLA_H = FIXTURE["oxygen_kla"][0]
FIXTURE_O2_SATURATION = FIXTURE["oxygen_saturation"][0]  # kg/m3
CARD_FACTORS = {
    "light": "light.monod", "optics": "optics.slab_response_average",
    "temperature": "temperature.ctmi", "nutrients": ["nutrient.monod"],
    "combination": "combine.liebig", "loss": "loss.first_order",
    "stoichiometry": "stoich.photoautotrophic",
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _expect(condition: bool, label: str, detail: Any, report: dict[str, Any]) -> None:
    report["assertions"].append({"label": label, "passed": bool(condition), "detail": detail})
    if not condition:
        raise AssertionError(f"{label}: {json.dumps(detail, default=str)[:1000]}")


def _write(report: dict[str, Any]) -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False, default=str) + "\n", encoding="utf-8")


def _request(client: Any, method: str, path: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
    response = client.request(method, path, json=body)
    if response.status_code >= 400:
        raise RuntimeError(f"{method} {path}: HTTP {response.status_code}: {response.text[:1200]}")
    return response.json()


def _card(client: Any, workspace_id: str, *, name: str, changes: dict[str, tuple[float, str]] | None = None) -> dict[str, Any]:
    base = f"/workspaces/{workspace_id}/bio-models"
    parameter_set = _request(client, "POST", f"{base}/sets", {"name": f"{name} — synthetic, unqualified"})
    for symbol, (value, unit) in {**SYNTHETIC_VALUES, **(changes or {})}.items():
        parameter_set = _request(client, "PUT", f"{base}/sets/{parameter_set['id']}/values/{symbol}", {
            "expected_revision": parameter_set["revision"], "expected_digest": parameter_set["digest"],
            "value": value, "unit": unit, "expected_unit": unit,
            "conditions": "Synthetic solver exercise only; no biological qualification or source claim.",
        })
    card = _request(client, "POST", f"{base}/cards", {
        "name": name, "parameter_set_id": parameter_set["id"], "factors": CARD_FACTORS,
        "mu_max": Q(0.0625, "1/hour"), "n_source": "NH3",
    })
    return {"card": card, "set": parameter_set}


def _pbr_params(*, oxygen_kla_h: float = FIXTURE_KLA_H, peak_par: float = 800.0) -> dict[str, Any]:
    return {
        "tube_inner_diameter": Q(0.05, "m"), "tube_length": Q(100, "m"),
        "tube_count": Q(10, "dimensionless"), "liquid_velocity": Q(0.5, "m/s"),
        "pump_efficiency": Q(60, "percent"), "baffle_friction_multiplier": Q(1, "dimensionless"),
        "oxygen_kla": Q(oxygen_kla_h, "1/h"), "oxygen_saturation": Q(FIXTURE_O2_SATURATION * 1000.0, "mg/L"),
        "peak_par": Q(peak_par, "umol/(m2.s)"), "photoperiod": Q(12, "h"),
        "diffuse_fraction": Q(0.5, "dimensionless"),
        "temperature_mean": Q(298.15, "K"), "temperature_amplitude": Q(3, "K"),
    }


def _flow_for_hrt(hrt_days: float) -> float:
    # 997 kg/m³ is a setup estimate only; the evaluator uses the real DWSIM inlet density.
    volume_m3 = 10 * math.pi / 4 * 0.05**2 * 100
    return volume_m3 * 997 / (hrt_days * 86400)


def _ops(pin: dict[str, Any], *, hrt_days: float, biomass: float = 0.0,
         nitrogen: float = 0.05,
         oxygen: float = FIXTURE_O2_SATURATION, oxygen_kla_h: float = FIXTURE_KLA_H, peak_par: float = 800.0,
         mixed: bool = False) -> list[dict[str, Any]]:
    def stream(id: str, tag: str, x: int, y: int) -> dict[str, Any]:
        return {"op": "add_stream", "id": id, "tag": tag, "x": x, "y": y}

    def unit(id: str, type: str, tag: str, x: int, y: int) -> dict[str, Any]:
        return {"op": "add_unit", "id": id, "type": type, "tag": tag, "x": x, "y": y}

    def connect(stream_id: str, end: str, unit_id: str, port: int = 0) -> dict[str, Any]:
        return {"op": "connect", "stream": stream_id, "end": end, "unit": unit_id, "port": port}

    flow = _flow_for_hrt(hrt_days)
    shared = [
        {"op": "set_thermo", "compounds": ["Water"], "property_package": "NRTL"},
        stream("feed", "CultureFeed", 30, 100),
        {"op": "set_stream_spec", "stream": "feed", "temperature": Q(25, "degC"),
         "pressure": Q(2, "bar"), "mass_flow": Q(flow, "kg/s"), "composition": {"Water": 1}},
        {"op": "set_stream_culture", "stream": "feed", "culture": {
            "biomass": Q(biomass, "kg/m3"), "nitrogen": Q(nitrogen, "kg/m3"),
            "oxygen": Q(oxygen, "kg/m3"), "salinity": Q(35, "g/kg")}},
        unit("pbr", "PhotobioreactorT1", "PBR", 280, 100),
        {"op": "set_unit_params", "unit": "pbr", "values": _pbr_params(oxygen_kla_h=oxygen_kla_h, peak_par=peak_par)},
        {"op": "set_unit_model", "unit": "pbr", "model": {
            "card_id": pin["id"], "card_revision": pin["revision"], "card_digest": pin["digest"]}},
    ]
    if not mixed:
        return [*shared, stream("product", "Product", 530, 100),
                connect("feed", "target", "pbr"), connect("product", "source", "pbr")]
    # 168 consumed tear: culture feed + return → Mixer → PBR → Jarvis separator;
    # clarified carrier → DWSIM Splitter → Heater → Recycle → Mixer.
    return [*shared, stream("tear", "Return", 30, 230), unit("mix", "Mixer", "Mixer", 150, 150),
            stream("mixed", "Mixed", 230, 150), stream("grown", "Grown", 390, 150),
            unit("sep", "SpecifiedSeparator", "Separator", 490, 150),
            stream("concentrate", "Concentrate", 590, 70), stream("clarified", "Clarified", 590, 225),
            unit("split", "Splitter", "Splitter", 690, 225),
            stream("purge", "Purge", 790, 180), stream("toheat", "ToHeater", 790, 270),
            unit("heater", "Heater", "Heater", 900, 270), stream("torecycle", "ToRecycle", 1000, 270),
            unit("recycle", "Recycle", "Recycle", 1100, 270),
            connect("feed", "target", "mix"), connect("tear", "source", "recycle"),
            connect("tear", "target", "mix", 1), connect("mixed", "source", "mix"),
            connect("mixed", "target", "pbr"), connect("grown", "source", "pbr"),
            connect("grown", "target", "sep"), connect("concentrate", "source", "sep"),
            connect("clarified", "source", "sep", 1), connect("clarified", "target", "split"),
            connect("purge", "source", "split"), connect("toheat", "source", "split", 1),
            connect("toheat", "target", "heater"), connect("torecycle", "source", "heater"),
            connect("torecycle", "target", "recycle"),
            {"op": "set_unit_params", "unit": "sep", "mode": "specified", "values": {
                "biomass_recovery": Q(90, "percent"), "concentration_factor": Q(10, "dimensionless")}},
            {"op": "set_unit_params", "unit": "split", "mode": "split_ratios", "values": {
                "split_ratio_1": Q(0.5, "dimensionless"), "split_ratio_2": Q(0.5, "dimensionless")}},
            {"op": "set_unit_params", "unit": "heater", "mode": "outlet_temperature", "values": {
                "outlet_temperature": Q(30, "degC")}}]


def _seed(client: Any, workspace_id: str, name: str, ops: list[dict[str, Any]]) -> dict[str, Any]:
    base = f"/workspaces/{workspace_id}/process/drafts"
    created = _request(client, "POST", base, {"name": name})
    patched = _request(client, "POST", f"{base}/{created['draft_id']}/patch", {
        "expected_revision": created["revision"], "ops": ops})
    return {"base": base, "draft_id": created["draft_id"], "projection": patched}


def _run(client: Any, seed: dict[str, Any]) -> dict[str, Any]:
    projection = seed["projection"]
    path = f"{seed['base']}/{seed['draft_id']}/revisions/{projection['revision']}/run"
    response = _request(client, "POST", path)
    return response["run"]


def _reported(run: dict[str, Any], key: str) -> float:
    row = run["units"]["PBR"]["reported"][key]
    value = row["value"]
    if not isinstance(value, (int, float)) or not math.isfinite(value):
        raise AssertionError(f"PBR reported {key} is not finite: {row}")
    return float(value)


def _elapsed_s(run: dict[str, Any]) -> float:
    return (datetime.fromisoformat(run["finished_at"]) - datetime.fromisoformat(run["started_at"])).total_seconds()


def _case(client: Any, workspace_id: str, report: dict[str, Any], name: str,
          pin: dict[str, Any], *, hrt_days: float, expected: str, **inputs: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    seed = _seed(client, workspace_id, name, _ops(pin, hrt_days=hrt_days, **inputs))
    run = _run(client, seed)
    report["cases"][name] = {"draft_id": seed["draft_id"], "revision": seed["projection"]["revision"],
                             "pre_run_findings": seed["projection"].get("findings"), "run": run}
    _write(report)
    _expect(run.get("dwsim_version") == "10.2.9", f"{name}: real DWSIM 10.2.9", run.get("dwsim_version"), report)
    _expect(run.get("status") == expected, f"{name}: run status", {
        "actual": run.get("status"), "reason": (run.get("mixed_solve") or {}).get("reason")}, report)
    return seed, run


def _balances(run: dict[str, Any], name: str, report: dict[str, Any]) -> None:
    unit = run["units"]["PBR"]
    for field in ("biomass", "nitrogen", "oxygen"):
        row = unit["unit_balances"][field]
        _expect(row["passed"] and abs(row["residual"]) <= row["tolerance"],
                f"{name}: PBR {field} unit balance", row, report)
        whole = run["mixed_solve"]["balances"][field]
        _expect(whole["passed"] and abs(whole["residual"]) <= whole["tolerance"],
                f"{name}: {field} whole-graph balance", whole, report)
    _oxygen_transfer(run, name, report)


def _oxygen_transfer(run: dict[str, Any], name: str, report: dict[str, Any]) -> None:
    """Signed net O2 gas transfer is reported with its direction and closes the PBR O2 balance."""
    unit = run["units"]["PBR"]
    transfer = unit["reported"]["oxygen_gas_transfer"]
    production = unit["reported"]["net_biomass_production"]
    _expect(transfer["units"] == "kg/d" and "degassing" in transfer["label"] and "absorption" in transfer["label"],
            f"{name}: signed O2 gas transfer is labelled with its direction", transfer, report)
    row = unit["unit_balances"]["oxygen"]
    # Net O2 generation (kg/s) = Y_O2 * biomass production - signed gas transfer (+ out of the liquid).
    expected = (OXYGEN_YIELD * float(production["value"]) - float(transfer["value"])) / 86400.0
    _expect(abs(row["generated"] - expected) <= row["tolerance"],
            f"{name}: O2 generation equals Y_O2 production minus signed gas transfer",
            {"generated_kg_s": row["generated"], "expected_kg_s": expected, "tolerance": row["tolerance"]}, report)
    _expect(abs(row["in"] - row["out"] + row["generated"]) <= row["tolerance"] + row.get("generation_allowance", 0.0),
            f"{name}: O2 balance closes with the signed transfer",
            {"in": row["in"], "out": row["out"], "generated": row["generated"],
             "transfer_kg_d": transfer["value"], "direction": "degassing" if transfer["value"] > 0 else "absorption"},
            report)


def _failure_code(run: dict[str, Any]) -> str | None:
    detail: Any = (run.get("mixed_solve") or {}).get("errors") or run.get("error_detail")
    for _ in range(5):
        if isinstance(detail, list):
            detail = detail[0] if detail else None
        if not isinstance(detail, dict):
            break
        if isinstance(detail.get("code"), str):
            return detail["code"]
        detail = detail.get("detail")
    return None


def main() -> None:
    runtime = Path(os.environ["JARVISOS_DWSIM_MCP_PATH"]).resolve()
    if not runtime.is_file():
        raise SystemExit(f"DWSIM MCP not found: {runtime}")
    os.environ["JARVISOS_DWSIM_MCP_SHA256"] = _sha256(runtime)
    report: dict[str, Any] = {
        "source_sha": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "dwsim_required": "10.2.9", "dwsim_mcp_sha256": _sha256(runtime),
        "synthetic_fixture": "scripts/qualification/107/synthetic-parameters.json",
        "cases": {}, "assertions": [], "complete": False,
    }
    try:
        from app.modules.bio_models import forms

        yields = forms.stoich_photoautotrophic(*(SYNTHETIC_VALUES[key][0] for key in ("a", "b", "c", "d", "w_ash")),
                                               "NH3")["yields"]
        _expect(abs(yields["N_consumed_kg_per_kg_total_dry"] - FIXTURE["biomass_nitrogen_fraction"][0]) < 1e-9
                and abs(yields["O2_produced_kg_per_kg_total_dry"] - OXYGEN_YIELD) < 1e-9,
                "fitted stoichiometry reproduces the 107 fixture q and Y_O2", yields, report)
        with tempfile.TemporaryDirectory(prefix="jarvisos-170-accept-") as data_root:
            os.environ["JARVISOS_DATA_ROOT"] = data_root
            from fastapi.testclient import TestClient

            from app.core.config import get_settings
            from app.core.database import initialize_database
            from app.main import app

            get_settings.cache_clear()
            initialize_database()
            with TestClient(app) as client:
                workspace = _request(client, "POST", "/workspaces", {
                    "name": "170 real DWSIM acceptance", "slug": "accept-170-real"})
                workspace_id = workspace["id"]
                standard = _card(client, workspace_id, name="170 synthetic Monod screening card")
                card = standard["card"]
                report["pin"] = {key: card[key] for key in ("id", "revision", "digest", "parameter_set_id",
                                                               "parameter_set_revision", "parameter_set_digest")}

                productive_seed, productive = _case(client, workspace_id, report, "productive_once_through", card,
                                                    hrt_days=3, expected="completed")
                _expect(productive["units"]["PBR"]["branch"] == "productive", "productive branch",
                        productive["units"]["PBR"].get("branch"), report)
                productive_lambda = _reported(productive, "lambda_h")
                productive_dilution = 1 / (24 * _reported(productive, "hrt_d"))
                _expect(productive_lambda > productive_dilution,
                        "productive thin-culture growth exceeds measured dilution",
                        {"lambda_h": productive_lambda, "dilution_h": productive_dilution}, report)
                _balances(productive, "productive", report)

                washout_seed, washout = _case(client, workspace_id, report, "washout_once_through", card,
                                             hrt_days=1.5, expected="completed")
                _expect(washout["units"]["PBR"]["branch"] == "washout", "washout branch",
                        washout["units"]["PBR"].get("branch"), report)
                washout_lambda = _reported(washout, "lambda_h")
                washout_dilution = 1 / (24 * _reported(washout, "hrt_d"))
                _expect(washout_lambda < washout_dilution,
                        "washout thin-culture growth is below measured dilution",
                        {"lambda_h": washout_lambda, "dilution_h": washout_dilution}, report)
                product_biomass = washout["culture"]["Product"]["values"]["biomass"]["mass_specific"]
                _expect(isinstance(product_biomass, (int, float)) and abs(product_biomass) < 1e-9,
                        "washout outlet biomass is zero", product_biomass, report)
                _expect("PBR_WASHOUT" in {finding.get("code") for finding in washout["units"]["PBR"].get("findings", [])},
                        "washout finding visible in unit result", washout["units"]["PBR"].get("findings"), report)
                _balances(washout, "washout", report)

                _, changed_inlet = _case(client, workspace_id, report, "changed_culture_inlet", card,
                                         hrt_days=3, expected="completed", biomass=0.01,
                                         nitrogen=0.03, oxygen=0.008)
                _expect(changed_inlet["units"]["PBR"]["branch"] == "productive",
                        "changed inlet still has a certified productive branch",
                        changed_inlet["units"]["PBR"].get("branch"), report)
                _balances(changed_inlet, "changed inlet", report)

                # Compare two fresh Runs of the same mixed draft; measured results must repeat.
                mixed_seed, mixed = _case(client, workspace_id, report, "mixed_dwsim_loop", card,
                                          hrt_days=8, expected="completed", mixed=True)
                repeated = _run(client, mixed_seed)
                report["cases"]["mixed_dwsim_loop"]["repeat"] = repeated
                _expect(repeated["status"] == "completed", "mixed repeat completed", repeated["status"], report)
                _expect(_elapsed_s(mixed) < 90 and _elapsed_s(repeated) < 90,
                        "mixed DWSIM runs each under 90 seconds",
                        {"first_s": _elapsed_s(mixed), "repeat_s": _elapsed_s(repeated)}, report)
                _expect(mixed["units"]["PBR"]["owner"] == "jarvis_bio"
                        and mixed["units"]["Mixer"]["owner"] == "dwsim"
                        and mixed["units"]["Heater"]["owner"] == "dwsim",
                        "mixed calculation ownership", {tag: item.get("owner") for tag, item in mixed["units"].items()}, report)
                _balances(mixed, "mixed", report)
                for key in ("hrt_d", "lambda_h", "biomass_mean", "nitrogen_mean", "oxygen_mean",
                            "volumetric_productivity", "pressure_drop", "pumping_power"):
                    first, second = _reported(mixed, key), _reported(repeated, key)
                    _expect(abs(first - second) <= 1e-9 * max(abs(first), abs(second), 1e-12),
                            f"mixed repeat {key} within 1e-9 relative", [first, second], report)

                # A real completed result must stale on a semantic edit, stay current on layout,
                # and never adopt a newer card/set revision without an explicit pin change.
                base = productive_seed["base"]
                draft_id = productive_seed["draft_id"]
                latest = _request(client, "GET", f"{base}/{draft_id}")
                moved = _request(client, "POST", f"{base}/{draft_id}/patch", {
                    "expected_revision": latest["revision"],
                    "ops": [{"op": "move", "id": "pbr", "x": 300, "y": 110}]})
                _expect(moved["results"]["state"] == "current", "layout edit preserves current result",
                        moved["results"], report)
                edited = _request(client, "POST", f"{base}/{draft_id}/patch", {
                    "expected_revision": moved["revision"], "ops": [{"op": "set_unit_params", "unit": "pbr",
                    "values": {"peak_par": Q(810, "umol/(m2.s)")}}]})
                _expect(edited["results"]["state"] == "stale", "PBR parameter edit stales result",
                        edited["results"], report)
                # Revising the library set alone leaves the PBR's document pin unchanged.
                current_set = _request(client, "GET", f"/workspaces/{workspace_id}/bio-models/sets/{standard['set']['id']}")
                _request(client, "PUT", f"/workspaces/{workspace_id}/bio-models/sets/{current_set['id']}/values/k_X", {
                    "expected_revision": current_set["revision"], "expected_digest": current_set["digest"],
                    "value": 151.0, "unit": "m**2/kg", "expected_unit": "m**2/kg"})
                still_current = _request(client, "GET", f"{washout_seed['base']}/{washout_seed['draft_id']}")
                _expect(still_current["results"]["state"] == "current",
                        "newer set revision does not stale pinned PBR", still_current["results"], report)
                pinned = _request(client, "GET", f"{base}/{draft_id}")
                unit = next(item for item in pinned["objects"] if item["tag"] == "PBR")
                _expect(unit["model"] == {"card_id": card["id"], "card_revision": card["revision"],
                                                   "card_digest": card["digest"]},
                        "set edit never repins an existing PBR", unit.get("model"), report)

                # Typed failures retain unit, code and operator message in the 168 failed segment. The oxygen
                # case is the contract scenario: no aeration, no inlet O2 and dark biomass decay (a lit,
                # productive culture makes net O2 and certifies a positive periodic O2).
                _, oxygen_failure = _case(client, workspace_id, report, "nonphysical_oxygen", card,
                                          hrt_days=3, expected="segment_failed", biomass=0.1,
                                          oxygen=0.0, oxygen_kla_h=0.0, peak_par=0.0)
                _expect(_failure_code(oxygen_failure) == "PBR_NONPHYSICAL_STATE", "typed oxygen failure",
                        oxygen_failure.get("mixed_solve"), report)
                no_feedback = _card(client, workspace_id, name="170 synthetic no-feedback card",
                                    changes={"c": (0.0, "1"), "k_X": (0.0, "m**2/kg")})["card"]
                _, no_finite = _case(client, workspace_id, report, "no_finite_productive_state", no_feedback,
                                     hrt_days=5, expected="segment_failed", biomass=0.01)
                _expect(_failure_code(no_finite) == "PBR_NO_FINITE_PRODUCTIVE_STATE", "typed no-finite failure",
                        no_finite.get("mixed_solve"), report)

                repin = _request(client, "POST", f"{washout_seed['base']}/{washout_seed['draft_id']}/patch", {
                    "expected_revision": washout_seed["projection"]["revision"],
                    "ops": [{"op": "set_unit_model", "unit": "pbr", "model": {
                        "card_id": no_feedback["id"], "card_revision": no_feedback["revision"],
                        "card_digest": no_feedback["digest"]}}]})
                _expect(repin["results"]["state"] == "stale", "explicit card repin stales result",
                        repin["results"], report)
                report["complete"] = True
    except Exception as exc:
        report["error"] = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        _write(report)


if __name__ == "__main__":
    main()
