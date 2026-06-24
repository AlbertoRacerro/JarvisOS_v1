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
