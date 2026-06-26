# Local Responder Root-Cause Rerun

## Scope

- current HEAD: `9e04b41384aa452611d5b5331874ab384e18e9f7`
- starting git status: clean
- script-starting git status: `?? reports/router_policy/1G-B2-F3-LOCAL-RESPONDER-ROOT-CAUSE-RERUN/`
- previous post-reconnection diagnostic data discarded: yes
- runtime/router/A5-R3 changes: none
- permanent `NUM_PREDICT`/timeout/model changes: none

## Preflight

- Ollama alive before diagnostics: True
- Ollama startup required: False
- relevant installed models: qwen3:14b, gemma4:12b-it-qat
- `gemma4:12b-it-qat` available: True
- `qwen3:14b` available: True
- warm-up ok: True
- warm-up duration ms: 2743.955

## Gemma Direct Streaming

- processor class: `100% GPU`
- wall-clock ms: `22999.433`
- time_to_first_chunk_ms: `13846.147`
- time_to_first_visible_text_ms: `13846.147`
- visible chars after 64 chunks: `205`
- visible chars after 512 chunks: `1537`
- total visible chars: `1537`
- empty/whitespace chunks: `28`
- stopped reason: `max_512_chunks`
- output characterization: `useful_visible_text`
- `ollama ps` snapshots during run: in `diagnostic_raw.json` at `direct_stream_gemma.ollama_ps_snapshots`

## Backend Comparison

| case | HTTP | executed | reason | error_type | wall ms | responder ms | chars |
|---|---:|---|---|---|---:|---:|---:|
| problematic | 200 | True | `local_answer` | `None` | 35967.443 | 35751.581 | 4505 |
| short_control | 200 | True | `local_answer` | `None` | 4266.363 | 4079.218 | 63 |
| bluerev_ip_control | 200 | True | `local_answer` | `None` | 20603.624 | 20415.914 | 1436 |
| bluerev_generic_control | 200 | True | `local_answer` | `None` | 30341.273 | 30149.828 | 3626 |

Backend `ollama ps` snapshots for each case are in `diagnostic_raw.json` at `backend_results[].ollama_ps_snapshots`.

## Qwen Direct Streaming

- processor class: `100% GPU`
- wall-clock ms: `11370.46`
- time_to_first_visible_text_ms: `None`
- visible chars after 64 chunks: `0`
- visible chars after 512 chunks: `0`
- total visible chars: `0`
- stopped reason: `max_512_chunks`
- output characterization: `no_visible_text`
- `ollama ps` snapshots during run: in `diagnostic_raw.json` at `direct_stream_qwen.ollama_ps_snapshots`

## Verdict

- Gemma vs qwen verdict: same placement=100% GPU; gemma first visible=13846.147 ms, qwen first visible=None ms; gemma visible chars after 64=205, qwen visible chars after 64=0
- classification: `A. normal long useful generation`
- throughput collapse/offload: not supported; Gemma and qwen `ollama ps` snapshots show `100% GPU`
- Gemma prefix pathology: not supported; Gemma produced useful visible text by the first captured chunk and 205 visible chars by 64 chunks
- qwen better model-specific path: not supported in this run; qwen produced no visible `response` text in the first 512 chunks under the same `100% GPU` placement

## Recommended Next Action

- If behavior is acceptable, add failure-path timing instrumentation before any timeout/output-budget changes.
- Do not set permanent NUM_PREDICT from one run.

## Files

- `reports/router_policy/1G-B2-F3-LOCAL-RESPONDER-ROOT-CAUSE-RERUN/run_diagnostic.py`
- `reports/router_policy/1G-B2-F3-LOCAL-RESPONDER-ROOT-CAUSE-RERUN/diagnostic_raw.json`
- `reports/router_policy/1G-B2-F3-LOCAL-RESPONDER-ROOT-CAUSE-RERUN/summary.json`
- `reports/router_policy/1G-B2-F3-LOCAL-RESPONDER-ROOT-CAUSE-RERUN/summary.md`

## Checks

- `git diff --check` -> pass.
- `git status --short` -> `?? reports/router_policy/1G-B2-F3-LOCAL-RESPONDER-ROOT-CAUSE-RERUN/`.
- `python -m json.tool summary.json and diagnostic_raw.json` -> pass.
