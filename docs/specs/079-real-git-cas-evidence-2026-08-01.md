# Spec 079 real local Git CAS evidence — 2026-08-01

## Status and relation to prior evidence

This document extends `079-disposable-proof-evidence-2026-08-01.md` with a second offline proof slice using a real local bare Git repository rather than only the in-memory fake ref model.

It remains **partial proof evidence**. Spec 079 stays `planned`; this document does not establish GitHub-hosted behavior, readiness, implementation authority, provider authority, or an operational grant.

## Updated clean bundle

Prototype source commit inside the disposable local repository:

`5b4afc6619648b83c5859bbd1008fdf931bbf32c`

Updated clean proof bundle SHA-256:

`793d0fb96b68a1fbf1ede6fc5ff7f16f2ff7fd8220a32d49ef1054e3e80ed2c6`

The bundle was exported from the local Git repository without `.git` metadata and all proof runners were executed again from that clean tree.

Evidence file SHA-256 values inside the clean bundle:

- `evidence/proof-report.json`: `a54b9201e2c6ba9a5bd0da0612e00cb35e747f680dfd0ebe7b950163abbd88ca`
- `evidence/cas-stress-report.json`: `2c5272e61a1477a38c47223fa8f628c55131441433706d6088771b316d4e7294`
- `evidence/real-git-cas-report.json`: `41ead2b63ead57426297741eb998f11c12e4d9a9d1afb44984ddf03effe9eeba`
- `evidence/proof-summary.md`: `676127c28bb587fb7a722223727986fbf6cdfebba4365dbef2df68868ed82443`

## Existing fake-model evidence rerun

From the clean archive:

- unit/conformance suite: 20 passed, 0 failed;
- in-memory CAS stress: 100 rounds;
- contenders per round: 32;
- attempts: 3,200;
- winners: 100;
- stale losers: 3,100;
- failed rounds: 0;
- network calls: 0;
- paid calls: 0.

## Actual local bare-Git proof

Runner:

```text
PYTHONPATH=src python scripts/stress_real_git.py
```

The runner created a disposable bare repository with Git 2.47.3 and used real Git plumbing:

- `hash-object` for candidate content;
- `mktree` for candidate trees;
- `commit-tree` for commits with one exact recorded parent;
- `update-ref refs/heads/jarvis-control <new> <old>` for compare-and-swap ref mutation;
- `rev-parse` and `merge-base --is-ancestor` for reconciliation and ancestry checks;
- `fsck --strict` for repository integrity.

Clean-tree result:

- rounds: 50;
- contenders per round: 16;
- total conditional ref-update attempts: 800;
- canonical winners: 50;
- stale losers: 750;
- failed rounds: 0;
- wrong-parent candidate rejected before ref mutation: true;
- bootstrap commit remained ancestor of final canonical head: true;
- simulated lost response reconciled by reading the canonical ref: true;
- `git fsck --strict`: success;
- network calls: 0;
- paid calls: 0.

Each round pre-created 16 distinct direct-child commits from the same current control head and released 16 concurrent conditional `update-ref` operations. Exactly one operation changed the ref in every round; all other stale writers were rejected.

## What this proves

This slice materially strengthens the architecture evidence for the selected control-ref primitive:

1. Actual Git object creation supports the required exact-parent commit shape.
2. Git's old-value conditional ref update provides single-winner compare-and-swap behavior under local concurrent contention.
3. A wrapper can reject commits whose parent is not the recorded control head before mutation.
4. Losing writers do not overwrite the canonical winner.
5. The resulting history remains linear and passes strict object/reference integrity checks.
6. A caller that loses the success response can reconcile by reading the canonical ref rather than blindly retrying.

## What this still does not prove

Local Git behavior is not a substitute for GitHub-hosted proof. The following remain mandatory:

- GitHub REST Git Data API behavior for commit/ref creation and `force=false` under real races;
- installation-token identity, expiry, revocation, and role separation;
- GitHub ruleset, branch-protection, endpoint, path, and bypass-denial tests;
- API timeout, eventual consistency, webhook order, replay, and installation suspension/deletion;
- GitHub PR/check/workflow and human merge/close observation semantics;
- durable publication of the prototype in a separate proof repository;
- real service/database/queue and provider-accounting proof;
- all remaining proof categories and dated readiness evidence listed in the merged full specification.

## Conclusion and blocker

The exact-parent plus compare-and-swap ref approach is viable both in the deterministic model and in real local Git. No contradiction was found in 4,000 total concurrent CAS attempts across the two proof engines.

The next authoritative step cannot be completed with the currently exposed connector capabilities: it requires creation or selection of a separate disposable GitHub repository, installation or configuration of test identities, and permission/ruleset changes. Those actions must not be performed against JarvisOS or the unrelated BlueRev benchmark repository.

Spec 079 therefore remains `planned`.
