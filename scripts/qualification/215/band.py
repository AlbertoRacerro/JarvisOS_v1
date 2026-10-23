"""Spec 215 declared-assumption uncertainty band for the C1 layouts.

Run from ``backend/`` (each case runs in its own temporary data root)::

    PYTHONPATH=. python ../scripts/qualification/215/band.py --workers 20 \\
        --out ../scripts/qualification/215/band_results.json

The plan is a one-at-a-time sensitivity sweep around the central run plus a
small seeded Monte Carlo. Every range below is a declared assumption or a
transferred source range; none is chosen from, or fitted to, C1 observations.
``summarize`` rebuilds the band report from the pinned per-case results.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import random
import runpy
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
_CENTRAL = runpy.run_path(str(HERE / "central_run.py"))
_INPUTS = runpy.run_path(str(HERE / "scenario_inputs.py"))
_CARD = runpy.run_path(str(HERE / "card_candidates.py"))["build_audit"]()
LAYOUTS = _INPUTS["LAYOUTS"]
SEED = 215
MONTE_CARLO_SAMPLES = 64

_MU = _CARD["candidates"]["mu_max"]["value"]
_KI = _CARD["relative_candidates"]["K_I"]["value"]
_KD = _CARD["relative_candidates"]["k_d"]["value"]
_KX = _CARD["relative_candidates"]["k_X"]["range"]
_KS = _CARD["nutrient_candidates"]["K_j_0"]["range"]

# name -> (kind, OAT levels, Monte Carlo law, state). Cross-section levels name
# each layout's first (spec 212 proxy) or second (alternative) optical module.
FACTORS: dict[str, dict[str, Any]] = {
    "forcing_window": {"levels": ["low", "median", "high"], "law": ("choice", ["low", "median", "high"]),
                       "state": "scenario; lowest/median/highest-PAR 36-day KNMI surrogate windows"},
    "culture_temperature_c": {"levels": [20.0, 30.0], "law": ("uniform", 20.0, 30.0),
                              "state": "assumed constant inside S01's maintained 20-30 C"},
    "axis_azimuth_deg": {"levels": [45.0, 90.0], "law": ("choice", [0.0, 45.0, 90.0]),
                         "state": "scenario; S01 gives no array azimuth"},
    "cross_section": {"levels": ["alternative"], "law": ("choice", ["primary", "alternative"]),
                      "state": "assumed optical module; 3x1/1x3 horizontal, 1x7/2x3 fence"},
    "illuminated_volume_basis": {"levels": ["reported_illuminated_share"],
                                 "law": ("choice", ["tube_cylinder", "reported_illuminated_share"]),
                                 "state": "S01 reported illuminated share or calculated tube cylinder"},
    "k_X": {"levels": [_KX[1]], "law": ("uniform", _KX[0], _KX[1]),
            "state": "cross-strain Lima 2022 annular/flat fitted values as bounds"},
    "K_I": {"levels": [_KI / 2, _KI * 2], "law": ("loguniform", _KI / 2, _KI * 2),
            "state": "assumed factor-2 screening range around cross-strain Lima 2022; no source interval"},
    "k_d": {"levels": [_KD / 2, _KD * 2], "law": ("loguniform", _KD / 2, _KD * 2),
            "state": "assumed factor-2 screening range around cross-strain Lima 2022; no source interval"},
    "mu_max": {"levels": [_MU * 0.8, _MU * 1.2], "law": ("uniform", _MU * 0.8, _MU * 1.2),
               "state": "assumed +/-20% screening range around same-strain 2025 value; no source interval used"},
    "initial_biomass_kg_m3": {"levels": [0.5, 2.0], "law": ("loguniform", 0.5, 2.0),
                              "state": "assumed start; S01 reports no aligned initial state"},
    "K_j_0": {"levels": [_KS[0], _KS[1]], "law": ("uniform", _KS[0], _KS[1]),
              "state": "cross-strain Sanchez-Bayo 2020 4 +/- 2 mg NO3/L converted to N"},
}


def _override(name: str, value: Any) -> dict[str, Any]:
    if name == "cross_section":
        index = 0 if value == "primary" else 1
        return {name: {layout: list(row["cross_sections"][index]) for layout, row in LAYOUTS.items()}}
    return {name: value}


def build_plan(seed: int = SEED, samples: int = MONTE_CARLO_SAMPLES) -> list[dict[str, Any]]:
    """Central case, one-at-a-time levels, then seeded Monte Carlo draws."""
    plan: list[dict[str, Any]] = [{"id": "central", "kind": "central", "factor": None, "draw": {}}]
    for name, factor in FACTORS.items():
        for level in factor["levels"]:
            plan.append({"id": f"oat_{name}_{level}", "kind": "oat", "factor": name, "draw": {name: level}})
    rng = random.Random(seed)
    for index in range(samples):
        draw: dict[str, Any] = {}
        for name, factor in FACTORS.items():
            law = factor["law"]
            if law[0] == "choice":
                draw[name] = rng.choice(law[1])
            elif law[0] == "uniform":
                draw[name] = rng.uniform(law[1], law[2])
            else:
                draw[name] = math.exp(rng.uniform(math.log(law[1]), math.log(law[2])))
        plan.append({"id": f"mc_{index:03d}", "kind": "monte_carlo", "factor": None, "draw": draw})
    return plan


def overrides_for(draw: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for name, value in draw.items():
        result.update(_override(name, value))
    return result


def run_one(case: dict[str, Any], days: float | None = None) -> dict[str, Any]:
    """Run one plan case in this process's (isolated) data root."""
    from app.core.database import initialize_database
    from app.modules.workspaces.models import WorkspaceCreate
    from app.modules.workspaces.service import create_workspace

    initialize_database()
    workspace = create_workspace(WorkspaceCreate(name=f"C1 215 {case['id']}", slug="c1-215-band")).id
    output = _CENTRAL["run_central"](workspace, days=days, overrides=overrides_for(case["draw"]))
    return {**case, "layouts": {
        name: {key: row[key] for key in (
            "predicted_areal_g_m2_day", "predicted_volumetric_g_l_day", "harvest_g",
            "inventory_change_g", "produced_g", "harvest_only_areal_g_m2_day",
            "illuminated_volume_m3", "min_pbr_nitrogen_kg_m3", "biomass_residual_rel")}
        for name, row in output["layouts"].items()}, "summary_sha256": output["summary_sha256"]}


