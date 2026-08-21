# Core Software Ecosystem Audit — Continuation 6 — 2026-08-20

Status: audit/intake only; **not implementation authority**.

This continuation records deeper code evidence discovered after the initial Rizzo/Unsloth/DwarfStar pass and a negative/low-value sibling result.

---

## 1. Unsloth Start — useful architecture, different license boundary

Source file inspected: `unsloth_cli/commands/start.py` in `unslothai/unsloth`.

### Critical license finding

The file is explicitly marked:

`SPDX-License-Identifier: AGPL-3.0-only`

and points to `studio/LICENSE.AGPL-3.0`.

Therefore the `unsloth start` agent-integration implementation must **not** be treated as Apache-2.0 merely because the repository root metadata reports Apache-2.0.

### Concrete reusable design patterns

Even when code reuse is not appropriate, the implementation is a strong reference for an agent/model bridge.

#### A. Agent-specific compatibility overlays

The command adapts local Unsloth serving to multiple coding agents rather than forcing one common client. It carries separate profiles/env/config logic for Codex, Claude, Hermes, Pi/OpenCode and related clients.

Jarvis should similarly prefer one normalized internal model-runtime contract with thin compatibility adapters rather than forcing every external agent to understand Jarvis internals.

#### B. Remove conflicting provider credentials from child environment

The source explicitly unsets original provider credential environment variables for some launched clients so the child does not silently bypass the intended local route.

General Jarvis principle:

> When launching a constrained worker, inherited credentials are capabilities and must be explicitly minimized.

Do not pass the parent process environment wholesale to workers.

#### C. Pin remote installer/upstream code by exact commit

The Hermes installer path is pinned to a full commit because executing a moving upstream branch with the user's privileges would allow silent replacement.

Jarvis installer/plugin/skill admission should record:

- source repository;
- exact commit/version;
- hash/signature where available;
- license;
- granted capabilities;
- update/revocation path.

#### D. Session overlays and ephemeral homes

Unsloth relocates or overlays agent state into session-specific directories and distinguishes ephemeral from persistent sessions. This reduces pollution/collision with a user's normal global client configuration.

Jarvis should expose worker/session state location as a first-class execution-manifest field.

#### E. Read-only subagent is a distinct contract

The Claude subagent integration has a separate read-only planning/research role instead of merely asking an ordinary write-capable agent "please do not edit".

This is a strong pattern for Jarvis:

`research capability != implementation capability`.

#### F. Local-runtime timing needs client adaptation

The source raises Codex's stream-idle timeout because a slow local model can legitimately spend minutes in prompt processing before emitting bytes. Otherwise the client reconnects, loses prefix/KV reuse and can enter a loop that never finishes.

This illustrates why Jarvis runtime adapters need explicit timing/capability metadata rather than assuming cloud-provider latency semantics.

#### G. Dangerous bypass switches remain dangerous

Unsloth normalizes several agents' "skip permissions / bypass approvals / yolo" controls. This is convenient UX, but from Jarvis's perspective it is also a warning: downstream runtimes expose authority escape hatches that a Jarvis-managed launch must either block, surface explicitly, or constrain through an outer sandbox/policy layer.

### Disposition

**Reference value: S-. Direct reuse of this file: blocked/limited by AGPL boundary unless deliberately compatible.**

Reimplement only a thin compatibility adapter if required; prefer invoking stable upstream interfaces where possible.

---

## 2. RizzoClaw — low unique architecture value, useful negative memory reference

Source: https://github.com/Rizzo-AI-Academy/RizzoClaw

The repository describes itself as a workshop Rizzo version of OpenClaw. Its tree includes `.agents`, `BRAIN.md`, `memories/`, `CLAUDE.md`, Docker and a small Python package.

The public `BRAIN.md` demonstrates a simple plaintext agent-memory pattern: user/profile/session context is materialized directly as Markdown in the project tree.

### Jarvis lesson

This is **not** a stronger memory architecture than the candidates already audited. The useful lesson is negative:

- personal memory should not be conflated with source code;
- sensitivity/retention metadata should not be implicit in a filename;
- repository publication and memory persistence need separate policy;
- canonical project evidence and personal profile memory need distinct stores/authorities.

