# A4-R2 - Local responder keep_alive and latency metadata

## Summary

Minimal adapter and dev-path patch:

- generic local responder default stays behavior-preserving with `keep_alive=None`
- dev local-chat layer applies default `keep_alive="30m"` and optional `num_predict`
- Ollama timing metadata is mapped into safe additive response fields
- backend end-to-end stage timing is added to the dev local-chat response only

## Start

- start HEAD: `11201d1e1a420bc949290cadd4393ccdac0e3348`
- working tree status before commit: `clean before implementation`

## Scope

- milestone: `A4-R2`
- task type: `minimal adapter and metadata patch`
- docs-only/code/runtime: `code + tests + report`
- files inspected: `scripts/router_policy_local_responder.py`, `backend/app/modules/dev_message_route/smoke_adapter.py`, `backend/tests/test_dev_local_chat.py`, `backend/tests/test_dev_message_route_smoke.py`

## Decisions

- shared payload construction remains single-site in `scripts/router_policy_local_responder.py`
- generic adapter does not send `keep_alive` unless explicitly provided
- generic adapter does not send `options.num_predict` unless it is a valid positive integer
- dev local-chat default `keep_alive` is confined to `JARVISOS_DEV_MESSAGE_ROUTE_KEEP_ALIVE` with fallback `30m`
- `keep_alive="-1"` is accepted as an override but is not the default
- backend timing wraps the existing order only: gate -> filter -> assembly -> responder
- timing metadata exposes durations/counts only; no prompt, raw request body, history, secret, or user content

## Manual latency measurement summary

- cold call: total about `9.58s`, load about `8.24s`
- warm call: total about `1.76s`, load about `0.58s`
- prompt eval duration: about `0.05s` to `0.09s`
- eval duration: about `1.11s` to `1.24s`
- `ollama ps`: `PROCESSOR = 100% GPU`
- interpretation: direct Ollama cold load is significant, but backend end-to-end timing is still required to explain the full UI path latency

## Residual risks

- keep_alive reduces reload latency but does not solve inference-bound latency
- multi-model benchmarking can cause VRAM contention and evictions
- `keep_alive="-1"` should not be used during multi-model benchmark unless intentionally pinning one model
- `backend_timing` is diagnostic and should not be treated as production observability
- if `backend_timing` shows large gate/history-filter durations, the next fix is Python path optimization, not keep_alive
