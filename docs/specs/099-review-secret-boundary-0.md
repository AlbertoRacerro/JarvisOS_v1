# 099 — REVIEW-SECRET-BOUNDARY-0

Definition status: **complete; emergency security interrupt; ready only with the paired readiness record and registry authority**  
Derived from exact master: `c87e149145c15ea1e87e967694bbebb45591a18b`  
Depends on runtime authority: 017, 019

## 1. Purpose

Close the confirmed secret-exposure boundary in the manually dispatched Cheap and Senior review workflows before normal product implementation continues.

Today those workflows checkout an arbitrary pull-request head, restore only `AGENTS.md`, `scripts/cheap_review.py`, and `scripts/manual_review.py` from trusted `master`, and then execute `python scripts/manual_review.py` while `GITHUB_TOKEN` and a provider API key are present. Because Python imports can resolve modules from the executed script directory, an untrusted PR can add a shadow module such as `scripts/json.py` or another import target that is not overwritten by the partial restore. Dispatching the manual review on that PR can therefore execute PR-controlled Python in the secret-bearing process.

099 removes that class of failure. The provider-bearing review process must execute only trusted repository code from exact `master`; pull-request content is review **data**, never executable/importable filesystem authority.

## 2. Emergency sequencing authority

099 is a maintainer-authorized security interrupt under `AGENTS.md` and `docs/AGENT_EXECUTION_AND_AUTOMATION_PROTOCOL.md`.

The already-open 092 implementation PR #303 is preserved, not abandoned or superseded. While 099 is active, no new functional 092 implementation commit may be added. The 092 branch/head remains a recoverable paused checkpoint. After 099 implementation is merged and registry-reconciled, the normal binding queue resumes at 092 with its existing specification, readiness authority, PR, and implementation state; 099 does not re-derive or alter 092.

Only one writer/front is active at a time. The security implementation is intentionally bounded to review-workflow infrastructure and its deterministic security tests.

## 3. Scope

In scope:

- `.github/workflows/cheap-review.yml`;
- `.github/workflows/senior-review.yml`;
- `scripts/manual_review.py` only if a minimal trusted-worktree guard or testable seam is required;
- `scripts/cheap_review.py` only if a minimal shared helper change is required;
- one focused deterministic workflow-security checker/test and its CI invocation if needed;
- normal `docs/specs/STATUS.md` lifecycle bookkeeping.

Out of scope (binding non-goals):

- changing review verdict semantics, prompts, providers, models, budgets, token limits, retry policy, or review authority;
- changing `claude-review.yml`, `codex-autopush.yml`, spec 079, normal CI, product runtime, frontend, backend, schemas, database state, provider gateway, runner behavior, or product egress policy unless a new independently proven P0 is discovered during implementation;
- rotating credentials without evidence that a secret was actually exposed;
- allowing automatic external reviews or automatic implementation/fix loops;
- broad workflow refactors or a new CI framework;
- modifying or closing PR #303 except for the minimum explicit pause/resume coordination required by this security interrupt.

## 4. Required trust boundary

The implementation must establish all of the following:

1. A job/process that receives `DEEPSEEK_API_KEY`, `GLM_API_KEY`, or another review-provider secret must not checkout, execute, import, source, install, or otherwise load code from the reviewed PR head.
2. Trusted executable review code and authority files come from exact repository `master` for the dispatched workflow revision.
3. PR metadata and diff are fetched through GitHub API calls and treated as bounded inert text. `manual_review.py` already obtains PR metadata and the diff through `gh_request`; preserve that shape unless a smaller equivalent is proven.
4. The referenced implementation spec is read only from trusted `master`. Under normal JarvisOS lifecycle, implementation authority is already merged before an implementation PR exists. A PR that references an unavailable/unmerged spec must not cause the workflow to checkout that PR to obtain executable or authority files.
5. Checkout credentials are not persisted into the working tree when they are unnecessary (`persist-credentials: false`).
6. Provider and GitHub secrets are never printed, embedded in artifacts/comments, or passed to PR-controlled code.
7. No change weakens current stale-head detection, append-only advisory comments, explicit maintainer dispatch, or human merge authority.

## 5. Minimum implementation shape

The expected minimum fix is:

- both manual review workflows checkout trusted `refs/heads/master` (or an equivalently exact trusted master commit resolved by the workflow), **not** `refs/pull/<n>/head`;
- set `persist-credentials: false` on the trusted checkout;
- remove the current partial post-checkout repair (`git fetch origin master` plus `git checkout FETCH_HEAD -- AGENTS.md scripts/cheap_review.py scripts/manual_review.py`) because there must be no untrusted PR worktree to repair;
- continue to pass only `REVIEW_PR_NUMBER` into trusted `scripts/manual_review.py`;
- continue to obtain PR metadata/diff through GitHub API using the bounded workflow token;
- add a deterministic guard that fails if either provider-secret workflow again checks out a PR ref or executes review Python from a PR-controlled tree.