def _run_subprocess(case: dict[str, Any], backend: Path, days: float | None) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="c1-215-band-") as root:
        env = {**os.environ, "JARVISOS_DATA_ROOT": root, "PYTHONPATH": str(backend),
               "OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1", "MKL_NUM_THREADS": "1"}
        command = [sys.executable, str(Path(__file__).resolve()), "--case", json.dumps(case)]
        if days is not None:
            command += ["--days", str(days)]
        done = subprocess.run(command, cwd=backend, env=env, capture_output=True, text=True, check=False)
        if done.returncode != 0:
            raise RuntimeError(f"{case['id']} failed:\n{done.stderr[-4000:]}")
        return json.loads(done.stdout.strip().splitlines()[-1])


def _quantile(values: list[float], q: float) -> float:
    """Linear-interpolated sample quantile (numpy default 'linear')."""
    ordered = sorted(values)
    position = (len(ordered) - 1) * q
    low = math.floor(position)
    high = min(low + 1, len(ordered) - 1)
    return ordered[low] + (ordered[high] - ordered[low]) * (position - low)


METRICS = ("predicted_areal_g_m2_day", "predicted_volumetric_g_l_day")
OBSERVED = {"predicted_areal_g_m2_day": "observed_areal_g_m2_day",
            "predicted_volumetric_g_l_day": "observed_volumetric_g_l_day"}


