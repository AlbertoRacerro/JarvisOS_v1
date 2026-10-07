"""Measure real-card 30-day T1 productive and washout branches for spec 172."""

from __future__ import annotations

import json
import os
import resource
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "backend"))

from app.core.paths import build_paths  # noqa: E402
from app.modules.process_stack import draft, dynamic_engine  # noqa: E402
from app.modules.process_stack.draft_models import SetScenario  # noqa: E402
from tests.plumbing_170_support import new_workspace  # noqa: E402
from tests.test_process_dynamic_engine import _real_scenario  # noqa: E402

EVIDENCE = Path("/home/thera/jarvis-control/work/evidence/172")


def _branch(workspace_id: str, flow_m3_s: float, label: str) -> dict[str, Any]:
    state, _ = _real_scenario(workspace_id, 30 * 86400)
    directory = draft.draft_dir(workspace_id, state["draft_id"])
    head = draft._head(directory)
    revision = draft.load_revision(directory, head["revision"])
    scenario = dict(revision["document"]["scenarios"]["run"])
    scenario["feed_flows"] = {"Feed": flow_m3_s}
    state = draft.patch(
        workspace_id, state["draft_id"], state["revision"],
        [SetScenario(op="set_scenario", id="run", value=scenario)],
    )
    snapshot = dynamic_engine.prepare(workspace_id, state["draft_id"], "run")
    before_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    started = time.perf_counter()
    result = dynamic_engine.run(snapshot, cancelled=lambda: False, progress=lambda _value: None)
    wall_s = time.perf_counter() - started
    peak_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    peak_rss_bytes = int(peak_rss if sys.platform == "darwin" else peak_rss * 1024)
    card = snapshot.payload["units"][0]["model"].get("card", {})
    with tempfile.TemporaryDirectory(prefix="jarvis-172-qualification-") as directory_name:
        artifact = Path(directory_name) / "series.npz"
        np.savez_compressed(artifact, **result.series)
        artifact_size = artifact.stat().st_size
    initial_x = snapshot.payload["units"][0]["state"][0]
    final_x = float(result.series["PBR_X"][-1]) if len(result.series.get("PBR_X", [])) else None
    verdict = "productive" if final_x is not None and final_x > initial_x else "washout" if final_x is not None else "failed"
    return {
        "branch": label,
        "status": result.status,
        "error": result.error,
        "git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "workspace_id": workspace_id,
        "draft_id": snapshot.payload["draft_id"],
        "draft_revision": snapshot.payload["revision"],
        "content_digest": snapshot.payload["content_digest"],
        "card": {key: card.get(key) for key in ("id", "revision", "digest")},
        "profile": snapshot.payload["profiles"][0]["ref"],
        "solver": result.manifest.get("solver"),
        "wall_time_s": wall_s,
        "output_count": len(result.series.get("t_s", [])),
        "peak_rss_platform_units": peak_rss,
        "peak_rss_bytes": peak_rss_bytes,
        "rss_growth_platform_units": peak_rss - before_rss,
        "artifact_npz_bytes": artifact_size,
        "balance_residuals": result.manifest.get("balances"),
        "initial_biomass_kg_m3": initial_x,
        "final_biomass_kg_m3": final_x,
        "branch_verdict": verdict,
    }


def main() -> None:
    if not os.environ.get("JARVISOS_DATA_ROOT"):
        raise SystemExit("Set JARVISOS_DATA_ROOT to an isolated temporary directory and bootstrap it first.")
    build_paths().data_root.mkdir(parents=True, exist_ok=True)
    workspace = new_workspace()
    outcomes = [
        _branch(workspace, 1e-6, "productive"),
        _branch(workspace, 5e-2, "washout"),
    ]
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    target = EVIDENCE / "qualify_30d.json"
    report = {
        "branches": outcomes,
        "four_pbr_bluerev_loop": {
            "status": "not_run",
            "reason": "The qualification builder covers single-PBR branch cases only; no four-PBR result is claimed.",
        },
    }
    target.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(target)
    print(json.dumps(outcomes, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
