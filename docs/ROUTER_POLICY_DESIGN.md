# RouterPolicy Design v3.1.1

## Purpose

RouterPolicy is the deterministic layer that decides what a JarvisOS message is allowed to do next. It decides permission and routing; it does not execute.

## 1G-B2-F3-A2 deterministic probe

`1G-B2-F3-A2` adds a deterministic decision producer/probe, not runtime chat
routing. The producer emits full v3.1.1 RouterPolicy decision objects but
implements only minimal first-match routing behavior.

Evaluation order is:

1. secret/credential hard rule;
2. raw private/IP-sensitive context and provider/export boundary;
3. clarification or ambiguity;
4. unknown or not-positively-safe sensitivity before external escalation;
5. positively non-sensitive high-complexity external candidate proposal;
6. non-sensitive simple local chat;
7. deterministic safe fallback.

Safety rules run before routing/escalation rules. External escalation is
allowlist-based and requires `sensitivity_bucket_proposal in {public,
internal}`. Unknown, sensitive, or secret sensitivity never routes externally by
default, even for high-complexity scientific tasks.

ActionPreflight/world-model fields are populated conservatively. Non-routed
action/preflight fields use fail-safe restrictive defaults: no provider call, no
external network, no tool/browser/terminal/MCP execution, no memory/retrieval/file
state change, and no runtime execution.

Because the current semantic validator treats `external_allowed=true` as an
externally-authorizing route shape, A2-R1 represents high-complexity external
routing as proposal-only metadata: `proposed_external_target` may name the
external target, but `provider_candidate` remains non-external,
`external_allowed=false`, `provider_call_allowed_now=false`, and
`external_network_allowed_now=false`. Confirmation only creates review context;
it does not execute.

A2 keeps the producer as a module with unittest coverage. It does not add a CLI
smoke writer or any runtime report-generation path.

A2-R1 adds the contract invariant that `external_allowed=true` requires
`route_action=route_external_candidate`.

## 1G-B2-F3-A3 local-route smoke integration

`1G-B2-F3-A3` adds the first minimal usable local-route smoke path:

```text
normalized input
-> decide_router_policy(input_obj)
-> validate_router_decision_semantics(input_obj, decision)
-> safe-local execution guard
-> injected local responder
-> local response
```

A3 executes only validator-valid safe `LOCAL_FAST` local-answer decisions. The
execution guard checks permission booleans, not route labels alone. A decision
must use `route_action in {answer_local, route_local}`,
`route_tier=LOCAL_FAST`, a local provider candidate, `response_allowed_now=true`,
`allowed_execution_mode=answer_only`, no side effects, chat environment, and all
provider/network/tool/state permissions false.

A3 intentionally does not execute `LOCAL_ONLY`, `USER_CONFIRM`, `BLOCKED`,
`ask_clarification`, `ask_user_confirm`, external proposal decisions, or
`allowed_execution_mode=propose_only`. Sensitive local-only answering remains
future work.

The library path is offline-safe by default. If `responder=None`, A3 returns
`local_responder_missing` and calls no model. Tests use an injected fake
responder. Real local model execution is not implemented in A3 and remains
blocked pending an approved explicit local adapter.

A3 does not call external providers, execute tools/browser/terminal/MCP, write
memory/retrieval/file state, add backend routes, add frontend UI, add database
schema, or add BlueRev modeling behavior.

## 1G-B2-F3-A4 approved local responder adapter

`1G-B2-F3-A4` adds a narrow approved localhost-only Ollama `/api/generate`
responder adapter for injection into the A3 local-route smoke path.

The adapter is exposed as:

```text
build_local_responder(...) -> Callable[[str], str]
call_local_ollama_generate(prompt, ...) -> str
```

`build_local_responder` is side-effect free. It performs no network request, no
model availability check, no subprocess call, and no import-time model call.
Only the returned callable can contact Ollama, and only when caller code
injects it into `run_local_route`.

