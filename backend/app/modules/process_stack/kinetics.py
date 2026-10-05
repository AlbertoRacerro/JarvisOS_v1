"""Closed, deterministic DWSIM script kinetics for spec 180."""

from __future__ import annotations

import math
from typing import Any

from app.modules.process_stack.draft_models import COMPOUNDS

KINETICS_VERSION = "180.1"


def _parameter(item: dict[str, Any], name: str, *, positive: bool = False,
               maximum: float = 1e6) -> float:
    value = float(item["si"])
    if not math.isfinite(value) or value > maximum or (value <= 0 if positive else value < 0):
        raise ValueError(f"{name} is outside the supported finite domain")
    return value


def validate_rate_law(reaction: dict[str, Any], declared: set[str]) -> None:
    law = reaction.get("rate_law")
    if not law:
        return
    substrate = law["substrate"]
    participants = set(reaction["stoichiometry"])
    if substrate != reaction["base_reactant"] or substrate not in participants:
        raise ValueError("substrate must be the base reactant")
    if not participants <= declared or not participants <= set(COMPOUNDS):
        raise ValueError("reaction compounds must be declared and supported")
    _parameter(law["v_max"], "v_max", maximum=1e6 * 1000 / 3600)
    _parameter(law["k_s"], "k_s", positive=True)
    if law["form"] == "haldane":
        _parameter(law["k_i"], "k_i", positive=True)
    seen: set[str] = set()
    for term in law.get("inhibitions", []):
        inhibitor = term["inhibitor"]
        if inhibitor not in participants or inhibitor == substrate or inhibitor in seen:
            raise ValueError("inhibitors must be distinct non-substrate participants")
        seen.add(inhibitor)
        _parameter(term["k_i"], "inhibition k_i", positive=True)
    factor = law.get("temperature")
    if factor:
        _parameter(factor["activation_energy"], "activation_energy", maximum=1e5)
        reference = _parameter(factor["reference_temperature"], "reference_temperature", positive=True,
                               maximum=1000)
        if reference < 250:
            raise ValueError("reference_temperature must be at least 250 K")
    provenance = reaction.get("provenance")
    if not provenance or provenance.get("kind") == "literature" and not provenance.get("citation"):
        raise ValueError("provenance and a literature citation are required")


def _amount(name: str) -> str:
    if name not in COMPOUNDS or any(char in name for char in "'\\\n\r"):
        raise ValueError("unsafe compound name")
    return f"max(Amounts['{name}'], 0.0)"


def render(reaction: dict[str, Any]) -> str:
    """Render only the bounded grammar; no caller text becomes Python syntax."""
    law = reaction["rate_law"]
    validate_rate_law(reaction, set(COMPOUNDS))
    lines = [f"S = {_amount(law['substrate'])}"]
    ks = law["k_s"]["si"] / 1000.0
    vmax = law["v_max"]["si"] * 3.6
    lines.append(f"K = {repr(float(ks))}")
    for index, term in enumerate(law.get("inhibitions", [])):
        lines.append(f"I{index} = {_amount(term['inhibitor'])}")
        ki = term["k_i"]["si"] / 1000.0
        if term["kind"] == "competitive":
            lines.append(f"K = K * (1.0 + I{index} / {repr(float(ki))})")
    if law["form"] == "monod":
        expression = "S / (K + S)"
    else:
        ki = law["k_i"]["si"] / 1000.0
        expression = f"S / (K + S + S * S / {repr(float(ki))})"
    for index, term in enumerate(law.get("inhibitions", [])):
        if term["kind"] == "noncompetitive":
            ki = term["k_i"]["si"] / 1000.0
            expression += f" * ({repr(float(ki))} / ({repr(float(ki))} + I{index}))"
    if factor := law.get("temperature"):
        ea = factor["activation_energy"]["si"]
        tref = factor["reference_temperature"]["si"]
        lines.insert(0, "import math")
        expression += f" * math.exp(-({repr(float(ea))} / 8.314462618) * (1.0 / T - 1.0 / {repr(float(tref))}))"
    lines.append(f"r = {repr(float(vmax))} * ({expression})")
    return "\n".join(lines) + "\n"
