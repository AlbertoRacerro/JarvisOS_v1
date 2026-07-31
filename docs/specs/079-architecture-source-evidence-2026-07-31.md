# Spec 079 — architecture source-evidence map

**Companion:** `079-architecture-evidence-closure-2026-07-31.md`  
**Pinned JarvisOS baseline:** `d5441f64b1b053d909a15817af70c38a07f6bd0c`  
**Review date:** 2026-07-31

---

## 1. Evidence labels

| Label | Meaning |
| --- | --- |
| `REPO_VERIFIED` | Read directly from the pinned JarvisOS repository state. |
| `UPSTREAM_DOCUMENTED` | Read directly from a pinned first-party upstream documentation repository. |
| `ARCHITECTURE_DECISION` | Decision made by the companion closure from the available evidence and repository constraints. |
| `PROPOSED_PENDING_PROOF` | Candidate mechanism that must pass isolated runtime/security proof before becoming an implementation contract. |
| `DEFERRED` | Intentionally left for the full specification or later governance/readiness work. |
| `BLOCKED` | Claim or behavior that must not be relied upon because evidence contradicts it or is absent. |

Documentation establishes contracts and stated behavior. It does not prove deployment-specific security, permissions, race behavior, cost, or semantic correctness. Those require the disposable-repository proofs listed in the closure.

## 2. Pinned sources

### JarvisOS first-party sources

| ID | Source | Pin | What it establishes | Label |
| --- | --- | --- | --- | --- |
| `RT-01` | `docs/specs/STATUS.md` | `d5441f64b1b053d909a15817af70c38a07f6bd0c` | One active front; 079 remains `planned`; implementation and automatic control remain frozen; planning PRs do not occupy the Implementation PR column. | `REPO_VERIFIED` |
| `RT-02` | `docs/specs/079-autonomous-development-loop-0.md` | same | Required GitHub-owned state, repository-wide atomic claim, exact-head evidence, bounded roles, human merge boundary, stop conditions, promotion ladder, and proof direction. | `REPO_VERIFIED` |
| `RT-03` | `AGENTS.md` | same | Agents may not merge or enable auto-merge; external review and Codex are manual/explicit-only; model findings are advisory and require deterministic reproduction or traceability. | `REPO_VERIFIED` |
| `RT-04` | `docs/specs/022-codex-pr-autopush-no-automerge.md` and current registry description | same | Existing same-branch Codex actuation is retained only for explicit maintainer-requested use; no workflow automatically dispatches it. | `REPO_VERIFIED` |
| `RT-05` | `docs/DECISIONS.md` | same | Repository precedent for recording architectural authority, rejected alternatives, and non-goals without treating planning prose as runtime proof. | `REPO_VERIFIED` |

### GitHub first-party upstream sources

Pinned source repository: `github/docs` at commit `59576b8ee04c6966d6b27766785845c2ed505584`.

| ID | Source path | First-party documented behavior used | Label |
| --- | --- | --- | --- |
| `GH-01` | `data/reusables/actions/actions-group-concurrency.md` | A concurrency group permits at most one running and one pending job/run; a new pending item may replace an existing pending item; ordering is not guaranteed; running work may be cancelled when configured. | `UPSTREAM_DOCUMENTED` |
| `GH-02` | `data/reusables/actions/actions-do-not-trigger-workflows.md` | Events caused using the repository `GITHUB_TOKEN` generally do not create new workflow runs, apart from documented dispatch exceptions; this is intended to prevent recursive runs. | `UPSTREAM_DOCUMENTED` |
| `GH-03` | `content/webhooks/using-webhooks/best-practices-for-using-webhooks.md` | Use a webhook secret, HTTPS, narrow subscriptions, asynchronous processing, rapid acknowledgement, delivery identifiers, and redelivery/replay handling. | `UPSTREAM_DOCUMENTED` |
| `GH-04` | `data/reusables/apps/generate-installation-access-token.md` | Installation tokens may be scoped to repositories and permissions, cannot exceed the App installation permissions, and expire after one hour. | `UPSTREAM_DOCUMENTED` |

Pinned API-description source repository: `github/rest-api-description` at commit `5e28810649ba41b5483753ba74f976f83856a504`.

| ID | Source | Documented mechanism used | Label |
| --- | --- | --- | --- |
| `GH-05` | `descriptions/api.github.com/api.github.com.json`, repository-contents create/update operation | Updating an existing contents object uses the current content/blob identity as an input to the request. This supports evaluating a stale-writer rejection design. | `UPSTREAM_DOCUMENTED` |

`GH-05` does **not** prove that the complete proposed branch/file protocol is linearizable, race-free, immune to ruleset bypass, or sufficient as a repository-wide lock. The closure labels that conclusion `PROPOSED_PENDING_PROOF` and requires an isolated two-writer race test.

