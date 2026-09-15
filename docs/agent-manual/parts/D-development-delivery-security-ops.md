# Area D — Development / delivery / GitHub / security / operations

MAPPING_STATUS: COMPLETE

Source policy: runtime/scripts/workflows/tests first; specs/strategy only for authority/boundary context. Labels describe observed implementation, not intended future state.

## Capability: Frontier builder execution + repository authority contract — REAL
- **What / when:** Common fresh-state/recovery-first/bounded-authority/exact-head delivery contract for repository work.
- **Canonical files:** `AGENTS.md`; `docs/AGENT_EXECUTION_AND_AUTOMATION_PROTOCOL.md`; `docs/POST_112_PARALLEL_DELIVERY_PROFILE.md` for concurrency.
- **Invoke / reuse:** read before authority-bearing work; use Generic Frontier Builder Contract, not vendor-specific lifecycle rules.
- **I/O / persistence:** fresh GitHub/spec/code evidence → branch/PR/review/merge/reconciliation; STATUS is spec-state authority.
- **Preconditions:** accepted/readied product scope where required; fresh remote/head for authority decisions.
- **Side effects / authority / risk:** prose governs but does not itself enforce security; model identity grants no repository authority.
- **Tests / evidence:** deterministic CI/delivery/proof owners below implement key boundaries.
- **Limitations:** green CI is not semantic proof.
- **Do not reinvent:** no second agent queue/lifecycle/reviewer constitution.
- **Search anchors:** `Generic Frontier Builder Contract`, `Exact-state and delivery truth`, `Frontier Coordinator`.

## Capability: Post-112 shared-writer concurrency — REAL coordination / PARTIAL correctness
- **What / when:** Serializes conflicting shared GitHub/authority writes while allowing disjoint read-only/isolated work.
- **Canonical files:** `docs/POST_112_PARALLEL_DELIVERY_PROFILE.md`.
- **Invoke / reuse:** inspect scheduler titles; claim `[BUSY <UTC-ISO>]`; recheck topology; fresh lease <20 min, refresh ~10 min; restore base title.
- **I/O / persistence:** scheduler/automation titles; no repository lock database.
- **Preconditions:** actual shared-state conflict.
- **Side effects / authority / risk:** race reduction only; SHA/CAS/post-write verification remain mandatory.
- **Tests / evidence:** documented protocol; no atomic-CAS claim for title service.
- **Limitations:** stale/concurrent lease possible; disjointness is authority/state based, not filename-only.
- **Do not reinvent:** no parallel queue/lock/store for ordinary builders.
- **Search anchors:** `Global shared-writer mutex`, `[BUSY`, `Isolated worktree/worker principle`.

## Capability: Deterministic repository delivery + repository truth — REAL
- **What / when:** Typed Git mutation owner instead of generic model-authored Git; validates remote identity, branch/ref/path/config/history and exact remote-head CAS before and after push.
- **Canonical files:** `scripts/repository_delivery.py`; `backend/tests/test_repository_delivery*.py`.
- **Invoke / reuse:** typed operations/CLI; `GitRunner` uses server-owned argv, `shell=False`, scrubbed Git/network/token environment; guarded push only to admitted existing branch.
- **I/O / persistence:** repo/worktree + expected remote refs → `DeliveryResult`/refusal code; successful push changes admitted remote branch.
- **Preconditions:** approved GitHub HTTPS remote, exact expected remote head, safe branch/path/config, explicit credential adapter.
- **Side effects / authority / risk:** high-risk mutation. Refuses protected refs, forbidden control/secret paths, stale/non-FF/history-replacement state, unsafe Git config/import/config-worktree escape; post-push ref is re-read. Windows local path validates GCM and suppresses credential-bearing output.
- **Tests / evidence:** direct regressions cover missing branch, stale head, non-FF, replace/grafts, unsafe config, path escape, post-push truth and credential boundaries.
- **Limitations:** intentionally not generic Git; local-path remote is test-only; host credential path is platform dependent.
- **Do not reinvent:** use this owner for branch mutation/CAS/remote truth.
- **Search anchors:** `DeliveryCode`, `GitRunner`, `guarded_push`, `STALE_REMOTE_HEAD`, `NON_FAST_FORWARD_REFUSED`, `WindowsGCMAdapter`.

