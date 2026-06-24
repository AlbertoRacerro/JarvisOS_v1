"""RouterPolicy local-route smoke integration for A3.

This module is the first minimal execution smoke path for RouterPolicy. The
library entrypoint is offline-safe by default: it can only execute an injected
local responder after decision production, semantic validation, and a strict
safe-local permission guard pass.
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

from router_policy_local_responder import LocalResponderError, build_local_responder
from router_policy_decision_probe import decide_router_policy
from router_policy_semantic_validator import validate_router_decision_semantics


_DECIDE_ROUTER_POLICY = decide_router_policy
_VALIDATE_ROUTER_DECISION_SEMANTICS = validate_router_decision_semantics
_BUILD_LOCAL_RESPONDER = build_local_responder

SAFE_LOCAL_ROUTE_ACTIONS = {"answer_local", "route_local"}
SAFE_LOCAL_PROVIDERS = {"local:gemma", "local:qwen"}


def _is_safe_local_execution(decision: dict) -> bool:
    """Return true only for validator-valid, no-side-effect LOCAL_FAST answers."""

    return all(
        (
            decision.get("route_action") in SAFE_LOCAL_ROUTE_ACTIONS,
            decision.get("route_tier") == "LOCAL_FAST",
            decision.get("provider_candidate") in SAFE_LOCAL_PROVIDERS,
            decision.get("response_allowed_now") is True,
            decision.get("external_allowed") is False,
            decision.get("provider_call_allowed_now") is False,
            decision.get("external_network_allowed_now") is False,
            decision.get("tool_execution_allowed_now") is False,
            decision.get("state_change_allowed_now") is False,
            decision.get("allowed_execution_mode") == "answer_only",
            decision.get("modifies_state") is False,
            decision.get("side_effect_level") == "none",
            decision.get("environment_type") == "chat",
        )
    )


def run_local_route(
    input_obj: dict,
    *,
    responder: Callable[[str], str] | None = None,
    now: str | None = None,
) -> dict:
    """Run the minimal safe-local RouterPolicy smoke path."""

    decision = _DECIDE_ROUTER_POLICY(input_obj, now=now)
    violations = _VALIDATE_ROUTER_DECISION_SEMANTICS(input_obj, decision)
    if violations:
        return {
            "decision": decision,
            "executed": False,
            "response": None,
            "reason": "decision_failed_validation",
            "violations": violations,
        }

    if not _is_safe_local_execution(decision):
        return {
            "decision": decision,
            "executed": False,
            "response": None,
            "reason": "not_safe_local_route",
        }

    message_text = input_obj.get("message_text")
    if not isinstance(message_text, str) or not message_text:
        return {
            "decision": decision,
            "executed": False,
            "response": None,
            "reason": "message_text_missing",
        }

    if responder is None:
        return {
            "decision": decision,
            "executed": False,
            "response": None,
            "reason": "local_responder_missing",
        }

    text = responder(message_text)
    if not isinstance(text, str):
        return {
            "decision": decision,
            "executed": False,
            "response": None,
            "reason": "local_responder_invalid",
        }

    return {
        "decision": decision,
        "executed": True,
        "response": text,
        "reason": "local_answer",
    }


def _load_fixture(path: Path) -> dict[str, Any]:
    loaded = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(loaded, dict) and "input" in loaded and isinstance(loaded["input"], dict):
        return loaded["input"]
    if isinstance(loaded, dict):
        return loaded
    raise ValueError("fixture must contain a RouterPolicy input object")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="RouterPolicy A3 local-route smoke probe.")
    parser.add_argument("--fixture", required=True, help="Path to a normalized RouterPolicy input fixture.")
    parser.add_argument("--run-local", action="store_true", help="Explicitly enable localhost-only local responder.")
    parser.add_argument("--model", default="gemma3:4b", help="Ollama model name already pulled locally.")
    parser.add_argument("--endpoint", default="http://127.0.0.1:11434/api/generate")
    parser.add_argument("--timeout-s", type=float, default=30.0)
    parser.add_argument("--now", default=None)
    args = parser.parse_args(argv)

    input_obj = _load_fixture(Path(args.fixture))
    responder = None
    if args.run_local:
        try:
            responder = _BUILD_LOCAL_RESPONDER(
                model=args.model,
                endpoint=args.endpoint,
                timeout_s=args.timeout_s,
            )
        except LocalResponderError as exc:
            result = {
                "decision": None,
                "executed": False,
                "response": None,
                "reason": "local_responder_setup_failed",
                "error_type": type(exc).__name__,
                "error": str(exc),
            }
            print(json.dumps(result, indent=2, sort_keys=True))
            return 0
    try:
        result = run_local_route(input_obj, responder=responder, now=args.now)
    except LocalResponderError as exc:
        result = {
            "decision": None,
            "executed": False,
            "response": None,
            "reason": "local_responder_error",
            "error_type": type(exc).__name__,
            "error": str(exc),
        }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
