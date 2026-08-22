# 100b — CODEBASE-LEAN-CLEANUP-1

Definition status: **boundary defined now; candidate set must be freshly re-derived from merged 100a evidence before readiness**  
Depends on runtime authority: 100a

## 1. Purpose

Execute one bounded, high-confidence cleanup batch derived from the exact 100a codebase audit before 101 begins.

The goal is to reduce active semantic surface while preserving desired product behavior, security/authority boundaries, scientific evidence and future capability reachability.

This is not permission for a repository-wide aesthetic rewrite. 100b removes or collapses only what 100a has demonstrated to be unwanted, redundant, replaced or unnecessarily indirect with high confidence.

## 2. Why the exact candidate list is intentionally deferred

This definition is written before 100a runs and therefore must **not** guess which concrete modules are safe to delete.

After 100a merges, 100b must be freshly re-derived from then-current `master` and its audit artifact. The readiness record must freeze the exact candidate list, touched boundaries, preservation obligations and expected reduction.

If 100a produces no high-ROI behavior-preserving cleanup outside work already owned by 101 or 103–105, 100b should be cancelled rather than manufacturing refactor work to justify its existence.

## 3. Governing rule

> **Absence of a current consumer is not deletion authority.**

A desired backend capability with no current frontend/client consumer is a `WIRE`/`DEFER` finding, not dead code.

100b may not delete a capability merely because it is unreachable from the current UI. Product intent and the full 100a deletion gate must already be resolved.

## 4. Authorized disposition classes

100b may execute only high-confidence findings classified by 100a as:

- `SIMPLIFY`;
- `MERGE`;
- `INLINE`;
- `DELETE`;
- `STRANGLE` only when the replacement is already present/reachable and migration is bounded inside 100b;
- `REFERENCE_ONLY` only when the runtime removal is high-confidence and the required preservation destination is included in the same bounded plan.

`DELETE_CANDIDATE`, `PROFILE` and `UNKNOWN` are not implementation authority.

`WIRE` and `DEFER` are explicitly protected from cleanup. They must be preserved and mapped to the relevant existing/future product slice.

`REPLACE_UPSTREAM` belongs in 100b only if the replacement is already selected and outside a later dedicated authority. Process-solver replacement remains owned by 103/104.

## 5. Scope boundary against later specs

100b is intentionally placed before 101, but it must not steal the semantic work already reserved for later architecture slices.

### 5.1 101 remains owner of canonical-write semantics

100b may remove provably dead wrappers or duplicate code around state APIs, but it may not redesign lifecycle/write authority, Parameter status semantics, promotion rules or canonical-state behavior. Those belong to 101.

### 5.2 103/104 remain owners of process-stack selection and strangling

100b may classify or preserve evidence about process code, but it must not select a process upstream or delete the custom process kernel in advance of 103/104 unless the exact code is independently proven unrelated/dead and the later bake-off does not need it as incumbent evidence.

### 5.3 105 remains owner of engineering-domain structural cleanup

The obsolete `app/modules/engineering` boundary and the dependency/provenance `flowsheet` naming/domain collision remain 105 work unless 100a proves an entirely behavior-free deletion that 105 no longer needs. Prefer routing those findings to 105 rather than creating overlapping authority.

### 5.4 Feature wiring remains separate

If 100a discovers a useful backend capability that should appear in the frontend, 100b does not implement the feature simply because the code is nearby. Record or reconcile the owning product spec instead.

## 6. Lean implementation rules

For each accepted cleanup packet:

1. preserve externally meaningful behavior and current accepted invariants;
2. remove compatibility code when no real supported consumer exists rather than replacing it with a new compatibility layer;
3. prefer deleting an unnecessary abstraction over replacing it with a differently named abstraction;
4. prefer one direct authoritative implementation over multiple facades/repositories/helpers carrying the same semantics;
5. preserve boundaries that enforce actual authority, egress, security, transactions, provenance, scientific validity or replaceable solver/tool contracts;
6. do not add infrastructure to manage cleanup complexity unless the cleanup cannot be safely executed without it;
7. measure active-source reduction before and after, but do not distort code to maximize the number;
8. stop when remaining opportunities cross into low-confidence or low-ROI territory.

## 7. No code golf / no pedagogical ceremony

The target is **minimum semantic surface**, not minimum characters.

Do not:

