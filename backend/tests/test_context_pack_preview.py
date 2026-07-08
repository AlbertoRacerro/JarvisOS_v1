from __future__ import annotations

import json

from fastapi.testclient import TestClient

from app.core.bootstrap import initialize_storage
from app.core.database import open_sqlite_connection
from app.main import app
from app.modules.ai.context_builder import ContextSelectionSpec, _serialize_blocks, build_workspace_context_bundle
from app.modules.modeling.models import AssumptionCreate, DecisionCreate, ParameterCreate, RequirementCreate
from app.modules.modeling.service import create_assumption, create_decision, create_parameter, create_requirement


def _seed() -> dict[str, str]:
    initialize_storage(seed_default=True)
    decision = create_decision("bluerev", DecisionCreate(title="Use C++ solver", decision_text="alpha-beta stable 1.2", status="accepted"))
    draft_decision = create_decision("bluerev", DecisionCreate(title="Draft", decision_text="C++ draft", status="draft"))
    assumption = create_assumption("bluerev", AssumptionCreate(statement="Flow alpha-beta is steady", status="accepted"))
    parameter = create_parameter(
        "bluerev",
        ParameterCreate(name="C++ gain", symbol="k12", value="1.2", unit="m", value_status="validated", source_ref="test"),
    )
    requirement = create_requirement("bluerev", RequirementCreate(statement="Controller supports alpha-beta and C++ 1.2", status="active"))
    return {"decision": decision.id, "draft_decision": draft_decision.id, "assumption": assumption.id, "parameter": parameter.id, "requirement": requirement.id}


def _ids(bundle) -> set[str]:
    return {block["id"] for block in bundle.blocks}


def _types(bundle) -> list[str]:
    return [block["type"] for block in bundle.blocks]


def test_no_selection_workspace_context_bundle_is_byte_identical() -> None:
    _seed()
    before = build_workspace_context_bundle("bluerev")
    after = build_workspace_context_bundle("bluerev", selection=None)
    assert json.dumps(before.blocks, sort_keys=True, separators=(",", ":")) == json.dumps(after.blocks, sort_keys=True, separators=(",", ":"))
    assert before.context_digest == after.context_digest
    assert before.sources == after.sources
    assert before.included_count == after.included_count
    assert before.dropped_count == after.dropped_count


def test_selection_by_kind_status_id_query_and_deterministic_order() -> None:
    ids = _seed()
    selected = build_workspace_context_bundle(
        "bluerev",
        selection=ContextSelectionSpec(kinds=["decision", "requirement"], query="alpha-beta"),
    )
    assert [block["type"] for block in selected.blocks] == ["decision", "requirement"]
    assert ids["draft_decision"] not in _ids(selected)

    explicit = build_workspace_context_bundle(
        "bluerev",
        selection=ContextSelectionSpec(kinds=["decision"], ids=[ids["draft_decision"]]),
    )
    assert _ids(explicit) == {ids["draft_decision"]}

    first = build_workspace_context_bundle("bluerev", selection=ContextSelectionSpec(query="alpha-beta"))
    second = build_workspace_context_bundle("bluerev", selection=ContextSelectionSpec(query="alpha-beta"))
    assert first.blocks == second.blocks
    assert first.context_digest == second.context_digest


def test_budget_truncation_and_digest_stability() -> None:
    _seed()
    full = build_workspace_context_bundle("bluerev", budget_chars=32_000, selection=ContextSelectionSpec())
    assert _types(full) == ["decision", "assumption", "parameter", "requirement"]

    without_parameter = [block for block in full.blocks if block["type"] != "parameter"]
    parameter_dropped = build_workspace_context_bundle(
        "bluerev",
        budget_chars=len(_serialize_blocks(without_parameter)),
        selection=ContextSelectionSpec(),
    )
    assert _types(parameter_dropped) == ["decision", "assumption", "requirement"]

    without_parameter_assumption = [
        block for block in full.blocks if block["type"] not in {"parameter", "assumption"}
    ]
    parameter_then_assumption_dropped = build_workspace_context_bundle(
        "bluerev",
        budget_chars=len(_serialize_blocks(without_parameter_assumption)),
        selection=ContextSelectionSpec(),
    )
    assert _types(parameter_then_assumption_dropped) == ["decision", "requirement"]

    only_decision = [block for block in full.blocks if block["type"] == "decision"]
    parameter_assumption_requirement_dropped = build_workspace_context_bundle(
        "bluerev",
        budget_chars=len(_serialize_blocks(only_decision)),
        selection=ContextSelectionSpec(),
    )
    assert _types(parameter_assumption_requirement_dropped) == ["decision"]
    assert parameter_assumption_requirement_dropped.context_digest == build_workspace_context_bundle(
        "bluerev",
        budget_chars=len(_serialize_blocks(only_decision)),
        selection=ContextSelectionSpec(),
    ).context_digest


