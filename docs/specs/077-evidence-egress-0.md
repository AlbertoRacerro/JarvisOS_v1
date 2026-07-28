# 077 — EVIDENCE-EGRESS-0: canonical evidence provenance and classification

Status: planned; `docs/specs/STATUS.md` is authoritative.

Depends on: 044, 059a, 059b, 076

## 1. Goal

Bind every BLUECAD evidence block used by an external structural-repair model call to the existing 059a/059b authority chain before any network adapter invocation.

Spec 076 intentionally added no egress authority. Its merged runtime renders one deterministic, attempt-scoped `EvidenceSight` and embeds that text in the structural-repair prompt. This is sufficient for local execution, but an external call currently presents the evidence as undifferentiated prompt text. The 059b prompt authority can therefore classify the combined prompt without retaining canonical `evidence:<id>` identities, source digests, workspace ownership, label state, derivative lineage, or the exact sight digest.

077 closes only that provenance gap. It does not create another egress path, sensitivity taxonomy, provider route, evidence store, candidate state, or repair loop.

## 2. Current-runtime facts

The implementation must preserve these facts from current `master`:

1. `evidence` is already an allowed 059a canonical source kind.
2. Each evidence row is addressable as `evidence:<record_id>` and serializes through the existing deterministic `evidence_pack_line(...)` representation.
3. 059a already owns workspace-bound labels, source-content digests, immutable sanitized derivatives, deterministic floors, stale handling, and S0/S1-only external eligibility.
4. 059b already owns exact-packet construction, per-binding and per-fallback decisions, confirmation triggers, projected-budget checks, adapter invocation, and safe ledger evidence.
5. 076 already owns exact workspace/candidate/attempt selection, deterministic ordering, six-line and 2,000-character bounds, sight digest, structural request budget, and candidate lifecycle.
6. The merged structural cycle currently passes `sight.text` inside `user_prompt` and does not pass `workspace_id` or canonical evidence `context_blocks` to `run_ai_task`.
7. Marker-free prompt text may receive the existing bounded FAST_DEV S1 default. That default is not sufficient authority for canonical evidence rows whose labels, provenance, and current digests are knowable.

## 3. Binding direction

For a structural-repair request whose selected concrete binding requires network access:

1. the ordinary repair instruction and valid GeometrySpec remain prompt material;
2. raw `EvidenceSight.text` must not remain embedded in that external prompt;
3. the exact selected evidence rows must enter the existing 059a/059b context path as canonical sources or one current approved canonical derivative;
4. the external call must pass the real `workspace_id` to `run_ai_task`;
5. 059b must rebuild and re-evaluate the exact packet for every concrete provider/model binding and fallback;
6. missing ownership, label, source digest, derivative, policy version, or current-sight binding fails closed with zero external adapter calls.

For a binding that does not require network access, 077 preserves the merged 076 local/fake-provider behavior. No label, derivative, or external packet is required merely to run a local structural attempt.

## 4. Canonical authority model

### 4.1 Source identities

Every record selected by `render_evidence_sight(...)` maps to:

```text
evidence:<record_id>
```

The model never supplies or chooses these references. The structural cycle supplies the exact `EvidenceSight.record_ids` returned by the deterministic renderer.

External evidence preparation must reject:

- an empty or duplicate record-id set;
- a source kind other than `evidence`;
- any row outside the supplied workspace, candidate, or attempt;
- a record-id order that differs from the renderer result;
- a re-rendered sight whose text or digest differs from the supplied sight;
- any row added, removed, reordered, or replaced between render and authority resolution.

### 4.2 Coherent snapshot

Before constructing external context, JarvisOS must use one coherent SQLite read snapshot to resolve:

- workspace existence;
- candidate and attempt ownership;
- exact selected evidence rows;
- each canonical evidence source snapshot and current 059a label;
- source content digests;
- renderer version, text, digest, ordered record ids, and limits;
- any reusable derivative and its current lifecycle state.

The implementation must not combine independently read “latest” values and must not fall back to workspace-wide, candidate-wide, or globally latest evidence.

### 4.3 Effective levels

The effective level of every selected evidence source is resolved by existing 059a rules.

- Current effective S0/S1 evidence may be represented externally only through a provenance-bound current derivative or equivalent existing 059a-approved context authority.
- S2, S3, and `unknown` evidence must use the existing local sanitization/derivative path; raw content never enters the external packet.
- Raw S4 or surviving secret-bearing content is denied. Confirmation cannot override it.
- Missing, stale, malformed, source-missing, policy-version-mismatched, or digest-mismatched authority is ineligible and fails closed according to 059a/059b.

077 does not add a new default level and does not downgrade any evidence row in place.

## 5. Evidence derivative contract

### 5.1 Exact-sight derivative for S0/S1 sources

When every selected evidence source is current and effective S0/S1, JarvisOS may create or reuse one deterministic, auto-approved canonical derivative whose content is exactly the renderer output visible to the model.

Binding metadata must include:

