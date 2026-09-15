# Area D — Development / delivery / GitHub / security / operations

MAPPING_STATUS: IN_PROGRESS

Source policy: runtime/scripts/workflows first; specs/strategy only for boundary context. Labels describe observed implementation, not intended future state.

## Capability: Frontier builder execution + repository authority contract — REAL
- **What / when:** Common builder contract: fresh-state orientation, recovery-before-duplication, bounded authority, proportional evidence, exact-head merge/reconciliation.
- **Canonical files:** `AGENTS.md`; `docs/AGENT_EXECUTION_AND_AUTOMATION_PROTOCOL.md`; concurrency only `docs/POST_112_PARALLEL_DELIVERY_PROFILE.md`.
- **Invoke / reuse:** read before authority-bearing work; use the Generic Frontier Builder Contract rather than vendor-specific lifecycle rules.
- **I/O / persistence:** GitHub/code/spec evidence in; branch/PR mutations out. `docs/specs/STATUS.md` is live spec-state authority.
- **Preconditions:** accepted/readied scope for product work; fresh remote/head for authority decisions.
- **Side effects / authority / risk:** governance is non-execution; no prompt/model identity grants repository authority.
- **Tests / evidence:** deterministic delivery/CI/proof primitives below implement parts of the contract; green CI alone is not semantic proof.
- **Limitations:** prose is not a security boundary.
- **Do not reinvent:** no second agent queue/lifecycle/reviewer constitution.
- **Search anchors:** `Generic Frontier Builder Contract`, `Exact-state and delivery truth`, `Frontier Coordinator`.

## Capability: Post-112 shared-writer concurrency — REAL coordination / PARTIAL correctness
- **What / when:** Serializes conflicting shared GitHub/authority writes while permitting disjoint read-only/isolated work.
- **Canonical files:** `docs/POST_112_PARALLEL_DELIVERY_PROFILE.md`.
- **Invoke / reuse:** inspect scheduler titles; claim own `[BUSY <UTC-ISO>]`; recheck topology; fresh lease <20 min, refresh ~10 min; restore base title.
- **I/O / persistence:** automation titles only; no repository lock store.
- **Preconditions:** shared mutation actually conflicts.
- **Side effects / authority / risk:** operational race reduction only; exact SHA/CAS/post-write verification remain mandatory.
- **Tests / evidence:** profile defines mechanics; no atomic-CAS claim for title service.
- **Limitations:** stale/concurrent lease possible; disjointness is authority/state based, not filename-only.
- **Do not reinvent:** do not add a second queue/lock/store for ordinary parallel work.
- **Search anchors:** `Global shared-writer mutex`, `[BUSY`, `Isolated worktree/worker principle`.

## Capability: Deterministic repository delivery safety primitive — REAL
- **What / when:** Typed Git mutation owner validating remote/ref/branch/path/config/history/CAS constraints instead of exposing generic Git.
- **Canonical files:** `scripts/repository_delivery.py`; `backend/tests/test_repository_delivery*.py`.
- **Invoke / reuse:** import typed operations/results or CLI. `GitRunner` uses server-owned argv, `shell=False`, scrubbed Git/network/token environment.
- **I/O / persistence:** repo/worktree + remote refs → `DeliveryResult`/refusal codes; guarded push mutates only an existing admitted branch.
- **Preconditions:** approved GitHub HTTPS identity; exact expected remote head; safe branch/path/config; credential adapter selected explicitly.
- **Side effects / authority / risk:** high-risk mutation. Refuses protected refs, `.github/**`/control paths where applicable, secret-like non-source paths, unsafe config, history replacement/non-FF/stale head; local credential path validates Windows GCM and suppresses credential-bearing Git output.
- **Tests / evidence:** repository-delivery tests; shared owner reused by Codex autopush and continuation push.
- **Limitations:** intentionally not generic Git; local-path remote is test-only; host credential path is platform dependent.
- **Do not reinvent:** reuse for branch mutation/CAS/post-push truth.
- **Search anchors:** `DeliveryCode`, `GitRunner`, `guarded_push`, `STALE_REMOTE_HEAD`, `NON_FAST_FORWARD_REFUSED`, `WindowsGCMAdapter`.

