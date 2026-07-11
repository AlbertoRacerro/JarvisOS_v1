# 056 definition reconciliation — property testing and determinism canary

## Purpose

Reconcile the original docs-only 056 contract against the current BLUECAD CAD
adapter before implementation. This change does not add Hypothesis, tests,
fixtures, workflows, or runtime behavior.

## Blockers resolved

### Dependency ownership

The hard dependency is only 005. CI discipline from 007 and candidate-ledger
fixtures from 010 are contextual and are not called by the pure adapter tests.
The authoritative registry and spec now agree.

### Development dependency

The repository has a separate `requirements-dev.txt`; the implementation must pin
`hypothesis==6.156.6` there, not in runtime requirements.

### Portable properties versus full digest

The public `manifest_digest` includes exported STEP/STL/GLB hashes and the
recorded build123d version. The definition now separates:

- portable valid-domain invariants and same-environment repeatability;
- one full checked-in digest canary bound to `ubuntu-24.04`, CPython 3.11, and
  recorded build123d/OCP distribution versions.

Unsupported developer platforms explicitly skip only the full canary. The
canonical CI profile must fail rather than skip on profile drift.

### Manifest semantics

Builder volumes and bboxes are analytic metadata, while BREP validity/manifold
checks are separate kernel evidence. The property suite must not present analytic
volume as direct BREP metrology.

### Phase 1 generator domain

Random generation is intentionally limited to:

- one tube_run;
- two compatible connected tube_run parts;
- one float.

Bend remains in fixed canary fixtures but is excluded from random Phase 1.
Joint, manifold, anchor_mount, and harvest_module are deferred. Frames are
limited to planar cardinal unit directions because current assembly placement is
planar.

### Hypothesis and CI budget

The profile is frozen to deterministic, database-free, no-deadline execution with
only `HealthCheck.too_slow` suppressed. Exact Phase 1 counts are 38 generated
adapter builds plus eight canary builds, maximum 46. Canonical property and
canary execution must complete in 240 seconds.

### Digest contract

Every manifest digest is recomputed from canonical JSON after removing only its
own digest field. Same-spec fresh builds must produce identical complete
manifests and artifact hashes in the same environment. The suite does not make an
unnecessary claim that every distinct spec has a distinct digest.

### Canary update authority

There is no auto-update/write-back command. Expected profile and digest metadata
can change only in a reviewed PR that explains the dependency/export/builder
change and records old and new values.

## Implementation boundary after merge

Expected implementation surface:

- exact Hypothesis dev pin;
- two focused BLUECAD test modules;
- one small float fixture and one expected metadata file;
- a dedicated canonical Linux canary job;
- implementation notes and report.

Production CAD code is not pre-authorized. A minimized property failure may
justify a narrow fix, but the failing example and root cause must remain visible.
No solver, provider, network, candidate loop, UI, new part kind, schema mutation,
or generated CAD binary is in scope.

## Remaining stop conditions

Implementation must stop rather than weaken the contract if the 46-build bound
exceeds 240 seconds, same-profile full manifests drift, OCP metadata cannot be
bound, valid domains require broad filtering, or a valid minimized example
requires a broad builder/schema change.