## Capability: Local persistent worktree actuator — REAL, bounded
- **What / when:** Registers/claims one physical persistent worktree per worker and serializes writer operations with a host OS lock; delegates Git mutation to repository delivery.
- **Canonical files:** `scripts/local_worktree_actuator.py`; `.github/local_worktree_actuator_core.py`; `scripts/local_worktree_ipc.py`; actuator/IPC/writer-guard tests.
- **Invoke / reuse:** typed `LocalWorktreeActuator`/IPC operations after worker/repo/worktree registration and ownership claim.
- **I/O / persistence:** registrations/audit/ownership under `%LOCALAPPDATA%/JarvisOS/local-worktree-actuator-host` or XDG/`~/.local/state/jarvisos/...`.
- **Preconditions:** private non-symlink state, matching worker identity, durable ownership claim.
- **Side effects / authority / risk:** filesystem/Git writer; `msvcrt`/`flock` is live serialization; durable lease is interruption metadata only; POSIX state is 0700.
- **Tests / evidence:** `test_local_worktree_actuator.py`, `test_local_worktree_ipc.py`, `test_worktree_writer_guard.py` exercise reviewer read-only, ownership, corrupt-lease fail-closed, exact-SHA worktree creation and control/Git-admin path refusal.
- **Limitations:** optional local plane; no generic remote execution/branch-creation authority.
- **Do not reinvent:** persistent local coding workers reuse actuator + repository delivery.
- **Search anchors:** `LocalWorktreeActuator`, `_exclusive_writer_guard`, `_claim_physical_worktree`, `WORKTREE_IDENTITY_MISMATCH`.

## Capability: Scope-aware GitHub CI + reusable backend test harness — REAL
- **What / when:** Selects docs/backend/frontend/BLUECAD checks from exact base→head paths; ambiguous events fail closed to full CI. Backend pytest globally isolates runtime data roots.
- **Canonical files:** `.github/workflows/ci.yml`; `scripts/classify_ci_scope.py`; `backend/tests/conftest.py`.
- **Invoke / reuse:** PR/master/manual/nightly CI; local pytest inherits `isolated_data_root`; `--require-bluecad-real-tools` converts missing real tools from skip to failure.
- **I/O / persistence:** changed paths → scope flags/checks; pytest gets per-test temp `JARVISOS_DATA_ROOT` and clears settings cache.
- **Preconditions:** Actions/Python 3.11/Node as selected; pytest temp filesystem.
- **Side effects / authority / risk:** CI read/test/build only; fixtures prevent tests writing default operator data root.
- **Tests / evidence:** spec-status, review-tool self-tests, secret boundary, license scan, codegen drift, mypy ratchet, architecture enforcement, Ruff, sharded backend, frontend/BLUECAD jobs. `conftest.py` also contains named legacy compatibility wrappers only for historical tests.
- **Limitations:** scope optimization does not prove semantics; legacy fixture bridges are test-only compatibility, not production behavior.
- **Do not reinvent:** extend classifier/CI and shared fixtures rather than bespoke test workflows unless trust boundary differs.
- **Search anchors:** `classify_ci_scope.py`, `docs_only`, `full_required`, `isolated_data_root`, `--require-bluecad-real-tools`.

