from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(path: str, old: str, new: str) -> None:
    target = ROOT / path
    text = target.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{path}: expected one replacement, found {count}")
    target.write_text(text.replace(old, new, 1), encoding="utf-8")


CODE = "backend/app/modules/bluecad/evidence_egress.py"
TEST = "backend/tests/bluecad/test_evidence_egress.py"

replace_once(
    CODE,
    '''from app.modules.ai.egress_authority import (
    sanitize_canonical_sources_with_local_model,
    sanitize_prompt_with_local_model,
)
''',
    '''from app.modules.ai.egress_authority import (
    _sanitizer_config_digest,
    sanitize_canonical_sources_with_local_model,
    sanitize_prompt_with_local_model,
)
''',
)
replace_once(
    CODE,
    '''from app.modules.ai.egress_service import canonical_json, sha256_text
''',
    '''from app.modules.ai.egress_service import canonical_json, sha256_text
from app.modules.ai.provider_registry import load_default_provider_registry
''',
)
replace_once(
    CODE,
    '''    ordered_source_refs: tuple[str, ...]
    sight_digest: str
''',
    '''    ordered_source_refs: tuple[str, ...]
    source_effective_levels: tuple[str, ...]
    sight_digest: str
''',
)
replace_once(
    CODE,
    '''            "ordered_source_refs": list(self.ordered_source_refs),
            "sight_digest": self.sight_digest,
''',
    '''            "ordered_source_refs": list(self.ordered_source_refs),
            "source_effective_levels": list(self.source_effective_levels),
            "sight_digest": self.sight_digest,
''',
)
replace_once(
    CODE,
    '''        ordered_source_refs=snapshot["ordered_source_refs"],
        sight_digest=snapshot["sight"].digest,
''',
    '''        ordered_source_refs=snapshot["ordered_source_refs"],
        source_effective_levels=snapshot["effective_levels"],
        sight_digest=snapshot["sight"].digest,
''',
)
replace_once(
    CODE,
    '''        or derivative.sanitizer_kind != "model_local"
    ):
''',
    '''        or derivative.sanitizer_kind != "model_local"
        or derivative.sanitizer_version != _STRUCTURAL_SANITIZER_VERSION
        or derivative.sanitizer_config_digest
        != _expected_structural_prompt_config_digest()
    ):
''',
)
replace_once(
    CODE,
    '''def _validate_transformed_prompt_content(
''',
    '''def _expected_structural_prompt_config_digest() -> str:
    policy = load_default_egress_policy()
    registry = load_default_provider_registry()
    return _sanitizer_config_digest(
        policy=policy,
        route_class="local:fast",
        template=_STRUCTURAL_SANITIZER_TEMPLATE,
        version=_STRUCTURAL_SANITIZER_VERSION,
        registry=registry,
    )


def _validate_transformed_prompt_content(
''',
)
replace_once(
    CODE,
    '''        or _contains_structural_json_value(content, json.loads(forbidden_spec_json))
''',
    '''        or _contains_json_structure(content)
''',
)
replace_once(
    CODE,
    '''def _contains_structural_json_value(content: str, forbidden_value: Any) -> bool:
    decoder = json.JSONDecoder()
    for index, character in enumerate(content):
        if character not in "[{":
            continue
        try:
            value, _ = decoder.raw_decode(content[index:])
        except json.JSONDecodeError:
            continue
        if _json_value_contains(value, forbidden_value):
            return True
    return False


def _json_value_contains(value: Any, forbidden_value: Any) -> bool:
    if value == forbidden_value:
        return True
    if isinstance(value, dict):
        return any(_json_value_contains(item, forbidden_value) for item in value.values())
    if isinstance(value, list):
        return any(_json_value_contains(item, forbidden_value) for item in value)
    return False
''',
    '''def _contains_json_structure(content: str) -> bool:
    decoder = json.JSONDecoder()
    for index, character in enumerate(content):
        if character not in "[{":
            continue
        try:
            value, _ = decoder.raw_decode(content[index:])
        except json.JSONDecodeError:
            continue
        if isinstance(value, (dict, list)):
            return True
    return False
''',
)
replace_once(
    CODE,
    '''def _validate_current_lineage_sight(lineage: dict[str, Any]) -> None:
    current = _current_lineage_authority_snapshot(lineage)
    sight = current["sight"]
    derivative = current["derivative"]
    current_refs = current["source_refs"]
    source_digests = current["source_digests"]
    effective_levels = current["effective_levels"]
    expected_refs = tuple(lineage["ordered_source_refs"])
    stored_refs = tuple(json.loads(derivative["source_refs_json"]))
    stored_digests = json.loads(derivative["source_digests_json"])
    current_level = (
        max(effective_levels, key={"S0": 0, "S1": 1, "S2": 2, "S3": 3, "S4": 4}.__getitem__)
        if effective_levels
        else "S0"
    )
    if (
        sight.digest != lineage["sight_digest"]
        or current_refs != expected_refs
        or stored_refs != expected_refs
        or source_digests != stored_digests
        or current_level != derivative["effective_level"]
        or current_level != lineage["effective_level"]
        or derivative["content_digest"] != lineage["derivative_digest"]
    ):
        raise sensitivity.SensitivityPolicyError(
            "Evidence sight, labels, or derivative authority changed before packet authorization."
        )
''',
    '''def _validate_current_lineage_sight(lineage: dict[str, Any]) -> None:
    current = _current_lineage_authority_snapshot(lineage)
    sight = current["sight"]
    derivative = current["derivative"]
    current_refs = current["source_refs"]
    source_digests = current["source_digests"]
    effective_levels = current["effective_levels"]
    expected_refs = tuple(lineage["ordered_source_refs"])
    expected_levels = tuple(lineage["source_effective_levels"])
    stored_refs = tuple(json.loads(derivative["source_refs_json"]))
    stored_digests = json.loads(derivative["source_digests_json"])
    if (
        sight.digest != lineage["sight_digest"]
        or current_refs != expected_refs
        or stored_refs != expected_refs
        or source_digests != stored_digests
        or effective_levels != expected_levels
        or derivative["effective_level"] != lineage["effective_level"]
        or derivative["content_digest"] != lineage["derivative_digest"]
        or derivative["sanitizer_kind"] != lineage["sanitizer_kind"]
        or derivative["sanitizer_version"] != lineage["sanitizer_version"]
        or derivative["sanitizer_config_digest"]
        != lineage["sanitizer_config_digest"]
    ):
        raise sensitivity.SensitivityPolicyError(
            "Evidence sight, labels, or derivative authority changed before packet authorization."
        )
''',
)
replace_once(
    CODE,
    '''    if lineage.get("max_lines") != EVIDENCE_SIGHT_MAX_LINES or lineage.get(
''',
    '''    levels = lineage.get("source_effective_levels")
    if (
        not isinstance(levels, list)
        or len(levels) != len(refs)
        or any(level not in {"S0", "S1", "S2", "S3", "S4"} for level in levels)
    ):
        raise sensitivity.SensitivityPolicyError(
            "Evidence lineage source effective levels are malformed."
        )
    if lineage.get("max_lines") != EVIDENCE_SIGHT_MAX_LINES or lineage.get(
''',
)

