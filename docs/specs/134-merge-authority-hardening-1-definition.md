# 134 — MERGE-AUTHORITY-HARDENING-1 — definition

Status: definition-only planning authority; live implementation authority remains `docs/specs/STATUS.md`.

## Purpose

Make the repository's merge-governance assumptions mechanically inspectable and eventually enforceable without pretending that unreadable GitHub settings are known. The slice must establish a permission-safe declaration → verification → enforcement bootstrap for `master`, preserve exact-head/manual merge authority, and keep deferred auto-merge forbidden.

This definition does **not** authorize changing GitHub protection settings, rulesets, workflows, merge methods, repository permissions, or runtime/product code. `134` remains `planned` until a later full specification and separate readiness decision are accepted.

## Exact-master derivation

Derived from exact master `4191000b770f5b94f9ad3a29f2cd2a43306562e2` after `133 FRONTEND-CONTRACT-CODEGEN-1` implementation #490 and post-merge registry reconciliation #491.

Fresh live GitHub evidence at derivation time:

- repository rulesets are readable through the current integration and return an empty list (`[]`);
- the classic `master` branch-protection endpoint returns HTTP 403 `Resource not accessible by integration`;
- therefore the current integration can prove **no visible repository ruleset**, but it cannot prove whether classic branch protection is absent, present, or configured correctly;
- existing JarvisOS governance already requires one ChatGPT merge owner, exact-current-head checks, terminal required CI/review evidence, explicit merge, post-merge registry reconciliation, and no deferred auto-merge;
- `004` and `079` are historical governance/development-loop dependencies, but neither is sufficient evidence that current GitHub-side merge protection matches current repository policy.

The central failure mode is therefore **false certainty**: treating an unreadable GitHub control plane as either safely protected or definitely unprotected.

## Authority model to freeze

134 must preserve these separations:

1. **Repository declaration authority:** version-controlled JarvisOS policy may declare the intended merge invariants and required checks for `master`.
2. **GitHub observation authority:** a verifier may report only what the authenticated integration can actually read from GitHub APIs.
3. **GitHub enforcement authority:** changing branch protection/rulesets is a distinct privileged action and must never be inferred from a declaration or verifier result.
4. **Merge authority:** ChatGPT remains the explicit exact-head merge owner under `AGENTS.md`; no workflow/model/verifier gains merge authority.
5. **CI/review authority:** green checks and advisory model evidence are inputs, never self-executing approval or merge permission.

No implementation may collapse declaration, observation, and enforcement into one opaque boolean.

## Required state vocabulary

The later full spec must define a deterministic observation result at least capable of distinguishing:

- `VERIFIED`: live settings were readable and satisfy the declared minimum;
- `MISMATCH`: live settings were readable and conflict with the declaration;
- `UNKNOWN`: live settings required for the decision were not readable with current permissions or the API result is otherwise insufficient;
- `ERROR`: malformed declaration, unsupported response shape, transport/API failure, or verifier defect prevents a trustworthy decision.

`UNKNOWN` is not equivalent to PASS and not equivalent to FAIL. During the bootstrap phase it must be explicit and non-deceptive. Tightening required protection is authorized only after minimum read permission exists and the verifier can produce a green `VERIFIED` result against the exact declaration being enforced.

## Failure modes the full spec must close

