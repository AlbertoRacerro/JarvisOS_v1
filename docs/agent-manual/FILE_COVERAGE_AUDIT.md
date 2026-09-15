# JarvisOS agent manual — strict file coverage audit

GLOBAL_FILE_COVERAGE: IN_PROGRESS

Fresh master baseline: `240d5e0b27d9837d40f47bddfa24871ae7a2a4bb`.

This ledger is deliberately fail-closed. `READ` is credited only where a builder ledger or this audit establishes actual content inspection; capability prose alone is not enough. Directory discovery or a filename mention does not count as READ.

## Current union state

| Item | Current evidence |
|---|---|
| Area A PR | #658, part reports `MAPPING_STATUS: COMPLETE`, but no explicit file-by-file coverage ledger is present in the current patch |
| Area B PR | #660, part reports `MAPPING_STATUS: COMPLETE`, but no explicit file-by-file coverage ledger is present in the current patch |
| Area C PR | #659, part reports `MAPPING_STATUS: COMPLETE`, but no explicit file-by-file coverage ledger is present in the current patch |
| Area D PR | #657; capability mapping exists, strict explicit ledger is being added |
| Fresh recursive tree | master tree SHA above retrieved from GitHub; strict union comparison remains open until all owner ledgers enumerate every tracked blob |

## Counts

- Total tracked files: **PENDING strict enumeration**. The recursive tree has been fetched from fresh master, but this audit does not invent a count from truncated connector rendering.
- A READ / GENERATED-ASSET: **PENDING A ledger**.
- B READ / GENERATED-ASSET: **PENDING B ledger**.
- C READ / GENERATED-ASSET: **PENDING C ledger**.
- D READ / GENERATED-ASSET: **IN PROGRESS**.
- Duplicate ownership count: **PENDING union**.
- Ambiguous-owner count: **non-zero until A/B/C explicit ledgers exist**.

## UNACCOUNTED_FILES

`UNACCOUNTED_FILES: UNKNOWN_NONZERO`

Strict completion is blocked because PRs #658/#660/#659 currently contain capability maps but do not yet expose literal path-by-path ledgers. Therefore the auditor cannot truthfully prove that every tracked blob—including tiny `__init__.py`, fixtures/helpers, lock/package/config/report/schema files and the specifically called-out backend modules—has exactly one owner. Those paths are treated as unaccounted until their owning ledgers enumerate them or Area D reads and assigns them explicitly.

### Explicit blockers for owning ledgers

- **A (#658):** must enumerate every owned backend/core/api/schema/module/test/helper/fixture/config file, explicitly including `backend/app/modules/agents`, `dev_message_route`, `events`, `files`, `local_ai`, `local_ai_eval`, `secrets`, `tools`, `workspaces`, and tiny registry/protocol/`__init__.py` files.
- **B (#660):** must enumerate every owned frontend source/test/helper/fixture/style/package/lock/build-config file and frontend-facing generated/asset files.
- **C (#659):** must enumerate every owned BLUECAD/process/scientific module/test/helper/fixture/config/schema/report asset.
- **D (#657):** must finish literal coverage for `.github/**`, all development/delivery/security/ops `scripts/**`, root launch/metadata files, governance/operations docs, repository-level configs/tests and any D-owned generated/assets.

## D audit evidence already established

Fresh directory inventories were re-read for repository root, `.github/`, `.github/workflows/`, and `scripts/`. Prior Area-D capability work source-read the implementation and tests for repository delivery/CAS, local worktree actuator/IPC/writer guard, CI scope classifier, architecture/type/codegen enforcement, PR Attention, Claude/manual review, Codex delivery/autopush, cloud delivery bridge, exact-head browser proof/controller/contract, continuation, merge authority, BLUECAD real-tool proof, backup/restore and Windows launchers. These reads will be converted to literal per-path entries in the Area-D part; until that conversion is complete they are not sufficient for GLOBAL completion.

## Completion gate

Set `GLOBAL_FILE_COVERAGE: COMPLETE` only after all of the following are mechanically checkable against the same fresh master tree:

1. every tracked blob appears in exactly one owner ledger as `READ` or `GENERATED/ASSET`, or appears as `OUT_OF_SCOPE` with an explicit cross-reference to the ledger that owns it;
2. `UNACCOUNTED_FILES: 0`;
3. duplicate ownership is zero after intentional cross-references are normalized;
4. no ambiguous owner remains;
5. branch ledgers have been refreshed if master changed after their baseline.
