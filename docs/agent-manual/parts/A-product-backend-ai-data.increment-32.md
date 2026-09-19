# Area A file-coverage increment 32

MAPPING_STATUS: IN_PROGRESS
UNACCOUNTED_FILES: >0

Fresh baseline checked: `master` `240d5e0b27d9837d40f47bddfa24871ae7a2a4bb`.

## EXPLICIT FILE COVERAGE LEDGER

| path | status | concise role/reason |
|---|---|---|
| `backend/app/modules/ai/flow_grade_routes.py` | READ | Operator-facing flow-grade HTTP boundary: GET current grade, PUT set grade, POST withdraw; delegates subject/read/event authority and maps not-found/conflict/contract failures to 404/409/422. |

## Runtime observations

`flow_grade_routes.py` contains no grade persistence or evidence computation itself. It preserves optimistic-concurrency/evidence guards by forwarding `expected_subject_version`, `expected_flow_outcome_digest`, and `expected_current_grade_event_id` into the event service; set additionally forwards grade/reasons/note and both mutations identify `source="operator_api"`. Pydantic response validation is applied after the delegated operation.

Failure boundary: only the three domain exception classes are translated to HTTP responses here. Unexpected dependency/database/runtime exceptions propagate to the framework rather than being converted into a misleading grade-domain result.

This shard is additive because the canonical Area-A file is protected against destructive partial replacement. Canonical consolidation remains pending a complete safe read/write cycle.
