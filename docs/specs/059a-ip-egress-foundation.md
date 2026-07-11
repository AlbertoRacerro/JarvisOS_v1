# 059a — IP-EGRESS-1A: sensitivity and context foundation

Status: ready; `docs/specs/STATUS.md` is authoritative.

Depends on: 003, 015, 018, 021, 040, 042

Parent definition: `docs/specs/059-ip-egress-1.md`

## Scope

This is the mechanically gateable implementation slice called **059-A** in the
parent definition. It owns only:

- additive digest-bound sensitivity-label storage;
- operator-reviewed sanitized derivatives and source provenance;
- deterministic sensitivity floors and stale-label handling;
- sensitivity-aware context selection and preview manifests;
- tests proving legacy unknown defaults, withholding before serialization,
  derivative provenance, and zero provider calls.

It must not alter provider-adapter invocation, confirmation semantics, fallback
execution, or ticket consumption. Those belong to 059b.

## Merge gate

An implementation PR must declare `**Spec gate:** implementation 059a`, update the
059a registry row to `in_review`, pass deterministic CI, receive a completed Codex
review, and have every finding resolved or explicitly dispositioned before human
merge. The assistant must not merge before that review.

## Completion handoff

After 059a merges, the registry may move 059b from `blocked` to `ready`. No 059b
implementation may start before that state transition.
