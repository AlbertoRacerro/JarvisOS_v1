# JarvisOS agent manual — strict file coverage audit

GLOBAL_FILE_COVERAGE: IN_PROGRESS

Fresh master baseline: `240d5e0b27d9837d40f47bddfa24871ae7a2a4bb`.

This audit is deliberately fail-closed. `READ` is credited only where an active owner ledger or this audit establishes actual content inspection; capability prose, directory discovery, or a filename mention does not count as `READ`.

## Active owner set

Only these mapping owners participate in the union:

- **A+B:** PR #660 / `docs/capability-map-B-frontend-ux`.
- **C:** PR #659 / `docs/capability-map-C-engineering`.
- **D:** PR #657 / `docs/capability-map-D-devops-security`.

PR #658 is superseded as an execution owner. Its material may be absorbed by A+B but it cannot independently satisfy union ownership.

## Current union state

| Owner | Current evidence | Union eligibility |
|---|---|---|
| A+B | #660 capability map exists; latest inspected patch still lacks a literal `## EXPLICIT FILE COVERAGE LEDGER` | BLOCKED until exact paths are enumerated |
| C | #659 capability map exists; strict file-level reconciliation is not yet proven complete | BLOCKED until latest exact-path ledger is available and fresh enough |
| D | #657 capability map + this audit exist; D literal per-path ledger conversion is still incomplete | IN PROGRESS |
| Fresh recursive tree | master tree at baseline SHA fetched from GitHub | authoritative comparison set once ledgers are mechanically enumerable |

## Counts

- Total tracked files: **PENDING strict mechanical enumeration**. The fresh recursive tree has been fetched, but connector rendering is truncated; this audit will not invent a count.
- Covered files: **PENDING union**.
- A+B READ / GENERATED-ASSET: **PENDING A+B ledger**.
- C READ / GENERATED-ASSET: **PENDING C ledger**.
- D READ / GENERATED-ASSET: **IN PROGRESS**.
- Duplicate ownership count: **PENDING union**.
- Ambiguous ownership count: **non-zero** until all three active ledgers are literal and cross-owner `OUT_OF_SCOPE` references resolve to an exact destination entry.

## UNACCOUNTED_FILES

`UNACCOUNTED_FILES: UNKNOWN_NONZERO`

A literal zero is not yet defensible. Until all active ledgers are mechanically enumerable, every tracked path not explicitly resolved by those ledgers remains unaccounted. This includes tiny `__init__.py`, registry/protocol files, fixtures/helpers, package/lock/config/schema/report files, and files added to master after an owner's ledger baseline.

### Active-owner blockers

- **A+B (#660):** enumerate every owned backend/core/api/schema/module/test/helper/fixture/config path plus frontend source/test/helper/fixture/style/package/lock/build-config/generated/asset paths. Explicitly resolve `backend/app/modules/agents`, `dev_message_route`, `events`, `files`, `local_ai`, `local_ai_eval`, `secrets`, `tools`, `workspaces`, and all tiny registry/protocol/`__init__.py` files. Cross-owner exclusions must name the destination owner.
- **C (#659):** enumerate every owned BLUECAD/process/scientific module, runner, test/helper/fixture, config, schema, report and asset path. Cross-owner exclusions must name the destination owner.
- **D (#657):** finish literal coverage for `.github/**`, all development/delivery/security/ops `scripts/**`, root launch/metadata files, governance/operations docs, repository-level configs/tests and D-owned generated/assets.

## Freshness / added-file guard

For each active ledger, record or infer its master baseline before union. Compare that baseline with the fresh master tree. Any tracked file added after an owner's baseline is automatically `UNACCOUNTED` until that owner explicitly reads/classifies the exact path or another active owner legitimately owns it. A capability-level statement cannot grandfather later files.

## D audit evidence already established

Fresh directory inventories were re-read for repository root, `.github/`, `.github/workflows/`, and `scripts/`. Prior Area-D capability work source-read implementation/tests for repository delivery/CAS, local worktree actuator/IPC/writer guard, CI scope classifier, architecture/type/codegen enforcement, PR Attention, Claude/manual review, Codex delivery/autopush, cloud delivery bridge, exact-head browser proof/controller/contract, continuation, merge authority, BLUECAD real-tool proof, backup/restore and Windows launchers. Those reads still require literal per-path ledger rows before they count toward strict global completion.

## Completion gate

Set `GLOBAL_FILE_COVERAGE: COMPLETE` only after all conditions are mechanically checkable against one fresh tracked-file tree:

1. every tracked file resolves to exactly one active owner as `READ` or `GENERATED/ASSET`;
2. every `OUT_OF_SCOPE` entry cross-references an active destination ledger that covers that exact path;
3. `UNACCOUNTED_FILES: 0`;
4. duplicate ownership count = 0 after intentional cross-references are normalized;
5. ambiguous ownership count = 0;
6. no file was added to master after an owner's ledger baseline without explicit reconciliation.