## Capability: Codex PR autopush/result delivery — REAL, bounded; older direct autopush is legacy-adjacent
- **What / when:** Two seams exist. `codex_pr_autopush.py` can materialize an already-present local Codex commit to an existing PR branch through shared repository delivery. Newer comment-bound result delivery accepts an immutable eligible Codex/owner comment and dispatches the trusted cloud-delivery bridge.
- **Canonical files:** `scripts/codex_pr_autopush.py`; `.github/workflows/codex-autopush.yml`; `scripts/codex_result_delivery_dispatch.py`; `.github/workflows/codex-result-delivery.yml`; cloud bridge below.
- **Invoke / reuse:** direct autopush is manual `workflow_dispatch`; result-delivery is automatic on qualifying `issue_comment` markers `jarvis-codex-result-delivery:v1` + `jarvis-cloud-delivery:v1`.
- **I/O / persistence:** existing PR branch/comment → exact branch update or bridge dispatch; comments provide durable materialized/non-materialized evidence.
- **Preconditions:** existing same-repo PR/branch; owner or admitted Codex bot comment for result delivery; exact remote head.
- **Side effects / authority / risk:** direct autopush has `contents:write`; result dispatcher has no contents write and only `actions:write`, delegating mutation to bridge. Autopush refuses master/main, force/delete, secret/env paths and workflow changes by default.
- **Tests / evidence:** `codex_pr_autopush.py --self-test`; architecture AE004 pins exact result-delivery workflow/dispatcher digests; bridge validation owns downstream CAS.
- **Limitations:** direct autopush is lane-specific 022 compatibility surface; result-delivery is the safer current automatic seam. Neither makes Codex output merge authority.
- **Do not reinvent:** new cloud worker result lanes should target the existing admitted-comment → bridge seam when compatible, not gain direct contents credentials.
- **Search anchors:** `codex-autopush:success`, `jarvis-codex-result-delivery:v1`, `AE004_CODEX_RESULT_WORKFLOW`, `guarded_push`.

## Capability: Local persistent worktree actuator — REAL, bounded
- **What / when:** Binds one physical persistent worktree to one registered worker and serializes authority-bearing operations with a host OS lock.
- **Canonical files:** `scripts/local_worktree_actuator.py`; `.github/local_worktree_actuator_core.py`; `scripts/local_worktree_ipc.py`; focused actuator/IPC/writer-guard tests.
- **Invoke / reuse:** typed `LocalWorktreeActuator`/IPC operations; physical worktree must be registered/claimed; Git mutation delegates to repository delivery.
- **I/O / persistence:** worker/repo/worktree registrations + audit/ownership state under `%LOCALAPPDATA%/JarvisOS/local-worktree-actuator-host` or XDG/`~/.local/state/jarvisos/...`.
- **Preconditions:** private non-symlink host state; matching worker identity; durable ownership claim.
- **Side effects / authority / risk:** filesystem/Git writer; nonblocking `msvcrt`/`flock` is live serialization; durable lease is interruption metadata only; POSIX state chmod 0700.
- **Tests / evidence:** `test_local_worktree_actuator.py`, `test_local_worktree_ipc.py`, `test_worktree_writer_guard.py`.
- **Limitations:** optional local plane, not generic remote execution or branch-creation authority.
- **Do not reinvent:** persistent local coding workers reuse actuator + repository delivery.
- **Search anchors:** `LocalWorktreeActuator`, `_exclusive_writer_guard`, `_claim_physical_worktree`, `WORKTREE_IDENTITY_MISMATCH`.

