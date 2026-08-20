# Hermes Agent code-first audit against JarvisOS AI

Date: 2026-08-20  
JarvisOS base: `f9db1e97d152ee7a4c2c7ed91653eec056af6b76`  
Hermes upstream: `NousResearch/hermes-agent`  
Hermes inspected head: `27562ad5f80e90f7d552f92dbd4af7f1f511c3c8`  
License: MIT  
Status: audit/reference only; **not implementation authority**

## Decision rule

Treat JarvisOS and Hermes as two unrelated external candidates for a hypothetical new system. Existing JarvisOS implementation has zero sunk-cost preference. Keep Jarvis code only where it wins on required properties; replace it where Hermes is materially stronger; combine them only when the responsibilities are genuinely complementary.

Labels used below:

- `KEEP JARVIS`: the Jarvis implementation/property should remain authoritative.
- `REPLACE WITH HERMES`: the current Jarvis implementation is weaker and should eventually be removed after migration/equivalence tests.
- `HYBRID`: use Hermes runtime mechanics under Jarvis deterministic authority or engineering-state contracts.

## Executive result

Hermes is materially ahead of JarvisOS as an **agent runtime**. JarvisOS is materially ahead of Hermes as a **deterministic authority, egress, sensitivity, budget, provenance, and engineering-state boundary**.

The preferred direction is therefore not two parallel AI stacks and not a wholesale Hermes embed. It is:

```text
Jarvis deterministic authority + engineering state
    RouterPolicy
    sensitivity / egress / budget / confirmation
    canonical context + provenance + evidence
    model/assumption/parameter state
              |
              | typed capability envelope
              v
Hermes-derived agent runtime kernel
    conversation/tool loop
    real tool registry + toolsets
    MCP/plugin discovery
    progressive tool disclosure
    delegation/subagents
    memory-provider mechanics
    skills mechanics, gated
    observer/middleware lifecycle
              |
              v
Jarvis validation / promotion / audit
```

A consequential Hermes tool call must never become a second authority path around JarvisOS policy.

## Code-first comparison

| Subsystem | Decision | Evidence and reason |
| --- | --- | --- |
| Agent conversation/tool loop | **REPLACE WITH HERMES** | Jarvis `backend/app/modules/ai/execution.py` is deliberately a provider-neutral completion/execution spine: it resolves a route, calls an adapter, records evidence, handles continuation/fallback. Hermes `agent/conversation_loop.py` is a real multi-turn tool-calling agent loop with tool dispatch, retries, failover, compression and post-turn hooks. Rebuilding this in Jarvis has little value. |
| Tool registry | **REPLACE WITH HERMES** | Jarvis `backend/app/modules/tools/registry.py` is a minimal dictionary skeleton. Hermes `tools/registry.py` is a mature central registry with schema, handler, toolset, availability check, async metadata, dynamic schema overrides, collision/override policy and discovery caching. |
| Toolsets / capability surfaces | **REPLACE WITH HERMES mechanics** | Hermes `toolsets.py` composes capability sets and keeps platform/session-specific surfaces separate. This is substantially more mature than Jarvis's current skeleton. Jarvis policy must still decide which toolsets may be granted. |
| MCP/plugin discovery | **REPLACE WITH HERMES mechanics** | Hermes dynamically discovers built-ins/plugins and exposes only available definitions. This is an existing solution to a problem Jarvis has not yet solved. |
| Progressive tool disclosure | **REPLACE WITH HERMES** | `tools/tool_search.py` implements stateless per-assembly catalogs and `tool_search` / `tool_describe` / `tool_call`; core tools stay eager while MCP/plugin schemas defer. The session's enabled toolset remains the discovery boundary. This directly addresses context-window growth as BLUECAD accumulates scientific backends. |
| Delegation/subagents | **REPLACE WITH HERMES runtime, wrap with Jarvis authority** | Hermes has real synchronous/async delegation, separate child contexts/terminals, concurrency controls, nested-role restrictions, stale monitoring and regression tests. Jarvis does not currently have a comparable product runtime. Child authority must be a monotonic subset of the parent Jarvis capability envelope. |
| Observer/middleware lifecycle | **IMPORT/HYBRID** | Hermes exposes pre/post LLM/tool hooks plus middleware for request/execution wrapping. This is useful for telemetry, verification and backend adapters. Jarvis policy must remain outside/below behavior-changing middleware so a plugin cannot grant itself authority. |
| Memory provider orchestration | **HYBRID** | Hermes `agent/memory_manager.py` is a stronger runtime integration point: provider initialization, prompt contribution, prefetch, background sync, tool routing, lifecycle and failure isolation. Jarvis engineering decisions/assumptions/parameters/evidence remain canonical records and must not be replaced by generic agent memory. |
| Skills/procedural learning | **HYBRID, gated more strongly than Hermes defaults** | Hermes already has skill management and background review. Keep the mechanics, but do not permit autonomous skill writes to become authoritative execution instructions without deterministic scan/staging/promotion. |
| Provider plumbing/model switching | **HYBRID** | Hermes has broader provider/model runtime plumbing. Jarvis already has a strong provider registry, explicit execution classes, pricing/caps/fallbacks and audited jobs. Prefer reuse of Hermes adapters where they reduce maintenance, while Jarvis retains routing/egress/budget decisions and ledger authority. |
| Router / egress / sensitivity | **KEEP JARVIS** | Jarvis `backend/app/modules/ai/routing/decision.py` explicitly separates deterministic policy from execution and encodes sensitivity, budget, external-target scope, confirmation intent, network/tool/state-change allowance and safe local fallback. Hermes approvals are not an equivalent global authority layer. |
| Budget and paid-provider controls | **KEEP JARVIS** | Jarvis treats budget/provider eligibility as deterministic product policy before execution. This should remain above any Hermes provider/runtime selection. |
| Context provenance | **KEEP JARVIS, feed Hermes** | Jarvis `context_builder.py` validates context blocks, separates project data from instructions, computes canonical digests/source manifests and selects engineering records deterministically. Hermes can consume the resulting context pack; it should not erase provenance. |
| Engineering model/evidence state | **KEEP JARVIS** | Jarvis has first-class ModelSpec, assumptions, parameters, requirements, evidence, confidence/status and supersession semantics. Generic agent memory is not a replacement for engineering truth. |
| Current Jarvis `agents/` skeleton | **DELETE/REPLACE when migration is authorized** | There is no architectural reason to preserve a tiny registry skeleton after a tested Hermes-derived runtime exists. |
| Current Jarvis `tools/` skeleton | **DELETE/REPLACE when migration is authorized** | Same conclusion: retain compatibility shims only for migration, not as permanent duplicate infrastructure. |

