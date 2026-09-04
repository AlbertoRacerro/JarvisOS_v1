# 119 CODING-RUNTIME-TRUTH-1

Exact source master: `5a04850bbb7eb917e3cc072d75a89918ba74965f`.

Authority: full specification only. `119` remains `planned`; this document does not authorize implementation until a separate readiness gate proves the frozen boundary implementable on fresh master and the live registry becomes `ready`.

## Purpose

Give the Coding lane one backend-owned, bounded, observation-only answer to two distinct questions:

1. what JarvisOS code/worktree state is observable locally for the running backend; and
2. how that observed local identity relates to an exact approved remote target supplied by merged spec 118.

The implementation must preserve uncertainty. It must never turn branch names, configured version strings, timestamps, copied paths, or model prose into proof of executed code or alignment.

## Fresh-code findings that freeze this design

- `backend/app/api/system.py` already owns general system information such as configured app version/environment and storage/database/AI health. It does not prove Git SHA, dirty state, or executed-code identity. 119 must not duplicate those existing generic health fields.
- `backend/app/main.py` constructs the FastAPI app and owns process-start/lifespan initialization. It is therefore the only accepted place to capture immutable startup code/worktree evidence for the current backend process.
- `scripts/start-backend.ps1` launches `python -m uvicorn app.main:app --reload ...` in the supported development path. Consequently a later filesystem HEAD observation is not sufficient by itself to prove what the current process loaded; 119 must keep immutable startup evidence distinct from live worktree evidence.
- `backend/app/core/config.py` has no configured arbitrary source-root input. 119 must derive the backend repository root from trusted module location, not accept a frontend/model/user path.
- merged 118 owns remote GitHub repository/ref/SHA/compare truth in `backend/app/modules/coding/repository_truth.py`. 119 consumes that owner and must not create a second GitHub transport, remote index, cache, or diff engine.
- `backend/requirements.txt` contains no GitPython/Dulwich dependency. Adding a Git library is unnecessary for the frozen scope.
- `backend/app/modules/runner/local_python.py` proves the repository already accepts bounded, shell-free subprocess execution with explicit argv/cwd/environment and timeouts, but its execution-owner machinery is write/execution oriented and not reusable as the 119 observer. 119 may use a smaller dedicated fixed Git probe seam; it must not route observation through the production runner or create ownership/working-directory artifacts.

## Accepted ownership

### New backend module

`backend/app/modules/coding/runtime_truth.py` owns:

- trusted repository-root derivation from `Path(__file__).resolve()` / backend package ancestry;
- fixed read-only Git probes against that one derived root;
- immutable process-start snapshot type;
- live worktree snapshot type;
- deterministic alignment derivation against a caller-supplied exact remote target result from 118;
- typed local-observation failures;
- bounded metadata-only telemetry.

No persistent database/store is added.

### App/process initialization

`backend/app/main.py` captures one immutable `RuntimeStartupSnapshot` while constructing/starting the backend and stores it in `app.state`. That snapshot is never recomputed to make the running process appear aligned after the worktree changes.

The snapshot is evidence of the code/worktree state observed at backend process start. It is **not** byte-level proof that every lazily imported Python module equals repository HEAD. The result therefore exposes provenance explicitly as `process_start_observation`, not `verified_loaded_bytes`.

### Read surface

119 adds one narrow backend read surface under the Coding lane, implemented as a GET-only route owned by a new `backend/app/modules/coding/runtime_routes.py` and included by `backend/app/main.py`:

`GET /api/coding/runtime-truth?repository=<configured owner/name>&target_ref=<ref>`

The route:

1. validates `repository` against existing `settings.coding_repositories` exactly as 118 does;
2. accepts a bounded `target_ref` using the same ref validation contract as 118;
3. obtains exact approved remote target SHA through the existing `RepositoryTruthService.repository_ref_truth()` owner;
4. reads immutable process-start snapshot from app state;
5. captures a fresh live worktree snapshot from the same derived local root;
6. derives the frozen alignment result below.

No local filesystem path, command, executable, PID, service name, arbitrary refspec, or host selector is accepted from the request.

## Local Git probe boundary

119 may invoke only the system `git` executable through a dedicated private helper with:

