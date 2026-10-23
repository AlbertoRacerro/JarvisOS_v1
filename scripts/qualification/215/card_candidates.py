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
RELATIVE_SOURCE = {
    "doi": "10.3390/app12125776",
    "author_copy_sha256": "7b75969c6ffa680a6a29d5ddeb98c4161c0529fe4b1162975dba4b1ddff38b89",
    "locator": "Lima et al. (2022), Eq. 1, Eq. 5, Eq. 10, Table 2",
    "strain": "Nannochloropsis gaditana (different species from C1 CCAP 211/78)",
    "conditions": "25 degC laboratory batch; 4 mm quasi-isoactinic and 15/30 mm flat panels, 35.5 mm annulus; artificial light",
}
NUTRIENT_SOURCE = {
    "doi": "10.3390/molecules25122834",
    "full_text_xml_sha256": "dc7c14c7d409c03fc1711609d74c997b852654e0b0afe4ee6b1ff3fba3c21463",
    "locator": "Sánchez-Bayo et al. (2020), Table 2 and Section 3.5, Eq. 2",
    "strain": "Nannochloropsis gaditana SAG 2.99 (different species from C1 CCAP 211/78)",
    "conditions": "25 degC freshwater Guillard F/2 batch mini-photobioreactors; 12:12 h light:dark; nitrate-limited",
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

# These are model-form-compatible values from a related Nannochloropsis species,
# not CCAP 211/78 measurements. The two k_X values are separate fitted reactor
# outcomes, not a confidence interval or calibrated C1 value. Eq. 1 uses exp.
RELATIVE_CANDIDATES = {
    "K_I": {"value": 15.28, "unit": "umol m^-2 s^-1", "original": "15.28 uE s^-1 m^-2",
            "transfer": "same Monod incident-light form; different species, 25 degC artificial light and outdoor tube optics"},
    "k_d": {"value": 0.0046, "unit": "h^-1", "original": "0.0046 h^-1",
            "transfer": "same first-order loss placement in Eq. 5; different species and batch operation"},
    "k_X": {"value": 200.0, "range": [200.0, 380.0], "unit": "m^2 kg^-1",
            "original": "0.20 annular / 0.38 flat m^2 g^-1; multiply by 1000",
            "transfer": "same exponential Beer-Lambert form; fitted attenuation changes with geometry and aggregation"},
}

# The source reports nitrate ion, whereas the 167/170 culture field is total
# dissolved nitrogen as N. 1 mg/L = 0.001 kg/m3; use atomic/molecular masses
# explicitly so a nitrate-ion number cannot silently become an N-as-N number.
N_AS_NO3 = 14.0067 / 62.0049
NUTRIENT_CANDIDATES = {
    "K_j_0": {
        "value": 4.0 * N_AS_NO3 / 1000,
        "range": [2.0 * N_AS_NO3 / 1000, 6.0 * N_AS_NO3 / 1000],
        "unit": "kg N m^-3",
        "original": "K_S = 4 +/- 2 mg NO3- L^-1; Table 2",
        "transfer": "nitrate-only Monod fit in freshwater N. gaditana batch; 170 uses total dissolved N as N, and C1 is outdoor marine CCAP 211/78; not a C1 confidence interval",
    },
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
        "relative_source": RELATIVE_SOURCE,
        "nutrient_source": NUTRIENT_SOURCE,
        "form_proposal": {"light": "light.monod", "temperature": "temperature.ctmi",
                          "nutrients": ["nutrient.monod"], "loss": "loss.first_order",
                          "stoichiometry": "stoich.photoautotrophic"},
        "candidates": {symbol: {**row, "state": "candidate", "source_locator": SOURCE["locator"]}
                       for symbol, row in CANDIDATES.items()},
        "relative_candidates": {
            symbol: {**row, "state": "candidate; cross-strain transfer", "source_locator": RELATIVE_SOURCE["locator"]}
            for symbol, row in RELATIVE_CANDIDATES.items()
        },
        "nutrient_candidates": {
            symbol: {**row, "state": "candidate; cross-strain and nutrient-basis transfer",
                     "source_locator": NUTRIENT_SOURCE["locator"]}
            for symbol, row in NUTRIENT_CANDIDATES.items()
        },
        "nontransferable": NONTRANSFERABLE,
        "missing_for_170": tuple(symbol for symbol in MISSING_170
                                 if symbol not in RELATIVE_CANDIDATES and symbol not in NUTRIENT_CANDIDATES),
    }


if __name__ == "__main__":
    print(json.dumps(build_audit(), indent=2, sort_keys=True, allow_nan=False))