## Capability: Scope-aware GitHub CI — REAL
- **What / when:** PR/master/manual/nightly CI chooses docs/backend/frontend/BLUECAD domains from exact base→head changed paths; ambiguous events fail closed to full CI.
- **Canonical files:** `.github/workflows/ci.yml`; `scripts/classify_ci_scope.py`.
- **Invoke / reuse:** automatic PR/master, manual dispatch, nightly. Classifier self-tests first; rename collapsing disabled.
- **I/O / persistence:** exact base/head + paths → `docs_only`, domain flags, `full_required`; conclusions become GitHub checks.
- **Preconditions:** Actions; Python 3.11/Node as selected.
- **Side effects / authority / risk:** read/test/build only.
- **Tests / evidence:** spec-status; review-tool self-tests; PR-attention anti-authority; review secret boundary; license scan; frontend codegen drift; mypy ratchet; architecture enforcement; Ruff; sharded backend; frontend/BLUECAD jobs.
- **Limitations:** scope optimization cannot prove semantics; docs-only skips unrelated runtime domains after governance gates.
- **Do not reinvent:** extend classifier/CI owner for new domains unless a distinct trust boundary requires another workflow.
- **Search anchors:** `classify_ci_scope.py`, `docs_only`, `full_required`, `backend`, `evidence`.

## Capability: Architecture enforcement gate — REAL
- **What / when:** AST/config-based fail-closed repository architecture guard against protected-table mutation, unauthorized HTTP/egress calls, legacy coordinator mutation surfaces and drift of pinned Codex result-delivery control files.
- **Canonical files:** `scripts/check_architecture_enforcement.py`; architecture exception config; CI backend gate.
- **Invoke / reuse:** run checker in CI/local deterministic validation; exceptions require exact `path::symbol`, rule id, classification, owner/removal spec and rationale.
- **I/O / persistence:** Python source/config → deterministic findings `AE001`–`AE004`; no mutation.
- **Preconditions:** repository source parseable; PyYAML for config paths.
- **Side effects / authority / risk:** read-only gate; stale/wildcard/ambiguous exceptions fail validation.
- **Tests / evidence:** checker self-tests/fixtures; exact SHA-256 constants pin `codex-result-delivery.yml` and dispatcher for AE004.
- **Limitations:** static analysis has explicit bounded rule coverage; exception inventory is accepted debt, not proof of absence of all architectural defects.
- **Do not reinvent:** add enforceable architecture invariants here rather than scattered grep checks where AST ownership applies.
- **Search anchors:** `AE001`, `AE002`, `AE003`, `AE004`, `EXACT_CANONICAL_MUTATION_OWNER_FILES`, `HTTP_MODULE_METHODS`.

## Capability: Backend typecheck debt ratchet — REAL
- **What / when:** Prevents per-file mypy error counts from increasing while allowing known debt to be reduced incrementally.
- **Canonical files:** `scripts/check_typecheck_ratchet.py`; `backend/mypy-baseline.json`; CI.
- **Invoke / reuse:** run checker against current tree/base SHA; baseline has exact schema/source SHA/mypy version/per-file counts.
- **I/O / persistence:** mypy diagnostics + baseline → regression list/pass; baseline is repository state.
- **Preconditions:** pinned/known mypy environment; exact lowercase base SHA for historical comparison.
- **Side effects / authority / risk:** read-only; malformed/unparseable diagnostics and escaped backend paths fail closed.
- **Tests / evidence:** parser/baseline validation and CI invocation.
- **Limitations:** ratchets existing debt; it does not mean backend is fully type-clean.
- **Do not reinvent:** use the ratchet for incremental typing rather than ad-hoc ignores/new baselines.
- **Search anchors:** `RatchetError`, `mypy-baseline.json`, `compare_counts`, `source_sha`.

