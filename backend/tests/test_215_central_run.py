"""Structural coverage of the spec 215 central declared-assumption C1 run."""

from __future__ import annotations

import math
import runpy
from pathlib import Path

from app.core.database import initialize_database
from app.modules.workspaces.models import WorkspaceCreate
from app.modules.workspaces.service import create_workspace

SCRIPT = Path(__file__).resolve().parents[2] / "scripts/qualification/215/central_run.py"


def test_central_run_reaches_both_layouts_through_t2_loop_owners() -> None:
    initialize_database()
    wid = create_workspace(WorkspaceCreate(name="C1 central", slug="c1-central-test")).id
    output = runpy.run_path(str(SCRIPT))["run_central"](wid, days=2.0)
    assert "not the uncertainty band and not a verdict" in output["status"]
    assert "truncated to 2.0 d" in output["status"]
    assert any("surrogate" in label for label in output["labels"])
    assert any("assumed / not qualified" in label for label in output["labels"])
    assert set(output["states"]) == {key for key, _ in output["central"].items()}
    for name, row in output["layouts"].items():
        assert row["days"] == 2.0
        assert row["dark_volume_m3"] > 0
        assert math.isclose(row["illuminated_volume_m3"] + row["dark_volume_m3"], row["working_volume_m3"])
        assert math.isclose(row["feed_m3_s"] * 86400 / row["working_volume_m3"], row["dilution_per_day"])
        assert row["harvest_g"] > 0
        assert math.isclose(row["predicted_areal_g_m2_day"] * row["ground_area_m2"],
                            row["predicted_volumetric_g_l_day"] * 1000 * row["working_volume_m3"])
        # The nutrient-replete assumption must hold: N stays far above the 4 mg/L nitrate K_S.
        assert row["min_pbr_nitrogen_kg_m3"] > 100 * 0.0009036, name
        assert row["biomass_residual_rel"] < 1e-9


def test_summary_digest_ignores_run_local_ids_and_round_off_only() -> None:
    digest = runpy.run_path(str(SCRIPT))["summary_digest"]
    base = {"profile_digest": "sha256:x", "card_digest": "a",
            "layouts": {"fence": {"predicted_areal_g_m2_day": 27.800837568980686,
                                  "snapshot_digest": "b", "biomass_residual_rel": 2.7e-13}}}
    noisy = {"profile_digest": "sha256:x", "card_digest": "c",
             "layouts": {"fence": {"predicted_areal_g_m2_day": 27.800837568999505,
                                   "snapshot_digest": "d", "biomass_residual_rel": 3.5e-13}}}
    moved = {**base, "layouts": {"fence": {**base["layouts"]["fence"], "predicted_areal_g_m2_day": 27.8008}}}
    assert digest(base) == digest(noisy)
    assert digest(base) != digest(moved)
    assert digest(base) != digest({**base, "profile_digest": "sha256:y"})