- compress logic into cryptic expressions;
- remove types or invariants that materially improve correctness;
- merge unrelated authority boundaries merely to reduce files;
- rewrite direct readable code into clever metaprogramming;
- retain factory/facade/manager layers solely because they are a familiar enterprise pattern;
- add explanatory classes/wrappers solely to make architecture easier for a hypothetical junior developer.

JarvisOS is expected to be maintained and reviewed heavily by AI agents. Code should therefore expose the smallest number of real concepts and paths while keeping consequential invariants explicit.

## 8. Testing and behavior preservation

The fresh 100b spec/readiness must identify the behavior proof for every cleanup family.

At minimum:

- full backend tests and Ruff remain green;
- frontend build/tests run if frontend code is touched;
- workflow/security checkers run if scripts/workflows are touched;
- public/runtime API behavior affected by a simplification has focused regression coverage;
- deleted code must not leave stale imports, routes, configuration, docs claims or tests that refer to removed behavior;
- tests that protect an accepted behavior contract are migrated with the implementation rather than deleted to make cleanup pass.

A failing test is not evidence that the test is obsolete. Its owning behavior must be traced first.

## 9. Runtime performance

100b is primarily a maintenance/semantic-surface optimization.

Runtime-performance changes are allowed only for hotspots measured by 100a when the fix is behavior-preserving and remains inside the bounded cleanup candidate set. A substantial algorithm, storage, language or native-extension change requires a separate specification.

Do not infer that fewer Python/TypeScript lines produce lower wall time.

## 10. Required before/after evidence

The implementation PR must record:

- exact base/head SHA;
- candidate list frozen by readiness;
- active first-party source LOC before and after for touched areas;
- file/module count before and after where meaningful;
- deleted/merged/inline boundaries;
- behavior proof used for each cleanup family;
- any `WIRE`/`DEFER` capability discovered near touched code and explicitly preserved;
- findings deliberately routed to 101, 103, 104, 105 or another future spec;
- why the implementation stopped where it did.

Net source reduction is expected for a cleanup slice. If implementation grows active runtime code overall, the PR must demonstrate a concrete semantic-surface reduction that outweighs LOC growth or the candidate should be removed from 100b.

## 11. Acceptance criteria

The fresh post-100a implementation spec/readiness must refine these criteria without weakening them:

1. Every concrete mutation maps to a high-confidence 100a disposition authorized by section 4.
2. No code is deleted solely because it lacks a current consumer.
3. Every deleted capability satisfies the complete 100a deletion gate on the exact implementation base.
4. Desired-but-unwired backend/API capability is preserved and remains classified `WIRE`/`DEFER` or assigned to a product slice.
5. No canonical-state semantic redesign from 101 is pre-implemented.
6. No process-upstream selection/strangling from 103/104 is pre-implemented.
7. No substantial engineering-domain redesign from 105 is smuggled into this slice.
8. Active semantic surface decreases materially enough to justify the churn; the PR records before/after evidence.
9. Accepted behavior, authority/security invariants and scientific fixtures remain intact.
10. No new broad framework, dependency, state store, compatibility subsystem or cleanup platform is added.
11. Runtime-performance claims are measured rather than inferred from LOC.
12. Cleanup stops at the low-confidence/low-ROI frontier instead of broadening scope to hit an arbitrary reduction target.
13. Exact-head deterministic gates are green and no current blocking review finding remains.

## 12. Minimum-necessary test

Criterion: remove high-confidence historical/duplicate semantic surface before 101–110 build on it.  
Is this work necessary? **Only if 100a proves high-ROI candidates.**  
Can the criterion be achieved by a broad refactor? **No.** Broad refactoring creates churn and risks mixing feature semantics with cleanup.  
Can the criterion be achieved by automatic dead-code deletion? **No.** Unwired desired capabilities and authority/scientific boundaries can look unreachable to static tools.  
What happens if the audit finds little value? Cancel 100b and proceed to 101; sunk cost in the cleanup plan is also zero.

## 13. Definition of done

- 100a merged and its exact audit evidence consumed;
- 100b freshly re-derived and readiness freezes one bounded high-confidence candidate set;
- implementation satisfies section 11;
- desired unwired capabilities are preserved;
- before/after semantic-surface evidence recorded;
- exact-head gates green;
- implementation merged and registry reconciled;
- 101 begins only from the simplified reconciled master.
