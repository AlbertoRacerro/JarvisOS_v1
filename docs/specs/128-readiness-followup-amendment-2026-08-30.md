# 128 ARCHITECTURE-ENFORCEMENT-GATE-1 — follow-up readiness disposition — 2026-08-30

**Decision: READY remains valid with the exact additional dispositions below.**

**Exact authority base:** `82b292887106872c0d3f5049b65795f1db439990`  
**Implementation PR inspected:** #441  
**Exact implementation head inspected:** `2980dd345ddbf4cdfa8200443308ab80f6e5b493`  
**Prior readiness authority:** PR #439 / `docs/specs/128-architecture-enforcement-gate-1.md` readiness packet  
**First inventory amendment:** `docs/specs/128-readiness-amendment-2026-08-30.md`

This is a planning/readiness disposition only. It does not modify product/runtime authority, does not broaden the implementation path budget, and does not itself prove #441 acceptable. The implementation remains limited to the already-authorized scanner/config/test/CI/status paths.

## Why this follow-up is required

After the first readiness amendment was merged, exact-head CI for #441 re-ran the narrowed full-tree scanner against the current PR merge tree. The scanner self-test passed, but the full-tree gate still reported four current AE003 findings:

- `backend/app/core/database.py::_ensure_parameter_lifecycle_schema`;
- `backend/app/modules/memory/service.py::_create_proposal_in_transaction`;
- `backend/app/modules/memory/service.py::create_calc_parameter_proposals`;
- `backend/app/modules/memory/service.py::promote_parameter_replacement`.

The accepted 128 contract requires an explicit disposition for current owners discovered by implementation rather than silently broadening an exception list. These four findings are therefore dispositioned here before any scanner repair.

## Exact dispositions

### `backend/app/core/database.py::_ensure_parameter_lifecycle_schema`

Classification: **accepted schema/migration owner**.  
Owner authority: existing core database initialization/migration boundary, including merged Parameter lifecycle schema authority from 098.

The function executes the already-merged additive Parameter lifecycle migration/index work from inside `initialize_database()`. It is not an ordinary domain service and does not create a new canonical business-write path. AE003 may exempt this exact path+symbol only. No sibling function, all-of-`core/**`, or arbitrary SQL in database helpers is authorized by this disposition.

### `backend/app/modules/memory/service.py::_create_proposal_in_transaction`

Classification: **accepted proposal owner**.  
Owner authority: 040 MemoryStore proposal boundary.

This symbol creates AI-originated Assumption/Parameter/Decision rows in `proposed` state inside the existing proposal transaction. Proposal creation is not canonical promotion authority. AE003 may exempt this exact path+symbol only.

### `backend/app/modules/memory/service.py::create_calc_parameter_proposals`

Classification: **accepted calculation-proposal owner**.  
Owner authority: 040 MemoryStore proposal boundary plus the merged calc proposal flow.

This symbol persists calculation-originated Parameters as `proposed` records; it does not silently promote them to current canonical authority. AE003 may exempt this exact path+symbol only.

### `backend/app/modules/memory/service.py::promote_parameter_replacement`

Classification: **accepted Parameter replacement-promotion owner**.  
Owner authority: existing 040 replacement promotion as explicitly preserved and extended by 098.

098 readiness states that existing Parameter replacement promotion remains the authoritative supersede path: it atomically validates the old/new relationship, updates both Parameter status/lifecycle states, persists 050/051 freshness invalidation, records audit evidence, and commits once. This exact symbol is therefore an accepted current owner, not new 127 debt. AE003 may exempt this exact path+symbol only. The accepted 112 composition helper `backend/app/modules/memory/project_knowledge_owner.py::promote_parameter_replacement_in_transaction` remains separately dispositioned by the first amendment and does not convert the rest of `memory/service.py` into an accepted mutation directory.

## Ratchet requirements after this disposition

The #441 repair must remain narrow:

1. add only the four exact AE003 owner entries above if the current scanner still reports them;
2. add focused regression proof that each exact owner passes while a sibling mutation symbol in the same file still fails AE003;
3. retain the five exact 127 modeling-service debt entries and the two exact 129 dispatch-debt entries without broadening them;
4. retain the first amendment's exact BLUECAD, Runner, recovery, AI-execution and Project-Knowledge dispositions;
5. no parent-directory wildcard or path-only blanket exemption is permitted;
6. the full-tree scanner, focused scanner tests, Ruff, full backend test suite, frontend build and BLUECAD deterministic proof must all be green on the same frozen implementation head before semantic acceptance.

## Scope conclusion

No product defect or runtime refactor is authorized by these findings. They are current, previously merged owners that the deliberately narrowed scanner now sees. The minimum safe repair is exact owner classification plus negative sibling tests. Any further undispositioned current-tree owner discovered after this amendment must fail closed again and return to readiness review rather than being auto-allowlisted.
