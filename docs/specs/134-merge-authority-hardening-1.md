# 134 — MERGE-AUTHORITY-HARDENING-1

Status: full specification; live implementation authority remains `docs/specs/STATUS.md`.
Depends on: 004, 079
Definition: `134-merge-authority-hardening-1-definition.md`

## Goal

Make merge governance for `master` mechanically truthful and enforceable without giving CI, model reviewers, or scheduled automation hidden merge/settings authority. The implementation establishes a version-controlled minimum policy, deterministic verification of readable GitHub state, and a separately privileged enforcement path. It must never report a protected/verified state while `master` is observably unprotected.

## Exact-master inventory

Derived from exact master `471574f9a73b9a25753abd82c3d7468ea7ce84e5` after merged 134 definition PR #492.

Fresh GitHub control-plane evidence:

- `GET /repos/AlbertoRacerro/JarvisOS_v1/branches/master` is readable and reports:
  - `protected=false`;
  - `protection.enabled=false`;
  - `required_status_checks.enforcement_level=off`;
  - no required contexts/checks.
- `GET /repos/AlbertoRacerro/JarvisOS_v1/rulesets` is readable and returns `[]`.
- the detailed classic protection endpoint `/branches/master/protection` returns HTTP 403 `Resource not accessible by integration`; detailed review/bypass/restriction settings therefore remain unreadable through this integration.
- repository settings are readable and currently report:
  - `allow_auto_merge=false`;
  - `allow_merge_commit=true`;
  - `allow_squash_merge=true`;
  - `allow_rebase_merge=true`;
  - `allow_update_branch=false`.
- current repository process already requires one ChatGPT merge owner, exact-current-head evidence, terminal required CI/review evidence, explicit merge, no deferred auto-merge, and post-merge registry reconciliation; these are process controls, not proof of GitHub-side protection.
- the current branch object is sufficient to classify the minimum protection requirement as a live **MISMATCH**, even though deeper classic-protection details remain UNKNOWN.

The implementation must preserve this distinction: an unreadable detailed endpoint does not erase a readable top-level contradiction.

## V1 minimum policy

The version-controlled declaration must express only controls necessary to close the demonstrated merge-authority gap. V1 minimum:

1. target repository/ref is exactly `AlbertoRacerro/JarvisOS_v1` / `master`;
2. `master` must be GitHub-protected by at least one readable branch-protection/ruleset mechanism;
3. required status-check enforcement must be enabled for the minimum exact-head deterministic merge gate selected below;
4. deferred GitHub auto-merge must remain disabled;
5. enforcement must not grant workflows/models automatic merge authority;
6. explicit maintainer/ChatGPT exact-head merge remains the repository merge operation;
7. any configured bypass that makes required checks optional for the normal merge owner is non-compliant unless explicitly declared and justified in a later spec amendment.

V1 does **not** require changing enabled merge methods. Merge-commit, squash, and rebase availability are observed and reported but are not a minimum enforcement target in this slice. Restricting them is not necessary to close the current missing-protection failure and would broaden repository behavior without evidence.

## Required check identity

The declaration must use stable logical gate IDs and a separately observed mapping to GitHub check contexts, not silently assume workflow display names equal branch-protection contexts.

V1 logical minimum gates:

- `jarvisos-ci`: canonical repository `CI` exact-head deterministic gate;
- `pr-attention-evidence`: `PR Attention Evidence` exact-head mechanical evidence generation.

`PR Attention Evidence` remains advisory/mechanical and never semantic approval. Requiring its check to finish successfully only ensures the accepted exact-head evidence artifact is produced; it does not transfer merge authority to that tool.

Before an enforcement mutation, implementation must discover/freeze the exact current check-run context names associated with successful exact-head runs and include them in the verification/enforcement evidence. If exact context identity cannot be determined safely, enforcement remains blocked rather than guessing a context string.

## Files and ownership

Expected bounded implementation:

- `.github/merge-authority-policy.json` — deterministic V1 declaration; no secrets;
- `scripts/verify_merge_authority.py` — stdlib-only policy parser, GitHub snapshot classifier, live read verifier, and self-test;
- `.github/workflows/merge-authority-verify.yml` — trusted verification/reporting path if required by the accepted readiness packet;
- focused fixture/test data under `scripts/fixtures/` or script-local self-test fixtures only when needed;
- `docs/specs/STATUS.md` lifecycle handshake;
- no product/runtime/frontend/provider/schema files.

Any enforcement mutation of branch protection/rulesets is **not** hidden in a normal PR workflow. It is a separate explicit maintainer-controlled operation using the minimum privileged credential/action available after verification proves the target and intended policy.

## Declaration contract

The policy file must be deterministic JSON with a schema/version field and at least:

