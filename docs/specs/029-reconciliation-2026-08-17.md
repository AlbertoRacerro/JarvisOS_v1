# 029 SETTINGS-1 — post-merge reconciliation (2026-08-17)

## Canonical result

Implementation PR #286 merged as `839265f977d75e68cbb0c3f2f6942ead7fe27d9d` after exact-head CI/build, a separate green browser-proof lane (#287, evidence-only and closed without merge), and peer-builder adversarial exact-head review on product head `8b43e8bc91f7b993d742b72a8bbd65ea572f0792` with no material P0/P1/P2 finding.

The `/settings` product route now exposes only the readiness-authorized mutable AI/budget/provider controls plus secure Scaleway credential mutation over existing backend authority. Credential values are not projected into normal frontend state or diagnostics; writes are bounded, independently locked, followed by canonical reread, and fail closed to an uncertain state when post-mutation ownership cannot be re-established. Legacy diagnostic routes and the 091 Jarvis sidecar composition remain available.

## Scope preserved

No backend/provider/schema/package/workflow/global-visual-identity authority was added by the product implementation. The browser-proof workflow lived only on the evidence branch and was not merged.

## Queue consequence

029 is complete. Per the maintainer decision of 2026-08-17, this reconciliation explicitly stops the previous automatic transition to the old 092 interpretation. The next frontend-beta authority work is a canonical operator-first re-derivation: engineering meaning and actions dominate normal UI; machine identity/debug detail is progressively disclosed; the sidecar becomes fixed Jarvis-over-Properties; Properties becomes a contract-driven engineering editor over a distinct working configuration; deterministic preflight owns blockers; execution-started runs alone enter run history; Jarvis may act on the working configuration only through structured, validated, stale-safe actions; Engineering Data becomes the project-centric projection of the same authority.

Spec 095 owns that re-derivation decision and the ordered downstream slice map. No downstream runtime implementation is authorized by this reconciliation alone.
