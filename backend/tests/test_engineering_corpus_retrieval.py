from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path

import pytest

from app.modules.engineering_corpus.models import EngineeringCorpusSearchRequest
from app.modules.engineering_corpus.policy import CorpusPolicyError
from app.modules.engineering_corpus.repository import (
    CorpusSnapshotError,
    ReadOnlyCorpusRepository,
)
from app.modules.engineering_corpus.retrieval import EngineeringCorpusRetrievalService


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _build_snapshot(path: Path) -> None:
    connection = sqlite3.connect(path)
    connection.executescript(
        """
        CREATE TABLE content_object (
            content_id TEXT PRIMARY KEY,
            filename TEXT NOT NULL,
            course_id TEXT,
            role TEXT NOT NULL
        );
        CREATE TABLE document_segment (
            segment_id TEXT PRIMARY KEY,
            content_id TEXT NOT NULL,
            page INTEGER,
            heading TEXT,
            text TEXT NOT NULL,
            text_sha256 TEXT NOT NULL
        );
        """
    )
    rows = [
        ("c1", "bioprocess.pdf", "bioprocess", "lecture_reference"),
        ("c2", "bioprocess-solutions.pdf", "bioprocess", "solution"),
        ("c3", "gold.jsonl", "bioprocess", "private_gold"),
    ]
    connection.executemany("INSERT INTO content_object VALUES (?, ?, ?, ?)", rows)
    segments = [
        (
            "s1",
            "c1",
            24,
            "Oxygen transfer",
            "OTR equals kLa times the oxygen driving force. OUR is oxygen uptake rate.",
            "1" * 64,
        ),
        (
            "s2",
            "c2",
            25,
            "Solved oxygen transfer",
            "OTR and OUR solved answer equals 24.",
            "2" * 64,
        ),
        ("s3", "c3", 1, "Evaluator", "OTR OUR hidden expected answer.", "3" * 64),
    ]
    connection.executemany(
        "INSERT INTO document_segment VALUES (?, ?, ?, ?, ?, ?)", segments
    )
    connection.commit()
    connection.close()


def test_read_only_retrieval_returns_bounded_provenance_and_excludes_private_roles(
    tmp_path: Path,
) -> None:
    snapshot = tmp_path / "corpus.sqlite3"
    _build_snapshot(snapshot)
    repository = ReadOnlyCorpusRepository(
        snapshot, allowed_root=tmp_path, expected_sha256=_sha256(snapshot)
    )
    service = EngineeringCorpusRetrievalService(repository)

    response = service.search(
        EngineeringCorpusSearchRequest(
            query="OTR OUR",
            course_ids=["bioprocess"],
            roles=["lecture_reference"],
            excerpt_chars=200,
        )
    )

    assert [hit.segment_id for hit in response.hits] == ["s1"]
    assert response.hits[0].source_ref == "bioprocess.pdf#page=24"
    assert len(response.hits[0].excerpt) <= 200
    assert "private_gold" in response.effective_excluded_roles


def test_evaluation_mode_forces_solution_exclusion(tmp_path: Path) -> None:
    snapshot = tmp_path / "corpus.sqlite3"
    _build_snapshot(snapshot)
    repository = ReadOnlyCorpusRepository(
        snapshot, allowed_root=tmp_path, expected_sha256=_sha256(snapshot)
    )
    service = EngineeringCorpusRetrievalService(repository)

    response = service.search(
        EngineeringCorpusSearchRequest(query="OTR OUR", evaluation_mode=True)
    )

    assert [hit.segment_id for hit in response.hits] == ["s1"]
    assert "solution" in response.effective_excluded_roles


def test_requesting_forbidden_role_fails_closed(tmp_path: Path) -> None:
    snapshot = tmp_path / "corpus.sqlite3"
    _build_snapshot(snapshot)
    repository = ReadOnlyCorpusRepository(
        snapshot, allowed_root=tmp_path, expected_sha256=_sha256(snapshot)
    )
    service = EngineeringCorpusRetrievalService(repository)

    with pytest.raises(CorpusPolicyError):
        service.search(
            EngineeringCorpusSearchRequest(query="OTR", roles=["private_gold"])
        )
    with pytest.raises(CorpusPolicyError):
        service.search(
            EngineeringCorpusSearchRequest(
                query="OTR", roles=["solution"], evaluation_mode=True
            )
        )


def test_snapshot_binding_rejects_hash_mismatch_and_outside_root(
    tmp_path: Path,
) -> None:
    root = tmp_path / "root"
    root.mkdir()
    outside = tmp_path / "outside.sqlite3"
    _build_snapshot(outside)

    with pytest.raises(CorpusSnapshotError):
        ReadOnlyCorpusRepository(
            outside, allowed_root=root, expected_sha256=_sha256(outside)
        )

    inside = root / "inside.sqlite3"
    _build_snapshot(inside)
    with pytest.raises(CorpusSnapshotError):
        ReadOnlyCorpusRepository(inside, allowed_root=root, expected_sha256="0" * 64)


def test_repository_connection_is_query_only(tmp_path: Path) -> None:
    snapshot = tmp_path / "corpus.sqlite3"
    _build_snapshot(snapshot)
    repository = ReadOnlyCorpusRepository(
        snapshot, allowed_root=tmp_path, expected_sha256=_sha256(snapshot)
    )

    with repository._connect() as connection:  # noqa: SLF001 - verifies the boundary contract directly
        with pytest.raises(sqlite3.OperationalError):
            connection.execute("DELETE FROM document_segment")
