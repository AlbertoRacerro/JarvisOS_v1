# 130 — RUNNER-DETERMINISM-1

Status: planning/readiness packet; live implementation authority remains `docs/specs/STATUS.md`.

## Purpose

Close the cross-process determinism gap left after merged spec 056. The BLUECAD property/canary suite currently proves repeated geometry/manifest construction inside one Python interpreter, but Python hash randomization is fixed for the lifetime of that interpreter. That evidence therefore cannot prove that an independently started Python process produces the same canonical manifest/artifact evidence when its inherited `PYTHONHASHSEED` differs.

This slice is intentionally narrow: make the Python child execution used by the BLUECAD determinism proof pin its own hash seed and add a meta-test that proves divergent parent/interpreter hash seeds cannot change the canonical child result.

## Exact-master inventory

Derived from exact master `b83d857fe52d3705e8329edce20d2d6e2d7cdc3c` after 129 post-merge reconciliation.

Relevant existing evidence:

- `backend/tests/bluecad/property_geometry_support.py::build_twice_and_assert` builds the same spec twice in one interpreter and compares `spec_id`, manifest equality, manifest digest, and artifact hashes.
- `backend/tests/bluecad/test_manifest_determinism_canary.py::test_canonical_full_manifest_digest_canary` exercises the canonical fixtures and compares their manifest digests against the frozen expected profile.
- The canonical CI BLUECAD canary runs those tests under Python 3.11, but no current proof launches independent child interpreters under intentionally divergent hash seeds.
- Hard dependency `056` is merged.

## Failure mode

A set/dict-derived traversal or any other hash-order-sensitive intermediate may remain stable across repeated calls in one interpreter yet reorder across independent interpreters. The current same-process repeatability proof would stay green while cross-process manifest ordering, digest material, or artifact bytes drift.

A weak fix that merely sets `PYTHONHASHSEED` on the outer pytest process is insufficient evidence: it can hide the drift without proving that the child execution boundary itself is deterministic. Likewise, a meta-test that compares only sorted/normalized JSON after the fact would not prove deterministic production of the canonical evidence.

## Accepted implementation boundary

The implementation MUST remain within the BLUECAD deterministic-test/runner boundary required to prove the existing 056 contract. It may:

1. add or extend a small test-support child-Python runner that invokes the canonical fixture build in a fresh interpreter;
2. construct the child environment from the current environment but explicitly override `PYTHONHASHSEED` to one frozen canonical value before `sys.executable` is launched;
3. emit only the deterministic evidence needed for comparison (fixture/spec identity, manifest digest and existing artifact hashes, or an equivalent canonical snapshot already owned by 056);
4. add a meta-test that starts independent parent/interpreter executions with at least two intentionally different inherited hash seeds and proves the child runner still executes with the pinned canonical seed and returns byte-/value-equivalent canonical evidence;
5. wire the proof into the existing BLUECAD test ownership without weakening or replacing the 056 same-process canary.

The implementation SHOULD prefer an explicit subprocess environment override local to the child launcher rather than a repository-global environment mutation. The canonical pin value is `0` unless fresh exact-head implementation evidence proves an existing project-owned value must be preserved.

## Acceptance criteria

All of the following are required on one exact implementation head:

1. A fresh Python child used by the determinism proof receives `PYTHONHASHSEED=0` explicitly from its launcher, independent of the caller's inherited value.
2. A deterministic meta-test executes equivalent canonical BLUECAD fixture work across independent Python processes whose incoming hash seeds differ (minimum two distinct values) and proves equal canonical result evidence.
3. The meta-test would fail if the child launcher stopped overriding the divergent incoming hash seed; the proof must therefore exercise the launcher boundary rather than compare pre-normalized constants.
4. Existing 056 same-process property/digest tests remain green and are not weakened, skipped, tolerance-broadened, or replaced.
5. No production BLUECAD geometry semantics, manifest schema, artifact schema, expected digest fixture, provider/runtime authority, credential, database, frontend, or external-tool execution behavior changes.
6. The focused BLUECAD tests and every repository-required exact-head merge gate are terminal green.

## Deterministic test plan

At minimum:

- existing `backend/tests/bluecad/test_manifest_determinism_canary.py` coverage remains green;
- new/extended subprocess determinism meta-test runs equivalent canonical fixture work through the child launcher under divergent inherited seeds such as `1` and `777`;
- assert child-reported seed is the canonical pinned value and compare canonical snapshot/digest/artifact-hash evidence exactly;
- include a focused unit assertion around environment construction if needed so omission of the override is independently detectable;
- run the normal affected-domain CI/BLUECAD gates on the frozen implementation head.

Tests must not rely on statistical probability of two hash seeds producing visibly different ordering. The causal property being tested is that the launcher overwrites the caller-provided seed and that the resulting independent child outputs are identical.

## Non-goals

- no global `PYTHONHASHSEED` policy for every JarvisOS process;
- no production geometry or manifest refactor;
- no sorting sweep or broad canonicalization rewrite without a separately proven defect;
- no regeneration of frozen expected digests merely to make the test pass;
- no CI-wide environment rewrite;
- no changes to providers, AI routing, credentials, schemas, stores, frontend, 113–126, or 131+;
- no attempt to make external CAD kernels bitwise reproducible across different OS/architecture/kernel versions beyond the existing canonical 056 profile.

## Readiness decision

**READY, conditional only on the live registry transition to `130=ready` merging.**

The dependency is already merged, the affected ownership is narrow and test-only, the failure mode is concrete, the minimum implementation paths and causal meta-test are explicit, and the change is reversible. This qualifies for post-112 compressed planning; a separate definition/full-spec/readiness ceremony would add no authority or material risk reduction.

Until `docs/specs/STATUS.md` on exact master records `130=ready`, this packet grants no implementation authority.

### Test del minimo necessario

Criterio di accettazione: prove cross-process BLUECAD determinism despite divergent inherited Python hash seeds, without broadening runtime semantics.

Questo lavoro serve a soddisfarlo? sì.

Il criterio è raggiungibile senza di esso? no — same-process repetition cannot establish independent-interpreter hash-seed determinism.
