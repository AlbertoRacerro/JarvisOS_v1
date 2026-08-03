# Spec 082 — SECURE-CREDENTIAL-STORAGE-0

**Definition status:** complete implementation contract; registry remains `planned` until a separate readiness decision.

**Depends on:** 015, 018, 021, 059b, 061a

**Authority:** spec 081 FRONTEND-BETA-AUTHORITY-0

**Target path:** `docs/specs/082-secure-credential-storage-0.md`

---

## 1. Purpose

Persist the operator-entered Scaleway API key across backend restarts without storing plaintext in
SQLite, repository files, logs, events, frontend state or browser storage, and without weakening the
existing provider, budget, sensitivity, egress, ledger or proposal boundaries.

The current secret endpoint stores an entered key only in a process-local Python dictionary. An
environment variable survives restart, but the browser-entered credential does not. This forces the
operator to re-enter the same key after every backend restart and prevents later Settings UI from
truthfully reporting durable credential state.

082 adds one narrow, Windows-first persistence boundary for the already existing Scaleway secret.
It is not a general vault, credential platform or provider-registry redesign.

## 2. Current runtime facts

This definition was derived from `master` at
`623540439760d4338a2f0fea231745ece14bca6b`.

1. `backend/app/modules/secrets/storage.py` resolves `SCALEWAY_API_KEY` from the environment first,
   then from a module-level dictionary keyed by data-root namespace, otherwise as absent.
2. `POST /secrets/scaleway` validates and writes the key through that runtime-memory boundary.
3. `DELETE /secrets/scaleway` removes only the runtime-memory value; it cannot remove the
   environment value.
4. `GET /secrets/scaleway/status` returns key presence, source, storage mode and a masked preview.
5. `resolve_secret_ref("env:SCALEWAY_API_KEY")` deliberately uses the effective Scaleway secret
   boundary, so persisted storage can remain behind the existing provider registry reference.
6. JarvisOS resolves all runtime paths from `JARVISOS_DATA_ROOT`, defaulting to `C:\JarvisOS`.
7. `JarvisPaths` currently owns database, workspaces, artifacts and logs paths but no secret path.
8. Recovery snapshots include only the database plus `workspaces/` and `artifacts/`; `logs/` is
   excluded. Restore atomically replaces the whole target data root from that bounded snapshot.
9. Therefore, a new `secrets/` directory under the data root is not captured by current snapshots
   and will be removed by a successful restore unless the recovery contract is deliberately changed.
10. Product tests and CI run on Linux and must not require a real Windows account, DPAPI key,
    provider call or secret.
11. The normal product is Windows-first, single-user and loopback-first.

Any implementation that changes provider permission, egress policy, budget authority, secret
reference syntax or recovery snapshot contents is outside 082 unless explicitly required below.

## 3. Security objective and limits

### 3.1 Objective

An attacker who obtains the JarvisOS data-root files but not the operator's Windows account context
must not obtain the plaintext provider key from the persisted credential artifact.

The product must also fail closed when the credential file is malformed, replaced, truncated,
protected for another account or machine, or otherwise undecryptable.

### 3.2 Explicit limits

082 does not claim protection against:

- malware or a process already executing as the same Windows user while that user is logged in;
- an attacker who can read process memory during provider execution;
- an administrator or operating-system compromise;
- plaintext supplied through the environment by the operator;
- forensic secure erasure from SSDs, filesystems, Python memory or Windows paging;
- portability of an encrypted credential to another Windows user or machine;
- multiuser access control;
- remote secret synchronization or recovery.

The documentation and API must not describe DPAPI persistence as a hardware-backed vault, a password
manager, or protection from same-user code execution.

## 4. Chosen architecture

### 4.1 Protection mechanism

The Windows production implementation uses the Data Protection API through
`CryptProtectData` and `CryptUnprotectData` with current-user scope.

Binding requirements:

- use `CRYPTPROTECT_UI_FORBIDDEN`;
- do not use `CRYPTPROTECT_LOCAL_MACHINE`;
- do not request an interactive prompt;
- free every DPAPI-allocated output buffer with `LocalFree`;
- surface operating-system failures as typed safe errors without including plaintext, ciphertext,
  raw Windows error messages containing paths, or buffer contents;
- keep the implementation behind a narrow injected interface;
- use standard-library `ctypes` unless implementation evidence proves it cannot meet the contract;
- add no package merely to wrap these two functions unless the minimum-necessary test demonstrates
  a correctness or safety gap in the standard-library route.