- `schema_version`;
- `repository`;
- `branch`;
- `require_protection: true`;
- `require_status_checks: true`;
- logical gate declarations and resolved GitHub context names once known;
- `allow_auto_merge: false`;
- bypass expectation for the normal merge owner;
- an explicit note/field that merge methods are `observe_only` in V1.

Unknown keys/schema versions fail closed. The verifier must reject duplicate/empty check identities, wrong repo/ref, contradictory options, or a policy attempting to authorize auto-merge.

## Observation model

The verifier outputs one overall state and per-control states:

- `VERIFIED`: every minimum control required by the declaration was readable and satisfied;
- `MISMATCH`: at least one readable required control contradicts the declaration;
- `UNKNOWN`: no readable contradiction exists, but at least one required control cannot be established because the relevant live detail is inaccessible/insufficient;
- `ERROR`: declaration/schema/transport/response parsing/verifier failure prevents trustworthy evaluation.

Precedence is deterministic: `ERROR` > `MISMATCH` > `UNKNOWN` > `VERIFIED`.

This means current `master` must classify as `MISMATCH`, not UNKNOWN, because the readable branch object says protection is disabled. The 403 on detailed protection is recorded as an UNKNOWN sub-observation only.

The verifier must emit machine-readable JSON plus concise human text containing:

- repository and branch;
- declaration digest;
- observed master SHA when available;
- queried endpoint classes and whether each was readable;
- per-control result and reason;
- overall state;
- no credential, auth header, token fragment, or raw secret-bearing response.

## Live-read and trusted-code boundary

Normal untrusted pull-request code must never execute with a settings-write credential. A read credential, if needed beyond default GitHub token visibility, must also not be exposed to untrusted PR-controlled executable code.

The preferred verification architecture is:

1. deterministic offline parser/classifier/self-tests run in ordinary PR CI using fixtures and no privileged secret;
2. live control-plane verification executes only trusted `master` code through a maintainer-triggered/trusted workflow or equivalent explicit action;
3. any future settings-write enforcement executes only trusted exact `master` code and requires explicit maintainer invocation/confirmation.

If the default integration can already obtain all required reads safely, no new read secret is introduced merely for symmetry.

## Verification phases

### Phase A — declaration and offline verifier

Implementation must prove:

- current readable snapshot with `protected=false` => `MISMATCH`;
- protected=true but detailed required checks unreadable => `UNKNOWN` unless a ruleset/other readable surface proves them;
- visible protection + exact required checks + auto-merge off + compliant bypass state => `VERIFIED`;
- malformed/unsupported API/policy => `ERROR`;
- readable contradiction outranks unrelated unknown details;
- rule/ruleset and classic-protection evidence are normalized without double-counting;
- output ordering and declaration digest are deterministic.

### Phase B — live verification

From trusted code, query current repository metadata, branch metadata, rulesets and detailed protection where permission allows. Capture a bounded evidence record. With current settings the expected pre-enforcement result is `MISMATCH`.

### Phase C — explicit enforcement

Only after exact target/policy/check contexts are established may the maintainer apply the minimum GitHub protection required by V1. Enforcement must:

- target only `master`;
- enable protection and required status checks for the frozen contexts;
- preserve `allow_auto_merge=false`;
- avoid enabling autonomous merge;
- avoid unrelated merge-method/repository-setting changes;
- record before/after snapshots with secret-safe evidence;
- fail without partial policy claims if GitHub rejects the mutation.

If this runtime/tool integration cannot perform the settings mutation, implementation must stop at the explicit human-only enforcement gate and report the exact required GitHub settings action; it must not use undocumented API workarounds or weaker credentials.

### Phase D — post-enforcement verification

134 is not complete merely because declaration/verifier code merged or because a settings API call returned 2xx. A trusted fresh live verification of the resulting configuration must return `VERIFIED` for all V1 minimum controls. If it returns `MISMATCH`, `UNKNOWN`, or `ERROR`, 134 remains unfinished.

## Failure modes and required behavior

1. `branches/master/protection` 403 while branch metadata says unprotected -> overall `MISMATCH`, detailed substate UNKNOWN.
2. rulesets `[]` + branch unprotected -> MISMATCH; do not infer hidden protection.
3. rulesets `[]` + branch protected but detailed settings unreadable -> UNKNOWN for required-check/bypass details, not VERIFIED.
4. policy file changed without verifier update -> schema/semantic validation fails.
5. required check context renamed -> live verification MISMATCH/UNKNOWN; no silent fallback to workflow name.
6. auto-merge becomes enabled -> MISMATCH even if protection is otherwise green.
7. verifier cannot distinguish bypass semantics -> UNKNOWN, never VERIFIED.
8. API rate/transport error -> ERROR; do not claim settings changed or compliant.
9. enforcement succeeds partially -> live post-check governs; no optimistic success state.
10. a PR modifies trusted workflow/script while privileged live workflow runs -> trusted workflow must fetch/use exact `master`, never PR executable content.
11. any attempt to add merge/write actuation to PR Attention, model review, or normal CI -> reject as out of scope/authority violation.
12. an enforcement proposal changes squash/rebase/merge-method settings -> reject in V1 unless separately re-derived.

