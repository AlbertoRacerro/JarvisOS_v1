"""Build, synchronize, verify, or repair the disposable retrieval index."""
from __future__ import annotations

import argparse
import json
import shutil
import sqlite3
import time
from datetime import UTC, datetime
from pathlib import Path

from app.core.database import open_retrieval_index_connection
from app.core.paths import build_paths
from app.modules.ai.retrieval_index import (
    INDEX_SCHEMA_VERSION,
    SQLiteIndexStore,
)


def _quarantine_index() -> Path:
    index_path = build_paths().retrieval_index_file
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    aside = index_path.with_name(f"{index_path.name}.corrupt-{stamp}")
    if index_path.exists():
        shutil.move(index_path, aside)
    for suffix in ("-wal", "-shm"):
        sidecar = Path(str(index_path) + suffix)
        if sidecar.exists():
            shutil.move(sidecar, Path(str(aside) + suffix))
    return aside


def main() -> None:
    parser = argparse.ArgumentParser(description="Maintain the disposable retrieval index")
    parser.add_argument("--repository-root", type=Path)
    parser.add_argument("--commit-sha", help="exact master target for a full build")
    parser.add_argument("--sync", action="store_true", help="catch up to configured current master")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--repair", action="store_true")
    args = parser.parse_args()
    if args.commit_sha and (not args.repository_root or args.sync):
        parser.error("--commit-sha requires --repository-root and cannot be combined with --sync")
    if args.sync and not args.repository_root:
        parser.error("--sync requires --repository-root")
    started = time.monotonic()
    if args.repair:
        try:
            store = SQLiteIndexStore(repository_root=args.repository_root)
            result: object = store.repair().model_dump(mode="json")
        except sqlite3.DatabaseError:
            _quarantine_index()
            store = SQLiteIndexStore(repository_root=args.repository_root)
            store.rebuild()
            result = store.verify().model_dump(mode="json")
    else:
        store = SQLiteIndexStore(repository_root=args.repository_root,
                                 master_ref=args.commit_sha or "refs/remotes/origin/master")
        if args.verify:
            result = store.verify().model_dump(mode="json")
        elif args.sync:
            target = store.resolve_master_sha()
            with open_retrieval_index_connection() as db:
                generation_before = int((db.execute("SELECT value FROM meta WHERE name='generation'").fetchone()
                                         or ["0"])[0])
            store.ensure_repository_fresh(target)
            with open_retrieval_index_connection() as db:
                generation_after = int((db.execute("SELECT value FROM meta WHERE name='generation'").fetchone()
                                        or ["0"])[0])
            indexed = store.indexed_master_sha
            if generation_after != generation_before:
                result = getattr(store, "_last_result", {})
            elif indexed == target:
                result = {"indexed_sha": target, "changed_paths": 0, "embedded_documents": 0,
                          "deleted_documents": 0}
            else:
                result = {"indexed_sha": indexed, "target_sha": target, "state": "behind",
                          "reason": f"repository index not at current master {target[:12]}"}
        else:
            revision = store.rebuild()
            result = {"revision": revision, **getattr(store, "_last_result", {})}
    with open_retrieval_index_connection() as db:
        count = int(db.execute("SELECT COUNT(*) FROM docs").fetchone()[0])
        generation = int((db.execute("SELECT value FROM meta WHERE name='generation'").fetchone() or ["0"])[0])
        indexed_sha = db.execute("SELECT value FROM meta WHERE name='indexed_master_sha'").fetchone()
    payload = {"schema_version": INDEX_SCHEMA_VERSION, "documents": count,
               "indexed_sha": str(indexed_sha[0]) if indexed_sha else None,
               "generation": generation, "changed_paths": 0, "embedded_documents": 0,
               "deleted_documents": 0, "elapsed_ms": round((time.monotonic() - started) * 1000),
               **(result if isinstance(result, dict) else {"result": result})}
    print(json.dumps(payload, sort_keys=True))


if __name__ == "__main__":
    main()