## Hermes implementation evidence worth importing

### 1. Tool registry and dynamic capability discovery

`tools/registry.py` is not a README facade. A registered tool carries at least:

- name;
- toolset;
- JSON schema;
- handler;
- availability/check function;
- environment requirements;
- sync/async behavior;
- description/display metadata;
- result-size policy;
- runtime-dynamic schema overrides.

Cross-toolset shadowing is rejected unless an explicit override path is used, and plugin override of built-ins requires operator opt-in. Availability probes are cached briefly instead of repeated on every schema assembly.

This should supersede Jarvis's current dictionary-only tool registry rather than be reimplemented from scratch.

### 2. Progressive disclosure is especially relevant to BLUECAD

`tools/tool_search.py` addresses the exact scaling problem BLUECAD will create: dozens or hundreds of scientific adapters can make tool JSON schemas consume substantial context on every turn.

Hermes keeps core/session-defining tools direct and defers MCP/non-core plugin tools behind:

- `tool_search`;
- `tool_describe`;
- `tool_call`.

The catalog is rebuilt from the current tool definitions each assembly, rather than maintaining a drifting session cache. Disclosure degrades from descriptions to names to server summaries as the catalog grows. The bridge remains scoped to the session's already granted toolsets.

For JarvisOS this should become a capability-discovery optimization **after** Jarvis policy has produced the allowed toolset. It must not discover tools outside the granted capability envelope.

### 3. Delegation is real and should not be rebuilt casually

Hermes has a substantial `tools/async_delegation.py` implementation plus dedicated tests. It tracks running units/children, capacity, parent session identity, progress/stale state, cancellation and completion routing. Documentation also distinguishes normal leaf children from nested orchestrators and warns that process-local background delegation is not durable across process/session loss.

Jarvis should reuse these mechanics, but change the authority contract to:

```text
child_capabilities = parent_capabilities INTERSECT requested_child_capabilities
```

A child must never regain network, filesystem, provider, memory-write or engineering-state permissions denied to its parent.

### 4. Memory manager is useful as plumbing, not as engineering truth

Hermes's `MemoryManager` centralizes memory-provider lifecycle, prefetch, sync and tool routing, allows at most one external plugin provider, and isolates provider failures. This is better runtime plumbing than adding backend-specific memory code throughout Jarvis.

However, Jarvis's structured engineering records remain categorically different from conversational memory. A saved Hermes memory cannot silently supersede a measured parameter, accepted assumption, requirement or validated evidence record.

### 5. Observer and middleware contracts are strong extension seams

Hermes has explicit lifecycle hooks for LLM requests, tools, approvals and subagents, plus middleware that can rewrite/wrap LLM or tool requests/execution while preserving downstream hooks and approval handling.

Useful Jarvis adaptation:

```text
Hermes runtime middleware
        -> Jarvis typed policy preflight
        -> tool execution
        -> deterministic verifier
        -> Jarvis event/evidence ledger
```