Microsoft's normative API references are:

- <https://learn.microsoft.com/en-us/windows/win32/api/dpapi/nf-dpapi-cryptprotectdata>
- <https://learn.microsoft.com/en-us/windows/win32/api/dpapi/nf-dpapi-cryptunprotectdata>

### 4.2 No weak non-Windows product fallback

The production factory behaves as follows:

- Windows: current-user DPAPI protector;
- unsupported operating system: persistence unavailable;
- environment-provided key: remains usable on every supported operating system.

The product must never silently replace DPAPI with:

- plaintext storage;
- reversible encoding;
- a repository constant;
- a key stored beside the ciphertext;
- a machine-global key available to every local user;
- the deterministic test protector.

Linux CI uses a deterministic injected test protector. That protector is reachable only through
explicit test construction or dependency injection and cannot be selected by environment variable,
API input or product configuration.

### 4.3 Narrow interface

The implementation introduces a protocol equivalent to:

```python
class SecretProtector(Protocol):
    protector_id: str

    def protect(self, *, secret_id: str, plaintext: bytes) -> bytes: ...
    def unprotect(self, *, secret_id: str, ciphertext: bytes) -> bytes: ...
```

The interface owns cryptographic protection only. It does not own:

- file paths;
- JSON serialization;
- environment precedence;
- API responses;
- provider routing;
- event writes;
- backup policy.

A separate storage service owns the persisted envelope and atomic filesystem behavior.

## 5. Persistence format and path

### 5.1 Canonical path

Extend `JarvisPaths` with:

```text
secrets_dir = <data_root>/secrets
scaleway_secret_file = <data_root>/secrets/scaleway-api-key.v1.json
```

All construction must pass through `backend/app/core/paths.py`.

The implementation must not accept a caller-provided path, filename, provider ID or secret ID.

### 5.2 Encrypted inner payload

Before protection, serialize a canonical UTF-8 JSON object containing exactly:

```json
{
  "payload_schema": 1,
  "secret_id": "scaleway_api_key",
  "value": "<plaintext key>",
  "value_sha256": "<sha256 of the UTF-8 key>"
}
```

Requirements:

- deterministic key ordering and compact separators;
- no timestamp, hostname, username or random metadata inside the payload;
- verify the schema, exact key set, fixed `secret_id`, value type and value digest after decrypt;
- run the existing key validation again after decrypt;
- reject extra fields, unknown schema and identity mismatch;
- never persist the inner payload outside the DPAPI ciphertext.

The inner digest is an additional post-decryption corruption check. It is not a password hash,
authentication substitute or external secret identifier.

### 5.3 Outer envelope

Persist one canonical UTF-8 JSON envelope containing exactly:

```json
{
  "envelope_schema": 1,
  "secret_id": "scaleway_api_key",
  "protector_id": "windows_dpapi_current_user_v1",
  "ciphertext_base64": "<base64>",
  "ciphertext_sha256": "<sha256 of ciphertext bytes>"
}
```

Requirements:

- maximum bounded file size;
- strict base64 decoding;
- exact key-set validation;
- verify the ciphertext digest before unprotect;
- reject unknown protector, schema or secret identity;
- no plaintext-derived preview, length, prefix, suffix or digest outside the encrypted payload;
- no absolute path, username, SID, hostname or provider endpoint in the envelope.

### 5.4 Filesystem safety

The canonical file and every parent under the data root must be treated as server-owned paths.

Before read, write or delete:

- reject a symlink, junction/reparse point or non-regular canonical file;
- reject a `secrets/` path that escapes the resolved data root;
- create the directory with the most restrictive standard-library permissions available;
- create the file with restrictive permissions where the platform honors them;
- do not claim POSIX mode bits provide Windows account isolation;
- use same-directory temporary files;
- flush and `fsync` the temporary file before `os.replace`;
- never delete the existing valid credential until the replacement has been protected, written,
  parsed and successfully unprotected from the temporary artifact;
- clean a temporary artifact on handled failure;
- ignore, rather than execute or adopt, abandoned temporary files from a previous crash;
- serialize in-process mutations with one lock;
- rely on atomic replacement, not a database transaction.

If atomic replacement or verification fails, the previous canonical credential must remain usable.

## 6. Effective-secret resolution

### 6.1 Precedence

Effective resolution is strictly:

1. non-empty `SCALEWAY_API_KEY` environment value;
2. usable secure persisted credential;
3. absent.

