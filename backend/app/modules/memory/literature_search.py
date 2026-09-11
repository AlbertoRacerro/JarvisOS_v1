from __future__ import annotations

from app.core.database import open_sqlite_connection
from app.modules.memory.literature_models import LiteratureSourceRead
from app.modules.memory.literature_service import (
    MAX_ENTRIES_PER_SOURCE,
    MAX_LITERATURE_PAGE_SIZE,
    list_literature_sources,
)


class LiteratureSearchCapacityError(RuntimeError):
    pass


def _contains_literal(needle: str, value: object) -> bool:
    return isinstance(value, str) and needle in value.casefold()


def search_literature_sources(workspace_id: str, query: str) -> list[LiteratureSourceRead]:
    """Return bounded literal Literature candidates without duplicating owner state.

    Literature's existing read owner is intentionally page/entry bounded. Project
    Search must not silently present one bounded prefix as a complete workspace
    search, so datasets beyond those owner bounds fail closed until a separately
    accepted persistent search/index strategy exists.
    """
    page = list_literature_sources(workspace_id, offset=0, limit=MAX_LITERATURE_PAGE_SIZE)
    if page.next_offset is not None or page.total > MAX_LITERATURE_PAGE_SIZE:
        raise LiteratureSearchCapacityError("Literature search exceeds the bounded source scan capacity.")

    with open_sqlite_connection() as connection:
        overflowing_entry = connection.execute(
            """
            SELECT source_id
            FROM literature_entries
            WHERE workspace_id = ?
            GROUP BY source_id
            HAVING COUNT(*) > ?
            LIMIT 1
            """,
            (workspace_id, MAX_ENTRIES_PER_SOURCE),
        ).fetchone()
        if overflowing_entry is not None:
            raise LiteratureSearchCapacityError("Literature search exceeds the bounded entry scan capacity.")

    needle = query.casefold()
    matches: list[LiteratureSourceRead] = []
    for source in page.items:
        source_matches = any(
            _contains_literal(needle, value)
            for value in (source.title, source.citation, source.publisher)
        )
        matching_entries = [
            entry
            for entry in source.entries
            if any(
                _contains_literal(needle, value)
                for value in (
                    entry.statement,
                    entry.value_text,
                    None if entry.value_number is None else str(entry.value_number),
                    entry.unit,
                    entry.context_text,
                )
            )
        ]
        if source_matches or matching_entries:
            matches.append(source.model_copy(update={"entries": matching_entries}))
    return matches
