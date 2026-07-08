from __future__ import annotations

import json

from fastapi.testclient import TestClient

from app.main import app


def _init() -> None:
    from app.core.bootstrap import initialize_storage

    initialize_storage(seed_default=True)


def _seed() -> None:
    from app.core.database import open_sqlite_connection

    rows = [
        (
            "dec-old",
            "decisions",
            "title, decision_text, rationale, status, linked_run_id, notes",
            ("Old", "old alpha", None, "accepted", None, None),
            "2026-01-01T00:00:00Z",
        ),
        (
            "dec-new",
            "decisions",
            "title, decision_text, rationale, status, linked_run_id, notes",
            ("New", "new needle", "rat", "accepted", None, None),
            "2026-01-02T00:00:00Z",
        ),
        (
            "dec-draft",
            "decisions",
            "title, decision_text, rationale, status, linked_run_id, notes",
            ("Draft", "needle", None, "draft", None, None),
            "2026-01-03T00:00:00Z",
        ),
        (
            "asm-ok",
            "assumptions",
            "statement, scope, confidence, status, source_ref, notes",
            ("assume needle", None, "high", "accepted", None, None),
            "2026-01-02T00:00:00Z",
        ),
        (
            "asm-no",
            "assumptions",
            "statement, scope, confidence, status, source_ref, notes",
            ("assume no", None, None, "proposed", None, None),
            "2026-01-04T00:00:00Z",
        ),
        (
            "par-ok",
            "parameters",
            "name, symbol, value, unit, value_status, value_min, value_max, source_ref, confidence, status, notes",
            ("param needle", "pn", "1", "m", "validated", None, None, "src", None, "draft", None),
            "2026-01-02T00:00:00Z",
        ),
        (
            "par-no",
            "parameters",
            "name, symbol, value, unit, value_status, value_min, value_max, source_ref, confidence, status, notes",
            ("param no", None, "1", "m", "candidate", None, None, None, None, "draft", None),
            "2026-01-04T00:00:00Z",
        ),
        (
            "req-ok",
            "requirements",
            "statement, rationale, status, notes, schema_version",
            ("require needle", None, "active", None, 1),
            "2026-01-02T00:00:00Z",
        ),
        (
            "req-no",
            "requirements",
            "statement, rationale, status, notes, schema_version",
            ("require no", None, "draft", None, 1),
            "2026-01-04T00:00:00Z",
        ),
    ]
    with open_sqlite_connection() as connection:
        for record_id, table, cols, values, ts in rows:
            placeholders = ", ".join("?" for _ in values)
            connection.execute(
                f"INSERT INTO {table} (id, workspace_id, {cols}, created_at, updated_at) VALUES (?, ?, {placeholders}, ?, ?)",
                (record_id, "bluerev", *values, ts, ts),
            )
        connection.commit()


def _ids(bundle_or_payload: object) -> list[str]:
    blocks = bundle_or_payload.blocks if hasattr(bundle_or_payload, "blocks") else bundle_or_payload["blocks"]
    return [block["id"] for block in blocks]


def test_selection_spec_filters_ordering_query_fallback_and_digest(monkeypatch) -> None:
    _init()
    _seed()
    from app.modules.ai.context_builder import ContextSelectionSpec, build_workspace_context_bundle
    from app.modules.modeling import service as modeling_service

    selection = ContextSelectionSpec(query="needle")
    first = build_workspace_context_bundle("bluerev", selection=selection)
    second = build_workspace_context_bundle("bluerev", selection=selection)
    assert _ids(first) == ["dec-new", "asm-ok", "par-ok", "req-ok"]
    assert first.blocks == second.blocks
    assert first.context_digest == second.context_digest

    kinds_only = build_workspace_context_bundle(
        "bluerev", selection=ContextSelectionSpec(kinds=["decision", "requirement"])
    )
    assert {block["type"] for block in kinds_only.blocks} == {"decision", "requirement"}
    assert _ids(kinds_only) == ["dec-new", "dec-old", "req-ok"]

    explicit = build_workspace_context_bundle(
        "bluerev", selection=ContextSelectionSpec(kinds=["decision"], ids=["dec-draft", "asm-ok"])
    )
    assert "dec-draft" in _ids(explicit)
    assert "asm-ok" not in _ids(explicit)

    fts_ids = _ids(first)
    monkeypatch.setattr(modeling_service, "context_pack_fts_available", lambda connection: False)
    fallback = build_workspace_context_bundle("bluerev", selection=selection)
    assert _ids(fallback) == fts_ids


def test_selection_budget_priority_retains_decisions_and_requirements() -> None:
    _init()
    _seed()
    from app.modules.ai.context_builder import ContextSelectionSpec, build_workspace_context_bundle

    bundle = build_workspace_context_bundle("bluerev", budget_chars=360, selection=ContextSelectionSpec(query="needle"))
    ids = set(_ids(bundle))
    assert {"dec-new", "req-ok"}.issubset(ids)
    assert "asm-ok" not in ids or "par-ok" not in ids
    assert bundle.dropped_count > 0


