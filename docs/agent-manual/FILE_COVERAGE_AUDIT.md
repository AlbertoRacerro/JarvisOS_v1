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
| D | Literal ledger exists; 70 exact paths are now classified `READ`; remaining D tree is still being source-read | IN PROGRESS |
| Fresh tree | master `240d5e0...`; recursive tree remains authoritative comparison set | READY FOR UNION once all ledgers are enumerable |

## Counts

- Total tracked files: **PENDING strict mechanical enumeration**. The recursive Git tree exists but the connector rendering is truncated; no count is inferred from truncated output.
- Covered files globally: **PENDING union**.
- A+B READ / GENERATED-ASSET: **PENDING A+B ledger**.
- C READ / GENERATED-ASSET: **PENDING C ledger**.
- D READ: **70 literal rows currently**.
- D GENERATED/ASSET: **0 currently**.
- Duplicate ownership count: **PENDING union**.
- Ambiguous ownership count: **non-zero** until A+B/C ledgers exist and D remaining scope is classified.

## UNACCOUNTED_FILES

`UNACCOUNTED_FILES: UNKNOWN_NONZERO`

A literal zero is not defensible yet. The exact orphan list becomes mechanically valid only when all three active ledgers are enumerable against one fresh tracked tree.

### Active-owner blockers

- **A+B (#660):** latest patch still has no literal ledger. Must enumerate every owned backend/core/api/schema/module/test/helper/fixture/config path plus frontend source/test/helper/fixture/style/package/lock/build-config/generated/asset path, including `backend/app/modules/agents`, `dev_message_route`, `events`, `files`, `local_ai`, `local_ai_eval`, `secrets`, `tools`, `workspaces`, tiny registry/protocol/`__init__.py` files.
- **C (#659):** latest patch still has no literal ledger. Must enumerate every BLUECAD/process/scientific module, runner, test/helper/fixture, config, schema, report and asset path.
- **D (#657):** `.github/browser-proof/**` is now completely literalized at the baseline. Remaining source reads/rows: unclassified remainder of `scripts/**`; D-owned governance/operations docs/config/tests/repository metadata. Cross-owner `OUT_OF_SCOPE` rows will only be credited when the destination ledger contains the exact path.

## Freshness / added-file guard

For each owner, compare its ledger baseline to the fresh master tree. Any tracked file added after an owner's baseline is automatically unaccounted until the exact path is explicitly classified by an active owner. Capability prose cannot grandfather later files.

## D evidence established

The D map is strict `MAPPING_STATUS: IN_PROGRESS` and now contains `## EXPLICIT FILE COVERAGE LEDGER` with 70 exact `READ` paths. The latest tranche adds every file under `.github/browser-proof/**`: controller package metadata, fixture registry, all three Python fixtures, generic plan library/executor/request policy, all eight declarative plans, three test files and both validators.

A concrete defect was found by actual content inspection: `.github/browser-proof/plans/115-project-search.json` performs `assert-value-equals` against `{capture:"mutationBaseline"}` but contains no step that creates that capture. `run.mjs` fails when a requested capture is absent, so this proof plan cannot complete successfully as written. Issue #656 is documentation-only, therefore the runtime plan was not modified; the defect is recorded in Area D rather than hidden by a capability-level `REAL` label.

The previously established D tranche includes all seven root files, both root `.github` policy/template files, both local-worktree control files, all 17 workflow files in the closed workflow tree, and 20 source-inspected delivery/review/CI/continuation/codegen/recovery scripts.

## Completion gate

Set `GLOBAL_FILE_COVERAGE: COMPLETE` only when all are mechanically checkable against one fresh tracked tree:

1. every tracked file resolves to exactly one active owner as `READ` or `GENERATED/ASSET`;
2. every `OUT_OF_SCOPE` entry resolves to an exact destination-ledger path;
3. `UNACCOUNTED_FILES: 0`;
4. duplicate ownership count = 0 after normalized cross-references;
5. ambiguous ownership count = 0;
6. files added after any owner baseline are explicitly reconciled.
