# 141 LOCAL-WORKTREE-ACTUATOR-1

## Lifecycle

**Stage:** full specification frozen; implementation is **not** authorized by this artifact. `docs/specs/STATUS.md` remains the sole live work-state authority and 141 remains `planned` until a separate readiness decision proves the contracts below.

**Fresh derivation basis:** exact `master` `652bed1d5a082c19a0df2c7e7c8f93a9c6f3f399`, including the merged 141 definition, current repository-development protocol, the existing 022 Codex autopush actuator, and the 079 scheduled-continuation control plane.

## Problem and product boundary

JarvisOS can produce tested local work that is not durable remote evidence when an ephemeral model environment loses its checkout or cannot materialize its commit on GitHub. A task-local SHA is not `REMOTE_VERIFIED` delivery.

141 adds a small deterministic **local repository execution plane** that preserves registered worktrees and commits across requesting-model sessions and can perform a narrowly admitted ordinary branch push. It is repository-development infrastructure only. It does not grant JarvisOS product/runtime, provider, desktop, terminal, merge, self-update, or domain authority.

## Authority map and coexistence with 022 / 079

141 MUST NOT create a second independent Git-delivery policy stack.

The accepted ownership is:

- **022 remains owner of Codex review-to-autopush workflow semantics**: when Codex work should be materialized, workflow-sensitive/secret-path restrictions for that lane, review-loop behavior, and its no-automerge boundary.
- **079 remains owner of scheduled continuation orchestration**: candidate selection, continuation markers/checkpoints, OIDC-bound continuation evidence, and its own execution-mode policy.
- **141 owns only the optional local-worker plane**: worker registration/health, actuator worktree lifecycle, local capability admission, persistent local commit identity, local-user credential adapter, local writer lock, and local execution audit.
- **Git mutation safety primitives shared by these paths must have one deterministic implementation contract.** During 141 implementation, overlapping branch validation, protected/default-branch refusal, normal non-force push admission, remote-head readback, and result classification MUST be reused from an existing bounded primitive or factored into one small shared repository-delivery module. Copy/paste or a divergent second CAS/push implementation is not accepted.
- Environment-specific credential acquisition remains separate adapters behind that common mutation contract: GitHub Actions/OIDC/GITHUB_TOKEN ownership stays with the existing workflow lanes; 141 local workers use only the OS-owned local credential adapter defined below. 141 creates no shared credential database and never asks 022/079 to expose their tokens.
- 141 may strengthen a shared primitive where needed for `expected_remote_head` CAS and ambiguous-result handling, but must preserve existing 022/079 caller semantics unless a separately reviewed compatibility change proves otherwise.

A future separately authorized non-local browser-proof lane remains independent of 141. This spec does not assume that any future spec number or workflow is already registered or ready.

## Availability and worker topology

141 is an optional execution plane, never a global availability dependency.

- The control plane supports **zero, one, or multiple** registered trusted local workers.
- A maintainer personal Windows laptop is only an optional worker. It is never a required control-plane host and need not remain powered on.
- Each worker has a stable `worker_id`, host fingerprint/version, `online|offline|degraded` health, registered repository IDs, registered actuator worktrees, and an explicit capability set.
- Offline/degraded state affects only capabilities that require that worker. The result is typed `WORKER_OFFLINE` or `CAPABILITY_UNAVAILABLE`; it is never fabricated success or a global pipeline failure.
- With **zero workers online**, GitHub connector/API operations, GitHub-hosted Actions/CI, cloud semantic review, repository governance, and separately authorized non-local browser proof remain usable when otherwise authorized.
- A request is admitted only to a worker already registered for the repository/worktree/capability. Dirty or persistent worktree state is never silently copied, recreated, or migrated to another worker.
- Disconnect/reconnect preserves that worker's durable worktree/commit metadata. Any later push begins from a new remote-head read and new CAS admission.
- A future dedicated always-on host can be enrolled as another worker without changing the protocol.

Worker install/enrollment/startup and host-local Git credential bootstrap are **LOCAL CAPABILITY ACTIVATION** only. Their absence cannot block unrelated cloud/GitHub work.

## Process and IPC boundary

The MVP consists of one local-user worker service per host plus a thin deterministic client/tool adapter.

### Transport

