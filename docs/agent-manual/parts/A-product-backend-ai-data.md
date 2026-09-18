# Area A — Product backend / AI / data / context

MAPPING_STATUS: IN_PROGRESS
UNACCOUNTED_FILES: >0

## Capability map increment — Jarvis exact-context contracts
`backend/app/modules/ai/jarvis_context_models.py` freezes canonical route-id/path pairs and defines strict exact-reference identity: each context ref must carry at least one version, revision, immutable ref, or SHA-256 content digest. Non-current resolutions are forbidden from exposing content. Context requests cap selected/added refs at 50 each and budget at the shared deterministic context ceiling.

`backend/app/modules/ai/jarvis_context.py` owns the common READ/CONTEXT preview seam, not domain write authority. Adapter/capability registration rejects COMMIT/EXECUTE, duplicate registrations fail closed, adapters may not mutate requested exact identity, preview evidence must be JSON-serializable and bounded, conflicting duplicate logical refs/workspace mismatches fail closed, and stale/unavailable/unknown added refs make previews non-dispatchable. Whole blocks are deterministically dropped on budget overflow; preview digest binds workspace, frozen route, exact refs, included blocks, source manifest, outcomes and budget. Dispatch requires both a dispatchable rebuild and exact expected digest match.

## EXPLICIT FILE COVERAGE LEDGER

`READ` means contents were opened and inspected directly from fresh `master` during file-coverage recovery. PR #660 is hints-only and confers no coverage.

| path | status | concise role/reason |
|---|---|---|
| `backend/app/modules/ai/jarvis_context_models.py` | READ | Frozen Jarvis route/action/value contracts; exact refs require version/revision/immutable-ref/digest identity, non-current refs cannot expose content, request ref-count/context-budget bounds are explicit. |
| `backend/app/modules/ai/jarvis_context.py` | READ | Common deterministic READ/CONTEXT adapter/capability registry and exact-context preview/digest gate; forbids COMMIT/EXECUTE authority, conflicting identity/workspace, oversized/nonserializable evidence, and stale/digest-changed dispatch. |

> RECOVERY NOTE: connector response-size limits prevented safe full-file replacement of the prior long ledger. This commit records the newly verified rows durably rather than pretending completion. Prior Area-A rows remain recoverable from parent commit `740b86701f098a3fb9133ffb00ea7582e9dfe9a0`; next run must reconstruct/merge the full ledger before COMPLETE can be claimed.
