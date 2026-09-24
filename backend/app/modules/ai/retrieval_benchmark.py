"""Deterministic offline retrieval smoke benchmark over fixtures and an exact Git commit."""
from __future__ import annotations

import json
import os
import statistics
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

from app.core.config import get_settings
from app.modules.ai.context_builder import canonical_digest
from app.modules.ai.jarvis_context_models import SourceRef
from app.modules.ai.retrieval_contracts import IndexDocument
from app.modules.ai.retrieval_index import (
    SQLiteIndexStore,
    repository_file_documents,
    repository_symbol_documents,
)

_SEEDED = (
    ("pump-sizing", "pump sizing pressure head decision engineering"),
    ("valve-cavitation", "valve cavitation margin assumption engineering"),
    ("mesh-quality", "mesh quality elements nodes evidence"),
    ("reactor-heat", "reactor heat transfer coefficient requirement"),
    ("budget-rule", "project budget zero paid provider policy"),
    ("run-provenance", "simulation run provenance solver version"),
    ("material-strength", "material strength yield stress parameter"),
    ("literature-citation", "literature citation source doi evidence"),
    ("thread-history", "thread interaction history assistant response"),
    ("snapshot-reconcile", "project snapshot reconcile validation digest"),
)


def _percentile(values: list[int], fraction: float) -> int:
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, int((len(ordered) - 1) * fraction + 0.5))]


def _run_case(label: str, docs: list[IndexDocument], cases: list[tuple[str, str]],
              repo: Path | None = None) -> dict[str, object]:
    store = SQLiteIndexStore(documents=lambda: docs, repository_root=repo,
                             resolver=(lambda ref: next((doc for doc in docs if doc.source_ref == ref), None))
                             if repo is None else None)
    revision = store.rebuild()
    recalls: list[bool] = []
    misses: list[str] = []
    estimates: list[int] = []
    expanded_estimates: list[int] = []
    for query, expected_id in cases:
        hits = store.search_hybrid(query, limit=10)
        found = any(hit.source_ref.object_id == expected_id for hit in hits)
        recalls.append(found)
        if not found:
            misses.append(expected_id)
        estimates.append(store.build_bundle(query, workspace_id=None, token_budget=4000).token_estimate)
        expanded_estimates.append(store.build_bundle(query, workspace_id=None, token_budget=4000,
                                                     expansion_level=1).token_estimate)
    return {
        "case": label, "documents": len(docs), "index_revision": revision,
        "queries": len(cases), "recall_at_10": f"{sum(recalls)}/{len(recalls)}",
        "misses": misses,
        "token_estimate_median": statistics.median(estimates),
        "token_estimate_p90": _percentile(estimates, 0.9), "token_estimates": estimates,
        "expanded_token_estimate_median": statistics.median(expanded_estimates),
        "expanded_token_estimate_p90": _percentile(expanded_estimates, 0.9),
        "expanded_token_estimates": expanded_estimates,
    }


def main() -> None:
    repo = Path(__file__).resolve().parents[4]
    sha = subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()
    tracked = subprocess.check_output(["git", "-C", str(repo), "ls-files"], text=True).splitlines()
    paths: list[str] = []
    for module in ("ai", "modeling", "bluecad", "project_knowledge"):
        module_paths = [path for path in tracked
                        if path.startswith(f"backend/app/modules/{module}/") and path.endswith(".py")]
        paths.extend(module_paths[:20])
    required = (
        "backend/app/modules/ai/execution.py",
        "backend/app/modules/ai/thread_service.py",
        "backend/app/modules/modeling/service.py",
        "backend/app/modules/bluecad/evidence.py",
        "backend/app/modules/project_knowledge/service.py",
    )
    docs = [path for path in tracked if path.startswith("docs/specs/") and path.endswith(".md")][:20]
    paths = sorted(set([*paths, *required, *docs]))
    repo_docs = repository_file_documents(repo, sha, paths) + repository_symbol_documents(repo, sha, paths)
    repo_cases = [
        ("run_ai_task", "backend/app/modules/ai/execution.py::run_ai_task"),
        ("get_thread", "backend/app/modules/ai/thread_service.py::get_thread"),
        ("create_decision", "backend/app/modules/modeling/service.py::create_decision"),
        ("get_evidence_record", "backend/app/modules/bluecad/evidence.py::get_evidence_record"),
        ("get_snapshot", "backend/app/modules/project_knowledge/service.py::get_snapshot"),
        *((path, path) for path in required),
    ]
    seeded_docs = [
        IndexDocument(source_ref=SourceRef(
            authority_owner="fixture", object_type="record", object_id=object_id,
            workspace_id="benchmark", content_digest=canonical_digest(content),
        ), text=content)
        for object_id, content in _SEEDED
    ]
    seeded_cases = [(content, object_id) for object_id, content in _SEEDED]
    with TemporaryDirectory() as temporary:
        os.environ["JARVISOS_DATA_ROOT"] = temporary
        get_settings.cache_clear()
        seeded_result = _run_case("seeded_workspace", seeded_docs, seeded_cases)
        repository_result = _run_case("repository_at_head", repo_docs, repo_cases, repo)
        get_settings.cache_clear()
    print(json.dumps({"sha": sha, "cases": [seeded_result, repository_result]}, sort_keys=True))


if __name__ == "__main__":
    main()