## Capability: Architecture/type/codegen enforcement — REAL
- **What / when:** Deterministic gates prevent known architecture drift, type-debt regression and stale generated frontend contracts.
- **Canonical files:** `scripts/check_architecture_enforcement.py`; architecture exception config; `scripts/check_typecheck_ratchet.py`; `backend/mypy-baseline.json`; `scripts/generate_frontend_contracts.py`; generated `frontend/src/api/generated/modeling.ts`.
- **Invoke / reuse:** CI/local checker commands; generator owns selected TS output.
- **I/O / persistence:** source/config → AE001–AE004 findings; mypy diagnostics+baseline → regression result; backend Pydantic `ParameterRead` → bounded TS contract.
- **Preconditions:** parseable source/config; supported codegen annotation shapes.
- **Side effects / authority / risk:** checkers read-only; generator writes one generated file. Architecture exceptions require exact path/symbol/rule/owner/removal/rationale; malformed/wildcard/stale exceptions fail.
- **Tests / evidence:** self-tests/fixtures; AE004 pins exact Codex result-delivery control digests; mypy parser/baseline validation; generator tests + CI drift/build/typecheck.
- **Limitations:** static rules are bounded; mypy ratchets existing debt; codegen is deliberately not general OpenAPI generation.
- **Do not reinvent:** add enforceable invariants to existing owners; never hand-edit generated file.
- **Search anchors:** `AE001`, `AE004`, `mypy-baseline.json`, `RatchetError`, `ContractGenerationError`, `GENERATED FILE — DO NOT EDIT`.

## Capability: PR Attention exact-head evidence — REAL, advisory/read-only
- **What / when:** Mechanical PR attention/gate/semantic/safety evidence bound to PR event head without mutation authority.
- **Canonical files:** `.github/workflows/pr-attention.yml`; `scripts/check_pr_attention_integration.py`; immutable-pinned external action.
- **Invoke / reuse:** automatic on PR opened/synchronize/reopened with event SHA as `expected-head`.
- **I/O / persistence:** PR/check metadata → validated manifest artifact (3-day retention) + summary.
- **Preconditions:** Actions and pinned action.
- **Side effects / authority / risk:** read-only permissions; checker forbids `pull_request_target`, semantic-authority inputs and downstream mutation.
- **Tests / evidence:** negative fixtures for mutable pin/write permission/head drift/mutation/authority inputs.
- **Limitations:** advisory only; cannot accept spec/review/merge.
- **Do not reinvent:** reuse for exact-head mechanical attention.
- **Search anchors:** `PR Attention Evidence`, `expected-head`, `FORBIDDEN_INPUTS`, `merge_candidate`.

## Capability: Claude exact-head semantic review — REAL
- **What / when:** `expert-review` label triggers structured independent Claude semantic/security review after exact-head `backend` + `evidence` checks pass.
- **Canonical files:** `.github/workflows/claude-review.yml`.
- **Invoke / reuse:** label non-draft PR; validated V3.2 evidence is deduplicated only for identical head/base.
- **I/O / persistence:** trusted policy/spec/diff → strict JSON verdict/findings → bot comment `JARVIS_CLAUDE_REVIEW_V3_2_JSON` bound to head/base/run.
- **Preconditions:** `CLAUDE_CODE_OAUTH_TOKEN`; exact-head required checks green.
- **Side effects / authority / risk:** provider egress; checkout has no persisted Git credential; Claude is instructed not to push/comment/merge; workflow publishes evidence. P0/P1 BLOCK, P2/P3 may PARK.
- **Tests / evidence:** deterministic pre-gate and schema/verdict/provenance publication validation.
- **Limitations:** provider availability/quota; advisory model evidence, not deterministic correctness.
- **Do not reinvent:** use existing exact-head independent review seam.
- **Search anchors:** `expert-review`, `jarvis.claude-review.v3.2`, `JARVIS_CLAUDE_REVIEW_V3_2_JSON`.