## Capability: Frontend contract code generation guard — REAL, deliberately narrow
- **What / when:** Generates a bounded TypeScript response contract from authoritative backend Pydantic `ParameterRead` and detects stale generated output.
- **Canonical files:** `scripts/generate_frontend_contracts.py`; `frontend/src/api/generated/modeling.ts`; backend model source.
- **Invoke / reuse:** `python scripts/generate_frontend_contracts.py`; CI checks drift.
- **I/O / persistence:** backend Pydantic annotations → generated TS file.
- **Preconditions:** supported scalar/Literal/single-nullable-union shapes only.
- **Side effects / authority / risk:** generator writes one generated file; unsupported annotations fail closed instead of widening types.
- **Tests / evidence:** generator focused tests + CI drift/build/type checks.
- **Limitations:** not general OpenAPI codegen; only selected contract.
- **Do not reinvent:** extend this owner deliberately if the same bounded source-authority pattern applies; do not hand-edit generated file.
- **Search anchors:** `ParameterRead`, `ContractGenerationError`, `render_parameter_read`, `GENERATED FILE — DO NOT EDIT`.

## Capability: PR Attention exact-head evidence — REAL, advisory/read-only
- **What / when:** Collects mechanical PR attention/gate/semantic/safety evidence at the exact PR event head without repository mutation authority.
- **Canonical files:** `.github/workflows/pr-attention.yml`; `scripts/check_pr_attention_integration.py`; external action pinned to immutable commit.
- **Invoke / reuse:** automatic on PR opened/synchronize/reopened; pass `expected-head` directly from event SHA.
- **I/O / persistence:** PR/check metadata → validated manifest artifact retained 3 days + step summary.
- **Preconditions:** GitHub Actions; pinned `AlbertoRacerro/jarvis-pr-attention/cycle@c544...`.
- **Side effects / authority / risk:** permissions are read-only; checker forbids `pull_request_target`, semantic-authority inputs and downstream mutation actions/commands.
- **Tests / evidence:** integration checker has negative fixtures for mutable pin/write permissions/head drift/mutation/authority inputs.
- **Limitations:** manifest fields are advisory only; cannot accept spec, review semantics, or merge.
- **Do not reinvent:** reuse this evidence surface for exact-head mechanical attention instead of another PR-state bot.
- **Search anchors:** `PR Attention Evidence`, `expected-head`, `FORBIDDEN_INPUTS`, `merge_candidate`.

## Capability: Claude exact-head semantic review — REAL, manual independent-review seam
- **What / when:** Maintainer-applied `expert-review` label triggers structured Claude semantic/security review only after exact-head `backend` + `evidence` checks are green.
- **Canonical files:** `.github/workflows/claude-review.yml`.
- **Invoke / reuse:** apply `expert-review` label to non-draft PR. Workflow deduplicates only a validated prior V3.2 marker from a successful run for identical head+base.
- **I/O / persistence:** exact PR head/base + trusted policy/spec/diff → strict JSON verdict/findings → GitHub Actions bot comment `JARVIS_CLAUDE_REVIEW_V3_2_JSON` bound to head/base/run id.
- **Preconditions:** `CLAUDE_CODE_OAUTH_TOKEN`; successful exact-head backend/evidence checks.
- **Side effects / authority / risk:** provider egress; checkout has no persisted Git credential. Claude is instructed not to push/comment/merge; workflow owns publication. P0/P1 must BLOCK; P2/P3 may only PARK.
- **Tests / evidence:** deterministic pre-gate validates checks and prior marker provenance; publication validates exact schema/verdict consistency.
- **Limitations:** provider availability/quota can fail; advisory evidence, not deterministic correctness. `bypassPermissions` is inside an isolated Actions review job, so trust relies on workflow checkout/token boundaries.
- **Do not reinvent:** use this existing exact-head structured review seam when an independent Claude review is useful.
- **Search anchors:** `expert-review`, `jarvis.claude-review.v3.2`, `JARVIS_CLAUDE_REVIEW_V3_2_JSON`, `blocking`.

