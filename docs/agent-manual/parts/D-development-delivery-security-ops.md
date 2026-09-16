# Area D — Development / delivery / GitHub / security / operations

MAPPING_STATUS: IN_PROGRESS

Evidence baseline: fresh `master` `240d5e0b27d9837d40f47bddfa24871ae7a2a4bb`. Runtime/scripts/workflows/tests are primary evidence; prose is secondary. `READ` below means actual source-content inspection, not filename discovery.

## Capability map

### Frontier builder execution / authority — REAL
- **What/when:** fresh-state, bounded-authority, exact-head delivery contract for repository work.
- **Canonical:** `AGENTS.md`, `docs/AGENT_EXECUTION_AND_AUTOMATION_PROTOCOL.md`, `docs/POST_112_PARALLEL_DELIVERY_PROFILE.md`.
- **Reuse:** follow Generic Frontier Builder Contract; serialize shared authority writes; remote SHA/CAS remains mandatory.
- **Risk/limits:** prose does not enforce security; title mutex is coordination, not atomic CAS.
- **Do not reinvent:** no second agent lifecycle/queue/governance authority.
- **Anchors:** `Frontier Coordinator`, `Global shared-writer mutex`, `Exact-state and delivery truth`.

### Repository delivery / truth — REAL
- **Canonical:** `scripts/repository_delivery.py` + repository-delivery tests.
- **Reuse/I/O:** typed guarded Git operations; exact remote-head admission and post-push verification.
- **Risk:** high-authority mutation; refuses protected refs, unsafe config/history/path/control/secret state.
- **Do not reinvent:** reuse `GitRunner`/guarded push rather than generic model-authored Git.
- **Anchors:** `DeliveryCode`, `STALE_REMOTE_HEAD`, `NON_FAST_FORWARD_REFUSED`.

### Local persistent worktree actuator — REAL bounded
- **Canonical:** `.github/local_worktree_actuator_core.py`, `.github/local_worktree_recovery.py`, `scripts/local_worktree_actuator.py`, `scripts/local_worktree_ipc.py` + tests.
- **Reuse:** host OS writer lock + durable ownership/registration; Git mutation delegates to repository delivery.
- **Risk/limits:** durable lease is recovery metadata, not live lock; no generic remote execution authority.
- **Anchors:** `LocalWorktreeActuator`, `_exclusive_writer_guard`, `WORKTREE_IDENTITY_MISMATCH`.

### Scope-aware CI / reusable test harness — REAL
- **Canonical:** `.github/workflows/ci.yml`, `scripts/classify_ci_scope.py`, `backend/tests/conftest.py`.
- **Reuse:** exact changed-path scope; ambiguous events fail closed to full CI; pytest isolates `JARVISOS_DATA_ROOT`.
- **Limits:** green CI is not semantic proof.
- **Anchors:** `docs_only`, `full_required`, `isolated_data_root`.

### Architecture / type / codegen guards — REAL
- **Canonical:** `scripts/check_architecture_enforcement.py`, `scripts/check_typecheck_ratchet.py`, `scripts/generate_frontend_contracts.py`, baseline/exception/generated files.
- **Reuse:** deterministic static enforcement and drift checks; generated TS is owner-written output.
- **Limits:** bounded static rules and ratcheted existing debt.
- **Anchors:** `AE001`, `AE004`, `RatchetError`, `GENERATED FILE — DO NOT EDIT`.

### PR attention / exact-head review evidence — REAL advisory
- **Canonical:** `.github/workflows/pr-attention.yml`, `scripts/check_pr_attention_integration.py`.
- **Reuse:** event-head-bound mechanical evidence; read-only permissions.
- **Limits:** cannot accept/merge or establish semantic correctness.
- **Anchors:** `PR Attention Evidence`, `expected-head`.

### Claude exact-head semantic review — REAL
- **Canonical:** `.github/workflows/claude-review.yml`.
- **I/O/risk:** exact-head trusted policy/diff -> structured provider review -> provenance-bound PR evidence; provider secret only in trusted step.
- **Limits:** advisory and provider-dependent.
- **Anchors:** `expert-review`, `JARVIS_CLAUDE_REVIEW_V3_2_JSON`.

