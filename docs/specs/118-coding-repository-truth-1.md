# 118 CODING-REPOSITORY-TRUTH-1 — full specification

Exact source master: `83922aeaa8a52291a56c0b5e2ec6d6b2676e81cb`.

Authority: full specification only. `STATUS.md` remains `planned`; implementation is not authorized until a separate readiness decision proves this design against fresh exact master.

## Purpose

Provide one server-side, read-only, exact-ref repository-truth seam for the Coding lane. The seam owns remote repository/ref/SHA/branch/PR/check/review truth, bounded Repository Inspector search/preview, and exact safe GitHub URLs. It must not become a generic GitHub proxy, repository writer, workflow/merge actor, local-checkout owner, or second canonical repository store.

## Accepted capabilities

The first implementation SHALL expose only these operation families for configured/authorized repositories:

1. `repository_ref_truth` — repository identity, requested ref, exact resolved commit SHA, branch/tag/ref metadata needed to prove what was inspected.
2. `commit_truth` — bounded immutable commit metadata for an exact SHA.
3. `path_list` — bounded tree/directory listing at an exact SHA.
4. `file_preview` — bounded file/blob preview at an exact SHA/path, with binary/invalid-text/oversize outcomes explicit rather than coerced.
5. `literal_search` — bounded literal/path/identifier repository search; no semantic/vector index and no arbitrary query language.
6. `compare_truth` — bounded exact-base/exact-head compare metadata and patch summary sufficient for Coding inspection, with truncation/partial state explicit.
7. `pull_request_truth` — PR identity/state plus exact head/base refs and SHAs.
8. `check_truth` — bounded status/check/workflow-result projection associated with the exact PR/head SHA; stale-head results are never represented as current.
9. `review_truth` — bounded review/submission/thread-state projection needed to distinguish approved, changes-requested, unresolved, unavailable, or stale review evidence; model text is never review authority.
10. `safe_github_url` — server-derived HTTPS GitHub URL for an already-authorized repository/ref/path/PR/commit target. Arbitrary user/model URLs are not accepted as authority inputs.

No operation outside this allowlist is accepted by this slice.

## Ownership and architecture

### Backend ownership

Create one cohesive backend Coding repository-truth boundary rather than a generic provider framework. The planned implementation owner is a new narrow module under `backend/app/modules/coding/` because fresh exact-master inspection found no existing first-party Coding repository module or reusable GitHub transport owner that already satisfies this complete boundary.

The module SHALL contain:
- typed request/result/failure contracts for the operation allowlist;
- deterministic repository/ref/path/size/pagination/redirect checks before dispatch;
- one GitHub-specific read transport adapter;
- one service entry point that binds every successful result to configured repository identity and exact resolved SHA;
- no durable repository mirror, cache, index, mutation queue, planner, or second authority registry.

Any implementation file split is readiness-authorized only when it preserves one conceptual owner and does not introduce manager/factory/facade indirection without an authority or test need.

### API ownership

Expose repository truth only through backend-owned Jarvis/Coding read/context surfaces that already preserve `111` READ/CONTEXT separation. Frontend code may request bounded projections through JarvisOS backend APIs but MUST NOT call GitHub directly or receive provider credentials.

### Configuration and credentials

Repository identity and provider host are server-owned configuration. Initial provider is GitHub only.

- Host allowlist: exactly `api.github.com` for API reads and `github.com` only for generated human-facing URLs; redirects to any other host fail closed.
- Repository allowlist: explicit configured `owner/name` identities; no wildcard owner, arbitrary URL, or model-selected repository.
- Authentication: public repositories MAY use unauthenticated reads where provider limits permit. Private-repository support MAY use one existing server-side secret/config seam only if readiness proves it exists and can hold a least-privilege read credential. No credential creation, installation, or broader permission is authorized by this spec.
- Credentials are never logged, returned, embedded in generated URLs, persisted in repository-truth results, or exposed to model/frontend payloads.

If fresh readiness evidence cannot prove a lawful least-privilege private-repository credential seam, the initial implementation SHALL support configured public repositories only rather than introduce a new secret system.

## Exact-ref contract

Every material read follows this sequence:

1. validate provider host and configured repository identity;
2. validate operation and operation-specific bounds;
3. resolve mutable ref input to an immutable commit SHA through the same authorized repository;
4. perform the requested read against that exact SHA where GitHub supports exact-ref addressing;
5. return repository identity, requested ref if any, resolved SHA, operation-specific provenance, and completeness state;
6. for PR/check/review reads, independently bind returned head/base SHAs to the PR and mark evidence stale when the expected/current head no longer matches.

