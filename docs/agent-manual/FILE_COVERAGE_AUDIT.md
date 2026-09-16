# JarvisOS agent manual — strict file coverage audit

GLOBAL_FILE_COVERAGE: IN_PROGRESS

Fresh master baseline: `240d5e0b27d9837d40f47bddfa24871ae7a2a4bb`.

This audit is fail-closed. `READ` is credited only where an active owner ledger establishes actual content inspection; capability prose, directory discovery, or filename mention does not count.

## Active owner set

- **A+B:** PR #660 / `docs/capability-map-B-frontend-ux`.
- **C:** PR #659 / `docs/capability-map-C-engineering`.
- **D:** PR #657 / `docs/capability-map-D-devops-security`.

PR #658 is superseded as an execution owner and cannot independently satisfy union ownership.

## Current union state

| Owner | Current evidence | Union eligibility |
|---|---|---|
| A+B | Latest #660 patch re-read; still no literal `## EXPLICIT FILE COVERAGE LEDGER` | BLOCKED |
| C | Latest #659 patch re-read; still no literal `## EXPLICIT FILE COVERAGE LEDGER` | BLOCKED |
| D | Literal ledger now exists; first 48 exact paths are classified `READ`; remaining D tree is still being source-read | IN PROGRESS |
| Fresh tree | master `240d5e0...`; root and `.github/workflows` closed trees revalidated; recursive tree is authoritative comparison set | READY FOR UNION once ledgers are enumerable |

## Counts

- Total tracked files: **PENDING strict mechanical enumeration**. The recursive Git tree exists but the connector rendering is truncated; no count is inferred from truncated output.
- Covered files globally: **PENDING union**.
- A+B READ / GENERATED-ASSET: **PENDING A+B ledger**.
- C READ / GENERATED-ASSET: **PENDING C ledger**.
- D READ: **48 literal rows currently**.
- D GENERATED/ASSET: **0 currently**.
- Duplicate ownership count: **PENDING union**.
- Ambiguous ownership count: **non-zero** until A+B/C ledgers exist and D remaining scope is classified.

## UNACCOUNTED_FILES

`UNACCOUNTED_FILES: UNKNOWN_NONZERO`

A literal zero is not defensible yet. The exact orphan list becomes mechanically valid only when all three active ledgers are enumerable against one fresh tracked tree.

### Active-owner blockers

- **A+B (#660):** no literal ledger yet. Must enumerate every owned backend/core/api/schema/module/test/helper/fixture/config path plus frontend source/test/helper/fixture/style/package/lock/build-config/generated/asset path, including `backend/app/modules/agents`, `dev_message_route`, `events`, `files`, `local_ai`, `local_ai_eval`, `secrets`, `tools`, `workspaces`, tiny registry/protocol/`__init__.py` files.
- **C (#659):** no literal ledger yet. Must enumerate every BLUECAD/process/scientific module, runner, test/helper/fixture, config, schema, report and asset path.
- **D (#657):** first literal tranche is durable. Remaining source reads/rows: `.github/browser-proof/**`; unclassified remainder of `scripts/**`; D-owned governance/operations docs/config/tests/repository metadata. Cross-owner `OUT_OF_SCOPE` rows will only be credited when the destination ledger contains the exact path.

## Freshness / added-file guard

For each owner, compare its ledger baseline to the fresh master tree. Any tracked file added after an owner's baseline is automatically unaccounted until the exact path is explicitly classified by an active owner. Capability prose cannot grandfather later files.

## D evidence established this run

The D map was changed from capability-level `MAPPING_STATUS: COMPLETE` to strict `MAPPING_STATUS: IN_PROGRESS` and now contains `## EXPLICIT FILE COVERAGE LEDGER` with 48 exact `READ` paths. This tranche includes all seven root files, both root `.github` policy/template files, both local-worktree control files, all 17 workflow files in the closed workflow tree, and 20 source-inspected delivery/review/CI/continuation/codegen/recovery scripts.

The closed workflow tree at this baseline contains exactly: `bluecad-real-tool-proof.yml`, `browser-proof-contract.yml`, `cheap-review.yml`, `ci.yml`, `claude-review.yml`, `cloud-delivery-bridge.yml`, `codex-autopush.yml`, `codex-result-delivery.yml`, `daily-development-continuation.yml`, `event-driven-continuation.yml`, `exact-head-browser-proof-command.yml`, `exact-head-browser-proof.yml`, `merge-authority-verify.yml`, `post-merge-status-reconcile.yml`, `pr-attention.yml`, `project-knowledge-fast.yml`, `senior-review.yml`.

## Completion gate

Set `GLOBAL_FILE_COVERAGE: COMPLETE` only when all are mechanically checkable against one fresh tracked tree:

1. every tracked file resolves to exactly one active owner as `READ` or `GENERATED/ASSET`;
2. every `OUT_OF_SCOPE` entry resolves to an exact destination-ledger path;
3. `UNACCOUNTED_FILES: 0`;
4. duplicate ownership count = 0 after normalized cross-references;
5. ambiguous ownership count = 0;
6. files added after any owner baseline are explicitly reconciled.
