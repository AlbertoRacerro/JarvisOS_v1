from __future__ import annotations

from uuid import uuid4

import pytest

from app.core.database import open_sqlite_connection
from app.modules.bluecad.cad_link import CadLinkError
from app.modules.events.service import utc_now


@pytest.fixture
def initialized_storage(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("JARVISOS_DATA_ROOT", str(tmp_path / "JarvisOS"))
    monkeypatch.setenv("DATABASE_URL", "must-not-enter-cad-link-074-concurrency")
    from app.core.config import get_settings

    get_settings.cache_clear()
    from app.core.bootstrap import initialize_storage

    initialize_storage(seed_default=True)
    yield
    get_settings.cache_clear()


def test_stuck_concurrent_reservation_fails_bounded(
    initialized_storage,
    monkeypatch,
) -> None:
    import app.modules.bluecad.cad_link_topology_execute as execute_module

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
            ) VALUES (?, 'bluerev', 'stuck concurrency probe', ?, 'generating',
                NULL, NULL, NULL, NULL, NULL, 'process_linked', NULL,
                '{}', ?, ?, 'stuck concurrency probe')
            """,
            (candidate_id, "sha256:" + "2" * 64, now, now),
        )
        connection.commit()

    monkeypatch.setattr(execute_module, "_REPLAY_WAIT_SECONDS", 0.0)
    monkeypatch.setattr(execute_module, "_REPLAY_POLL_SECONDS", 0.0)

    with pytest.raises(CadLinkError) as exc_info:
        execute_module._wait_for_replay_candidate("bluerev", candidate_id)

    assert exc_info.value.code == "cad_link_execution_in_progress"
    assert exc_info.value.status_code == 409
    with open_sqlite_connection() as connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM bluecad_candidates WHERE id = ?",
            (candidate_id,),
        ).fetchone()[0] == 1
