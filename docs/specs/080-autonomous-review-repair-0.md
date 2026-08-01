# Spec 080 — AUTONOMOUS-REVIEW-REPAIR-0

**Definition status:** planning kernel; registry remains `planned`.

**Depends on:** 004, 017, 019, 022, 079

## 1. Purpose

Define, separately from scheduled continuation, a removable capability that can request an implementer review, represent current findings, authorize bounded correction on the same PR branch and request a re-review.

080 exists because continuation and review/repair have different authority, state and rollback boundaries. Removing 080 must leave the daily continuation implemented by 079 intact.

## 2. Candidate scope

- exact-head review request;
- normalized finding identity and severity;
- open, fixed, rebutted, superseded and stale dispositions;
- implementer/reviewer role separation;
- bounded fix and re-review rounds;
- deterministic gates before every review;
- no automatic merge.

## 3. Explicit non-goals

- scheduled continuation;
- selecting or authorizing a new spec;
- merge or auto-merge;
- new provider accounts or credentials;
- hidden state outside GitHub;
- unbounded review loops;
- treating model findings as authority;
- combining this spec back into 079.

## 4. Test del minimo necessario

080 is not required to satisfy 079's continuation acceptance criterion. It is therefore not implemented as part of 079. Promotion requires a separate demonstrated need and a separate minimum-necessary test.

## 5. Promotion blockers

Before full specification:

1. prove whether existing Codex PR comments provide reliable same-branch repair without a new credential;
2. choose a deterministic representation for unresolved review threads using GitHub's available APIs;
3. define maximum rounds and no-progress termination;
4. define how exact-head CI and review evidence become stale;
5. preserve advisory review and agent-owned merge only after deterministic gates are green and no current findings remain.