## Capability: Manual cheap/senior provider review — PARTIAL / legacy governance
- **What / when:** Trusted-master manual workflows fetch reviewed PR as inert API data and run legacy OpenAI-compatible review helper; senior currently targets GLM endpoint.
- **Canonical files:** `.github/workflows/cheap-review.yml`; `.github/workflows/senior-review.yml`; `scripts/cheap_review.py`; `scripts/manual_review.py`; `scripts/check_review_secret_boundary.py`.
- **Invoke / reuse:** `workflow_dispatch` from master only; senior uses trusted checkout `persist-credentials:false` and `GLM_API_KEY` only in review step.
- **I/O / persistence:** PR diff/spec excerpts → provider response → advisory PR comment.
- **Preconditions:** configured provider secret/quota.
- **Side effects / authority / risk:** provider egress + comment write; no repository contents write. Secret-boundary checker ensures trusted-code/untrusted-data separation and guards against import shadowing.
- **Tests / evidence:** helper self-tests; safe/vulnerable workflow fixtures; synthetic `json.py` shadow exploit regression.
- **Limitations:** helper prose still describes historical provider tiers/human merge authority; superseded as governance by current vendor-neutral execution protocol. Checker covers enumerated workflows/secrets, not arbitrary future ones.
- **Do not reinvent:** reuse parsing/redaction where useful; preserve secret isolation; do not treat legacy tier ordering as authority.
- **Search anchors:** `Manual Senior Review`, `CHEAP_REVIEW_API_KEY`, `GLM_API_KEY`, `REVIEW_TIER`, `_prove_untrusted_shadow_is_not_on_execution_path`.

## Capability: Codex result delivery / direct autopush — REAL bounded seams; direct path legacy-adjacent
- **What / when:** Newer comment-bound result delivery accepts eligible immutable Codex/owner comment and dispatches trusted cloud bridge; older manual autopush materializes an already-local Codex commit through repository delivery.
- **Canonical files:** `scripts/codex_result_delivery_dispatch.py`; `.github/workflows/codex-result-delivery.yml`; `scripts/codex_pr_autopush.py`; `.github/workflows/codex-autopush.yml`.
- **Invoke / reuse:** result path reacts to `jarvis-codex-result-delivery:v1` + `jarvis-cloud-delivery:v1`; direct path is manual dispatch.
- **I/O / persistence:** existing PR/comment/local commit → exact existing PR branch update + durable evidence comment.
- **Preconditions:** same-repo existing PR/branch; admitted author/comment; exact remote head.
- **Side effects / authority / risk:** result dispatcher has `actions:write` but no contents write and delegates mutation; direct autopush has `contents:write` but refuses master/main, force/delete, secret/env and workflow changes by default.
- **Tests / evidence:** autopush self-test; AE004 pins result workflow/dispatcher; downstream bridge owns CAS.
- **Limitations:** direct path is 022 compatibility surface; neither grants Codex merge authority.
- **Do not reinvent:** prefer admitted-comment → common bridge when compatible.
- **Search anchors:** `jarvis-codex-result-delivery:v1`, `codex-autopush:success`, `AE004_CODEX_RESULT_WORKFLOW`.

## Capability: Cloud-native delivery bridge — REAL / PARTIAL genericity
- **What / when:** Materializes owner-authorized patch from existing PR comment onto existing same-repo PR branch after digest/base/head/path/profile admission.
- **Canonical files:** `.github/workflows/cloud-delivery-bridge.yml`; `scripts/cloud_delivery_bridge.py`.
- **Invoke / reuse:** trusted-master dispatch with PR, payload comment id and exact body SHA-256; admission freezes patch+manifest before candidate code executes.
- **I/O / persistence:** comment/PR metadata → immutable admitted patch/manifest → validation → CAS branch update.
- **Preconditions:** existing same-repo PR; trusted master; exact admitted base/head and payload grammar.
- **Side effects / authority / risk:** high-risk branch mutation; refuses governance/`.github`/conformance control paths, unsupported classes, mixed frontend/backend payloads and profile mismatch.
- **Tests / evidence:** separate admission/verify phases, frozen bridge owner, exact base and CAS before push.
- **Limitations:** still contains `frontend-143` specialization; trust shape is reusable, profile logic is not fully generic.
- **Do not reinvent:** reuse admitted-payload/CAS boundary; generalize declaratively rather than cloning bridges.
- **Search anchors:** `jarvis-cloud-delivery:v1`, `payload_body_sha256`, `validation_profile`, `frontend-143`.