An invalid environment value is a configuration error. It must not fall through to persisted
storage silently.

A corrupted persisted credential is a distinct unavailable state. It must not be reported as merely
absent.

### 6.2 Runtime memory retirement

The module-level runtime secret dictionary is removed from product behavior.

No compatibility path may continue accepting a browser-entered key only in memory. After 082:

- a successful POST means the encrypted canonical file was committed and reread successfully;
- a failed POST leaves no new effective runtime key;
- process restart is part of the ordinary contract, not a special migration operation.

### 6.3 Environment override

When `SCALEWAY_API_KEY` is present:

- provider execution uses the environment value;
- POST `/secrets/scaleway` returns conflict and does not create or replace persisted state;
- the response explains only that an environment override is active;
- DELETE may remove an existing persisted file but cannot alter the environment;
- after DELETE, effective status remains environment-provided;
- no endpoint returns the environment value or a derived preview.

This avoids a false `saved` state whose value is not actually effective.

## 7. API and status contract

### 7.1 Additive status fields

Keep the existing endpoint paths. Extend the status response additively so later Settings can
distinguish effective source and persisted health.

Required semantics:

```text
effective_source:
  environment | secure_persisted | none

persisted_state:
  absent | usable | corrupted | unavailable

storage_mode:
  environment | secure_persisted | none | unavailable | corrupted
```

`storage_mode` reflects the effective or blocking state for existing clients. `persisted_state`
reports the file independently, including when an environment override is active.

`key_present` is true only when an effective usable key exists.

### 7.2 No secret preview

The API must not return any key prefix, suffix, masked fragment, plaintext-derived digest or key
length.

The existing `masked_preview` field may remain temporarily for response compatibility but must be
`null` or a fixed non-secret token independent of the key. Tests must prove that no substring of the
test key appears in JSON responses.

### 7.3 Safe error mapping

Public responses may distinguish:

- unsupported platform;
- environment override conflict;
- corrupted persisted credential;
- credential unavailable for the current account or machine;
- invalid submitted key;
- filesystem persistence failure.

They must not expose:

- plaintext or ciphertext;
- Windows SID or username;
- raw DPAPI buffers;
- full operating-system exception text;
- arbitrary filesystem paths;
- temporary filenames;
- secret length or fragments.

Provider execution continues to surface the existing safe missing/configuration outcome rather than
inventing a second direct-provider path.

## 8. Events, logs and database boundary

Events may record only bounded metadata such as:

- action: set, replace, delete, read-failed;
- secret ID from the fixed server-owned enum;
- resulting storage mode;
- safe reason code;
- timestamp supplied by the existing event service.

Events, logs, SQLite rows, test reports and exception messages must never contain:

- submitted key;
- decrypted key;
- masked prefix or suffix;
- inner payload;
- ciphertext;
- base64 envelope content;
- plaintext-derived digest.

No new database table or migration is authorized.

## 9. Recovery and backup policy

### 9.1 Chosen policy

Secure credentials are deliberately excluded from data-root recovery snapshots.

The current snapshot allowlist remains unchanged:

- database;
- `workspaces/`;
- `artifacts/`.

Do not add `secrets/` to the snapshot manifest or archive.

Reason:

- current-user DPAPI ciphertext is intentionally bound to one Windows user and normally one machine;
- transporting it in a general JarvisOS backup creates a misleading recovery promise;
- the provider key can be re-entered;
- the minimum required capability is restart persistence, not cross-machine credential recovery.

### 9.2 Restore semantics

A successful data-root restore replaces the target root and therefore removes any previously
persisted secret file.

After restore:

- an environment key remains effective if externally configured;
- otherwise status becomes not configured;
- the operator re-enters the key;
- no automatic attempt is made to recover, copy or re-encrypt the old credential;
- restore documentation and tests state this behavior explicitly.

The implementation may add tests and documentation for this policy but must not broaden the recovery
archive format in 082.

## 10. Startup and corruption behavior

Persistence is lazy: backend startup must not fail solely because a credential is absent.

When status or provider resolution first reads the canonical file:

- absent file: normal absent state;
- malformed envelope: corrupted;
- ciphertext digest mismatch: corrupted;
- DPAPI unavailable on this platform: unavailable;
- DPAPI cannot decrypt for current account or machine: unavailable;
- decrypted payload malformed or identity/digest invalid: corrupted;
- valid payload: usable.

Corrupted or unavailable state must:

