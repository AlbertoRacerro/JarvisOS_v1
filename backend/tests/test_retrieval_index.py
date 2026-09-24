from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from app.core.config import get_settings
from app.core.database import initialize_database, open_retrieval_index_connection, open_sqlite_connection
from app.modules.ai import retrieval_index
from app.modules.ai.context_builder import canonical_digest
from app.modules.ai.jarvis_context_models import SourceRef
from app.modules.ai.retrieval_contracts import IndexDocument
from app.modules.ai.retrieval_index import SQLiteIndexStore, repository_file_documents, repository_symbol_documents
from app.modules.ai.thread_models import AIThreadCreate
from app.modules.ai.thread_service import create_thread
from app.modules.bluecad.evidence import EvidenceRecordCreate, create_evidence_record
from app.modules.bluecad.ledger import register_artifact
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
    assert "a" in [hit.source_ref.object_id for hit in lexical]
    assert [hit.source_ref.object_id for hit in index.search_lexical("a", limit=5, workspace_id="w1")] == ["a"]
    exact = _doc("path::alpha", "w1", "opaque symbol body")
    index.upsert([exact])
    assert [hit.source_ref.object_id for hit in index.search_lexical("path::alpha", limit=5, workspace_id="w1")] == ["path::alpha"]
    assert index.search_lexical("secret", limit=5, workspace_id="w1") == []
    assert index.search_vector("pressure", limit=5, workspace_id="w1")
    bundle = index.build_bundle("alpha pressure", workspace_id="w1", token_budget=100)
    assert bundle.items
    assert bundle.items and bundle.token_estimate <= 100
    assert all(item.source_ref.object_type.endswith("summary") for item in bundle.items)


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
    neighbors = index.expand_graph([docs["a"].source_ref], depth=1, limit=5)
    assert "b" in [hit.source_ref.object_id for hit in neighbors]
    assert all(hit.source_ref.workspace_id == "w1" for hit in neighbors)
    assert len(index.expand_graph([docs["a"].source_ref], depth=3, limit=1)) == 1
    bundle = index.build_bundle("reactor", workspace_id="w1", token_budget=100, expansion_level=1)
    assert any(item.source_ref.object_id == "a" for item in bundle.items)
    assert all(item.source_ref.workspace_id == "w1" for item in bundle.items)
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
    assert index.search_lexical("alpha", limit=5)[0].source_ref.object_id == "sample.py::alpha"
    assert index.resolve_authoritative(docs[0].source_ref).state == "current"
    changed_ref = docs[0].source_ref.model_copy(update={"content_digest": canonical_digest("changed")})
    assert index.resolve_authoritative(changed_ref).state == "stale"
    file_doc = repository_file_documents(repo, sha, ["sample.py"])[0]
    assert index.resolve_authoritative(file_doc.source_ref).state == "current"
    changed_file = file_doc.source_ref.model_copy(update={"content_digest": canonical_digest("changed")})
    assert index.resolve_authoritative(changed_file).state == "stale"
    (repo / "sample.py").write_text("def alpha():\n    return 2\n", encoding="utf-8")
    assert index.resolve_authoritative(docs[0].source_ref).state == "current"
    get_settings.cache_clear()


def test_summary_progression_and_source_deletion(store: tuple[SQLiteIndexStore, dict[str, IndexDocument]]) -> None:
    index, docs = store
    index.rebuild()
    summary = index.build_bundle("alpha reactor", workspace_id="w1", token_budget=400, expansion_level=0)
    assert summary.items
    assert all(item.source_ref.object_type.endswith("summary") for item in summary.items)
    expanded = index.build_bundle("alpha reactor", workspace_id="w1", token_budget=400, expansion_level=1)
    assert any(item.source_ref.object_id == "a" and item.expansion_level == 1 for item in expanded.items)
    del docs["a"]
    stale = index.build_bundle("alpha reactor", workspace_id="w1", token_budget=400, expansion_level=1)
    assert not stale.items
    assert all(entry.outcome == "unavailable" for entry in stale.evidence_manifest)


