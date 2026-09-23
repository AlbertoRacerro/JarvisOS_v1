"""Disposable hybrid index. SQLite contents are candidates; canonical owners are reread for bundles."""
from __future__ import annotations

import ast
import hashlib
import json
import math
import re
import sqlite3
import subprocess
from collections.abc import Callable, Iterable, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol

from app.core.database import open_retrieval_index_connection, open_sqlite_connection
from app.modules.ai.context_builder import canonical_digest
from app.modules.ai.jarvis_context_models import SourceLocation, SourceRef
from app.modules.ai.retrieval_contracts import (
    AuthoritativeResolution,
    ContextBundle,
    ContextBundleItem,
    ContextManifestEntry,
    IndexDocument,
    RetrievalHit,
    context_bundle_digest,
)
from app.modules.memory.literature_service import get_literature_source, list_literature_sources
from app.modules.modeling.model_dossier import get_model_dossier, list_model_dossier_index
from app.modules.modeling.project_search_owner import get_context_record_exact
from app.modules.modeling.service import (
    get_model_spec,
    list_assumptions,
    list_decisions,
    list_model_specs,
    list_parameters,
    list_requirements,
)
from app.modules.project_knowledge.service import get_snapshot
from app.modules.workspaces.service import list_workspaces

INDEX_SCHEMA_VERSION = "retrieval-index.v2"
_TOKEN = re.compile(r"\w+", re.UNICODE)


class Embedder(Protocol):
    def embed(self, text: str) -> tuple[float, ...]: ...


class HashingEmbedder:
    """Offline, deterministic semantic-path fixture. Real embeddings are optional."""

    def __init__(self, dimensions: int = 128) -> None:
        if dimensions < 1:
            raise ValueError("dimensions must be positive")
        self.dimensions = dimensions

    def embed(self, text: str) -> tuple[float, ...]:
        values = [0.0] * self.dimensions
        for token in _TOKEN.findall(text.casefold()):
            digest = hashlib.sha256(token.encode()).digest()
            values[int.from_bytes(digest[:4], "big") % self.dimensions] += 1.0
        norm = math.sqrt(sum(value * value for value in values))
        return tuple(value / norm for value in values) if norm else tuple(values)


class E5Embedder:
    """Optional sentence-transformers adapter; import occurs only on explicit construction."""

    def __init__(self, model_name: str = "intfloat/multilingual-e5-small") -> None:
        from sentence_transformers import SentenceTransformer

        self.model: object = SentenceTransformer(model_name)

    def embed(self, text: str) -> tuple[float, ...]:
        from typing import Any

        model: Any = self.model
        return tuple(float(value) for value in model.encode("passage: " + text, normalize_embeddings=True))


def _key(ref: SourceRef) -> str:
    return canonical_digest((ref.authority_owner, ref.object_type, ref.object_id, ref.workspace_id, ref.location.model_dump(mode="json") if ref.location else None))


def _model_document(kind: str, record: object, workspace_id: str) -> IndexDocument:
    from pydantic import BaseModel

    assert isinstance(record, BaseModel)
    data = record.model_dump(mode="json")
    text = json.dumps(data, sort_keys=True, ensure_ascii=False)
    ref = SourceRef(authority_owner="modeling", object_type=kind, object_id=str(data["id"]), workspace_id=workspace_id,
                    revision=str(data["updated_at"]), content_digest=canonical_digest(data))
    return IndexDocument(source_ref=ref, text=text)


def canonical_documents() -> Iterable[IndexDocument]:
    """Enumerate owner APIs; each document keeps the exact read projection's digest."""
    for workspace in sorted(list_workspaces(), key=lambda item: item.id):
        wid = workspace.id
        for kind, records in (("model_spec", list_model_specs(wid)), ("decision", list_decisions(wid)), ("assumption", list_assumptions(wid)),
                              ("parameter", list_parameters(wid)), ("requirement", list_requirements(wid))):
            for record in records:
                yield _model_document(kind, record, wid)
        offset = 0
        while True:
            page = list_literature_sources(wid, offset=offset, limit=50)
            for source in page.items:
                data = source.model_dump(mode="json")
                yield IndexDocument(source_ref=SourceRef(authority_owner="literature", object_type="source",
                    object_id=source.id, workspace_id=wid, content_digest=canonical_digest(data)),
                    text=json.dumps(data, sort_keys=True, ensure_ascii=False))
            offset += len(page.items)
            if not page.items or offset >= page.total:
                break
        for item in list_model_dossier_index(wid):
            for version in item.versions:
                dossier = get_model_dossier(wid, version.model_version_id)
                if dossier is None:
                    continue
                data = dossier.model_dump(mode="json")
                yield IndexDocument(source_ref=SourceRef(authority_owner="modeling", object_type="dossier",
                    object_id=version.model_version_id, workspace_id=wid, content_digest=canonical_digest(data)),
                    text=json.dumps(data, sort_keys=True, ensure_ascii=False))
        with open_sqlite_connection() as db:
            snapshot_ids = [str(row[0]) for row in db.execute(
                "SELECT id FROM project_knowledge_reconciled_snapshots WHERE workspace_id=? ORDER BY id", (wid,))]
        for snapshot_id in snapshot_ids:
            snapshot = get_snapshot(wid, snapshot_id)
            data = snapshot.model_dump(mode="json")
            text = json.dumps(data, sort_keys=True, ensure_ascii=False)
            if len(text) <= 200_000:
                yield IndexDocument(source_ref=SourceRef(authority_owner="project_knowledge", object_type="snapshot",
                    object_id=snapshot_id, workspace_id=wid, revision=snapshot_id,
                    content_digest=canonical_digest(data)), text=text)