A branch/tag/ref string alone is never a successful truth result.

## Path and URL safety

Repository paths are normalized as provider repository-relative POSIX paths and rejected when they contain or decode to traversal or ambiguous escape forms. At minimum reject:
- absolute paths;
- `..` traversal segments;
- percent-encoded traversal or separators that change normalization;
- NUL/control characters;
- backslash-based alternate traversal;
- paths outside configured operation bounds.

Symlink/submodule/LFS/archive/download indirection is represented as metadata/unsupported content unless the exact target remains inside the configured repository and accepted operation. This slice does not follow arbitrary provider download URLs.

Generated GitHub URLs are constructed from validated repository identity and already-resolved/validated identifiers. No arbitrary URL fetcher is exposed.

## Deterministic bounds

Readiness must freeze concrete numeric limits; implementation must centralize them and tests must prove enforcement. The initial readiness candidate should prefer conservative limits:
- file preview bytes: 256 KiB maximum decoded payload;
- aggregate response body: 1 MiB per operation unless a smaller operation-specific limit applies;
- directory/tree entries: 1,000 maximum;
- literal-search matches: 100 maximum;
- compare files: 100 maximum and patch bytes bounded by aggregate response limit;
- PR/check/review items: 100 maximum per collection;
- pagination: at most 10 pages and never silently partial;
- connect/read timeout: deterministic finite values, no unbounded wait;
- retry: zero or one bounded retry only for explicitly transient provider failures; never retry authorization, validation, stale-ref, or oversize failures.

If provider data exceeds a bound, the operation returns a typed `partial`/`oversized` failure/result state; callers may not interpret it as complete.

## Typed results and failures

Successful result envelopes include at minimum:
- provider=`github`;
- configured repository identity;
- operation;
- requested ref when supplied;
- exact resolved SHA(s);
- observed provider identifiers relevant to the operation;
- completeness/truncation state;
- bounded payload;
- observation timestamp as metadata only, never freshness authority by itself.

Typed non-fabricating failures distinguish at least:
- unauthorized repository;
- unsupported provider/host/operation;
- invalid or forbidden ref/path;
- missing repository/ref/path/PR;
- stale/moved ref or stale PR head;
- authentication/authorization failure;
- rate limited/provider unavailable/timeout;
- malformed or inconsistent provider response;
- redirect/host escape;
- binary/unsupported content;
- oversized/partial result.

Provider errors never fall back to guessed data, cached-as-current truth, alternate hosts, or model claims.

## Untrusted content handling

Repository content, commit messages, PR text, reviews, patches, and search matches are untrusted data.

The implementation MUST NOT:
- execute, import, eval, shell, build, run hooks, dispatch workflows, or invoke repository-controlled scripts;
- interpolate content into shell commands;
- grant repository content authority over routing, credentials, tools, merge, review, or canonical state;
- treat prompt-like repository text as instructions.

Text previews are bounded data. Binary or invalid UTF-8 content returns typed metadata/unsupported preview rather than lossy implicit execution-oriented decoding.

## PR / checks / reviews freshness

For PR-related truth:
- PR metadata returns exact current provider-reported base/head SHAs;
- check/review evidence MUST include the SHA it actually evaluates where available;
- a caller-supplied expected head mismatch produces stale evidence, not approval/current state;
- terminal workflow success alone is not semantic review approval;
- review projection preserves reviewer identity, state, commit/head association when available, and unresolved-thread state needed by later pipeline slices;
- this slice does not decide whether a PR may merge; it only returns bounded exact evidence for `120` and later policy owners.

## Search / preview boundary

Repository Inspector search is deliberately literal and bounded. It may search provider-supported code/path text only within an authorized repository and exact ref/SHA. No embeddings, vector DB, semantic index, fuzzy autonomous crawl, local clone, or second repository database are created.

Preview returns exact repository/ref/SHA/path/blob provenance whenever provider evidence supplies it. Search hits that cannot be tied to the accepted exact repository/ref evidence are rejected or marked incomplete/stale.

## Safe GitHub URL derivation

The backend may derive exact human-facing HTTPS links for authorized repository identities and validated commit/PR/path targets. These URLs are display/navigation artifacts only. They grant no provider authority and are never subsequently trusted without revalidation.

## Jarvis integration boundary

Under merged `111`, repository-truth results may become READ/CONTEXT evidence after deterministic validation. They do not themselves become COMMIT/EXECUTE capability and cannot mutate canonical domain state. Later `123` may consume these projections for inspect/explain/suggest flows, but modification remains proposal-only under its own accepted authority.