- The worker MUST NOT expose an Internet-reachable listener.
- Windows MVP uses an OS-local IPC endpoint with current-user ACL (named pipe or an equivalently user-scoped local transport). POSIX implementations may use a Unix-domain socket with owner-only permissions.
- A generic TCP listener, even loopback-only, is out of scope for MVP unless a later readiness proof supplies equivalent peer identity and local-user isolation.
- Requests and responses are versioned structured objects. No request field is interpolated into a shell command.
- Every authority-bearing request carries `protocol_version`, `request_id`, `principal_id`, `session_id`, `worker_id`, `repository_id`, optional `worktree_id`, `capability`, and capability-specific typed arguments.
- The service derives host/user identity itself; caller-supplied identity is descriptive and cannot elevate capability.

### Principal/capability model

Server-side capability admission is authoritative:

- `observer`: worker/repository/worktree health plus bounded status metadata;
- `reviewer`: read-only status/diff and read-only named checks only;
- `implementer`: assigned-worktree writes, admitted named tests, stage/commit, and guarded push on the assigned non-default branch;
- no capability implies another; `reviewer` can never write, commit, or push.

The model/client cannot create capabilities, register a new repository, enroll a host, change credential adapters, or edit server policy through this protocol.

## Durable local state and registry

A local worker must survive requester/session loss without depending on the JarvisOS product backend being online. Therefore a tiny host-local state owner is minimum necessary; coupling this development-plane state to product SQLite would incorrectly make the optional worker depend on product runtime and would mix authorities.

The worker owns one OS-user-private state directory outside all registered repositories. It contains only:

1. `worker.json`: immutable/stable worker identity plus schema version;
2. `registry.json`: atomically replaced registration metadata for allowed repository roots, actuator worktree IDs/paths/branch bindings, capability policy references, and durable local commit identity;
3. `locks/`: local writer-lock metadata recoverable after crash;
4. `audit.jsonl`: append-only redacted action records, optionally hash-chained for corruption detection;
5. an empty trusted hooks directory used by controlled Git invocation.

No token, provider secret, GitHub PAT, SSH private key, browser cookie, or model credential may be persisted there.

Registration/enrollment is explicit maintainer activation outside model authority. Repository identity is `(canonical_remote_host, owner, repo, canonical_common_git_dir)` and not a caller path string. Registry updates use atomic replace + fsync-equivalent where supported. A corrupt/unknown schema fails closed; it is never silently rebuilt from caller input.

## Worktree lifecycle and filesystem containment

141-created worktrees live only under maintainer-registered actuator roots. `worktree_create` takes a registered `repository_id`, exact source ref/SHA, requested non-default branch name, and a new server-generated `worktree_id`.

The worker MUST validate:

- source ref resolves to the requested exact SHA before creation;
- branch is not `master`, `main`, current repository default branch, or any configured protected local boundary;
- worktree belongs to the registered Git common directory and expected repository identity;
- HEAD/branch binding matches registry before every write/commit/push;
- dirty state is explicit in status and cannot be silently absorbed into a new operation.

Lexical prefix checks are insufficient. For every write target, the worker resolves canonical filesystem identity beneath the assigned worktree and refuses path traversal or indirection escape. Windows implementation MUST inspect path components/file handles and reject symlink/junction/mount/reparse-point escape; POSIX implementation MUST reject symlink escape using `lstat`/no-follow semantics or an equivalently deterministic primitive. Case/normalization aliases that cannot be proven inside the assigned root fail closed.

A dirty/persistent worktree is bound to exactly one `worker_id`; another worker cannot claim it from registry metadata alone.

## Writer serialization and crash recovery

Exactly one implementer writer lease exists per `(worker_id, repository_id, worktree_id)`.

- Acquisition is atomic at the worker, with owner request/session metadata and monotonic lease generation.
- A second writer is refused `WORKTREE_BUSY`.
- Process death releases OS lock ownership; persistent metadata marks the previous operation interrupted until state is re-inspected.
- Recovery never discards local changes automatically. The next authorized implementer must first obtain fresh `status`, confirm registered HEAD/branch, and explicitly continue or abandon through a non-destructive operation.
- Local serialization does not replace remote CAS.

## Named test profiles: no arbitrary shell

The worker exposes only server-owned named profiles. The model supplies a profile name, never executable text, shell syntax, arbitrary argv, cwd, or environment.

Each profile freezes:

- executable as an absolute or installation-resolved allowlisted program;
- fixed argv template with only typed bounded substitutions defined by the profile;
- cwd = registered worktree or one fixed subdirectory;
- timeout and output-size cap;
- environment allowlist built from a minimal clean environment;
- whether the profile is `reviewer_readonly` or `implementer`;
- exact artifact/output paths it may create.

MVP does not invoke `cmd.exe`, PowerShell, `sh`, `bash`, a generic task runner supplied by the repository, or a PTY. If a useful test can only be expressed through arbitrary shell, it belongs to 126 or a separately authorized prerequisite.

Repository-controlled profile definitions are forbidden. A worktree cannot modify the currently running worker's profile registry.

## Controlled Git invocation

Git itself is an execution surface. Every Git operation runs through one internal `GitRunner`; callers cannot invoke Git directly.

### Configuration isolation

Before any mutating or network Git operation the worker:

1. validates the registered Git common directory and worktree identity;
2. parses local/worktree Git configuration and fails closed on executable/network-rewriting configuration outside a narrow allowlist;
3. disables system configuration and unrelated global configuration for the child process;
4. uses a trusted empty `core.hooksPath` for commit operations;
5. supplies only server-owned credential-helper configuration for the selected adapter;
6. scrubs secret-bearing/proxy/SSH/Git environment variables not explicitly required;
7. permits only a normalized HTTPS GitHub remote matching the registered `(host, owner, repo)` for MVP;
8. refuses a different push URL, `url.*.insteadOf`, proxy, SSH command, external filter/process helper, or other executable config that could redirect credentials or spawn an unapproved process.

The implementation must explicitly test dangerous local/worktree config including hooks, credential helper overrides, URL rewriting, proxy settings, SSH command, and filter/process commands. Unknown executable-capable config in an authority-bearing path fails closed rather than being guessed safe.

Checkout/worktree creation uses the same isolated/validated config boundary so repository-local filters/hooks cannot execute merely because a worktree is materialized.

### Credential ownership

The MVP local credential adapter is OS-owned and non-exporting. On Windows, prefer an explicitly allowlisted Git Credential Manager installation/path. A GitHub CLI credential adapter is allowed only if readiness proves an equally bounded invocation with no caller-controlled shell/helper string.

- The worker never reads or returns a raw token to the model/client.
- Credential helper stdout containing a secret is consumed only inside the Git/credential boundary and is never copied to ordinary logs/audit/errors.
- The model cannot select helper executable, account, host, token, or credential-store path.
- If no approved local credential adapter is available, `push` returns `LOCAL_CREDENTIAL_UNAVAILABLE`; all non-push local operations and all non-local cloud lanes remain unaffected.
- GitHub Actions credentials used by 022/079 stay in their existing workflow authority and are not persisted or brokered by 141.

## Git operations

MVP surface is restricted to typed equivalents of:

- `worktree_create`, `worktree_attach`, `worktree_inspect`;
- `git_status`;
- `git_diff` with bounded committed/worktree ranges;
- `stage_paths` for already containment-validated paths;
- `commit`;
- `push_branch`.

There is no generic `git(args)` capability.

### Commit contract

`commit` requires implementer capability, writer lock, correct registered branch/HEAD, explicit current status, and a non-empty staged diff. It refuses default/protected branch binding and reviewer mode. Commit author identity comes from maintainer-owned worker configuration, not model-provided Git config. Message is a bounded UTF-8 field with control characters rejected; it is passed as an argv/data field, never through a shell. Hooks are disabled through the trusted Git boundary. The result includes exact local commit SHA and bounded changed-path summary.

The local commit and worktree remain discoverable after the requesting model session disappears.

### Guarded normal push contract

`push_branch(repository_id, worktree_id, branch, intended_local_commit, expected_remote_head)` is the only push shape.

Admission order is deterministic:

1. implementer capability + writer lock;
2. registered worker/repository/worktree/branch identity matches request;
3. branch is non-default/non-protected and local HEAD exactly equals `intended_local_commit`;
4. worktree/Git config/remote/credential boundaries validate;
5. remote head is read fresh from the registered HTTPS remote;
6. fresh remote head MUST equal the supplied 40-char `expected_remote_head`; otherwise return `STALE_REMOTE_HEAD` with no push;
7. execute an ordinary same-branch non-force push; no `--force`, `--force-with-lease`, `+refspec`, deletion refspec, merge, or default-branch refspec exists in the API or implementation;
8. re-read remote head;
9. report `REMOTE_VERIFIED` only when remote head exactly equals `intended_local_commit`.