## Capability: Exact-head trusted browser proof + declarative plans — REAL
- **What / when:** Real Chromium acceptance proof for open same-repo PR exact head using trusted-master declarative plan; command wrapper provides owner-label dispatch path.
- **Canonical files:** `.github/workflows/exact-head-browser-proof.yml`; `.github/workflows/exact-head-browser-proof-command.yml`; `.github/workflows/browser-proof-contract.yml`; `.github/browser-proof/run.mjs`; `validate-plan.mjs`; `plans/*.json`.
- **Invoke / reuse:** trusted dispatch with PR/exact head/plan id, or owner-applied command label; add plans rather than per-spec controller logic.
- **I/O / persistence:** PR metadata + candidate head + plan → browser manifest/artifacts; isolated temp data/runtime roots.
- **Preconditions:** same-repo open PR, exact lowercase SHA, trusted plan validation, Chromium runner dependencies.
- **Side effects / authority / risk:** candidate checkout has `persist-credentials:false`, executes as unprivileged `jarviscandidate`; candidate cannot write trusted controller/plan workspace; GitHub/provider tokens are blanked from candidate runtime.
- **Tests / evidence:** contract workflow validates closed vocabulary/mutation window/request policy; command wrapper checks trusted controller, owner label, same-repo/open PR and fresh head; executor verifies checkout identity, credential-header absence, controller cleanliness/ownership, candidate health and Playwright result.
- **Limitations:** same-repo/hosted-runner dependent; not semantic/security review.
- **Do not reinvent:** generic executor + declarative proof plan; 113/124/140/143 are migration/compatibility scenarios, not controller forks.
- **Search anchors:** `PROOF_PLAN_ID`, `validate-plan.mjs`, `jarviscandidate`, `PROOF_EXPECTED_HEAD_SHA`.

## Capability: Scheduled/event-driven continuation — REAL but legacy phase-sensitive
- **What / when:** Reconstructs an active front, optionally wakes from terminal CI, lets Claude generate only an untrusted local patch, then separately validates and trusted-pushes with exact-head CAS/OIDC provenance.
- **Canonical files:** `.github/workflows/daily-development-continuation.yml`; `.github/workflows/event-driven-continuation.yml`; continuation planner/runner scripts and tests.
- **Invoke / reuse:** schedule/manual; event wake on completed `CI`; mode may be OFF/SHADOW/noop.
- **I/O / persistence:** GitHub/STATUS/check state → plan; patch capped 200 KB/20 files → artifact → validated commit; durable PR markers include workflow-bound OIDC proof.
- **Preconditions:** admitted active work, configured mode; Claude OAuth only in generation job; exact input head.
- **Side effects / authority / risk:** generator is read-only and checked for absent remote mutation; trusted push job has `contents:write` + OIDC and copies trusted validators/delivery owner before patch apply; immutable control paths refused.
- **Tests / evidence:** pre/post generation head checks, patch caps, spec/status validator, backend/BLUECAD/frontend validation, repository-delivery CAS.
- **Limitations:** historical one-active-front/model/scheduling assumptions; not current scheduling authority merely because code exists.
- **Do not reinvent:** reusable trust pattern is untrusted generation → deterministic validation → trusted CAS mutation.
- **Search anchors:** `CONTINUATION_WORKFLOW_VERSION`, `continuation.patch`, `ci-guarded-push`, `Jarvis-OIDC`.

