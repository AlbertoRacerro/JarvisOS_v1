# 128a — JARVIS-PR-ATTENTION-EVIDENCE-1

Planning/readiness authority date: 2026-08-30
Exact JarvisOS planning base: `73094eb54f6650b8dd8d18e4e0e95a6d768284e6`
Hard dependency: `128 ARCHITECTURE-ENFORCEMENT-GATE-1` merged through implementation PR #441 and registry reconciliation on the planning base.
Upstream candidate: `AlbertoRacerro/jarvis-pr-attention`
Pinned inspected upstream head: `c544e2885a69173c58feb2355bb53e8866e627eb`
Upstream release PR at planning time: #16 (`Release 0.13.1 compact V1.11 cycle`), open/draft because of the known connector Draft/Ready regression.
Direct upstream license at the inspected head: MIT.

This document is the complete low-risk definition/full-spec/readiness packet for one independently removable JarvisOS repository-development integration of the already-audited `jarvis-pr-attention` V1.11 strict cycle. It does not itself authorize implementation while the live `docs/specs/STATUS.md` row is absent or not `ready`.

The upstream tool is evidence collection only. JarvisOS remains the sole owner of semantic acceptance, queue/work state, review decisions, exact-head merge decisions, `STATUS.md`, persistence and all product/runtime authority.

## 1. Problem statement

JarvisOS repeatedly reconstructs pull-request facts—exact head, checks, review state, branch-policy evidence, bounded patch/thread evidence and stale-head continuity—before semantic acceptance and merge. The already-audited V1.11 `jarvis-pr-attention` cycle packages that read-only collection into a strict exact-head evidence helper.

The useful part is mechanical evidence collection. The dangerous failure mode is authority inversion: treating a favorable tool output such as `merge_candidate=true`, `READY`, or an accepted-head input as permission to approve, merge, mutate the queue, persist canonical work state or bypass fresh JarvisOS semantic acceptance.

128 now provides deterministic architecture enforcement against new ownership side channels. 128a may therefore integrate the tool only as a removable read-only CI/evidence surface under that guard.

## 2. Exact source evidence

The accepted source audit is `docs/audits/JARVIS_PR_ATTENTION_V1_11_AUDIT_2026-08-30.md`, originally bound to upstream head `c544e2885a69173c58feb2355bb53e8866e627eb`.

Fresh planning inspection of that exact upstream head confirms:

- `cycle/action.yml` is a composite read/evidence action;
- it accepts one repository/PR and optional exact `expected-head`;
- it emits bounded evidence/status outputs including `head-sha`, `attention`, `gate-status`, `semantic-status`, `live-review-bound`, `merge-candidate`, `safety-status`, and evidence-file paths;
- the strict cycle rejects caller/head mismatches and stale/incomplete evidence;
- the inspected action invokes the Python cycle CLI and contains no repository-write, comment, review, label, merge or provider step;
- a naked accepted-head claim does not establish semantic authority in strict mode;
- the upstream release PR remains unmerged at planning time, so JarvisOS MUST pin the immutable inspected commit SHA rather than a mutable branch/tag/release name.

The upstream PR's draft transport state is not a JarvisOS semantic blocker. The pin is to the exact audited Git commit, not to the GitHub PR state.

## 3. Goal

Add one repository-development-only, read-only, exact-head evidence integration that runs the pinned V1.11 strict cycle for JarvisOS pull requests and publishes inspectable advisory evidence without granting the upstream tool any JarvisOS authority.

The integration must be removable without loss of JarvisOS truth or delivery capability.

## 4. Scope

The implementation may add only the minimum repository-development surfaces required to run and verify the integration, expected to be:

- one GitHub Actions workflow under `.github/workflows/` that invokes the pinned exact upstream action;
- one small deterministic repository checker and/or focused tests only if required to mechanically enforce the authority and pinning contract in normal CI;
- the corresponding minimal CI hook if the checker is not naturally covered by existing CI;
- the live registry lifecycle change for 128a.

No product backend, frontend, schema, migration, database, provider, AI execution, domain API, runtime store or user-facing behavior belongs to this slice.

## 5. Required integration contract

### 5.1 Immutable upstream identity

The workflow MUST invoke the upstream action by full 40-character commit SHA:

`AlbertoRacerro/jarvis-pr-attention/cycle@c544e2885a69173c58feb2355bb53e8866e627eb`

No branch, floating tag, release alias or short SHA is acceptable. Updating the upstream pin is a future reviewed change with a fresh source/license/security audit.

### 5.2 Event and token boundary

The integration MUST use a normal `pull_request`-class read-only workflow boundary. It MUST NOT use `pull_request_target` merely to obtain stronger credentials.

Workflow permissions must be explicitly least-privilege/read-only. No `contents: write`, `pull-requests: write`, `issues: write`, `checks: write`, `statuses: write`, `actions: write`, repository-administration, deployment or package-write permission may be granted.

