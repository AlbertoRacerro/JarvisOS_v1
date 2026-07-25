from __future__ import annotations

from pathlib import Path


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise SystemExit(f"expected exactly one target in {path}: {old[:80]!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def patch_execute() -> None:
    path = Path("backend/app/modules/bluecad/cad_link_topology_execute.py")
    text = path.read_text(encoding="utf-8")
    text = text.replace(
        "import sqlite3\nimport time\nfrom collections.abc import Mapping\n",
        "import sqlite3\nimport threading\nimport time\nfrom collections.abc import Mapping\nfrom datetime import datetime, timezone\n",
        1,
    )
    text = text.replace(
        "_REPLAY_POLL_SECONDS = 0.05\n_REPLAY_WAIT_SECONDS = BUILD_TIMEOUT_SECONDS + 5.0\n",
        "_REPLAY_POLL_SECONDS = 0.05\n"
        "_REPLAY_WAIT_SECONDS = BUILD_TIMEOUT_SECONDS + 5.0\n"
        "_RESERVATION_POLL_SECONDS = 0.05\n"
        "_RESERVATION_WAIT_SECONDS = BUILD_TIMEOUT_SECONDS + 5.0\n"
        "_RESERVATION_HEARTBEAT_SECONDS = 5.0\n"
        "_ABANDONED_RESERVATION_SECONDS = 30.0\n",
        1,
    )

    start_marker = "    try:\n        with open_sqlite_connection() as connection:\n            connection.execute(\"BEGIN IMMEDIATE\")\n"
    end_marker = "\n\n    out_dir = candidate_work_dir"
    start = text.index(start_marker, text.index("def execute_cad_link_072"))
    end = text.index(end_marker, start)
    reservation = '''    reservation_deadline = time.monotonic() + _RESERVATION_WAIT_SECONDS
    while True:
        try:
            with open_sqlite_connection() as connection:
                connection.execute("BEGIN IMMEDIATE")
                try:
                    current = _preview_from_connection(
                        connection,
                        workspace_id,
                        preview_request,
                    )
                    _require_preview_digest(current, payload.preview_digest)
                    row = connection.execute(
                        """
                        SELECT * FROM bluecad_cad_links
                        WHERE workspace_id = ? AND preview_digest = ?
                        """,
                        (workspace_id, payload.preview_digest),
                    ).fetchone()
                    if row is not None:
                        connection.rollback()
                        return _replay_response(workspace_id, dict(row), current)

                    connection.execute(
                        """
                        INSERT INTO bluecad_candidates (
                            id, workspace_id, brief_text, brief_digest, status,
                            parked_reason, spec_artifact_id, glb_artifact_id,
                            report_artifact_id, promoted_decision_id, origin,
                            parent_candidate_id, loop_config_json, created_at,
                            updated_at, notes
                        ) VALUES (?, ?, ?, ?, 'generating', NULL, NULL, NULL,
                            NULL, NULL, 'process_linked', NULL, '{}', ?, ?, ?)
                        """,
                        (
                            candidate_id,
                            workspace_id,
                            brief,
                            brief_digest,
                            now,
                            now,
                            (
                                f"CAD-LINK transformation={TRANSFORMATION_VERSION}; "
                                f"source_simulation_run_id={payload.source_simulation_run_id}; "
                                f"{REPRESENTATION_NOTES}"
                            ),
                        ),
                    )
                    connection.execute(
                        """
                        INSERT INTO bluecad_attempts (
                            id, candidate_id, attempt_no, route_class,
                            proposal_ai_job_id, proposal_outcome, build_outcome,
                            validation_verdict, spec_artifact_id,
                            report_artifact_id, manifest_artifact_id, started_at,
                            finished_at, error_detail_json
                        ) VALUES (?, ?, 1, ?, NULL, 'not_applicable', NULL,
                            NULL, NULL, NULL, NULL, ?, NULL, NULL)
                        """,
                        (attempt_id, candidate_id, ROUTE_CLASS, now),
                    )
                    connection.execute(
                        """
                        INSERT INTO bluecad_cad_links (
                            id, workspace_id, source_simulation_run_id,
                            source_runner_job_id, child_candidate_id,
                            transformation_version, source_snapshot_json,
                            source_snapshot_digest, source_model_identity_json,
                            source_model_identity_digest, analysis_contract_digest,
                            preview_digest, resolved_spec_digest,
                            reconciliation_json, reconciliation_digest, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            link_id,
                            workspace_id,
                            current["source_simulation_run_id"],
                            current["source_runner_job_id"],
                            candidate_id,
                            current["transformation_version"],
                            canonical_json(current["source_snapshot"]),
                            current["source_snapshot_digest"],
                            canonical_json(current["source_model_identity"]),
                            current["source_model_identity_digest"],
                            current["analysis_contract_digest"],
                            current["preview_digest"],
                            current["resolved_spec_digest"],
                            canonical_json(current["reconciliation"]),
                            current["reconciliation_digest"],
                            now,
                        ),
                    )
                    connection.commit()
                    preview = current
                except Exception:
                    connection.rollback()
                    raise
            break
        except sqlite3.OperationalError as exc:
            if not _is_database_locked(exc):
                raise
            existing = _load_existing_link(workspace_id, payload.preview_digest)
            if existing is not None:
                return _replay_response(workspace_id, existing, preview)
            if time.monotonic() >= reservation_deadline:
                raise CadLinkError(
                    "cad_link_execution_in_progress",
                    "A matching topology CAD-link reservation is still in progress.",
                    status_code=409,
                ) from None
            time.sleep(_RESERVATION_POLL_SECONDS)
        except sqlite3.IntegrityError:
            existing = _load_existing_link(workspace_id, payload.preview_digest)
            if existing is not None:
                return _replay_response(workspace_id, existing, preview)
            raise CadLinkError(
                "cad_link_persistence_failed",
                "The topology CAD-link record could not be created coherently.",
                status_code=500,
            ) from None
'''
    text = text[:start] + reservation + text[end:]

    text = text.replace(
        "    attempt_finished = False\n    try:\n",
        "    attempt_finished = False\n"
        "    lease_stop, lease_thread = _start_reservation_heartbeat(\n"
        "        workspace_id, candidate_id\n"
        "    )\n"
        "    try:\n",
        1,
    )
    text = text.replace(
        "        if all(\n            artifact_id is None\n",
        "        if all(\n            artifact_id is None\n",
        1,
    )
    text = text.replace(
        "        ):\n            _best_effort_cleanup_unregistered(out_dir)\n        raise CadLinkError(\n",
        "        ):\n            _best_effort_cleanup_unregistered(out_dir)\n"
        "        _stop_reservation_heartbeat(lease_stop, lease_thread)\n"
        "        raise CadLinkError(\n",
        1,
    )
    text = text.replace(
        "\n    candidate = get_candidate(workspace_id, candidate_id)\n",
        "\n    _stop_reservation_heartbeat(lease_stop, lease_thread)\n"
        "    candidate = get_candidate(workspace_id, candidate_id)\n",
        1,
    )

    load_end = '''    return None if row is None else dict(row)


'''
    helpers = '''    return None if row is None else dict(row)


def _is_database_locked(exc: sqlite3.OperationalError) -> bool:
    return "locked" in str(exc).lower()


def _start_reservation_heartbeat(
    workspace_id: str,
    candidate_id: str,
) -> tuple[threading.Event, threading.Thread]:
    stop_event = threading.Event()
    thread = threading.Thread(
        target=_reservation_heartbeat,
        args=(workspace_id, candidate_id, stop_event),
        name="cad-link-072-reservation-heartbeat",
        daemon=True,
    )
    thread.start()
    return stop_event, thread


def _stop_reservation_heartbeat(
    stop_event: threading.Event,
    thread: threading.Thread,
) -> None:
    stop_event.set()
    thread.join(timeout=1.0)


def _reservation_heartbeat(
    workspace_id: str,
    candidate_id: str,
    stop_event: threading.Event,
) -> None:
    while not stop_event.wait(_RESERVATION_HEARTBEAT_SECONDS):
        try:
            with open_sqlite_connection() as connection:
                connection.execute(
                    """
                    UPDATE bluecad_candidates
                    SET updated_at = ?
                    WHERE workspace_id = ? AND id = ? AND status = 'generating'
                    """,
                    (utc_now(), workspace_id, candidate_id),
                )
                connection.commit()
        except sqlite3.Error:
            continue


'''
    if text.count(load_end) != 1:
        raise SystemExit("execute helper insertion target missing")
    text = text.replace(load_end, helpers, 1)

    old_deadline = '''        if time.monotonic() >= deadline:
            raise CadLinkError(
                "cad_link_execution_in_progress",
                "The matching topology CAD-link execution is still in progress.",
                status_code=409,
            )
'''
    new_deadline = '''        if time.monotonic() >= deadline:
            recovered = _recover_abandoned_reservation(workspace_id, candidate_id)
            if recovered is not None:
                return recovered
            raise CadLinkError(
                "cad_link_execution_in_progress",
                "The matching topology CAD-link execution is still in progress.",
                status_code=409,
            )
'''
    if text.count(old_deadline) != 1:
        raise SystemExit("replay deadline target missing")
    text = text.replace(old_deadline, new_deadline, 1)

    recovery_marker = '''def _json_object(raw: Any) -> dict[str, Any]:
'''
    recovery = '''def _recover_abandoned_reservation(
    workspace_id: str,
    candidate_id: str,
) -> Any | None:
    now = utc_now()
    with open_sqlite_connection() as connection:
        connection.execute("BEGIN IMMEDIATE")
        row = connection.execute(
            """
            SELECT c.status, c.updated_at, c.notes,
                   a.id AS attempt_id, a.finished_at
            FROM bluecad_candidates c
            LEFT JOIN bluecad_attempts a
              ON a.candidate_id = c.id AND a.attempt_no = 1
            WHERE c.workspace_id = ? AND c.id = ?
            """,
            (workspace_id, candidate_id),
        ).fetchone()
        if row is None:
            connection.rollback()
            raise _persistence_inconsistent()
        if row["status"] != "generating":
            connection.rollback()
            candidate = get_candidate(workspace_id, candidate_id)
            if candidate is None:
                raise _persistence_inconsistent()
            return candidate
        if _timestamp_age_seconds(row["updated_at"], now) < _ABANDONED_RESERVATION_SECONDS:
            connection.rollback()
            return None
        if row["attempt_id"] is None or row["finished_at"] is not None:
            connection.rollback()
            raise _persistence_inconsistent()

        notes = str(row["notes"] or "").strip()
        suffix = "cad_link_abandoned_reservation"
        notes = f"{notes}; {suffix}" if notes else suffix
        detail = canonical_json(
            {
                "transformation_version": TRANSFORMATION_VERSION,
                "reason": "reservation_lease_expired",
            }
        )
        connection.execute(
            """
            UPDATE bluecad_attempts
            SET build_outcome = 'cad_link_abandoned',
                validation_verdict = 'fail',
                finished_at = ?,
                error_detail_json = ?
            WHERE id = ? AND finished_at IS NULL
            """,
            (now, detail, row["attempt_id"]),
        )
        connection.execute(
            """
            UPDATE bluecad_candidates
            SET status = 'parked', parked_reason = 'cad_link_abandoned',
                notes = ?, updated_at = ?
            WHERE workspace_id = ? AND id = ? AND status = 'generating'
            """,
            (notes, now, workspace_id, candidate_id),
        )
        connection.commit()

    candidate = get_candidate(workspace_id, candidate_id)
    if candidate is None:
        raise _persistence_inconsistent()
    return candidate


def _timestamp_age_seconds(value: Any, current: str) -> float:
    try:
        timestamp = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        now = datetime.fromisoformat(str(current).replace("Z", "+00:00"))
    except ValueError as exc:
        raise _persistence_inconsistent() from exc
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    return max(0.0, (now - timestamp).total_seconds())


'''
    if text.count(recovery_marker) != 1:
        raise SystemExit("recovery insertion target missing")
    text = text.replace(recovery_marker, recovery + recovery_marker, 1)
    path.write_text(text, encoding="utf-8")


def patch_preflight() -> None:
    path = Path("backend/app/modules/bluecad/cad_link_topology_preflight.py")
    text = path.read_text(encoding="utf-8")
    old = '''        topology = _classify_pair_intersection(left.shape, right.shape)
        minimum_distance = _strict_number(topology.get("minimum_distance_mm"))
        has_topology = any(
            topology[key] > 0 for key in ("face_count", "edge_count", "vertex_count")
        )
        has_contact = minimum_distance <= COINCIDENCE_ABS_TOL_MM or has_topology
'''
    new = '''        topology = _classify_pair_intersection(left.shape, right.shape)
        has_contact = _has_topological_contact(topology)
'''
    if text.count(old) != 1:
        raise SystemExit("preflight contact target missing")
    text = text.replace(old, new, 1)
    marker = '''def _build_preflight_evidence(
'''
    helper = '''def _has_topological_contact(topology: Mapping[str, Any]) -> bool:
    return any(
        int(topology.get(key, 0)) > 0
        for key in ("face_count", "edge_count", "vertex_count")
    )


'''
    if text.count(marker) != 1:
        raise SystemExit("preflight helper insertion target missing")
    text = text.replace(marker, helper + marker, 1)
    path.write_text(text, encoding="utf-8")


def patch_service() -> None:
    path = Path("backend/app/modules/bluecad/service.py")
    text = path.read_text(encoding="utf-8")
    old = '''    process.start()
    payload: dict[str, Any] | None = None
'''
    new = '''    try:
        process.start()
    except Exception as exc:
        result_queue.close()
        error = BluecadError(
            "KERNEL_ERROR",
            {
                "message": "build worker could not start",
                "type": type(exc).__name__,
            },
        )
        report = write_validation_report(canonical, out_path, error=error)
        return BuildResult(
            canonical["spec_id"],
            out_path,
            None,
            out_path / "validation_report.json",
            None,
            report,
            "error",
            [error.as_report_error()],
        )
    payload: dict[str, Any] | None = None
'''
    if text.count(old) != 1:
        raise SystemExit("service startup target missing")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def patch_concurrency_tests() -> None:
    path = Path("backend/tests/bluecad/test_cad_link_topology_concurrency.py")
    text = path.read_text(encoding="utf-8")
    text = text.replace(
        "from uuid import uuid4\n\nimport pytest\n",
        "from contextlib import contextmanager\n"
        "from datetime import datetime, timedelta, timezone\n"
        "from typing import Any\n"
        "from uuid import uuid4\n\n"
        "import pytest\n",
        1,
    )
    addition = '''


def test_lock_contention_replays_the_winning_reservation(monkeypatch) -> None:
    import app.modules.bluecad.cad_link_topology_execute as execute_module

    preview_digest = "sha256:" + "4" * 64
    payload = execute_module.CadLink072ExecuteRequest(
        source_simulation_run_id="run-lock-probe",
        layout_spec={},
        analysis_spec=None,
        preview_digest=preview_digest,
    )
    monkeypatch.setattr(
        execute_module,
        "_preview_for_execute",
        lambda *_args: {"preview_digest": preview_digest},
    )
    existing_rows = iter([None, {"id": "winning-link"}])
    monkeypatch.setattr(
        execute_module,
        "_load_existing_link",
        lambda *_args: next(existing_rows),
    )
    sentinel = object()
    monkeypatch.setattr(
        execute_module,
        "_replay_response",
        lambda *_args: sentinel,
    )

    class LockedConnection:
        def execute(self, statement: str, *_args: Any):
            assert statement == "BEGIN IMMEDIATE"
            raise execute_module.sqlite3.OperationalError("database is locked")

    @contextmanager
    def locked_connection():
        yield LockedConnection()

    monkeypatch.setattr(execute_module, "open_sqlite_connection", locked_connection)

    assert execute_module.execute_cad_link_072("bluerev", payload) is sentinel


def test_abandoned_reservation_is_parked_and_attempt_is_finished(
    initialized_storage,
    monkeypatch,
) -> None:
    import app.modules.bluecad.cad_link_topology_execute as execute_module

    candidate_id = str(uuid4())
    attempt_id = str(uuid4())
    old = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()
    with open_sqlite_connection() as connection:
        connection.execute(
            """
            INSERT INTO bluecad_candidates (
                id, workspace_id, brief_text, brief_digest, status,
                parked_reason, spec_artifact_id, glb_artifact_id,
                report_artifact_id, promoted_decision_id, origin,
                parent_candidate_id, loop_config_json, created_at,
                updated_at, notes
            ) VALUES (?, 'bluerev', 'abandoned reservation probe', ?, 'generating',
                NULL, NULL, NULL, NULL, NULL, 'process_linked', NULL,
                '{}', ?, ?, 'abandoned reservation probe')
            """,
            (candidate_id, "sha256:" + "5" * 64, old, old),
        )
        connection.execute(
            """
            INSERT INTO bluecad_attempts (
                id, candidate_id, attempt_no, route_class,
                proposal_ai_job_id, proposal_outcome, build_outcome,
                validation_verdict, spec_artifact_id, report_artifact_id,
                manifest_artifact_id, started_at, finished_at, error_detail_json
            ) VALUES (?, ?, 1, 'deterministic:cad_link:072', NULL,
                'not_applicable', NULL, NULL, NULL, NULL, NULL, ?, NULL, NULL)
            """,
            (attempt_id, candidate_id, old),
        )
        connection.commit()

    monkeypatch.setattr(execute_module, "_REPLAY_WAIT_SECONDS", 0.0)
    monkeypatch.setattr(execute_module, "_REPLAY_POLL_SECONDS", 0.0)
    monkeypatch.setattr(execute_module, "_ABANDONED_RESERVATION_SECONDS", 1.0)

    candidate = execute_module._wait_for_replay_candidate("bluerev", candidate_id)

    assert candidate.status == "parked"
    assert candidate.parked_reason == "cad_link_abandoned"
    with open_sqlite_connection() as connection:
        attempt = connection.execute(
            "SELECT * FROM bluecad_attempts WHERE id = ?", (attempt_id,)
        ).fetchone()
        assert attempt is not None
        assert attempt["build_outcome"] == "cad_link_abandoned"
        assert attempt["validation_verdict"] == "fail"
        assert attempt["finished_at"] is not None
'''
    if "test_lock_contention_replays_the_winning_reservation" in text:
        raise SystemExit("concurrency tests already patched")
    path.write_text(text + addition, encoding="utf-8")


def patch_preflight_tests() -> None:
    path = Path("backend/tests/bluecad/test_cad_link_topology_preflight.py")
    text = path.read_text(encoding="utf-8")
    text = text.replace(
        "    _classify_pair_intersection,\n    _kernel_bbox,\n",
        "    _classify_pair_intersection,\n    _has_topological_contact,\n    _kernel_bbox,\n",
        1,
    )
    addition = '''


def test_positive_submicron_gap_is_not_classified_as_contact() -> None:
    topology = {
        "minimum_distance_mm": 5e-7,
        "face_count": 0,
        "edge_count": 0,
        "vertex_count": 0,
    }

    assert _has_topological_contact(topology) is False


def test_actual_topological_contact_is_classified() -> None:
    topology = {
        "minimum_distance_mm": 0.0,
        "face_count": 0,
        "edge_count": 0,
        "vertex_count": 1,
    }

    assert _has_topological_contact(topology) is True
'''
    if "test_positive_submicron_gap_is_not_classified_as_contact" in text:
        raise SystemExit("preflight tests already patched")
    path.write_text(text + addition, encoding="utf-8")


def patch_service_tests() -> None:
    path = Path("backend/tests/bluecad/test_build_service_spawn.py")
    text = path.read_text(encoding="utf-8")
    addition = '''


def test_worker_start_failure_returns_bounded_error_result(
    tmp_path,
    monkeypatch,
) -> None:
    import app.modules.bluecad.service as service

    class StartQueue:
        def close(self) -> None:
            return None

    class StartFailProcess:
        def start(self) -> None:
            raise RuntimeError("process capacity exhausted")

    class StartFailContext:
        def Queue(self, *, maxsize: int) -> StartQueue:
            assert maxsize == 1
            return StartQueue()

        def Process(self, **kwargs: Any) -> StartFailProcess:
            assert kwargs["daemon"] is True
            return StartFailProcess()

    monkeypatch.setattr(
        service.mp,
        "get_context",
        lambda method: StartFailContext() if method == "spawn" else None,
    )

    result = service.build_geometry_spec(
        _tube_spec(),
        tmp_path / "start-failure",
        timeout_s=10.0,
    )

    assert result.verdict == "error"
    assert result.errors[0]["code"] == "KERNEL_ERROR"
    assert result.report_path.is_file()
    assert result.report["errors"][0]["detail"]["message"] == (
        "build worker could not start"
    )
'''
    if "test_worker_start_failure_returns_bounded_error_result" in text:
        raise SystemExit("service tests already patched")
    path.write_text(text + addition, encoding="utf-8")


patch_execute()
patch_preflight()
patch_service()
patch_concurrency_tests()
patch_preflight_tests()
patch_service_tests()