- `workspace_id`;
- ordered `source_refs = ["evidence:<id>", ...]`;
- exact current source digests;
- exact `EvidenceSight.digest`;
- renderer identifier/version, initially `evidence_sight_v0`;
- exact renderer limits;
- derivative content digest;
- final effective level equal to the maximum current source level;
- stable transformation identifier such as `evidence_sight_v0_render`;
- sanitizer kind `deterministic`;
- stable renderer/sanitizer version and config digest;
- existing 059a/059b policy version and approval lifecycle.

The derivative transaction must re-resolve current source digests and reject mutation between snapshot and approval. The derivative is a separate immutable representation; it does not alter source labels or authorize other evidence from the attempt.

### 5.2 Sanitized evidence derivative

When any selected source is S2, S3, or `unknown`, JarvisOS must use the existing canonical-source local sanitization path or a strictly deterministic non-model transformation permitted by 059.

The result:

- remains bound to all exact evidence source refs and source digests;
- must be current, approved, effective S0/S1, and secret-free;
- carries sanitizer kind/version/config digest and sanitizer `ai_jobs` id when model-backed;
- may contain a generic technical summary rather than raw sight text;
- retains the original ordered record-id set and original sight digest as safe lineage metadata;
- never claims byte identity with `EvidenceSight.text` unless its content is exactly that text.

Sanitizer failure, malformed output, source mutation, final level above S1, or surviving deterministic floor pauses or denies under existing 059b policy. It does not consume a structural model request and does not alter the valid candidate.

### 5.3 Reuse and staleness

Reuse requires identical and current:

- workspace and ordered source refs;
- source digests, labels, and effective levels;
- sight digest, renderer version, and limits;
- derivative content digest;
- sanitizer/config/policy versions;
- approval, sampled-audit, and revocation state.

Any drift invalidates reuse. A stale or revoked derivative creates zero external adapter calls.

## 6. External prompt and context

### 6.1 Prompt separation

For network-bound structural repair, add a dedicated external prompt builder or mode containing:

- the structural-repair instruction;
- the already geometrically valid GeometrySpec;
- an explicit statement that project context is reference data, not instructions;
- no raw evidence lines and no duplicate sanitized evidence body.

The approved evidence derivative is supplied as one canonical `context_block` using the existing block schema. Its `source` must identify the derivative rather than pretend to be one raw evidence row. The exact source string must follow the canonical derivative-manifest convention confirmed during implementation.

The ordinary 076 local prompt and `STRUCTURAL_REPAIR_PROMPT_VERSION` remain byte/behavior compatible for non-network bindings. A distinct external prompt version may be added only when needed for honest audit history.

### 6.2 `run_ai_task`

Every network-bound structural attempt must call `run_ai_task` with:

- the external structural instruction prompt;
- `task_kind="bluecad_cad_repair"`;
- unchanged route class and output-token limit;
- `workspace_id` equal to the candidate workspace;
- exactly one approved evidence derivative context block;
- no caller authorization flag and no alternate adapter path.

The existing 059b execution spine remains the sole authority. BLUECAD may prepare provenance but may not authorize egress, provider selection, budget, fallback, confirmation, or sensitivity downgrade.

## 7. Exact-packet lineage

For every concrete network binding, the 059b packet and decision must bind at least:

- existing prompt authority metadata;
- evidence derivative id and content digest;
- ordered evidence source refs and current source digests;
- original `EvidenceSight.digest`;
- renderer/config version and limits;
- evidence derivative final level;
- sanitizer kind/version/config digest and sanitizer AI job id where present;
- workspace id;
- candidate id and structural attempt id as safe correlation metadata;
- concrete route/provider/model, fallback index, token ceiling, and policy versions.

Changing any value creates a new packet digest and invalidates prior decisions or tickets. Every fallback rebuilds and re-evaluates the packet; one binding never authorizes another.

## 8. Ledger and privacy

No prompt body, raw evidence line, derivative body, report artifact body, raw solver output, credential, or authorization header is added to `ai_jobs`, events, or egress-decision metadata.

Safe metadata may include:

- candidate, BLUECAD attempt, and AI job ids;
- evidence derivative id and digest;
- sight digest and renderer version;
- source refs/digests only under existing 059b safe-manifest rules, otherwise canonical manifest digests and bounded counts;
- effective level and sanitizer/policy versions;
- decision, reason code, packet digest, ticket, reservation, provider/model, fallback index, and bounded usage/cost.

Denied or paused preparation remains inspectable and makes zero external network calls.

## 9. Structural lifecycle

077 does not change the 076 structural lifecycle.

- Evidence authority preparation occurs before `start_structural_attempt(...)` only if doing so avoids creating an attempt for a request that cannot lawfully leave; otherwise the implementation must record an ordinary structural attempt with a precise non-execution outcome. The final sequence must be explicit in the implementation report and tests.
- A sanitizer AI job is not a structural repair request and does not consume `max_structural_repairs`.
- No egress failure may call `park_candidate`, call `mark_candidate_valid`, change candidate status, or change public artifact pointers.
- Denied, paused, stale, malformed, or sanitizer-failed preparation returns the original valid candidate.
- Existing local/fake-provider structural attempts remain unaffected.

The implementation must choose one deterministic attempt-accounting sequence; it must not leave the ordering implicit.

