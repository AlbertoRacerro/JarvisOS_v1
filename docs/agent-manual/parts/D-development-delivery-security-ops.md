# Area D — Development / delivery / GitHub / security / operations

MAPPING_STATUS: IN_PROGRESS

Source policy: runtime/scripts/workflows first; specs/strategy only for boundary context. Labels below describe observed implementation, not intended future state.

## Capability: Frontier builder execution + repository authority contract — REAL
- **What / when:** Common operating contract for repository builders: fresh-state orientation, reversible authority, recovery-before-duplication, proportional evidence, exact-head merge/reconciliation.
- **Canonical files:** `AGENTS.md`; `docs/AGENT_EXECUTION_AND_AUTOMATION_PROTOCOL.md`; concurrency only: `docs/POST_112_PARALLEL_DELIVERY_PROFILE.md`.
- **Invoke / reuse:** Read before authority-bearing work; Generic Frontier Builder Contract is in protocol §1. Do not fork it into vendor-specific governance.
- **I/O / persistence:** Reads GitHub/code/spec evidence; repository mutations persist through ordinary GitHub branches/PRs. `docs/specs/STATUS.md` remains live spec-state authority.
- **Preconditions:** accepted/readied scope for product implementation; exact current master/head for authority decisions.
- **Side effects / authority / risk:** governance itself is non-execution; coordinator may make ordinary reversible technical/merge decisions, but cannot weaken branch/ruleset controls or cross secret/destructive authority without separately granted capability.
- **Tests / evidence:** governance is enforced indirectly by deterministic delivery/CI/proof primitives below; green CI alone is explicitly insufficient semantic evidence.
- **Limitations:** prompts are not security boundaries; model/provider name grants no authority.
- **Do not reinvent:** use this contract rather than new agent lifecycle/queue/reviewer constitutions.
- **Search anchors:** `Generic Frontier Builder Contract`, `Exact-state and delivery truth`, `Frontier Coordinator`, `Minimum-necessary process rule`.

## Capability: Post-112 shared-writer concurrency — REAL (coordination), PARTIAL (correctness)
- **What / when:** Serializes shared GitHub/shared-authority writes across scheduler slots while permitting disjoint read-only/isolated work.
- **Canonical files:** `docs/POST_112_PARALLEL_DELIVERY_PROFILE.md`.
- **Invoke / reuse:** inspect A/B/C/D automation titles; claim own `[BUSY <UTC-ISO>]`; recheck topology; fresh lease <20 min, refresh around 10 min; restore base title on exit.
- **I/O / persistence:** automation titles are lease metadata only; no repository lock store.
- **Preconditions:** post-112 active; shared mutation actually conflicts.
- **Side effects / authority / risk:** prevents scheduler races operationally but is not correctness authority. Exact SHA/current remote/CAS/post-write verification remain mandatory.
- **Tests / evidence:** canonical profile describes mechanics; no claim here that automation-title service itself provides atomic compare-and-swap.
- **Limitations:** lease can be stale or concurrently claimed; disjointness is state/authority based, not filename-only.
- **Do not reinvent:** serialize only conflicting authority; do not add a second queue/lock/store for ordinary parallel work.
- **Search anchors:** `Global shared-writer mutex`, `[BUSY`, `Isolated worktree/worker principle`.

