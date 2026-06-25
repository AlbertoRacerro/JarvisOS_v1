# 1G-B2-F3-C2-R2 - Explicit Local Chat Authorization Gate

## Summary

C2-R2 removes the fragile local-chat authorization dependency on the diagnostic
`local_responder_missing` reason string.

Authorization now uses the public local-route predicate:
`is_safe_local_execution(decision)`.

## Execution Split

Local-chat uses the existing A5/A3 route machinery only to authorize the
current user message. After positive safe-local authorization, local-chat
assembles clean recent history plus the current message and calls the A4
localhost-only responder directly.

This split is intentional because the assembled prompt uses the local-chat
adapter prompt budget and does not fit the single-message A5 smoke execution
path.

## Results

- `local_route_positive_predicate_promoted`: true
- `public_predicate_name`: `is_safe_local_execution`
- `private_alias_preserved`: true
- `local_chat_uses_positive_predicate`: true
- `local_chat_authorization_uses_reason_string`: false
- `local_responder_missing_treated_as_diagnostic_only`: true
- `missing_decision_fails_closed`: true
- `malformed_decision_fails_closed`: true
- `unexpected_reason_with_safe_decision_authorizes`: true
- `unsafe_decision_blocks_a4`: true
- `a4_direct_call_before_authorization`: false
- `execution_split_documented`: true
- `current_message_authorized_by_a5_a3`: true
- `assembled_prompt_executed_by_a4_direct_after_authorization`: true

## Boundary

- `frontend_added`: false
- `persistent_memory_added`: false
- `retrieval_added`: false
- `provider_routing_added`: false
- `external_provider_calls_added`: false
- `tool_mcp_browser_terminal_added`: false
- `db_conversation_persistence_added`: false
- `a4_modified`: false
- `real_ollama_calls_in_tests`: false

## Checks

- `git status --short` - pass; clean at start.
- `git merge-base --is-ancestor d513b40ea0ab5f9e5e4e17e791bedd9749365184 HEAD` - pass.
- `python -m unittest tests.test_router_policy_local_route_probe` - pass; 12 tests.
- `cd backend; .\.venv\Scripts\python -m pytest tests\test_dev_local_chat.py -q` - pass; 26 tests.
- `cd backend; .\.venv\Scripts\python -m pytest tests\test_dev_message_route_smoke.py -q` - pass; 52 tests.
- `cd backend; .\.venv\Scripts\python -m pytest -q` - pass; 403 tests.
- `python -m unittest tests.test_router_policy_local_responder` - pass; 20 tests.
- `python -m unittest tests.test_router_policy_message_route_smoke` - pass; 84 tests.
- `python -m unittest discover -s tests` - pass; 338 tests.

## Known Residual Risks

- The dev local-chat endpoint remains smoke/dev-only and gated by environment flags.
- Positive safe-local authorization does not make model output semantically complete or production-safe.
- Local-chat history filtering remains deterministic smoke filtering, not persistent memory or retrieval.