No new secret or credential is authorized. The action may receive only the normal ephemeral GitHub token within the explicit read-only permission boundary.

If some GitHub policy fact cannot be read with that token, the result must remain incomplete/UNKNOWN/BLOCKED evidence; the integration must not broaden credentials or reinterpret unreadable truth as PASS.

### 5.3 Exact-head binding

Every invocation MUST bind `expected-head` to the exact pull-request event head (or an equivalently direct exact GitHub event value). A moved head invalidates the evidence normally.

The workflow MUST expose the action's observed `head-sha` in its evidence and fail or clearly classify a mismatch. JarvisOS merge logic continues to perform its own fresh exact-head read immediately before mutation.

### 5.4 No imported semantic acceptance

V0 MUST NOT supply `accepted-head`, `confirm-accepted-head-authority`, review-result files, continuity-result files, or any other semantic-acceptance input from JarvisOS unless a later separately accepted slice defines a signed/traceable bridge.

This keeps the first integration strictly in full evidence-collection mode and prevents external evidence continuity from becoming a shadow semantic-acceptance registry.

### 5.5 Advisory outputs only

All upstream outputs are evidence/display only. In particular:

- `merge-candidate` MUST NOT feed a merge, auto-merge, Ready/Draft transition, approval, review submission, comment, thread resolution, label, branch update, queue transition, `STATUS.md` update or any repository mutation;
- `attention`, `next-action`, `gate-status`, `semantic-status`, `safety-status` and `baseline-authority` are advisory classifications, not JarvisOS work-state authority;
- workflow success is not semantic PASS;
- a favorable result cannot skip JarvisOS spec/readiness, deterministic gates, independent review when required, or ChatGPT semantic acceptance.

The workflow may upload the generated evidence artifact and/or write a job summary because those are non-canonical CI evidence surfaces. It must not persist a second JarvisOS queue or approval database.

### 5.6 Failure behavior

The integration must fail closed or surface an explicit non-green evidence state for:

- exact-head mismatch;
- malformed/tampered action output;
- unavailable required evidence;
- upstream action execution failure;
- missing evidence artifact;
- an unexpected upstream pin;
- any future workflow edit that introduces write permissions or mutation consumers.

The integration must not make otherwise-required JarvisOS deterministic CI disappear merely because the helper is unavailable. A helper outage is an evidence-helper failure, not permission to merge without required JarvisOS gates.

## 6. Deterministic anti-authority guard

Implementation MUST provide repository-local deterministic evidence that the integration cannot silently drift into authority. The smallest acceptable mechanism is a focused checker/test that parses the workflow and proves at least:

1. exact upstream owner/repository/path and full pinned SHA;
2. no mutable action ref for `jarvis-pr-attention`;
3. event is not `pull_request_target`;
4. explicit workflow/job permissions contain no write/admin scope;
5. `expected-head` is bound from the live PR event rather than a caller-supplied free string;
6. no downstream expression or step uses `merge-candidate` (or equivalent favorable output) to invoke a repository mutation;
7. no comment/review/label/merge/STATUS mutation step is present in this workflow;
8. 128's architecture checker remains green and the V2 coordination bus remains non-authoritative.

The checker should inspect the exact workflow structure rather than depend only on brittle free-text regex where YAML structure is available. A tiny, purpose-specific parser is preferred over new general infrastructure.

## 7. Acceptance criteria

Implementation is accepted only when all of the following are true on one frozen exact head:

1. 128a is the sole implementation identity for this integration and live `STATUS.md` is correctly associated with its implementation PR.
2. The workflow invokes only `AlbertoRacerro/jarvis-pr-attention/cycle@c544e2885a69173c58feb2355bb53e8866e627eb` for the helper.
3. The workflow uses a normal pull-request event and explicit read-only permissions; no new secret/account/credential is required.
4. `expected-head` is exact-event-bound.
5. The first integration supplies no accepted-head/review-result/continuity semantic authority inputs.
6. Tool outputs are published only as advisory CI evidence/artifacts/summary and have no mutation consumer.
7. Focused deterministic anti-authority tests contain both positive and synthetic negative fixtures for mutable pin, write permission, `pull_request_target`, missing exact-head binding and a synthetic merge-candidate→mutation misuse.
8. `python scripts/check_architecture_enforcement.py` passes on the implementation head.
9. `python scripts/check_spec_status.py --self-test` passes.
10. Full backend test and Ruff gates required by `AGENTS.md` pass on the frozen head; no browser proof is required because this slice has no visible frontend delta.
11. The integration is independently removable: deleting its workflow/checker/test surfaces leaves JarvisOS canonical/runtime truth and merge authority intact.
12. A fresh semantic acceptance audit confirms no upstream output, artifact, summary, or check conclusion has become JarvisOS semantic acceptance or merge authority.

A live successful run of the helper on the implementation PR is desired exact-head evidence when GitHub permits the external action to execute. If GitHub refuses to execute the exact pinned action for transport/policy reasons, that is an implementation blocker to solve within this slice; do not weaken pinning or permissions merely to obtain green status.