def test_preview_endpoint_is_side_effect_free_and_manifest_matches() -> None:
    _seed()
    client = TestClient(app)
    with open_sqlite_connection() as connection:
        before = connection.execute("SELECT COUNT(*) AS count FROM ai_jobs").fetchone()["count"]
    response = client.post("/ai/context/packs/preview", json={"workspace_id": "bluerev", "selection": {"query": "alpha-beta"}})
    assert response.status_code == 200
    payload = response.json()
    assert payload["char_count"] == len(json.dumps(payload["blocks"], sort_keys=True, separators=(",", ":"), ensure_ascii=False))
    assert payload["estimated_token_count"] == payload["char_count"] // 4
    assert payload["context_sources_manifest"] == [
        {"source": block["source"], "type": block.get("type"), "id": block.get("id")} for block in payload["blocks"]
    ]
    with open_sqlite_connection() as connection:
        after = connection.execute("SELECT COUNT(*) AS count FROM ai_jobs").fetchone()["count"]
    assert after == before


def test_fts_backfill_and_literal_query_handling(monkeypatch) -> None:
    ids = _seed()
    initialize_storage(seed_default=True)
    for query in ("C++", "1.2", "alpha-beta"):
        bundle = build_workspace_context_bundle("bluerev", selection=ContextSelectionSpec(query=query))
        assert ids["decision"] in _ids(bundle)
        assert ids["requirement"] in _ids(bundle)

    fts_bundle = build_workspace_context_bundle("bluerev", selection=ContextSelectionSpec(query="alpha-beta"))

    from app.modules import modeling

    monkeypatch.setattr(modeling.service, "sqlite_fts5_available", lambda connection: False)
    like_bundle = build_workspace_context_bundle("bluerev", selection=ContextSelectionSpec(query="alpha-beta"))
    assert _ids(like_bundle) == _ids(fts_bundle)


def test_like_fallback_escapes_sql_wildcards(monkeypatch) -> None:
    seed_ids = _seed()
    literal_underscore = create_parameter(
        "bluerev",
        ParameterCreate(
            name="C_D coefficient",
            symbol="c_d",
            value="0.8",
            unit="1",
            value_status="validated",
            source_ref="test",
        ),
    )
    wildcard_decoy = create_parameter(
        "bluerev",
        ParameterCreate(
            name="CAD coefficient",
            symbol="cad",
            value="0.9",
            unit="1",
            value_status="validated",
            source_ref="test",
        ),
    )
    literal_percent = create_requirement(
        "bluerev",
        RequirementCreate(statement="Pump operates at 100% duty", status="active"),
    )
    percent_decoy = create_requirement(
        "bluerev",
        RequirementCreate(statement="Pump operates at 100x duty", status="active"),
    )

    from app.modules import modeling

    monkeypatch.setattr(modeling.service, "sqlite_fts5_available", lambda connection: False)

    percent_ids = _ids(build_workspace_context_bundle("bluerev", selection=ContextSelectionSpec(query="%")))
    assert literal_percent.id in percent_ids
    assert percent_decoy.id not in percent_ids
    assert seed_ids["decision"] not in percent_ids

    underscore_ids = _ids(build_workspace_context_bundle("bluerev", selection=ContextSelectionSpec(query="_")))
    assert literal_underscore.id in underscore_ids
    assert wildcard_decoy.id not in underscore_ids
    assert seed_ids["decision"] not in underscore_ids

    cd_ids = _ids(build_workspace_context_bundle("bluerev", selection=ContextSelectionSpec(query="C_D")))
    assert literal_underscore.id in cd_ids
    assert wildcard_decoy.id not in cd_ids

    duty_ids = _ids(build_workspace_context_bundle("bluerev", selection=ContextSelectionSpec(query="100%")))
    assert literal_percent.id in duty_ids
    assert percent_decoy.id not in duty_ids
