from __future__ import annotations

from pathlib import Path

EXECUTE = Path("backend/app/modules/bluecad/cad_link_topology_execute.py")
TEST = Path("backend/tests/test_cad_link_topology_execute.py")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one target, found {count}")
    return text.replace(old, new, 1)


execute = EXECUTE.read_text(encoding="utf-8")
execute = replace_once(
    execute,
    "import sqlite3\n",
    "import sqlite3\nimport time\n",
    "time import",
)
execute = replace_once(
    execute,
    '''REPRESENTATION_NOTES = (
    "represented: common tubing, split/merge manifolds, repeated branch tubing; "
    "not represented: pump, reservoir vessel, supports, floats, anchors, "
    "instrumentation; CAD boundary: open supply inlet and open return outlet"
)
''',
    '''REPRESENTATION_NOTES = (
    "represented: common tubing, split/merge manifolds, repeated branch tubing; "
    "not represented: pump, reservoir vessel, supports, floats, anchors, "
    "instrumentation; CAD boundary: open supply inlet and open return outlet"
)
_REPLAY_POLL_SECONDS = 0.05
_REPLAY_WAIT_SECONDS = BUILD_TIMEOUT_SECONDS + 5.0
''',
    "replay timing constants",
)
execute = replace_once(
    execute,
    '''    candidate = get_candidate(workspace_id, str(row["child_candidate_id"]))
    if candidate is None:
        raise _persistence_inconsistent()
    return CadLinkExecuteResponse(
''',
    '''    candidate = _wait_for_replay_candidate(
        workspace_id,
        str(row["child_candidate_id"]),
    )
    return CadLinkExecuteResponse(
''',
    "replay candidate lookup",
)
helper_marker = '''def _json_object(raw: Any) -> dict[str, Any]:
'''
helper = '''def _wait_for_replay_candidate(
    workspace_id: str,
    candidate_id: str,
) -> Any:
    deadline = time.monotonic() + _REPLAY_WAIT_SECONDS
    while True:
        candidate = get_candidate(workspace_id, candidate_id)
        if candidate is None:
            raise _persistence_inconsistent()
        if candidate.status != "generating":
            return candidate
        if time.monotonic() >= deadline:
            raise CadLinkError(
                "cad_link_execution_in_progress",
                "The matching topology CAD-link execution is still in progress.",
                status_code=409,
            )
        time.sleep(_REPLAY_POLL_SECONDS)


''' + helper_marker
if "def _wait_for_replay_candidate" not in execute:
    execute = replace_once(execute, helper_marker, helper, "replay wait helper")
EXECUTE.write_text(execute, encoding="utf-8")

test = TEST.read_text(encoding="utf-8")
if "test_replay_waits_for_generating_candidate" not in test:
    test += '''


def test_replay_waits_for_generating_candidate(client: TestClient, monkeypatch) -> None:
    import threading
    import time
    from uuid import uuid4

    import app.modules.bluecad.cad_link_topology_execute as execute_module
    from app.modules.events.service import utc_now

    candidate_id = str(uuid4())
    now = utc_now()
    with open_sqlite_connection() as connection:
        connection.execute(
            """
            INSERT INTO bluecad_candidates (
                id, workspace_id, brief_text, brief_digest, status,
                parked_reason, spec_artifact_id, glb_artifact_id,
                report_artifact_id, promoted_decision_id, origin,
                parent_candidate_id, loop_config_json, created_at,
                updated_at, notes
            ) VALUES (?, 'bluerev', 'concurrency probe', ?, 'generating',
                NULL, NULL, NULL, NULL, NULL, 'process_linked', NULL,
                '{}', ?, ?, 'concurrency probe')
            """,
            (candidate_id, "sha256:" + "1" * 64, now, now),
        )
        connection.commit()

    monkeypatch.setattr(execute_module, "_REPLAY_WAIT_SECONDS", 1.0)
    monkeypatch.setattr(execute_module, "_REPLAY_POLL_SECONDS", 0.01)

    def complete_candidate() -> None:
        time.sleep(0.1)
        with open_sqlite_connection() as connection:
            connection.execute(
                "UPDATE bluecad_candidates SET status = 'valid', updated_at = ? WHERE id = ?",
                (utc_now(), candidate_id),
            )
            connection.commit()

    worker = threading.Thread(target=complete_candidate)
    worker.start()
    started = time.monotonic()
    candidate = execute_module._wait_for_replay_candidate("bluerev", candidate_id)
    elapsed = time.monotonic() - started
    worker.join()

    assert candidate.id == candidate_id
    assert candidate.status == "valid"
    assert elapsed >= 0.08
'''
TEST.write_text(test, encoding="utf-8")