- `shell=False`;
- explicit argv list;
- `cwd` fixed to the derived repository root;
- no inherited environment except a minimal allowlist required for deterministic execution;
- `GIT_OPTIONAL_LOCKS=0` so observation does not perform optional index refresh/locking;
- `GIT_TERMINAL_PROMPT=0`;
- fixed timeout `2.0 s` per probe;
- stdout and stderr bounded to `64 KiB` each; exceeding either bound is a typed `probe_output_oversized` failure;
- UTF-8 decoding with malformed output becoming a typed failure;
- no shell metacharacter interpretation and no model/user text interpolated into a command.

Accepted Git commands are exactly:

1. `git rev-parse --show-toplevel`
2. `git rev-parse --verify HEAD`
3. `git symbolic-ref --quiet --short HEAD`
4. `git status --porcelain=v1 --untracked-files=normal`

`symbolic-ref` exit code 1 means detached HEAD and is not a provider failure. Other nonzero outcomes are typed according to the failure taxonomy below.

The implementation must verify that `--show-toplevel` resolves exactly to the trusted derived repository root before accepting any subsequent Git observation. Symlink/path-resolution mismatch produces `root_mismatch` and no alignment claim.

### Index mutation constraint

The definition review correctly identified that ordinary `git status` may refresh/write the index. The full spec resolves this by requiring `GIT_OPTIONAL_LOCKS=0` on **every** Git probe and by testing that the probe seam supplies that environment. 119 does not permit an index-refresh carve-out. If a supported Git version/platform cannot produce dirty evidence under this constraint, dirty state becomes typed `unknown`; implementation must not silently fall back to a potentially mutating status probe.

## Snapshot contracts

### `RuntimeStartupSnapshot`

Fields:

- `root_identity`: SHA-256 digest of the normalized trusted local root; raw absolute path is not returned or logged;
- `observed_at`: UTC timestamp;
- `git_available`: boolean;
- `git_sha`: exact lowercase 40-char SHA or `None`;
- `head_state`: `branch | detached | unavailable`;
- `branch`: bounded branch name or `None`;
- `dirty_state`: `clean | dirty | unknown`;
- `provenance`: constant `process_start_observation`;
- `failure_code`: typed code or `None`.

### `LiveWorktreeSnapshot`

Same root/Git/SHA/ref/dirty fields, with `provenance=live_worktree_observation`.

Live observation may legitimately differ from startup observation. This difference is evidence, not something to reconcile automatically.

### Dirty semantics

Any non-empty porcelain output means `dirty`. The raw porcelain lines, filenames, status records, and repository contents are never returned or logged. Only the boolean-derived state is retained.

If dirty status cannot be proven because Git is absent, metadata is missing, status times out, output is malformed/oversized, or safe no-index-refresh probing is unavailable, dirty state is `unknown`.

## Remote target contract

The route consumes 118's exact `repository_ref_truth(repository, target_ref)` result and retains:

- configured repository identity;
- requested ref;
- resolved exact remote SHA;
- observation timestamp from 118.

119 never treats a branch name alone as target identity and never performs its own network request.

Before final response construction, the route may re-resolve the target ref once through 118. If that exact SHA differs from the first resolved target, the result is `unknown` with reason `remote_target_moved`; 119 does not compare against a moving target.

## Alignment state machine

Output state is exactly one of:

- `aligned`
- `local_behind`
- `divergent`
- `unknown`

The result also exposes startup/live/remote SHAs separately plus `dirty_state`, `worktree_changed_since_start`, and a typed `reason`.

### `aligned`

Allowed only when all are true:

1. startup SHA is known;
2. live worktree SHA is known;
3. startup SHA equals live worktree SHA;
4. live dirty state is `clean`;
5. startup dirty state is `clean`;
6. exact remote target SHA is stable across the accepted observation window;
7. startup SHA equals remote target SHA.

A matching SHA with dirty or unknown dirty evidence is never `aligned`.

### `local_behind`

Allowed only when all are true:

1. startup and live SHA are known and equal;
2. both dirty states are clean;
3. remote target is stable;
4. the local SHA is known to 118/GitHub; and
5. `RepositoryTruthService.compare_truth(local_sha, remote_target_sha)` returns complete evidence that remote target is ahead and the local SHA is its ancestor, with no contradictory behind/divergence evidence.

If 118 cannot resolve/compare the local SHA because it is unpushed or unavailable remotely, state is `unknown`.

### `divergent`

Allowed only for a clean, stable startup/live snapshot where 118 has complete remote compare evidence proving the local SHA is not the accepted ancestor behind relation and is not equal to target. This includes a remotely known local-ahead or diverged relation as represented by 118 compare evidence.

An unpushed local commit is **not** automatically divergent because GitHub cannot prove its relationship to the target.

### `unknown`

Required for every other case, including:

- Git unavailable/non-Git/package installation;
- root mismatch;
- malformed/timeout/oversized probe;
- startup or live SHA unknown;
- dirty state dirty or unknown;
- startup SHA differs from live worktree SHA;
- remote target moved during observation;
- 118 target/commit/compare evidence unavailable, partial, stale, or typed failure;
- local SHA exists only locally/unpushed and remote ancestry cannot be proven;
- any contradiction between evidence sources.

`unknown` is an accepted truth state, not an error to paper over.

## Worktree-changed-since-start semantics

`worktree_changed_since_start=true` when any of these differ between startup and live snapshots:

- SHA;
- dirty state;
- branch/detached state;
- branch name where applicable.

When true, alignment is `unknown` even if the current live worktree happens to equal the remote target, because the backend process-start identity no longer matches current disk evidence.

This is the minimum safe answer under the existing `uvicorn --reload` development launcher without claiming verified loaded-byte identity.

## Semantic delta projection

119 does **not** create a local diff engine and does not expose dirty filenames/content.

- For clean local SHA values that are already known to GitHub, 119 may project 118 `compare_truth()` metadata: status, ahead/behind counts, bounded changed filenames/status/patch projection exactly as 118 returns it, preserving `partial`.
- For dirty worktrees or unpushed/unknown local SHAs, semantic delta is `unavailable` with a typed reason (`dirty_local_state`, `local_sha_not_remote`, or corresponding failure). This directly resolves the definition review PARK item: the dominant local-only drift case is intentionally not over-promised.
- A partial 118 compare may be displayed as partial evidence but may not establish `local_behind` or `divergent`.

No second repository index/database, local patch crawler, or provider is allowed.

## Runtime health projection

119 does not duplicate `/api/system/info`. Its result contains only Coding-relevant observation health:

- `observer_status`: `ok | degraded | unavailable`;
- typed local failure code if any;
- remote-target observation status from 118;
- process-start/live observation timestamps.

Database, storage, AI gateway, generic environment, and configured version remain owned by the existing system API.

## Typed local failure taxonomy

The local observer uses deterministic codes:

- `git_unavailable`
- `not_git_worktree`
- `root_mismatch`
- `probe_timeout`
- `probe_output_oversized`
- `malformed_probe_output`
- `probe_failed`
- `dirty_state_unavailable`
- `startup_snapshot_unavailable`
- `remote_target_unavailable`
- `remote_target_moved`
- `remote_relation_unavailable`

These codes may lead to a successful HTTP response with `alignment=unknown` when observation itself completed safely. Existing 118 typed errors preserve their own provider semantics; 119 maps only the alignment consequence and does not relabel provider failures as local failures.

## Safety and mutation exclusions

119 exposes no code path for:

- `git fetch`, `pull`, `checkout`, `switch`, `reset`, `clean`, `stash`, `commit`, `merge`, `rebase`, `update-index`, `add`, `restore`, `config`, `worktree add/remove`, ref creation/deletion, hook invocation, or credential access;
- arbitrary executable/argv/cwd/environment selection;
- file write/delete/rename/chmod;
- package installation or build;
- process spawn except the four fixed bounded Git observations;
- service/process restart, kill, terminate, signal, supervisor/service-manager calls;
- production runner invocation;
- remote repository mutations or GitHub credentials.

The accepted fixed Git observer is READ/CONTEXT evidence only under 111. It grants no COMMIT/EXECUTE authority.

## Telemetry