### Optional actuator source inspected but not selected

Pinned source repository: `openai/codex` at commit `3d1d26915a303c3b4765828f973f5464f8c28c5c`.

| ID | Source | What it establishes | Label |
| --- | --- | --- | --- |
| `AI-01` | `README.md` | A maintained Codex CLI exists as a possible future implementing adapter. It does not establish repository authority, safe unattended operation, reviewer independence, price, or suitability for 079. | `UPSTREAM_DOCUMENTED` |

No implementer or reviewer provider is chosen by the architecture closure.

## 3. Claim-to-evidence map

| Claim ID | Claim | Evidence | Classification |
| --- | --- | --- | --- |
| `C-01` | GitHub Actions concurrency is insufficient as the canonical repository-wide authority lock. | `GH-01`, `RT-02` | `ARCHITECTURE_DECISION` |
| `C-02` | A workflow-self-trigger chain based on ordinary `GITHUB_TOKEN` side effects has special recursion/liveness limits and must not own continuation authority. | `GH-02` | `ARCHITECTURE_DECISION` |
| `C-03` | A webhook-driven dispatcher must treat delivery as replayable/duplicable input and process asynchronously. | `GH-03` | `ARCHITECTURE_DECISION` |
| `C-04` | A GitHub App provides a stronger primary dispatcher identity than a maintainer-local process while permitting short-lived installation credentials. | `GH-03`, `GH-04`, `RT-02` | `ARCHITECTURE_DECISION` |
| `C-05` | Canonical authority must remain reconstructible from GitHub rather than an external database or vendor conversation. | `RT-01`, `RT-02`, `RT-03` | `ARCHITECTURE_DECISION` |
| `C-06` | One control branch plus one authority file minimizes partial multi-object transition states. | `RT-02`, `GH-05` | `PROPOSED_PENDING_PROOF` |
| `C-07` | Presenting the current file/blob and expected branch head can be the basis for a single-winner conditional transition. | `GH-05` | `PROPOSED_PENDING_PROOF` |
| `C-08` | App permissions alone are not sufficient proof that a compromised App cannot merge or write outside the intended path/branch. | Coarse repository-level permission model; absence of a verified path-capability contract | `ARCHITECTURE_DECISION` |
| `C-09` | The reviewer must have no contents-write authority and cannot share the effective implementing credential. | `RT-02`, `RT-03` | `ARCHITECTURE_DECISION` |
| `C-10` | A clean review or green CI is evidence, not merge consent. | `RT-02`, `RT-03` | `REPO_VERIFIED` |
| `C-11` | Lease expiry cannot itself authorize another front. | `RT-01`, `RT-02` | `ARCHITECTURE_DECISION` |
| `C-12` | GitHub Actions remains suitable for exact-head deterministic gates after canonical authorization. | Existing repository workflows and `RT-02` | `ARCHITECTURE_DECISION` |
| `C-13` | Current JarvisOS runtime egress/accounting authority 059b automatically governs GitHub-hosted coding agents. | No supporting boundary exists | `BLOCKED` |
| `C-14` | A provider can safely deduplicate paid retries. | Provider not selected; no adapter proof | `DEFERRED` |
| `C-15` | The GitHub App is cheaper than a local dispatcher. | No stable cost evidence; deployment not selected | `DEFERRED` |

## 4. Alternative evaluation

| Candidate | Authority integrity | Availability | Permission isolation | Operational burden | Result |
| --- | --- | --- | --- | --- | --- |
| GitHub Actions plus issue/check state | Weak as canonical lock; documented pending replacement and unordered execution | High | Workflow-token dependent | Low–medium | Reject as authority; retain as worker |
| Installed GitHub App plus GitHub control branch | Strongest candidate if conditional write and ruleset proofs pass | High with hosted service | Better identity and short-lived tokens, but contents permission remains coarse | Medium–high | Select as primary, proof-gated |
| Maintainer-local scheduler | Can be safe while online; local authority/recovery risk | Low–variable | Local key custody | Medium and maintainer-dependent | Reject as primary; optional manual inspector |
| External transactional database as authority | Strong database transactions | Host-dependent | Service-defined | Medium–high | Reject because repository cannot reconstruct authority |
| Issue/label/comment as authority | Mutable and multi-object | High | Coarse | Low | Reject; presentation only |
| Model/vendor task state as authority | Vendor-specific, not repository-replayable | Vendor-dependent | Unverified | Low initially | Reject |

## 5. Permission evidence and unresolved enforcement gap

GitHub App installation permissions are repository/resource classes, not a demonstrated path-capability system. The architecture therefore separates three layers:

