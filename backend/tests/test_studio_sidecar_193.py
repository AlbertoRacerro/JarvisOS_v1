"""Spec 193: inert Studio proposals through the governed workspace-action owner."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core.bootstrap import initialize_storage
from app.core.database import open_sqlite_connection
from app.main import create_app
from app.modules.ai.thread_service import _turn_tools
from app.modules.workspace_actions import service
from app.modules.workspace_actions.models import ActionOrigin, ActionRequest, SurfaceRef


@pytest.fixture
def client():
    initialize_storage(seed_default=True)
    with TestClient(create_app()) as test_client:
        yield test_client


INPUT = {"name": "flow", "label": "Flow", "unit": "m**3/s", "description": "Volume flow"}
OUTPUT = {"name": "loss", "label": "Loss", "unit": "Pa", "description": "Pressure loss"}
SOURCE = "def main(inputs: dict) -> dict:\n    return {'loss': inputs['flow'] * 3}\n"


def action(category="calculation", source=SOURCE, **changes):
    value = {"op": "studio_draft", "mode": "create", "category": category,
             "name": "Pressure model", "engineering_question": "What is the pressure loss?",
             "contract": {"inputs": [INPUT], "outputs": [OUTPUT]}, "source": source,
             "assumptions": "Steady flow"}
    value.update(changes)
    return value


def submit(action_value, *, revision="new", draft_id=None, workspace="bluerev", interaction="turn-1",
           kind="local"):
    request = ActionRequest(surface="studio", base_revision=revision, draft_id=draft_id,
                            actions=[action_value])
    origin = ActionOrigin(kind=kind, thread_id="thread-193", interaction_id=interaction if kind == "local" else None,
                          relay_run_id=interaction if kind == "relay" else None)
    return service.submit(workspace, request, origin)


def test_create_is_inert_and_requires_explicit_apply(client, tmp_path):
    canary = tmp_path / "executed"
    source = (f"from pathlib import Path\nPath({str(canary)!r}).write_text('bad')\n"
              "def evaluate(x):\n    return x * 3\n" + SOURCE)
    brief = service.surface_brief("bluerev", SurfaceRef(route_id="design-studio"))
    assert brief.surface == "studio" and brief.base_revision == "new"
    proposed = submit(action(source=source))
    assert proposed.state == "proposed" and proposed.tier == "confirm"
    assert not canary.exists()
    assert next(line for line in proposed.changes if line.label == "Source").after == source
    assert client.get("/workspaces/bluerev/studio/models").json() == []
    applied = client.post(f"/workspaces/bluerev/actions/{proposed.action_id}/apply")
    assert applied.status_code == 200, applied.text
    model_id = applied.json()["draft_id"]
    model = client.get(f"/workspaces/bluerev/studio/models/{model_id}").json()
    assert model["source"] == source and model["status"] == "draft"
    assert model["last_test_report"] is None and model["versions"] == []
    assert not canary.exists()
    assert client.post(f"/workspaces/bluerev/actions/{proposed.action_id}/apply").status_code == 409
    with open_sqlite_connection() as connection:
        assert connection.execute("SELECT COUNT(*) FROM studio_drafts WHERE model_spec_id=?", (model_id,)).fetchone()[0] == 1


def test_update_cas_and_test_evidence_invalidation(client):
    created = submit(action(), interaction="create")
    applied = service.apply("bluerev", created.action_id)
    model_id = applied.draft_id
    assert model_id
    model = client.get(f"/workspaces/bluerev/studio/models/{model_id}").json()
    with open_sqlite_connection() as connection:
        connection.execute("UPDATE studio_drafts SET test_report_json=? WHERE model_spec_id=?",
                           ('{"passed":true,"source_sha256":"old","contract_sha256":"old","cases":[{}]}', model_id))
        connection.commit()
    selected = service.surface_brief("bluerev", SurfaceRef(route_id="design-studio", studio_model_id=model_id))
    assert selected.base_revision and selected.draft_id == model_id
    changed_source = SOURCE.replace("* 3", "* 4")
    update = action(source=changed_source, mode="update")
    proposed = submit(update, revision=selected.base_revision, draft_id=model_id, interaction="update")
    assert proposed.state == "proposed"
    source_diff = next(line for line in proposed.changes if line.label == "Source")
    assert source_diff.before == SOURCE and source_diff.after == changed_source
    assert service.apply("bluerev", proposed.action_id).state == "applied"
    changed = client.get(f"/workspaces/bluerev/studio/models/{model_id}").json()
    assert changed["source"] == changed_source and changed["last_test_report"] is None
    assert len(client.get("/workspaces/bluerev/studio/models").json()) == 1
    assert model["source_sha256"] != changed["source_sha256"]


def test_stale_foreign_and_relay_proposals_cannot_mutate(client):
    created = service.apply("bluerev", submit(action(), interaction="create").action_id)
    model_id = created.draft_id
    assert model_id
    selected = service.surface_brief("bluerev", SurfaceRef(route_id="design-studio", studio_model_id=model_id))
    update = action(mode="update", source=SOURCE.replace("* 3", "* 5"))
    relay = submit(update, revision=selected.base_revision, draft_id=model_id, interaction="relay-1", kind="relay")
    assert relay.state == "proposed"
    other = client.post("/workspaces", json={"name": "Other studio", "slug": "other-studio-193"})
    assert other.status_code == 201
    foreign = submit(update, revision=selected.base_revision, draft_id=model_id,
                     workspace=other.json()["id"], interaction="foreign")
    assert foreign.state in {"refused", "stale"}
    client.put(f"/workspaces/bluerev/studio/models/{model_id}", json={"source": SOURCE + "# operator edit\n"})
    assert client.post(f"/workspaces/bluerev/actions/{relay.action_id}/apply").status_code == 409
    assert client.get(f"/workspaces/bluerev/studio/models/{model_id}").json()["source"].endswith("# operator edit\n")


def test_invalid_contract_source_and_duplicate_local_turn(client):
    invalid = submit(action(source="def main(: pass"), interaction="syntax")
    assert invalid.state == "refused" and invalid.reason_code == "studio_source_invalid"
    invalid_unit = submit(action(**{"contract": {"inputs": [{**INPUT, "unit": "not_a_unit_xyz"}],
                                                  "outputs": [OUTPUT]}}), interaction="unit")
    assert invalid_unit.state == "refused"
    with pytest.raises(ValidationError):
        ActionRequest(surface="studio", base_revision="new", actions=[action(source="x" * 65537)])
    first = submit(action(), interaction="same-turn")
    duplicate = submit(action(), interaction="same-turn")
    assert duplicate.action_id == first.action_id
    assert client.get("/workspaces/bluerev/studio/models").json() == []


def test_documentation_preview_parses_without_execution(client, tmp_path):
    canary = Path(tmp_path / "preview-executed")
    source = (f"from pathlib import Path\nPath({str(canary)!r}).write_text('bad')\n"
              "def evaluate(x):\n    return x * 3\n" + SOURCE)
    result = client.post("/studio/documentation/preview", json={"source": source})
    assert result.status_code == 200 and result.json()["status"] == "ok"
    assert not canary.exists()
    assert client.post("/studio/documentation/preview", json={"source": "x" * 65537}).status_code == 422
    assert "mcp__jarvis__jarvis_studio_act" in _turn_tools("studio")
    assert "mcp__jarvis__jarvis_studio_act" not in _turn_tools("process")
