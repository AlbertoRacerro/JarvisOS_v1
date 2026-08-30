# Post-112 hardening backlog — 127–134

Status: **planning/backlog authority only; no implementation authority**  
Re-derived against exact source `master`: `2a9563fc3016e4c2babff3bca9fc42f54e45902d`  
Date: 2026-08-30

This packet canonizes the post-112 hardening intent for specifications 127–134 after fresh comparison with the exact merged runtime. It deliberately does **not** compress eight independent specification lifecycles into one implementation authority.

After this packet and the corresponding `docs/specs/STATUS.md` rows merge:

- every row remains `planned`;
- every slice still needs its own normal definition/full-spec/readiness authority before implementation, except where the then-current post-112 profile explicitly permits a low-risk planning compression;
- a later implementation PR must still satisfy the normal exact-head gate and registry rules;
- the historical 2026-08-29 drafts are source material only; this repository packet owns the planning deltas that survived fresh runtime inspection.

## Why this packet exists

The 2026-08-29 review identified several structural failure modes that were intentionally held until `112 PROJECT-KNOWLEDGE-CORE-1` merged. Exact `master` now records 112 merged through PR #432 and activates the post-112 controlled-parallel profile.

Fresh inspection also showed that some historical wording is stale or too narrow. Registering the old drafts verbatim would therefore create bad future authority. The reconciliations below are binding inputs to the later per-spec definitions.

## Sequencing intent

The maintainer priority is now hardening-first. At the time of this amendment, PR #434 is the only active JarvisOS PR and must be finished/reconciled before a new front starts. The aborted 113 start left no implementation branch or runtime work; 113 remains technically `ready` but is intentionally held by scheduling policy.

After #434 closes cleanly, the required hardening order is:

`128`
→ advisory/read-only `jarvis-pr-attention` V1.11 integration under a separately accepted JarvisOS boundary
→ `127`
→ `129`, `130`, and `132` when fresh ownership/disjointness proves they can proceed independently
→ `131`
→ `133`
→ `134`

Until 134 is merged, do **not** start 113 implementation and do **not** open new 114–126 planning or implementation fronts. This is a scheduling-priority hold, not a claim that 113 readiness became invalid and not permission to implement any `planned` hardening row.

After 134 merges, the temporary hold lifts. Resume 113 plus 114+ and the other canonical post-112 lanes in controlled parallel according to fresh dependencies, accepted readiness, disjointness and exact-head evidence.

During the initial scheduler transition, no more than two planning fronts may be active concurrently until one clean end-to-end scheduler cycle has been demonstrated under the fresh generic A/B/C/D regime.

## Cross-cutting invariants

1. GitHub exact runtime and deterministic evidence outrank prose.
2. `docs/specs/STATUS.md` remains the sole live registry.
3. `planned` never means READY.
4. No new durable owner/store is introduced unless a later spec proves it is minimum-necessary.
5. AI/model output is advisory. Canonical state, egress, merge and semantic acceptance remain deterministic/human-governed authorities.
6. No new consumer may be added to the legacy modeling direct-write surfaces while 127 remains unimplemented.
7. Exact-head evidence is invalidated after every relevant head mutation.

---

# 127 — CANONICAL-WRITE-PATH-1

## Planning goal

Eliminate ambiguous public canonical-write authority left after 112. Every legacy modeling mutation surface must be inventoried and receive an explicit disposition: delegate to an accepted canonical owner with equivalent CAS/provenance/audit behavior; reject authoritative caller-supplied state; or remain separate only when it demonstrably owns non-canonical evidence rather than Project Basis/model truth.

## Fresh correction to the 2026-08-29 draft

The old draft was too narrow when it named only assumptions/parameters/decisions. Exact runtime still exposes broader mutating modeling routes, including ModelSpec, Requirement and SimulationRun surfaces. Some create paths already reuse Project Knowledge transaction-safe owner primitives, so the simplistic claim that 112 owner functions exist only inside `apply.py` is also false.

A material bypass remains: the legacy Requirement update path performs a direct update rather than the 112 reconciliation/CAS contract. Client request models also still expose multiple status-like fields. 127 must therefore reason from **behavior and authority**, not a static call graph or a hard-coded list copied from the old review.

## Required later-definition constraints

- Inventory every registered public modeling mutation route on the then-current exact head.
- For every caller-supplied lifecycle/status/origin-like field, explicitly classify whether it is legal input. Canonical authoritative values must be server-owned.
- Supplying an unauthorized authoritative lifecycle value must be rejected with a typed, coded error. Silent ignore/normalization is not acceptable evidence of a closed contract.
- Requirement PATCH/direct-update behavior is an explicit target unless fresh runtime has already removed it through separately accepted authority.
- SimulationRun creation must be classified against its evidence/run owner; do not silently absorb run evidence into Project Knowledge canonical authority merely to make the architecture look uniform.
- Retained compatibility routes must be behaviorally equivalent delegates and prove provenance/audit/CAS semantics, not merely call a similarly named helper.
- No opportunistic schema rewrite or historical-row backfill.

