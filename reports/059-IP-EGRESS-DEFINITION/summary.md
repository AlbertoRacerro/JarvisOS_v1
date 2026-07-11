# 059 IP-EGRESS definition reconciliation report

## Scope

This is a documentation-only pre-implementation audit for spec 059. It changes no
backend runtime, database schema, provider adapter, route, confirmation endpoint,
context builder, frontend, workflow, corpus, runner, CAD, mesh, or FEM behavior.

Base commit: `4ae612a4aedec37608970ab8c2c67ab5ba454317`.

## Runtime seams inspected

- shared provider execution spine in `backend/app/modules/ai/execution.py`;
- provider/budget Alpha Gate in `backend/app/modules/ai/budget.py`;
- explicit and Auto routing in `gateway.py` and `routing/bridge.py`;
- context-block validation, workspace packs, FTS/LIKE selection, and preview;
- Domain Foundation and MemoryStore record models/schema;
- provider contracts and privacy-class vocabulary;
- current escalation proposal and confirmation path;
- smoke/probe sensitivity floors and local-classification non-authority rules;
- canonical ADRs and existing specs 003, 015, 018, 021, 040, and 042.

## Findings

1. **The Alpha Gate is not an IP-egress gate.** It correctly owns provider,
   credential, usage, and budget state, but it has no exact-packet sensitivity,
   provenance, derivative, or confirmation binding.
2. **Context has no authoritative sensitivity metadata.** Caller blocks contain
   only source/content/type/id; workspace packs select accepted records without a
   policy-owned label or withheld-source manifest.
3. **Existing project and MemoryStore rows are unlabeled.** Silently treating
   legacy rows as public/internal would create an external-leak path.
4. **The execution spine can call a network adapter without an egress decision.**
   `AIRequest.privacy_class` exists, but the current request construction does not
   supply a final server-owned class.
5. **The current confirmation path trusts client proposal content.** It reloads
   neither a server-owned packet nor a one-use authorization; route, text, and
   token limit are read from the request proposal object.
6. **Historical sensitivity logic is fragmented.** Smoke/probe floors and the
   local classifier are useful evidence, but they are not one production
   boundary. Model sensitivity remains advisory by contract.
7. **Sensitivity must filter before prompt serialization.** Filtering after pack
   assembly or after `AIRequest` construction is too late to prove withheld
   content never entered the outbound packet.

## Frozen decisions

- Canonical five-level scale: S0 public, S1 internal, S2 confidential, S3
  sensitive IP, S4 secret; unknown is fail-closed.
- Persist labels in an additive digest-bound sidecar instead of adding duplicated
  columns to every record table.
- Legacy unlabeled or stale-labelled records are unknown for external use.
- S2-S4 sources are never downgraded in place. Lower-level material is represented
  by a new operator-reviewed sanitized derivative with preserved source digests.
- Structural secret scanning is mandatory but is not represented as proof of
  semantic IP removal.
- Context selection emits separate included and withheld manifests and never
  returns withheld bodies in external preview/output.
- Every network attempt requires an exact canonical EgressPacket and immutable
  EgressDecision in addition to the existing Alpha Gate decision.
- Confirmation becomes server-loaded, digest-bound, expiring, and single-use.
  Client-supplied outbound text or route data cannot authorize execution.
- Fallback targets are fixed in the ticket and rechecked per concrete binding.
- Safe ledger metadata contains digests, levels, counts, ids, and reason codes;
  not prompt/source/secret bodies.

## Delivery

- **059-A:** sensitivity labels, sanitized derivatives, deterministic floors,
  stale-digest handling, and sensitivity-aware context preview/selection.
- **059-B:** canonical packet/decision, server-owned ticket, confirmation replay
  prevention, and per-binding execution-spine enforcement.

059-A must merge before 059-B begins. Neither slice adds a provider, external-tool
runtime, conversation history, vector retrieval, automatic redaction, or frontend.

## Review and merge gate

- This definition PR requires a completed Codex review.
- Review findings must be read and resolved or explicitly dispositioned.
- The assistant must not merge this or either implementation PR before that gate.
- CI green is necessary but not sufficient; final merge authority remains human.

## Residual risks carried into implementation

- A normalized `<kind>:<id>` resolver and exact record-content digest contract must
  be proven against every source kind used by 059-A.
- Atomic allow-once consumption must be strong enough to prevent ordinary replay
  in the local SQLite deployment model.
- Sanitized derivative approval remains a human judgment; automated tests can
  prove provenance and structural constraints, not semantic completeness.
- Existing external smoke/supervisor paths must be audited during 059-B so no
  network adapter remains outside the shared enforcement spine.
