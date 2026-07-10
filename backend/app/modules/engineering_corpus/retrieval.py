from __future__ import annotations

from app.modules.engineering_corpus.models import (
    EngineeringCorpusSearchHit,
    EngineeringCorpusSearchRequest,
    EngineeringCorpusSearchResponse,
)
from app.modules.engineering_corpus.policy import resolve_role_policy
from app.modules.engineering_corpus.repository import ReadOnlyCorpusRepository


def _bounded_excerpt(text: str, query: str, max_chars: int) -> str:
    normalized = " ".join(text.split())
    if len(normalized) <= max_chars:
        return normalized

    query_tokens = [token.lower() for token in query.split() if token]
    lower_text = normalized.lower()
    positions = [lower_text.find(token) for token in query_tokens]
    positions = [position for position in positions if position >= 0]
    center = min(positions) if positions else 0
    start = max(0, center - max_chars // 3)
    end = min(len(normalized), start + max_chars)
    start = max(0, end - max_chars)
    excerpt = normalized[start:end]
    if start > 0:
        excerpt = f"…{excerpt[1:]}"
    if end < len(normalized):
        excerpt = f"{excerpt[:-1]}…"
    return excerpt


class EngineeringCorpusRetrievalService:
    def __init__(self, repository: ReadOnlyCorpusRepository) -> None:
        self._repository = repository

    def search(
        self, request: EngineeringCorpusSearchRequest
    ) -> EngineeringCorpusSearchResponse:
        policy = resolve_role_policy(
            requested_roles=request.roles,
            excluded_roles=request.exclude_roles,
            evaluation_mode=request.evaluation_mode,
        )
        rows = self._repository.search_segments(
            query=request.query,
            course_ids=tuple(
                sorted(
                    {
                        course_id.strip().lower()
                        for course_id in request.course_ids
                        if course_id.strip()
                    }
                )
            ),
            roles=policy.requested_roles,
            excluded_roles=policy.excluded_roles,
            limit=request.top_k,
        )
        hits = [
            EngineeringCorpusSearchHit(
                segment_id=str(row["segment_id"]),
                content_id=str(row["content_id"]),
                course_id=str(row["course_id"])
                if row["course_id"] is not None
                else None,
                role=str(row["role"]),
                filename=str(row["filename"]),
                page=int(row["page"]) if row["page"] is not None else None,
                heading=str(row["heading"]) if row["heading"] is not None else None,
                excerpt=_bounded_excerpt(
                    str(row["text"]), request.query, request.excerpt_chars
                ),
                text_sha256=str(row["text_sha256"]),
                source_ref=_source_ref(str(row["filename"]), row["page"]),
            )
            for row in rows
        ]
        return EngineeringCorpusSearchResponse(
            query=request.query,
            snapshot_sha256=self._repository.snapshot_sha256,
            evaluation_mode=request.evaluation_mode,
            effective_excluded_roles=list(policy.excluded_roles),
            hits=hits,
        )


def _source_ref(filename: str, page: object) -> str:
    if page is None:
        return filename
    return f"{filename}#page={int(page)}"