## Capability: Merge-authority policy/live verifier + post-merge reconciliation — REAL, bounded
- **What / when:** Read-only verifier compares declared master protection with GitHub live state; separate post-merge workflow can perform only exact STATUS `in_review → merged` reconciliation for recognized merged implementation PRs.
- **Canonical files:** `.github/merge-authority-policy.json`; `scripts/verify_merge_authority.py`; `.github/workflows/merge-authority-verify.yml`; `.github/workflows/post-merge-status-reconcile.yml`.
- **Invoke / reuse:** verifier on master/manual; reconciliation only after admitted implementation merge and exact expected STATUS line.
- **I/O / persistence:** policy+GitHub state → `VERIFIED|UNKNOWN|MISMATCH|ERROR`; reconciliation creates deterministic branch/PR rather than writing master directly.
- **Preconditions:** GitHub API read; reconciliation exact branch/file/status shape.
- **Side effects / authority / risk:** verifier read-only. Reconciler has bounded write authority and refuses drift rather than overwriting it.
- **Tests / evidence:** strict policy schema/live workflow. Fresh 2026-09-15 API inspection observed active `JarvisOS master merge authority` ruleset requiring `backend` and `evidence`, no bypass actors, `current_user_can_bypass=never`; repository settings have auto-merge disabled.
- **Limitations:** ruleset `strict_required_status_checks_policy:false`; exact-head freshness remains process/application responsibility. Reconciler is not a generic STATUS editor.
- **Do not reinvent:** query live verifier for protection truth; reuse bounded reconciliation only for its exact state transition.
- **Search anchors:** `jarvisos.merge-authority.v1`, `required_check_contexts`, `Merge Authority Verify`, `post-merge-status-reconcile`.

## Capability: External-tool proof + data-root recovery — REAL operations primitives
- **What / when:** BLUECAD workflow proves real distro Gmsh/CalculiX availability; recovery CLI snapshots/verifies/restores canonical local data root.
- **Canonical files:** `.github/workflows/bluecad-real-tool-proof.yml`; `scripts/jarvisos_data_root.py`; `scripts/data_root_recovery/`; `docs/DATA_ROOT_RECOVERY.md`; recovery tests.
- **Invoke / reuse:** BLUECAD workflow on relevant paths/manual; `python scripts/jarvisos_data_root.py snapshot|verify|restore ...`.
- **I/O / persistence:** external binary hashes/versions/registry → proof; SQLite+`workspaces/`+`artifacts/` → manifest+`COMPLETE`, then verified atomic restore with root-bound path rebasing.
- **Preconditions:** Ubuntu apt for proof; backup destination outside source; writers stopped for restore; target absent/empty unless destructive flag.
- **Side effects / authority / risk:** runner-local apt install; restore mutates filesystem/database and needs `--allow-nonempty-target` for replacement; snapshot source is never deleted/modified.
- **Tests / evidence:** full offline backend regression before external proof; executable/hash/health deck checks; backup hashes/sizes, SQLite integrity/migrations/rows/FKs/artifact reads/staging rename.
- **Limitations:** external proof is less hermetic due apt; recovery has no cloud scheduler/encryption/compression and excludes machine/user-bound credentials.
- **Do not reinvent:** use real-tool proof and recovery package instead of mocks/ad-hoc copies.
- **Search anchors:** `BLUECAD Real Tool Proof`, `health.inp`, `jarvisos_data_root.py`, `create_snapshot`, `restore_snapshot`, `COMPLETE`.

## Capability: Windows local launch/dev tooling — REAL convenience / PARTIAL diagnostics
- **What / when:** Starts backend/frontend from repo root with dependency checks; combined launcher opens separate consoles.
- **Canonical files:** `Start-JarvisOS.cmd`; component `.cmd`; `scripts/start-backend.ps1`; `scripts/start-frontend.ps1`.
- **Invoke / reuse:** double-click or component scripts; backend creates `backend/.venv`, upgrades pip/requirements, bootstraps and runs Uvicorn `127.0.0.1:8000`; frontend installs npm deps if absent, starts Vite and opens `localhost:5173`.
- **I/O / persistence:** local venv/node_modules/runtime data; processes/browser.
- **Preconditions:** Windows PowerShell, Python >=3.11, Node/npm, package network on install/update.
- **Side effects / authority / risk:** local package installation/runtime startup; backend dependency install is convenience-first, not hermetic.
- **Tests / evidence:** concrete launch scripts; no dedicated launcher test or general `doctor` subsystem found in inspected repository.
- **Limitations:** Windows-first; combined launcher waits fixed 3 seconds instead of backend health probe; diagnostics are distributed across bootstrap/tests/proof/recovery rather than one operator doctor.
- **Do not reinvent:** use launchers for ordinary local startup; use CI/proof/recovery for reproducible acceptance/diagnostics.
- **Search anchors:** `Start-JarvisOS.cmd`, `start-backend.ps1`, `app.core.bootstrap`, `npm run dev`.

