"""Audited CCAP 211/78 inputs for spec 215; this is not a runnable model card.

Run ``python3 scripts/qualification/215/card_candidates.py`` from the repo root.
The cited primary values and original conditions are detailed in the 215 report.
"""

from __future__ import annotations

import json

SOURCE = {
    "doi": "10.1016/j.algal.2025.104196",
    "author_copy_sha256": "30346040253415e5d477b255ba3876ec266034f11d60edc1e0b48273df41b9db",
    "locator": "Ihadjadene et al. (2025), Table 5; equations and methods for interpretation",
    "strain": "Nannochloropsis sp. CCAP 211/78",
    "conditions": "lab-scale ProviAPT flat panel; 20 mm light path; not outdoor AlgaePARC tubes",
}

# Only quantities with a justified exact symbol conversion enter this table.
# Their state remains candidate: Table 5 validation is not C1 qualification.
CANDIDATES = {
    "mu_max": {"value": 2.50 / 24, "unit": "h^-1", "original": "2.50 d^-1",
               "transfer": "same strain; outdoor geometry and operating range differ"},
    "T_min": {"value": 6.27 + 273.15, "unit": "K", "original": "6.27 degC",
              "transfer": "same strain; fitted outside much of training temperature range"},
    "T_opt": {"value": 24.50 + 273.15, "unit": "K", "original": "24.50 degC",
              "transfer": "same strain; outdoor temperature varies"},
    "T_max": {"value": 30.03 + 273.15, "unit": "K", "original": "30.03 degC",
              "transfer": "same strain; above the cited training range"},
}

# The source light law has an optimum, while the 170 PBR accepts Monod K_I.
# A numerical substitution would silently change the model form.
NONTRANSFERABLE = {
    "I_opt": {"value": 112.70, "unit": "umol m^-2 s^-1", "reason": "not Monod K_I"},
    "r_s": {"value": 0.08 / 24, "unit": "h^-1", "reason": "loss placement differs from 170 k_d"},
}
MISSING_170 = ("K_I", "K_j_0", "k_X", "a", "b", "c", "d", "w_ash")


def build_audit() -> dict:
    return {
        "status": "assumed candidate inputs; incomplete; no C1 prediction or qualification",
        "source": SOURCE,
        "form_proposal": {"light": "light.monod", "temperature": "temperature.ctmi",
                          "nutrients": ["nutrient.monod"], "loss": "loss.first_order",
                          "stoichiometry": "stoich.photoautotrophic"},
        "candidates": {symbol: {**row, "state": "candidate", "source_locator": SOURCE["locator"]}
                       for symbol, row in CANDIDATES.items()},
        "nontransferable": NONTRANSFERABLE,
        "missing_for_170": MISSING_170,
    }


if __name__ == "__main__":
    print(json.dumps(build_audit(), indent=2, sort_keys=True, allow_nan=False))
