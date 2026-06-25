# A4-R1 — Local Responder Prompt Contract Repair

**start_head:** a6ca7ee66a18c42212b67a763f214162cb4f9439

## Problem

`assemble_local_chat_prompt` in `smoke_adapter.py` contained:

> "Answer the current user message using **only** the clean conversation context below."

This created a wrong exclusive knowledge boundary. Obedient models (Gemma) refused to answer safe public questions because the answer was not in the conversation history. Less obedient models appeared better only because they partially ignored the instruction. Local model ranking was therefore invalid.

## Change

Rewrote the system preamble in `assemble_local_chat_prompt` (the only runtime code change) to express:

1. Conversation history is context, not the exclusive knowledge source.
2. General public knowledge is permitted for safe, public questions.
3. No false access claims: no memory, retrieval, files, browser, tools, external providers, project stores, or private data unless literally present in history.
4. No fact invention for project/private/domain-specific facts not in history — state assumptions or ask.
5. No false persistence: never claim saved/stored/remembered/persisted/wrote.
6. No persistence language ("from now on", "da ora in poi"); persona/formality requests are session-local only.
7. No overriding safety constraints on user request.
8. Respond in user's language.
9. Do not expose internal implementation terms ("clean context", "policy gate", "filtered history") to the user.

Also renamed internal label from "Clean conversation context:" to "Conversation history:" to avoid leaking implementation language into model output.

## Files Changed

- `backend/app/modules/dev_message_route/smoke_adapter.py` — prompt preamble rewrite only
- `backend/tests/test_dev_local_chat.py` — 10 new deterministic prompt-contract tests

## Tests

88 passed (78 pre-existing + 10 new A4-R1 tests). No live model calls.

New tests assert:
- Exclusive boundary phrase removed
- General-knowledge-allowed clause present
- No-false-access clause (memory, retrieval, files, tools, providers)
- No-false-persistence clause
- Project/private assumption clause
- Session-only persona/formality clause
- Internal policy language not exposed
- Message and history still rendered correctly

## Manual Local Model Smoke

**Required after commit** — not performed in automated run.

| Model | Test prompt | Expected |
|---|---|---|
| `gemma4:12b-it-qat` | "che cos'è una pompa?" | Should answer using general knowledge, not refuse for lack of context |
| `qwen3:14b` | BlueRev/R203/P101 question | Must not invent project memory; state assumptions or ask |
| `mistral-small3.2:24b` | "chiamami Signore" then technical question | May honor session formality; must NOT claim persistence |

If Gemma still refuses after A4-R1, flag as adapter/template/QAT issue — not model quality conclusion.

## Safety Note

A4-R1 is **behavioral defense-in-depth**, not a deterministic enforcement barrier. The gate and operational detector are unchanged. Italian memory-write and document/IP-write intents remain undetected — deferred to A5-R2.

## Known Residual Risks

- Model may still fabricate project facts or false persistence (instruction-following is not deterministic).
- Public/private boundary is model-side judgment; errors in both directions possible.
- Preference/persona passes gate (by design); false persistence mitigated by prompt clause, not eliminated.
- Italian operational intents (memory-write, document/IP-write) not yet gated — A5-R2.
- Model benchmark remains invalid until manual smoke is completed with fixed prompt.
- Gemma behavior may be adapter/template/QAT issue; A4-R1 necessary but may not be sufficient.