Endpoint validation uses `urllib.parse.urlparse`, not substring matching. A4
accepts only HTTP URLs for `127.0.0.1`, `localhost`, or `::1` with path
`/api/generate`, no credentials, no query string, and no fragment. Non-localhost
hosts, private LAN IPs, external domains, HTTPS external APIs, localhost-like
suffixes, and query/path tricks are rejected.

The payload is deterministic and bounded:

```json
{
  "model": "<model>",
  "prompt": "<message_text>",
  "stream": false,
  "options": {
    "temperature": 0
  }
}
```

The adapter sends only the prompt string received from A3. It does not include
RouterPolicy decision JSON, audit notes, memory, retrieval, file contents,
provider metadata, or tool instructions. Prompt length is bounded by
`max_prompt_chars`; output text is sliced to `max_output_chars`. Non-zero
temperature is rejected.

CLI `--run-local` constructs the local responder and injects it into A3. It does
not bypass RouterPolicy: decision production, semantic validation, and the
safe-local guard still run before the responder is called. Without `--run-local`
or with `responder=None`, no model is called.

Unit tests are offline and use fake clients. Manual smoke requires Ollama to be
running and the selected model to already be pulled locally.

A4 does not add external provider routing, non-localhost network calls,
tools/browser/terminal/MCP, memory writes, retrieval runtime, file-write
runtime, backend routes, frontend UI, database schema, or BlueRev modeling.

## 1G-B2-F3-A5 real-message local-route smoke bridge

`1G-B2-F3-A5` adds a controlled real-message smoke bridge:

```text
message_text
-> RouterPolicyInput v0_3_1_1
-> run_local_route(...)
-> injected/local responder only if all A3/A4 gates pass
```

A5 is not a production Phase A/B normalizer. No complete production
message-to-RouterPolicy-input normalizer exists in the current repository, so
A5 uses a clearly marked smoke-only fallback builder.

Fallback behavior is conservative:

- arbitrary CLI `--message` input defaults to no-execution;
- `--run-local` alone does not make fallback input executable;
- safe fallback CLI execution requires both `--assume-public-simple` and
  `--run-local`;
- `assume_public_simple` does not override deterministic hard-gate safety
  signals;
- detected secret/private/external/tool/memory/retrieval/clarification signals
  force conservative no-execution input.

A5 populates exactly `input_obj["message_text"]` with the original message
string. A3 still passes only that string to the injected responder. A5 does not
send RouterPolicy decision JSON, audit notes, memory, retrieval data, file
contents, reports, or fixture paths to the model.

A5 includes a private structural validator for the producer-used
RouterPolicyInput fields. It checks required sections, `message_text` equality,
critical boolean fields, string enum-like fields, list fields, and budget/router
types before calling A3. This is not complete Draft 2020-12 validation; schema
validation is unavailable, structural checks only.

CLI output is redacted by default. It does not print full input objects, raw
messages, full decision JSON, audit notes, or responses when `executed=false`.
When `executed=true`, response output is bounded.

`--run-local` still does not bypass RouterPolicy, the semantic validator, the
A3 safe-local guard, or the A4 localhost-only adapter.

A5 does not add broad routing, production Phase A/B classification, external
providers, non-localhost network calls, tools/browser/terminal/MCP, memory
writes, retrieval runtime, file-write runtime, backend routes, frontend UI,
database schema, or BlueRev modeling.

### 1G-B2-F3-A5-R1 operational-intent hard-gate repair

`1G-B2-F3-A5-R1` patches the A5 smoke builder so `assume_public_simple` cannot
authorize obvious operational intent.

The smoke-only builder now applies a small deterministic operational-intent
overlay before `_has_hard_gate_signal(input_obj)` runs. The overlay sets
existing schema-compatible hard-gate fields for:

- tool/MCP intent;
- browser/search intent;
- terminal/subprocess/shell intent;
- memory-write intent;
- retrieval/file-access intent;
- provider/upload intent.

If any such signal is detected, final input remains conservative even with
`--assume-public-simple --run-local`:

- `router_hint.task_type` is not `answer`;
- `router_hint.complexity` is not `low`;
- `context_metadata.assume_public_simple_safe_path` is `false`;
- `hard_reason_codes` is not `["low_risk"]`;
- category-specific fields such as `needs_terminal`,
  `needs_memory_write`, `needs_file_context`, `needs_current_info`, or
  `needs_provider_call` are set where schema-compatible.

This detector is smoke-only and conservative. It is not production Phase B/Qwen
classification, may over-block benign discussion of operational terms, and does
not replace future intent classification. Benign local answer smoke still
requires `--assume-public-simple --run-local`.

A5-R1 does not add production Phase A/B normalization, Qwen runtime integration,
external provider routing, tool/MCP/browser/terminal execution, memory writes,
retrieval runtime, file-write runtime, backend routes, frontend UI, database
schema, or BlueRev modeling.

### 1G-B2-F3-B1 Phase B RouterHint bridge

`1G-B2-F3-B1` adds an offline deterministic bridge from existing Phase B/Qwen
soft-review output to RouterPolicy `router_hint` and safe `action_hint` fields.

B1 maps advisory Phase B fields only:

- `soft_reason_code` is the primary `router_hint.task_type` driver;
- `primary_domain` maps to `router_hint.domain`;
- `domain_tags` help derive complexity and scientific-depth hints;
- `suggested_followup_question` forces clarification/review when required;
- `soft_uncertain_fields` lowers derived quality and can force review.

B1 does not depend on a Phase B `confidence` field. The Phase B soft-review
schema does not expose one. Instead, B1 derives `router_hint.confidence` from
real fields: required-field shape, recognized `soft_reason_code`, empty or
non-empty `suggested_followup_question`, and bounded uncertainty fields.

Phase A and operational gates remain fail-closed authority. If the input already
contains a hard gate, B1 cannot produce `task_type="answer"`,
`complexity="low"`, provider/tool/memory/retrieval permission, or route
selection authority. Phase B/Qwen cannot authorize execution, provider calls,
tools, memory writes, retrieval, or route selection.

B1 derives complexity and scientific-depth heuristically from
`primary_domain`/`domain_tags`. Phase B soft review was designed for
memory/review usefulness, not full routing classification, so a later dedicated
routing classifier or Phase B schema extension may be needed before removing
`--assume-public-simple` from real user-facing chat.

B1 does not call models or responders, does not run A3, does not add chat, and
does not add external provider routing, tool/MCP/browser/terminal execution,
memory writes, retrieval runtime, file-write runtime, backend routes, frontend
UI, database schema, workers, hooks, or BlueRev modeling.

### 1G-B2-F3-B2 Message Route Phase B Hint Bridge Flag

`1G-B2-F3-B2` wires the existing B1 bridge into the A5 real-message smoke path
behind explicit `--use-phase-b-hints`.

The B2 smoke order is:

```text
message
-> A5 smoke builder / Phase A overlay / A5-R1 operational gates
-> optional B1 Phase B RouterHint bridge
-> RouterPolicy decision
-> semantic validator
-> A3 safe-local guard
-> local responder only if safe
```

B2 completes the A5 smoke default `phase_b_soft_proposal` with the full
B1-compatible benign field set:

- `summary_short`;
- `project_bucket`;
- `primary_domain`;
- `domain_tags`;
- `storage_relevance`;
- `usefulness_for_future_review`;
- `possible_memory_card_type`;
- `soft_reason_code`;
- `brief_rationale`;
- `suggested_followup_question`;
- `soft_uncertain_fields`.

The new flag does not replace `--assume-public-simple`. `--use-phase-b-hints`
alone cannot make an arbitrary message executable. B1 hints are applied only
after the A5 builder and A5-R1 operational gates have produced the final smoke
input shape, and before the A5 structural check, RouterPolicy decision,
semantic validator, and A3 safe-local guard.

