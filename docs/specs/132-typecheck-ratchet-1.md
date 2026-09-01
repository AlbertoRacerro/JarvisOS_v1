# 132 — TYPECHECK-RATCHET-1

Status: compressed definition/full-spec/readiness packet; live implementation authority remains `docs/specs/STATUS.md`.

## Purpose

Turn the backend's existing advisory mypy setup into a deterministic **non-regression ratchet** without requiring a repo-wide typing cleanup. Existing type debt may remain at the accepted exact-SHA baseline, but no backend runtime file may increase its mypy error count and a newly typed/runtime file starts with zero debt.

The ratchet is intentionally incremental: it prevents new debt while allowing existing files to improve independently. Aggregate error totals are diagnostic only and never permit one file's improvement to pay for another file's regression.

## Exact-master inventory

Derived from exact master `ba3500eee7430ecb65f18353019ae23c7d7cb41e` after 131 post-merge reconciliation.

Fresh repository evidence:

- `backend/pyproject.toml` already defines `[tool.mypy]` for Python 3.11, `ignore_missing_imports = true`, `warn_unused_ignores = true`, `warn_redundant_casts = true`, excludes `local_ai` / `local_ai_eval`, and documents `python -m mypy app` as the runtime-backend check;
- `backend/requirements-dev.txt` already installs mypy, currently as the floating constraint `mypy>=1.11`;
- `.github/workflows/ci.yml` installs backend development dependencies in backend lanes but currently runs architecture enforcement and Ruff only; mypy is not a required CI gate;
- there is no existing repository mypy baseline, ratchet checker, or mypy CI step to reuse;
- the current CI backend domain is Linux/Python 3.11, while the maintainer workstation is Windows; ratchet evidence therefore needs normalized repository-relative paths rather than platform-native path identity.

The floating mypy dependency is a determinism failure mode for a checked-in baseline: a future upstream mypy release can change diagnostics without any JarvisOS code change. The implementation must therefore bind the baseline to one exact mypy version and make CI use that same version.

## Failure modes to prevent

1. **Aggregate laundering:** one file fixes two errors while another introduces one; a global total falls and falsely reports improvement.
2. **Baseline laundering:** a PR increases the checked-in allowance to hide new type errors.
3. **New-file blind spot:** a file absent from the baseline acquires errors and is silently ignored.
4. **Tool drift:** an unpinned mypy version changes diagnostics and invalidates the meaning of the baseline.
5. **Parser ambiguity:** warnings, notes, Windows paths, summaries, or tool failures are mistaken for type-error debt.
6. **Mypy crash/config failure treated as debt:** exit status indicating invocation/internal failure is accepted as ordinary existing errors.
7. **Scope creep:** the slice attempts to annotate/fix the whole backend, type-check research scaffolding excluded by current policy, or introduces a new typing framework.
8. **Baseline SHA fiction:** a baseline claims an exact source SHA but was not generated from that source/config/tool identity.

## Accepted implementation boundary

The implementation may add only the minimum repository tooling needed to enforce the ratchet:

1. pin the existing mypy development dependency to one exact version used to establish the first baseline;
2. add one small deterministic repository checker, expected at `scripts/check_typecheck_ratchet.py`, that invokes the accepted backend command (`python -m mypy app`) with stable machine-oriented output flags, parses only true mypy error diagnostics, normalizes paths to repository-relative POSIX form, and compares current per-file counts with the checked-in baseline;
3. add one versioned baseline artifact under an existing backend/tooling boundary (for example `backend/mypy-baseline.json`) containing at minimum schema version, exact source SHA, exact mypy version/config identity, and a sorted map of runtime-backend file path → accepted error count;
4. integrate the checker into the existing backend CI lane only when `run_backend == true`;
5. add deterministic checker self-tests or focused tests covering comparison, parsing, tamper, new-file, deletion/rename, and tool-failure semantics;
6. add the checker itself to the existing Ruff-controlled script list when needed.

The first baseline is a bootstrap snapshot, not a typing-quality claim. It must be generated from the exact implementation base before product-code typing changes are made. The implementation PR must not mix broad annotation cleanup into baseline establishment.

## Ratchet semantics

The hard gate is **per file**, not aggregate:

- if a baseline path has `N` errors, current count must be `<= N`;
- if a current runtime-backend path is absent from the baseline, its allowed count is `0`;
- if a baseline path no longer exists, its current count is `0` and passes; the implementation must not keep a synthetic error allowance alive for a deleted path;
- file renames are intentionally treated as a new path with zero allowance unless the renamed file is already clean, preventing debt from being silently carried into a new owner by path manipulation;
- aggregate totals may be printed for operator visibility but may never offset a per-file regression.

A future baseline update may lower/remove per-file allowances after genuine cleanup. It must never raise an allowance relative to the baseline on the PR base. CI must compare a modified baseline against the exact PR-base baseline (or an equivalently exact merge-base source) so a same-PR baseline increase cannot hide a regression. The initial 132 bootstrap is the only no-parent-baseline case and is valid only when the baseline's recorded source SHA equals the exact accepted 132 implementation base.

