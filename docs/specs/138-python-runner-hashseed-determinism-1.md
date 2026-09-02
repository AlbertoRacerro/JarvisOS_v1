# 138 PYTHON-RUNNER-HASHSEED-DETERMINISM-1

Status: full specification / planning authority

## Purpose

Close the bounded post-134 F6 residual determinism gap in the generic production Python runner by pinning Python hash randomization for every runner child process. This is a corrective change to the existing isolated child environment, not a new runner, sandbox, execution framework, or retroactive failure of spec 130.

## Derivation evidence

Derived from exact master `f20eacb635e7da6d058a9c955edd6056aaf75eb7` after spec 137 reconciliation.

Fresh source inspection confirms `backend/app/modules/runner/local_python.py::execute_python_script` constructs an explicit non-inherited child environment containing `PYTHONIOENCODING=utf-8` and, only for a local artifact-path condition, `PYTHONDONTWRITEBYTECODE=1`. It does not set `PYTHONHASHSEED`, so Python string/set/dict hash randomization can differ across independently launched production-runner subprocesses even with identical inputs.

The existing `backend/tests/test_python_runner.py` already exercises the real production runner and asserts its environment metadata. The post-134 Coordination Bus workpack also established that spec 130 pinned `PYTHONHASHSEED=0` only in a separate BLUECAD test helper; it did not modify the production runner. Therefore F6 remains a live bounded residual-risk repair.

## Authority and dependencies

Depends on merged 130 and the merged post-134 repairs through 137. Implementation authority exists only after an accepted readiness decision and `STATUS.md=ready`.

## Required behavior

1. Add `PYTHONHASHSEED=0` to the existing explicit child-process environment created by `execute_python_script`.
2. Preserve the current non-inherited environment model; do not copy the parent environment or broaden the allowlist.
3. Preserve `PYTHONIOENCODING=utf-8` and the existing conditional `PYTHONDONTWRITEBYTECODE=1` behavior unchanged.
4. Prove causality through the real production runner by launching two independent child processes for the same script and asserting identical hash-dependent output plus visible `PYTHONHASHSEED=0` inside the child.
5. Update the existing environment-metadata expectation so the runner reports the new allowlisted key deterministically.
6. Do not claim determinism for sources outside Python hash randomization (filesystem ordering, wall clock, RNG APIs, locale, external tools, floating-point/library nondeterminism, or user code that deliberately introduces nondeterminism).

## Allowed implementation paths

- `backend/app/modules/runner/local_python.py`
- `backend/tests/test_python_runner.py`
- normal lifecycle bookkeeping in `docs/specs/STATUS.md`

No frontend, provider, network/egress, schema/store/migration, workflow, BLUECAD runtime, or unrelated runner refactor is authorized.

## Deterministic acceptance matrix

| Case | Expected result |
| --- | --- |
| existing successful runner invocation | behavior preserved; metadata allowlist contains `PYTHONHASHSEED` and `PYTHONIOENCODING` |
| local artifact-path invocation | existing `PYTHONDONTWRITEBYTECODE` remains additive to the same isolated environment |
| two independent production-runner subprocesses executing a script that prints `hash(<fixed string>)` | byte-identical stdout on both runs |
| same causal script | child observes `PYTHONHASHSEED=0` |
| parent environment contains unrelated variables | they remain absent from the child because the runner still uses the explicit allowlist |

The cross-process proof must call `execute_python_script`; a unit test that inspects only a constructed dictionary is insufficient.

## Required gates

- focused `backend/tests/test_python_runner.py`
- normal repository CI on the frozen implementation head
- independent exact-head semantic review because this changes production execution semantics

## Failure modes to prevent

- setting the seed only in tests while production subprocesses remain randomized;
- inheriting the parent environment as a shortcut, reintroducing secrets/configuration leakage into child processes;
- replacing or dropping the existing encoding/bytecode environment behavior;
- a weak test that passes without actually spawning independent Python processes;
- broad claims that this makes arbitrary Python scripts fully deterministic.

## Non-goals

- no generic reproducibility framework;
- no RNG seeding for `random`, NumPy, ML frameworks, or external tools;
- no process sandbox redesign;
- no runner crash-recovery work (F8);
- no RunArtifact contract work (F7);
- no BLUECAD stale-generation work (F9);
- no calc-runner artifact/proposal consistency work (F10).

## Minimum-necessary test

The production runner already owns an explicit child environment and a focused real-process test surface. Adding one fixed environment entry and one causal cross-process regression proof is the smallest change that removes Python hash-seed variance without widening the runner's authority or environment exposure.
