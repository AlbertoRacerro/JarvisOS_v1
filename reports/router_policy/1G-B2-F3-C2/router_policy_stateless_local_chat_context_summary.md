# 1G-B2-F3-C2 - Stateless Local Chat Context Backend

## Summary

C2 adds a dev-only stateless local chat backend endpoint:

```text
POST /api/dev/local-chat
```

The client may send recent transcript/history, but every turn is validated and
rescanned server-side. Only turns without positive deterministic exclusion
signals are assembled into the local responder prompt.

## Contract

- `message`: required nonblank string, max `12000` chars.
- `history`: optional list, max `20` turns.
- history turn: `role=user|assistant`, nonblank capped `content`, no extra
  fields.
- `run_local_responder`: boolean, default `true`.
- client safety labels are rejected.
- dev gate, validation, trace, disabled, and internal-error boundaries reuse
  the C1-R1 helpers.

## Filtering

History classification reuses the existing message-route smoke builder and
deterministic overlay. A turn is excluded only for positive exclusion signals:

- secret or credential signal;
- raw private/IP-sensitive signal;
- external provider/upload intent;
- operational/tool/file/browser/terminal/MCP intent;
- malformed scan result or scan failure.

Benign turns are included even when the existing builder carries conservative
`unknown_sensitivity` or `manual_review_required` markers without positive
exclusion signals.

## Tests

```text
cd backend
.\.venv\Scripts\python -m pytest tests\test_dev_local_chat.py -q
18 passed

.\.venv\Scripts\python -m pytest tests\test_dev_message_route_smoke.py -q
52 passed

.\.venv\Scripts\python -m pytest -q
395 passed

python -m unittest tests.test_router_policy_message_route_smoke
84 tests OK

python -m unittest tests.test_router_policy_hint_bridge_probe
15 tests OK

python -m unittest tests.test_router_policy_local_route_probe
11 tests OK

python -m unittest tests.test_router_policy_decision_probe
14 tests OK

python -m unittest tests.test_router_policy_semantic_validator
40 tests OK

python -m unittest discover -s tests
330 tests OK

python -m json.tool reports/router_policy/1G-B2-F3-C2/router_policy_stateless_local_chat_context_summary.json
valid JSON
```

## Boundary

C2 does not add frontend UI, production chat, persistent memory, retrieval,
provider routing, external provider calls, tools, MCP, browser/terminal
execution, file-write runtime, DB conversation persistence, live Qwen Phase B
exposure, or BlueRev runtime behavior.

## Residual Risks

Filtering is per-turn and can leave semantically incomplete context if an
assistant turn refers to an excluded user turn.

The detector is more reliable for English-centric secret/private/provider/upload
patterns than for Italian or BlueRev-domain phrasing. C2 remains local-only dev
use. Future external/cheap provider routing over transcript/private/project
context must wait for explicit Italian/BlueRev detector hardening and tests.

Future hardening must be phrase/intention-based, not naked technical nouns such
as modello, parametri, correlazioni, dati, assunzioni, reattore, or simulazione.
