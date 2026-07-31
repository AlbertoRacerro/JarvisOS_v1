# Spec 079 — architecture source-evidence map

**Companion:** `079-architecture-evidence-closure-2026-07-31.md`  
**Pinned JarvisOS baseline:** `d5441f64b1b053d909a15817af70c38a07f6bd0c`  
**Review date:** 2026-07-31

---

## 1. Evidence labels

| Label | Meaning |
| --- | --- |
| `REPO_VERIFIED` | Read directly from the pinned JarvisOS repository state. |
| `UPSTREAM_DOCUMENTED` | Read from first-party upstream documentation. |
| `ARCHITECTURE_DECISION` | Selected direction derived from repository constraints and evidence. |
| `PROPOSED_PENDING_PROOF` | Candidate mechanism requiring isolated runtime/security proof. |
| `DEFERRED` | Left for full-spec, governance, or readiness work. |
| `BLOCKED` | Must not be relied upon because evidence contradicts it or is absent. |

Documentation records an interface contract. It does not prove deployment-specific atomicity, permissions, rulesets, security, cost, or semantic correctness.

## 2. Pinned repository sources

| ID | Source | Pin | Establishes | Label |
| --- | --- | --- | --- | --- |
| `RT-01` | `docs/specs/STATUS.md` | `d5441f64b1b053d909a15817af70c38a07f6bd0c` | One active front; 079 remains `planned`; automatic-control implementation remains frozen; planning PRs do not occupy the Implementation PR column. | `REPO_VERIFIED` |
| `RT-02` | `docs/specs/079-autonomous-development-loop-0.md` | same | GitHub-owned state, repository-wide atomic claim, exact-head evidence, bounded roles, human merge boundary, stop conditions, promotion ladder, and proof direction. | `REPO_VERIFIED` |
| `RT-03` | `AGENTS.md` | same | Agents may not merge or enable auto-merge; external review and Codex are manual/explicit-only; model findings are advisory. | `REPO_VERIFIED` |
| `RT-04` | `docs/specs/022-codex-pr-autopush-no-automerge.md` and registry description | same | Same-branch Codex actuation exists only for explicit maintainer-requested use; no workflow automatically dispatches it. | `REPO_VERIFIED` |
| `RT-05` | `docs/DECISIONS.md` | same | Architectural decisions and rejected alternatives may be recorded without treating prose as runtime proof. | `REPO_VERIFIED` |

## 3. GitHub first-party upstream evidence

Pinned documentation repository: `github/docs` at commit `59576b8ee04c6966d6b27766785845c2ed505584`.

| ID | Source | Documented behavior used | Label |
| --- | --- | --- | --- |
| `GH-01` | `data/reusables/actions/actions-group-concurrency.md` | A concurrency group permits one running and one pending item; a new pending item may replace the prior pending item; order is not guaranteed. | `UPSTREAM_DOCUMENTED` |
| `GH-02` | `data/reusables/actions/actions-do-not-trigger-workflows.md` | Ordinary repository `GITHUB_TOKEN` side effects generally do not recursively create workflow runs outside documented dispatch exceptions. | `UPSTREAM_DOCUMENTED` |
| `GH-03` | `content/webhooks/using-webhooks/best-practices-for-using-webhooks.md` | Webhooks require secret validation, HTTPS, narrow subscriptions, fast acknowledgement, asynchronous processing, delivery IDs, and replay handling. | `UPSTREAM_DOCUMENTED` |
| `GH-04` | `data/reusables/apps/generate-installation-access-token.md` | Installation tokens can be scoped within installation permissions and expire after one hour. | `UPSTREAM_DOCUMENTED` |

Pinned API-description repository: `github/rest-api-description` at commit `5e28810649ba41b5483753ba74f976f83856a504`.