### Cheap/senior manual review — PARTIAL / legacy governance
- **Canonical:** `.github/workflows/{cheap-review,senior-review}.yml`, `scripts/{cheap_review,manual_review,check_review_secret_boundary}.py`.
- **Reuse:** trusted-code/untrusted-data and redaction boundary.
- **Limits:** historical tier/provider governance is superseded; checker covers enumerated seams only.
- **Anchors:** `GLM_API_KEY`, `CHEAP_REVIEW_API_KEY`, `_prove_untrusted_shadow_is_not_on_execution_path`.

### Codex delivery seams — REAL bounded; direct autopush legacy-adjacent
- **Canonical:** `.github/workflows/{codex-result-delivery,codex-autopush}.yml`, `scripts/{codex_result_delivery_dispatch,codex_pr_autopush}.py`.
- **Reuse:** prefer admitted immutable comment -> common bridge; direct autopush is narrower compatibility path.
- **Risk:** branch mutation is CAS-guarded; neither grants merge authority.
- **Anchors:** `jarvis-codex-result-delivery:v1`, `codex-autopush:success`.

### Cloud delivery bridge — REAL / PARTIAL genericity
- **Canonical:** `.github/workflows/cloud-delivery-bridge.yml`, `scripts/cloud_delivery_bridge.py`.
- **Reuse:** freeze admitted patch/manifest, validate candidate data, then trusted CAS update.
- **Limits:** `frontend-143` profile specialization remains; do not clone bridge control logic.
- **Anchors:** `jarvis-cloud-delivery:v1`, `payload_body_sha256`, `validation_profile`.

### Exact-head browser proof — REAL
- **Canonical:** `.github/workflows/{exact-head-browser-proof,exact-head-browser-proof-command,browser-proof-contract}.yml`, `.github/browser-proof/**`.
- **Reuse:** generic trusted controller + declarative plans; candidate checkout unprivileged/token-blanked.
- **Risk:** real candidate/browser execution; controller/plan workspace protected and verified clean.
- **Limits:** browser evidence is not semantic/security review.
- **Anchors:** `PROOF_PLAN_ID`, `jarviscandidate`, `PROOF_EXPECTED_HEAD_SHA`.

### Scheduled/event continuation — REAL but legacy phase-sensitive
- **Canonical:** `.github/workflows/{daily-development-continuation,event-driven-continuation}.yml` + continuation scripts.
- **Reuse:** untrusted patch generation -> deterministic validation -> trusted exact-head CAS push.
- **Limits:** historical active-front/model scheduling assumptions are not current scheduling authority.
- **Anchors:** `CONTINUATION_WORKFLOW_VERSION`, `continuation.patch`, `Jarvis-OIDC`.

### Merge authority / reconciliation — REAL bounded
- **Canonical:** `.github/merge-authority-policy.json`, `.github/workflows/{merge-authority-verify,post-merge-status-reconcile}.yml`, `scripts/verify_merge_authority.py`.
- **Reuse:** verifier is read-only; reconciler only performs admitted exact STATUS transition through a branch/PR.
- **Limits:** no auto-merge; ruleset truth must be read live; no generic STATUS editor.
- **Anchors:** `jarvisos.merge-authority.v1`, `required_check_contexts`.

### External-tool proof / data-root recovery — REAL
- **Canonical:** `.github/workflows/bluecad-real-tool-proof.yml`, `scripts/jarvisos_data_root.py`, `scripts/data_root_recovery/**`, `docs/DATA_ROOT_RECOVERY.md`.
- **Reuse:** real-tool proof and hash/integrity-checked snapshot/verify/restore.
- **Risk:** restore mutates local data/database; writers must be stopped.
- **Limits:** no cloud backup scheduler/encryption/compression.
- **Anchors:** `BLUECAD Real Tool Proof`, `COMPLETE`, `restore_snapshot`.