1. **Installation permission ceiling** — remove all classes not required by the full spec.
2. **Repository rulesets/branch protection** — prevent direct `master` mutation, bypass, force-push, deletion, and unauthorized branch operations.
3. **Capability wrapper** — allow-list exact endpoints, repository ID, branch/path patterns, transition preconditions, and actor role.

None of these layers has been configured or tested by this planning work. The full spec must state exact permissions and denial tests; readiness must provide results from a disposable repository.

Claims withheld:

- that `contents: write` can be scoped natively to only `.jarvis/development-loop/authority.json`;
- that an App with the candidate permissions is technically incapable of calling a merge endpoint;
- that branch protection/rulesets cannot be bypassed by an incorrectly configured App or maintainer token;
- that reviewer and implementer separation exists merely because two model prompts differ.

## 6. Webhook and replay evidence

`GH-03` supports these requirements:

- validate the delivery signature before parsing authority-bearing fields;
- subscribe only to events needed by the state machine;
- acknowledge quickly and process asynchronously;
- retain delivery IDs for deduplication;
- expect missed, delayed, duplicated, or redelivered events;
- reconcile against live GitHub state rather than trusting webhook order.

Claims withheld:

- exactly-once delivery;
- globally ordered delivery;
- automatic redelivery under every failure condition;
- a webhook event proving that the referenced branch/head remains current when processed.

## 7. Actions evidence

`GH-01` directly blocks using a concurrency group as the only global front claim because:

- one pending run can be replaced by another pending run;
- execution ordering is not guaranteed;
- cancellation behavior can change running/pending work without changing repository authority.

`GH-02` blocks assuming that normal `GITHUB_TOKEN` mutations will recursively continue an arbitrary workflow chain.

Therefore:

- a workflow run is an attempt/worker record, not authorization;
- cancelled, missing, stale, action-required, or infrastructure-ambiguous runs cannot release a front;
- only a canonical control transition can claim, release, pause, or halt the front.

## 8. Cost evidence status

No stable first-party price table is adopted by this closure. Prices, quotas, public-repository allowances, included agent seats, and model billing can change independently of repository code.

The full spec must make costs inputs to policy rather than prose constants. Required numerical fields include:

- currency and time basis;
- projected and reserved amount;
- final provider/Actions/hosting amount;
- per-request, run, day, and month caps;
- reservation and release identities;
- unknown/unpriced outcome;
- retry and duplicate-charge evidence.

Until a provider and host are selected, all numeric cost claims are `DEFERRED`.

## 9. Runtime proofs still absent

No live App, webhook, Actions dispatch, model, secret, ruleset, branch-protection change, or provider call was created for this closure. Consequently these remain `PROPOSED_PENDING_PROOF`:

- two-writer single-winner semantics for the control file;
- stale writer failure behavior under the selected API and ruleset;
- hash-chain and commit-ancestry reconstruction;
- App permission-denial behavior;
- inability of dispatcher/reviewer credentials to merge;
- lease recovery after process and GitHub interruptions;
- duplicate paid-request prevention;
- cost reservation/accounting;
- untrusted-fork and prompt-injection isolation;
- kill switches and recovery.

## 10. Claims explicitly blocked or deferred

| Claim | Status | Reason |
| --- | --- | --- |
| GitHub Actions concurrency is a FIFO queue or durable global mutex | `BLOCKED` | Contradicted by `GH-01` |
| Webhook delivery is exactly once and ordered | `BLOCKED` | Not documented; replay/deduplication guidance assumes duplicates/failure |
| Ordinary `GITHUB_TOKEN` side effects can freely self-trigger continuation workflows | `BLOCKED` | Contradicted by `GH-02` outside documented dispatch exceptions |
| Current 059b automatically covers GitHub-hosted agent spend/content | `BLOCKED` | No implemented authority bridge |
| Conditional file update alone proves complete atomic front ownership | `PROPOSED_PENDING_PROOF` | Endpoint/ruleset race test absent |
| App permissions alone guarantee no merge or out-of-scope write | `BLOCKED` | Permission granularity is insufficiently proven |
| Codex, Claude, or another provider is selected | `DEFERRED` | Provider/adapter evidence and governance absent |
| Hosted App is cheaper than a local process | `DEFERRED` | Host/provider/cost basis not selected |
| Architecture closure authorizes the full spec or implementation | `BLOCKED` | Promotion ladder and maintainer boundary explicitly forbid it |

## 11. Evidence result

The evidence supports selecting a GitHub App plus GitHub-owned protected control branch as the primary architecture **only as a proof-gated direction**.

The architecture decision is strong enough to narrow the full-spec design space. It is not strong enough to claim readiness, install permissions, create workflows, spend money, or automate a provider. Those require the isolated proofs and later explicit maintainer decisions.
