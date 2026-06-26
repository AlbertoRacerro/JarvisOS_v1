# Local Responder Timeout Diagnostic

## Scope

- current HEAD: `bf1d31d0b27b96f560c4ec36692a2c10701a12c5`
- working tree clean before start: yes
- A5-R3 changed: no
- router policy changed: no
- Phase-B bridge changed: no
- permanent timeout changed: no
- permanent `NUM_PREDICT` set: no
- retry/fallback added: no
- live-Ollama-dependent automated tests added: no

## Inspection

- `LocalResponderTransportError`: `scripts/router_policy_local_responder.py` wraps `urllib.error.URLError`, `TimeoutError`, and `OSError`; HTTP errors are also wrapped as transport errors.
- timeout default: `backend/app/modules/dev_message_route/smoke_adapter.py` has `DEFAULT_TIMEOUT_S = 30.0`; live diagnostic temporarily used `JARVISOS_DEV_MESSAGE_ROUTE_TIMEOUT_S=120`.
- `backend_timing.local_responder_call_duration_ms`: assigned only after `responder(prompt)` returns successfully.
- failed responder calls: no `backend_timing.local_responder_call_duration_ms`; exception exits before assignment and internal-error body omits timing.
- `local_responder_timing`: available on successful Ollama responses with timing metadata only.
- `NUM_PREDICT`: read from `JARVISOS_DEV_MESSAGE_ROUTE_NUM_PREDICT` in `smoke_adapter._num_predict_from_env`.

## Live Baseline

- model used: `gemma4:12b-it-qat`
- reason: shell had no `JARVISOS_DEV_MESSAGE_ROUTE_MODEL`; repo default `gemma3:4b` is not installed locally.
- timeout: `120s`
- keep_alive: `30m`
- baseline `NUM_PREDICT`: unset
- Ollama before: alive, `/api/tags` status `200`
- Ollama after: alive, process `ollama`, PID `35320`

| case | prompt | HTTP | executed | reason | error_type | wall-clock ms | responder ms | local timing |
|---|---|---:|---|---|---|---:|---:|---|
| failing_exact | `dimensioniamo concettualmente una pompa centrifuga per un fotobioreattore: prevalenza, portata, NPSH` | 500 | false | `internal_error` | `LocalResponderTransportError` | 120065.158 | unavailable | unavailable |
| comparison_ciao | `ciao` | 200 | true | `local_answer` | null | 17748.816 | 17432.889 | available |
| comparison_bluerev | `dimensioniamo concettualmente una pompa centrifuga per BlueRev: prevalenza, portata, NPSH` | 500 | false | `internal_error` | `LocalResponderTransportError` | 120503.277 | unavailable | unavailable |
| comparison_bluerev_ip | `usa i parametri proprietari BlueRev per dimensionare concettualmente una pompa centrifuga: prevalenza, portata, NPSH` | 200 | true | `local_answer` | null | 83448.855 | 81482.794 | available |

Failing response body:

```json
{
  "trace_id": "771eb576-edf1-4477-9913-fde5f151ce26",
  "audit_ref": null,
  "executed": false,
  "reason": "internal_error",
  "assume_public_simple_used": true,
  "use_phase_b_hints_used": true,
  "phase_b_source_kind": "stub",
  "phase_b_source_used": false,
  "error_type": "LocalResponderTransportError"
}
```

## NUM_PREDICT Experiment

- exact failing prompt only
- temporary env only; no config change committed
- `NUM_PREDICT=64` not tested

| num_predict | HTTP | executed | reason | wall-clock ms | responder ms | eval_count | chars returned | result |
|---:|---:|---|---|---:|---:|---:|---:|---|
| 512 | 200 | true | `local_answer` | 23080.335 | 23057.387 | 512 | 0 | avoided timeout, empty response |
| 1024 | 200 | true | `local_answer` | 19953.069 | 19946.335 | 1024 | 1068 | avoided timeout, non-empty response |

Note: the ad-hoc script emitted both per-case results, then failed during final aggregate JSON printing because Windows `cp1252` could not encode a Unicode subscript in generated text. Diagnostic case data above was already captured.

## Classification

- primary: `A. timeout-long-generation`
- secondary: `D. backend instrumentation gap`

Evidence:

- exact failing prompt failed at `120065.158 ms` with `timeout_s=120`
- BlueRev comparison failed at `120503.277 ms` with same transport error
- Ollama remained alive after failures
- successful IP-marker comparison took `83448.855 ms`, showing long local answer generation can complete
- failed responses do not expose responder call duration or local responder timing

## Recommended Next Action

- Add minimal failure-path instrumentation: include `backend_timing.local_responder_call_duration_ms` or equivalent sanitized responder duration on `LocalResponderTransportError`.
- Preserve prompt secrecy; do not add raw prompt/model output to failure bodies.
- After instrumentation, repeat a bounded diagnostic for `NUM_PREDICT=1024`; `512` is not acceptable because it returned empty output once.
- Do not change router policy, A5-R3, model selection, permanent timeout, permanent `NUM_PREDICT`, or retry behavior yet.

## Checks

- `python -m unittest tests.test_router_policy_local_responder` -> pass, 23 tests.
- backend pytest not run: backend test harness was not touched.
- `git diff --check` -> pass.
- `git status --short` -> `?? reports/router_policy/1G-B2-F3-LOCAL-RESPONDER-TIMEOUT-DIAG/`.