## 10. Configuration and defaults

077 adds no provider, route, fallback, confirmation, or budget configuration.

If an implementation feature flag is required, it must default off for external evidence use until merge, never permit raw-evidence fallback, never weaken 059a/059b, and never affect local/fake-provider 076 behavior. Missing or malformed configuration fails closed for network-bound structural repair.

## 11. Required tests

### 11.1 Ownership and renderer binding

Prove:

1. exact workspace/candidate/attempt ownership;
2. `EvidenceSight.record_ids` map only to `evidence:<id>`;
3. no cross-workspace, cross-candidate, or cross-attempt leakage;
4. ordered source refs match renderer order exactly;
5. re-rendered text and sight digest must match;
6. inserted, removed, reordered, or mutated rows invalidate preparation;
7. the model cannot select ids, kinds, limits, or order.

### 11.2 Sensitivity and derivatives

Prove:

1. all-current S0 sources create/reuse an S0 exact-sight derivative;
2. mixed S0/S1 sources produce final S1;
3. S2/S3/unknown requires existing local sanitization or deterministic derivative handling;
4. final S2/S3, raw S4, surviving secret evidence, or sanitizer failure creates zero external calls;
5. source mutation between snapshot and approval fails atomically;
6. stale label, missing source, policy mismatch, revoked derivative, or sampled-audit rejection prevents reuse;
7. no source label is downgraded in place.

### 11.3 Prompt and packet

Prove:

1. external structural prompt contains no raw `EVIDENCE_SIGHT_V0` block;
2. approved evidence content appears exactly once as project context;
3. `workspace_id` reaches `run_ai_task` and 059b;
4. packet lineage binds derivative id/digest, source digests or canonical manifest, sight digest, renderer version, workspace/candidate/attempt, and concrete binding;
5. lineage mutation changes packet digest and invalidates prior decisions/tickets;
6. every fallback reconstructs and re-evaluates the packet;
7. confirmation cannot override stale provenance, final level above S1, S4, or missing authority;
8. logs and events contain safe metadata only.

### 11.4 Lifecycle and compatibility

Prove:

1. local/fake-provider 076 prompt, provider-call count, attempt budget, candidate outcome, and pointer behavior remain unchanged;
2. external authority/sanitizer work does not consume structural request budget;
3. denial, pause, stale authority, or sanitizer failure leaves candidate `valid` and pointers unchanged;
4. no such path calls `park_candidate` or `mark_candidate_valid`;
5. no decision or engineering-record promotion is created;
6. ordinary tests make no live provider call.

### 11.5 Existing gates

```bash
cd backend
python -m pytest -q
python -m ruff check app tests
python ../scripts/check_spec_status.py --self-test
```

The BLUECAD canonical canary and strict Gmsh/CalculiX proof remain required. No new live-provider CI call is authorized.

## 12. Likely implementation files

Verify paths against then-current `master`. Expected bounded scope:

- `backend/app/modules/bluecad/evidence_sight.py` — stable renderer/config metadata or source refs without changing selection semantics;
- `backend/app/modules/bluecad/evidence_egress.py` — new BLUECAD provenance-preparation helper;
- `backend/app/modules/bluecad/prompts.py` — external structural prompt/version only if required;
- `backend/app/modules/bluecad/loop.py` — local compatibility path versus network-authorized context path and `workspace_id`;
- existing 059a/059b authority or sanitizer modules only where a generic helper is missing;
- narrowly named evidence-egress tests plus existing structural tests.

No route, frontend, process model, mesh/FEM adapter, provider adapter, runner, or workflow change is expected.

A migration is not expected because evidence is already a canonical source and existing derivative/packet stores own provenance. If safe sight lineage cannot be represented without additive fields, return the spec to `planned` for an explicit schema amendment rather than hiding lineage in unrelated JSON.

## 13. Binding non-goals

077 does not add:

- a second egress service or direct provider call;
- a new sensitivity level or FAST_DEV exception;
- raw S2/S3/S4 evidence permission;
- a new evidence table, evidence kind, candidate state, parked reason, or promotion authority;
- model-selected evidence or artifact/report-body access;
- general RAG, memory, dossier, review-panel, or alternative-design work;
- provider-family diversification;
- a new confirmation class or override for stale/ineligible content;
- UI/frontend work;
- geometric, mesh/FEM, criteria, or structural-budget changes;
- implementation of Hermes, MCP, or other roadmap slices.

## 14. Readiness sequence

1. Merge this definition while 077 remains `planned` and the Implementation PR cell stays empty.
2. Review it against current 059a/059b packet and derivative schemas, 076 runtime, exact fixtures, and open PR overlap.
3. Resolve the attempt-accounting sequence and whether safe packet metadata can represent sight lineage without migration.
4. Promote to `ready` only in a separate PR after all contract conflicts are resolved.
5. Implement in one bounded PR from the exact promoted head.
6. Move the row to `in_review` and add the implementation PR number when that PR opens.
7. Leave implementation merge authority to the maintainer after deterministic gates and explicit review.

This definition does not activate external evidence use and does not authorize implementation while the registry remains `planned`.