## Capability: Provider-secret review isolation — REAL for guarded legacy workflows
- **What / when:** Deterministic checker ensures provider-bearing manual review workflows execute trusted master code and treat reviewed PR as data, preventing PR-controlled Python/import execution with provider secrets.
- **Canonical files:** `scripts/check_review_secret_boundary.py`; `.github/workflows/cheap-review.yml`; `.github/workflows/senior-review.yml`.
- **Invoke / reuse:** CI self-test/check; guarded workflows must be `workflow_dispatch` only, master-gated, one trusted checkout with `persist-credentials:false`.
- **I/O / persistence:** workflow YAML → pass/fail; no mutation.
- **Preconditions:** workflow shape remains within parser contract.
- **Side effects / authority / risk:** checker is read-only; protected secret appears only in trusted `manual_review.py` step; adversarial fixture proves sibling untrusted `json.py` cannot shadow imports.
- **Tests / evidence:** safe/vulnerable fixtures + synthetic import-shadow exploit regression.
- **Limitations:** protects enumerated workflows/secrets, not every possible future workflow; cheap/senior provider tiers are legacy policy surfaces.
- **Do not reinvent:** any secret-bearing review path should preserve trusted-code/untrusted-data separation and add itself to deterministic enforcement.
- **Search anchors:** `WORKFLOWS`, `CHEAP_REVIEW_API_KEY`, `_prove_untrusted_shadow_is_not_on_execution_path`.

## Capability: Legacy tiered AI review helper — PARTIAL / superseded as governance
- **What / when:** `scripts/cheap_review.py` constructs scoped packs, calls OpenAI-compatible endpoints and can publish advisory review comments.
- **Canonical files:** `scripts/cheap_review.py`; `.github/workflows/cheap-review.yml`; `scripts/manual_review.py`; senior-review workflow.
- **Invoke / reuse:** only through currently admitted review paths; offline self-tests run in CI.
- **I/O / persistence:** PR diff/spec/AGENTS excerpts → provider result → advisory GitHub evidence.
- **Preconditions:** provider token/config where invoked.
- **Side effects / authority / risk:** external egress + comments; model output is not merge authority.
- **Tests / evidence:** `cheap_review.py --self-test`, `manual_review.py --self-test`, secret-boundary checker.
- **Limitations:** module prose still describes historical DeepSeek→GLM→Claude tiers and human merge authority, conflicting with current vendor-neutral/proportional technical-merge governance. Treat as legacy seam, not policy.
- **Do not reinvent:** reuse compatible pack/parsing/redaction helpers; authority comes from current execution protocol.
- **Search anchors:** `COMMENT_MARKER`, `FIX_REQUEST_MARKER`, `REVIEW_TIER`, `manual_review.py`.

## Capability: Exact-head trusted browser proof — REAL
- **What / when:** Real Chromium acceptance proof bound to an open same-repo PR exact head and a declarative trusted-master plan.
- **Canonical files:** `.github/workflows/exact-head-browser-proof.yml`; command wrapper; `.github/browser-proof/run.mjs`, `validate-plan.mjs`, `plans/*.json`; `browser-proof-contract.yml`.
- **Invoke / reuse:** trusted dispatch with `pr_number`, exact `expected_head_sha`, `plan_id`; add declarative plans rather than per-spec controller logic.
- **I/O / persistence:** PR metadata + candidate head + plan → browser manifest/artifacts; isolated temporary data/runtime roots.
- **Preconditions:** same-repo open PR; exact lowercase SHA; master plan validates; Chromium runner dependencies.
- **Side effects / authority / risk:** candidate checkout `persist-credentials:false`, runs unprivileged `jarviscandidate`; candidate cannot write trusted controller/plan workspace; GitHub/provider tokens blanked from candidate execution.
- **Tests / evidence:** verifies fresh head, checkout identity, credential-header absence, controller cleanliness/ownership, candidate health and trusted Playwright result.
- **Limitations:** same-repo PR only; hosted-runner dependent; not semantic/security review.
- **Do not reinvent:** generic executor + declarative plan is the reusable primitive; 113/124/140/143 plans are compatibility scenarios.
- **Search anchors:** `PROOF_PLAN_ID`, `validate-plan.mjs`, `jarviscandidate`, `PROOF_EXPECTED_HEAD_SHA`.

