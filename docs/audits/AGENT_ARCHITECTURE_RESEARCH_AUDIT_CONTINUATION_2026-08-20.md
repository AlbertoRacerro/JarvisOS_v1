# Agent Architecture Research Audit — Continuation — 2026-08-20

Status: research/intake only; **not implementation authority**.  
Focus: authorization, information-flow safety, memory boundaries and computer-use risk.

---

## 1. Progent — programmable privilege control

Paper: https://arxiv.org/abs/2504.11703

Progent treats least privilege as an external deterministic enforcement problem rather than trusting the agent to self-police. Policies are expressed in a DSL over tool calls and can specify fallbacks when a call is denied.

### Jarvis implication

A future Jarvis policy engine should be **outside** generic agent runtimes and capable of constraining a tool call without modifying each runtime's internals.

This supports:

`runtime proposal -> normalized action -> Jarvis policy evaluator -> allow/deny/ask/transform -> executor`

Policy generation may be assisted by an LLM, but policy **enforcement** must remain deterministic.

**Grade: S- architecture/security reference.**

---

## 2. Tracked capabilities — information flow stronger than path allowlists

Paper: "Securing Agents With Tracked Capabilities", ACM CAIS 2026, DOI 10.1145/3786335.3813127.

The paper uses object capabilities tracked in Scala 3 types. A central result is that access control over individual tool calls is insufficient to prevent information leakage: an agent can legally read a secret and later legally call a network tool unless the system also tracks how capabilities/data may flow.

### Jarvis implication

This is highly relevant to the combination of Rizzo PII + egress policy + tool authority.

Jarvis eventually needs to distinguish at least:

- permission to **read** sensitive data;
- permission to **derive/process** it locally;
- permission to **persist** derived content;
- permission to **send** it to a specific egress/provider class.

A single boolean `can_read_file` or `can_use_network` cannot encode this.

The exact Scala/capture-checking implementation is not a Jarvis requirement, but the security property is valuable: **capability possession and information-flow authority must be separable from model intent**.

**Grade: S research direction.**

---

## 3. Least-privilege policy inference is not safe to delegate entirely to models

Paper: https://arxiv.org/abs/2605.14859 — "Do Coding Agents Understand Least-Privilege Authorization?"

AuthBench evaluates file-level read/write/execute policy inference. The reported result is important: frontier models can simultaneously omit permissions needed for task completion and grant unnecessary sensitive permissions; more reasoning does not reliably fix the mismatch.

### Jarvis implication

Do not ask an LLM once, "what permissions do you need?", and turn the answer into authority.

A safer future admission process is:

1. propose a coverage-oriented capability request;
2. resolve concrete execution dependencies;
3. independently audit each requested grant for grounding/sensitivity;
4. attenuate to the narrowest sufficient capability;
5. enforce runtime budgets/expiry;
6. record used vs unused grants after execution.

Unused grants become evidence for future tightening, not proof that the original model understood least privilege.

**Grade: S- authorization design evidence.**

---

## 4. Verifiably safe tool use

Paper: ICSE-NIER 2026, "Towards Verifiably Safe Tool Use for LLM Agents", DOI 10.1145/3786582.3786839.

The research motivation matches the audit's recurring failure mode: model-based safeguards improve reliability but do not provide system-level safety guarantees for destructive or privacy-sensitive tool interactions.

### Jarvis implication

Safety-critical Jarvis actions need machine-checkable pre/postconditions where possible. Example classes:

- target object/version exists and is still current;
- proposed path is inside an allowed root;
- no secret-class data crosses an egress boundary;
- mutation delta is bounded;
- approval hash matches exact normalized action;
- post-action state satisfies expected invariant.

**Grade: A+ research support for deterministic contracts.**

---

## 5. Computer-using-agent threat taxonomy

Paper: ACL 2026, "JARVIS or Ultron? A Survey on the Safety and Security Threats of Computer-Using Agents", https://aclanthology.org/2026.acl-long.2106/