A normal Git non-fast-forward rejection remains a refusal even if the pre-read matched; this closes the read→push race without using force semantics.

### Ambiguous push result

Timeout/disconnect/process loss after a possible push is `PUSH_RESULT_UNKNOWN`, not success and not blind retry. Before a retry decision, remote head is re-read:

- remote == intended commit → classify the original effect `REMOTE_VERIFIED` idempotently;
- remote == expected old head → a newly authorized retry may repeat the ordinary push after all admission checks;
- any other remote head → `STALE_REMOTE_HEAD` / conflict; no retry mutation.

## API result vocabulary

At minimum the worker uses stable typed outcomes rather than prose-only errors:

`OK`, `REMOTE_VERIFIED`, `WORKER_OFFLINE`, `CAPABILITY_UNAVAILABLE`, `LOCAL_CREDENTIAL_UNAVAILABLE`, `REVIEWER_READ_ONLY`, `WORKTREE_BUSY`, `WORKTREE_IDENTITY_MISMATCH`, `PATH_ESCAPE`, `DIRTY_STATE_MISMATCH`, `PROTECTED_BRANCH`, `GIT_CONFIG_UNSAFE`, `REMOTE_IDENTITY_MISMATCH`, `STALE_REMOTE_HEAD`, `PUSH_REJECTED`, `PUSH_RESULT_UNKNOWN`, `SECRET_REDACTED`, `INTERNAL_ERROR`.

Unknown/unclassified authority failures fail closed and emit a redacted audit record.

## Audit contract

Every admitted or refused authority-bearing operation writes one redacted append-only record with:

- schema version, timestamp, request ID;
- principal/session/worker IDs;
- repository/worktree IDs and capability;
- operation name;
- branch and SHA before/after where applicable;
- expected/observed remote SHA where non-secret and relevant;
- admission decision/result code;
- exit code and bounded stdout/stderr digests rather than raw secret-bearing output;
- changed-path digest/count where applicable;
- previous-record digest / record digest if hash chaining is used.

Raw credentials, Authorization headers, credential-helper payloads, arbitrary environment dumps, file contents, provider data, and model prompts are forbidden from audit.

Audit is development evidence, not STATUS/lifecycle authority and not an authorization source for later requests.

## Security and authority hard refusals

141 structurally excludes:

1. merge, auto-merge, push to default/protected branch, force push, force-with-lease, remote branch deletion;
2. arbitrary shell, generic PTY, unrestricted subprocess/argv, or process-supervisor authority;
3. arbitrary filesystem outside registered actuator roots/worktrees;
4. self-update, restart, rollback, service replacement, installer update;
5. browser/desktop/mouse/keyboard/screen capture/general computer use;
6. provider credentials, model routing, egress, budget, promotion, product database/service/domain authority;
7. raw GitHub/Git credentials in model context, ordinary API response, audit, fixture, logs, or frontend state;
8. model-driven worker enrollment, repository registration, capability grant, credential-helper selection, or policy mutation;
9. Hermes ownership of JarvisOS policy, credentials, capability admission, audit, repository, database, or exact-head decisions.

125 SAFE-SELF-UPDATE-1 and 126 LOCAL-TERMINAL-PTY-1 remain separately gated and cannot be implemented through 141.

## Deterministic test matrix required before readiness

Readiness must map each item below to an exact automated test or an explicit host-only activation smoke where the OS credential layer cannot be represented in CI. CI tests use temporary repositories/bare remotes and no live GitHub credential/provider call.

### Availability/topology

- zero workers online: local capability typed unavailable while a mocked/non-local GitHub/CI/review/browser-proof capability registry remains independently available;
- one worker offline does not poison another worker or cloud lane;
- wrong-worker dirty/persistent worktree continuation refuses;
- reconnect preserves local commit/worktree identity and forces remote re-read before push.

### Identity/filesystem/roles

- wrong repository/common-dir/branch/HEAD binding refuses;
- `master`, `main`, and configured default branch refuse write/push;
- traversal, symlink, junction, mount/reparse escape refuses;
- case/normalization ambiguous escape refuses;
- reviewer write/stage/commit/push refuses;
- second writer on same worktree refuses deterministically;
- interrupted writer recovery preserves dirty state rather than discarding it.

### Command/Git safety

