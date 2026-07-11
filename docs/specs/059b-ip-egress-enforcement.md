# 059b — IP-EGRESS-1B: packet, ticket, and execution enforcement

Status: blocked until 059a is merged; `docs/specs/STATUS.md` is authoritative.

Depends on: 059a

Parent definition: `docs/specs/059-ip-egress-1.md`

## Scope

This is the mechanically gateable implementation slice called **059-B** in the
parent definition. It owns only:

- canonical exact `EgressPacket` and immutable `EgressDecision` contracts;
- server-owned expiring, digest-bound, single-use confirmation tickets;
- replay prevention and safe ticket consumption;
- enforcement immediately before every concrete external provider/fallback;
- safe egress ledger metadata and mutation-resistant integration tests.

It must reuse the labels, derivatives, and sensitivity-aware context foundation
merged by 059a. It must not create a second provider gateway, MemoryStore,
external-tool runtime, conversation system, provider adapter, or frontend.

## Merge gate

An implementation PR must declare `**Spec gate:** implementation 059b`. The 059b
row may move to `in_review` only after 059a is `merged`; the registry gate must
reject any earlier implementation. The PR must pass deterministic CI, receive a
completed Codex review, and have every finding resolved or explicitly
dispositioned before human merge. The assistant must not merge before that review.

## Completion

Real BlueRev IP/cloud-provider dogfood remains blocked until 059b is merged and the
exact-packet egress boundary is active on the shared execution spine.
