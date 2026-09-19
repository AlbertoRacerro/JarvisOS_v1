# Area A file-coverage increment 41

MAPPING_STATUS: IN_PROGRESS
UNACCOUNTED_FILES: >0

## EXPLICIT FILE COVERAGE LEDGER

| path | status | concise role/reason |
| --- | --- | --- |
| `backend/app/modules/ai/egress_authority.py` | READ | External-egress authority for exact prompts and manual/canonical context: deterministic sensitivity floor, approved derivatives, local-only model sanitization, binding/fallback closure checks, post-sanitizer deterministic scan, canonical source snapshot/digest capture, and S0/S1 eligibility projection. |

## Inspection notes

- Re-opened directly and completely from fresh master `240d5e0b27d9837d40f47bddfa24871ae7a2a4bb`; credit is based on actual source inspection, not PR #660 history.
- `authorize_prompt` fails closed for S4, pauses S2/S3 without an approved/local-sanitized derivative, and only defaults marker-free input to S1 in `FAST_DEV`; other policy modes require classification.
- Model-backed sanitization is constrained to an explicitly `local:` route. The resolved primary binding and every configured fallback provider are rejected if network-capable, preventing a sanitizer fallback from becoming external egress.
- Sanitizer output must match the selected provider/model binding, be bounded non-empty text, and survive a deterministic sensitivity scan with no remaining floor before it can become derivative authority.
- Canonical-source sanitization snapshots exact source digests before the local model call and passes those expected digests into derivative approval, so source mutation between read and approval fails closed in the derivative-owner transaction.
- `authorize_manual_context` previews derivative-backed context, pauses if anything is withheld, then re-reads each included approved derivative and checks digest/effective-level continuity. This is a second authority check after preview rather than treating preview JSON as sufficient evidence.
- Cross-area dependency: eligible manual context is enriched through `app.modules.bluecad.evidence_egress`; this Area-A file consumes that enrichment but does not own the BlueCAD implementation.

Canonical Area-A file was not modified in this increment; this additive shard avoids destructive replacement risk while complete canonical-safe replacement is not required for durable progress.
