# Generic builder toolbox audit — 2026-09-10

Status: bounded post-143 infrastructure audit and migration decision

Authority: `docs/MAINTAINER_BETA_DELIVERY_DIRECTIVE_2026-09-09.md`. This record does not widen product, Git, credential, filesystem, provider, execution, review, or merge authority.

## Evidence base

The beta-convergence work through specs 113/124/140/141/142/143 established several repository-owned primitives under real CI and exact-head delivery/proof use. The post-143 directive requires classifying those recent primitives before changing them and generalizing only measured task/spec coupling.

The observed coupling is concentrated in the browser-proof stack:

- `.github/browser-proof/run.mjs` contains a `routes` table plus permanent `prove113`, `prove124`, and `prove140` control branches and product presentation strings.
- `.github/workflows/exact-head-browser-proof.yml` exposes exactly three scenario choices and contains a `113-memory-models` seed branch.
- `.github/workflows/exact-head-browser-proof-command.yml` hard-codes three labels and maps each label to a scenario in shell control flow.
- the trusted/controller, exact-head, candidate-user, credential-isolation, manifest, artifact, and Chromium boundaries themselves are already reusable and must be preserved.

This coupling caused repeated controller-only repairs during 143 closure (#594/#596/#598) when product semantics changed while the trusted execution boundary remained valid. That is evidence for separating reusable proof capability from task-specific proof intent; it is not evidence for weakening or replacing the trust boundary.

## Inventory decision

| Infrastructure | Classification | Evidence / decision |
| --- | --- | --- |
| Exact-head candidate resolution, same-repository/open-PR checks, expected-head equality and CAS-style identity | **GENERIC AS-IS** | Task-neutral trust invariant. Keep exact behavior. |
| Unprivileged candidate user, stripped checkout credentials, blank `GITHUB_TOKEN`/`GH_TOKEN`, trusted-controller ownership checks | **GENERIC AS-IS** | Task-neutral security boundary. No authority widening is justified. |
| Chromium startup, trace/screenshot/manifest hashing, fallback failure manifest, artifact upload | **ABSORB** | Reusable engine/evidence primitives already exist but are embedded beside scenario logic; retain semantics inside the generic executor/workflow. |
| `.github/browser-proof/run.mjs` `prove113` / `prove124` / `prove140` branches | **GENERALIZE** | Permanent spec-specific control logic and presentation strings in the trusted engine caused measured repair churn. Replace with a closed declarative plan interpreter. |
| Workflow `scenario` choice list and command-wrapper label-to-scenario `case` | **GENERALIZE** | Future proof plans currently require infrastructure edits. Resolve a validated trusted plan ID instead; only plans committed on trusted `master` may execute. |
| 113-only fixture setup and `seed_113.py` identity | **GENERALIZE narrowly** | The need for a task fixture is legitimate; the permanent spec-number branch is not. Move to an allowlisted closed fixture operation/fixture identifier. Do not accept arbitrary scripts or paths from plan/model input. |
| Cloud-native delivery bridge (#591–#593) | **GENERIC AS-IS** | Already binds durable payloads to exact PR/head/ref/path/profile and delegates mutation to trusted fixed owners. No spec-143 coupling remains. |
| Local worktree actuator 141 | **GENERIC AS-IS** | Already capability-oriented and optional; no evidence that a new abstraction improves reuse. |
| Manual expert review / deterministic review evidence | **GENERIC AS-IS** | Review is exact-head/task-input driven; recent #597 changed only capacity headroom, not per-spec control logic. |
| Mechanical post-merge STATUS reconciliation | **GENERIC AS-IS** | Repeated 113/124/141/143 reconciliations use the same lifecycle primitive; do not add another lifecycle system. |
| Historical per-spec proof compatibility code after migration | **RETIRE/REPLACE** | 113/124/140 remain regression plans, not engine branches. 143 is product acceptance history, not a permanent proof executor mode. |

## Minimum target architecture

### 1. Trusted generic browser executor

Keep one trusted controller on `master`. It loads exactly one declarative proof plan from a fixed trusted directory after validating the plan identifier against a strict safe-name grammar and resolving the file beneath that directory. Unknown IDs, unknown schema versions, unknown operations, malformed selectors/arguments, and unsupported fixture IDs fail closed.

The executor exposes a closed vocabulary only. Initial primitives should be limited to operations already required by the proven 113/124/140 regression cases, for example:

- navigate to a relative application route and assert HTTP/path;
- issue a same-origin GET and retain parsed JSON as read-only evidence;
- locate by approved Playwright locator forms (`role`, `text`, `testid`, fixed CSS) and assert visible/count/attribute/text;
- focus/keyboard-toggle native `details > summary` through the existing keyboard-tested disclosure primitive;
- click a located control;
- capture text/attribute or a JSON-pointer-like scalar into a named evidence value;
- compare captured values using closed equality/regex/template/set-membership predicates;
- assert absence of bounded text/regex vocabulary from page/body/button labels;
- run an allowlisted trusted fixture operation with fixed argument schema;
- save a screenshot;
- emit assertion/evidence records.

No plan operation may evaluate JavaScript supplied by the plan, run arbitrary shell/Python/Node, provide an arbitrary filesystem path, select an arbitrary workflow, expose credentials, or acquire mutation/merge authority.

### 2. Trusted declarative proof plans

Move 113/124/140 intent into trusted data files such as `.github/browser-proof/plans/<plan-id>.json`. The files are repository-reviewed trusted controller data, never read from the candidate checkout. Product strings, task routes, expected human labels, task-specific JSON fields, and assertion ordering belong in these plans.

The first migration must preserve the existing real-browser semantics rather than merely reproduce green status:

- **113**: empty state, bounded model-version fixture, exact A/B selection, real keyboard Technical-details disclosure, exact identities, and absence of forbidden mutation/provider/filesystem/Git affordances.
- **124**: production settings route/provider rows, server-owned credential axes, human summary matched to canonical codes, real disclosure, empty secret input, no secret-reference leakage, no provider execution affordance, egress-state projection.
- **140**: production repository/runtime routes, server-owned repository/runtime/pipeline truth, local-vs-remote directional semantics, nested Technical-details/raw semantic evidence, and no direct mutation/execute/push/merge/update/restart affordances.

Plan data is not a weaker authority source: it is trusted only because it is loaded from the exact default-branch controller checkout under the same ownership protections as the executor.

### 3. Generic trigger without generic authority

The owner-only `pull_request_target:labeled` entry point may admit labels shaped as `browser-proof:<plan-id>`, but it must validate the suffix and verify that the corresponding trusted plan exists on `master` before dispatch. The downstream workflow must independently perform the same plan-ID validation and exact PR/head checks.

This removes per-plan shell branches without making arbitrary workflows, candidate files, or model-authored plans executable. Adding a new proof plan remains a normal reviewed repository change to the trusted plan directory.

### 4. Fixture boundary

Fixtures remain candidate-data preparation, not privileged general scripting. The executor/workflow may call only fixture identifiers present in a closed trusted fixture registry whose implementations and fixed argument schemas live on `master`. The current 113 seed becomes a compatibility fixture with a semantic name rather than a spec-number control branch. Unknown fixture IDs fail closed.

## Migration and acceptance

Implement this as a bounded infrastructure PR, not a product/spec rewrite. Preserve current proof behavior while migrating the three existing scenarios to plans. Required acceptance before merge:

1. deterministic CI and architecture/security checks green;
2. independent severe exact-head review focused on parser/path traversal, plan trust source, operation allowlisting, credential isolation, and authority non-expansion;
3. plan-schema/engine negative tests proving rejection of unknown operation/schema/fixture, unsafe plan ID/path, malformed locator/input, and any arbitrary-code-shaped operation;
4. compatibility tests proving all 113/124/140 plans parse and exercise the same mandatory assertions as the current controller;
5. after the generic controller is trusted on `master`, dogfood at least one real Chromium proof through the generic path; retain the other migrated plans as required regression coverage and run them when practical before declaring the migration converged;
6. exact-head manifest continues to bind repository, PR, base/head identities, controller SHA, plan ID, browser and verdict; fallback failure evidence remains fail-closed.

Do not combine this pass with product redesign, provider/network expansion, merge automation, generic shell/PTY/filesystem access, or changes to 141/cloud-delivery authority.

## Outcome

The bounded generalization decision is therefore:

- leave cloud delivery, local delivery, review and lifecycle owners unchanged;
- generalize only the measured browser-proof scenario coupling;
- preserve the existing trusted/exact-head/isolation/evidence boundary;
- migrate 113/124/140 into trusted declarative compatibility plans over a closed executor vocabulary;
- treat future proof intent as plan data reviewed on `master`, not as new permanent `prove<spec>` infrastructure logic.
