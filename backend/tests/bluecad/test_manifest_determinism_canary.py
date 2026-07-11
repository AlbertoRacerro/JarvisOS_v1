from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import pytest

from tests.bluecad.property_geometry_support import (
    artifact_hashes,
    build_twice_and_assert,
    canonical_canary_enabled,
    canonical_profile_metadata,
)

FIXTURE_ROOT = Path(__file__).parent / "fixtures"
EXPECTED_PATH = FIXTURE_ROOT / "property_geometry" / "expected.json"
FIXTURE_PATHS = (
    "minimal_single_tube.json",
    "chain_tube_bend_joint.json",
    "u_shape_two_bends.json",
    "property_geometry/minimal_float.json",
)
EXPECTED_SCHEMA_VERSION = "bluecad_property_geometry_expected_v0_1"
DIAGNOSTIC_ENV = "JARVISOS_BLUECAD_CANARY_ACTUAL"


def test_canonical_full_manifest_digest_canary() -> None:
    if not canonical_canary_enabled():
        pytest.skip(
            "full BLUECAD digest canary requires "
            "JARVISOS_BLUECAD_CANARY_PROFILE=ubuntu24-py311"
        )

    expected = json.loads(EXPECTED_PATH.read_text(encoding="utf-8"))
    assert expected["schema_version"] == EXPECTED_SCHEMA_VERSION
    actual_fixtures: list[dict[str, str]] = []
    diagnostics: dict[str, Any] = {"artifact_sha256": {}}

    for relative_path in FIXTURE_PATHS:
        spec_path = FIXTURE_ROOT / relative_path
        spec = json.loads(spec_path.read_text(encoding="utf-8"))
        first, second = build_twice_and_assert(spec)
        assert first.manifest is not None
        assert second.manifest is not None
        actual_fixtures.append(
            {
                "spec_path": relative_path,
                "spec_id": first.spec_id,
                "manifest_digest": first.manifest["manifest_digest"],
            }
        )
        diagnostics["artifact_sha256"][relative_path] = artifact_hashes(
            first.manifest
        )

    actual = {
        "schema_version": EXPECTED_SCHEMA_VERSION,
        "profile": canonical_profile_metadata(),
        "fixtures": actual_fixtures,
    }
    diagnostics["expected"] = expected
    diagnostics["actual"] = actual
    diagnostic_path = os.getenv(DIAGNOSTIC_ENV)
    if diagnostic_path:
        path = Path(diagnostic_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(diagnostics, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    assert actual == expected, json.dumps(diagnostics, indent=2, sort_keys=True)