## Capability: Cloud-native delivery bridge — REAL but PARTIAL genericity
- **What / when:** Materializes an owner-authorized patch carried in an existing PR comment onto an existing same-repo PR branch after digest, exact-base, path and fixed-profile admission.
- **Canonical files:** `.github/workflows/cloud-delivery-bridge.yml`; `scripts/cloud_delivery_bridge.py`.
- **Invoke / reuse:** dispatch trusted master workflow with PR, payload comment id, SHA-256 of exact body; admission freezes patch+manifest before candidate code executes.
- **I/O / persistence:** comment/PR metadata → immutable admitted patch/manifest → validation → branch update.
- **Preconditions:** existing same-repo PR; trusted master; accepted payload grammar/exact base/head.
- **Side effects / authority / risk:** high-risk branch mutation; refuses governance/`.github`/conformance control paths, unsupported classes, mixed frontend/backend payloads and profile mismatch.
- **Tests / evidence:** admission/verify phases, frozen bridge owner, exact admitted base and CAS before push.
- **Limitations:** workflow still carries `frontend-143` specialization; not fully generic.
- **Do not reinvent:** reuse admitted-payload/CAS boundary; generalize declaratively rather than cloning bridges.
- **Search anchors:** `jarvis-cloud-delivery:v1`, `payload_body_sha256`, `validation_profile`, `frontend-143`.

## Capability: Scheduled/event-driven continuation control plane — REAL but legacy phase-sensitive
- **What / when:** Reconstructs one active development front, optionally wakes from terminal CI, lets Claude produce only a local untrusted patch, validates it in a separate job, then trusted code commits/pushes with exact-head CAS and OIDC-bound provenance markers.
- **Canonical files:** `.github/workflows/daily-development-continuation.yml`; `.github/workflows/event-driven-continuation.yml`; `scripts/daily_development_continuation.py`; `scripts/event_bound_continuation_plan.py`; `scripts/event_driven_continuation.py`; focused tests.
- **Invoke / reuse:** scheduled/manual continuation; event wake on completed `CI` workflow. Mode variable can make plan OFF/SHADOW/noop.
- **I/O / persistence:** fresh GitHub/STATUS/PR/check state → plan/checkpoint; Claude working-tree diff capped at 200 KB/20 files → artifact → validated commit; durable PR markers use workflow-bound OIDC proof.
- **Preconditions:** active admitted spec/PR; configured continuation mode; Claude OAuth only for generation job; exact input head.
- **Side effects / authority / risk:** generator has read-only repo permissions and remote mutation is explicitly checked absent; trusted push job has `contents:write` + OIDC and copies trusted validators/delivery owner before applying patch. Immutable control paths are rejected.
- **Tests / evidence:** exact-head checks before/after generation, patch size/file caps, spec/status validator, full backend + BLUECAD canary + frontend build when changed, repository-delivery CAS.
- **Limitations:** encodes historical one-active-front/spec continuation semantics and specific Claude models; current maintainer phase may not use it as scheduling authority. Event wake has `actions:write` solely to wake existing continuation.
- **Do not reinvent:** useful pattern is untrusted patch generation → separate deterministic validation → trusted CAS mutation, not the historical scheduler policy itself.
- **Search anchors:** `CONTINUATION_WORKFLOW_VERSION`, `continuation.patch`, `event_driven_continuation.py`, `ci-guarded-push`, `Jarvis-OIDC`.

## Capability: Merge-authority declaration + live verifier — REAL; observe-only
- **What / when:** Declares expected master protection and read-only verifies GitHub live state; never changes settings or grants merge authority.
- **Canonical files:** `.github/merge-authority-policy.json`; `scripts/verify_merge_authority.py`; `.github/workflows/merge-authority-verify.yml`.
- **Invoke / reuse:** offline self-test on policy/verifier PRs; live on master push/manual dispatch.
- **I/O / persistence:** policy + GitHub branch/ruleset state → `VERIFIED|UNKNOWN|MISMATCH|ERROR` JSON/step summary.
- **Preconditions:** GitHub API read access; trusted master for live workflow.
- **Side effects / authority / risk:** read-only. Precedence is ERROR > MISMATCH > UNKNOWN > VERIFIED; no enforcement mutation.
- **Tests / evidence:** strict policy schema/target checks + live workflow. Fresh repository API inspection on 2026-09-15 shows active ruleset `JarvisOS master merge authority` on default branch requiring `backend` and `evidence`, no bypass actors, `current_user_can_bypass=never`.
- **Limitations:** policy explicitly `allow_auto_merge:false`, `normal_merge_owner_bypass:forbidden`, `merge_methods:observe_only`; ruleset has `strict_required_status_checks_policy:false`, so freshness/exact-head acceptance remains an application/process concern beyond GitHub's required contexts.
- **Do not reinvent:** use verifier for branch/ruleset truth instead of assuming protection from docs.
- **Search anchors:** `jarvisos.merge-authority.v1`, `required_check_contexts`, `_ruleset_evidence`, `Merge Authority Verify`.

