from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from typing import Any


INCLUDED_DIGEST_FIELDS = (
    "proposed_external_target",
    "provider_call_allowed_now",
    "external_network_allowed_now",
    "confirmation_required",
    "confirmation_payload_required",
    "confirmation_payload",
    "confirmation_options",
)
EXCLUDED_EXISTING_DIGEST_FIELDS = frozenset({"confirmation_digest", "digest"})


def _canonicalize_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            key: _canonicalize_value(val)
            for key, val in sorted(value.items())
            if key not in EXCLUDED_EXISTING_DIGEST_FIELDS
        }
    if isinstance(value, list):
        # Preserve list order. Current runtime semantics do not prove these lists are unordered.
        return [_canonicalize_value(item) for item in value]
    return value


def canonicalize_confirmation_intent(decision_or_payload: Mapping[str, Any]) -> dict[str, Any]:
    canonical_payload: dict[str, Any] = {}
    for field in INCLUDED_DIGEST_FIELDS:
        if field in decision_or_payload:
            canonical_payload[field] = _canonicalize_value(decision_or_payload[field])
    return canonical_payload


def compute_confirmation_digest(decision_or_payload: Mapping[str, Any]) -> dict[str, Any]:
    canonical_payload = canonicalize_confirmation_intent(decision_or_payload)
    encoded = json.dumps(canonical_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {
        "canonical_payload": canonical_payload,
        "digest": "sha256:" + hashlib.sha256(encoded).hexdigest(),
    }