## No-write proof

The implementation surface must contain no mutation operation and tests must prove that write-capable provider methods/endpoints are unreachable through the accepted operation dispatcher. At minimum reject create/update/delete file/ref/branch/commit/issue/PR/review/label/workflow/release/settings/secret/merge/dispatch operation names before network dispatch.

## Deterministic test matrix

Readiness must map implementation tests covering at least:
1. unauthorized repository and host rejected before network dispatch;
2. arbitrary URL and redirect to alternate host rejected;
3. mutable ref resolved to exact SHA and returned payload bound to it;
4. moved/stale ref cannot be represented as current exact evidence;
5. traversal, encoded traversal, absolute/backslash/control-character paths rejected;
6. oversize file/tree/search/compare/PR/check/review responses fail or mark partial deterministically;
7. binary/invalid UTF-8 preview does not fabricate text;
8. provider timeout/rate-limit/auth/malformed response remain typed;
9. credential value absent from logs/results/generated URLs;
10. PR truth returns exact head/base SHA;
11. check evidence for an old PR head is stale rather than current;
12. review evidence does not treat workflow success as semantic approval;
13. literal search is bounded and exact-repository/ref scoped;
14. generated GitHub URLs use only validated authorized identifiers;
15. every write-capable operation is rejected before dispatch;
16. repository content cannot trigger execution/workflow/tool authority;
17. frontend/model-visible payload contains no token/provider credential;
18. successful READ/CONTEXT use preserves `111` separation and grants no COMMIT/EXECUTE authority.

All tests are offline with fake/mocked provider transport; no live GitHub call or paid provider use is required.

## Planned implementation surface for readiness verification

Readiness SHALL revalidate exact master and freeze the smallest concrete file set. Candidate scope:
- one new bounded backend module under `backend/app/modules/coding/` for contracts/service/GitHub read adapter;
- minimal backend configuration addition only if required for authorized repository identity and optional read credential reference;
- minimal API/Jarvis projection wiring needed to expose the accepted read operations;
- focused backend tests plus any deterministic repository egress/static-owner fixture required by current canonical gates;
- no frontend work unless the current frontend contract cannot consume the existing Jarvis read/context projection without a bounded type addition.

A new database table, migration, local clone, durable cache/index, generic SCM provider abstraction, background worker, queue, planner, second mutex, merge bot, or direct frontend GitHub client is explicitly prohibited unless a future accepted specification authorizes it.

## Acceptance criteria

`118` may become `ready` only when fresh exact-master readiness proves:

1. the complete accepted operation allowlist covers repository/ref/SHA/PR/check/review truth, bounded literal/path/identifier search/preview, compare evidence needed by Coding, and exact safe GitHub URLs;
2. every result is bound to explicit authorized repository identity and exact SHA evidence;
3. arbitrary hosts/repositories/URLs, traversal/redirect/provider-indirection escapes fail closed before sensitive dispatch;
4. credential mode is least-privilege, server-owned, redacted, and no new credential/account is required unless explicitly human-provisioned later;
5. repository content remains non-executable untrusted data;
6. numeric payload/pagination/time/retry limits are frozen and deterministically testable;
7. stale ref/head, partial result, provider failure, unsupported content, authorization failure, and missing data are typed/non-fabricating;
8. PR/check/review truth has exact-head semantics sufficient for downstream `120` without granting merge/review authority;
9. `111` READ/CONTEXT separation is preserved and no operation grants COMMIT/EXECUTE;
10. the concrete implementation file/test plan is the smallest sufficient owner and adds no duplicate repository truth/index or generalized SCM framework.

## Non-goals

- Any repository mutation or branch/commit/PR/issue/review/label/workflow/release/settings/secret write.
- Merge, auto-merge, deployment, CI dispatch, restart/update/self-update, patch application, local checkout orchestration, shell/PTY or code execution.
- Semantic/vector repository indexing or durable mirror/cache as canonical truth.
- Generic multi-provider SCM abstraction.
- Runtime/deployment truth owned by `119`, pipeline-state policy owned by `120`, or coding modification actions owned by `123`.
- Ruff autofix, CI digest, or unrelated governance/tooling work.

## Minimum-necessary conclusion

The smallest sufficient design is one GitHub-specific, server-owned, read-only bounded repository-truth seam with explicit operation allowlist and exact-SHA provenance. A general SCM framework, new store, local clone, background orchestrator, or frontend provider client is unnecessary and therefore forbidden by this slice.