### Windows launch/dev tooling — REAL convenience / PARTIAL diagnostics
- **Canonical:** root `Start-JarvisOS*.cmd`, `scripts/start-backend.ps1`, `scripts/start-frontend.ps1`.
- **Reuse:** ordinary local startup only.
- **Limits:** dependency installation is convenience-first; combined launcher uses fixed delay, not health probe; no comprehensive doctor.
- **Anchors:** `app.core.bootstrap`, `npm run dev`.

### Secret / credential / builder egress boundary — REAL but distributed
- **Canonical:** repository delivery env scrub, `check_review_secret_boundary.py`, trusted review/browser/delivery workflows, architecture AE002.
- **Risk:** no universal Actions network sandbox; npm/pip/apt/GitHub/provider egress is workflow-specific.
- **Do not reinvent:** keep provider/Git credentials out of candidate/model-authored execution and preserve least privilege.
- **Anchors:** `persist-credentials: false`, `AE002`, `jarviscandidate`.

### Jules / Copilot / Google / Antigravity repository worker seam — DEFERRED
- No implemented repository-side adapter/workflow/dispatcher/credential seam found at this baseline; planning/account entitlement is not repository capability.

## Obsolete / superseded paths
- `codex-autopush.yml` overlaps newer comment-bound result delivery; prefer the common bridge where compatible.
- Cheap/manual review provider-tier governance is historical; retain only useful parsing/redaction/secret-isolation primitives.
- Continuation workflows contain reusable trust primitives plus phase-sensitive scheduling assumptions; do not reuse scheduler policy blindly.
- Shared-writer title mutex reduces races but never replaces repository CAS.

## EXPLICIT FILE COVERAGE LEDGER