def summarize(results: list[dict[str, Any]]) -> dict[str, Any]:
    """Band, spread ranking and comparison from per-case results (pure, offline)."""
    by_kind: dict[str, list[dict[str, Any]]] = {}
    for row in results:
        by_kind.setdefault(row["kind"], []).append(row)
    central = by_kind["central"][0]
    mc = by_kind["monte_carlo"]
    layouts: dict[str, Any] = {}
    for layout, source in LAYOUTS.items():
        entry: dict[str, Any] = {}
        for metric in METRICS:
            values = [row["layouts"][layout][metric] for row in mc]
            observed = source[OBSERVED[metric]]
            band = {"p05": _quantile(values, 0.05), "median": _quantile(values, 0.5),
                    "p95": _quantile(values, 0.95), "min": min(values), "max": max(values)}
            spread = {}
            for name in FACTORS:
                oat = [row["layouts"][layout][metric] for row in by_kind["oat"] if row["factor"] == name]
                points = oat + [central["layouts"][layout][metric]]
                spread[name] = max(points) - min(points)
            entry[metric] = {
                "central": central["layouts"][layout][metric], "observed": observed, **band,
                "observed_inside_5_95": band["p05"] <= observed <= band["p95"],
                "observed_quantile": sum(value <= observed for value in values) / len(values),
                "oat_spread_ranking": sorted(spread.items(), key=lambda item: (-item[1], item[0])),
            }
        layouts[layout] = entry
    direction = {}
    for metric, observed_fence_higher in (("predicted_areal_g_m2_day", True),
                                          ("predicted_volumetric_g_l_day", False)):
        paired = [row["layouts"]["fence"][metric] > row["layouts"]["horizontal"][metric] for row in mc]
        direction[metric] = {"observed_fence_higher": observed_fence_higher,
                             "share_of_draws_fence_higher": sum(paired) / len(paired),
                             "central_fence_higher": central["layouts"]["fence"][metric]
                             > central["layouts"]["horizontal"][metric]}
    summary = {"status": "declared-assumption band; surrogate forcing; assumed / not qualified card",
               "seed": SEED, "monte_carlo_samples": len(mc), "oat_cases": len(by_kind["oat"]),
               "layouts": layouts, "direction": direction}
    summary["band_sha256"] = band_digest(summary)
    return summary


def band_digest(summary: dict[str, Any]) -> str:
    """Digest of the band summary with floats to 6 significant digits."""
    def stable(value: Any) -> Any:
        if isinstance(value, dict):
            return {key: stable(item) for key, item in value.items() if key != "band_sha256"}
        if isinstance(value, (list, tuple)):
            return [stable(item) for item in value]
        if isinstance(value, float):
            return float(f"{value:.6g}")
        return value

    return hashlib.sha256(json.dumps(stable(summary), sort_keys=True, separators=(",", ":"),
                                     allow_nan=False).encode()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", help="internal: run one JSON plan case and print its result")
    parser.add_argument("--days", type=float, default=None, help="truncate runs (testing only)")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--samples", type=int, default=MONTE_CARLO_SAMPLES)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    if args.case:
        print(json.dumps(run_one(json.loads(args.case), args.days), sort_keys=True, allow_nan=False))
        return
    backend = Path.cwd().resolve()
    plan = build_plan(samples=args.samples)
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        results = list(pool.map(lambda case: _run_subprocess(case, backend, args.days), plan))
    payload = {"plan_sha256": hashlib.sha256(json.dumps(plan, sort_keys=True).encode()).hexdigest(),
               "days": args.days, "factors": {name: {key: row[key] for key in ("levels", "law", "state")}
                                              for name, row in FACTORS.items()},
               "results": results, "summary": summarize(results)}
    text = json.dumps(payload, indent=1, sort_keys=True, allow_nan=False)
    if args.out:
        args.out.write_text(text + "\n", encoding="utf-8")
    print(json.dumps(payload["summary"], indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