This is a survey rather than a component. Its value is as a checklist source for desktop/browser/UI threat modeling.

### Jarvis implication

Before Jarvis computer-use becomes broadly autonomous, the strategy document should map threats and controls across:

- model/reasoning failure;
- multimodal perception ambiguity;
- indirect prompt injection in UI/web content;
- action mis-targeting;
- credential/session theft;
- unsafe application composition;
- external side effects;
- audit/recovery failure.

Use the survey to build an acceptance/threat matrix, not to derive code architecture directly.

**Grade: A taxonomy reference.**

---

## 6. MIRIX — useful memory taxonomy, unsafe as canonical authority if copied literally

Paper: https://arxiv.org/abs/2507.07957

MIRIX separates six memory categories: Core, Episodic, Semantic, Procedural, Resource and Knowledge Vault, coordinated by multiple agents.

### Jarvis interpretation

The taxonomy is useful, especially the distinction between procedural/resource/personal memory, but Jarvis needs an additional axis absent from many memory papers:

**authority class**.

Every memory/object should be classifiable as one of:

- canonical/authoritative;
- source evidence;
- derived/indexed;
- episodic/operational;
- personal/preference;
- transient working state.

Two objects may both be "semantic memory" while having completely different write/retention authority.

**Grade: A- taxonomy reference.**

---

## 7. A-MEM — dynamic linking belongs in derived memory only

Paper: https://arxiv.org/abs/2502.12110

A-MEM dynamically links notes and can revise contextual representations of historical memories as new information arrives.

### Jarvis implication

This is attractive for retrieval, but unacceptable for canonical engineering evidence if the mutation is opaque/model-driven.

Use an architecture such as:

`immutable source/canonical record -> regenerable semantic note/link graph`

The graph can evolve; the underlying evidence and canonical event history do not.

**Grade: A- derived-memory candidate, D as canonical-state model.**

---

## 8. Security synthesis: three independent control planes

The audit now suggests that "agent permissions" should be decomposed into at least three planes.

### Plane A — capability authority

What can this actor do to which resource?

Examples: read object, edit object, run solver, invoke network provider, spawn worker.

### Plane B — information-flow / egress authority

What sensitivity classes may flow into which destination?

Examples: local-only secret, pseudonymizable PII, public engineering data, provider-approved context.

### Plane C — state-commit authority

Which actor may turn a proposal/result into canonical Jarvis state?

Generic LLM workers normally get **none**; they submit proposals/evidence to the deterministic authority layer.

Keeping these planes separate prevents a common escalation:

`can read + can call network` accidentally becoming `can exfiltrate`, or `can generate output` becoming `can overwrite canonical truth`.

---

## 9. Candidate action envelope

A later strategic spec should consider a normalized action object with fields conceptually equivalent to:

- `action_id`;
- actor/runtime/session identity;
- capability requested;
- target resource/object + version;
- normalized typed arguments;
- sensitivity/egress classification;
- expected effect and postcondition;
- budget/lease/expiry;
- approval identity/hash if required;
- provenance links;
- rollback/idempotency metadata.

This action object, not the model's natural-language summary, should be what policy and approval bind to.

---

## 10. Strategic consequence

The future backend puzzle should not be organized by vendor/project names ("implement Serena", "implement Unsloth", etc.). It should be organized by **architectural contracts and invariants**, with candidate upstreams competing inside each slot.

Example slots:

1. Authority/Event Kernel
2. AgentRuntime
3. Tool/Capability Gateway
4. Execution/Sandbox
5. Model Runtime/Provider
6. Code Intelligence
7. Canonical Memory/Evidence
8. Derived Memory/Index
9. Egress/Privacy
10. Observability/Evaluation
11. Training/Specialization
12. Desktop/Frontend IPC

Only after the current product queue and frontend visual-identity phase are complete should these slots become an implementation queue.
