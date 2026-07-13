# 062 — GRADE-0: graded AI outcomes for empirical routing

Status: planned; this is a kernel, not an implementation-ready spec.

Depends on: 021, 059b

## Problem

JarvisOS records calls and usage but lacks a compact operator outcome signal.
Without graded dogfood evidence, route promotion remains speculative and cost
comparisons cannot distinguish cheap useful calls from cheap rework.

## Maintainer direction

Add one graded outcome to `ai_jobs`, settable from the UI in one click and from a
backend API:

- `useful`;
- `partly`;
- `rework`;
- `failed`;
- optional bounded note.

The grade is operator/evaluation evidence, not provider truth and not a model
permission. A model may suggest a grade only as an untrusted proposal.

## Required future contract

A full spec must define:

1. additive schema fields, allowed transitions, actor, timestamp, and note bounds;
2. API read/write contracts and workspace/job authorization assumptions;
3. idempotent update behavior and audit events;
4. one-click UI behavior without optimistic false persistence;
5. treatment of provider errors, partial responses, continuations, and fallbacks;
6. export/query shape for routing evaluation;
7. deterministic tests for invalid grades, stale updates, and audit provenance.

## Link to spec 025

After enough representative graded dogfood data exists, spec 025 may build a
deterministic route-per-task-kind policy table selected on
cost-per-useful-outcome. The table is server policy. The local classifier remains
advisory and cannot select providers or authorize execution.

The data threshold, task-family coverage, holdout method, promotion/reversion
criteria, and minimum useful sample size must be specified before 025 becomes
ready. No routing change may be justified by aggregate grade counts alone.

## Non-goals

No automatic self-grading authority, reward-model training, provider leaderboard,
autonomous route mutation, external analytics service, or frontend redesign.

## Promotion evidence

Before this row becomes `ready`, inspect the current `ai_jobs` schema/API and
freeze the smallest additive grade contract that supports 025 without creating a
parallel evaluation database.