- unknown test profile and caller-provided argv/env/cwd refuse;
- no shell/PTTY executable path exists in accepted surface;
- repository/local Git hooks cannot run during worktree creation or commit;
- malicious credential helper override refuses;
- `url.*.insteadOf`, proxy, push-url, SSH command, and external filter/process config cannot redirect execution/network/credentials;
- unregistered/non-HTTPS/non-GitHub remote refuses for MVP;
- secret-bearing environment is scrubbed from child process except the internal credential path;
- raw credential sentinel never appears in response, log, audit, fixture output, or model-facing error.

### Commit/delivery

- explicit staged diff creates a deterministic local commit and returns exact SHA;
- requester/session loss simulation followed by worker restart still discovers worktree + local commit;
- stale `expected_remote_head` performs no push;
- remote movement in the pre-read→push race produces ordinary non-fast-forward refusal and no force path;
- force/force-with-lease/delete/merge/default-branch operations are absent/refused structurally;
- successful guarded push re-reads remote and reports success only when remote SHA == intended local commit;
- no-op/local-only commit is never classified remote verified;
- ambiguous push with remote==intended resolves idempotently to verified;
- ambiguous push with remote==expected may be retried only after a fresh authorized admission;
- ambiguous push with third-party remote head refuses retry.

### Compatibility / no duplicate owner

- 022 Codex autopush caller retains its workflow-specific restrictions and no-automerge semantics while using the common Git mutation contract where factored;
- 079 continuation caller retains candidate/marker/OIDC/orchestration semantics while using shared delivery primitives only where overlapping;
- local 141 credential adapter cannot access Actions/OIDC tokens, and Actions callers cannot read 141 local credentials;
- a static/architectural test fails if a second ordinary branch-push implementation bypasses the canonical shared mutation primitive in the accepted 141 paths.

## Host activation smoke

Local activation is optional and occurs only after repository implementation/review is accepted.

Minimum Windows activation proof:

1. install/start the worker under the maintainer's ordinary user account;
2. enroll one repository root/worktree root through the maintainer-only activation path;
3. verify approved GCM/GitHub credential adapter without printing a token;
4. run health + read-only status;
5. create a disposable non-default test branch/worktree, local commit, guarded push with known expected remote head, and post-push SHA verification;
6. shut worker down and confirm cloud/GitHub lanes are unaffected;
7. restart and confirm durable local metadata is revalidated.

Failure of this smoke means **local push capability unavailable**, not roadmap-wide failure. Repository implementation, CI, cloud review, and separately authorized browser proof can continue.

## Readiness gate

141 may move from `planned` to `ready` only in a separate readiness artifact that:

- identifies exact implementation files/modules and canonical shared Git-delivery primitive ownership;
- maps every deterministic test above to concrete test paths;
- proves no dependency on 125/126 or an unregistered future browser-proof spec;
- proves no second credential store or product database owner is introduced;
- documents the local state directory, permissions, schema/recovery contract, and redaction rules;
- freezes the first supported OS/credential adapter and exact activation smoke;
- records any remaining host-only limitation as LOCAL CAPABILITY ACTIVATION rather than a cloud/global blocker.

If readiness discovers that accepted behavior requires generic PTY, unrestricted filesystem/process authority, self-update authority, a new general credential store, remote desktop, or a second durable repository/lifecycle authority, readiness MUST refuse and derive a separate prerequisite.

## Non-goals

- no implementation in this full-spec PR;
- no readiness promotion in this full-spec PR;
- no workstation installation or credential bootstrap in this full-spec PR;
- no product/runtime UI or API authority;
- no generic MCP agent framework requirement (the core may later be exposed through MCP only as an adapter to these server-side capabilities);
- no self-hosted GitHub runner on the maintainer's normal personal PC;
- no replacement for GitHub Actions, semantic review, STATUS, exact-head gates, or maintainer merge policy;
- no automatic migration of existing 022/079 behavior beyond minimum shared-primitive reuse required to avoid duplicate Git-delivery ownership.

## Full-spec exit criteria

This full specification is complete when it freezes one independently removable, offline-tolerant local worker/worktree owner; a single compatible Git mutation safety contract shared rather than duplicated across overlapping delivery paths; fail-closed path/Git-config/credential/role/concurrency boundaries; deterministic CAS and ambiguous-push semantics; secret-free audit; and a concrete readiness test matrix.

`STATUS.md` remains `planned`. No implementation authority is granted until the separate readiness decision passes.