| ID | Endpoint family | Documented mechanism used | Label |
| --- | --- | --- | --- |
| `GH-05` | Repository contents create/update | Existing-content updates accept a current blob identity, which can reject a stale file version but does not assert the exact branch-head SHA. | `UPSTREAM_DOCUMENTED` |
| `GH-06` | Git blobs, trees, commits, and references | A caller can create a blob, tree, and commit with an explicit parent, then update a branch ref. A ref update with `force=false` requires a fast-forward update. | `UPSTREAM_DOCUMENTED` |

The ref-level sequence supported by `GH-06` is a stronger candidate than `GH-05` for exact-head exclusion: build the candidate commit on the exact expected ref parent, then attempt a non-forced ref update. If another writer advanced the ref to a divergent commit, the stale candidate is not a fast-forward from the current ref and must be rejected.

This remains `PROPOSED_PENDING_PROOF`. Documentation does not establish complete linearizability, timeout recovery, ruleset behavior, App bypass behavior, or zero side effects by losing workers.

## 4. Optional actuator inspected but not selected

Pinned repository: `openai/codex` at commit `3d1d26915a303c3b4765828f973f5464f8c28c5c`.

| ID | Source | Establishes | Label |
| --- | --- | --- | --- |
| `AI-01` | `README.md` | A maintained Codex CLI exists as a possible future implementer adapter. It does not establish authority, safe unattended operation, reviewer independence, price, or suitability for 079. | `UPSTREAM_DOCUMENTED` |

No implementer or reviewer provider is selected.

## 5. Claim-to-evidence map

| Claim ID | Claim | Evidence | Classification |
| --- | --- | --- | --- |
| `C-01` | GitHub Actions concurrency is insufficient as canonical repository-wide authority. | `GH-01`, `RT-02` | `ARCHITECTURE_DECISION` |
| `C-02` | A self-trigger chain based on ordinary `GITHUB_TOKEN` mutations must not own continuation authority. | `GH-02` | `ARCHITECTURE_DECISION` |
| `C-03` | Webhook delivery is replayable input and must be processed asynchronously and idempotently. | `GH-03` | `ARCHITECTURE_DECISION` |
| `C-04` | A GitHub App provides a stronger primary dispatcher identity than a maintainer-local process. | `GH-03`, `GH-04`, `RT-02` | `ARCHITECTURE_DECISION` |
| `C-05` | Canonical authority must be reconstructible from GitHub rather than an external database or vendor conversation. | `RT-01`, `RT-02`, `RT-03` | `ARCHITECTURE_DECISION` |
| `C-06` | One protected control branch plus one authority file minimizes partial transition states. | `RT-02` | `ARCHITECTURE_DECISION` |
| `C-07` | A Contents API update is sufficient to assert both current file blob and exact branch head. | `GH-05`; contradicted by endpoint boundary | `BLOCKED` |
| `C-08` | A commit built on the exact expected parent plus a non-forced ref update is the selected single-winner candidate. | `GH-06`, `RT-02` | `PROPOSED_PENDING_PROOF` |
| `C-09` | The ref-level candidate is already proven linearizable and race-free. | Runtime proof absent | `BLOCKED` |
| `C-10` | App permissions alone prove no merge or out-of-scope write. | Permission granularity insufficient | `BLOCKED` |
| `C-11` | Reviewer credentials must have no contents-write authority. | `RT-02`, `RT-03` | `ARCHITECTURE_DECISION` |
| `C-12` | A clean review or green CI is evidence, not merge consent. | `RT-02`, `RT-03` | `REPO_VERIFIED` |
| `C-13` | Lease expiry alone may release or transfer the front. | `RT-01`, `RT-02` | `BLOCKED` |
| `C-14` | Actions remains suitable for exact-head deterministic gates after authorization. | Existing workflows, `RT-02` | `ARCHITECTURE_DECISION` |
| `C-15` | JarvisOS runtime egress/accounting policy 059b automatically governs GitHub-hosted coding agents. | No implemented authority bridge | `BLOCKED` |
| `C-16` | A provider can deduplicate paid retries safely. | Provider/adapter not selected | `DEFERRED` |
| `C-17` | Hosted App operation is cheaper than a local process. | Stable deployment/cost evidence absent | `DEFERRED` |

