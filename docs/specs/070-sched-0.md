# 070 — SCHED-0: policy scheduler

Status: planned; this is a kernel, not an implementation-ready spec.

Depends on: 021, 066, 068

## Problem

An OS is defined by what it does unattended, but JarvisOS has no policy-owned
way to run recurring jobs: nightly memory consolidation (069), a morning
briefing, flowsheet stale checks, a weekly local-model bench. Hermes' own cron
is deliberately disabled by 068, and any ad-hoc OS-level task scheduler outside
JarvisOS would launch work that bypasses policy, budget, and audit.

## Maintainer direction

A deterministic, SQLite-backed schedule (job kind, cadence, scope, per-job
budget, enabled flag) owned by the policy kernel. Jobs either launch a Hermes
run through the pinned 068 profile and the 066 passthrough, or trigger an
internal deterministic task; either path is bound to `run_ai_task`/`ai_jobs`
exactly like any other AI call. Every firing writes ledger events in order:
`scheduled` -> `started` -> outcome. No resident daemon is assumed. The kernel
defines a single idempotent "tick" entrypoint; an OS-level trigger (an existing
launcher script, a Windows scheduled task, or equivalent) invokes that
entrypoint, and the kernel — not the trigger mechanism — owns catch-up and
missed-tick semantics.

## Required future contract

A full spec must define:

1. schedule table shape (job kind, cadence, scope, per-job budget, enabled
   flag) as an additive migration;
2. tick-endpoint idempotency and overlap/lock semantics — two ticks firing
   close together, or a slow tick still running when the next external
   invocation happens, must not double-run a job;
3. catch-up policy after downtime (e.g. missed nightly ticks): run once, skip,
   or bounded backfill, decided explicitly per job kind, not assumed;
4. per-job budget and scope binding, reusing existing budget/scope mechanisms
   rather than a second accounting path;
5. Hermes job launch contract: which pinned 068 profile, how correlation ids
   flow into the resulting `ai_jobs` row, and how a scheduled job is
   distinguishable from a manually triggered one in the ledger;
6. failure/retry/backoff bounds per job kind, with a hard ceiling so a broken
   job cannot retry unboundedly;
7. observability: schedule state and each tick's outcome must be visible
   through existing event/audit surfaces, not a new dashboard;
8. deterministic tests using a fake clock — no test may depend on wall-clock
   sleep or a real scheduled-task/cron facility.

## Authority boundary

The scheduler triggers work; it owns no content decisions. Every job it
launches still passes through all existing gates (budget, egress autopilot,
promotion) exactly as if invoked manually. Hermes never self-schedules — 068's
disabled cron/proactive paths stay disabled, and this kernel does not reopen
them.

## Non-goals

No resident background worker (this remains a standing non-goal until a
separate spec proves otherwise), no second job-runner framework beyond
existing runner/job patterns, no Hermes-owned cron, no distributed or
multi-machine scheduling, no UI beyond a bounded list/enable-disable view.

## Promotion evidence

Before this row becomes `ready`:

1. pick the smallest OS-trigger mechanism (reuse an existing launcher script or
   a single documented scheduled-task registration) rather than inventing a
   scheduling service;
2. prove a missed or overlapping tick cannot double-run a job (concurrent-tick
   or catch-up test against the fake clock);
3. prove a scheduled Hermes job produces the same `ai_jobs`/ledger evidence
   shape as a manually triggered one, distinguishable only by origin metadata.