B2 keeps the B1 invariant: Phase B can enrich safe advisory hints or make a
route more conservative, but cannot authorize execution, provider calls, tools,
memory writes, retrieval, route selection, or external network access. If the
B1 bridge fails, the message-route smoke path fails closed with
`phase_b_hint_bridge_failed`.

`context_metadata` may contain B1 bridge metadata because the
RouterPolicyInput schema permits additional metadata keys and the A5 structural
validator checks only the required boolean metadata fields.

B2 does not add production chat, live Qwen/Gemma/Ollama classification, backend
routes, frontend UI, database schema, workers, hooks, MCP execution, memory
runtime, retrieval runtime, provider routing, file writes, or BlueRev modeling.

### 1G-B2-F3-B3 Default Phase B Hints

`1G-B2-F3-B3` makes B1 Phase B RouterHint bridge application default-on in the
A5 real-message smoke path. The integration point remains unchanged from B2:
B1 runs after the A5 builder, Phase A overlay, and A5-R1 operational gates have
finished the smoke input shape, and before structural validation, RouterPolicy
decision production, semantic validation, and the A3 safe-local guard.

CLI behavior:

- default: Phase B hints enabled;
- `--use-phase-b-hints`: retained as a backward-compatible alias for enabled;
- `--no-phase-b-hints`: explicit opt-out for baseline/debug smoke comparisons;
- `--use-phase-b-hints` with `--no-phase-b-hints`: rejected by argparse.

B3 changes only advisory hint plumbing. `--assume-public-simple` remains a
separate manual safety assertion and is still required for benign local
execution. `--run-local` remains required for real local responder
construction. `--run-local` alone does not execute.

Phase B hints remain advisory and non-authoritative. They can enrich a safe
RouterPolicy hint or make a route more conservative, but cannot authorize
execution, provider calls, tools, memory writes, retrieval, route selection, or
external network access. Hard-gate and operational-intent signals dominate
Phase B hints, and the A3 safe-local guard remains final authority before local
responder execution.

B3 is not production chat, not live Qwen/Gemma/Ollama classification, not a
production Phase A/B normalizer, and not approval to remove
`--assume-public-simple`. The A5 Phase B stub remains a smoke placeholder.

B3 does not add backend routes, frontend UI, database schema, workers, hooks,
MCP execution, memory runtime, retrieval runtime, provider routing, file writes,
terminal/browser execution, or BlueRev modeling.

### 1G-B2-F3-B3-R1 malformed-input boundary repair

`1G-B2-F3-B3-R1` adds a pre-bridge structural validation boundary to the A5
message-route smoke wrapper. The A5 builder output is validated before the
default-on B1 Phase B hint bridge runs, then validated again after B1 returns.

The current smoke path intentionally uses the same private A5 structural
validator before and after B1. This is acceptable because the A5 builder already
emits a complete structurally valid `RouterPolicyInput`.

Required interpretation:

- pre-B1 validation proves the builder or future producer output is valid
  enough to hand to B1;
- B1 is an advisory Phase B RouterHint bridge, not a production normalizer;
- post-B1 validation checks the enriched structure before RouterPolicy
  decision production and A3.

This prevents B1 from normalizing malformed safety-critical fields, such as
string booleans or malformed policy lists, into executable-safe values before
A5 rejects the input. The original mutable object returned by an injected
builder must not be repaired in-place, malformed input must not reach
`_RUN_LOCAL_ROUTE`, and malformed input must not execute.

Safety-critical fields include at least Phase A hard-gate booleans, action
execution-risk booleans, provider/user/budget policy fields, and router fields
required before B1.

For future live or per-message Phase B producer work, the live producer must
emit a structurally valid Phase B proposal before B1 consumes it. Malformed live
producer output must fail closed before B1 or inside B1. B1 must not normalize
arbitrary raw model output into valid RouterPolicy input.

