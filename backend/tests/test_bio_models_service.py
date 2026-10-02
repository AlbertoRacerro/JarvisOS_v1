from __future__ import annotations

from pathlib import Path

import pytest

from app.core.config import get_settings
from app.core.database import initialize_database, open_sqlite_connection
from app.modules.bio_models import service
from app.modules.bio_models.service import BioModelError
from app.modules.memory.literature_models import LiteratureEntryCreate, LiteratureSourceCreate
from app.modules.memory.literature_service import create_literature_entry, create_literature_source
from app.modules.workspaces.models import WorkspaceCreate
from app.modules.workspaces.service import create_workspace


@pytest.fixture
def workspace(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("JARVISOS_DATA_ROOT", str(tmp_path / "jarvis"))
    get_settings.cache_clear()
    initialize_database()
    return create_workspace(WorkspaceCreate(name="Bio models test", slug="bio-models-test", status="active"))


def make_numeric_basis(workspace_id: str, value: float = 0.08, unit: str = "1/hour") -> dict[str, str]:
    source = create_literature_source(workspace_id, LiteratureSourceCreate(title="Test source", source_kind="paper", citation="Fixture citation"))
    entry = create_literature_entry(workspace_id, source.id, LiteratureEntryCreate(entry_kind="datum", value_number=value,
        unit=unit, context_text="Specific growth rate"))
    return {"object_type": "literature_entry", "object_id": entry.id}


def test_sets_revision_cas_duplicate_edit_and_units(workspace) -> None:
    created = service.create_set(workspace.id, "Empty", "N. gaditana", "T1")
    first = service.edit_set_value(workspace.id, created["id"], "mu_max", {"value": 0.08, "unit": "1/hour", "expected_unit": "1/hour"}, created["revision"], created["digest"])
    assert first["revision"] != created["revision"]
    assert first["history"][-1]["parent_revision"] == created["revision"]
    assert first["values"]["mu_max"]["state"] == "candidate"
    assert first["values"]["mu_max"]["validity_range"] == "> 0"
    duplicate = service.duplicate_set(workspace.id, created["id"], first["revision"], first["digest"])
    assert duplicate["id"] != created["id"]
    assert duplicate["values"]["mu_max"]["state"] == "candidate"
    assert duplicate["values"]["mu_max"]["verification"] is None
    with pytest.raises(BioModelError) as duplicate_conflict:
        service.duplicate_set(workspace.id, created["id"], created["revision"], created["digest"])
    assert duplicate_conflict.value.status == 409
    with pytest.raises(BioModelError) as conflict:
        service.edit_set_value(workspace.id, created["id"], "mu_max", {"value": 1, "unit": "1/hour", "expected_unit": "1/hour"}, created["revision"], created["digest"])
    assert conflict.value.status == 409
    with pytest.raises(BioModelError, match="not compatible"):
        service.edit_set_value(workspace.id, created["id"], "mu_max", {"value": 1, "unit": "m", "expected_unit": "1/hour"}, first["revision"], first["digest"])


def test_verification_matching_mismatch_snapshot_and_review(workspace) -> None:
    basis = make_numeric_basis(workspace.id)
    created = service.create_set(workspace.id, "Empty")
    edited = service.edit_set_value(workspace.id, created["id"], "mu_max", {"value": 0.08, "unit": "1/hour", "expected_unit": "1/hour", "basis_ref": basis}, created["revision"], created["digest"])
    verified = service.verify_value(workspace.id, created["id"], "mu_max", edited["revision"], edited["digest"])
    value = verified["values"]["mu_max"]
    assert value["state"] == "source_verified"
    assert value["verification"]["snapshot_digest"]
    assert value["verification"]["no_backing_document"] is True
    reviewed = service.review_value(workspace.id, created["id"], "mu_max", "Reviewer A", "Compared with source section 2.", verified["revision"], verified["digest"])
    assert reviewed["values"]["mu_max"]["state"] == "expert_reviewed"
    assert not any("qualified" in str(event) for event in reviewed["history"])

    mismatch_set = service.create_set(workspace.id, "Mismatch")
    mismatch = service.edit_set_value(workspace.id, mismatch_set["id"], "mu_max", {"value": 0.2, "unit": "1/hour", "expected_unit": "1/hour", "basis_ref": basis}, mismatch_set["revision"], mismatch_set["digest"])
    with pytest.raises(BioModelError, match="entered 0.2 1/hour; source reports 0.08 1/hour") as refusal:
        service.verify_value(workspace.id, mismatch_set["id"], "mu_max", mismatch["revision"], mismatch["digest"])
    assert refusal.value.detail["entered"] == "0.2 1/hour"
    assert refusal.value.detail["source"] == "0.08 1/hour"


def test_zero_and_near_zero_matching_and_locator_confirmation(workspace) -> None:
    zero_basis = make_numeric_basis(workspace.id, 0.0)
    zero_set = service.create_set(workspace.id, "Zero")
    zero_edit = service.edit_set_value(workspace.id, zero_set["id"], "mu_max", {"value": 0.0, "unit": "1/hour", "expected_unit": "1/hour", "basis_ref": zero_basis}, zero_set["revision"], zero_set["digest"])
    assert service.verify_value(workspace.id, zero_set["id"], "mu_max", zero_edit["revision"], zero_edit["digest"])["values"]["mu_max"]["state"] == "source_verified"

    tiny_basis = make_numeric_basis(workspace.id, 1e-14)
    tiny = service.create_set(workspace.id, "Tiny")
    tiny_edit = service.edit_set_value(workspace.id, tiny["id"], "mu_max", {"value": 1.0001e-14, "unit": "1/hour", "expected_unit": "1/hour", "basis_ref": tiny_basis}, tiny["revision"], tiny["digest"])
    assert service.verify_value(workspace.id, tiny["id"], "mu_max", tiny_edit["revision"], tiny_edit["digest"])["values"]["mu_max"]["state"] == "source_verified"

    source = create_literature_source(workspace.id, LiteratureSourceCreate(title="Claim source", source_kind="book"))
    claim_set = service.create_set(workspace.id, "Claim")
    claim_edit = service.edit_set_value(workspace.id, claim_set["id"], "mu_max", {"value": 1, "unit": "1/hour", "expected_unit": "1/hour", "basis_ref": {"object_type": "literature_source", "object_id": source.id, "locator_kind": "section", "locator": "Table 3"}}, claim_set["revision"], claim_set["digest"])
    with pytest.raises(BioModelError, match="Confirm the shown locator: Table 3"):
        service.verify_value(workspace.id, claim_set["id"], "mu_max", claim_edit["revision"], claim_edit["digest"])
    assert service.verify_value(workspace.id, claim_set["id"], "mu_max", claim_edit["revision"], claim_edit["digest"], locator_confirmed=True)["values"]["mu_max"]["state"] == "source_verified"


def test_changed_snapshot_displays_stale_and_edit_resets_state(workspace) -> None:
    basis = make_numeric_basis(workspace.id)
    created = service.create_set(workspace.id, "Stale")
    edited = service.edit_set_value(workspace.id, created["id"], "mu_max", {"value": 0.08, "unit": "1/hour", "expected_unit": "1/hour", "basis_ref": basis}, created["revision"], created["digest"])
    verified = service.verify_value(workspace.id, created["id"], "mu_max", edited["revision"], edited["digest"])
    with open_sqlite_connection() as connection:
        connection.execute("UPDATE literature_sources SET title = ? WHERE workspace_id = ?", ("Changed metadata", workspace.id))
        connection.commit()
    stale = service.get_set(workspace.id, created["id"])
    assert stale["values"]["mu_max"]["state"] == "source_verified"
    assert stale["values"]["mu_max"]["display_state"] == "source_changed_since_verification"
    edited_again = service.edit_set_value(workspace.id, created["id"], "mu_max", {"value": 0.09, "unit": "1/hour", "expected_unit": "1/hour", "basis_ref": basis}, verified["revision"], verified["digest"])
    assert edited_again["values"]["mu_max"]["state"] == "candidate"
    assert edited_again["values"]["mu_max"]["verification"] is None


def test_expert_review_requires_source_verification(workspace) -> None:
    created = service.create_set(workspace.id, "Review")
    edited = service.edit_set_value(workspace.id, created["id"], "mu_max", {"value": 1, "unit": "1/hour", "expected_unit": "1/hour"}, created["revision"], created["digest"])
    with pytest.raises(BioModelError, match="source_verified"):
        service.review_value(workspace.id, created["id"], "mu_max", "Reviewer", "Note", edited["revision"], edited["digest"])


def test_no_shipping_parameter_values_and_card_refusal(workspace) -> None:
    assert service.list_forms()
    template = service.create_set(workspace.id, "N. gaditana T1 — empty", "N. gaditana")
    assert template["values"] == {}
    with pytest.raises(BioModelError, match="form"):
        service.create_card(workspace.id, "Invalid", template["id"], {"light": "invented.form"}, {"value": 0.1, "unit": "1/hour"})


def test_model_card_pins_parameter_revision_evaluates_and_requires_typed_inputs(workspace) -> None:
    current = service.create_set(workspace.id, "Growth parameters")
    parameters = {"K_I": (200.0, "umol/(m**2*s)"), "K_i": (900.0, "umol/(m**2*s)"),
                  "T_min": (285.0, "K"), "T_opt": (298.15, "K"), "T_max": (315.0, "K"),
                  "K_j": (0.02, "kg/m3"), "k_d": (0.003, "1/hour")}
    for symbol, (value, unit) in parameters.items():
        current = service.edit_set_value(workspace.id, current["id"], symbol,
            {"value": value, "unit": unit, "expected_unit": unit}, current["revision"], current["digest"])
    card = service.create_card(workspace.id, "PBR growth", current["id"],
        {"light": "light.haldane", "optics": "optics.slab_response_average", "temperature": "temperature.ctmi",
         "nutrients": ["nutrient.monod"], "combination": "combine.liebig", "loss": "loss.first_order",
         "stoichiometry": "stoich.photoautotrophic"}, {"value": 0.08, "unit": "1/hour"})
    assert card["parameter_set_revision"] == current["revision"]
    operating = {"I0": {"value": 800, "unit": "umol/(m**2*s)"}, "k_X": {"value": 120, "unit": "m**2/kg"},
                 "X": {"value": 0.7, "unit": "kg/m3"}, "L": {"value": 0.05, "unit": "m"},
                 "T": {"value": 298.15, "unit": "K"}, "S": {"value": 0.1, "unit": "kg/m3"}}
    output = service.evaluate_card(workspace.id, card["id"], operating)
    assert output["mu_net"]["unit"] == "h⁻¹"
    assert output["breakdown"]["light_average"]["value"] > 0
    assert output["breakdown"]["nutrients"]["value"] == pytest.approx(0.1 / 0.12)
    changed = service.edit_set_value(workspace.id, current["id"], "k_d", {"value": 0.1, "unit": "1/hour", "expected_unit": "1/hour"}, current["revision"], current["digest"])
    assert changed["revision"] != card["parameter_set_revision"]
    assert service.evaluate_card(workspace.id, card["id"], operating) == output
    with pytest.raises(BioModelError, match="value and unit"):
        service.evaluate_card(workspace.id, card["id"], {**operating, "T": 298.15})
    with pytest.raises(BioModelError, match="not compatible"):
        service.evaluate_card(workspace.id, card["id"], {**operating, "T": {"value": 298.15, "unit": "m"}})