def test_owner_dispatch_refuses_digest_mismatch_for_every_indexed_kind(
    store: tuple[SQLiteIndexStore, dict[str, IndexDocument]], monkeypatch: pytest.MonkeyPatch,
) -> None:
    index, _ = store
    index.resolver = None
    for owner, kind in retrieval_index._OWNER_RESOLVERS:
        ref = SourceRef(authority_owner=owner, object_type=kind, object_id="one", workspace_id="w1",
                        content_digest=canonical_digest("before"))
        changed = IndexDocument(source_ref=ref.model_copy(update={"content_digest": canonical_digest("after")}),
                                text="after")
        monkeypatch.setitem(retrieval_index._OWNER_RESOLVERS, (owner, kind), lambda _ref, doc=changed: doc)
        assert index.resolve_authoritative(ref).state == "stale", (owner, kind)


def test_new_canonical_owners_rebuild_and_reread(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JARVISOS_DATA_ROOT", str(tmp_path))
    get_settings.cache_clear()
    initialize_database()
    seed_default_workspace()
    thread = create_thread(AIThreadCreate(workspace_id="bluerev", title="Pump review"))
    report = tmp_path / "report.txt"
    report.write_text("mesh pass", encoding="utf-8")
    artifact_id = register_artifact("bluerev", report, role="report", source_ref="benchmark")
    evidence = create_evidence_record(EvidenceRecordCreate(
        workspace_id="bluerev", kind="mesh_quality_v0", verdict="pass", metrics_json="{}",
        report_artifact_id=artifact_id,
    ))
    index = SQLiteIndexStore()
    first = index.rebuild()
    assert index.rebuild() == first
    for owner, kind, object_id in (("ai_threads", "thread", thread.id),
                                   ("bluecad", "evidence_record", evidence.id)):
        hit = next(hit for hit in index.search_lexical(object_id, limit=3, workspace_id="bluerev")
                   if hit.source_ref.authority_owner == owner and hit.source_ref.object_type == kind)
        assert index.resolve_authoritative(hit.source_ref).state == "current"
        changed = hit.source_ref.model_copy(update={"content_digest": canonical_digest("changed")})
        assert index.resolve_authoritative(changed).state == "stale"
    get_settings.cache_clear()


def test_typed_temporal_edges_and_workspace_isolation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("JARVISOS_DATA_ROOT", str(tmp_path))
    get_settings.cache_clear()

    def record(owner: str, kind: str, object_id: str, workspace: str, **fields: str) -> IndexDocument:
        data = {"id": object_id, "created_at": "2026-01-01", **fields}
        return IndexDocument(source_ref=SourceRef(
            authority_owner=owner, object_type=kind, object_id=object_id, workspace_id=workspace,
            content_digest=canonical_digest(data),
        ), text=json.dumps(data, sort_keys=True))

    docs = [
        record("bluecad", "candidate", "candidate-1", "w1"),
        record("bluecad", "attempt", "attempt-1", "w1", candidate_id="candidate-1"),
        record("bluecad", "evidence_record", "evidence-1", "w1",
               candidate_id="candidate-1", attempt_id="attempt-1"),
        record("modeling", "parameter", "parameter-1", "w1"),
        record("modeling", "parameter", "parameter-2", "w1", supersedes_parameter_id="parameter-1"),
        record("ai_threads", "thread", "thread-1", "w1"),
        record("ai_threads", "interaction", "interaction-1", "w1"),
        record("bluecad", "candidate", "foreign", "w2"),
    ]
    docs[6] = docs[6].model_copy(update={"title": "thread-1"})
    index = SQLiteIndexStore(documents=lambda: docs, resolver=lambda ref: next(
        (doc for doc in docs if doc.source_ref == ref), None))
    index.rebuild()
    with open_retrieval_index_connection() as db:
        edges = {(row["kind"], row["valid_from"]) for row in db.execute("SELECT kind,valid_from FROM edges")}
        assert ("evidence_candidate", "2026-01-01") in edges
        assert ("evidence_attempt", "2026-01-01") in edges
        assert ("parameter_supersedes", "2026-01-01") in edges
        assert ("interaction_thread", "2026-01-01") in edges
        source = retrieval_index._key(docs[0].source_ref)
        target = retrieval_index._key(docs[-1].source_ref)
        db.execute("INSERT INTO edges VALUES (?,?,?,?)", (source, target, "knowledge_relation", None))
        db.commit()
    hits = index.expand_graph([docs[0].source_ref], depth=2, limit=50)
    assert all(hit.source_ref.workspace_id == "w1" for hit in hits)
    get_settings.cache_clear()