Do not treat schema-valid, structurally valid, model-produced, or
Phase-B-enriched output as semantically safe. Execution still requires
deterministic hard gates, operational-intent gates, `--assume-public-simple` in
smoke, validator-valid RouterPolicy decision output, the A3 safe-local guard,
and an injected responder or explicit `--run-local`.

Qwen/Phase B live output may propose hints only. It must not authorize
execution, provider calls, tool/MCP/browser/terminal actions, memory writes,
retrieval, route selection by itself, or removal of `--assume-public-simple`.
Partial or greedy live Phase B output must go through a separate deterministic
adapter/validator layer before reaching B1.

B3-R1 does not change B1 behavior, A3 safe-local guard behavior, A4 local
responder behavior, RouterPolicy decision production, semantic validation,
schemas, backend routes, frontend UI, DB schema, memory/retrieval runtime,
provider/tool/MCP/browser/terminal runtime, workers, hooks, or BlueRev
modeling.

### 1G-B2-F3-B4 deterministic Phase B source

`1G-B2-F3-B4` adds an explicit offline message-route smoke path that replaces
the fixed benign Phase B stub with deterministic per-message Phase B soft-review
output from `local_phase_b_soft_review_probe.build_soft_review`.

The default B3 path still uses the fixed benign stub unless the explicit B4
offline source is requested. The deterministic Phase B source receives the same
synthetic/sanitized message and the same deterministic Phase A output generated
by A5, preserving a coherent triple:

```text
same message/case_id
-> deterministic Phase A overlay
-> deterministic Phase B soft review
-> B1
-> RouterPolicy/A3
```

The Fast Secretary Phase B builder already emits the B1-compatible field shape,
so no adapter is required. Cross-case Phase A/Phase B mixing is rejected before
B1. Malformed deterministic Phase B output fails closed before RouterPolicy/A3.

B4 does not add live Qwen/Gemma/Ollama calls, provider calls, tools, MCP,
browser/terminal runtime, memory/retrieval runtime, backend routes, frontend UI,
DB schema, or BlueRev behavior. Phase B remains advisory only; Phase A/gates,
RouterPolicy, and A3 remain authority.

## 1G-B2-F3-A1 boundary

This document is part of the RouterPolicy contract layer only. It does not add
runtime routing, provider calls, tool execution, browser or terminal actions,
MCP, file writes, memory writes, retrieval behavior, backend routes, frontend
behavior, database schema, or BlueRev modeling.

## Lifecycle

```text
initial_request
dry_run_ready
awaiting_confirmation
confirmed_execution
blocked
```

A confirmed execution decision must include `consent_context` proving which previous decision and payload were confirmed.

## Permission split

```text
response_allowed_now
tool_execution_allowed_now
provider_call_allowed_now
external_network_allowed_now
state_change_allowed_now
```

`external_network_allowed_now` covers browser/search/networked tools/MCP. It prevents browser/search from bypassing redaction under the generic tool permission.

## Confirmation

If confirmation is required, the decision must include:

```text
confirmation_payload
confirmation_digest
confirmation_options including allow_once and deny
expires_at
requires_new_decision_after_confirmation=true
```

The confirmation click records consent. A new RouterPolicy decision must be generated before execution.

## Provider fields

```text
provider_candidate = currently policy-eligible provider
proposed_external_target = target displayed for confirmation/preflight
```

External proposed target is not authorization.

## Budget ordering

Executable/cost tiers are ordered:

```text
LOCAL_ONLY = 0
LOCAL_FAST = 1
CHEAP_EXTERNAL = 2
SCIENTIFIC_MEDIUM = 3
FRONTIER = 4
```

`USER_CONFIRM` and `BLOCKED` are control states, not cost tiers.

## Default

If uncertain:

```text
external_allowed=false
provider_call_allowed_now=false
external_network_allowed_now=false
state_change_allowed_now=false
allowed_execution_mode=propose_only or blocked
```

Unknown is not executable.

Rule 9 fallback prevents undefined behavior when high-complexity external
routing is unavailable because of budget, provider policy, external-disabled
policy, or non-safe sensitivity.
