"""Instant, Jarvis-side Photobioreactor (T1) findings that need more than the culture graph (spec 170 cap. 6).

Culture reachability and the biomass / nitrogen / oxygen requirements live with the other culture findings in
``culture.py``. This module owns the model-card, temperature and feed-basis HRT findings.
"""

from __future__ import annotations

import math
from functools import lru_cache
from typing import Any

from app.modules.process_stack.draft_models import UNIT_REGISTRY, pbr_temperature_invalid

HRT_MIN_DAYS = 0.1
HRT_MAX_DAYS = 100.0
TEMPERATURE_DIFFERS_K = 5.0
_STANDARD_TEMPERATURE_K = 298.15


def _finding(severity: str, code: str, tag: str, field: str, message: str) -> dict[str, Any]:
    return {"severity": severity, "code": code, "object": tag, "field": field, "message": message,
            "source": "jarvis"}


@lru_cache(maxsize=256)
def _water_density(temperature_k: float, pressure_pa: float) -> float | None:
    """Pre-run stand-in for the 167 density basis (DWSIM mixture density, seawater-as-water approximation)."""
    try:
        from CoolProp.CoolProp import PropsSI

        value = float(PropsSI("D", "T", temperature_k, "P", pressure_pa, "Water"))
    except Exception:  # noqa: BLE001 - an unavailable or out-of-range basis skips the screening check
        return None
    return value if math.isfinite(value) and value > 0 else None


def _model_findings(workspace_id: str | None, unit: dict[str, Any]) -> list[dict[str, Any]]:
    tag, pin = unit["tag"], unit.get("model") or None
    if pin is None:
        return [_finding("blocker", "PBR_REQUIRES_MODEL_CARD", tag, "model",
                         f"{tag} needs a pinned biological model card; choose one in the Biology tab.")]
    if workspace_id is None:
        return []  # without a workspace the model library cannot be consulted
    from app.modules.bio_models import service as bio_models

    try:
        return [{"object": tag, "field": "model", "source": "jarvis", **item}
                for item in bio_models.pbr_model_findings(workspace_id, tag, pin)]
    except Exception:  # noqa: BLE001 - a broken library must not break instant validation
        return [_finding("blocker", "PBR_MODEL_CARD_UNAVAILABLE", tag, "model",
                         "The pinned model card could not be resolved; re-pin a card in the Biology tab.")]


def _feed_flow_kg_s(document: dict[str, Any], feed: dict[str, Any]) -> float | None:
    from app.modules.process_stack import mixed_runtime

    try:
        spec = feed["spec"]
        fractions = mixed_runtime._mass_fractions_from_spec(spec, document["compounds"])
        flow = mixed_runtime._feed_mass_flow(spec, fractions)
    except Exception:  # noqa: BLE001 - an unreadable feed flow skips the screening check
        return None
    return flow if math.isfinite(flow) and flow > 0 else None


def pbr_findings(document: dict[str, Any], workspace_id: str | None = None) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    objects = document["objects"]
    for unit in sorted((item for item in objects.values() if item["kind"] == "unit"
                        and UNIT_REGISTRY[item["type"]].culture_rule == "pbr"), key=lambda item: item["tag"]):
        tag, params = unit["tag"], unit["params"]
        if pbr_temperature_invalid(params):
            findings.append(_finding("blocker", "PBR_TEMPERATURE_INVALID", tag, "temperature_amplitude",
                                     "The mean culture temperature minus the diel amplitude must stay above 0 K."))
        findings.extend(_model_findings(workspace_id, unit))
        inlet = next((item for item in objects.values() if item["kind"] == "stream" and item["type"] != "EnergyStream"
                      and (item.get("target") or {}).get("unit") == unit["id"]), None)
        if inlet is None or inlet.get("source") is not None:
            # From a unit or a recycle the solved inlet is only known after Run; the instant check is skipped.
            continue
        spec = inlet.get("spec") or {}
        temperature = (spec.get("temperature") or {}).get("si")
        mean = (params.get("temperature_mean") or {}).get("si")
        if isinstance(temperature, (int, float)) and isinstance(mean, (int, float)) and (
                abs(mean - temperature) > TEMPERATURE_DIFFERS_K):
            findings.append(_finding(
                "info", "PBR_TEMPERATURE_DECLARED_DIFFERS", tag, "temperature_mean",
                f"The declared mean culture temperature differs from the feed temperature by more than "
                f"{TEMPERATURE_DIFFERS_K:g} K. Tier 1 has no energy balance: growth uses the declared profile "
                "and the outlet temperature equals the inlet temperature."))
        dims = [(params.get(key) or {}).get("si") for key in ("tube_inner_diameter", "tube_length", "tube_count")]
        pressure = (spec.get("pressure") or {}).get("si")
        if not (all(isinstance(value, (int, float)) and value > 0 for value in dims)
                and isinstance(temperature, (int, float)) and isinstance(pressure, (int, float))):
            continue
        flow = _feed_flow_kg_s(document, inlet)
        density = _water_density(float(temperature), float(pressure)) if flow is not None else None
        if flow is None or density is None:
            continue
        diameter, length, count = (float(value) for value in dims)
        volume = count * math.pi / 4.0 * diameter ** 2 * length
        hrt_days = volume * density / flow / 86400.0
        if not HRT_MIN_DAYS <= hrt_days <= HRT_MAX_DAYS:
            findings.append(_finding(
                "warning", "PBR_HRT_OUT_OF_RANGE", tag, "tube_length",
                f"Feed basis: HRT is {hrt_days:.3g} d (volume {volume:.3g} m3, feed {flow:.3g} kg/s, water density "
                f"{density:.0f} kg/m3 at the feed state), outside {HRT_MIN_DAYS:g}-{HRT_MAX_DAYS:g} d. "
                "A solved basis is reported after Run."))
    return findings