## Mypy execution contract

The implementation must make diagnostic parsing deterministic and fail closed:

- run from `backend/` against `app` using the repository `pyproject.toml`;
- use stable non-pretty/no-summary/error-code output flags sufficient for line-oriented parsing;
- count only mypy `error:` diagnostics, not `note:` lines or summaries;
- normalize `\` and `/` path forms before comparison;
- mypy's ordinary "type errors found" exit status is expected input to the ratchet; invocation/config/internal failures must fail the gate rather than become baseline debt;
- checker output must name every regressed file with baseline/current counts and return non-zero on any regression or invalid baseline/tool identity.

The exact pinned mypy version must be recorded in the baseline and validated at runtime. A version mismatch is a deterministic gate failure requiring an explicit baseline/tooling update, not silent rebasing.

## Acceptance criteria

All are required on one exact implementation head:

1. Exact mypy version is pinned and the ratchet rejects a version mismatch.
2. A checked-in baseline records the exact accepted implementation-base SHA and sorted per-file debt counts for the current `backend/app` mypy scope.
3. Running the checker on unchanged baseline-equivalent code passes even when pre-existing mypy errors remain.
4. Adding one error to any baseline file fails even if another file removes more errors and aggregate debt decreases.
5. A new runtime-backend file with any mypy error fails with baseline allowance zero.
6. Lowering/removing existing debt passes; deleting a debt-bearing file does not require preserving its allowance.
7. Raising a baseline allowance relative to the exact PR-base baseline fails and cannot be used to make a same-PR regression pass.
8. Ordinary non-error mypy notes/summaries are not counted; path normalization is stable across slash styles.
9. Mypy invocation/config/internal failure fails closed and is not serialized as accepted debt.
10. Existing `local_ai` / `local_ai_eval` exclusion and current mypy policy are preserved unless an exact implementation-base conflict proves a smaller correction necessary.
11. Existing backend tests/runtime behavior are unchanged; no broad annotation/refactor campaign is bundled.
12. Repository-required exact-head CI is terminal green with the new ratchet active for backend-affecting changes.

## Deterministic test plan

At minimum, checker self-tests/focused tests must prove:

- exact parsing of representative mypy `error:` vs `note:` output;
- POSIX/Windows-style path normalization;
- unchanged baseline pass;
- same-file increase fail;
- aggregate-improves-but-one-file-regresses fail;
- new-file error fail;
- reduced debt pass;
- deleted baseline path pass without transferable allowance;
- baseline-increase/tamper fail against an exact parent baseline;
- mypy-version mismatch fail;
- malformed baseline/schema fail;
- mypy invocation/config/internal failure fail closed.

Frozen implementation-head CI must run the actual checker against the real backend, not only parser fixtures.

## Non-goals

- no repo-wide typing cleanup or annotation campaign;
- no requirement to make current mypy output globally clean;
- no frontend TypeScript/type-generation work (133 remains separate);
- no type checking of currently excluded `local_ai` / `local_ai_eval` research scaffolding;
- no new package manager, lockfile system, daemon, service, database, durable runtime state, provider, credential, egress, or external account;
- no global CI redesign or BLUECAD dependency split;
- no weakening of existing Ruff/Pytest/architecture gates;
- no 133/134 implementation.

## Files likely touched

Implementation is expected to remain bounded to:

- `backend/requirements-dev.txt` — exact mypy pin;
- `backend/mypy-baseline.json` (or one equivalently narrow backend tooling path) — deterministic baseline;
- `scripts/check_typecheck_ratchet.py` — checker/self-test;
- `.github/workflows/ci.yml` — backend ratchet gate and Ruff inclusion if needed;
- focused tests only if self-test alone is insufficient;
- `docs/specs/STATUS.md` for the implementation lifecycle handshake.

No runtime `backend/app/**` file is expected to require a behavior change merely to establish the ratchet.

## Readiness decision

**READY, conditional only on this compressed planning/readiness PR merging with the atomic live registry transition to `132=ready`.**

Rationale: this is additive, local, reversible repository tooling; it introduces no runtime/product, security, credential, provider, egress, durable-store, migration, destructive, or cross-domain ownership authority. Exact-master inventory identifies an existing mypy configuration and dependency but no enforcement gate. The primary determinism risk (floating mypy version) and baseline-laundering risk are explicitly closed by acceptance criteria. It therefore qualifies for post-112 low-risk planning compression.

Until this PR merges and exact `master` records `132=ready`, implementation remains forbidden.

### Test del minimo necessario

Criterio di accettazione della spec: prevent any backend runtime file from increasing its accepted mypy debt while allowing existing debt to remain or decrease independently.

Questo lavoro serve a soddisfarlo? sì.

Il criterio è raggiungibile senza di esso? no — current repository configuration installs mypy but CI does not execute it and no per-file baseline/ratchet exists; a plain global mypy failure would instead require immediate cleanup of all existing debt and is outside the bounded objective.