Do not allow a plugin middleware to become the policy authority. Behavior-changing middleware is code, not trusted model output, but it still sits below Jarvis product policy.

## Negative evidence: do not import Hermes's safety posture wholesale

Hermes is not a drop-in replacement for Jarvis authority.

### Approval coverage is narrower than Jarvis needs

Current Hermes approval logic is heavily centered on terminal dangerous-command detection. File tools have had separate sensitive-path handling rather than one general consequential-action authority contract. Open issues in 2026 document inconsistent treatment between `terminal`, `write_file`, `patch`, and the official config CLI.

Examples retained as negative evidence:

- `#45563`: config writes through `patch`/`write_file` can be hard-blocked instead of using the approval lifecycle;
- `#81101`: reported route where `hermes config set approvals.mode off` could bypass the intended config-file protection path in the affected version;
- `#48344`: request for a true filesystem allowlist because smart approvals do not generally gate file tools.

Some of these paths are actively changing upstream; revalidate exact code before implementation. The architectural lesson is stable: Jarvis needs a single typed authority boundary across **all consequential tools**, not command-regex safety as the primary permission model.

### Self-updating skills require stronger promotion

`agent/background_review.py` really does fork a restricted review agent after turns and can write memory/skills. That mechanism is useful. The default trust posture is not sufficient for JarvisOS: issue `#78515` reports agent-authored skill content reaching future system prompts without the optional guard enabled by default in the affected configuration.

Jarvis adaptation should therefore use:

```text
agent proposes skill change
 -> staging artifact
 -> deterministic content/security scan
 -> provenance + diff
 -> bounded approval/promotion policy
 -> only then active skill
```

For high-risk skills, require explicit user promotion.

## Sunk-cost decision

The comparison already justifies deleting/replacing real Jarvis work when an implementation spec is authorized:

1. replace the current `tools/` registry skeleton rather than expand it independently;
2. replace the current `agents/` skeleton rather than grow a parallel agent framework;
3. use Hermes's conversation/tool loop instead of independently reproducing a mature tool-calling runtime;
4. reuse Hermes delegation/tool-search/plugin/memory-manager mechanics where tests confirm behavior;
5. keep Jarvis's deterministic authority, egress, budget, sensitivity, canonical context and engineering-state layers as the wrapper and source of truth;
6. remove compatibility shims once equivalence tests and migrations prove no remaining callers need them.

The intended end state is one runtime, not `JarvisAgent + HermesAgent` competing inside the product.

## Suggested implementation order when promoted

This is a candidate sequence, not current implementation authority.

### H0 — exact-version spike

- vendor/fork or adapter against one pinned Hermes commit;
- run a Hermes tool-calling loop behind a Jarvis-issued capability envelope;
- initially allow only read-only/no-side-effect tools;
- prove every LLM/provider call and tool call can be correlated to a Jarvis run/flow record;
- no new memory/skill writes.

### H1 — replace tool infrastructure

- replace Jarvis tool/agent skeletons with Hermes-derived registry/toolsets;
- add Tool Search progressive disclosure;
- preserve Jarvis allow/deny capability decision before definitions are exposed to the model;
- add conformance tests that forbidden tools cannot be searched, described or called through the bridge.

### H2 — agent loop and delegation

- move normal agent execution to the Hermes-derived conversation loop;
- add subagent delegation;
- enforce monotonic inherited authority and deterministic child run records;
- verify child claims against parent outputs/tests rather than trusting summaries.

### H3 — memory/skills

- use Hermes memory-provider lifecycle where useful;
- keep Jarvis engineering records canonical;
- introduce staged skill changes and gated promotion;
- disable direct autonomous activation of newly written skills until the stronger policy exists.

### H4 — provider/runtime consolidation and deletion

- compare Hermes provider adapters against Jarvis adapters one by one;
- retain only the stronger implementation behind Jarvis provider/egress/budget contracts;
- delete superseded Jarvis agent/tool/runtime compatibility paths after migration tests;
- do not keep duplicate frameworks for historical reasons.

## Minimum-necessary conclusion

Hermes integration belongs near the front of the external-integration queue because it is **multiplicative infrastructure**: a stronger agent/tool/delegation runtime can later implement and maintain scientific adapters more cheaply.

That does **not** justify stopping the current broad discovery/audit phase or integrating every Hermes subsystem immediately. First promote the smallest migration slice that gives Jarvis a real extensible tool runtime while preserving its stronger authority boundary.

## Revalidation triggers

Before implementation, re-check:

- current Hermes head/release and license;
- exact plugin/tool registry contracts;
- current fixes for approval/config/file-tool issues;
- current skill guard defaults;
- Windows behavior and local-model behavior;
- dependency footprint relative to JarvisOS;
- upstream API stability and whether vendoring, fork, library import or narrow adapter gives the lowest long-term maintenance cost.