def test_preview_endpoint_has_no_ai_side_effects_and_manifest_matches() -> None:
    _init()
    _seed()
    from app.core.database import open_sqlite_connection

    with open_sqlite_connection() as connection:
        before = connection.execute("SELECT COUNT(*) AS count FROM ai_jobs").fetchone()["count"]

    response = TestClient(app).post(
        "/ai/context/packs/preview",
        json={"workspace_id": "bluerev", "selection": {"query": "needle"}},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["char_count"] == len(
        json.dumps(payload["blocks"], sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    )
    assert payload["estimated_token_count"] == payload["char_count"] // 4
    block_manifest = [
        {"source": block["source"], "type": block.get("type"), "id": block.get("id")} for block in payload["blocks"]
    ]
    assert payload["context_sources_manifest"] == block_manifest

    with open_sqlite_connection() as connection:
        after = connection.execute("SELECT COUNT(*) AS count FROM ai_jobs").fetchone()["count"]
    assert after == before


def test_context_pack_fts_backfills_existing_records(monkeypatch) -> None:
    from app.core import database
    from app.core.bootstrap import initialize_storage
    from app.core.database import open_sqlite_connection
    from app.modules.ai.context_builder import ContextSelectionSpec, build_workspace_context_bundle

    monkeypatch.setattr(database, "sqlite_supports_fts5", lambda connection: False)
    initialize_storage(seed_default=True)
    _seed()

    monkeypatch.setattr(database, "sqlite_supports_fts5", lambda connection: True)
    initialize_storage(seed_default=True)

    with open_sqlite_connection() as connection:
        indexed = connection.execute("SELECT COUNT(*) AS count FROM context_pack_fts").fetchone()["count"]
    assert indexed == 9

    bundle = build_workspace_context_bundle("bluerev", selection=ContextSelectionSpec(query="needle"))
    assert _ids(bundle) == ["dec-new", "asm-ok", "par-ok", "req-ok"]


def test_preview_fts_queries_treat_engineering_terms_as_literals() -> None:
    _init()
    from app.core.database import open_sqlite_connection

    rows = [
        ("dec-cpp", "C++ parser", "accepted"),
        ("dec-version", "version 1.2 parser", "accepted"),
        ("dec-hyphen", "alpha-beta parser", "accepted"),
    ]
    with open_sqlite_connection() as connection:
        for record_id, text, status in rows:
            connection.execute(
                """
                INSERT INTO decisions (
                    id, workspace_id, title, decision_text, rationale, status,
                    linked_run_id, notes, created_at, updated_at
                )
                VALUES (?, 'bluerev', ?, ?, NULL, ?, NULL, NULL,
                    '2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z')
                """,
                (record_id, text, text, status),
            )
        connection.commit()

    client = TestClient(app)
    for query in ("C++", "1.2", "alpha-beta"):
        response = client.post(
            "/ai/context/packs/preview",
            json={"workspace_id": "bluerev", "selection": {"query": query, "kinds": ["decision"]}},
        )
        assert response.status_code == 200, response.text
        assert response.json()["blocks"]


def test_spec_041_and_042_ai_models_coexist() -> None:
    from app.modules.ai.models import AITaskRunResponse, ContextPackPreviewRequest, ContextPackPreviewResponse

    response = AITaskRunResponse(
        status="completed",
        ledger_id="job-1",
        selected_route_class="local",
        decision_reason="test",
    )
    assert response.records_parse_error is None
    assert response.proposed_record_ids == []
    assert ContextPackPreviewRequest().selection.max_items_per_kind == 10
    preview = ContextPackPreviewResponse(
        blocks=[],
        context_sources_manifest=[],
        char_count=2,
        estimated_token_count=0,
        context_digest=None,
    )
    assert preview.blocks == []


def test_no_selection_context_bundle_legacy_serialization_is_stable() -> None:
    _init()
    _seed()
    from app.modules.ai.context_builder import build_workspace_context_bundle

    bundle = build_workspace_context_bundle("bluerev")
    serialized = json.dumps(bundle.blocks, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    assert serialized == (
        '[{"content":"title=Draft; decision=needle; status=draft","id":"dec-draft",'
        '"source":"decision:dec-draft","type":"decision"},{"content":"title=New; decision=new needle; '
        'status=accepted; rationale=rat","id":"dec-new","source":"decision:dec-new","type":"decision"},'
        '{"content":"title=Old; decision=old alpha; status=accepted","id":"dec-old",'
        '"source":"decision:dec-old","type":"decision"},{"content":"statement=assume no; status=proposed",'
        '"id":"asm-no","source":"assumption:asm-no","type":"assumption"},{"content":"statement=assume '
        'needle; status=accepted; confidence=high","id":"asm-ok","source":"assumption:asm-ok","type":"assumption"},'
        '{"content":"name=param no; value=1; unit=m; status=draft; source=MISSING; [incomplete: not '
        'authoritative]","id":"par-no","source":"parameter:par-no","type":"parameter"},{"content":"name=param '
        'needle; symbol=pn; value=1; unit=m; status=draft; source=src","id":"par-ok",'
        '"source":"parameter:par-ok","type":"parameter"}]'
    )
