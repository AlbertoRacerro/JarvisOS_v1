# 1G-B2-F3-B1 - Phase B/Qwen RouterHint Producer

## Summary

- milestone: `1G-B2-F3-B1 - Phase B/Qwen RouterHint Producer`
- start HEAD: `a75b15160b0bd17ae1d9b789dfbbce2e7c3f2407`
- type: offline deterministic mapping only
- model calls: `false`
- responder calls: `false`
- A3 route execution added: `false`

## Actual Phase B Fields Used

- `summary_short`
- `project_bucket`
- `primary_domain`
- `domain_tags`
- `storage_relevance`
- `usefulness_for_future_review`
- `possible_memory_card_type`
- `soft_reason_code`
- `brief_rationale`
- `suggested_followup_question`
- `soft_uncertain_fields`

B1 does not use or require a Phase B `confidence` field.

## Soft Reason Mapping

| `soft_reason_code` | RouterPolicy hint result |
|---|---|
| `clarification_context` | clarification / unknown / low confidence |
| `source_candidate` | review / medium / current-info + file-context |
| `contextual_summary` | answer when no hard gate, no follow-up, quality high or medium |
| `memory_candidate` | answer only for benign low-storage none/knowledge-card cases; otherwise review |
| `low_value` | answer when no hard gate, no follow-up, quality high or medium |
| `decision_candidate` | review |
| `assumption_candidate` | review |
| `evidence_candidate` | review |
| `blocked_by_phase_a` | review or hard-gate blocked |
| `unknown` / missing / malformed | review / unknown / low confidence |

## Derived Quality Logic

- high: required fields valid, recognized non-ambiguous `soft_reason_code`, no follow-up, no uncertain fields
- medium: recognized `soft_reason_code`, no follow-up, bounded non-route-relevant uncertain fields
- low: missing or malformed fields, unknown/malformed/clarification/blocking reason, non-empty follow-up, or route-relevant uncertainty

## Mapping Results

- hard gate dominance: pass
- operational gate dominance: pass
- benign answer mapping: pass
- technical/scientific mapping: pass
- source/current-info mapping: pass
- ambiguity/follow-up mapping: pass
- low-quality fallback: pass
- memory_candidate tie-breaker: pass
- structural validation: pass with B1 structural checks; no full Draft 2020-12 validation claimed

## Tests Run

- `python -m unittest tests.test_router_policy_hint_bridge_probe` -> `15/15 OK`
- `python -m unittest tests.test_router_policy_message_route_smoke` -> `31/31 OK`
- `python -m unittest tests.test_router_policy_local_route_probe` -> `11/11 OK`
- `python -m unittest tests.test_router_policy_decision_probe` -> `14/14 OK`
- `python -m unittest tests.test_router_policy_semantic_validator` -> `40/40 OK`
- `python -m unittest discover -s tests` -> `277/277 OK`
- `git diff --check` -> pass with expected Windows CRLF warnings
- focused runtime-boundary grep -> literal schema/action-field and forbidden-name test hits only

## Runtime Boundary

- external provider calls added: `false`
- local model calls added: `false`
- responder calls added: `false`
- A3 route execution added: `false`
- tool/browser/terminal/MCP runtime added: `false`
- memory runtime added: `false`
- retrieval runtime added: `false`
- file-write runtime added: `false`
- backend routes added: `false`
- frontend UI added: `false`
- DB migrations added: `false`
- workers/queues/hooks added: `false`
- BlueRev modeling added: `false`

## Known Residual Risks

- B1 maps existing Phase B/Qwen advisory output only; it does not prove semantic truth.
- B1 does not approve live Qwen runtime routing.
- B1 does not remove deterministic Phase A or operational gates.
- B1 does not approve chat without `--assume-public-simple` yet.
- B1 derives confidence/quality from real Phase B fields; it does not rely on a Phase B confidence field.
- B1 derives complexity and scientific-depth heuristically from Phase B domain fields.
- Phase B soft review was designed for memory/review usefulness, not full routing classification.
- A later dedicated routing classifier or Phase B schema extension may be needed before removing `--assume-public-simple` from real user-facing chat.
- Field mapping may need adjustment after live Phase B/Qwen output audit.
