from __future__ import annotations

import hashlib
import re
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_REQUIRED_COLUMNS = {
    "content_object": {
        "content_id",
        "filename",
        "course_id",
        "role",
    },
    "document_segment": {
        "segment_id",
        "content_id",
        "page",
        "heading",
        "text",
        "text_sha256",
    },
}


class CorpusSnapshotError(RuntimeError):
    """Raised when a corpus snapshot cannot be trusted or queried safely."""


@dataclass(frozen=True)
class ReadOnlyFileBinding:
    path: Path
    sha256: str


def sha256_file(path: Path, *, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def bind_read_only_file(
    path: Path,
    *,
    allowed_root: Path,
    expected_sha256: str,
) -> ReadOnlyFileBinding:
    normalized_digest = expected_sha256.strip().lower()
    if not _SHA256_RE.fullmatch(normalized_digest):
        raise CorpusSnapshotError(
            "expected SHA-256 must be 64 lowercase hexadecimal characters"
        )

    try:
        root = allowed_root.expanduser().resolve(strict=True)
        resolved = path.expanduser().resolve(strict=True)
    except OSError as exc:
        raise CorpusSnapshotError("configured read-only file does not exist") from exc

    if not root.is_dir():
        raise CorpusSnapshotError("allowed root must be a directory")
    if not resolved.is_file():
        raise CorpusSnapshotError("configured read-only path must be a file")
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise CorpusSnapshotError(
            "configured read-only file is outside the allowed root"
        ) from exc

    actual_digest = sha256_file(resolved)
    if actual_digest != normalized_digest:
        raise CorpusSnapshotError(
            "configured read-only file SHA-256 does not match the expected snapshot"
        )
    return ReadOnlyFileBinding(path=resolved, sha256=actual_digest)


def _escape_like(value: str) -> str:
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _query_tokens(query: str) -> tuple[str, ...]:
    tokens = tuple(
        dict.fromkeys(
            re.findall(r"[^\W_]+(?:[-'][^\W_]+)*", query.lower(), flags=re.UNICODE)
        )
    )
    if not tokens:
        raise ValueError("query does not contain searchable tokens")
    return tokens


class ReadOnlyCorpusRepository:
    def __init__(
        self,
        database_path: Path,
        *,
        allowed_root: Path,
        expected_sha256: str,
    ) -> None:
        self._binding = bind_read_only_file(
            database_path,
            allowed_root=allowed_root,
            expected_sha256=expected_sha256,
        )
        self._validate_schema()

    @property
    def snapshot_sha256(self) -> str:
        return self._binding.sha256

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        uri = f"{self._binding.path.as_uri()}?mode=ro&immutable=1"
        connection = sqlite3.connect(uri, uri=True)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA query_only = ON")
        try:
            yield connection
        finally:
            connection.close()

    def _validate_schema(self) -> None:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
            existing_tables = {str(row["name"]) for row in rows}
            missing_tables = set(_REQUIRED_COLUMNS) - existing_tables
            if missing_tables:
                raise CorpusSnapshotError("corpus snapshot is missing required tables")
            for table, required_columns in _REQUIRED_COLUMNS.items():
                columns = {
                    str(row["name"])
                    for row in connection.execute(
                        f"PRAGMA table_info({table})"
                    ).fetchall()
                }
                if not required_columns.issubset(columns):
                    raise CorpusSnapshotError(
                        "corpus snapshot is missing required columns"
                    )

    def search_segments(
        self,
        *,
        query: str,
        course_ids: tuple[str, ...],
        roles: tuple[str, ...],
        excluded_roles: tuple[str, ...],
        limit: int,
    ) -> list[dict[str, object]]:
        tokens = _query_tokens(query)
        clauses: list[str] = []
        parameters: list[object] = []

        for token in tokens:
            pattern = f"%{_escape_like(token)}%"
            clauses.append(
                "(LOWER(ds.text) LIKE ? ESCAPE '\\' OR LOWER(COALESCE(ds.heading, '')) LIKE ? ESCAPE '\\')"
            )
            parameters.extend((pattern, pattern))

        if course_ids:
            placeholders = ", ".join("?" for _ in course_ids)
            clauses.append(f"LOWER(COALESCE(co.course_id, '')) IN ({placeholders})")
            parameters.extend(course_id.lower() for course_id in course_ids)
        if roles:
            placeholders = ", ".join("?" for _ in roles)
            clauses.append(f"LOWER(COALESCE(co.role, 'unknown')) IN ({placeholders})")
            parameters.extend(roles)
        if excluded_roles:
            placeholders = ", ".join("?" for _ in excluded_roles)
            clauses.append(
                f"LOWER(COALESCE(co.role, 'unknown')) NOT IN ({placeholders})"
            )
            parameters.extend(excluded_roles)

        phrase_pattern = f"%{_escape_like(query.lower())}%"
        parameters.extend((phrase_pattern, phrase_pattern, limit))
        where_sql = " AND ".join(clauses)
        sql = f"""
            SELECT
                ds.segment_id,
                ds.content_id,
                co.course_id,
                LOWER(COALESCE(co.role, 'unknown')) AS role,
                co.filename,
                ds.page,
                ds.heading,
                ds.text,
                ds.text_sha256
            FROM document_segment AS ds
            JOIN content_object AS co ON co.content_id = ds.content_id
            WHERE {where_sql}
            ORDER BY
                CASE
                    WHEN LOWER(ds.text) LIKE ? ESCAPE '\\'
                      OR LOWER(COALESCE(ds.heading, '')) LIKE ? ESCAPE '\\'
                    THEN 0 ELSE 1
                END,
                COALESCE(ds.page, 2147483647),
                ds.segment_id
            LIMIT ?
        """
        with self._connect() as connection:
            rows = connection.execute(sql, parameters).fetchall()
        return [dict(row) for row in rows]