One metadata-only log record per top-level runtime-truth request may contain:

- operation name;
- repository digest, not raw repository if current Coding telemetry policy requires digesting;
- target SHA prefix or digest, not source contents;
- root identity digest;
- observer status;
- alignment state/reason;
- dirty-state enum;
- probe duration and failure code;
- whether remote compare evidence was complete/partial/unavailable.

Never log raw absolute paths, command stdout/stderr, environment values, dirty filenames, repository content, patches beyond what 118 already owns in the returned product result, secrets, tokens, or arbitrary process data.

## Deterministic acceptance tests

Implementation readiness must map each case to a deterministic test before `ready`:

1. clean startup/live SHA equals stable target -> `aligned`;
2. same SHA but startup or live dirty -> `unknown`, never aligned;
3. startup SHA differs from live SHA -> `unknown` + `worktree_changed_since_start=true`;
4. clean local SHA proven ancestor of stable remote target by complete 118 compare -> `local_behind`;
5. clean remotely known local SHA with complete contradictory/ahead/diverged relation -> `divergent`;
6. unpushed/local-only SHA -> `unknown`, no local diff invention;
7. detached HEAD with known clean SHA -> accepted observation, branch `None`, relation derived only from SHA evidence;
8. non-Git/missing Git -> typed unknown/unavailable without crash;
9. trusted root mismatch/symlink escape -> `root_mismatch`, no further probes used for alignment;
10. target ref changes between initial/final 118 resolution -> `remote_target_moved` + unknown;
11. partial 118 compare -> may project partial delta but cannot prove behind/divergent;
12. Git timeout -> typed unknown and process is terminated without shell/process-control surface exposed to caller;
13. oversized/malformed Git output -> typed failure, no raw output leakage;
14. probe harness proves `shell=False`, fixed cwd, fixed argv family, minimal environment, `GIT_OPTIONAL_LOCKS=0`, and 2 s timeout;
15. status probe output with hostile filename/shell metacharacters is treated only as opaque bytes for dirty boolean and never executed/logged;
16. request cannot provide path/executable/argv/cwd/PID/service/environment;
17. mutation verbs are absent/unreachable from route/service dispatch;
18. raw absolute local path never appears in API output/log metadata;
19. system info existing database/storage/AI fields remain unchanged and are not duplicated by 119;
20. startup snapshot is immutable across live worktree change and cannot be recomputed by the request path to manufacture alignment.

## Readiness evidence required

A separate readiness artifact must revalidate on fresh master:

- implementation files/owners above still exist and no equivalent runtime-truth owner has appeared;
- 118 contracts used by target/ref/compare are unchanged or compatibility is explicitly mapped;
- app startup/lifespan permits one bounded startup snapshot without blocking/failing application startup when Git is unavailable;
- fixed Git probe behavior is testable on Windows and POSIX CI using injected probe transport/harness rather than depending on host Git quirks for every semantic test;
- startup capture failure degrades to typed unavailable and never prevents JarvisOS startup;
- exact route/request schema contains no arbitrary local-path or command authority;
- AE002/current security gates do not require a new network owner because 119 performs no direct network call;
- no new dependency is necessary;
- tests above are assigned to concrete files;
- implementation scope is small enough to review as one material PR.

Only then may `STATUS.md` move `119` from `planned` to `ready`.

## Non-goals

- Proving byte-for-byte identity of every Python module loaded in memory.
- Self-update, synchronization, deployment, restart, service/process control, watchdogs, package/build execution.
- Generic process inventory, arbitrary filesystem browsing, arbitrary command execution, shell/PTY, IDE-agent behavior.
- Local diff/index/database for dirty or unpushed content.
- A second GitHub transport/provider/cache or replacement for 118.
- Development pipeline lifecycle owned by 120 or later code mutation/execution slices.
- Frontend/model authority over local paths, probes, alignment state, or runtime mutation.

## Minimum-necessary test

The design adds only what 118 cannot provide: bounded local process-start/live worktree evidence and deterministic alignment against 118 exact remote truth. It reuses existing configuration, app startup, Coding repository truth, and subprocess safety principles; adds no dependency, persistent store, daemon, supervisor, remote provider, or mutation authority.