## 8. Non-goals

128a does NOT authorize:

- any product/runtime feature;
- any backend/frontend/domain/schema change;
- semantic review by `jarvis-pr-attention`;
- automatic review requests, approvals, request-changes, comments or thread resolution;
- merge or auto-merge;
- queue/spec/readiness selection;
- writes to `STATUS.md` from the workflow;
- persistent scheduler/work-state storage;
- accepted-head or failed-review continuity import from JarvisOS;
- repository-settings changes;
- broader GitHub credentials;
- vendoring the upstream project;
- replacing existing deterministic CI, ChatGPT semantic acceptance or exact-head merge guards;
- implementation of 127, 129–134, 113, or any 114–126 slice.

## 9. Failure modes to test first

| Failure mode | Required result |
| --- | --- |
| Upstream ref changes from exact c544 SHA to tag/branch/short SHA | deterministic checker fails |
| Workflow changes to `pull_request_target` | deterministic checker fails |
| Any GitHub permission becomes write/admin | deterministic checker fails |
| `expected-head` omitted or sourced from free input | deterministic checker fails |
| `merge-candidate` is wired to merge/comment/review/label/status mutation | deterministic checker fails |
| Action reports head different from event head | helper/workflow fails or emits explicit blocking state; never accepted |
| Required GitHub fact unreadable with read-only token | explicit incomplete/UNKNOWN/BLOCKED evidence; no credential broadening |
| Upstream helper is unavailable | integration red/explicitly unavailable; no semantic bypass |
| Evidence artifact is malformed/missing | integration red/explicitly invalid |
| Coordination Bus V2 workpack claims favorable state | ignored as authority; 128 gate remains green |

## 10. Files likely touched by implementation

Expected narrow allow-list, to be revalidated on fresh implementation base:

- `.github/workflows/pr-attention.yml` (new)
- `scripts/check_pr_attention_integration.py` (new, only if needed for the deterministic guard)
- `backend/tests/test_pr_attention_integration_contract.py` or an equivalent focused repository test (new, only if that is the existing test-home convention)
- `.github/workflows/ci.yml` only if the checker is not already reached by an existing repository-wide gate
- `docs/specs/STATUS.md` for lifecycle only

Any product source path is outside scope.

## 11. Test plan

Focused moving-head checks:

```bash
python scripts/check_pr_attention_integration.py
python -m pytest -q backend/tests/test_pr_attention_integration_contract.py
python scripts/check_architecture_enforcement.py
python scripts/check_spec_status.py --self-test
```

Use the exact paths/commands that exist after implementation; do not add redundant runners if one checker can own the contract.

Frozen-head terminal gates:

```bash
cd backend
python -m pytest -q
python -m ruff check app tests
cd ..
python scripts/check_spec_status.py --self-test
python scripts/check_architecture_enforcement.py
python scripts/check_pr_attention_integration.py
```

Plus the exact-head GitHub workflow run of the new helper and ordinary repository CI. Browser proof: not required unless implementation unexpectedly creates a visible UI delta, which would itself require scope review.

## 12. Readiness decision

Decision: **READY only after this planning packet is merged and the live registry is separately reconciled to `128a=ready`.**

Readiness basis on exact planning master `73094eb54f6650b8dd8d18e4e0e95a6d768284e6`:

- hard dependency 128 is merged and reconciled;
- the exact upstream source and license were previously code-first audited and rechecked at the same immutable upstream head;
- implementation is additive, repository-development-only, read-only and independently removable;
- it adds no product store, schema, provider, secret, external account or runtime authority;
- the first release deliberately excludes semantic continuity/accepted-head inputs, reducing the integration to exact-head evidence collection;
- failure modes and deterministic negative tests are bounded and inspectable;
- connector compatibility mode requires the eventual implementation PR to be created directly non-draft, but that transport state grants no semantic authority.

Before implementation starts, the writer must re-read fresh master, this file, the upstream exact head, the audit, 128 gate state, current open PRs and live `STATUS.md`. If upstream head c544 is no longer fetchable or its content differs from the audited commit identity, readiness fails closed and must be re-derived.

## 13. Minimum-necessary test

### Test del minimo necessario
Criterio di accettazione della spec:
Reduce repeated exact-PR evidence collection without adding a second acceptance/merge/work-state authority.
Questo lavoro serve a soddisfarlo?           sì
Il criterio è raggiungibile senza di esso?   sì — manual ChatGPT/GitHub evidence collection already works, but it repeats a bounded error-prone mechanism that the audited exact upstream implements directly.
Se sì: perché lo aggiungo comunque
The integration is justified only because it is pinned, read-only, removable and mechanically prevented from becoming authority; it reduces repetitive evidence plumbing while preserving every existing deterministic and semantic merge gate. If that narrow boundary cannot be maintained, do not implement it.