def _git_show(repo: Path, sha: str, path: str) -> str | None:
    if not re.fullmatch(r"[0-9a-f]{40}", sha) or Path(path).is_absolute() or ".." in Path(path).parts:
        raise ValueError("exact SHA and relative repository path required")
    result = subprocess.run(["git", "-C", str(repo), "show", f"{sha}:{path}"], capture_output=True,
                            text=True, check=False, timeout=10)
    return result.stdout if result.returncode == 0 else None


def repository_symbol_documents(repo: Path, sha: str, paths: Sequence[str]) -> list[IndexDocument]:
    """Index top-level Python definitions at an immutable commit."""
    documents: list[IndexDocument] = []
    for path in sorted(set(paths)):
        if not path.endswith(".py"):
            continue
        content = _git_show(repo, sha, path)
        if content is None:
            continue
        try:
            tree = ast.parse(content)
        except SyntaxError:
            continue
        lines = content.splitlines()
        for node in tree.body:
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                continue
            end = node.end_lineno or node.lineno
            snippet = "\n".join(lines[node.lineno - 1:end])
            ref = SourceRef(authority_owner="repository", object_type="symbol", object_id=f"{path}::{node.name}",
                            revision=sha, content_digest=canonical_digest(snippet),
                            location=SourceLocation(start_line=node.lineno, end_line=end))
            documents.append(IndexDocument(source_ref=ref, title=node.name, text=snippet[:200_000]))
    return documents


