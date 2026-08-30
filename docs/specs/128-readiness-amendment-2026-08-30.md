# 128 ARCHITECTURE-ENFORCEMENT-GATE-1 — readiness inventory amendment — 2026-08-30

**Decision: READY remains valid with the exact dispositions below.**

**Exact amendment base:** `947044c037d7501db7098b86bf2c053b95f23acc`  
**Implementation evidence inspected:** PR #441 head `68bccaa5a143045f6c4188e81cd548e2fd17c19e`, CI run `33323294109`, backend job `99288929176`.

This amendment exists because the first full-tree execution of the 128 scanner correctly failed closed on current first-party paths omitted by the original readiness inventory. Per the accepted readiness contract, those findings are not auto-allowlisted. They are dispositioned here before any implementation repair. No runtime/product behavior change is authorized.

## Observed current-tree findings and disposition

### AE001 — data-root recovery

The four findings in `scripts/data_root_recovery/{snapshot,restore}.py` are existing recovery-tool persistence ownership accepted by the merged 021b recoverable-data-root capability, not new product database ownership:

- `snapshot.py::create_snapshot`
- `snapshot.py::verify_snapshot`
- `restore.py::_rebase_database`
- `restore.py::_verify_restored_database`

128 may represent these as exact `accepted_owner` entries with durable owner `021b ALPHA-GATE completion: recoverable data root`. No directory wildcard is authorized. New raw SQLite owners elsewhere still fail AE001.

### AE002 — canonical AI execution spine

`backend/app/modules/ai/execution.py::_run_local_continuations` and `backend/app/modules/ai/execution.py::run_ai_task` are the already-accepted product AI execution spine required by AGENTS invariant 2 and by the 059b egress boundary. Their `adapter.complete(...)` calls are accepted execution ownership, not 129 debt. 128 must recognize these exact symbols (or the exact execution module owner boundary if implemented without weakening alias detection). The two previously frozen smoke/public-test bypasses remain debt owned by 129.

### AE003 — existing run/evidence and Project Knowledge owners

The scanner surfaced existing direct SQL in boundaries that are not new canonical Project Basis write side channels:

- `backend/app/modules/bluecad/cad_link_topology_execute.py::_fail_nonterminal_analysis_run`
- `backend/app/modules/bluecad/cad_link_topology_execute.py::_recover_abandoned_reservation`
- `backend/app/modules/bluecad/loop.py::_best_effort_fail_simulation_run`
- `backend/app/modules/bluecad/loop.py::_complete_simulation_run`
- `backend/app/modules/bluecad/loop.py::_create_simulation_run`
- `backend/app/modules/runner/guarded_service.py::_create_runner_job_idempotent`
- `backend/app/modules/runner/service.py::_claim_and_mark_running`
- `backend/app/modules/runner/service.py::_finish_failed`
- `backend/app/modules/runner/service.py::create_runner_job`
- `backend/app/modules/runner/service.py::run_runner_job`

These are existing run/evidence lifecycle owners. 128 may retain them only as exact accepted-owner entries, with their existing BLUECAD/runner merged authority as durable owner; it must not generalize them into a directory exemption. `backend/app/modules/modeling/service.py::create_simulation_run` remains the separately frozen legacy public modeling debt owned by 127.

`backend/app/modules/memory/project_knowledge_owner.py::promote_parameter_replacement_in_transaction` is part of the accepted 112 Project Knowledge/098 Parameter promotion composition and may be an exact accepted owner. The original readiness named the 112 owner composition but omitted this concrete path.

`scripts/data_root_recovery/restore.py::_rebase_database` may also appear under AE003 because recovery rebases persisted canonical rows as part of the accepted 021b restore operation; it is an exact accepted recovery owner, not ordinary domain mutation authority.

`scripts/check_architecture_enforcement.py::_self_test` is scanner-owned inert fixture text. The production full-tree scan must classify the scanner's own deterministic self-test fixture separately so it does not report itself as runtime mutation authority; this is not an architecture exception entry and must not exempt other scripts.

## Repair constraints for PR #441

The implementation repair may modify only the already-authorized 128 paths. It may add the exact accepted-owner entries above and/or narrow scanner classification logic where that is strictly stronger and clearer. It must not touch `backend/app/**`, refactor any discovered owner, broaden path wildcards, add baseline-refresh behavior, or suppress future new symbols under these files/directories.

Focused regression coverage must prove at least:

1. the exact current-tree owners above no longer produce findings;
2. a new sibling symbol in the same file/path with the corresponding forbidden pattern still fails;
3. the two 129 debt entries remain exact debt rather than accepted execution owners;
4. the five 127 modeling-service entries remain exact debt;
5. scanner self-test fixture text is inert and does not create a production-tree false positive;
6. the full-tree scanner command is green before terminal merge gates are accepted.

## Authority conclusion

This amendment repairs readiness inventory drift only. `STATUS.md=ready` remains implementation authority for 128, PR #441 remains the sole implementation front, and all hardening holds remain unchanged. The CI failure is therefore a valid fail-closed inventory discovery, not evidence that runtime code should be changed.