## Required proof shape

Use behavioral HTTP/integration tests over the registered mutating surface to prove that no public request can directly manufacture authoritative canonical state. Static call-graph assertions may supplement this but cannot be the acceptance proof.

---

# 128 — ARCHITECTURE-ENFORCEMENT-GATE-1

## Planning goal

Turn two important architectural conventions into deterministic CI failures for **new** violations: raw database ownership outside the accepted database chokepoint and direct network/provider ownership outside explicitly designated egress/local-AI boundaries.

## Required later-definition constraints

- Use AST/semantic inspection rather than fragile regex for Python imports/calls.
- Cover aliased imports, `from ... import ...` and relevant attribute-call forms.
- Keep an explicit allowlist small and machine-readable.
- Every designed-boundary allowlist entry requires a justification.
- Every debt allowlist entry additionally requires an owning removal/fix spec; ownerless debt fails the gate.
- The currently observed AI side channels remain **temporary debt owned by 129**, not permanent legitimate provider boundaries.
- Test/fixture exceptions must be narrowly defined; tests must not accidentally become a way to perform real network calls.
- The gate must fail with file/line/actionable evidence when a synthetic violating fixture is introduced.

128 is the first intended hardening slice because JarvisOS should mechanically enforce ownership boundaries before integrating another review/evidence tool.

---

# Candidate integration after 128 — jarvis-pr-attention V1.11

Exact upstream candidate inspected for this planning packet:

- repository: `AlbertoRacerro/jarvis-pr-attention`;
- V1.11 release PR: #16;
- inspected head: `c544e2885a69173c58feb2355bb53e8866e627eb`;
- direct license: MIT.

The inspected V1.11 cycle is suitable only as a read-only exact-head **evidence helper**. Any JarvisOS integration must remain stateless with respect to JarvisOS authority and must never become:

- semantic acceptance authority;
- approval/review-decision authority;
- comment/thread-resolution authority;
- merge authority;
- queue/work-state authority;
- canonical persistence/source of truth.

Its `merge_candidate` result is advisory evidence, not permission to merge. Caller-supplied accepted-head claims likewise cannot replace JarvisOS-owned exact-head/semantic acceptance.

No runtime integration is authorized by this packet. A later accepted integration boundary may wire the tool only after 128 has established the relevant architecture guard.

---

# 129 — EGRESS-SIDE-CHANNEL-CLOSURE-1

Depends on merged `059b`, which remains the egress policy/autopilot authority owner.

## Planning goal

Ensure every real external-provider dispatch reachable through production HTTP surfaces uses the normal JarvisOS egress/execution spine and its persisted policy, sanitizer, reservation, attempt and usage evidence, rather than parallel ad-hoc authorization logic.

## Fresh evidence

Exact runtime still contains dedicated provider-smoke and supervisor-public-test paths that construct/call provider adapters outside the normal `run_ai_task` spine. Local privacy or budget checks do not make a parallel egress owner acceptable.

## Required later-definition constraints

- Route real network dispatch through the accepted 059b/normal execution spine, or remove/disable the real network authority entirely.
- A non-default diagnostic flag cannot become a second weaker authorization model.
- No duplicate budget ledger, privacy policy, sanitizer or confirmation semantics.
- Provider mocks/synthetic diagnostics remain deterministic and network-free in CI.
- Every real dispatch must leave the canonical attempt/cost/egress evidence required by current owners.

---

# 130 — RUNNER-DETERMINISM-HARDENING-1

Depends on 056.

## Planning goal

Close cross-process Python hash-order nondeterminism in the runner and prove the resulting environment contract.

## Fresh correction to the 2026-08-29 draft

The repository already runs `backend/tests/bluecad/test_manifest_determinism_canary.py` in the Linux CI job. A later 130 implementation must **not** add a duplicate canary/job merely because the historical draft asked for one.

The remaining failure mode is that runner subprocess startup does not explicitly pin a deterministic `PYTHONHASHSEED` contract.

## Required later-definition constraints

- Explicitly set the child-process hash seed in every relevant Python runner environment without inheriting an uncontrolled parent value.
- Add a true cross-process repeatability test.
- Add a negative/meta-test that intentionally launches equivalent fixtures under divergent hash seeds and proves the fixture would expose order leakage when the runner contract is absent.
- Keep the existing Linux full-manifest canary as incumbent evidence unless fresh runtime has legitimately replaced it.
- Do not weaken isolation/environment-scrubbing controls to gain determinism.

