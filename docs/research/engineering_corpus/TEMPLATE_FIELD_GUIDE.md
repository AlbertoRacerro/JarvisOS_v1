# Template v1 Field Guide

## Purpose

A microtopic is the smallest unit that can be explained, verified and assessed without importing an entire chapter. A record must preserve both **what the source says** and **what verification accepts**.

## Atomicity rule

Create a separate microtopic when any of these changes independently: governing equation, assumptions, validity range, boundary conditions, numerical method, source claim, verification verdict, or benchmark target. Do not split mere notation changes.

## Required interpretation

- `provenance` identifies the exact source and location; authority is not truth.
- `definition` is normalized wording, not a copied paragraph.
- `physical_meaning` states what the relation means in engineering terms.
- `assumptions`, `validity_conditions`, and `invalidity_conditions` are mandatory for equations and models.
- `variables` bind symbols to meanings and units.
- `verification_status` describes evidence, not confidence in the source author.
- `benchmark_candidate` is only a proposal until the gold is reproduced independently.
- `jarvis_capability_candidate` separates deterministic authority from AI interpretation.

## Verification ladder

1. `source_transcribed` — faithful extraction only.
2. `dimensionally_checked` — units and dimensions are consistent.
3. `numerically_reproduced` — stated results are recalculated.
4. `cross_source_verified` — derivation or independent reference agrees.
5. `expert_verified` — domain expert approves assumptions and interpretation.
6. `disputed` — evidence conflicts or specification is incomplete.
7. `incorrect` — a claim is falsified by reproducible checks.

## Why v1 is temporary

The pilot showed that record-level provenance and verification are too coarse. Template v2 therefore moves to source claims and claim-level checks.
