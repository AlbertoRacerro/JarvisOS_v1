# Semantic review race policy

Status: canonical operational process amendment
Effective date: 2026-09-06
Maintainer authorization: explicit

## 1. Purpose and precedence

This amendment removes external-model review latency from the critical path while preserving semantic scrutiny, exact-head correctness, deterministic gates, and required real-environment evidence.

For repository-development semantic-review mechanics, this document supersedes only conflicting review-order/quorum clauses in:

- `docs/AGENT_EXECUTION_AND_AUTOMATION_PROTOCOL.md`, especially sections 6, 10A, and 12;
- `docs/POST_112_PARALLEL_DELIVERY_PROFILE.md`, especially section 3 and 3A.

All non-conflicting rules in those documents remain unchanged. This amendment changes repository-development review mechanics only. It grants no product/runtime/provider/credential/filesystem/merge authority, does not alter `docs/specs/STATUS.md`, does not make `planned` implementation-ready, and never weakens an explicit deterministic, browser, hardware, human, or real-environment acceptance gate.

## 2. Review race

Whenever a material exact head requires semantic review:

1. The active ChatGPT coordinator immediately performs a severe adversarial review of the exact head. It inspects the exact diff, accepted scope, relevant owners/invariants, tests, and failure modes and tries to falsify the acceptance criteria rather than merely confirming them.
2. Claude and Codex are requested concurrently on that same exact head when no current-head request/result already exists. Do not wait for one before launching the other.
3. All semantic reviewers receive the same substantive review family: accepted scope only; P0/P1 first; security, authority, credential, filesystem, Git/CAS, egress, data-loss, correctness, and acceptance regressions as applicable; useful P2 classification; no cosmetic or unrelated expansion.
4. If any reviewer finds a P0/P1, it performs exactly one bounded causal-sibling sweep of the same failure family/directly adjacent accepted-scope paths and consolidates the findings. The sweep does not recurse.
5. Review latency is never a reason to idle. While external verdicts are pending, builders perform useful same-slice work such as independent adversarial review, exact repair preparation, failure-mode/test analysis, or read-only implementation workpack preparation.

## 3. Normal semantic-review completion

The semantic-review gate is satisfied on one unchanged exact head when all of the following hold:

- at least one consumable exact-head PASS has arrived from either Claude or Codex;
- at least one exact-head ChatGPT builder PASS exists;
- there is no unresolved P0/P1, blocking P2, substantial reviewer disagreement, or violated accepted-scope requirement.

The first qualifying external PASS plus builder PASS is sufficient. Do not wait for the slower external reviewer. If a later external P0/P1 or blocking P2 arrives before merge, consume it and the gate becomes unsatisfied until repaired/re-reviewed.

## 4. Bounded degraded builder quorum

External reviewer availability is valuable for diversity but cannot create an indefinite distributed lock.

If all of the following are true:

- the exact head has not changed;
- Claude and Codex were both requested for that exact head;
- neither has produced a consumable verdict;
- two subsequent scheduled Builder A/B/C/D wake-ups have occurred after the first current-head external requests;

then external latency stops blocking the semantic-review gate.

The degraded semantic-review gate is satisfied only by:

- PASS verdicts from two distinct Builder A/B/C/D sessions on the same exact head;
- at least one of those PASS verdicts coming from a builder/session that did not perform the last material mutation;
- both verdicts being severe adversarial reviews of exact diff + relevant accepted context rather than workflow-green assertions;
- no unresolved P0/P1, blocking P2, substantial disagreement, or failed required acceptance criterion.

A single builder can never self-certify its own material change. Two labels emitted by the same review session do not form quorum. Head mutation invalidates the affected review evidence and restarts the exact-head review race.

Where practical, an independent builder forms its initial verdict before reading another builder's verdict to reduce anchoring.

## 5. Evidence that review can never replace

Semantic review, including degraded quorum, never substitutes for evidence whose truth depends on execution or environment. Required evidence remains mandatory, including as applicable:

- deterministic tests and CI gates;
- exact-head status/registry checks;
- real-browser/Playwright acceptance proof;
- hardware/local-host activation evidence;
- live integration evidence explicitly required by an accepted spec;
- required human-controlled action or credential/account existence;
- exact remote-head/CAS and post-mutation verification.

Green workflows do not by themselves establish semantic PASS, and semantic PASS does not fabricate missing runtime/browser/hardware evidence.

## 6. Merge interaction

A material PR may merge only when the current exact head satisfies:

1. authorized diff and accepted scope;
2. required deterministic and real-environment gates/proofs;
3. the semantic-review gate under section 3 or, when eligible, section 4;
4. no P0/P1 or blocking P2 and no unresolved substantial disagreement;
5. all existing secret, spending, dependency, schema, provider, authority, registry, expected-head/CAS, and no-auto-merge rules.

Any head mutation invalidates affected review and proof evidence exactly as before.

## 7. Telemetry and reassessment

For review-race decisions, record enough durable evidence to reconstruct:

- when the current-head external requests were made;
- which reviewer produced the first consumable verdict;
- whether degraded builder quorum was used;
- the identities of the two distinct builder sessions when degraded quorum was used;
- whether any later external reviewer found a material defect missed by the earlier accepted review set.

Use these observations to reassess the latency window and reviewer mix later. Do not turn reviewer telemetry into a new product store or queue.

## 8. Current recovery queue

The policy applies immediately to the maintainer-prioritized recovery sequence `141 -> 142 -> 124 -> 113 -> 140` and is the default semantic-review mechanic for subsequent repository-development work unless a narrower accepted spec explicitly requires a stronger independent-review arrangement or the maintainer amends this policy.

Narrower explicit evidence requirements remain stronger. In particular, browser proof required by 142/124/113/140 is not waivable through this policy.
