# 154b — Local responder default (Gemma 4 12B QAT, thinking off, relay repair)

State: **ready**. Combined definition, contract and readiness, authorized by the maintainer's 2026-09-27/28 pre-155 directives (Gemma 4 12B QAT selected as the primary local responder; Qwen3.5-4B retained as the fast fallback). Smallest follow-up to 151, 152 and 154a that makes the selected local model usable by default. No new provider, authority or egress surface.

## Fresh baseline

151 owns the local llama.cpp runtime and 152 relays Hermes agent turns through it with a flat text tool protocol: the model writes `{"tool_calls": [...]}` and `worker_shim.completion_message` promotes it to the one broker tool shape only if it parses exactly. The pre-155 qualification (51 real Hermes/engineering/coding/general tasks through the pinned Hermes worker and supervisor, llama.cpp b11178, ctx 16384, q8 KV) measured:

- Gemma 4 12B QAT Q4_0, thinking off: 35/51 (Hermes 14/23, engineering 10/10), p50 12.4 s, p95 20 s, peak 7.9 GB VRAM on a 12 GB GPU, 0 crashes — about +7 tasks over the best 4B responders, twice the measured run-to-run noise.
- Without a repair, 9 of those 51 finals were tool proposals the strict parser rejected (Gemma's native `<|tool_call>call:name{...}<tool_call|>` form, string-encoded `arguments`, code fences, unclosed braces) and were shown to the user as the answer.
- Thinking on multiplies latency without a correctness gain on this path; the current runtime has no way to turn it off per configuration.
- The previous default (Qwen3.8-27B IQ2_M) left 1.4 GB headroom and crashed llama-server at least four times; a crash currently leaves the local route down until a manual restart.

Evidence: `jarvis-control/work/evidence/pre155/e4/FINAL-S1-MATRIX.md` (operator machine).

## Accepted capability

1. **Thinking control.** The local runtime configuration accepts `thinking = default | on | off` (`JARVISOS_LLAMACPP_THINKING`). `on`/`off` is sent on every local chat request as the chat-template switch; `default` leaves the model template unchanged. Status reports the configured value.
2. **Authority-neutral relay repair.** Before the strict check, `completion_message` recovers the recognized malformed forms of a tool proposal — code fence, bounded missing closers, string-encoded JSON arguments, the Gemma native call syntax — into the canonical proposal. The admission rules are unchanged: 1–4 calls, every name in the relayed tool list, object arguments. Anything else stays plain assistant text exactly as today. The repair adds no tool, name or argument the model did not write.
3. **Bounded crash recovery.** When a Jarvis-managed llama-server exits unexpectedly and a request fails, the owner restarts it in the background at most 3 times per 10 minutes, reports `LLAMACPP_RECOVERING` meanwhile and `LLAMACPP_CRASH_LOOP` beyond the bound. An operator stop is never treated as a crash. Status polls never wait for a model load.
4. **Operator default.** The operator configuration uses Gemma 4 12B QAT Q4_0 with thinking off. Switching to Qwen3.5-4B Q4_K_M is a configuration change of the model keys only.

## Non-goals

- No System-1/decision model in the loop, no automatic model or route switching, no cloud routing change, no Hermes re-pin, no new broker tool.
- No model files, paths or hashes in the repository; the operator configuration stays private.

## Required evidence

- Deterministic tests: thinking value parsing and request payload; each repair form, byte-identical pass-through of already-valid and non-proposal text, unchanged rejection of unknown names, non-object arguments and more than 4 calls; crash counted only for unexpected exits, bounded restarts, crash-loop state, status not blocked during a load.
- Real runtime on the operator machine through the one-click launcher with Gemma: a Sidecar chat answer and a Hermes agent turn that promotes a broker tool call and answers from its result, visible in Edge; VRAM/context reported; killing llama-server during use recovers without operator action; the same launcher starts with the Qwen3.5-4B configuration.

## Completion

The one-click JarvisOS starts on Gemma 4 12B QAT with thinking off, Hermes tool proposals from Gemma are promoted instead of leaking as answers, a llama-server crash recovers by itself, and Qwen3.5-4B remains a configuration switch away. Registry and PR association are reconciled after merge.