## Capability: Deterministic repository delivery safety primitive — REAL
- **What / when:** Typed Git mutation safety used by repository-development lanes; validates remote/ref/branch/path/config/history/CAS constraints instead of exposing generic Git.
- **Canonical files:** `scripts/repository_delivery.py`; tests under `backend/tests/test_repository_delivery*.py`.
- **Invoke / reuse:** import typed operations/results or its CLI rather than shelling arbitrary request-authored Git. `GitRunner` runs server-owned argv with `shell=False` and scrubbed Git/network/token environment.
- **I/O / persistence:** repository/worktree + remote refs in; `DeliveryResult`/refusal codes out; push mutates an existing admitted remote branch only when operation passes policy.
- **Preconditions:** approved GitHub HTTPS identity; exact expected remote head; safe non-protected branch/path set; credential adapter only where explicitly selected.
- **Side effects / authority / risk:** high-risk repository mutation. Refuses `.github/**`, CODEOWNERS/control paths, secret-like non-source paths, unsafe Git config, history replacement/non-FF/stale head. Production local credential path uses a validated Windows GCM executable and suppresses Git stdout/stderr on failure to avoid credential leakage.
- **Tests / evidence:** repository-delivery tests plus CI architecture/lint surface; `CONTROL_PATHS` includes actuator/autopush/continuation owners and their tests.
- **Limitations:** intentionally not a generic Git wrapper; local-path remote is test-only. Credentialed local delivery is host/platform dependent.
- **Do not reinvent:** all local-worker/delivery lanes should reuse this policy owner instead of custom push/CAS/sensitive-path logic.
- **Search anchors:** `DeliveryCode`, `GitRunner`, `assert_safe_paths`, `STALE_REMOTE_HEAD`, `NON_FAST_FORWARD_REFUSED`, `WindowsGCMAdapter`.

## Capability: Local persistent worktree actuator — REAL, bounded
- **What / when:** Binds a physical persistent worktree to one registered worker and serializes authority-bearing operations with a host-shared OS lock.
- **Canonical files:** public compatibility API `scripts/local_worktree_actuator.py`; immutable control core `.github/local_worktree_actuator_core.py`; IPC seam `scripts/local_worktree_ipc.py`; tests `backend/tests/test_local_worktree_actuator.py`, `test_local_worktree_ipc.py`, `test_worktree_writer_guard.py`.
- **Invoke / reuse:** use `LocalWorktreeActuator`/IPC typed operations; physical worktree must be registered/claimed. Reuse `repository_delivery.py` for Git safety.
- **I/O / persistence:** worker/repository/worktree registrations and audit state; host ownership record keyed by common git-dir + worktree path. Host state root is `%LOCALAPPDATA%/JarvisOS/local-worktree-actuator-host` on Windows or XDG/`~/.local/state/jarvisos/...` elsewhere.
- **Preconditions:** private non-symlink host state directory; worker identity matches registration; durable ownership claim exists for writer authority.
- **Side effects / authority / risk:** filesystem/Git writer; nonblocking `msvcrt`/`flock` guard is live serialization, durable lease is interruption metadata only. Host state is chmod 0700 on POSIX.
- **Tests / evidence:** focused actuator/IPC/writer-guard regressions are explicit control paths.
- **Limitations:** optional local-worker plane; worker offline removes only worker-dependent capabilities. Not generic remote execution and not authority to create arbitrary branches.
- **Do not reinvent:** reuse actuator + repository-delivery primitives for persistent local coding workers.
- **Search anchors:** `LocalWorktreeActuator`, `_exclusive_writer_guard`, `_claim_physical_worktree`, `WORKTREE_IDENTITY_MISMATCH`, `local_worktree_ipc`.

## Capability: Scope-aware GitHub CI — REAL
- **What / when:** PR/master/manual/nightly CI chooses docs/backend/frontend/BLUECAD domains from exact base→head changed paths, failing closed to full CI for ambiguous scheduled/manual/unusual push cases.
- **Canonical files:** `.github/workflows/ci.yml`; `scripts/classify_ci_scope.py`.
- **Invoke / reuse:** automatic on PR and master push; manual dispatch; nightly cron. Classifier self-test runs before classification; rename collapsing disabled so cross-domain moves cannot obtain a narrower lane.
- **I/O / persistence:** exact base/head + changed paths → `docs_only`, `run_backend`, `run_frontend`, `run_bluecad`, `full_required`; check conclusions persist in GitHub Actions.
- **Preconditions:** GitHub Actions; Python 3.11 and Node where selected.
- **Side effects / authority / risk:** read/test/build only; no product provider execution implied.
- **Tests / evidence:** backend gate includes spec-status, review-tool offline self-tests, PR-attention anti-authority, license-boundary import scan, frontend contract codegen drift, typecheck debt ratchet, architecture enforcement, Ruff, sharded backend tests; frontend/BLUECAD jobs continue in workflow.
- **Limitations:** scope classifier reduces work but cannot prove semantics; docs-only intentionally skips unrelated runtime domains after governance gates.
- **Do not reinvent:** add domain checks to the existing classifier/CI owner rather than parallel all-purpose workflows unless a distinct trust boundary requires it.
- **Search anchors:** `classify_ci_scope.py`, `docs_only`, `full_required`, `check_typecheck_ratchet.py`, `check_architecture_enforcement.py`, `generate_frontend_contracts.py`.