replace_once(
    TEST,
    '''        "ordered_source_refs": ["evidence:e1"],
        "sight_digest": "sha256:" + "1" * 64,
''',
    '''        "ordered_source_refs": ["evidence:e1"],
        "source_effective_levels": ["S1"],
        "sight_digest": "sha256:" + "1" * 64,
''',
)
replace_once(
    TEST,
    '''            "effective_level": "S1",
            "content_digest": "sha256:" + "2" * 64,
''',
    '''            "effective_level": "S1",
            "content_digest": "sha256:" + "2" * 64,
            "sanitizer_kind": "deterministic",
            "sanitizer_version": "bluecad_evidence_sight_derivative_v0_1",
            "sanitizer_config_digest": "3" * 64,
''',
)
replace_once(
    TEST,
    '''def test_lineage_mutation_changes_packet_digest() -> None:
''',
    '''def test_packet_authorization_accepts_bound_sensitive_source_after_sanitization(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    lineage = _lineage()
    lineage.update(
        source_effective_levels=["S2"],
        sanitizer_kind="model_local",
        sanitizer_version="canonical-local-sanitizer-v1",
        sanitizer_config_digest="6" * 64,
    )
    snapshot = _matching_authority_snapshot(effective_level="S2")
    snapshot["derivative"].update(
        sanitizer_kind="model_local",
        sanitizer_version="canonical-local-sanitizer-v1",
        sanitizer_config_digest="6" * 64,
    )
    monkeypatch.setattr(
        evidence_egress_module,
        "_current_structural_prompt_derivative",
        lambda _lineage: _matching_prompt_derivative(),
    )
    monkeypatch.setattr(
        evidence_egress_module,
        "_current_lineage_authority_snapshot",
        lambda _lineage: snapshot,
    )

    with bind_evidence_lineage(lineage):
        enriched = enrich_authorized_evidence_manifest(_manifest())
    assert enriched[0]["evidence_lineage"]["source_effective_levels"] == ["S2"]


def test_lineage_mutation_changes_packet_digest() -> None:
''',
)
replace_once(
    TEST,
    '''        'Generic repair\n{"payload":{"schema_version":"geometry_spec_v0_1"}}',
''',
    '''        'Generic repair\n{"payload":{"schema_version":"geometry_spec_v0_1"}}',
        'Generic repair\n{"objects":[{"id":"tube-1","diameter":0.4}]}',
''',
)
replace_once(
    TEST,
    '''def test_bluecad_prompt_sanitizer_binds_template_and_version(
''',
    '''@pytest.mark.parametrize(
    ("sanitizer_version", "sanitizer_config_digest"),
    (
        ("prompt-local-sanitizer-v1", "e" * 64),
        ("bluecad_structural_abstraction_v0_1", "f" * 64),
    ),
)
def test_prompt_reuse_requires_exact_bluecad_sanitizer_identity(
    monkeypatch: pytest.MonkeyPatch,
    sanitizer_version: str,
    sanitizer_config_digest: str,
) -> None:
    existing = SimpleNamespace(
        id="prompt-generic",
        status="approved",
        workspace_id=WORKSPACE_ID,
        sanitizer_kind="model_local",
        sanitizer_version=sanitizer_version,
        sanitizer_config_digest=sanitizer_config_digest,
        derivative_content="Generic bounded repair request.",
        derivative_digest="sha256:" + "7" * 64,
    )
    replacement = SimpleNamespace(id="prompt-bluecad")
    calls: list[str] = []
    monkeypatch.setattr(
        evidence_egress_module,
        "resolve_approved_prompt_derivative",
        lambda **_kwargs: existing,
    )
    monkeypatch.setattr(
        evidence_egress_module,
        "_expected_structural_prompt_config_digest",
        lambda: "e" * 64,
    )
    monkeypatch.setattr(
        evidence_egress_module,
        "sanitize_prompt_with_local_model",
        lambda **_kwargs: calls.append("sanitize") or replacement,
    )

    result = evidence_egress_module._resolve_external_prompt_derivative(
        workspace_id=WORKSPACE_ID,
        raw_prompt="CONFIDENTIAL PROJECT GEOMETRY: raw task.",
        forbidden_spec_json='{"schema_version":"geometry_spec_v0_1"}',
        adapters=None,
    )
    assert result is replacement
    assert calls == ["sanitize"]


def test_prompt_reuse_accepts_exact_bluecad_sanitizer_identity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    existing = SimpleNamespace(
        id="prompt-bluecad",
        status="approved",
        workspace_id=WORKSPACE_ID,
        sanitizer_kind="model_local",
        sanitizer_version="bluecad_structural_abstraction_v0_1",
        sanitizer_config_digest="e" * 64,
        derivative_content="Generic bounded repair request.",
        derivative_digest="sha256:" + "7" * 64,
    )
    monkeypatch.setattr(
        evidence_egress_module,
        "resolve_approved_prompt_derivative",
        lambda **_kwargs: existing,
    )
    monkeypatch.setattr(
        evidence_egress_module,
        "_expected_structural_prompt_config_digest",
        lambda: "e" * 64,
    )
    monkeypatch.setattr(
        evidence_egress_module,
        "sanitize_prompt_with_local_model",
        lambda **_kwargs: (_ for _ in ()).throw(AssertionError("must reuse")),
    )

    result = evidence_egress_module._resolve_external_prompt_derivative(
        workspace_id=WORKSPACE_ID,
        raw_prompt="CONFIDENTIAL PROJECT GEOMETRY: raw task.",
        forbidden_spec_json='{"schema_version":"geometry_spec_v0_1"}',
        adapters=None,
    )
    assert result is existing


def test_bluecad_prompt_sanitizer_binds_template_and_version(
''',
)

print("S3 review P1 patch prepared")
