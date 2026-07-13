# Post-101 059b lifecycle gate correction

## Problem

PR #101 correctly reconciled ADR-059 lifecycle wording, but one sentence in the
parent 059 definition still creates a circular gate by saying implementation work
cannot begin until that same implementation has merged.

## Required correction

- 059b implementation work may begin only after its full implementation spec is
  reconciled and the canonical registry explicitly promotes it to `ready`.
- Policy-autopilot runtime activation and real external execution remain blocked
  until the implementation PR is reviewed and merged.
- No sensitivity, sanitization, packet, trigger, budget, confirmation, audit, or
  authority policy changes.

## Scope

Exactly two docs/report files:

- `docs/specs/059-ip-egress-1.md`;
- this report.

No runtime, schema, workflow, provider, frontend, test, STATUS, AGENTS, DECISIONS,
or merged 059a implementation change.
