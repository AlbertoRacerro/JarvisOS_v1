"""The sourced screening choices form a resolvable, unqualified 169 card."""

import importlib.util
from pathlib import Path

from app.core.database import initialize_database
from app.modules.bio_models import service
from app.modules.workspaces.models import WorkspaceCreate
from app.modules.workspaces.service import create_workspace


def test_assumed_c1_card_resolves_without_promoting_candidate_values():
    path = Path(__file__).resolve().parents[2] / "scripts/qualification/215/assumed_card.py"
    spec = importlib.util.spec_from_file_location("assumed_card_215", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    initialize_database()
    workspace = create_workspace(WorkspaceCreate(name="C1 assumed card test", slug="c1-assumed", status="active"))
    result = module.create_assumed_card(workspace.id)
    manifest = result["manifest"]
    card = result["card"]
    resolved = service.resolve_growth_model(workspace.id, card["id"], card["revision"], card["digest"])
    assert resolved["mu_max_h"] == 2.5 / 24
    assert resolved["card"]["n_source"] == "HNO3"
    assert set(resolved["candidate_symbols"]) == set(manifest["values"])
    assert all(row["source_doi"] and row["source_digest"] and row["conditions"]
               for row in manifest["values"].values())
    assert resolved["parameters"]["k_X"] == 200.0
    assert resolved["nitrogen_quota"] > 0
    assert resolved["oxygen_yield"] > 0
