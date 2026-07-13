# 073 — MEASUREMENT-0: as-measured records

Status: planned; this is a kernel, not an implementation-ready spec.
Trigger-gated — do not draft the full spec until a physical prototype produces
real measurements.

Depends on: 001, 040, 051

## Problem

The digital twin only closes when as-designed values can be compared against
as-measured reality. Today no record family exists for measurements at all, so
there is nothing to diff the design against once hardware exists.

## Maintainer direction

A measurement record family mirroring the 001 parameter shape (units,
uncertainty, instrument/source provenance, timestamps). A deterministic
as-designed vs as-measured diff reuses the 050/051 flowsheet dependency graph
and stale-propagation mechanism rather than a second comparison engine.
Threshold alarm rules are deterministic thresholds only; a fired alarm writes
a ledger event and surfaces through existing notification surfaces (and
through Hermes messaging once 068 allows it, not before). Manual entry is the
first import path; file-based telemetry import is second, and both remain
bounded, deterministic ingestion — not a live sensor feed.

## Required future contract

A full spec must define:

1. the measurement record schema (mirroring 001's unit/uncertainty/provenance
   fields) as an additive migration;
2. linkage from a measurement to the parameter/requirement it evaluates;
3. diff semantics: how tolerance/uncertainty from the requirement record
   combines with measurement uncertainty to decide match/mismatch, reusing
   051 stale-propagation rather than a parallel recompute path;
4. alarm-rule shape — deterministic thresholds only, no learned or adaptive
   rule;
5. import format bounds for the file-based telemetry path (accepted formats,
   size/time limits, rejection behavior for anything outside them);
6. deterministic test fixtures; no dependency on a real instrument, sensor
   feed, or live import source in tests.

## Authority boundary

Measurements are evidence, not automatic truth: a mismatch marks the
corresponding designed value stale or contradicted via the existing
stale-propagation mechanism, but never silently overwrites it. This kernel
carries no actuation of hardware, under any condition, ever.

## Non-goals

No streaming telemetry infrastructure, no dashboards beyond existing views, no
control loops, no ML-based anomaly detection.

## Promotion evidence

Before this row leaves `planned` and drafting begins in earnest:

1. the trigger itself: a physical prototype exists and has produced a first
   real measurement set;
2. the chosen file-based import format, picked from what that prototype's
   instrumentation actually emits rather than assumed in advance.