class SQLiteIndexStore:
    def __init__(self, *, embedder: Embedder | None = None,
                 documents: Callable[[], Iterable[IndexDocument]] = canonical_documents,
                 resolver: Callable[[SourceRef], IndexDocument | None] | None = None,
                 repository_root: Path | None = None) -> None:
        self.embedder = embedder or HashingEmbedder()
        self.documents = documents
        self.resolver = resolver
        self.repository_root = repository_root
        self._initialize()

    def _initialize(self) -> None:
        with open_retrieval_index_connection() as db:
            db.execute("CREATE TABLE IF NOT EXISTS meta (name TEXT PRIMARY KEY, value TEXT NOT NULL)")
            version = db.execute("SELECT value FROM meta WHERE name='schema_version'").fetchone()
            if version and version[0] != INDEX_SCHEMA_VERSION:
                raise ValueError("retrieval index schema changed; delete the disposable index and rebuild")
            db.execute("INSERT OR IGNORE INTO meta VALUES ('schema_version', ?)", (INDEX_SCHEMA_VERSION,))
            db.execute("CREATE TABLE IF NOT EXISTS docs (key TEXT PRIMARY KEY, ref TEXT NOT NULL, object_id TEXT NOT NULL, title TEXT, text TEXT NOT NULL, vector TEXT NOT NULL, workspace_id TEXT)")
            db.execute("CREATE INDEX IF NOT EXISTS docs_object_id ON docs(object_id,workspace_id)")
            db.execute("CREATE VIRTUAL TABLE IF NOT EXISTS docs_fts USING fts5(key UNINDEXED, object_id, title, text)")
            db.execute("CREATE TABLE IF NOT EXISTS edges (source_key TEXT NOT NULL, target_key TEXT NOT NULL, kind TEXT NOT NULL, PRIMARY KEY(source_key,target_key,kind))")
            db.commit()

    def _revision(self, db: sqlite3.Connection) -> str:
        rows = [tuple(row) for row in db.execute("SELECT key,ref,object_id,title,text,vector FROM docs ORDER BY key")]
        edges = [tuple(row) for row in db.execute("SELECT source_key,target_key,kind FROM edges ORDER BY 1,2,3")]
        revision = canonical_digest({"documents": rows, "edges": edges})
        db.execute("INSERT OR REPLACE INTO meta VALUES ('revision', ?)", (revision,))
        return revision

    @property
    def revision(self) -> str:
        with open_retrieval_index_connection() as db:
            row = db.execute("SELECT value FROM meta WHERE name='revision'").fetchone()
            return str(row[0]) if row else self._revision(db)

    def _upsert(self, db: sqlite3.Connection, documents: Sequence[IndexDocument]) -> None:
        for document in documents:
            ref = document.source_ref
            key = _key(ref)
            db.execute("DELETE FROM docs_fts WHERE key=?", (key,))
            db.execute("INSERT OR REPLACE INTO docs VALUES (?,?,?,?,?,?,?)", (key, ref.model_dump_json(), ref.object_id, document.title,
                       document.text, json.dumps(self.embedder.embed(document.text)), ref.workspace_id))
            db.execute("INSERT INTO docs_fts(key,object_id,title,text) VALUES (?,?,?,?)", (key, ref.object_id, document.title or "", document.text))

    def rebuild(self) -> str:
        docs = sorted(self.documents(), key=lambda item: _key(item.source_ref))
        with open_retrieval_index_connection() as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute("DELETE FROM edges")
            db.execute("DELETE FROM docs_fts")
            db.execute("DELETE FROM docs")
            self._upsert(db, docs)
            # Explicit, typed link: dossier version -> its model spec when both are indexed.
            for doc in docs:
                if doc.source_ref.object_type == "dossier":
                    data = json.loads(doc.text)
                    spec_id = data.get("identity", {}).get("model_spec_id")
                    if isinstance(spec_id, str):
                        target = SourceRef(authority_owner="modeling", object_type="model_spec", object_id=spec_id,
                                           workspace_id=doc.source_ref.workspace_id, revision="link")
                        db.execute("INSERT OR IGNORE INTO edges VALUES (?,?,?)", (_key(doc.source_ref), _key(target), "dossier_model"))
            revision = self._revision(db)
            db.commit()
            return revision

    def upsert(self, documents: Sequence[IndexDocument]) -> None:
        with open_retrieval_index_connection() as db:
            self._upsert(db, documents)
            self._revision(db)
            db.commit()

    def delete(self, refs: Sequence[SourceRef]) -> None:
        with open_retrieval_index_connection() as db:
            for ref in refs:
                key = _key(ref)
                stored = db.execute("SELECT ref FROM docs WHERE key=?", (key,)).fetchone()
                if stored is None or SourceRef.model_validate_json(stored[0]) != ref:
                    continue
                db.execute("DELETE FROM docs WHERE key=?", (key,))
                db.execute("DELETE FROM docs_fts WHERE key=?", (key,))
                db.execute("DELETE FROM edges WHERE source_key=? OR target_key=?", (key, key))
            self._revision(db)
            db.commit()

    def add_edge(self, source: SourceRef, target: SourceRef, kind: str) -> None:
        if kind not in {"dossier_model", "evidence_candidate", "knowledge_relation"}:
            raise ValueError("unsupported edge kind")
        if source.workspace_id != target.workspace_id:
            raise ValueError("graph edges cannot cross workspace boundaries")
        with open_retrieval_index_connection() as db:
            db.execute("INSERT OR IGNORE INTO edges VALUES (?,?,?)", (_key(source), _key(target), kind))
            self._revision(db)
            db.commit()

    def _hit(self, row: sqlite3.Row, *, lexical: float | None = None, vector: float | None = None,
             graph: float | None = None) -> RetrievalHit:
        return RetrievalHit(source_ref=SourceRef.model_validate_json(row["ref"]), lexical_score=lexical,
                            vector_score=vector, graph_score=graph, fused_score=0.0,
                            excerpt=row["text"][:500], index_revision=self.revision)

    def search_lexical(self, query: str, *, limit: int, workspace_id: str | None = None) -> list[RetrievalHit]:
        if limit <= 0:
            return []
        with open_retrieval_index_connection() as db:
            exact = db.execute("SELECT * FROM docs WHERE object_id=? AND (? IS NULL OR workspace_id=?) ORDER BY key LIMIT ?",
                               (query, workspace_id, workspace_id, limit)).fetchall()
        if exact:
            return [self._hit(row, lexical=-1000.0) for row in exact]
        tokens = _TOKEN.findall(query)
        if not tokens:
            return []
        expression = ('"' + " ".join(tokens) + '"') if query.strip().startswith('"') and query.strip().endswith('"') else " AND ".join('"' + token + '"' for token in tokens)
        with open_retrieval_index_connection() as db:
            rows = db.execute("SELECT d.*, bm25(docs_fts) AS score FROM docs_fts JOIN docs d ON d.key=docs_fts.key "
                              "WHERE docs_fts MATCH ? AND (? IS NULL OR d.workspace_id=?) ORDER BY score, d.key LIMIT ?",
                              (expression, workspace_id, workspace_id, limit)).fetchall()
        return [self._hit(row, lexical=float(row["score"])) for row in rows]

    def search_vector(self, query: str, *, limit: int, workspace_id: str | None = None) -> list[RetrievalHit]:
        if limit <= 0:
            return []
        q = self.embedder.embed(query)
        with open_retrieval_index_connection() as db:
            rows = db.execute("SELECT * FROM docs WHERE (? IS NULL OR workspace_id=?)", (workspace_id, workspace_id)).fetchall()
        scored = [(sum(a * b for a, b in zip(q, json.loads(row["vector"], parse_float=float), strict=True)), row) for row in rows]
        scored.sort(key=lambda pair: (-pair[0], pair[1]["key"]))
        return [self._hit(row, vector=score) for score, row in scored[:limit] if score > 0]

    def expand_graph(self, refs: Sequence[SourceRef], *, depth: int, limit: int) -> list[RetrievalHit]:
        if depth <= 0 or limit <= 0:
            return []
        seen = {_key(ref) for ref in refs}
        frontier = set(seen)
        found: list[RetrievalHit] = []
        with open_retrieval_index_connection() as db:
            for level in range(1, min(depth, 8) + 1):
                following: set[str] = set()
                for key in sorted(frontier):
                    rows = db.execute("SELECT d.* FROM edges e JOIN docs d ON d.key=e.target_key WHERE e.source_key=? "
                                      "UNION SELECT d.* FROM edges e JOIN docs d ON d.key=e.source_key WHERE e.target_key=? ORDER BY key",
                                      (key, key)).fetchall()
                    for row in rows:
                        neighbor = str(row["key"])
                        if neighbor not in seen:
                            seen.add(neighbor)
                            following.add(neighbor)
                            found.append(self._hit(row, graph=1.0 / level))
                            if len(found) >= limit:
                                return found
                frontier = following
                if not frontier:
                    break
        return found

    def search_hybrid(self, query: str, *, limit: int, workspace_id: str | None = None) -> list[RetrievalHit]:
        """Merge lexical and vector ranks with reciprocal-rank fusion (k=60)."""
        if limit <= 0:
            return []
        ranked: dict[str, RetrievalHit] = {}
        scores: dict[str, float] = {}
        for hits in (self.search_lexical(query, limit=limit, workspace_id=workspace_id),
                     self.search_vector(query, limit=limit, workspace_id=workspace_id)):
            for rank, hit in enumerate(hits, 1):
                key = _key(hit.source_ref)
                previous = ranked.get(key)
                ranked[key] = hit.model_copy(update={
                    "lexical_score": hit.lexical_score if hit.lexical_score is not None else
                    (previous.lexical_score if previous else None),
                    "vector_score": hit.vector_score if hit.vector_score is not None else
                    (previous.vector_score if previous else None),
                })
                scores[key] = scores.get(key, 0.0) + 1.0 / (60 + rank)
        ordered = sorted(scores, key=lambda key: (-scores[key], key))[:limit]
        return [ranked[key].model_copy(update={"fused_score": scores[key]}) for key in ordered]

    def resolve_authoritative(self, ref: SourceRef) -> AuthoritativeResolution:
        doc: IndexDocument | None = None
        if self.resolver is not None:
            doc = self.resolver(ref)
        elif ref.authority_owner == "modeling" and ref.workspace_id:
            if ref.object_type in {"decision", "assumption", "parameter", "requirement"}:
                record = get_context_record_exact(ref.workspace_id, ref.object_type, ref.object_id)
                if record is not None:
                    doc = _model_document(ref.object_type, record, ref.workspace_id)
            elif ref.object_type == "model_spec":
                record = get_model_spec(ref.object_id)
                if record is not None and record.workspace_id == ref.workspace_id:
                    doc = _model_document("model_spec", record, ref.workspace_id)
            elif ref.object_type == "dossier":
                dossier = get_model_dossier(ref.workspace_id, ref.object_id)
                if dossier is not None:
                    data = dossier.model_dump(mode="json")
                    doc = IndexDocument(source_ref=SourceRef(authority_owner="modeling", object_type="dossier",
                        object_id=ref.object_id, workspace_id=ref.workspace_id, content_digest=canonical_digest(data)),
                        text=json.dumps(data, sort_keys=True, ensure_ascii=False))
        elif ref.authority_owner == "literature" and ref.object_type == "source" and ref.workspace_id:
            try:
                source = get_literature_source(ref.workspace_id, ref.object_id)
            except ValueError:
                source = None
            if source is not None:
                data = source.model_dump(mode="json")
                doc = IndexDocument(source_ref=SourceRef(authority_owner="literature", object_type="source",
                    object_id=source.id, workspace_id=ref.workspace_id, content_digest=canonical_digest(data)),
                    text=json.dumps(data, sort_keys=True, ensure_ascii=False))
        elif ref.authority_owner == "project_knowledge" and ref.object_type == "snapshot" and ref.workspace_id:
            try:
                snapshot = get_snapshot(ref.workspace_id, ref.object_id)
            except ValueError:
                snapshot = None
            if snapshot is not None:
                data = snapshot.model_dump(mode="json")
                doc = IndexDocument(source_ref=SourceRef(authority_owner="project_knowledge", object_type="snapshot",
                    object_id=ref.object_id, workspace_id=ref.workspace_id, revision=ref.object_id,
                    content_digest=canonical_digest(data)), text=json.dumps(data, sort_keys=True, ensure_ascii=False))
        elif ref.authority_owner == "repository" and ref.object_type == "symbol" and self.repository_root and ref.revision:
            path = ref.object_id.split("::", 1)[0]
            doc = next((item for item in repository_symbol_documents(self.repository_root, ref.revision, [path])
                        if item.source_ref.object_id == ref.object_id), None)
        if doc is None:
            return AuthoritativeResolution(ref=ref, state="unavailable")
        current = doc.source_ref
        if _key(current) != _key(ref) or (ref.revision and current.revision != ref.revision) or (ref.content_digest and current.content_digest != ref.content_digest):
            return AuthoritativeResolution(ref=ref, state="stale", current_revision=current.revision,
                                           current_content_digest=current.content_digest)
        return AuthoritativeResolution(ref=ref, state="current", current_revision=current.revision,
                                       current_content_digest=current.content_digest, content=doc.text)

    def build_bundle(self, query: str, *, workspace_id: str | None, token_budget: int,
                     expansion_level: int = 0, limit: int = 32) -> ContextBundle:
        if token_budget < 0 or not 0 <= expansion_level <= 8 or limit < 0:
            raise ValueError("invalid bundle bounds")
        direct = self.search_hybrid(query, limit=limit, workspace_id=workspace_id)
        candidates = [(hit, 0) for hit in direct]
        if expansion_level:
            candidates.extend((hit, round(1.0 / (hit.graph_score or 1.0))) for hit in self.expand_graph([hit.source_ref for hit in direct], depth=expansion_level, limit=limit)
                              if workspace_id is None or hit.source_ref.workspace_id == workspace_id)
        items: list[ContextBundleItem] = []
        manifest: list[ContextManifestEntry] = []
        used = 0
        for hit, level in candidates[:256]:
            resolution = self.resolve_authoritative(hit.source_ref)
            if resolution.state != "current" or resolution.content is None or resolution.current_content_digest is None:
                manifest.append(ContextManifestEntry(source_ref=hit.source_ref, outcome="stale" if resolution.state == "stale" else "unavailable"))
                continue
            estimate = (len(resolution.content) + 3) // 4
            if used + estimate > token_budget or len(items) >= 64:
                manifest.append(ContextManifestEntry(source_ref=hit.source_ref, outcome="dropped_budget"))
                continue
            item = ContextBundleItem(source_ref=hit.source_ref, content_digest=resolution.current_content_digest,
                                     token_estimate=estimate, expansion_level=level)
            items.append(item)
            manifest.append(ContextManifestEntry(source_ref=hit.source_ref, outcome="included"))
            used += estimate
        return ContextBundle(bundle_id="bundle-" + canonical_digest((query, workspace_id, self.revision,
                             [item.model_dump(mode="json") for item in items]))[7:39], workspace_id=workspace_id,
                             items=tuple(items), evidence_manifest=tuple(manifest), token_estimate=used,
                             token_budget=token_budget, expansion_level=expansion_level, index_revision=self.revision,
                             bundle_digest=context_bundle_digest(items), created_at=datetime.now(UTC))
