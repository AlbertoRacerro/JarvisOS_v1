from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from app.core.config import get_settings
from app.core.database import initialize_database, open_retrieval_index_connection, open_sqlite_connection
from app.modules.ai.context_builder import canonical_digest
from app.modules.ai.jarvis_context_models import SourceRef
from app.modules.ai.retrieval_contracts import IndexDocument
from app.modules.ai.retrieval_index import SQLiteIndexStore, repository_symbol_documents
from app.modules.modeling.models import DecisionCreate
from app.modules.modeling.service import create_decision
from app.modules.workspaces.service import seed_default_workspace


@pytest.fixture
def store(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[SQLiteIndexStore, dict[str, IndexDocument]]:
    monkeypatch.setenv("JARVISOS_DATA_ROOT", str(tmp_path))
    get_settings.cache_clear()
    docs = {
        "a": _doc("a", "w1", "alpha reactor pressure"),
        "b": _doc("b", "w1", "beta pressure vessel"),
        "c": _doc("c", "w2", "alpha secret workspace"),
    }
    index = SQLiteIndexStore(documents=lambda: docs.values(), resolver=lambda ref: docs.get(ref.object_id))
    yield index, docs
    get_settings.cache_clear()


def _doc(id_: str, workspace: str, text: str, revision: str = "1") -> IndexDocument:
    return IndexDocument(source_ref=SourceRef(authority_owner="fixture", object_type="record", object_id=id_,
                         workspace_id=workspace, revision=revision, content_digest=canonical_digest(text)), text=text)


def test_rebuild_is_stable_and_separate_from_canonical_database(store: tuple[SQLiteIndexStore, dict[str, IndexDocument]], tmp_path: Path) -> None:
    index, _ = store
    first = index.rebuild()
    with open_retrieval_index_connection() as db:
        before = [tuple(row) for row in db.execute("SELECT * FROM docs ORDER BY key")]
    assert index.rebuild() == first
    with open_retrieval_index_connection() as db:
        assert [tuple(row) for row in db.execute("SELECT * FROM docs ORDER BY key")] == before
    assert (tmp_path / "retrieval-index.sqlite3").exists()
    assert not (tmp_path / "jarvisos.db").exists()


def test_exact_phrase_lexical_vector_and_workspace_isolation(store: tuple[SQLiteIndexStore, dict[str, IndexDocument]]) -> None:
    index, _ = store
    index.rebuild()
    lexical = index.search_lexical('"alpha reactor"', limit=5, workspace_id="w1")
    assert [hit.source_ref.object_id for hit in lexical] == ["a"]
    assert [hit.source_ref.object_id for hit in index.search_lexical("a", limit=5, workspace_id="w1")] == ["a"]
    exact = _doc("path::alpha", "w1", "opaque symbol body")
    index.upsert([exact])
    assert [hit.source_ref.object_id for hit in index.search_lexical("path::alpha", limit=5, workspace_id="w1")] == ["path::alpha"]
    assert index.search_lexical("secret", limit=5, workspace_id="w1") == []
    assert index.search_vector("pressure", limit=5, workspace_id="w1")
    bundle = index.build_bundle("alpha pressure", workspace_id="w1", token_budget=100)
    assert {item.source_ref.object_id for item in bundle.items} <= {"a", "b"}
    assert bundle.items and bundle.token_estimate <= 100


def test_stale_deleted_and_budget_manifest(store: tuple[SQLiteIndexStore, dict[str, IndexDocument]]) -> None:
    index, docs = store
    index.rebuild()
    old = docs["a"].source_ref
    docs["a"] = _doc("a", "w1", "changed pressure", revision="2")
    stale = index.resolve_authoritative(old)
    assert stale.state == "stale" and stale.content is None
    index.upsert([docs["a"]])
    index.delete([old])
    assert index.search_lexical("changed", limit=5, workspace_id="w1")
    index.upsert([_doc("a", "w1", "alpha reactor pressure")])
    bundle = index.build_bundle("alpha reactor", workspace_id="w1", token_budget=1)
    assert [entry.outcome for entry in bundle.evidence_manifest] == ["stale"]
    del docs["a"]
    assert index.resolve_authoritative(old).state == "unavailable"
    index.delete([old])
    assert not index.search_lexical("alpha reactor", limit=5, workspace_id="w1")
    small = index.build_bundle("beta pressure", workspace_id="w1", token_budget=1)
    assert small.token_estimate == 0
    assert [entry.outcome for entry in small.evidence_manifest] == ["dropped_budget"]


def test_fusion_and_bounded_graph(store: tuple[SQLiteIndexStore, dict[str, IndexDocument]]) -> None:
    index, docs = store
    index.rebuild()
    index.add_edge(docs["a"].source_ref, docs["b"].source_ref, "knowledge_relation")
    with pytest.raises(ValueError):
        index.add_edge(docs["b"].source_ref, docs["c"].source_ref, "knowledge_relation")
    assert [hit.source_ref.object_id for hit in index.expand_graph([docs["a"].source_ref], depth=1, limit=5)] == ["b"]
    assert len(index.expand_graph([docs["a"].source_ref], depth=3, limit=1)) == 1
    bundle = index.build_bundle("reactor", workspace_id="w1", token_budget=100, expansion_level=1)
    assert bundle.items[0].source_ref.object_id == "a"
    assert {item.source_ref.object_id for item in bundle.items} == {"a", "b"}
    assert any(hit.lexical_score is not None for hit in index.search_lexical("reactor", limit=5))
    assert any(hit.vector_score is not None for hit in index.search_vector("reactor", limit=5))
    fused = index.search_hybrid("reactor", limit=5, workspace_id="w1")
    assert fused[0].source_ref.object_id == "a"
    assert fused[0].lexical_score is not None and fused[0].vector_score is not None
    assert fused[0].fused_score > 0


def test_canonical_owner_reread_refuses_changed_decision(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JARVISOS_DATA_ROOT", str(tmp_path))
    get_settings.cache_clear()
    initialize_database()
    seed_default_workspace()
    decision = create_decision("bluerev", DecisionCreate(title="Pump sizing", decision_text="Use lower pressure"))
    index = SQLiteIndexStore()
    first = index.rebuild()
    assert index.rebuild() == first
    hit = index.search_lexical("Pump", limit=5, workspace_id="bluerev")[0]
    assert hit.source_ref.object_id == decision.id
    assert index.resolve_authoritative(hit.source_ref).state == "current"
    with open_sqlite_connection() as db:
        db.execute("UPDATE decisions SET decision_text=?, updated_at=? WHERE id=?", ("Use higher pressure", "later", decision.id))
        db.commit()
    assert index.resolve_authoritative(hit.source_ref).state == "stale"
    bundle = index.build_bundle("Pump", workspace_id="bluerev", token_budget=200)
    assert not bundle.items and bundle.evidence_manifest[0].outcome == "stale"
    get_settings.cache_clear()


def test_repository_symbols_are_bound_to_exact_git_content(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JARVISOS_DATA_ROOT", str(tmp_path / "data"))
    get_settings.cache_clear()
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "sample.py").write_text("def alpha():\n    return 1\n\nclass Beta:\n    pass\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    subprocess.run(["git", "-C", str(repo), "add", "sample.py"], check=True)
    subprocess.run(["git", "-C", str(repo), "-c", "user.name=Test", "-c", "user.email=test@example.invalid",
                    "commit", "-qm", "fixture"], check=True)
    sha = subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()
    docs = repository_symbol_documents(repo, sha, ["sample.py"])
    assert [doc.source_ref.object_id for doc in docs] == ["sample.py::alpha", "sample.py::Beta"]
    assert docs[0].source_ref.location.start_line == 1
    index = SQLiteIndexStore(documents=lambda: docs, repository_root=repo)
    index.rebuild()
    assert index.resolve_authoritative(docs[0].source_ref).state == "current"
    (repo / "sample.py").write_text("def alpha():\n    return 2\n", encoding="utf-8")
    assert index.resolve_authoritative(docs[0].source_ref).state == "current"
    get_settings.cache_clear()
