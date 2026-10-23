"""Pin the C1 surrogate CSV as immutable environment profiles.

``pin_profile`` freezes the hourly import and its T2 site context; the 174 T2
owner needs the 15-minute child from ``pin_t2_profile``. The site is the KNMI station used to decompose the weather record, not an
AlgaePARC site measurement. The resulting profile is an input artifact only.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

from app.modules.environment import profiles

HERE = Path(__file__).resolve().parent
CSV = HERE / "knmi_2013_deelen_surrogate.csv"
MAPPING = HERE / "environment_mapping.json"
SITE = {"name": "KNMI Deelen 275 surrogate", "latitude": 52.056,
        "longitude": 5.873, "elevation_m": 48.20,
        "timezone": "UTC", "water_body": "land"}
PAR_UMOL_PER_J = 0.45 * 4.57
# The 174 T2 owner evaluates the sun at interval midpoints and refuses profiles
# coarser than 15 minutes. KNMI gives hourly means only.
T2_STEP_MINUTES = 15


def pin_profile(workspace_id: str) -> dict:
    """Import through the 171 owner, then freeze T2 context in its provenance."""
    mapping = json.loads(MAPPING.read_text(encoding="utf-8"))
    imported = profiles.confirm_csv(workspace_id, CSV, CSV.name, mapping)
    provenance = {
        **imported["provenance"],
        "site_snapshot": SITE,
        "factor_umol_per_j": PAR_UMOL_PER_J,
        "qualification_context": "spec 215 surrogate weather; C1 campaign dates unknown",
    }
    return profiles.create_profile(
        workspace_id, name="C1 surrogate KNMI Deelen; pinned T2 context",
        timestamps=imported["timestamps"], channels=imported["channels"],
        resolution_minutes=imported["resolution_minutes"], provenance=provenance,
        parent_digest=imported["digest"], profile_label="surrogate; not AlgaePARC measured",
    )


def pin_t2_profile(workspace_id: str) -> dict:
    """Hold each hourly surrogate mean over its four 15-minute sub-intervals.

    No sub-hourly weather is invented: every channel keeps its hourly mean, so the
    hourly beam-normal and diffuse PAR dose is unchanged. Only the T2 sun geometry
    moves to 15-minute midpoints, which is the declared surrogate construction.
    """
    hourly = pin_profile(workspace_id)
    split = 60 // T2_STEP_MINUTES
    stamps = []
    for stamp in hourly["timestamps"]:
        end = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
        stamps += [(end - timedelta(minutes=T2_STEP_MINUTES * k)).isoformat().replace("+00:00", "Z")
                   for k in range(split - 1, -1, -1)]
    channels = {name: [value for value in values for _ in range(split)]
                for name, values in hourly["channels"].items()}
    provenance = {
        **hourly["provenance"],
        "subhourly_construction": f"hourly means held over {split} x {T2_STEP_MINUTES} min intervals "
                                  "for the T2 midpoint-sun limit; no sub-hourly weather is observed",
    }
    return profiles.create_profile(
        workspace_id, name="C1 surrogate KNMI Deelen; 15 min hold for T2",
        timestamps=stamps, channels=channels, resolution_minutes=T2_STEP_MINUTES,
        provenance=provenance, parent_digest=hourly["digest"],
        profile_label="surrogate; not AlgaePARC measured",
    )
