"""Rebuild the disposable retrieval index from canonical owner reads."""
from __future__ import annotations

import argparse
import json
from itertools import chain
from pathlib import Path

from app.core.database import open_retrieval_index_connection
from app.modules.ai.retrieval_index import (
    INDEX_SCHEMA_VERSION,
    SQLiteIndexStore,
    canonical_documents,
    repository_symbol_documents,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Rebuild the disposable retrieval index")
    parser.add_argument("--repository-root", type=Path)
    parser.add_argument("--commit-sha")
    parser.add_argument("--path", action="append", default=[])
    args = parser.parse_args()
    if bool(args.repository_root) != bool(args.commit_sha) or (args.path and not args.commit_sha):
        parser.error("repository root and exact commit SHA are required together")
    symbols = repository_symbol_documents(args.repository_root, args.commit_sha, args.path) if args.commit_sha else []
    store = SQLiteIndexStore(documents=lambda: chain(canonical_documents(), symbols), repository_root=args.repository_root)
    revision = store.rebuild()
    with open_retrieval_index_connection() as db:
        count = int(db.execute("SELECT COUNT(*) FROM docs").fetchone()[0])
    print(json.dumps({"schema_version": INDEX_SCHEMA_VERSION, "revision": revision, "documents": count}, sort_keys=True))


if __name__ == "__main__":
    main()