- make the persisted key unusable;
- prevent provider dispatch through that key;
- preserve the artifact for operator diagnosis or explicit deletion;
- not overwrite it automatically;
- not silently fall back to runtime memory;
- permit an explicit replacement POST when no environment override is active.

## 11. Required implementation files

Expected files, subject to exact-head verification before coding:

- `backend/app/core/paths.py`;
- `backend/app/modules/secrets/protection.py` — new narrow protection boundary;
- `backend/app/modules/secrets/storage.py`;
- `backend/app/modules/secrets/service.py`;
- `backend/app/modules/secrets/models.py`;
- `backend/app/modules/secrets/routes.py`;
- focused backend secret-storage and route tests;
- data-root recovery tests and bounded operator documentation;
- `docs/specs/STATUS.md` only in the implementation PR lifecycle.

Potentially touched only if evidence requires it:

- provider adapter or registry tests proving `env:SCALEWAY_API_KEY` still resolves through the
  effective boundary;
- application startup wiring for dependency construction.

No frontend file is in scope.

## 12. Acceptance criteria

### 12.1 Persistence

1. POST on supported Windows protects and atomically persists the key.
2. A newly constructed store in a fresh process context resolves the same key without POST.
3. No plaintext key appears in the canonical file, data-root scan, SQLite scan, logs, events or API
   response.
4. The runtime-memory dictionary is absent from product resolution.
5. A failed replacement preserves the previous valid credential.

### 12.2 Protection

6. Production Windows uses current-user DPAPI and `CRYPTPROTECT_UI_FORBIDDEN`.
7. `CRYPTPROTECT_LOCAL_MACHINE` is never set.
8. DPAPI output buffers are released with `LocalFree`.
9. Unsupported platforms do not persist with a weaker fallback.
10. The deterministic protector is test-injected only.

### 12.3 Integrity and paths

11. Malformed JSON, unknown schema, wrong secret identity, bad base64, ciphertext digest mismatch,
    failed unprotect, malformed inner payload and inner digest mismatch all fail closed.
12. Symlink, junction/reparse or non-regular canonical paths fail closed.
13. Temporary write or verification failure does not corrupt the previous file.
14. Reads enforce a bounded maximum file size.

### 12.4 Resolution and API

15. Environment value has strict precedence.
16. Invalid environment value does not fall through silently.
17. POST under an environment override returns conflict without mutating persisted state.
18. DELETE removes persisted state but cannot alter an environment key.
19. Status distinguishes environment, secure persisted, absent, corrupted and unavailable states.
20. No response contains a key-derived preview.
21. Existing provider-registry secret references require no configuration-file change.

### 12.5 Recovery

22. Recovery snapshots do not contain `secrets/` or the encrypted envelope.
23. Restore removes prior persisted secret state and requires re-entry unless an environment key
    exists.
24. Existing snapshot manifests remain compatible and unchanged.

### 12.6 Authority preservation

25. No provider call bypasses `run_ai_task`.
26. No budget, egress, sensitivity, route, fallback, ledger or promotion authority changes.
27. Tests make no live provider call.
28. No schema migration, frontend storage or browser persistence is added.

## 13. Required automated tests

### 13.1 Protector tests

- deterministic injected protector round-trip;
- wrong secret ID rejection;
- unsupported production platform failure;
- Windows-only real DPAPI round-trip, skipped elsewhere;
- Windows-only same-user subprocess read or equivalent fresh-process proof;
- Windows-only proof that `LOCAL_MACHINE` is not used;
- buffer release on success and failure seams where mockable.

### 13.2 Envelope and filesystem tests

- canonical envelope round-trip;
- strict key-set and schema rejection;
- bad base64;
- outer digest mismatch;
- inner digest mismatch;
- bounded oversized file;
- malformed encrypted payload;
- atomic replacement preserves old secret on write, fsync, verify and replace failures;
- symlink and non-regular path rejection;
- stale temporary file ignored;
- concurrent in-process writes produce one complete canonical file, never a torn artifact.

### 13.3 Service and route tests

- create, replace, status and delete;
- module/store reconstruction proves restart persistence;
- environment precedence;
- invalid environment fail-closed behavior;
- POST conflict under environment override;
- DELETE while environment override remains effective;
- corrupted and unavailable status;
- no key substring in response;
- no key, ciphertext or inner payload in captured logs/events;
- `resolve_secret_ref("env:SCALEWAY_API_KEY")` uses the persisted value when environment is absent;
- provider adapter configuration succeeds with injected persisted key and no provider dispatch.

