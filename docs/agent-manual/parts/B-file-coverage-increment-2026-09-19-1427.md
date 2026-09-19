# Area B file coverage increment — 2026-09-19 14:27 Europe/Rome

MAPPING_STATUS: IN_PROGRESS
UNACCOUNTED_FILES: NOT_YET_RECONCILED

This increment is Area-B-only evidence for issue #656. It does not assert global-union ownership and adds no backend Area-A rows.

## EXPLICIT FILE COVERAGE LEDGER — increment

| path | status | concise role / verified failure boundary |
|---|---|---|
| `frontend/src/app/selection.ts` | READ | Pure frontend selection type contract. Direct inspection verifies four selection families: canonical `record` refs, ephemeral `geometry-hit`, unresolved/ambiguous/resolving `bluecad-binding-status`, and resolved `bluecad-part`. The type boundary preserves workspace/candidate/artifact/viewer/object/mesh/semantic identity for BLUECAD states and only grants `partId` on resolved `bluecad-part`; geometry hits remain explicitly session/object-ephemeral. No I/O, persistence, mutation, authorization, or runtime validation occurs here: these are TypeScript compile-time shapes, so callers must not treat construction of a `StageSelection` value as proof that the referenced record/part exists or is authorized. |

## Reconciliation note

Fresh `master` remains `240d5e0b27d9837d40f47bddfa24871ae7a2a4bb`; PR #660 head at run start was `979e02740b0892c314978225234561de53b83aed`. `frontend/src/app/selection.ts` is present in the fresh tracked frontend tree and its complete source was directly inspected in this run, so this row is `READ` rather than inferred from capability prose.

The canonical `docs/agent-manual/parts/B-frontend-operator-ux.md` still contains the historical `MAPPING_STATUS: COMPLETE` line while lacking the maintainer-required literal one-row-per-B-owned-file canonical ledger. That completion claim remains non-defensible. Canonical consolidation plus a fresh tracked-tree set-difference is still required before `UNACCOUNTED_FILES: 0` can be asserted.
