# 124 PROVIDER-SETTINGS-GENERIC-1 — READINESS AMENDMENT — 2026-09-07

Status: bounded readiness amendment to `docs/specs/124-readiness-2026-09-06.md` for the already-open implementation PR #559. This document changes authority only; it does not change `docs/specs/STATUS.md`, product behavior, or the accepted browser-proof gate.

Fresh amendment basis: exact `master` `44ae6d5e8aeab42310ce34fcd45ef1d10cef7bee`, with exact PR #559 head `18f2ee1f1ad23c56a74a30f239005575712ee97e` revalidated against the accepted 124 full specification and merged readiness.

## Fresh trigger

Fresh remote review of exact PR #559 head `18f2ee1f1ad23c56a74a30f239005575712ee97e` found that the provider-settings projection can disagree with the canonical execution gate when global and provider caps are simultaneously exhausted, and cannot truthfully project availability/blocking for a non-active provider. The accepted full spec already requires usage/budget/policy/status projection to delegate to existing accounting/egress owners rather than recompute a second truth.

The 2026-09-06 readiness froze an exact product-code touch set that omitted `backend/app/modules/ai/egress_persistence.py`. The reviewed repair requires a read-only projection from that canonical owner; implementing equivalent blocker/accounting logic only in `settings.py` would duplicate authority and preserve the drift failure. Therefore the omission is a readiness-boundary defect, not authorization to approximate the owner elsewhere.

## Narrow authority amendment

The permitted product-code touch set is extended by exactly one path:

- `backend/app/modules/ai/egress_persistence.py` — only to expose a side-effect-free, read-only projection of the canonical egress/accounting decision already used for real attempts, including existing blocker precedence, canonical ledger spend/reservations, credential/provider enablement, and global/provider caps.

This amendment authorizes no other unlisted product-code or gate-wiring path.

The read projection MUST reuse/delegate to the existing canonical egress/accounting decision logic. It MUST NOT duplicate blocker ordering or accounting formulas in a second owner, and MUST NOT change the semantics or precedence of the existing execution path. It MUST NOT persist an attempt, reservation, provider snapshot, credential, policy state, or accounting state; expire or otherwise mutate existing reservations as a side effect of a read; dispatch provider traffic; consume a budget; mutate credentials; expose provider credentials/raw secret references; add a provider adapter/SDK; create a new route; or widen provider-test authority.

`backend/app/modules/ai/settings.py` and `GET /ai/provider-settings` remain projection consumers only. Existing egress/accounting ownership remains unchanged.

## Required causal evidence

Before #559 can be treated as frozen for final review, exact-head deterministic evidence must additionally prove:

1. simultaneous global-cap and provider-cap exhaustion reports the same canonical blocker precedence as the real egress execution gate;
2. a provider that is not the active `provider_mode` receives its own owner-derived availability/blocking state, including provider-cap exhaustion;
3. the read projection performs no attempt/reservation persistence, reservation expiry/mutation, or provider dispatch;
4. the existing execution path retains its accepted blocker ordering and side effects unchanged;
5. the existing 124 redaction, credential-axis, secure-storage, DeepSeek-smoke, frontend, and normal repository gates remain green.

The accepted exact-head real-browser `/settings/ai` proof remains mandatory after material repair and is not replaced by this amendment.

## Preserved stop conditions

This amendment does not authorize a new accounting/policy/health authority, generic credential persistence, generic live provider testing, direct browser/provider egress, new provider adapters/storage, a frontend test framework, or any unrelated Settings redesign. If the P1 family cannot be closed with the single read-only canonical-owner seam above plus the already-frozen 124 surfaces, stop for fresh authority rather than widening again.