### Disposition

**Grade: C-/SUPERSEDED as architecture reference.**

Study original OpenClaw/nanoclaw or stronger memory frameworks instead of importing RizzoClaw patterns.

---

## 3. Rizzo-Mesh — captured but insufficient evidence for architectural promotion

Source: https://github.com/Rizzo-AI-Academy/Rizzo-Mesh

The public README currently describes a fine-tuned LLM that generates 3D objects but exposes too little architectural evidence by itself to justify promotion over the already audited CAD/geometry stack and training candidates.

### Disposition

**CAPTURED / PARKED.**

If a future BLUECAD generative-geometry phase needs model-generated geometry, re-audit the actual training data, representation, output contract and verifier. Do not treat a model that emits 3D artifacts as a replacement for canonical BLUECAD geometry semantics or deterministic geometry kernels.

---

## 4. antirez engineering notes — tool design and QA as first-class interfaces

Primary sources:

- https://antirez.com/news/166 — alternatives for agent EDIT;
- https://antirez.com/news/168 — AI-driven release QA;
- https://antirez.com/news/169 — control the ideas, not the code;
- DwarfStar `AGENT.md` and `QA_BEFORE_RELEASES.md`.

These are practitioner evidence rather than peer-reviewed research, but they are unusually concrete and match source-level DwarfStar behavior.

### A. Compare-and-set edit semantics with compact identity

The EDIT discussion starts from a real concurrency/staleness problem: raw line-number editing is unsafe because the user/branch/file can change and the model can hallucinate old content. Traditional `old -> new` CAS is safer but token-expensive. The proposed line/tag or file-checksum designs preserve a version check with lower context cost.

Jarvis code/file mutations should therefore bind to **content/version identity**, not only path + line number.

Potential contract:

`Edit(path, base_version/hash/tag, range/symbol, replacement)`

and reject stale edits before mutation.

Serena/LSP symbolic edits can provide a higher-level version of the same invariant.

### B. AI QA should specialize from the diff

The QA article describes an agent that starts by reading changes since the last release, then expands a maintained manual/operational checklist with regression hypotheses specific to those changes.

This should complement, not replace, deterministic CI:

`deterministic gates + diff-aware adversarial QA + hardware/manual matrices`.

For Jarvis, a future release/readiness system should preserve historically fragile scenarios and let an independent agent derive additional tests from the exact diff.

### C. Automatic programming raises the value of verification

The DwarfStar workflow accepts that code can be produced quickly, but correctness is established by comparison, QA, golden vectors, real hardware and explicit regression bands. This maps directly to Jarvis's desired builder/reviewer separation.

### D. Minimize complexity and dependency cost, but benchmark instead of romanticizing rewrites

antirez repeatedly argues for small tailored software and warns against dependency chains. The audit should retain this as a counterweight to indiscriminate upstream adoption.

The correct Jarvis rule is not "always reuse" or "always write our own":

> Compare total complexity, authority fit, licensing, update risk, testability and runtime footprint. Keep the smallest solution that satisfies the contract and qualification gates.

### Disposition

**Grade: S- as engineering-process reference.**

---

## 5. Additional audit rules derived from this pass

### Worker launch manifest must include environment authority

Record which credentials/environment variables are passed, removed or replaced. Environment inheritance is part of capability control.

### Read-only must be structural

A read-only researcher should receive read-only tools/filesystem/capabilities, not a write-capable runtime with a natural-language instruction.

### Runtime timeouts are capability metadata

Local vs cloud runtimes can have radically different prefill/first-token behavior. Retry logic must not destroy resumability/KV reuse or duplicate side effects.

### File edits require stale-state protection

Every mutating code/file tool should have an exact base identity and deterministic stale rejection, whether implemented with hashes, tags, object versions or semantic edit anchors.

---

## 6. Follow-up

The next high-value work is no longer to enumerate random agent repositories indefinitely. The audit should continue selectively until each architectural slot has at least two or three serious candidates and known failure modes. Then produce the separate strategic disposition document (`KEEP_JARVIS / REPLACE / WRAP / HYBRID / DELETE / PARK`) before deriving the future backend puzzle queue.

The current product queue and frontend visual-identity phase remain untouched by this research.
