"""Pin the C1 surrogate CSV as an immutable, T2-ready environment profile.

The site is the KNMI station used to decompose the weather record, not an
AlgaePARC site measurement. The resulting profile is an input artifact only.
"""

from __future__ import annotations

import json
from pathlib import Path

from app.modules.environment import profiles

HERE = Path(__file__).resolve().parent
CSV = HERE / "knmi_2013_deelen_surrogate.csv"
MAPPING = HERE / "environment_mapping.json"
SITE = {"name": "KNMI Deelen 275 surrogate", "latitude": 52.056,
        "longitude": 5.873, "elevation_m": 48.20,
        "timezone": "UTC", "water_body": "land"}
PAR_UMOL_PER_J = 0.45 * 4.57


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