### 13.4 Storage scans

Use a high-entropy sentinel secret and scan:

- data-root files other than the encrypted envelope;
- encrypted envelope bytes;
- SQLite database and WAL/SHM when present;
- captured logs;
- event payloads;
- HTTP response bodies;
- test-generated diagnostic artifacts.

The literal sentinel and meaningful fragments must be absent.

### 13.5 Recovery tests

- snapshot manifest remains on the existing exact include/exclude contract;
- a `secrets/` fixture is absent from archive inventory and bytes;
- restore into a root containing a persisted-secret fixture removes it;
- post-restore status is absent unless environment is set;
- no recovery code tries to decrypt or transport the credential.

## 14. Operator-visible P0 proof

After implementation gates are green, perform one local Windows checkpoint:

1. start the backend with no `SCALEWAY_API_KEY` environment override;
2. enter the real Scaleway key through the current UI or existing secret endpoint;
3. confirm status is `secure_persisted`;
4. terminate the backend process fully;
5. start a new backend process under the same Windows user;
6. confirm status remains `secure_persisted` without re-entry;
7. make one explicitly authorized, bounded AI smoke call through the normal execution spine;
8. confirm the call succeeds without re-entering the key;
9. inspect safe ledger evidence and confirm no secret appears;
10. delete the persisted credential after the checkpoint only if the operator chooses to remove it.

The live call is not part of CI. It requires operator authorization if it creates real spend. Failure
at this final checkpoint does not authorize bypassing provider, budget or egress controls.

## 15. Readiness requirements

A separate readiness decision may promote 082 from `planned` to `ready` only after confirming:

1. current `master` still has the runtime facts in section 2;
2. no concurrent front owns the secrets or recovery paths;
3. the implementation can use standard-library DPAPI without a new dependency, or a minimum-
   necessary case for a dependency is documented;
4. the production/test protector separation is mechanically enforceable;
5. the snapshot-exclusion and restore-removal policy is accepted as the binding backup behavior;
6. public status and error states are fully enumerated;
7. required Windows-only tests and the operator P0 checkpoint are assigned;
8. implementation files remain one reviewable medium slice;
9. no frontend work is required to satisfy the implementation acceptance criteria.

The readiness decision must name the implementation branch and merge owner. It must not execute a
provider call or contain a real credential.

## 16. Non-goals

082 does not add:

- a general multi-provider secret catalogue;
- arbitrary secret names or caller-selected files;
- a database secret table;
- Azure Key Vault, AWS Secrets Manager, HashiCorp Vault or cloud synchronization;
- DPAPI-NG, roaming credentials or cross-machine recovery;
- password-derived encryption;
- master-password UI;
- browser localStorage or sessionStorage secrets;
- frontend Settings redesign;
- Hermes or MCP credential access;
- secret export, reveal, copy or download;
- automatic key rotation;
- provider-token validation by making a live call during save;
- secure-erasure claims;
- authentication, multiuser ACLs or remote access;
- changes to provider routing, budget, egress or promotion;
- recovery snapshot expansion.

## 17. Stop conditions

Stop implementation and report if:

1. current-user DPAPI cannot be invoked non-interactively without adding an unjustified dependency;
2. the implementation would require `LOCAL_MACHINE` scope;
3. the only viable persistence path stores a decryption key beside the ciphertext;
4. a frontend change becomes necessary for restart persistence itself;
5. recovery snapshot compatibility would require changing historical manifest semantics;
6. provider execution would need a second secret-resolution or direct-provider path;
7. secret material appears in logs, events, responses, SQLite or test artifacts;
8. atomic replacement cannot preserve a previous valid credential;
9. an unsupported platform would silently fall back to weak storage;
10. the operator checkpoint would require bypassing spend, egress or sensitivity authority.

## 18. Definition of done

The implementation is complete only when:

1. every acceptance criterion is satisfied;
2. focused tests and the full backend suite pass;
3. Ruff passes;
4. registry and conformance gates pass;
5. BLUECAD geometry canary and Real Tool Proof remain green;
6. no new dependency is present without accepted minimum-necessary evidence;
7. exact-head review has no unresolved blocking finding;
8. the implementation PR records the final storage envelope, path, status and backup semantics;
9. the Windows operator P0 proof is completed or recorded as the sole explicit maintainer checkpoint;
10. the merge is exact-head guarded and `STATUS.md` is reconciled immediately afterward.