## Capability: BLUECAD real external-tool proof — REAL, domain-specific operations proof
- **What / when:** GitHub-hosted strict proof installs real distro Gmsh/CalculiX and builds a hash-pinned runtime registry before running BLUECAD evidence.
- **Canonical files:** `.github/workflows/bluecad-real-tool-proof.yml`; BLUECAD tests/config/runbook.
- **Invoke / reuse:** automatic on BLUECAD/tool-registry paths or manual dispatch.
- **I/O / persistence:** Ubuntu packages + binary hashes/versions + generated registry → external-tool proof/check artifacts.
- **Preconditions:** Ubuntu 24.04 runner, apt network/package availability.
- **Side effects / authority / risk:** runner-local package install only; no repository write authority needed for proof.
- **Tests / evidence:** standalone dispatch first runs full offline backend regression; registry verifies executable presence and includes CalculiX health deck.
- **Limitations:** external apt/package availability makes it less hermetic than pure deterministic CI; domain-specific, not generic browser/review proof.
- **Do not reinvent:** reuse this workflow for actual Gmsh/CalculiX evidence rather than mocking external solver availability.
- **Search anchors:** `BLUECAD Real Tool Proof`, `gmsh`, `calculix-ccx`, `health.inp`.

## Capability: Data-root snapshot / verify / restore — REAL
- **What / when:** Operator-triggered deterministic backup/recovery of minimum canonical local data root.
- **Canonical files:** `scripts/jarvisos_data_root.py`; `scripts/data_root_recovery/`; `docs/DATA_ROOT_RECOVERY.md`; recovery tests.
- **Invoke / reuse:** `python scripts/jarvisos_data_root.py snapshot|verify|restore ...`.
- **I/O / persistence:** SQLite + `workspaces/` + `artifacts/` → manifest + `COMPLETE`; logs excluded. Restore rebases registered root-bound paths and atomically publishes verified target.
- **Preconditions:** destination outside source; backend/writers stopped for restore; target absent/empty unless destructive flag.
- **Side effects / authority / risk:** snapshot read/copy; restore filesystem/database mutation; non-empty replacement requires `--allow-nonempty-target`; source snapshot is never modified/deleted.
- **Tests / evidence:** hashes/sizes, SQLite integrity/migrations/row counts, FK/artifact reads, unresolved old-root checks, staging/atomic rename.
- **Limitations:** no cloud backup/scheduler/daemon/encryption/compression; machine/user-bound credentials are not portable backup state.
- **Do not reinvent:** use recovery package rather than ad-hoc DB/file copies.
- **Search anchors:** `jarvisos_data_root.py`, `create_snapshot`, `verify_snapshot`, `restore_snapshot`, `COMPLETE`.

