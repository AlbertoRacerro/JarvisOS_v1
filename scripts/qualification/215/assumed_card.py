"""Create one explicitly assumed C1 card through the spec 169 owner.

The caller supplies an isolated workspace. This module never edits an existing
card or marks a literature value verified. It does not fit C1 observations.
"""

from __future__ import annotations

import runpy
from pathlib import Path

HERE = Path(__file__).resolve().parent
AUDIT = runpy.run_path(str(HERE / "card_candidates.py"))["build_audit"]()

UNITS = {
    "K_I": "umol/(m**2*s)", "K_j_0": "kg/m3", "k_d": "1/hour",
    "k_X": "m**2/kg", "T_min": "K", "T_opt": "K", "T_max": "K",
    "a": "1", "b": "1", "c": "1", "d": "1", "w_ash": "1",
}
FACTORS = {
    "light": "light.monod", "optics": "optics.slab_response_average",
    "temperature": "temperature.ctmi", "nutrients": ["nutrient.monod"],
    "combination": "combine.liebig", "loss": "loss.first_order",
    "stoichiometry": "stoich.photoautotrophic",
}


def card_inputs() -> dict:
    """Pin the central screening choices and their source transfer limits."""
    sources = (
        (AUDIT["candidates"], AUDIT["source"]),
        (AUDIT["relative_candidates"], AUDIT["relative_source"]),
        (AUDIT["nutrient_candidates"], AUDIT["nutrient_source"]),
        (AUDIT["composition_candidates"], AUDIT["composition_source"]),
    )
    values = {}
    for rows, source in sources:
        for symbol, row in rows.items():
            if symbol == "mu_max":
                continue
            values[symbol] = {
                "value": row["value"], "unit": UNITS[symbol],
                "species": "Nannochloropsis sp." if source is AUDIT["source"] else "Nannochloropsis gaditana",
                "strain": source["strain"],
                "conditions": f"DOI {source['doi']}; {source['locator']}; original {row['original']}; "
                              f"{source['conditions']}; transfer: {row['transfer']}",
                "source_doi": source["doi"], "source_digest": source.get("author_copy_sha256", source.get("full_text_xml_sha256")),
                "state": "assumed candidate; not source-verified in 169",
            }
    if set(values) != set(UNITS) - {"mu_max"}:
        raise ValueError("Assumed card symbol inventory is incomplete")
    return {
        "status": "assumed screening card; not qualified or C1-calibrated",
        "values": values,
        "mu_max": {"value": AUDIT["candidates"]["mu_max"]["value"], "unit": "1/hour",
                   "source_doi": AUDIT["source"]["doi"], "source_digest": AUDIT["source"]["author_copy_sha256"],
                   "conditions": AUDIT["source"]["conditions"]},
        "factors": FACTORS, "n_source": "HNO3",
        "selection": "central transferred values; k_X=200 m2/kg annular candidate; ranges remain sensitivity inputs",
    }


def create_assumed_card(workspace_id: str) -> dict:
    """Persist candidate values and a pinned card; return the complete input manifest."""
    from app.modules.bio_models import service

    manifest = card_inputs()
    parameter_set = service.create_set(
        workspace_id, "C1 CCAP 211/78 declared-assumption parameters",
        species="Nannochloropsis sp.", strain="CCAP 211/78", actor="spec-215")
    for symbol, row in manifest["values"].items():
        parameter_set = service.edit_set_value(
            workspace_id, parameter_set["id"], symbol,
            {key: row[key] for key in ("value", "unit", "species", "strain", "conditions")},
            parameter_set["revision"], parameter_set["digest"], actor="spec-215")
    card = service.create_card(
        workspace_id, "C1 CCAP 211/78 assumed screening card", parameter_set["id"],
        manifest["factors"], {key: manifest["mu_max"][key] for key in ("value", "unit")},
        actor="spec-215", n_source=manifest["n_source"])
    return {"manifest": manifest, "parameter_set": parameter_set, "card": card}
