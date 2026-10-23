"""Guard the narrow mapping from the primary CCAP 211/78 study to 169/170."""

import importlib.util
from pathlib import Path


def test_candidate_card_does_not_silently_complete_pbr_parameters():
    path = Path(__file__).resolve().parents[2] / "scripts/qualification/215/card_candidates.py"
    spec = importlib.util.spec_from_file_location("card_candidates_215", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    audit = module.build_audit()
    assert audit["source"]["strain"] == "Nannochloropsis sp. CCAP 211/78"
    assert audit["candidates"]["mu_max"]["value"] == 2.50 / 24
    assert audit["candidates"]["T_opt"]["value"] == 297.65
    assert all(row["state"] == "candidate" and row["source_locator"] for row in audit["candidates"].values())
    assert "K_I" in audit["missing_for_170"]
    assert "I_opt" in audit["nontransferable"]
    assert "r_s" in audit["nontransferable"]
    assert not set(audit["missing_for_170"]) & set(audit["candidates"])