## Capability: Secret, credential and builder-egress boundaries — REAL but distributed
- **What / when:** Existing control plane minimizes credential exposure by separating trusted controller code from candidate/untrusted data and limiting write permissions per workflow.
- **Canonical files:** repository delivery/GitRunner; `check_review_secret_boundary.py`; Claude/manual review workflows; browser-proof workflows; cloud bridge; continuation workflows; CI architecture egress checker.
- **Invoke / reuse:** use the existing boundary matching the task: provider secret only in trusted review/generation step; candidate checkout `persist-credentials:false`; result dispatcher delegates contents mutation; repository delivery scrubs credential/network env.
- **I/O / persistence:** provider/GitHub credentials remain ephemeral workflow environment; no provider secrets are repository state.
- **Preconditions:** trusted master controller and configured GitHub secrets where external provider is used.
- **Side effects / authority / risk:** external egress exists for Claude/GLM review/generation, GitHub API, npm/pip/apt and browser-proof dependency/runtime needs. Architecture AE002 statically restricts unauthorized application HTTP/egress call sites; workflow egress itself is bounded by workflow code/permissions, not a universal network sandbox.
- **Tests / evidence:** secret-boundary exploit fixtures; architecture enforcement; browser candidate token blanking/ownership checks; repository-delivery env/config tests; workflow permission review.
- **Limitations:** no repository-wide deny-by-default network firewall for all Actions jobs; future secret-bearing workflows must be added to deterministic guards rather than assumed covered.
- **Do not reinvent:** preserve trusted-code/untrusted-data split and least-privilege workflow permissions; never expose PAT/provider secret to model-authored candidate code.
- **Search anchors:** `persist-credentials: false`, `check_review_secret_boundary.py`, `AE002`, `GitRunner`, `jarviscandidate`.

## Capability: Jules / Copilot / Google / Antigravity worker integration — DEFERRED
- **What / when:** Current master contains maintainer scheduling prose for GitHub Education/Copilot Student and Google AI Pro/Jules, but no repository-side worker adapter/workflow/dispatcher/credential seam was found.
- **Canonical files:** planning only: `docs/MAINTAINER_BETA_DELIVERY_DIRECTIVE_2026-09-15.md`.
- **Invoke / reuse:** none implemented in repository.
- **I/O / persistence:** none implemented.
- **Preconditions:** future accepted authority/integration work; account-side entitlement is not repository capability.
- **Side effects / authority / risk:** no current JarvisOS repository/provider credential authority for these workers.
- **Tests / evidence:** code/workflow search found terms only in directive/context prose, not runtime integration.
- **Limitations:** native external product integrations may exist account-side but are outside repository truth until wired/evidenced.
- **Do not reinvent:** future seams should reuse existing PR/CAS/CI/cloud-delivery/worktree/review boundaries rather than a second canonical queue.
- **Search anchors:** `MAINTAINER_BETA_DELIVERY_DIRECTIVE_2026-09-15`, `Jules`, `Copilot Student`, `Antigravity`.

## Gaps / duplication discovered
- `cloud-delivery-bridge.yml` has a reusable trust boundary but retains `frontend-143` profile specialization; cloning it would multiply control logic.
- Direct `codex-autopush.yml` overlaps newer comment-bound result delivery; the latter has narrower credential surface and delegates mutation.
- `cheap_review.py`/manual tier prose is operationally usable but governance language is superseded; do not derive authority/provider ordering from it.
- Continuation workflows contain strong reusable trust primitives plus obsolete/phase-sensitive one-active-front/model assumptions; reuse primitives, not scheduler policy.
- Shared-writer title mutex reduces races but is not atomic CAS; repository CAS remains mandatory.
- Launch tooling is convenience-first; there is no single comprehensive local doctor/health command.
- Actions/network egress controls are distributed and workflow-specific; there is no universal repository-level Actions network sandbox.
