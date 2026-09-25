"""Disposable hybrid index. SQLite contents are candidates; canonical owners are reread for bundles."""
from __future__ import annotations

import ast
import hashlib
import json
import math
import re
import sqlite3
import struct
import subprocess
from collections.abc import Callable, Iterable, Sequence
from datetime import UTC, datetime, timedelta
from itertools import chain
from pathlib import Path
from typing import Protocol

from pydantic import BaseModel

try:
    import sqlite_vec
except ImportError:  # pragma: no cover - optional accelerator, absent in the backend venv
    sqlite_vec = None

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
from app.modules.ai.thread_service import get_thread, list_threads
from app.modules.bluecad.evidence import EvidenceRecord, get_evidence_record
from app.modules.bluecad.ledger import get_attempt, get_candidate, list_attempts, list_candidates
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

INDEX_SCHEMA_VERSION = "retrieval-index.v4"
_REPOSITORY_EXTRACTOR_ID = "repository-file-symbols.v1"
_SQLITE_VEC_CHUNK_SIZE = 8
_TOKEN = re.compile(r"\w+", re.UNICODE)
_HERMES_MEMORY_MAX_ENTRIES = 128
_HERMES_MEMORY_MAX_BYTES = 256_000
_HERMES_MEMORY_MAX_AGE = timedelta(days=365)
_HERMES_MEMORY_REDACTIONS = (
    re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]{8,}"),
    re.compile(r"\b(?:sk-[A-Za-z0-9_-]{12,}|gh[pousr]_[A-Za-z0-9_]{12,}|github_pat_[A-Za-z0-9_]{12,}|xox[baprs]-[A-Za-z0-9-]{12,})\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bAIza[0-9A-Za-z_-]{30,}\b|\bya29\.[0-9A-Za-z_-]{20,}\b"),
    re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b"),
    re.compile(r"(?i)(\b(?:api[_ -]?key|access[_ -]?token|client[_ -]?secret|password|passwd|secret|token)\b\s*[:=]\s*)([^\s,;]+)"),
    re.compile(r"(?i)(https?://[^:/\s]+:)([^@/\s]+)(@)"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----[\s\S]*?-----END (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
)


class Embedder(Protocol):
    def embed(self, text: str) -> tuple[float, ...]: ...

    def embed_query(self, text: str) -> tuple[float, ...]: ...


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

    def embed_query(self, text: str) -> tuple[float, ...]:
        # The hashing fixture has no document/query asymmetry.
        return self.embed(text)


class E5Embedder:
    """Optional sentence-transformers adapter; import occurs only on explicit construction."""

    def __init__(self, model_name: str = "intfloat/multilingual-e5-small") -> None:
        from sentence_transformers import SentenceTransformer

        self.model: object = SentenceTransformer(model_name)

    def embed(self, text: str) -> tuple[float, ...]:
        return self._encode("passage: " + text)

    def embed_query(self, text: str) -> tuple[float, ...]:
        # multilingual-e5 requires the "query: " prefix for queries and "passage: " for
        # documents; using "passage: " for both degrades asymmetric retrieval quality.
        return self._encode("query: " + text)

    def _encode(self, text: str) -> tuple[float, ...]:
        from typing import Any

        model: Any = self.model
        return tuple(float(value) for value in model.encode(text, normalize_embeddings=True))


def _key(ref: SourceRef) -> str:
    location = ref.location.model_dump(mode="json") if ref.location else None
    return canonical_digest((ref.authority_owner, ref.object_type, ref.object_id, ref.workspace_id, location))


def _model_document(kind: str, record: object, workspace_id: str) -> IndexDocument:
    assert isinstance(record, BaseModel)
    data = record.model_dump(mode="json")
    text = json.dumps(data, sort_keys=True, ensure_ascii=False)
    ref = SourceRef(
        authority_owner="modeling", object_type=kind, object_id=str(data["id"]),
        workspace_id=workspace_id, revision=str(data["updated_at"]), content_digest=canonical_digest(data),
    )
    return IndexDocument(source_ref=ref, text=text)


def _record_document(
    owner: str, kind: str, record: BaseModel, workspace_id: str, *, object_id: str | None = None,
    title: str | None = None,
) -> IndexDocument:
    data = record.model_dump(mode="json")
    revision = data.get("updated_at") or data.get("created_at")
    ref = SourceRef(
        authority_owner=owner, object_type=kind, object_id=object_id or str(data["id"]),
        workspace_id=workspace_id, revision=str(revision) if revision else None,
        content_digest=canonical_digest(data),
    )
    return IndexDocument(source_ref=ref, text=json.dumps(data, sort_keys=True, ensure_ascii=False), title=title)


def _snapshot_document(snapshot: BaseModel, workspace_id: str) -> IndexDocument:
    doc = _record_document("project_knowledge", "snapshot", snapshot, workspace_id)
    snapshot_ref = doc.source_ref.model_copy(update={"revision": doc.source_ref.object_id})
    return doc.model_copy(update={"source_ref": snapshot_ref})


def _evidence_document(record: EvidenceRecord, workspace_id: str) -> IndexDocument:
    # This base lacks engineering.evidence_contracts.evidence_record_ref.
    return _record_document("bluecad", "evidence_record", record, workspace_id)


def canonical_documents() -> Iterable[IndexDocument]:
    """Enumerate owner APIs; each document keeps the exact read projection's digest."""
    for workspace in sorted(list_workspaces(), key=lambda item: item.id):
        wid = workspace.id
        model_lists = (
            ("model_spec", list_model_specs(wid)), ("decision", list_decisions(wid)),
            ("assumption", list_assumptions(wid)), ("parameter", list_parameters(wid)),
            ("requirement", list_requirements(wid)),
        )
        for kind, records in model_lists:
            for record in records:
                yield _model_document(kind, record, wid)
        offset = 0
        while True:
            page = list_literature_sources(wid, offset=offset, limit=50)
            for source in page.items:
                yield _record_document("literature", "source", source, wid)
            offset += len(page.items)
            if not page.items or offset >= page.total:
                break
        for item in list_model_dossier_index(wid):
            for version in item.versions:
                dossier = get_model_dossier(wid, version.model_version_id)
                if dossier is None:
                    continue
                yield _record_document(
                    "modeling", "dossier", dossier, wid, object_id=version.model_version_id,
                )
        for thread in list_threads(workspace_id=wid, limit=50).threads:
            yield _record_document("ai_threads", "thread", thread, wid)
            detail = get_thread(workspace_id=wid, thread_id=thread.id, interaction_limit=100)
            for interaction in detail.interactions:
                yield _record_document("ai_threads", "interaction", interaction, wid, title=thread.id)
        for candidate in list_candidates(wid):
            yield _record_document("bluecad", "candidate", candidate, wid)
            for attempt in list_attempts(candidate.id):
                yield _record_document("bluecad", "attempt", attempt, wid)
        # The evidence selector requires a verdict filter; enumerate its owned table,
        # then obtain every typed record through the owner API.
        with open_sqlite_connection() as db:
            evidence_ids = [str(row[0]) for row in db.execute(
                "SELECT id FROM evidence_records WHERE workspace_id=? ORDER BY id", (wid,))]
            snapshot_ids = [str(row[0]) for row in db.execute(
                "SELECT id FROM project_knowledge_reconciled_snapshots WHERE workspace_id=? ORDER BY id", (wid,))]
        for evidence_id in evidence_ids:
            evidence_record = get_evidence_record(evidence_id)
            if evidence_record is not None and evidence_record.workspace_id == wid:
                yield _evidence_document(evidence_record, wid)
        for snapshot_id in snapshot_ids:
            snapshot = get_snapshot(wid, snapshot_id)
            doc = _snapshot_document(snapshot, wid)
            if len(doc.text) <= 200_000:
                yield doc


def _hermes_home() -> Path:
    from app.core.paths import build_paths

    return build_paths().data_root / "hermes"


def _redact_hermes_memory(text: str) -> str:
    for pattern in _HERMES_MEMORY_REDACTIONS:
        if pattern.groups:
            text = pattern.sub(lambda match: match.group(1) + "[REDACTED]" +
                               (match.group(3) if match.lastindex and match.lastindex >= 3 else ""), text)
        else:
            text = pattern.sub("[REDACTED]", text)
    return text


def _hermes_memory_file_documents(home: Path, *, now: datetime | None = None) -> list[IndexDocument]:
    """Read bounded Hermes built-in memories as operational context, never canonical state.

    Hermes 0.21.4 stores entries in memories/{MEMORY,USER}.md separated by ``\\n§\\n``.
    The separate state.db session/message store remains owned by Hermes session_search.
    """
    now = now or datetime.now(UTC)
    documents: list[IndexDocument] = []
    total_bytes = 0
    for filename, label in (("MEMORY.md", "agent notes"), ("USER.md", "user profile")):
        path = home / "memories" / filename
        try:
            stat = path.stat()
            modified = datetime.fromtimestamp(stat.st_mtime, UTC)
            remaining_bytes = _HERMES_MEMORY_MAX_BYTES - total_bytes
            if stat.st_size <= 0 or stat.st_size > remaining_bytes:
                continue
            if now - modified > _HERMES_MEMORY_MAX_AGE or modified > now + timedelta(minutes=5):
                continue
            with path.open("rb") as source:
                raw = source.read(remaining_bytes + 1)
        except (OSError, ValueError):
            continue
        if len(raw) != stat.st_size or total_bytes + len(raw) > _HERMES_MEMORY_MAX_BYTES:
            continue
        try:
            entries = [entry.strip() for entry in raw.decode("utf-8").split("\n§\n") if entry.strip()]
        except UnicodeDecodeError:
            continue
        total_bytes += len(raw)
        revision = str(stat.st_mtime_ns)
        for entry_index, entry in enumerate(entries):
            if len(documents) >= _HERMES_MEMORY_MAX_ENTRIES:
                return documents
            safe_entry = _redact_hermes_memory(entry)
            if not safe_entry.strip():
                continue
            text = ("OPERATIONAL MEMORY — Hermes built-in memory; non-canonical, may be outdated, "
                    "never authoritative JarvisOS state.\n"
                    f"Source: {label} ({filename})\n{safe_entry}")
            if len(text.encode("utf-8")) > _HERMES_MEMORY_MAX_BYTES:
                continue
            ref = SourceRef(
                authority_owner="hermes_operational_memory", object_type="memory_entry",
                object_id=f"{filename}:{entry_index}", revision=revision,
                content_digest=canonical_digest(text),
            )
            documents.append(IndexDocument(
                source_ref=ref, title=f"Operational memory · Hermes · {label} · non-canonical", text=text,
            ))
    return documents


def hermes_operational_memory_documents(home: Path | None = None) -> list[IndexDocument]:
    """Return bounded, redacted Hermes memory entries when the Hermes store exists."""
    return _hermes_memory_file_documents(home or _hermes_home())


def _resolve_hermes_operational_memory(ref: SourceRef) -> IndexDocument | None:
    if ref.object_type != "memory_entry":
        return None
    return next((doc for doc in hermes_operational_memory_documents()
                 if doc.source_ref.object_id == ref.object_id), None)


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


def repository_file_documents(repo: Path, sha: str, paths: Sequence[str]) -> list[IndexDocument]:
    documents: list[IndexDocument] = []
    for path in sorted(set(paths)):
        content = _git_show(repo, sha, path)
        if not content or len(content) > 200_000:
            continue
        ref = SourceRef(
            authority_owner="repository", object_type="file", object_id=path,
            revision=sha, content_digest=canonical_digest(content),
        )
        documents.append(IndexDocument(source_ref=ref, title=path, text=content))
    return documents


def _document_summary(doc: IndexDocument) -> IndexDocument:
    ref = doc.source_ref
    summary_ref = SourceRef(
        authority_owner="retrieval", object_type="document_summary", object_id=_key(ref),
        workspace_id=ref.workspace_id, content_digest=canonical_digest(ref.model_dump(mode="json")),
    )
    text = f"{ref.authority_owner} {ref.object_type} {ref.object_id}: {(doc.title or '')} {doc.text[:240]}"
    return IndexDocument(source_ref=summary_ref, title=doc.title, text=text[:200_000])


def _group_summary(docs: Sequence[IndexDocument], owner: str, workspace_id: str | None) -> IndexDocument:
    ordered = sorted(docs, key=lambda doc: _key(doc.source_ref))
    digest = canonical_digest([doc.source_ref.model_dump(mode="json") for doc in ordered])
    ref = SourceRef(
        authority_owner="retrieval", object_type="group_summary", object_id=owner,
        workspace_id=workspace_id, content_digest=digest,
    )
    names = ", ".join(doc.source_ref.object_id for doc in ordered[:12])
    return IndexDocument(source_ref=ref, title=owner, text=f"{owner}: {len(ordered)} records. {names}")


def _resolve_model(ref: SourceRef) -> IndexDocument | None:
    if ref.workspace_id is None:
        return None
    if ref.object_type == "model_spec":
        record = get_model_spec(ref.object_id)
        if record is None or record.workspace_id != ref.workspace_id:
            return None
        return _model_document(ref.object_type, record, ref.workspace_id)
    if ref.object_type == "dossier":
        dossier = get_model_dossier(ref.workspace_id, ref.object_id)
        return _record_document("modeling", "dossier", dossier, ref.workspace_id,
                                object_id=ref.object_id) if dossier else None
    record = get_context_record_exact(ref.workspace_id, ref.object_type, ref.object_id)
    return _model_document(ref.object_type, record, ref.workspace_id) if record else None


def _resolve_literature(ref: SourceRef) -> IndexDocument | None:
    if ref.workspace_id is None:
        return None
    try:
        record = get_literature_source(ref.workspace_id, ref.object_id)
    except ValueError:
        return None
    return _record_document("literature", "source", record, ref.workspace_id) if record else None


def _resolve_snapshot(ref: SourceRef) -> IndexDocument | None:
    if ref.workspace_id is None:
        return None
    try:
        return _snapshot_document(get_snapshot(ref.workspace_id, ref.object_id), ref.workspace_id)
    except ValueError:
        return None


def _resolve_evidence(ref: SourceRef) -> IndexDocument | None:
    if ref.workspace_id is None:
        return None
    record = get_evidence_record(ref.object_id)
    if record is None or record.workspace_id != ref.workspace_id:
        return None
    return _evidence_document(record, ref.workspace_id)


def _resolve_bluecad(ref: SourceRef) -> IndexDocument | None:
    if ref.workspace_id is None:
        return None
    if ref.object_type == "candidate":
        candidate = get_candidate(ref.workspace_id, ref.object_id)
        return _record_document("bluecad", "candidate", candidate, ref.workspace_id) if candidate else None
    attempt = get_attempt(ref.object_id)
    if attempt is None or get_candidate(ref.workspace_id, attempt.candidate_id) is None:
        return None
    return _record_document("bluecad", "attempt", attempt, ref.workspace_id)


def _resolve_thread(ref: SourceRef) -> IndexDocument | None:
    if ref.workspace_id is None:
        return None
    try:
        # The owner exposes paged thread reads; search its bounded list for this identity.
        for thread in list_threads(workspace_id=ref.workspace_id, limit=50).threads:
            if thread.id == ref.object_id and ref.object_type == "thread":
                return _record_document("ai_threads", "thread", thread, ref.workspace_id)
            if ref.object_type == "interaction":
                detail = get_thread(workspace_id=ref.workspace_id, thread_id=thread.id, interaction_limit=100)
                for interaction in detail.interactions:
                    if interaction.id == ref.object_id:
                        return _record_document("ai_threads", "interaction", interaction,
                                                ref.workspace_id, title=thread.id)
    except ValueError:
        return None
    return None


_OWNER_RESOLVERS: dict[tuple[str, str], Callable[[SourceRef], IndexDocument | None]] = {
    **{("modeling", kind): _resolve_model for kind in
       ("decision", "assumption", "parameter", "requirement", "model_spec", "dossier")},
    ("literature", "source"): _resolve_literature,
    ("project_knowledge", "snapshot"): _resolve_snapshot,
    ("bluecad", "evidence_record"): _resolve_evidence,
    ("bluecad", "candidate"): _resolve_bluecad,
    ("bluecad", "attempt"): _resolve_bluecad,
    ("ai_threads", "thread"): _resolve_thread,
    ("ai_threads", "interaction"): _resolve_thread,
    ("hermes_operational_memory", "memory_entry"): _resolve_hermes_operational_memory,
}


def _load_vector_extension(db: sqlite3.Connection) -> bool:
    """Load the optional sqlite-vec accelerator into this connection, when installed.

    SQLite extensions are per-connection, so every fresh connection that touches the
    vec0 virtual table must reload it; this is cheap and local (no network).
    """
    if sqlite_vec is None:
        return False
    db.enable_load_extension(True)
    sqlite_vec.load(db)
    db.enable_load_extension(False)
    return True


def _pack_vector(vector: Sequence[float]) -> bytes:
    return struct.pack(f"<{len(vector)}f", *vector)


class SQLiteIndexStore:
    def __init__(self, *, embedder: Embedder | None = None,
                 documents: Callable[[], Iterable[IndexDocument]] = lambda: chain(
                     canonical_documents(), hermes_operational_memory_documents()),
                 resolver: Callable[[SourceRef], IndexDocument | None] | None = None,
                 repository_root: Path | None = None) -> None:
        self.embedder = embedder or HashingEmbedder()
        self.documents = documents
        self.resolver = resolver
        self.repository_root = repository_root
        self.use_sqlite_vec = False
        self._vector_dimensions = 0
        self._initialize()

    def _initialize(self) -> None:
        with open_retrieval_index_connection() as db:
            use_vec = _load_vector_extension(db)
            db.execute("CREATE TABLE IF NOT EXISTS meta (name TEXT PRIMARY KEY, value TEXT NOT NULL)")
            version = db.execute("SELECT value FROM meta WHERE name='schema_version'").fetchone()
            if version and version[0] != INDEX_SCHEMA_VERSION:
                for table in ("edges", "docs_fts", "docs"):
                    db.execute(f"DROP TABLE IF EXISTS {table}")
                db.execute("DELETE FROM meta")
            db.execute("INSERT OR IGNORE INTO meta VALUES ('schema_version', ?)", (INDEX_SCHEMA_VERSION,))
            db.execute("INSERT OR IGNORE INTO meta VALUES ('extractor_identity', ?)",
                       (_REPOSITORY_EXTRACTOR_ID,))
            db.execute(
                "CREATE TABLE IF NOT EXISTS docs (key TEXT PRIMARY KEY, ref TEXT NOT NULL, "
                "object_id TEXT NOT NULL, title TEXT, text TEXT NOT NULL, vector TEXT NOT NULL, workspace_id TEXT)"
            )
            db.execute("CREATE INDEX IF NOT EXISTS docs_object_id ON docs(object_id,workspace_id)")
            db.execute("CREATE VIRTUAL TABLE IF NOT EXISTS docs_fts USING fts5(key UNINDEXED, object_id, title, text)")
            db.execute(
                "CREATE TABLE IF NOT EXISTS edges (source_key TEXT NOT NULL, target_key TEXT NOT NULL, "
                "kind TEXT NOT NULL, valid_from TEXT, PRIMARY KEY(source_key,target_key,kind))"
            )
            self.use_sqlite_vec = use_vec
            if use_vec:
                self._sync_vector_table(db)
            db.commit()

    def _sync_vector_table(self, db: sqlite3.Connection) -> None:
        """Keep the derived vec0 table consistent with ``docs.vector`` (the rebuildable source).

        The index may have been written by a process without sqlite-vec, or with another
        embedding dimension; any mismatch against the recorded state rebuilds vec_docs from
        the stored vectors, so the accelerator never serves stale neighbours.
        """
        self._vector_dimensions = len(self.embedder.embed(""))
        row = db.execute("SELECT value FROM meta WHERE name='revision'").fetchone()
        state = db.execute("SELECT value FROM meta WHERE name='vector_index'").fetchone()
        expected_state = f"{self._vector_dimensions}:{_SQLITE_VEC_CHUNK_SIZE}:{row[0] if row else ''}"
        if state and state[0] == expected_state:
            return
        db.execute("DROP TABLE IF EXISTS vec_docs")
        db.execute(
            "CREATE VIRTUAL TABLE vec_docs USING vec0(key TEXT PRIMARY KEY, workspace_id TEXT PARTITION KEY, "
            f"embedding FLOAT[{self._vector_dimensions}] distance_metric=cosine, "
            f"chunk_size={_SQLITE_VEC_CHUNK_SIZE})"
        )
        for key, workspace_id, vector_json in db.execute("SELECT key, workspace_id, vector FROM docs").fetchall():
            vector = json.loads(vector_json)
            if len(vector) == self._vector_dimensions:
                db.execute("INSERT INTO vec_docs(key, workspace_id, embedding) VALUES (?,?,?)",
                           (key, workspace_id, _pack_vector(vector)))
        db.execute("INSERT OR REPLACE INTO meta VALUES ('vector_index', ?)",
                   (expected_state,))

    def _revision(self, db: sqlite3.Connection) -> str:
        rows = [tuple(row) for row in db.execute("SELECT key,ref,object_id,title,text,vector FROM docs ORDER BY key")]
        edges = [
            tuple(row) for row in db.execute("SELECT source_key,target_key,kind,valid_from FROM edges ORDER BY 1,2,3")
        ]
        revision = canonical_digest({"documents": rows, "edges": edges})
        db.execute("INSERT OR REPLACE INTO meta VALUES ('revision', ?)", (revision,))
        if self.use_sqlite_vec:
            db.execute("INSERT OR REPLACE INTO meta VALUES ('vector_index', ?)",
                       (f"{self._vector_dimensions}:{_SQLITE_VEC_CHUNK_SIZE}:{revision}",))
        return revision

    @property
    def revision(self) -> str:
        with open_retrieval_index_connection() as db:
            row = db.execute("SELECT value FROM meta WHERE name='revision'").fetchone()
            return str(row[0]) if row else self._revision(db)

    def _upsert(self, db: sqlite3.Connection, documents: Sequence[IndexDocument]) -> None:
        if self.use_sqlite_vec:
            _load_vector_extension(db)
        for document in documents:
            ref = document.source_ref
            key = _key(ref)
            old = db.execute("SELECT ref,title,text FROM docs WHERE key=?", (key,)).fetchone()
            if old is not None and old[1] == document.title and old[2] == document.text:
                previous_ref = SourceRef.model_validate_json(old[0])
                if previous_ref.content_digest == ref.content_digest:
                    # A new commit changes the provenance revision, not the indexed body.
                    db.execute("UPDATE docs SET ref=? WHERE key=?", (ref.model_dump_json(), key))
                    continue
            vector = self.embedder.embed(document.text)
            db.execute("DELETE FROM docs_fts WHERE key=?", (key,))
            db.execute(
                "INSERT OR REPLACE INTO docs VALUES (?,?,?,?,?,?,?)",
                (key, ref.model_dump_json(), ref.object_id, document.title, document.text,
                 json.dumps(vector), ref.workspace_id),
            )
            db.execute(
                "INSERT INTO docs_fts(key,object_id,title,text) VALUES (?,?,?,?)",
                (key, ref.object_id, document.title or "", document.text),
            )
            if self.use_sqlite_vec:
                db.execute("DELETE FROM vec_docs WHERE key=?", (key,))
                db.execute(
                    "INSERT INTO vec_docs(key, workspace_id, embedding) VALUES (?,?,?)",
                    (key, ref.workspace_id, _pack_vector(vector)),
                )

    def rebuild(self) -> str:
        full_docs = sorted(self.documents(), key=lambda item: _key(item.source_ref))
        if self.repository_root:
            head = subprocess.run(["git", "-C", str(self.repository_root), "rev-parse", "HEAD"],
                                  capture_output=True, text=True, check=False, timeout=10)
            if head.returncode == 0:
                sha = head.stdout.strip()
                names = subprocess.run(["git", "-C", str(self.repository_root), "ls-tree", "-r",
                                        "--name-only", sha], capture_output=True, text=True,
                                       check=True, timeout=30).stdout.splitlines()
                full_docs.extend(repository_file_documents(self.repository_root, sha, names))
                full_docs.extend(repository_symbol_documents(self.repository_root, sha, names))
                full_docs = sorted({_key(doc.source_ref): doc for doc in full_docs}.values(),
                                   key=lambda item: _key(item.source_ref))
        summaries = {
            _key(doc.source_ref): _document_summary(doc) for doc in full_docs
            if doc.source_ref.authority_owner != "hermes_operational_memory"
        }
        groups: dict[tuple[str, str | None], list[IndexDocument]] = {}
        for doc in full_docs:
            ref = doc.source_ref
            groups.setdefault((ref.authority_owner, ref.workspace_id), []).append(doc)
        group_docs = [_group_summary(items, owner, wid) for (owner, wid), items in sorted(
            groups.items(), key=lambda pair: (pair[0][0], pair[0][1] or ""))]
        docs = sorted([*full_docs, *summaries.values(), *group_docs], key=lambda item: _key(item.source_ref))
        identities = {
            (ref.authority_owner, ref.object_type, ref.object_id, ref.workspace_id): _key(ref)
            for ref in (doc.source_ref for doc in docs)
        }

        def link(db: sqlite3.Connection, source: IndexDocument, owner: str, kind: str,
                 object_id: str | None, edge_kind: str, valid_from: str | None = None) -> None:
            if not object_id:
                return
            ref = source.source_ref
            target = identities.get((owner, kind, object_id, ref.workspace_id))
            if target is not None:
                db.execute("INSERT OR IGNORE INTO edges VALUES (?,?,?,?)",
                           (_key(ref), target, edge_kind, valid_from))

        with open_retrieval_index_connection() as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute("DELETE FROM edges")
            db.execute("DELETE FROM docs_fts")
            db.execute("DELETE FROM docs")
            if self.use_sqlite_vec:
                _load_vector_extension(db)
                db.execute("DELETE FROM vec_docs")
            self._upsert(db, docs)
            for doc in full_docs:
                summary = summaries.get(_key(doc.source_ref))
                if summary is not None:
                    db.execute("INSERT INTO edges VALUES (?,?,?,?)",
                               (_key(summary.source_ref), _key(doc.source_ref), "summary_document", None))
            for group in group_docs:
                for doc in groups[(group.source_ref.object_id, group.source_ref.workspace_id)]:
                    summary = summaries.get(_key(doc.source_ref))
                    if summary is not None:
                        db.execute("INSERT INTO edges VALUES (?,?,?,?)",
                                   (_key(group.source_ref), _key(summary.source_ref), "group_summary", None))
            for doc in full_docs:
                ref = doc.source_ref
                if ref.authority_owner in {"modeling", "bluecad", "ai_threads"}:
                    data = json.loads(doc.text)
                else:
                    data = {}
                since = data.get("created_at") or data.get("updated_at") or ref.revision
                if ref.object_type == "dossier":
                    link(db, doc, "modeling", "model_spec", data.get("identity", {}).get("model_spec_id"),
                         "dossier_model", since)
                elif ref.object_type == "evidence_record":
                    link(db, doc, "bluecad", "candidate", data.get("candidate_id"), "evidence_candidate", since)
                    link(db, doc, "bluecad", "attempt", data.get("attempt_id"), "evidence_attempt", since)
                elif ref.object_type == "parameter":
                    link(db, doc, "modeling", "parameter", data.get("supersedes_parameter_id"),
                         "parameter_supersedes", since)
                elif ref.object_type == "interaction":
                    link(db, doc, "ai_threads", "thread", doc.title, "interaction_thread", since)
                elif ref.object_type == "symbol":
                    link(db, doc, "repository", "file", ref.object_id.split("::", 1)[0],
                         "symbol_file", ref.revision)
            revision = self._revision(db)
            if self.repository_root:
                head = subprocess.run(["git", "-C", str(self.repository_root), "rev-parse", "HEAD"],
                                      capture_output=True, text=True, check=False, timeout=10)
                if head.returncode == 0:
                    db.execute("INSERT OR REPLACE INTO meta VALUES ('indexed_master_sha', ?)",
                               (head.stdout.strip(),))
            db.execute("INSERT OR REPLACE INTO meta VALUES ('embedder_identity', ?)",
                       (f"{type(self.embedder).__module__}.{type(self.embedder).__qualname__}:"
                        f"{len(self.embedder.embed(''))}",))
            db.commit()
            return revision

    @property
    def indexed_master_sha(self) -> str | None:
        with open_retrieval_index_connection() as db:
            row = db.execute("SELECT value FROM meta WHERE name='indexed_master_sha'").fetchone()
            return str(row[0]) if row else None

    def synchronize_repository(self, new_sha: str) -> dict[str, int | str]:
        """Apply one exact Git delta atomically; unchanged document vectors are retained."""
        if self.repository_root is None or not re.fullmatch(r"[0-9a-f]{40}", new_sha):
            raise ValueError("repository root and exact commit SHA are required")
        repo = self.repository_root
        check = subprocess.run(["git", "-C", str(repo), "cat-file", "-e", f"{new_sha}^{{commit}}"],
                               capture_output=True, check=False, timeout=10)
        if check.returncode:
            raise ValueError("target commit is unavailable")
        old_sha = self.indexed_master_sha
        if old_sha == new_sha:
            return {"indexed_sha": new_sha, "changed_paths": 0, "embedded_documents": 0}
        paths: set[str] = set()
        if old_sha:
            diff = subprocess.run(["git", "-C", str(repo), "diff", "--name-status", "-M", old_sha, new_sha],
                                  capture_output=True, text=True, check=True, timeout=30)
            rows = [line.split("\t") for line in diff.stdout.splitlines()]
            for row in rows:
                if row[0].startswith("R"):
                    paths.update(row[1:3])
                else:
                    paths.add(row[-1])
        else:
            listing = subprocess.run(["git", "-C", str(repo), "ls-tree", "-r", "--name-only", new_sha],
                                     capture_output=True, text=True, check=True, timeout=30)
            paths.update(listing.stdout.splitlines())
        source_docs = [*repository_file_documents(repo, new_sha, sorted(paths)),
                       *repository_symbol_documents(repo, new_sha, sorted(paths))]
        old_docs: list[SourceRef] = []
        with open_retrieval_index_connection() as db:
            for row in db.execute("SELECT ref FROM docs"):
                ref = SourceRef.model_validate_json(row[0])
                if ref.authority_owner == "repository":
                    path = ref.object_id.split("::", 1)[0]
                    if path in paths:
                        old_docs.append(ref)
        # Drop stale derived summaries for touched documents and regenerate only that
        # bounded set, then refresh the one repository group summary and symbol edges.
        summary_refs = [SourceRef(authority_owner="retrieval", object_type="document_summary",
                                  object_id=_key(ref), workspace_id=ref.workspace_id,
                                  content_digest=canonical_digest(ref.model_dump(mode="json")))
                        for ref in old_docs]
        old_docs.extend(summary_refs)
        target_keys = {_key(doc.source_ref) for doc in source_docs}
        deletes = [ref for ref in old_docs if _key(ref) not in target_keys]
        new_docs = [*source_docs, *(_document_summary(doc) for doc in source_docs)]
        with open_retrieval_index_connection() as db:
            repository_refs = [SourceRef.model_validate_json(row[0]) for row in db.execute("SELECT ref FROM docs")
                               if SourceRef.model_validate_json(row[0]).authority_owner == "repository"
                               and SourceRef.model_validate_json(row[0]).object_type in {"file", "symbol"}
                               and SourceRef.model_validate_json(row[0]).object_id.split("::", 1)[0] not in paths]
        repository_refs.extend(doc.source_ref for doc in source_docs)
        pseudo_docs = [IndexDocument(source_ref=ref, text=" ") for ref in repository_refs]
        new_docs.append(_group_summary(pseudo_docs, "repository", None))
        target_keys |= {_key(doc.source_ref) for doc in new_docs}
        deletes = [ref for ref in deletes if _key(ref) not in target_keys]
        with open_retrieval_index_connection() as db:
            db.execute("BEGIN IMMEDIATE")
            if self.use_sqlite_vec:
                _load_vector_extension(db)
            embedded_documents = 0
            for doc in new_docs:
                row = db.execute("SELECT ref,title,text FROM docs WHERE key=?", (_key(doc.source_ref),)).fetchone()
                if row is None or row[1] != doc.title or row[2] != doc.text or (
                        SourceRef.model_validate_json(row[0]).content_digest != doc.source_ref.content_digest):
                    embedded_documents += 1
            for ref in old_docs:
                if ref.authority_owner == "repository":
                    key = _key(ref)
                    db.execute("DELETE FROM edges WHERE source_key=? OR target_key=?", (key, key))
            for path in paths:
                db.execute("DELETE FROM edges WHERE kind='symbol_file' AND target_key IN "
                           "(SELECT key FROM docs WHERE object_id=?)", (path,))
            for ref in deletes:
                key = _key(ref)
                db.execute("DELETE FROM docs WHERE key=?", (key,))
                db.execute("DELETE FROM docs_fts WHERE key=?", (key,))
                db.execute("DELETE FROM edges WHERE source_key=? OR target_key=?", (key, key))
                if self.use_sqlite_vec:
                    db.execute("DELETE FROM vec_docs WHERE key=?", (key,))
            before = int(db.execute("SELECT COUNT(*) FROM docs").fetchone()[0])
            self._upsert(db, new_docs)
            for doc in source_docs:
                if doc.source_ref.object_type == "symbol":
                    file_ref = next((item.source_ref for item in source_docs
                                     if item.source_ref.object_type == "file"
                                     and item.source_ref.object_id == doc.source_ref.object_id.split("::", 1)[0]), None)
                    if file_ref:
                        db.execute("INSERT OR REPLACE INTO edges VALUES (?,?,?,?)",
                                   (_key(doc.source_ref), _key(file_ref), "symbol_file", new_sha))
            after = int(db.execute("SELECT COUNT(*) FROM docs").fetchone()[0])
            db.execute("INSERT OR REPLACE INTO meta VALUES ('indexed_master_sha', ?)", (new_sha,))
            db.execute("INSERT OR REPLACE INTO meta VALUES ('extractor_identity', ?)",
                       (_REPOSITORY_EXTRACTOR_ID,))
            db.execute("INSERT OR REPLACE INTO meta VALUES ('embedder_identity', ?)",
                       (f"{type(self.embedder).__module__}.{type(self.embedder).__qualname__}:"
                        f"{len(self.embedder.embed(''))}",))
            self._revision(db)
            db.commit()
        return {"indexed_sha": new_sha, "changed_paths": len(paths),
                "embedded_documents": embedded_documents, "deleted_documents": len(deletes),
                "document_count_delta": after - before}

    def ensure_repository_fresh(self, master_sha: str | None = None) -> None:
        """Catch up before a bundle is offered; failure propagates instead of serving stale hits."""
        if self.repository_root is None:
            return
        identity = (f"{type(self.embedder).__module__}.{type(self.embedder).__qualname__}:"
                    f"{len(self.embedder.embed(''))}")
        with open_retrieval_index_connection() as db:
            stored = db.execute("SELECT value FROM meta WHERE name='embedder_identity'").fetchone()
            extractor = db.execute("SELECT value FROM meta WHERE name='extractor_identity'").fetchone()
        if (stored and stored[0] != identity) or (extractor and extractor[0] != _REPOSITORY_EXTRACTOR_ID):
            self.rebuild()
            return
        if master_sha is None:
            result = subprocess.run(["git", "-C", str(self.repository_root), "rev-parse",
                                     "refs/remotes/origin/master"], capture_output=True, text=True,
                                    check=False, timeout=10)
            if result.returncode:
                result = subprocess.run(["git", "-C", str(self.repository_root), "rev-parse", "master"],
                                        capture_output=True, text=True, check=True, timeout=10)
            master_sha = result.stdout.strip()
        self.synchronize_repository(master_sha)

    def upsert(self, documents: Sequence[IndexDocument]) -> None:
        with open_retrieval_index_connection() as db:
            self._upsert(db, documents)
            self._revision(db)
            db.commit()

    def delete(self, refs: Sequence[SourceRef]) -> None:
        with open_retrieval_index_connection() as db:
            if self.use_sqlite_vec:
                _load_vector_extension(db)
            for ref in refs:
                key = _key(ref)
                stored = db.execute("SELECT ref FROM docs WHERE key=?", (key,)).fetchone()
                if stored is None or SourceRef.model_validate_json(stored[0]) != ref:
                    continue
                db.execute("DELETE FROM docs WHERE key=?", (key,))
                db.execute("DELETE FROM docs_fts WHERE key=?", (key,))
                if self.use_sqlite_vec:
                    db.execute("DELETE FROM vec_docs WHERE key=?", (key,))
                db.execute("DELETE FROM edges WHERE source_key=? OR target_key=?", (key, key))
                summary_key = _key(_document_summary(IndexDocument(source_ref=ref, text="deleted")).source_ref)
                db.execute("DELETE FROM docs WHERE key=?", (summary_key,))
                db.execute("DELETE FROM docs_fts WHERE key=?", (summary_key,))
                if self.use_sqlite_vec:
                    db.execute("DELETE FROM vec_docs WHERE key=?", (summary_key,))
                db.execute("DELETE FROM edges WHERE source_key=? OR target_key=?", (summary_key, summary_key))
                group_ref = SourceRef(
                    authority_owner="retrieval", object_type="group_summary",
                    object_id=ref.authority_owner, workspace_id=ref.workspace_id,
                    content_digest=canonical_digest([]),
                )
                group_key = _key(group_ref)
                db.execute("DELETE FROM docs WHERE key=?", (group_key,))
                db.execute("DELETE FROM docs_fts WHERE key=?", (group_key,))
                if self.use_sqlite_vec:
                    db.execute("DELETE FROM vec_docs WHERE key=?", (group_key,))
                db.execute("DELETE FROM edges WHERE source_key=? OR target_key=?", (group_key, group_key))
            self._revision(db)
            db.commit()

    def add_edge(self, source: SourceRef, target: SourceRef, kind: str,
                 valid_from: str | None = None) -> None:
        if kind not in {"dossier_model", "evidence_candidate", "knowledge_relation", "evidence_attempt",
                        "parameter_supersedes", "interaction_thread", "symbol_file"}:
            raise ValueError("unsupported edge kind")
        if source.workspace_id != target.workspace_id:
            raise ValueError("graph edges cannot cross workspace boundaries")
        with open_retrieval_index_connection() as db:
            db.execute("INSERT OR IGNORE INTO edges VALUES (?,?,?,?)",
                       (_key(source), _key(target), kind, valid_from))
            self._revision(db)
            db.commit()

    def _hit(self, row: sqlite3.Row, revision: str, *, lexical: float | None = None,
             vector: float | None = None, graph: float | None = None) -> RetrievalHit:
        return RetrievalHit(source_ref=SourceRef.model_validate_json(row["ref"]), lexical_score=lexical,
                            vector_score=vector, graph_score=graph, fused_score=0.0,
                            excerpt=row["text"][:500], index_revision=revision)

    def search_lexical(self, query: str, *, limit: int, workspace_id: str | None = None) -> list[RetrievalHit]:
        self.ensure_repository_fresh()
        if limit <= 0:
            return []
        with open_retrieval_index_connection() as db:
            revision = self.revision
            exact = db.execute(
                "SELECT * FROM docs WHERE object_id=? AND (? IS NULL OR workspace_id=?) ORDER BY key LIMIT ?",
                (query, workspace_id, workspace_id, limit),
            ).fetchall()
        if exact:
            return [self._hit(row, revision, lexical=-1000.0) for row in exact]
        if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", query):
            suffix = "::" + query
            with open_retrieval_index_connection() as db:
                symbols = db.execute(
                    "SELECT * FROM docs WHERE substr(object_id, -length(?))=? "
                    "AND (? IS NULL OR workspace_id=?) ORDER BY key LIMIT ?",
                    (suffix, suffix, workspace_id, workspace_id, limit),
                ).fetchall()
            if symbols:
                return [self._hit(row, revision, lexical=-900.0) for row in symbols]
        tokens = _TOKEN.findall(query)
        if not tokens:
            return []
        if query.strip().startswith('"') and query.strip().endswith('"'):
            expression = '"' + " ".join(tokens) + '"'
        else:
            expression = " AND ".join('"' + token + '"' for token in tokens)
        with open_retrieval_index_connection() as db:
            rows = db.execute(
                "SELECT d.*, bm25(docs_fts) AS score FROM docs_fts JOIN docs d ON d.key=docs_fts.key "
                "WHERE docs_fts MATCH ? AND (? IS NULL OR d.workspace_id=?) ORDER BY score, d.key LIMIT ?",
                (expression, workspace_id, workspace_id, limit),
            ).fetchall()
        return [self._hit(row, revision, lexical=float(row["score"])) for row in rows]

    def search_vector(self, query: str, *, limit: int, workspace_id: str | None = None) -> list[RetrievalHit]:
        self.ensure_repository_fresh()
        if limit <= 0:
            return []
        q = self.embedder.embed_query(query)
        with open_retrieval_index_connection() as db:
            if self.use_sqlite_vec:
                _load_vector_extension(db)
                q_bytes = _pack_vector(q)
                k = min(limit, 4096)  # vec0 KNN hard limit
                if workspace_id is None:
                    rows = db.execute(
                        "SELECT d.*, v.distance AS distance FROM vec_docs v JOIN docs d ON d.key = v.key "
                        "WHERE v.embedding MATCH ? AND v.k = ? ORDER BY v.distance, d.key",
                        (q_bytes, k),
                    ).fetchall()
                else:
                    rows = db.execute(
                        "SELECT d.*, v.distance AS distance FROM vec_docs v JOIN docs d ON d.key = v.key "
                        "WHERE v.embedding MATCH ? AND v.k = ? AND v.workspace_id = ? ORDER BY v.distance, d.key",
                        (q_bytes, k, workspace_id),
                    ).fetchall()
                scored = [(1.0 - float(row["distance"]), row) for row in rows]
            else:
                rows = db.execute(
                    "SELECT * FROM docs WHERE (? IS NULL OR workspace_id=?)", (workspace_id, workspace_id),
                ).fetchall()
                scored = [
                    (sum(a * b for a, b in zip(q, json.loads(row["vector"], parse_float=float), strict=True)), row)
                    for row in rows
                ]
        revision = self.revision
        scored.sort(key=lambda pair: (-pair[0], pair[1]["key"]))
        return [self._hit(row, revision, vector=score) for score, row in scored[:limit] if score > 0]

    def expand_graph(self, refs: Sequence[SourceRef], *, depth: int, limit: int) -> list[RetrievalHit]:
        if depth <= 0 or limit <= 0:
            return []
        seen = {_key(ref) for ref in refs}
        frontier = set(seen)
        found: list[RetrievalHit] = []
        revision = self.revision
        workspaces = {ref.workspace_id for ref in refs}
        if len(workspaces) > 1:
            raise ValueError("graph expansion requires one workspace")
        workspace_id = next(iter(workspaces), None)
        with open_retrieval_index_connection() as db:
            for level in range(1, min(depth, 8) + 1):
                following: set[str] = set()
                for key in sorted(frontier):
                    rows = db.execute(
                        "SELECT d.* FROM edges e JOIN docs d ON d.key=e.target_key WHERE e.source_key=? "
                        "AND d.workspace_id IS ? UNION SELECT d.* FROM edges e JOIN docs d ON d.key=e.source_key "
                        "WHERE e.target_key=? AND d.workspace_id IS ? ORDER BY key",
                        (key, workspace_id, key, workspace_id),
                    ).fetchall()
                    for row in rows:
                        neighbor = str(row["key"])
                        if neighbor not in seen:
                            seen.add(neighbor)
                            following.add(neighbor)
                            found.append(self._hit(row, revision, graph=1.0 / level))
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
        def ranked_score(key: str) -> float:
            # Hermes memory is useful operational context, but always ranks below canonical
            # JarvisOS and exact-revision repository sources when their retrieval evidence ties.
            factor = 0.2 if ranked[key].source_ref.authority_owner == "hermes_operational_memory" else 1.0
            return scores[key] * factor

        ordered = sorted(scores, key=lambda key: (-ranked_score(key), key))[:limit]
        return [ranked[key].model_copy(update={"fused_score": ranked_score(key)}) for key in ordered]

    def resolve_authoritative(self, ref: SourceRef) -> AuthoritativeResolution:
        doc: IndexDocument | None = None
        if ref.authority_owner == "retrieval" and ref.object_type == "document_summary":
            with open_retrieval_index_connection() as db:
                row = db.execute("SELECT ref FROM docs WHERE key=?", (ref.object_id,)).fetchone()
            if row is not None:
                source_ref = SourceRef.model_validate_json(row[0])
                source = self._resolve_document(source_ref)
                if source is not None:
                    doc = _document_summary(source)
        elif ref.authority_owner == "retrieval" and ref.object_type == "group_summary":
            # A group summary is an index navigation aid, not an authoritative record.
            # Resolving it by enumerating its whole owner can trigger unbounded rereads.
            return AuthoritativeResolution(ref=ref, state="unavailable")
        else:
            doc = self._resolve_document(ref)
        if doc is None:
            return AuthoritativeResolution(ref=ref, state="unavailable")
        current = doc.source_ref
        if (_key(current) != _key(ref) or current.revision != ref.revision
                or current.content_digest != ref.content_digest):
            return AuthoritativeResolution(
                ref=ref, state="stale", current_revision=current.revision,
                current_content_digest=current.content_digest,
            )
        return AuthoritativeResolution(
            ref=ref, state="current", current_revision=current.revision,
            current_content_digest=current.content_digest, content=doc.text,
        )

    def _resolve_document(self, ref: SourceRef) -> IndexDocument | None:
        if self.resolver is not None:
            doc = self.resolver(ref)
            return doc
        if ref.authority_owner == "repository" and self.repository_root and ref.revision:
            path = ref.object_id.split("::", 1)[0]
            documents = (repository_symbol_documents(self.repository_root, ref.revision, [path])
                         if ref.object_type == "symbol" else
                         repository_file_documents(self.repository_root, ref.revision, [path]))
            return next((item for item in documents if item.source_ref.object_id == ref.object_id), None)
        resolver = _OWNER_RESOLVERS.get((ref.authority_owner, ref.object_type))
        return resolver(ref) if resolver else None

    def build_bundle(self, query: str, *, workspace_id: str | None, token_budget: int,
                     expansion_level: int = 0, limit: int = 12) -> ContextBundle:
        self.ensure_repository_fresh()
        if token_budget < 0 or not 0 <= expansion_level <= 8 or limit < 0:
            raise ValueError("invalid bundle bounds")
        # Group summaries are index navigation aids, not evidence. Re-resolving one by
        # walking every canonical record in its owner can turn a small context request
        # into an unbounded repository reread (including reparsing every Python file).
        # Retrieve a wider candidate window, then fill the requested slots with
        # individually authoritative document summaries or source records.
        direct = [
            hit for hit in self.search_hybrid(query, limit=limit * 4, workspace_id=workspace_id)
            if not (hit.source_ref.authority_owner == "retrieval"
                    and hit.source_ref.object_type == "group_summary")
        ][:limit]
        candidates: list[tuple[RetrievalHit, int]] = []
        seen: set[str] = set()

        def include(hit: RetrievalHit, level: int) -> None:
            key = _key(hit.source_ref)
            if key not in seen:
                seen.add(key)
                candidates.append((hit, level))

        revision = self.revision
        with open_retrieval_index_connection() as db:
            for hit in direct:
                ref = hit.source_ref
                if ref.authority_owner == "hermes_operational_memory":
                    include(hit, 0)
                    continue
                if ref.authority_owner == "retrieval":
                    include(hit, 0)
                    continue
                rows = db.execute("SELECT * FROM docs WHERE object_id=?", (_key(ref),)).fetchall()
                row = next((item for item in rows if SourceRef.model_validate_json(item["ref"]).object_type
                            == "document_summary"), None)
                if row is not None:
                    include(self._hit(row, revision, graph=1.0), 0)
                if expansion_level >= 1:
                    include(hit, 1)
        if expansion_level >= 2 and direct and workspace_id is not None:
            refs = [hit.source_ref for hit in direct if hit.source_ref.workspace_id == workspace_id]
            for hit in self.expand_graph(refs, depth=expansion_level - 1, limit=limit):
                include(hit, min(expansion_level, 1 + round(1.0 / (hit.graph_score or 1.0))))
        items: list[ContextBundleItem] = []
        manifest: list[ContextManifestEntry] = []
        used = 0
        for hit, level in candidates[:256]:
            resolution = self.resolve_authoritative(hit.source_ref)
            if resolution.state != "current" or resolution.content is None or resolution.current_content_digest is None:
                if resolution.state == "stale":
                    manifest.append(ContextManifestEntry(source_ref=hit.source_ref, outcome="stale"))
                else:
                    manifest.append(ContextManifestEntry(source_ref=hit.source_ref, outcome="unavailable"))
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