## Capability: Exact-head trusted browser proof — REAL
- **What / when:** Real Chromium proof for browser-observable acceptance criteria, bound to an open same-repo PR exact head and a declarative proof plan owned by trusted master.
- **Canonical files:** `.github/workflows/exact-head-browser-proof.yml`; command wrapper `.github/workflows/exact-head-browser-proof-command.yml`; controller `.github/browser-proof/run.mjs`, `validate-plan.mjs`, `.github/browser-proof/plans/*.json`.
- **Invoke / reuse:** dispatch trusted default-branch workflow with `pr_number`, exact `expected_head_sha`, and trusted `plan_id`. Add task-specific declarative plans rather than per-spec control logic when existing plan primitives suffice.
- **I/O / persistence:** fresh PR metadata + candidate head + plan → browser artifacts/manifest uploaded by workflow; isolated `/tmp` data root/runtime.
- **Preconditions:** same-repository open PR; exact lowercase SHA; plan validates from master; Linux runner can install Chromium/dependencies.
- **Side effects / authority / risk:** candidate is checked out with `persist-credentials:false`, built/run as unprivileged `jarviscandidate`; candidate cannot write trusted workspace/controller/plan. Tokens are blanked in candidate install/runtime/proof environment. Controller identity is rechecked before verdict.
- **Tests / evidence:** workflow itself verifies fresh head, checkout identity, credential-header absence, controller cleanliness/ownership, candidate health, and runs trusted Playwright.
- **Limitations:** same-repo PR heads only; hosted-runner/environment dependent; browser proof does not replace semantic/security review.
- **Do not reinvent:** reuse executor + declarative plans; treat historical 113/124/140/143 plans as compatibility scenarios, not architecture owners.
- **Search anchors:** `PROOF_PLAN_ID`, `validate-plan.mjs`, `jarviscandidate`, `PROOF_EXPECTED_HEAD_SHA`, `persist-credentials: false`.

## Capability: Cloud-native delivery bridge — REAL but legacy/specialized profile surface
- **What / when:** Materializes an owner-authorized patch carried in an existing PR comment onto an existing same-repo PR branch after digest, exact-base, path and fixed-profile admission.
- **Canonical files:** `.github/workflows/cloud-delivery-bridge.yml`; `scripts/cloud_delivery_bridge.py`.
- **Invoke / reuse:** dispatch from master with existing PR number, payload comment id, and owner-authorized SHA-256 of exact comment body. Admission freezes patch+manifest artifact before candidate code executes.
- **I/O / persistence:** GitHub comment/PR metadata → admitted patch/manifest → validated candidate → target branch update (later workflow stage). Immutable artifact retained briefly.
- **Preconditions:** same-repo existing PR; trusted workflow on master; payload grammar accepted by script; exact base/head expectations.
- **Side effects / authority / risk:** high-risk branch mutation. Workflow refuses governance/`.github`/conformance control paths, unsupported path classes, mixed frontend/backend payloads, and validation-profile mismatch.
- **Tests / evidence:** admission + verify phases; exact frozen trusted bridge owner and exact admitted base; fixed validation profile before materialization.
- **Limitations:** current workflow still contains `frontend-143` special-case/profile and therefore is not fully generic. Treat as reusable bounded bridge with known migration debt, not a template for more per-spec bridges.
- **Do not reinvent:** prefer this existing admitted-payload/CAS boundary where applicable; generalize declaratively rather than cloning a new cloud delivery workflow.
- **Search anchors:** `jarvis-cloud-delivery:v1`, `payload_body_sha256`, `validation_profile`, `frontend-143`, `cloud_delivery_bridge.py admit`.