A larger sandbox, container, second repository checkout, package installation, or new credential is not authorized unless the builder proves this minimum shape cannot satisfy the acceptance criteria.

## 6. Threat model and failure cases

The implementation and tests must cover at least:

- malicious PR adds `scripts/json.py` and the reviewer imports `json`;
- malicious PR adds another stdlib/package-shadowing module imported transitively by `manual_review.py` or `cheap_review.py`;
- malicious PR modifies `scripts/manual_review.py`, `scripts/cheap_review.py`, or `AGENTS.md`;
- malicious PR modifies a spec file used to influence review authority;
- PR diff contains shell/Python/YAML text that looks executable or contains prompt-injection content;
- requested PR does not exist, has an unavailable spec, moves head during review, or returns an oversized diff;
- workflow is dispatched from a non-master ref.

In every case, reviewed content may influence the advisory model prompt as inert review text but must not gain local execution/import authority in the process that possesses provider credentials.

## 7. Acceptance criteria

1. `cheap-review.yml` and `senior-review.yml` contain no PR-head checkout in the provider-secret job and no later command reconstructs or executes a PR-controlled worktree.
2. Both jobs execute the review scripts and read `AGENTS.md`/spec text from trusted `master` only.
3. Both trusted checkouts use `persist-credentials: false` unless an exact test proves Git credentials are required; the existing API token path remains explicit through environment/API calls.
4. PR metadata and diff still come from GitHub API and the review remains bound to the captured PR head SHA with the existing stale-head footer behavior.
5. A deterministic adversarial test/checker proves that adding `scripts/json.py`, replacing review scripts, or changing authority files in a synthetic/untrusted PR tree cannot affect the Python code executed by the secret-bearing job.
6. The checker fails on the pre-099 vulnerable workflow pattern and passes on the corrected pattern.
7. Tests make zero live provider calls and require no real provider secret.
8. Existing `scripts/cheap_review.py --self-test`, `scripts/manual_review.py --self-test`, spec-status gate, backend tests, frontend tests/build, and other repository-required deterministic gates remain green on the exact implementation head, except gates demonstrably unrelated and already failing on exact base must be reported rather than hidden.
9. No product behavior, API/schema/database state, 092 runtime code, provider policy, cost policy, or merge authority changes.
10. After merge and reconciliation, 092 PR #303 is explicitly resumed as the sole active product implementation front without re-derivation.

## 8. Required deterministic tests

At minimum add one focused test/checker that parses the effective manual review workflows and asserts:

- `workflow_dispatch` remains the only trigger for Cheap/Senior manual review;
- dispatch is master-only;
- checkout ref is trusted `master`, never `refs/pull/...` or a PR-controlled input;
- `persist-credentials` is false;
- no shell step checks out a PR ref after the trusted checkout;
- the executed review entry point is the trusted `scripts/manual_review.py`;
- provider secrets are supplied only to that trusted review step.

Also preserve/extend offline self-tests so a mocked PR metadata/diff path reaches prompt construction without a PR checkout and without network/provider execution.

A source-string assertion alone is not proof if another step can reconstruct and execute untrusted code; the checker must inspect the complete two workflow job definitions relevant to this boundary.

## 9. Secret rotation decision

099 does not assume compromise. The observed fork alone does not expose repository secrets, and the confirmed vulnerable path requires a maintainer to dispatch one of the manual provider reviews against attacker-controlled PR content.

Implementation must record whether repository history/workflow evidence shows such a dispatch occurred on an external/untrusted PR while the vulnerable pattern existed. If no such evidence exists, rotation is not required by this spec. If such evidence exists or cannot be bounded confidently, stop under the security-interruption rule and report exactly which provider/GitHub credential class requires rotation; never print the credential value.

## 10. Rollback

The code change is independently removable, but rollback to the vulnerable PR-head checkout is prohibited while provider secrets remain available to these workflows. Review functionality may instead be disabled safely if the trusted-master path unexpectedly fails.

## 11. Minimum-necessary test

Security criterion: a reviewed pull request must never gain code-execution/import authority in a process holding JarvisOS review-provider secrets.  
Is this work necessary? **Yes.** The current partial file restore leaves untrusted sibling modules available to Python import resolution.  
Can the criterion be achieved with less? **No.** Restoring a growing allow-list of trusted files is not closed under transitive imports. Removing the untrusted worktree from the secret-bearing process is the smallest robust boundary.  
Why not broaden further? The existing trusted review script already fetches PR metadata and diff through GitHub API, so no new service, state store, dependency, credential, or product architecture is necessary.

## 12. Definition of done

- exact-head deterministic gates green;
- acceptance criteria satisfied;
- no current P0/P1 or substantial unresolved security-review finding;
- implementation merged with expected-head guard;
- 099 registry state reconciled to `merged`;
- paused 092/#303 front resumed explicitly at its preserved head/state.