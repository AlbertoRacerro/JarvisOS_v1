# 138 PYTHON-RUNNER-HASHSEED-DETERMINISM-1 — CI scope amendment

Decision: ACCEPTED BOUNDED AMENDMENT

Exact-master basis: `190d6413e9a9368cb07a203972bab075bc5ee9fb`.
Implementation PR evidence: #512 on head `e9f0288e68e2d3af55b274af853f5f0812627500`.

## Causal evidence

Normal repository CI proved that the accepted 138 environment-metadata change reaches two existing deterministic runner consumers outside the initially enumerated focused test file. The only failures are stale exact-list assertions:

- `backend/tests/test_python_runner_calc_v0.py` expects only `PYTHONIOENCODING`, while the same runner now truthfully reports additive `PYTHONHASHSEED`.
- `backend/tests/test_process_kernel_075_runner.py` expects `PYTHONDONTWRITEBYTECODE` plus `PYTHONIOENCODING`, while the same conditional process-kernel environment now truthfully reports additive `PYTHONHASHSEED` as required by the frozen 138 acceptance matrix.

Changing runtime metadata to hide the new key from those callers would violate 138 required behavior and make the persisted environment metadata false. These are direct sibling assertions of the exact accepted mechanism, not new product behavior.

## Bounded authority amendment

For implementation PR #512 only, extend the allowed implementation paths by exactly:

- `backend/tests/test_python_runner_calc_v0.py`
- `backend/tests/test_process_kernel_075_runner.py`

Only the stale `environment_metadata.allowlisted_keys` expectations may change in those files. No calc behavior, process-kernel behavior, runner protocol, artifact behavior, recovery behavior, or other test expansion is authorized.

All original 138 requirements, non-goals, gates, and production-code path limits remain unchanged. This amendment exists solely to let normal CI assert the already-accepted truthful environment metadata on the two concrete current first-party runner paths it exposed.
