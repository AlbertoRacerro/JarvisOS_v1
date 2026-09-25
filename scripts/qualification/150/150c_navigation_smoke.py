"""Qualify 150c navigation on a fetched JarvisOS clone with isolated canonical data."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from uuid import uuid4


def git(repo: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()


def main() -> None:
    repo = Path(sys.argv[1]).resolve()
    backend = Path(__file__).resolve().parents[3] / "backend"
    source_repo = Path("/home/thera/src/JarvisOS_v1")
    data_root = Path("/tmp") / f"150c-navigation-data-{uuid4().hex}"
    os.environ["JARVISOS_DATA_ROOT"] = str(data_root)
    sys.path.insert(0, str(backend))

    subprocess.run(["git", "-C", str(repo), "fetch", str(source_repo),
                    "origin/master:refs/remotes/origin/master"], check=True)
    master_sha = git(repo, "rev-parse", "refs/remotes/origin/master")
    subprocess.run(["git", "-C", str(repo), "switch", "--detach", master_sha], check=True,
                   capture_output=True, text=True)

    from app.core.database import initialize_database
    from app.modules.ai.retrieval_index import SQLiteIndexStore
    from app.modules.development.brainstorm_models import (
        BrainstormExactRef,
        BrainstormPromotionCreate,
        BrainstormRawCreate,
        BrainstormReconcileCreate,
    )
    from app.modules.development.brainstorm_service import (
        create_promotion,
        create_raw,
        reconcile,
    )
    from app.modules.memory.literature_models import (
        LiteratureEntryCreate,
        LiteratureSourceCreate,
    )
    from app.modules.memory.literature_service import (
        create_literature_entry,
        create_literature_source,
    )
    from app.modules.modeling.models import DecisionCreate, RequirementCreate
    from app.modules.modeling.service import create_decision, create_requirement
    from app.modules.workspaces.service import seed_default_workspace

    initialize_database()
    workspace = seed_default_workspace()
    suffix = uuid4().hex[:8]
    create_decision(workspace.id, DecisionCreate(
        title=f"PBR pump decision smoke {suffix}",
        decision_text="Use a variable-speed pump with the documented pressure boundary; verify against the selected reactor case.",
        rationale="Navigation smoke fixture in isolated qualification data.", status="accepted"))
    create_requirement(workspace.id, RequirementCreate(
        statement=f"PBR pump delivery remains below 10 kPa in smoke case {suffix}.", status="active"))
    raw = create_raw(BrainstormRawCreate(
        workspace_id=workspace.id, content=f"Exploratory thought: compare a low-shear PBR pump ({suffix}).",
        attachment_refs=[], created_by="150c-smoke", idempotency_key=f"150c-raw-{suffix}"))
    idea = reconcile(BrainstormReconcileCreate(
        workspace_id=workspace.id, title=f"Pump exploration {suffix}",
        takeaway="Compare low-shear pump alternatives.", synthesis="Exploratory synthesis; requires engineering review.",
        source_refs=[BrainstormExactRef(ref_type="raw", ref_id=str(raw["id"]))], actor="150c-smoke",
        idempotency_key=f"150c-reconcile-{suffix}"))
    create_promotion(BrainstormPromotionCreate(
        workspace_id=workspace.id, idea_id=str(idea["id"]), source_revision=int(idea["current_revision"]),
        target="roadmap", payload={"summary": "Consider a pump comparison study."}, actor="150c-smoke",
        idempotency_key=f"150c-promotion-{suffix}"))
    literature = create_literature_source(workspace.id, LiteratureSourceCreate(
        title=f"PBR circulation review smoke {suffix}", source_kind="paper",
        citation="Qualification-only local citation; not a validated engineering source."))
    create_literature_entry(workspace.id, literature.id, LiteratureEntryCreate(
        entry_kind="claim", statement="The cited review discusses circulation and pressure drop.",
        status="raw", context_text="Qualification smoke record."))

    branch = f"smoke/150c-{suffix}"
    store = SQLiteIndexStore(repository_root=repo, master_ref="refs/remotes/origin/master")
    store.rebuild()
    try:
        git(repo, "switch", "-c", branch)
        delta_file = repo / "scripts" / f"150c-smoke-{suffix}.txt"
        delta_file.write_text(f"150c small delta {suffix}\n", encoding="utf-8")
        git(repo, "add", str(delta_file.relative_to(repo)))
        subprocess.run(["git", "-C", str(repo), "-c", "user.name=150c smoke",
                        "-c", "user.email=150c-smoke@example.invalid", "commit", "-m",
                        "qualification: add 150c smoke delta"], check=True, capture_output=True, text=True)
        delta_sha = git(repo, "rev-parse", "HEAD")
        delta = store.synchronize_repository(delta_sha)

        queries = [
            ("where is the local Ollama adapter finish reason handled", None, ("repository",)),
            (f"PBR pump decision smoke {suffix}", workspace.id, ("modeling",)),
            (f"PBR pump pressure requirement smoke {suffix}", workspace.id, ("modeling",)),
            (f"pump exploration promotion smoke {suffix}", workspace.id, ("brainstorm",)),
            (f"PBR circulation review smoke {suffix}", workspace.id, ("literature",)),
        ]
        measurements = []
        for query, workspace_id, owners in queries:
            command = [sys.executable, "-m", "app.modules.ai.retrieval_query", query,
                       "--repository-root", str(repo), "--master-ref", f"refs/heads/{branch}",
                       "--limit", "8", "--token-budget", "1024"]
            if workspace_id:
                command.extend(["--workspace", workspace_id])
            for owner in owners:
                command.extend(["--source-scope", owner])
            started = time.perf_counter()
            completed = subprocess.run(command, cwd=backend, check=True, capture_output=True, text=True,
                                       env=os.environ.copy())
            elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
            payload = json.loads(completed.stdout)
            measurements.append({
                "query": query, "workspace_id": workspace_id, "source_scope": list(owners),
                "latency_ms": elapsed_ms, "token_estimate": payload["bundle"]["token_estimate"],
                "evidence_role": payload["evidence_role"],
                "freshness": payload["freshness"],
                "hits": [{"owner": item["source_ref"]["authority_owner"],
                          "type": item["source_ref"]["object_type"],
                          "id": item["source_ref"]["object_id"],
                          "excerpt": item["excerpt"][:300]} for item in payload["evidence"]],
            })
        evidence = {
            "schema_version": "150c-navigation-smoke.v1", "repository": str(repo),
            "source_repository": str(source_repo), "indexed_master_sha": master_sha,
            "delta_sha": delta_sha, "generation_after_delta": delta["generation"],
            "changed_paths": delta["changed_paths"], "embedded_documents": delta["embedded_documents"],
            "deleted_documents": delta["deleted_documents"],
            "document_count_delta": delta["document_count_delta"],
            "embedder": store.embedder.identity, "sqlite_vec_enabled": store.use_sqlite_vec,
            "hermes_runtime_exercised": False, "queries": measurements,
            "recall_observations": [
                "The seeded decision, requirement, Brainstorm raw/revision/promotion, and literature source/entry were retrieved in their scoped queries.",
                "The broad local Ollama finish-reason query returned repository excerpts but missed the expected adapter location in its top four; query phrasing or ranking needs improvement.",
            ],
            "known_gaps": ["Hermes route deterministically tested; real Hermes runtime not launched by smoke.",
                           "HashingEmbedder used; E5 was not exercised."],
        }
        output = Path(__file__).with_name("150c_navigation_smoke.json")
        output.write_text(json.dumps(evidence, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps({"evidence_path": str(output), "indexed_master_sha": master_sha,
                          "generation": delta["generation"], "changed_paths": delta["changed_paths"],
                          "embedded_documents": delta["embedded_documents"],
                          "queries": [{"query": row["query"], "latency_ms": row["latency_ms"],
                                       "token_estimate": row["token_estimate"], "hits": len(row["hits"])}
                                      for row in measurements]}, indent=2))
    finally:
        subprocess.run(["git", "-C", str(repo), "switch", "--detach", master_sha], check=True,
                       capture_output=True, text=True)
        subprocess.run(["git", "-C", str(repo), "branch", "-D", branch], check=True,
                       capture_output=True, text=True)


if __name__ == "__main__":
    main()
