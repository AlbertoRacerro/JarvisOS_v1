"""Dev-only adapter for the RouterPolicy message-route smoke path.

This module is a narrow import seam from backend code to the existing
evaluation/smoke script. It must not become a production dependency pattern.
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4


REPO_ROOT = Path(__file__).resolve().parents[4]
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from router_policy_local_responder import build_local_responder  # noqa: E402
from router_policy_message_route_smoke import (  # noqa: E402
    MAX_MESSAGE_CHARS,
    _safe_cli_result,
    run_message_route_smoke,
)


DEV_GATE_ENV = "JARVISOS_ENABLE_DEV_MESSAGE_ROUTE_SMOKE"
ASSUME_PUBLIC_ENV = "JARVISOS_DEV_MESSAGE_ROUTE_ASSUME_PUBLIC_SIMPLE"
ALLOW_LOCAL_RESPONDER_ENV = "JARVISOS_DEV_MESSAGE_ROUTE_ALLOW_LOCAL_RESPONDER"
MODEL_ENV = "JARVISOS_DEV_MESSAGE_ROUTE_MODEL"
ENDPOINT_ENV = "JARVISOS_DEV_MESSAGE_ROUTE_ENDPOINT"
TIMEOUT_ENV = "JARVISOS_DEV_MESSAGE_ROUTE_TIMEOUT_S"

DEFAULT_MODEL = "gemma3:4b"
DEFAULT_ENDPOINT = "http://127.0.0.1:11434/api/generate"
DEFAULT_TIMEOUT_S = 30.0


def _truthy_env(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in {"1", "true", "yes", "on"}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _timeout_from_env() -> float:
    raw = os.getenv(TIMEOUT_ENV)
    if raw is None or not raw.strip():
        return DEFAULT_TIMEOUT_S
    try:
        parsed = float(raw)
    except ValueError:
        return DEFAULT_TIMEOUT_S
    return parsed if parsed > 0 else DEFAULT_TIMEOUT_S


def _smoke_result(
    *,
    executed: bool,
    reason: str,
    assume_public_simple_used: bool,
    use_phase_b_hints_used: bool = True,
) -> dict[str, Any]:
    return {
        "executed": executed,
        "reason": reason,
        "input_source": "dev_message_route_endpoint",
        "assume_public_simple_used": assume_public_simple_used,
        "use_phase_b_hints_used": use_phase_b_hints_used,
        "phase_b_source_kind": "stub",
        "phase_b_source_used": False,
    }


def safe_endpoint_response(result: dict[str, Any], *, trace_id: str) -> dict[str, Any]:
    safe = _safe_cli_result(result)
    safe.pop("input_source", None)
    return {
        "trace_id": trace_id,
        "audit_ref": None,
        **safe,
    }


def internal_error_response(*, trace_id: str, error_type: str | None = None) -> dict[str, Any]:
    response = safe_endpoint_response(
        _smoke_result(
            executed=False,
            reason="internal_error",
            assume_public_simple_used=_truthy_env(ASSUME_PUBLIC_ENV),
        ),
        trace_id=trace_id,
    )
    if error_type:
        response["error_type"] = error_type
    return response


def run_dev_message_route_smoke(*, message: str, run_local_responder: bool) -> tuple[int, dict[str, Any]]:
    trace_id = str(uuid4())
    assume_public_simple = _truthy_env(ASSUME_PUBLIC_ENV)

    if not _truthy_env(DEV_GATE_ENV):
        return 404, safe_endpoint_response(
            _smoke_result(
                executed=False,
                reason="dev_message_route_smoke_disabled",
                assume_public_simple_used=assume_public_simple,
            ),
            trace_id=trace_id,
        )

    responder = None
    if run_local_responder:
        if not _truthy_env(ALLOW_LOCAL_RESPONDER_ENV):
            return 200, safe_endpoint_response(
                _smoke_result(
                    executed=False,
                    reason="local_responder_disabled",
                    assume_public_simple_used=assume_public_simple,
                ),
                trace_id=trace_id,
            )
        responder = build_local_responder(
            model=os.getenv(MODEL_ENV, DEFAULT_MODEL),
            endpoint=os.getenv(ENDPOINT_ENV, DEFAULT_ENDPOINT),
            timeout_s=_timeout_from_env(),
        )

    result = run_message_route_smoke(
        message,
        responder=responder,
        now=utc_now_iso(),
        assume_public_simple=assume_public_simple,
        use_phase_b_hints=True,
        phase_b_source_kind="stub",
    )
    return 200, safe_endpoint_response(result, trace_id=trace_id)