---

# 131 — ERROR-CONTRACT-UNIFICATION-1

## Planning goal

Establish one shared workspace-existence guard plus a stable typed/coded domain-error → HTTP translation contract, then migrate only a bounded first slice.

## Fresh correction to the 2026-08-29 draft

Historical counts such as “nine guards” or a fixed number of exception classes are not planning authority. They must be re-inventoried on the exact implementation base.

## Required later-definition constraints

- First implementation slice establishes the common contract and a small representative migration only.
- Do not turn 131 into a codebase-wide taxonomy/refactor sweep.
- Preserve externally pinned status/error behavior unless the definition explicitly identifies an existing untyped leak to correct.
- Domain errors carry stable machine-readable codes.
- Once central translation owns an error type, routes should not re-wrap it ad hoc.
- A fresh exact-head inventory determines the bounded migration set and follow-up debt.

---

# 132 — TYPECHECK-RATCHET-1

## Planning goal

Make existing mypy configuration enforce non-regression without demanding an all-at-once typing cleanup.

## Fresh correction to the 2026-08-29 draft

Historical aggregate numbers (`276 errors / 59 files`) are review-time observations, not current baseline authority. The baseline must be regenerated against the exact implementation base.

## Required later-definition constraints

- Commit the exact source SHA from which the baseline was generated.
- Gate authority is per-file/per-module: each baseline count may stay equal or decrease; aggregate total is informational only.
- New files/modules start at zero unless the accepted definition proves a narrower rule is necessary.
- A PR may not hide regression by moving errors between files.
- Baseline increases fail unless a later explicit authority changes the policy; ordinary implementation may only maintain/decrease debt.
- Comparator and baseline generation are deterministic/offline.

---

# 133 — FRONTEND-CONTRACT-CODEGEN-1

## Planning goal

Replace selected drift-prone hand-maintained frontend API type copies with deterministic types generated from the backend contract and make contract drift fail CI.

## Fresh correction to the 2026-08-29 draft

Sampled drift counts and named mismatches from the old review must be revalidated against the exact implementation base; they are not permanent acceptance facts.

## Required later-definition constraints

- Freshly inventory which endpoint/type is the smallest high-value first migration.
- Export schema deterministically from the app/contract source without network access in CI.
- Pin generator tooling/version and produce byte-stable output.
- A backend contract change without regenerated frontend types must yield a deterministic diff/failure.
- Migrate one bounded real surface first; record remaining handwritten debt instead of rewriting the entire client.
- Code generation does not add runtime validation or change backend semantics.

---

# 134 — MERGE-AUTHORITY-HARDENING-1

Depends on 004 and 079 and deliberately revisits their historical repository-settings non-goals.

## Planning goal

Make JarvisOS merge governance mechanically inspectable rather than relying on invisible repository settings, while avoiding a bootstrap deadlock when the automation credential cannot yet read branch/ruleset configuration.

## Fresh evidence

At this planning base the public branch object reports `master` as unprotected with no required status checks, and the repository rulesets collection is empty. A direct protection-detail read through the current connector is not accessible to the integration, which itself proves that permissions must be treated as an explicit bootstrap state rather than guessed.

## Required later-definition constraints

- Separate **declaration**, **verification**, and **enforcement** phases.
- Land a machine-readable desired protection/check declaration first.
- A dedicated verification workflow/tool must distinguish mismatch from unreadable/permission-missing state.
- While bootstrap credentials cannot read the settings, ordinary main CI must not become permanently unsatisfiable. Report explicit non-blocking `UNKNOWN / permission missing` rather than silently PASS.
- After an operator/credential route has the minimum read permission and one green verification proves the live configuration, only then may the verification become required/blocking and settings be tightened.
- Never use `continue-on-error` or equivalent to reinterpret unreadable settings as protected.
- Explicitly classify deterministic code checks versus advisory AI reviews.
- No auto-merge is introduced.
- Any repository-settings mutation remains exact-target, reviewable and reversible where GitHub permits it.

---

## Promotion rule

After this planning PR closes cleanly, the next per-spec definition is **128**. No 113 implementation and no 114–126 planning/implementation front may start before 134 is merged. 128 must complete its normal lifecycle first; then a separately accepted `jarvis-pr-attention` integration slice; then the remaining hardening order in this packet through 134.

After 134 merges, resume 113 plus 114+ and the other canonical post-112 lanes in controlled parallel under the then-current profile and registry.

No implementation agent may act directly from this file.