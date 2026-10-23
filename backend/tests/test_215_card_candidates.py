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
    assert audit["relative_source"]["doi"] == "10.3390/app12125776"
    assert audit["relative_candidates"]["K_I"]["value"] == 15.28
    assert audit["relative_candidates"]["k_d"]["value"] == 0.0046
    assert audit["relative_candidates"]["k_X"]["range"] == [200.0, 380.0]
    assert all(row["state"] == "candidate; cross-strain transfer" and row["source_locator"]
               for row in audit["relative_candidates"].values())
    nutrient = audit["nutrient_candidates"]["K_j_0"]
    assert audit["nutrient_source"]["doi"] == "10.3390/molecules25122834"
    assert nutrient["value"] == 4.0 * (14.0067 / 62.0049) / 1000
    assert nutrient["range"] == [2.0 * (14.0067 / 62.0049) / 1000,
                                 6.0 * (14.0067 / 62.0049) / 1000]
    assert nutrient["unit"] == "kg N m^-3"
    assert nutrient["state"] == "candidate; cross-strain and nutrient-basis transfer"
    assert nutrient["source_locator"]
    composition = audit["composition_candidates"]
    assert audit["composition_source"]["doi"] == "10.3390/app11104337"
    assert audit["composition_source"]["author_copy_sha256"] == (
        "3cc0c135f7b686577ef980c26e969270a9d84a05e89675ce12aafce3d9cfaea6"
    )
    assert composition["a"]["value"] == (7.1 / 1.008) / (48.7 / 12.011)
    assert composition["b"]["value"] == (36.5 / 15.999) / (48.7 / 12.011)
    assert composition["c"]["value"] == (6.80 / 14.007) / (48.7 / 12.011)
    assert composition["d"]["value"] == (6.43 / 10 / 30.974) / (48.7 / 12.011)
    assert composition["w_ash"]["value"] == 0.045
    assert all(row["source_locator"] and "cross-strain" in row["state"]
               for row in composition.values())
    assert "K_I" not in audit["missing_for_170"]
    assert "K_j_0" not in audit["missing_for_170"]
    assert "I_opt" in audit["nontransferable"]
    assert "r_s" in audit["nontransferable"]
    assert not set(audit["missing_for_170"]) & set(audit["candidates"])
    assert not set(audit["missing_for_170"]) & set(audit["relative_candidates"])
    assert not set(audit["missing_for_170"]) & set(audit["nutrient_candidates"])
    assert not audit["missing_for_170"]
