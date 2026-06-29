"""Manual live smoke for the positive AI execution path.

NOT run by pytest/CI. Requires --confirm-live so it never fires accidentally.
Makes ONE real provider call through run_ai_task using credentials from the
environment, and prints the ai_jobs ledger outcome.

Example (PowerShell):
    $env:SCALEWAY_API_KEY = "<your key>"
    python scripts/manual_ai_live_smoke.py --route external:cheap --max-tokens 128 --confirm-live
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND = REPO_ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="One real AI call through run_ai_task.")
    parser.add_argument("--route", default="external:cheap")
    parser.add_argument("--prompt", default="Say hello in one short sentence.")
    parser.add_argument("--max-tokens", type=int, default=128)
    parser.add_argument("--confirm-live", action="store_true")
    args = parser.parse_args(argv)

    if not args.confirm_live:
        print("Refusing to make a live call without --confirm-live.", file=sys.stderr)
        return 2

    from app.core.database import initialize_database
    from app.modules.ai.execution import run_ai_task

    initialize_database()  # idempotent; ensures ai_jobs exists
    outcome = run_ai_task(
        user_prompt=args.prompt,
        route_class=args.route,
        max_output_tokens=args.max_tokens,
    )

    print(f"status:        {outcome.status}")
    print(f"ledger_id:     {outcome.ledger_id}")
    print(f"route:         {outcome.selected_route_class}")
    print(f"decision:      {outcome.decision.decision_reason}")
    if outcome.response is not None:
        usage = outcome.response.usage
        print(f"provider/model: {outcome.response.provider_id}/{outcome.response.model_id}")
        print(f"tokens in/out:  {usage.input_tokens}/{usage.output_tokens}")
        text = outcome.response.text or ""
        print("response:")
        print(text[:1000])
    else:
        print(f"blocked_reason: {outcome.decision.blocked_reason}")
    return 0 if outcome.status == "success" else 1


if __name__ == "__main__":
    raise SystemExit(main())