## 6. Corrected CAS reasoning

The exact candidate transition is:

1. read `refs/heads/jarvis-control` and record expected head `H`;
2. verify the authority file and deterministic transition from `H`;
3. create replacement blob `B`;
4. create tree `T` from `H`'s tree with only the authority path replaced by `B`;
5. create commit `C` with parent exactly `H` and tree `T`;
6. update the control ref to `C` with `force=false`;
7. permit no side effect unless success is verified;
8. on rejection, timeout, or ambiguity, reread the ref and event ID before retry.

Why this fixes the P1 defect:

- the prior Contents API candidate bound only the authority blob;
- a separate commit could advance the branch while leaving that blob unchanged;
- the stale file update could then succeed on an unexpected branch tip;
- the corrected candidate binds the new commit to exact parent `H`;
- any concurrent divergent advance makes `C` non-fast-forward from the current ref, so a non-forced ref update rejects it.

The disposable-repository race and timeout proofs remain mandatory.

## 7. Permission and enforcement gap

GitHub App permissions are repository/resource classes, not native path capabilities. The design therefore requires:

1. minimum installation permission ceiling;
2. protected `master` and `jarvis-control`, with no App bypass, force-push, or deletion;
3. capability wrapper allow-listing repository, ref, path, endpoint, transition, and request shape;
4. short-lived credentials;
5. separate read-only reviewer identity;
6. audit of denied operations;
7. abuse tests for merge, ref deletion, settings/secrets mutation, and out-of-scope writes.

Claims withheld:

- that `contents: write` is natively path-scoped;
- that a candidate App is technically incapable of calling a merge endpoint;
- that incorrectly configured rulesets cannot be bypassed;
- that two prompts imply reviewer independence.

## 8. Actions, webhook, cost, and runtime proof status

`GH-01` blocks treating Actions concurrency as a FIFO mutex. `GH-02` blocks assuming arbitrary recursive continuation from normal `GITHUB_TOKEN` writes. `GH-03` blocks exactly-once or globally ordered webhook assumptions.

No stable price table is adopted. Costs must be policy inputs with projected, reserved, and final values, hard caps, unknown-cost stops, and duplicate-charge evidence.

No App, webhook, workflow dispatch, model, secret, ruleset, branch-protection change, or provider call was created. These remain proof-gated:

- two-writer single-winner ref transition;
- unrelated branch advance with unchanged authority blob;
- stale parent/ref rejection;
- timeout-after-success reconciliation;
- event/commit reconstruction and tamper detection;
- permission denials and no-merge proof;
- lease recovery;
- paid-request idempotency and accounting;
- untrusted-fork and prompt-injection isolation;
- kill switches and recovery.

## 9. Alternative evaluation

| Candidate | Result |
| --- | --- |
| GitHub Actions plus issue/check state | Reject as authority; retain as deterministic worker |
| Contents API blob update | Reject as exact-head CAS |
| GitHub App plus protected control branch and ref-level CAS candidate | Select as primary, proof-gated |
| External transactional database as authority | Reject; retain as cache/queue only |
| Maintainer-local scheduler | Reject as primary; optional manual inspector |
| Issue, label, comment, or model task state | Reject as authority |

## 10. Evidence result

The evidence supports a hosted GitHub App and GitHub-owned protected control branch as the narrowed architecture direction.

The authoritative transition candidate is no longer a Contents API file update. It is an exact-parent Git commit followed by a non-forced ref update, with all stale, rejected, timed-out, or ambiguous outcomes failing closed.

This direction is not readiness. Spec 079 remains `planned`; isolated proofs, rulesets, credential denials, schemas, provider contracts, cost authority, governance amendments, and a separate maintainer decision are still required.
