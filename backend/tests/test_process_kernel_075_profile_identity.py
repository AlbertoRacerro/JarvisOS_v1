from __future__ import annotations

from app.modules.process_kernel import components, profile_047
from app.modules.process_kernel.components import ScreeningMassConstants
from app.modules.runner.process_kernel_047 import (
    expected_bundle_manifest,
    expected_bundle_manifest_bytes,
)


def test_process_profile_manifest_records_all_named_identities() -> None:
    manifest = expected_bundle_manifest()
    for name in (
        "contract_sha256",
        "semantic_unit_registry_sha256",
        "component_catalog_sha256",
        "screening_mass_constants_sha256",
        "flowsheet_profile_sha256",
        "profile_constants_sha256",
        "assembler_contract_sha256",
        "entrypoint_sha256",
    ):
        assert isinstance(manifest[name], str)
        assert len(manifest[name]) == 64
    assert expected_bundle_manifest_bytes() == expected_bundle_manifest_bytes()


def test_standard_gravity_changes_constant_and_flowsheet_identity(monkeypatch) -> None:
    baseline = expected_bundle_manifest()
    monkeypatch.setattr(profile_047, "STANDARD_GRAVITY", 9.8)
    changed = expected_bundle_manifest()

    assert changed["profile_constants_sha256"] != baseline["profile_constants_sha256"]
    assert changed["flowsheet_profile_sha256"] != baseline["flowsheet_profile_sha256"]
    assert changed["assembler_contract_sha256"] == baseline["assembler_contract_sha256"]
    assert changed["screening_mass_constants_sha256"] == baseline["screening_mass_constants_sha256"]


def test_assembler_identity_changes_assembler_and_flowsheet_identity(monkeypatch) -> None:
    baseline = expected_bundle_manifest()
    monkeypatch.setattr(profile_047, "ASSEMBLER_ID", "bluerev_geometry_hydraulics_047_exact_assembler_v2")
    changed = expected_bundle_manifest()

    assert changed["assembler_contract_sha256"] != baseline["assembler_contract_sha256"]
    assert changed["flowsheet_profile_sha256"] != baseline["flowsheet_profile_sha256"]
    assert changed["profile_constants_sha256"] == baseline["profile_constants_sha256"]


def test_048_constant_change_is_visible_separately_from_component_catalog(monkeypatch) -> None:
    baseline = expected_bundle_manifest()
    monkeypatch.setattr(
        components,
        "SCREENING_MASS_CONSTANTS_V0",
        ScreeningMassConstants(
            carbon_g_per_mol=12.0,
            oxygen_g_per_mol=16.0,
            carbon_dioxide_g_per_mol=45.0,
            carbon_dioxide_to_carbon_ratio=45.0 / 12.0,
            authority="test-only changed constants",
        ),
    )
    changed = expected_bundle_manifest()

    assert changed["screening_mass_constants_sha256"] != baseline["screening_mass_constants_sha256"]
    assert changed["component_catalog_sha256"] != baseline["component_catalog_sha256"]
    assert changed["flowsheet_profile_sha256"] == baseline["flowsheet_profile_sha256"]