1. **403-as-absence:** interpreting inaccessible classic branch protection as disabled.
2. **Empty-ruleset overclaim:** treating `rulesets=[]` as proof that no other protection mechanism exists.
3. **Declaration-as-enforcement:** checking a committed policy file without comparing live GitHub state.
4. **Permission-dependent flapping:** CI becomes red solely because a low-privilege token cannot read settings that are intentionally protected.
5. **Fail-open enforcement:** a verifier error is silently interpreted as compliant.
6. **Self-authorizing workflow:** a workflow both decides policy and changes protection/merges without explicit authority separation.
7. **Stale policy evidence:** verification result is not bound to exact repository/ref/declaration revision.
8. **Check-name drift:** declared required checks no longer match current workflow/check names but governance claims protection.
9. **Unreviewable protection mutation:** branch/ruleset changes happen outside a bounded, inspectable maintainer-controlled path.
10. **Auto-merge creep:** GitHub deferred auto-merge is enabled as a convenience despite canonical prohibition.
11. **Admin-bypass ambiguity:** policy claims mandatory gates while configured bypass/admin behavior undermines them.
12. **Merge-method drift:** repository settings permit an unreviewed merge mode that breaks expected history/exact-head assumptions.
13. **Fork/PR secret escalation:** verification or enforcement uses privileged credentials on untrusted PR-controlled code.
14. **False CI authority:** a green verifier check is treated as permission to merge rather than evidence consumed by the merge owner.

## Full-spec questions that must be answered from fresh evidence

The next lifecycle stage must inventory and freeze, at minimum:

- the exact current GitHub APIs readable by the integration for repository rulesets, classic branch protection, repository merge settings, required-status-check configuration and bypass actors;
- current workflow/check names that are candidates for the declared minimum merge gate;
- whether a repository-local declaration should describe intended controls only, or also the minimum check-name set and merge-method constraints;
- the smallest deterministic verifier implementation and its permission model;
- how `UNKNOWN` behaves in ordinary PR CI before stronger read permission exists;
- what exact evidence is required before any enforcement mutation is permitted;
- how enforcement remains a separate explicit maintainer action and how rollback is represented;
- how trusted-code execution is guaranteed for any job that holds settings-read or settings-write credentials;
- how exact-head/manual merge and the no-auto-merge rule are preserved.

## Lifecycle requirement

134 does **not** qualify for low-risk planning compression. It concerns repository merge authority and may lead to hard-to-reverse GitHub control-plane changes. Preserve separate stages:

`definition -> full specification -> readiness -> implementation -> exact-head gates/review -> merge -> registry reconciliation`.

The full spec may authorize a declaration/verifier implementation before enforcement only if the phases remain mechanically separable and no settings mutation occurs until its explicit readiness conditions are met.

## Expected implementation shape — non-authoritative until full spec

The smallest plausible shape to evaluate is:

- one version-controlled merge-authority declaration under `.github/` or `docs/`;
- one stdlib-only verifier under `scripts/` that can self-test response classification and compare readable live state to the declaration;
- one permission-safe CI/reporting path that exposes `VERIFIED/MISMATCH/UNKNOWN/ERROR` without secrets on untrusted code;
- an explicit later enforcement step/action only if live read verification is proven and canonical readiness authorizes it.

This is an inventory hypothesis, not implementation authority. The full spec must delete or narrow any component that fresh evidence shows unnecessary.

## Non-goals

- no auto-merge;
- no autonomous workflow/model merge authority;
- no product/runtime/provider/schema/frontend change;
- no new external model review requirement;
- no blanket GitHub administration framework;
- no attempt to bypass a 403 using broader credentials without maintainer-controlled permission setup;
- no claim that unreadable protection is absent;
- no mandatory branch/ruleset mutation in the definition stage;
- no 113–126 implementation or planning authority change in this file.

## Definition acceptance

This definition is complete when it freezes the actual observed uncertainty, the declaration/verification/enforcement authority split, the four-state observation vocabulary, the failure modes, and the requirement for a separate full specification/readiness before any implementation or GitHub settings mutation.

### Test del minimo necessario

Criterio di accettazione della spec: make merge governance mechanically verifiable without converting permission gaps into false claims or granting automation hidden merge/settings authority.

Questo lavoro serve a soddisfarlo? sì.

Il criterio è raggiungibile senza questa separate definition? no — fresh GitHub evidence already contains an asymmetric visibility state (`rulesets=[]` while classic protection is 403), so implementation details cannot safely be chosen from the backlog sentence alone.