| Path | Status | Role / reason |
|---|---|---|
| `.gitignore` | READ | Ignore policy for Python/Node/env/runtime DB/log/local-eval outputs; `.env.example` exception. |
| `AGENTS.md` | READ | Stable AI engineering constitution, authority/evidence/security invariants, execution protocol pointers. |
| `CLAUDE.md` | READ | Root Claude worker guidance; repository-level agent metadata. |
| `README.md` | READ | Repository overview/launch/development context; secondary authority only. |
| `Start-JarvisOS-Backend.cmd` | READ | Windows backend wrapper delegating to PowerShell launcher. |
| `Start-JarvisOS-Frontend.cmd` | READ | Windows frontend wrapper delegating to PowerShell launcher. |
| `Start-JarvisOS.cmd` | READ | Combined Windows launcher; prerequisite checks, separate consoles, fixed startup delay. |
| `.github/merge-authority-policy.json` | READ | Declares master protection/status-check expectations; auto-merge false; observe-only merge methods. |
| `.github/pull_request_template.md` | READ | PR spec/status/deviation/test/invariant checklist; governance evidence template. |
| `.github/local_worktree_actuator_core.py` | READ | Persistent worktree registration/ownership/writer guard core; inspected during Area-D capability audit. |
| `.github/local_worktree_recovery.py` | READ | Local actuator recovery/reconciliation helper; inspected during Area-D capability audit. |
| `.github/workflows/bluecad-real-tool-proof.yml` | READ | Real Gmsh/CalculiX environment proof; D owns workflow control, C owns engineering semantics. |
| `.github/workflows/browser-proof-contract.yml` | READ | Deterministic browser-proof controller/plan contract checks. |
| `.github/workflows/cheap-review.yml` | READ | Manual cheap review seam; legacy governance, bounded secret path. |
| `.github/workflows/ci.yml` | READ | Scope-aware canonical CI orchestration and deterministic gates. |
| `.github/workflows/claude-review.yml` | READ | Exact-head external semantic review with trusted secret boundary. |
| `.github/workflows/cloud-delivery-bridge.yml` | READ | Trusted admitted-patch delivery bridge and CAS mutation boundary. |
| `.github/workflows/codex-autopush.yml` | READ | Direct Codex commit materialization compatibility path; legacy-adjacent. |
| `.github/workflows/codex-result-delivery.yml` | READ | Comment-bound Codex result dispatcher to common delivery bridge. |
| `.github/workflows/daily-development-continuation.yml` | READ | Scheduled continuation control plane; untrusted generation/trusted validation+push split. |
| `.github/workflows/event-driven-continuation.yml` | READ | CI-completion wake seam for continuation. |
| `.github/workflows/exact-head-browser-proof-command.yml` | READ | Owner-label/command wrapper for exact-head browser proof. |
| `.github/workflows/exact-head-browser-proof.yml` | READ | Trusted controller plus unprivileged candidate real-browser execution. |
| `.github/workflows/merge-authority-verify.yml` | READ | Read-only live merge-protection verification workflow. |
| `.github/workflows/post-merge-status-reconcile.yml` | READ | Bounded post-merge STATUS reconciliation through branch/PR. |
| `.github/workflows/pr-attention.yml` | READ | Exact-head mechanical PR attention evidence. |
| `.github/workflows/project-knowledge-fast.yml` | READ | Fast project-knowledge check workflow; repository CI/delivery surface. |
| `.github/workflows/senior-review.yml` | READ | Manual senior/GLM review seam with bounded secret exposure. |
| `scripts/cheap_review.py` | READ | Legacy/manual provider review helper and parsing/redaction primitives. |
| `scripts/check_architecture_enforcement.py` | READ | AE deterministic architecture/egress/control-owner enforcement. |
| `scripts/check_pr_attention_integration.py` | READ | Validates PR-attention permissions/pinning/head/mutation boundaries. |
| `scripts/check_review_secret_boundary.py` | READ | Trusted-code/untrusted-data review secret boundary checker including shadow-import defense. |
| `scripts/check_spec_status.py` | READ | Deterministic spec/STATUS linkage validation used by CI/delivery. |
| `scripts/check_typecheck_ratchet.py` | READ | Mypy baseline ratchet parser/enforcer. |
| `scripts/classify_ci_scope.py` | READ | Changed-path CI scope classifier; ambiguous inputs fail closed. |
| `scripts/cloud_delivery_bridge.py` | READ | Patch admission/verification/CAS bridge owner. |
| `scripts/codex_pr_autopush.py` | READ | Direct Codex autopush compatibility helper with protected-path/ref guards. |
| `scripts/codex_result_delivery_dispatch.py` | READ | Admits immutable result comments and dispatches common bridge. |
| `scripts/daily_development_continuation.py` | READ | Continuation planner/control logic; legacy phase-sensitive assumptions noted. |
| `scripts/event_bound_continuation_plan.py` | READ | Event-bound continuation plan helper. |
| `scripts/event_driven_continuation.py` | READ | Event wake/continuation helper. |
| `scripts/generate_frontend_contracts.py` | READ | Deterministic backend-model -> generated TS contract writer. |
| `scripts/data_root_recovery/__init__.py` | READ | Recovery package export/entry surface. |
| `scripts/data_root_recovery/cli.py` | READ | Snapshot/verify/restore CLI parsing/dispatch. |
| `scripts/data_root_recovery/common.py` | READ | Recovery manifests, hashes, path/integrity helpers. |
| `scripts/data_root_recovery/restore.py` | READ | Verified staged/atomic restore implementation and destructive guard. |
| `scripts/data_root_recovery/snapshot.py` | READ | Snapshot creation/integrity manifest implementation. |
| `scripts/jarvisos_data_root.py` | READ | Thin recovery CLI entry point. |

### Remaining coverage
- Finish literal source reads and rows for every remaining `.github/browser-proof/**` file and every remaining `scripts/**` file from the fresh tree; do not credit directory discovery.
- Finish repository-global governance/docs/config/test surfaces that belong to D and add exact `OUT_OF_SCOPE` cross-owner rows only after A+B/C ledgers contain the same exact destination paths.
- Re-read latest A+B #660 and C #659 ledgers when they appear, then mechanically union all three active ledgers against a fresh recursive tracked-file tree.
- Keep global audit fail-closed until total/covered/duplicate/ambiguous/unaccounted counts are exact and freshness-reconciled.