## Acceptance criteria

1. One deterministic policy declaration exists and cannot authorize auto-merge.
2. Offline verifier has deterministic self-tests/fixtures covering VERIFIED/MISMATCH/UNKNOWN/ERROR precedence and hostile/malformed inputs.
3. Current known unprotected branch snapshot deterministically produces MISMATCH.
4. Live trusted verification reports exact target/declaration digest/source endpoints and never logs credentials.
5. Exact required GitHub status-check contexts are discovered from live successful checks before enforcement; no guessed context names.
6. Untrusted PR code never executes with settings-write credential; privileged workflows/actions use trusted exact `master` code only.
7. Before/after enforcement is explicitly separated from declaration/verification and is maintainer-controlled.
8. Minimum protection is applied to `master` without enabling auto-merge or unrelated repository-setting changes.
9. A fresh post-enforcement live verification returns VERIFIED for protection, required status checks, no-auto-merge, and normal-owner bypass policy.
10. An attempted stale/wrong-ref/wrong-repo enforcement fails closed.
11. Existing canonical CI/PR Attention evidence and no-auto-merge process remain intact.
12. No product/runtime/provider/schema/frontend change occurs.
13. `docs/specs/STATUS.md` lifecycle handshake is correct on implementation PR, and post-merge reconciliation occurs only after exact implementation merge.
14. README progress mirror is updated only when the final 134 merged transition makes the hardening marker stale.

## Deterministic tests

At minimum:

- declaration parser success and invalid schema/version/target/options rejection;
- policy digest stability;
- fixture: current unprotected branch + empty rulesets + protection 403 -> MISMATCH;
- fixture: protected branch + unreadable detailed checks -> UNKNOWN;
- fixture: fully compliant protection/checks/auto-merge/bypass -> VERIFIED;
- fixture: compliant protection but auto-merge enabled -> MISMATCH;
- fixture: malformed API data / HTTP failure -> ERROR;
- fixture: MISMATCH outranks UNKNOWN; ERROR outranks all;
- check-context identity mismatch fails;
- wrong repository/branch/ref fails before any enforcement request;
- secret-redaction/log-output test;
- enforcement request builder, if implemented, changes only the declared minimum fields and cannot enable auto-merge;
- repeated identical verification produces byte-stable normalized JSON excluding explicitly time-varying observation fields.

## Required review/gates

Because 134 changes repository merge-governance/control-plane behavior, use the full lifecycle and exact-head frozen gates. The implementation diff requires explicit semantic review of:

- trusted-code/secret boundary;
- verifier truth table;
- enforcement target/minimum-diff semantics;
- bypass and required-check interpretation;
- no-auto-merge invariant;
- rollback/failure behavior.

Independent review is required before final implementation merge because a mistake could weaken repository merge protection or falsely report compliance.

## Rollback

Declaration/verifier/workflow files are ordinary version-controlled rollback. GitHub protection rollback is a separate explicit maintainer action using the recorded pre-enforcement snapshot. Never automatically restore a weaker pre-state after a verification failure; report the mismatch and require an explicit maintainer decision if rollback would remove protection.

## Non-goals

- no deferred GitHub auto-merge;
- no model/workflow-owned merge;
- no broad GitHub administration framework;
- no provider/runtime/frontend/backend product change;
- no new model reviewer dependency;
- no restriction of merge methods in V1;
- no generic repository/fork policy system;
- no bypass of GitHub permission errors with undocumented calls;
- no 113–126 implementation/planning work before 134 is actually complete and reconciled.

## Readiness prerequisites

A later separate readiness packet must revalidate exact current master and confirm:

- definition/full spec merged;
- current protection state and repository merge settings freshly observed;
- exact implementation files remain bounded;
- trusted live verification path is feasible;
- a concrete explicit path exists for the necessary `master` protection mutation and post-enforcement readback, even if the final mutation requires a human-controlled GitHub permission/action;
- required independent review can be obtained.

If no safe path exists to apply/read back the minimum protection, readiness must be BLOCKED rather than authorizing a report-only implementation and calling 134 complete.

### Test del minimo necessario

Criterio di accettazione della spec: `master` has a declared, mechanically verified minimum merge-protection policy whose enforcement is explicit, exact-target, no-auto-merge, and does not grant automation hidden merge authority.

Questo lavoro serve a soddisfarlo? sì.

Il criterio è raggiungibile senza GitHub-side enforcement? no — fresh live branch metadata currently reports `protected=false`; repository prose alone cannot close that control-plane gap.