## Capability: Data-root snapshot / verify / restore — REAL
- **What / when:** Operator-triggered deterministic backup/recovery of minimum canonical local data root.
- **Canonical files:** CLI facade `scripts/jarvisos_data_root.py`; package `scripts/data_root_recovery/`; runbook `docs/DATA_ROOT_RECOVERY.md`; recovery tests under backend tests.
- **Invoke / reuse:** `python scripts/jarvisos_data_root.py snapshot|verify|restore ...`.
- **I/O / persistence:** SQLite backup plus `workspaces/` and `artifacts/`; manifest + `COMPLETE`; logs excluded. Restore rebases registered root-bound paths and publishes target atomically after verification.
- **Preconditions:** destination outside source; backend/writers stopped for restore; target absent/empty unless explicit destructive flag.
- **Side effects / authority / risk:** snapshot read/copy; restore filesystem/database mutation. Non-empty replacement requires `--allow-nonempty-target`; source snapshot is never modified/deleted by restore.
- **Tests / evidence:** verify checks manifest/version/files/hash/size, SQLite integrity, migrations, row counts; restore checks FK/integrity, artifact SHA reads, unresolved old-root references and uses partial staging/atomic rename.
- **Limitations:** no cloud backup, scheduler, daemon, encryption, compression or automatic destructive recovery. Persisted machine/user-bound credentials are not a portable backup assumption.
- **Do not reinvent:** use this CLI/package for data-root recovery and test fixtures instead of ad-hoc SQLite/file copies.
- **Search anchors:** `jarvisos_data_root.py`, `data_root_recovery`, `create_snapshot`, `verify_snapshot`, `restore_snapshot`, `COMPLETE`.

## Capability: Legacy tiered AI review helper — PARTIAL / superseded as governance
- **What / when:** `scripts/cheap_review.py` can construct scoped review packs and call OpenAI-compatible endpoints, posting append-only advisory comments.
- **Canonical files:** `scripts/cheap_review.py`; `.github/workflows/cheap-review.yml`; related manual/Claude review workflows/scripts.
- **Invoke / reuse:** only through current accepted review paths where credentials/provider policy actually admits it; offline self-tests run in CI.
- **I/O / persistence:** PR diff/spec/AGENTS excerpts → provider review → GitHub comments/labels depending workflow.
- **Preconditions:** configured provider/token and GitHub permissions.
- **Side effects / authority / risk:** external egress + GitHub comments/labels; provider failures are intended to be handled without turning model output into merge authority.
- **Tests / evidence:** `cheap_review.py --self-test`, `manual_review.py --self-test`, secret-boundary self-test in CI.
- **Limitations:** module docstring still describes historical fixed DeepSeek→GLM→Claude tiers and says human merge authority; this conflicts with current vendor-neutral proportional-review/technical-merge governance. Treat those comments/workflows as legacy implementation seams, not canonical policy. Do not infer current required reviewer ordering from them.
- **Do not reinvent:** reuse pack/parsing/redaction helpers only where still compatible; use current execution protocol for review authority.
- **Search anchors:** `COMMENT_MARKER`, `FIX_REQUEST_MARKER`, `REVIEW_TIER`, `manual_review.py`, `check_review_secret_boundary.py`.

## Remaining coverage
- Inspect full workflow inventory: PR-attention, Claude review, Codex autopush/result delivery, continuation/event-driven, merge-authority verify, BLUECAD proof; classify active vs obsolete.
- Inspect generic builder/toolbox scripts and repository-truth helpers, including exact CAS/post-push verification details.
- Inspect architecture/typecheck/codegen implementations and reusable test harnesses beyond CI invocation.
- Inspect secret/credential and egress/network controls affecting builders, including workflow permission boundaries.
- Inspect branch/ruleset/merge assumptions from live repository/ruleset APIs where connector permissions allow.
- Inspect local launch/diagnostic scripts and health tooling.
- Inspect Jules/Copilot/Google seams in code/workflows; distinguish implemented integration from current planning only.
- Rebase against fresh master before finalization; open/update one docs-only PR when coverage is materially complete.
