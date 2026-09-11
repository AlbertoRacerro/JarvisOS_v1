from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.modules.project_search import routes, service


def _modeling_fixture(*_args, **_kwargs):
    return {
        "requirement": [
            SimpleNamespace(
                id="req-1",
                statement="reactor",
                rationale="Primary design requirement",
                notes=None,
                status="active",
            )
        ],
        "parameter": [],
        "assumption": [],
        "decision": [],
    }


def _model_fixture(_workspace_id: str, query: str):
    assert query == "reactor"
    return [
        SimpleNamespace(
            title="Reactor model",
            engineering_question="Predict conversion",
            scope="Design point",
            versions=[
                SimpleNamespace(
                    model_spec_id="model-1",
                    model_version_id="version-1",
                    version_label="v1",
                    implementation_kind="python",
                    status="active",
                )
            ],
        )
    ]


def _literature_fixture(_workspace_id: str, query: str):
    assert query == "reactor"
    return [
        SimpleNamespace(
            id="source-1",
            title="Advanced reactor paper",
            citation="Example et al.",
            publisher="Journal",
            state="accepted",
            source_ref="literature_source:source-1",
            entries=[
                SimpleNamespace(
                    id="entry-1",
                    entry_kind="claim",
                    statement="Reactor residence time controls conversion",
                    value_text=None,
                    value_number=None,
                    unit=None,
                    status="accepted",
                    locator_kind="line",
                    locator_start=12,
                    locator_end=12,
                    context_text="Reported reactor result",
                    provenance_ref="literature_entry:entry-1",
                )
            ],
        )
    ]


def _install_fixtures(monkeypatch) -> None:
    monkeypatch.setattr(service, "select_context_records", _modeling_fixture)
    monkeypatch.setattr(service, "search_model_dossier_index", _model_fixture)
    monkeypatch.setattr(service, "search_literature_sources", _literature_fixture)


def test_project_search_orders_exact_prefix_contains_and_preserves_identity(monkeypatch) -> None:
    _install_fixtures(monkeypatch)

    result = service.search_project("ws-1", query="reactor", kinds=None, limit=10)

    assert [item.kind for item in result.items] == [
        "requirement",
        "model",
        "literature_entry",
        "literature_source",
    ]
    assert [item.match_tier for item in result.items] == [
        "exact",
        "prefix",
        "prefix",
        "contains",
    ]
    assert result.items[0].stable_ref == "requirement:req-1"
    model = next(item for item in result.items if item.kind == "model")
    assert model.route == "/memory/models"
    assert model.route_params == {"modelSpecId": "model-1", "modelVersionId": "version-1"}
    entry = next(item for item in result.items if item.kind == "literature_entry")
    assert entry.provenance_refs == ["literature_entry:entry-1"]
    assert entry.source_refs == ["literature_source:source-1"]
    assert entry.route_params["locatorStart"] == "12"


def test_project_search_global_limit_is_deterministic_and_marks_truncation(monkeypatch) -> None:
    _install_fixtures(monkeypatch)

    first = service.search_project("ws-1", query="reactor", kinds=None, limit=2)
    second = service.search_project("ws-1", query="reactor", kinds=None, limit=2)

    assert first.truncated is True
    assert first.total_returned == 2
    assert [item.stable_ref for item in first.items] == [item.stable_ref for item in second.items]


def test_kind_filter_does_not_read_unrequested_owners(monkeypatch) -> None:
    monkeypatch.setattr(service, "select_context_records", _modeling_fixture)

    def forbidden(*_args, **_kwargs):
        raise AssertionError("unrequested owner was read")

    monkeypatch.setattr(service, "search_model_dossier_index", forbidden)
    monkeypatch.setattr(service, "search_literature_sources", forbidden)

    result = service.search_project("ws-1", query="reactor", kinds=["requirement"], limit=10)
    assert [item.kind for item in result.items] == ["requirement"]


def test_literal_matching_treats_fts_sql_and_unicode_shapes_as_data() -> None:
    fields = {"statement": 'α "reactor*" OR 1=1 --'}
    assert service._match('"reactor*"', fields) == ("contains", ["statement"])
    assert service._match("OR 1=1 --", fields) == ("contains", ["statement"])
    assert service._match("Α", fields) == ("prefix", ["statement"])


def test_owner_failure_fails_whole_request(monkeypatch) -> None:
    monkeypatch.setattr(service, "select_context_records", _modeling_fixture)

    def broken_owner(_workspace_id: str, _query: str):
        raise RuntimeError("owner read unavailable")

    monkeypatch.setattr(service, "search_model_dossier_index", broken_owner)
    monkeypatch.setattr(service, "search_literature_sources", _literature_fixture)

    with pytest.raises(RuntimeError, match="owner read unavailable"):
        service.search_project("ws-1", query="reactor", kinds=None, limit=30)


def test_kind_parser_accepts_repeated_csv_and_rejects_unknown() -> None:
    assert routes._parse_kinds(["requirement,model", "literature_entry"]) == [
        "requirement",
        "model",
        "literature_entry",
    ]
    with pytest.raises(HTTPException) as exc_info:
        routes._parse_kinds(["requirement,unknown"])
    assert exc_info.value.status_code == 422