## Capability: Windows local launchers — REAL, convenience tooling
- **What / when:** Starts local backend/frontend from repo root with user-facing dependency checks; combined launcher opens separate consoles.
- **Canonical files:** `Start-JarvisOS.cmd`, `Start-JarvisOS-Backend.cmd`, `Start-JarvisOS-Frontend.cmd`, `scripts/start-backend.ps1`, `scripts/start-frontend.ps1`.
- **Invoke / reuse:** double-click combined or component `.cmd`; backend PowerShell creates `backend/.venv`, upgrades pip, installs requirements, runs bootstrap then Uvicorn on `127.0.0.1:8000`; frontend installs npm deps if absent, starts Vite and opens `http://localhost:5173`.
- **I/O / persistence:** creates/updates local venv/node_modules and runtime data through normal bootstrap; launches processes/browser.
- **Preconditions:** Windows PowerShell, Python >=3.11, Node/npm for frontend; package-network access on first/update launch.
- **Side effects / authority / risk:** local package installation and runtime startup; backend launcher upgrades pip/requirements on every invocation, so it is convenient but not hermetic/reproducible CI.
- **Tests / evidence:** runtime scripts are concrete; no dedicated launcher test located yet.
- **Limitations:** Windows-first; combined launcher waits fixed 3 seconds rather than health-probing backend; no integrated stop/doctor command observed in inspected root/start scripts.
- **Do not reinvent:** use these for ordinary local startup; use CI/proof harnesses for reproducible acceptance.
- **Search anchors:** `Start-JarvisOS.cmd`, `start-backend.ps1`, `app.core.bootstrap`, `npm run dev`.

## Capability: Jules / Copilot / Google worker integration — DEFERRED / no runtime seam found
- **What / when:** Current master mentions GitHub Education/Copilot Student, Google AI Pro/Jules and Antigravity in the 2026-09-15 maintainer delivery directive, but code/workflow search found no implemented Jules/Copilot/Antigravity worker adapter, workflow, dispatcher or credential seam.
- **Canonical files:** planning/scheduling only: `docs/MAINTAINER_BETA_DELIVERY_DIRECTIVE_2026-09-15.md`.
- **Invoke / reuse:** none implemented in repository as of inspected master.
- **I/O / persistence:** none implemented.
- **Preconditions:** future accepted authority/integration work; do not infer entitlement activation from docs.
- **Side effects / authority / risk:** no current code path; therefore no repository/provider credential authority exists for these workers from JarvisOS code.
- **Tests / evidence:** repository code search returns only directive prose for Jules/Copilot/Google/Antigravity terms.
- **Limitations:** native external product integrations may exist account-side, but they are not repository capabilities until concretely wired/evidenced.
- **Do not reinvent:** future integration should reuse existing PR/CAS/CI/cloud-delivery/worktree/review boundaries instead of creating a second canonical queue.
- **Search anchors:** `MAINTAINER_BETA_DELIVERY_DIRECTIVE_2026-09-15`, `Jules`, `Copilot Student`, `Antigravity`.

## Gaps / duplication discovered
- `cloud-delivery-bridge.yml` is reusable in trust shape but still carries `frontend-143` specialization; cloning it would multiply control logic.
- Direct `codex-autopush.yml` and newer comment-bound Codex result delivery overlap; the latter has the narrower credential surface and delegates mutation to the common bridge.
- `cheap_review.py`/legacy review prose contains superseded provider-order/human-authority language; current execution protocol + exact-head Claude review are the safer authority reference.
- Continuation workflows contain strong reusable trust patterns but also historical one-active-front/model/scheduling assumptions; reuse primitives, not obsolete policy.
- Local launch scripts are convenience-first and not health-probed/hermetic.

## Remaining coverage
- Inspect the remaining workflow inventory not yet source-read end-to-end (`senior-review.yml`, browser-proof contract/command wrapper, any additional workflow files omitted by directory truncation) and classify obsolete vs active.
- Inspect repository-delivery implementation/tests deeper for remote identity, raw-history/config scrubbing and post-push verification details; inspect repository-truth helper scripts if separate owners exist.
- Inspect local actuator core/IPC tests directly rather than relying on already-established code mapping.
- Inspect generic reusable test harness/conftest fixtures and any diagnostics/health tooling outside the launch scripts.
- Recheck secret/egress boundaries across all mutation-capable workflows and GitHub permissions after full workflow inventory.
- Rebase/fresh-compare this branch to current master before declaring complete; update the single draft PR #657 only.
