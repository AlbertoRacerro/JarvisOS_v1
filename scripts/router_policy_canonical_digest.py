from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from typing import Any


DIGEST_PURPOSE = "router_confirmation_intent"
DIGEST_VERSION = "v1"
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


def canonicalize_confirmation_digest_envelope(decision_or_payload: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "digest_purpose": DIGEST_PURPOSE,
        "digest_version": DIGEST_VERSION,
        "confirmation_intent": canonicalize_confirmation_intent(decision_or_payload),
    }


def compute_confirmation_digest(decision_or_payload: Mapping[str, Any]) -> dict[str, Any]:
    canonical_envelope = canonicalize_confirmation_digest_envelope(decision_or_payload)
    encoded = json.dumps(canonical_envelope, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {
        "canonical_payload": canonical_envelope["confirmation_intent"],
        "canonical_envelope": canonical_envelope,
        "digest": "sha256:" + hashlib.sha256(encoded).hexdigest(),
    }


def validate_confirmation_digest_integrity(
    decision_or_payload: Mapping[str, Any],
    *,
    expected_digest: str | None = None,
) -> dict[str, Any]:
    computed = compute_confirmation_digest(decision_or_payload)
    actual_digest = expected_digest
    if actual_digest is None:
        candidate = decision_or_payload.get("confirmation_digest")
        actual_digest = candidate if isinstance(candidate, str) else None
    return {
        "valid": isinstance(actual_digest, str) and actual_digest == computed["digest"],
        "actual_digest": actual_digest,
        "expected_digest": computed["digest"],
        "canonical_payload": computed["canonical_payload"],
        "canonical_envelope": computed["canonical_envelope"],
    }
