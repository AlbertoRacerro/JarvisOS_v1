from __future__ import annotations

import hashlib
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(path: str, old: str, new: str) -> None:
    target = ROOT / path
    text = target.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{path}: expected one replacement, found {count}")
    target.write_text(text.replace(old, new, 1), encoding="utf-8")


def assert_blob(path: str, expected: str) -> None:
    actual = subprocess.check_output(
        ["git", "hash-object", path], cwd=ROOT, text=True
    ).strip()
    if actual != expected:
        raise RuntimeError(f"{path}: blob {actual} != expected {expected}")


# Generic local sanitizer seam; defaults remain byte-for-byte equivalent for old callers.
replace_once(
    "backend/app/modules/ai/egress_authority.py",
    '''    output_validator: Callable[[str], None] | None = None,
) -> PromptDerivative:
''',
    '''    output_validator: Callable[[str], None] | None = None,
    sanitizer_template: str = _LOCAL_SANITIZER_TEMPLATE,
    sanitizer_version: str = _LOCAL_SANITIZER_VERSION,
) -> PromptDerivative:
''',
)
replace_once(
    "backend/app/modules/ai/egress_authority.py",
    '''    binding, registry = _resolve_local_sanitizer_binding(
        route_class=route_class,
        registry=registry,
    )
    sanitizer_input = (
        f"{_LOCAL_SANITIZER_TEMPLATE}\\n\\n"
''',
    '''    binding, registry = _resolve_local_sanitizer_binding(
        route_class=route_class,
        registry=registry,
    )
    sanitizer_template = _required_text(sanitizer_template, "sanitizer_template")
    sanitizer_version = _required_text(sanitizer_version, "sanitizer_version")
    sanitizer_input = (
        f"{sanitizer_template}\\n\\n"
''',
)
replace_once(
    "backend/app/modules/ai/egress_authority.py",
    '''        template=_LOCAL_SANITIZER_TEMPLATE,
        version=_LOCAL_SANITIZER_VERSION,
''',
    '''        template=sanitizer_template,
        version=sanitizer_version,
''',
)
replace_once(
    "backend/app/modules/ai/egress_authority.py",
    '''        sanitizer_kind="model_local",
        sanitizer_version=_LOCAL_SANITIZER_VERSION,
        sanitizer_config_digest=config_digest,
''',
    '''        sanitizer_kind="model_local",
        sanitizer_version=sanitizer_version,
        sanitizer_config_digest=config_digest,
''',
)

# Validate the exact PromptAuthority selected by 059b before packet material exists.
replace_once(
    "backend/app/modules/ai/egress_runtime.py",
    '''    final_level = max(
        (prompt.prompt_level or "S1", context.level),
        key=_LEVEL_RANK.__getitem__,
    )
    if continuation_decision is None:
''',
    '''    final_level = max(
        (prompt.prompt_level or "S1", context.level),
        key=_LEVEL_RANK.__getitem__,
    )
    from app.modules.bluecad.evidence_egress import (
        validate_authorized_structural_prompt_authority,
    )

    validate_authorized_structural_prompt_authority(prompt)
    if continuation_decision is None:
''',
)

# BLUECAD-specific sanitizer identity and exact authority revalidation.
replace_once(
    "backend/app/modules/bluecad/evidence_egress.py",
    '''EXTERNAL_STRUCTURAL_PROMPT_VERSION = "bluecad_ai_loop_v3_structural_external_v0_1"
_EVIDENCE_DERIVATIVE_VERSION = "bluecad_evidence_sight_derivative_v0_1"
''',
    '''EXTERNAL_STRUCTURAL_PROMPT_VERSION = "bluecad_ai_loop_v3_structural_external_v0_1"
_STRUCTURAL_SANITIZER_VERSION = "bluecad_structural_abstraction_v0_1"
_STRUCTURAL_SANITIZER_TEMPLATE = (
    "Transform the BLUECAD structural repair task into a bounded generic abstraction. "
    "Remove the raw GeometrySpec, project identity, proprietary geometry, exact "
    "dimensions, unpublished parameters, credentials, and secrets. Preserve only "
    "non-sensitive structural symptoms and generic repair constraints. Return only "
    "the abstracted repair request, without JSON, source markers, or commentary."
)
_EVIDENCE_DERIVATIVE_VERSION = "bluecad_evidence_sight_derivative_v0_1"
''',
)
replace_once(
    "backend/app/modules/bluecad/evidence_egress.py",
    '''def enrich_authorized_evidence_manifest(
''',
    '''def validate_authorized_structural_prompt_authority(authority: Any) -> None:
    """Validate the exact prompt authority selected immediately before packet material."""

    lineage = _ACTIVE_LINEAGE.get()
    if lineage is None:
        return
    _validate_lineage(lineage)
    if (
        getattr(authority, "prompt_derivative_id", None)
        != lineage["instruction_derivative_id"]
        or getattr(authority, "prompt_derivative_digest", None)
        != lineage["instruction_derivative_digest"]
        or getattr(authority, "sanitizer_kind", None) != "model_local"
    ):
        raise sensitivity.SensitivityPolicyError(
            "Selected structural prompt authority differs from preparation authority."
        )
    derivative = get_prompt_derivative(
        lineage["instruction_derivative_id"],
        workspace_id=lineage["workspace_id"],
    )
    validate_authorized_structural_prompt_derivative(derivative)


def enrich_authorized_evidence_manifest(
''',
)
replace_once(
    "backend/app/modules/bluecad/evidence_egress.py",
    '''        output_validator=lambda content: _validate_transformed_prompt_content(
            content,
            raw_prompt=raw_prompt,
            forbidden_spec_json=forbidden_spec_json,
        ),
    )
''',
    '''        output_validator=lambda content: _validate_transformed_prompt_content(
            content,
            raw_prompt=raw_prompt,
            forbidden_spec_json=forbidden_spec_json,
        ),
        sanitizer_template=_STRUCTURAL_SANITIZER_TEMPLATE,
        sanitizer_version=_STRUCTURAL_SANITIZER_VERSION,
    )
''',
)
replace_once(
    "backend/app/modules/bluecad/evidence_egress.py",
    '''        content == raw_prompt
        or forbidden_spec_json in content
        or "RAW_GEOMETRY_SPEC_BEGIN" in content
''',
    '''        content == raw_prompt
        or forbidden_spec_json in content
        or _contains_structural_json_value(content, json.loads(forbidden_spec_json))
        or "RAW_GEOMETRY_SPEC_BEGIN" in content
''',
)
replace_once(
    "backend/app/modules/bluecad/evidence_egress.py",
    '''def _canonical_derivative_row(workspace_id: str, derivative_id: str) -> dict[str, Any]:
''',
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


def _canonical_derivative_row(workspace_id: str, derivative_id: str) -> dict[str, Any]:
''',
)
replace_once(
    "backend/app/modules/bluecad/evidence_egress.py",
    '''def _validate_current_lineage_sight(lineage: dict[str, Any]) -> None:
    sight = _current_lineage_sight(lineage)
    expected_refs = tuple(lineage["ordered_source_refs"])
    current_refs = tuple(f"evidence:{record_id}" for record_id in sight.record_ids)
    if sight.digest != lineage["sight_digest"] or current_refs != expected_refs:
        raise sensitivity.SensitivityPolicyError(
            "Evidence sight changed before packet authorization."
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


def _current_lineage_authority_snapshot(lineage: dict[str, Any]) -> dict[str, Any]:
    workspace_id = lineage["workspace_id"]
    candidate_id = lineage["candidate_id"]
    source_attempt_id = lineage["source_attempt_id"]
    with open_sqlite_connection() as connection:
        connection.execute("BEGIN")
        candidate = connection.execute(
            "SELECT workspace_id, status FROM bluecad_candidates WHERE id = ?",
            (candidate_id,),
        ).fetchone()
        attempt = connection.execute(
            "SELECT candidate_id FROM bluecad_attempts WHERE id = ?",
            (source_attempt_id,),
        ).fetchone()
        derivative = connection.execute(
            "SELECT * FROM sanitized_derivatives WHERE id = ? AND workspace_id = ?",
            (lineage["derivative_id"], workspace_id),
        ).fetchone()
        if (
            candidate is None
            or candidate["workspace_id"] != workspace_id
            or candidate["status"] != "valid"
            or attempt is None
            or attempt["candidate_id"] != candidate_id
            or derivative is None
            or derivative["status"] != "approved"
        ):
            raise sensitivity.SensitivityPolicyError(
                "Evidence authority ownership or lifecycle changed before packet authorization."
            )
        sight = _render_evidence_sight_in_connection(
            connection, workspace_id, candidate_id, source_attempt_id
        )
        current_refs = (
            tuple(f"evidence:{record_id}" for record_id in sight.record_ids)
            if sight is not None
            else ()
        )
        source_digests: dict[str, str] = {}
        effective_levels: list[str] = []
        for source_ref in current_refs:
            snapshot, label = sensitivity._resolve_source_snapshot_and_label_in_connection(
                connection, workspace_id, source_ref
            )
            source_digests[source_ref] = snapshot.content_digest
            effective_levels.append(
                sensitivity._effective_level_for_bound_snapshot(snapshot, label)
            )
        connection.commit()
    if sight is None:
        raise sensitivity.SensitivityPolicyError(
            "Evidence sight disappeared before packet authorization."
        )
    return {
        "sight": sight,
        "derivative": dict(derivative),
        "source_refs": current_refs,
        "source_digests": source_digests,
        "effective_levels": tuple(effective_levels),
    }


''',
)

# Focused fail-closed tests and sanitizer provenance identity.
replace_once(
    "backend/tests/bluecad/test_evidence_egress.py",
    '''from app.modules.bluecad.evidence_egress import (
    bind_evidence_lineage,
    enrich_authorized_evidence_manifest,
)
''',
    '''from app.modules.bluecad.evidence_egress import (
    bind_evidence_lineage,
    enrich_authorized_evidence_manifest,
    validate_authorized_structural_prompt_authority,
)
''',
)
replace_once(
    "backend/tests/bluecad/test_evidence_egress.py",
    '''def test_lineage_enrichment_is_scoped_and_exact(
''',
    '''def _matching_authority_snapshot(
    *, sight: EvidenceSight | None = None, effective_level: str = "S1"
) -> dict[str, object]:
    return {
        "sight": sight or _matching_sight(),
        "derivative": {
            "source_refs_json": '["evidence:e1"]',
            "source_digests_json": '{"evidence:e1":"sha256:' + "5" * 64 + '"}',
            "effective_level": "S1",
            "content_digest": "sha256:" + "2" * 64,
        },
        "source_refs": tuple(f"evidence:{item}" for item in (sight or _matching_sight()).record_ids),
        "source_digests": {"evidence:e1": "sha256:" + "5" * 64},
        "effective_levels": (effective_level,),
    }


def test_lineage_enrichment_is_scoped_and_exact(
''',
)
# The first two exact happy-path monkeypatches.
for _ in range(2):
    replace_once(
        "backend/tests/bluecad/test_evidence_egress.py",
        '''        "_current_lineage_sight",
        lambda _lineage: _matching_sight(),
''',
        '''        "_current_lineage_authority_snapshot",
        lambda _lineage: _matching_authority_snapshot(),
''',
    )
replace_once(
    "backend/tests/bluecad/test_evidence_egress.py",
    '''def test_packet_authorization_rejects_sight_insertion_order_or_digest_drift(
''',
    '''def test_selected_prompt_authority_rejects_substitution_before_packet(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    adapter_calls: list[str] = []
    monkeypatch.setattr(
        evidence_egress_module,
        "get_prompt_derivative",
        lambda *_args, **_kwargs: adapter_calls.append("lookup"),
    )
    substituted = SimpleNamespace(
        prompt_derivative_id="prompt-derivative-other",
        prompt_derivative_digest="sha256:" + "9" * 64,
        sanitizer_kind="model_local",
    )
    with bind_evidence_lineage(_lineage()), pytest.raises(
        sensitivity.SensitivityPolicyError
    ):
        validate_authorized_structural_prompt_authority(substituted)
    assert adapter_calls == []


def test_packet_authorization_rejects_sight_insertion_order_or_digest_drift(
''',
)
replace_once(
    "backend/tests/bluecad/test_evidence_egress.py",
    '''            "_current_lineage_sight",
            lambda _lineage, current=sight: current,
''',
    '''            "_current_lineage_authority_snapshot",
            lambda _lineage, current=sight: _matching_authority_snapshot(sight=current),
''',
)
replace_once(
    "backend/tests/bluecad/test_evidence_egress.py",
    '''def test_lineage_mutation_changes_packet_digest() -> None:
''',
    '''def test_packet_authorization_rejects_concurrent_effective_level_drift(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        evidence_egress_module,
        "_current_structural_prompt_derivative",
        lambda _lineage: _matching_prompt_derivative(),
    )
    monkeypatch.setattr(
        evidence_egress_module,
        "_current_lineage_authority_snapshot",
        lambda _lineage: _matching_authority_snapshot(effective_level="S2"),
    )
    with bind_evidence_lineage(_lineage()), pytest.raises(
        sensitivity.SensitivityPolicyError
    ):
        enrich_authorized_evidence_manifest(_manifest())


def test_lineage_mutation_changes_packet_digest() -> None:
''',
)
replace_once(
    "backend/tests/bluecad/test_evidence_egress.py",
    '''def test_prompt_validator_runs_before_derivative_persistence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
''',
    '''@pytest.mark.parametrize(
    "sanitized_content",
    (
        "Generic repair\\nRAW_GEOMETRY_SPEC_BEGIN",
        'Generic repair\\n{\\n  "schema_version": "geometry_spec_v0_1"\\n}',
        'Generic repair\\n{"payload":{"schema_version":"geometry_spec_v0_1"}}',
    ),
)
def test_prompt_validator_runs_before_derivative_persistence(
    monkeypatch: pytest.MonkeyPatch,
    sanitized_content: str,
) -> None:
''',
)
replace_once(
    "backend/tests/bluecad/test_evidence_egress.py",
    '''        text="Generic repair\\nRAW_GEOMETRY_SPEC_BEGIN",
''',
    '''        text=sanitized_content,
''',
)
replace_once(
    "backend/tests/bluecad/test_evidence_egress.py",
    '''def test_model_sanitizer_config_identity_binds_renderer_context() -> None:
''',
    '''def test_bluecad_prompt_sanitizer_binds_template_and_version(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    initialize_database()
    binding = SimpleNamespace(
        provider_id="local-provider",
        model_id="local-model",
        requires_network=False,
        max_output_tokens=256,
    )
    registry = SimpleNamespace(
        bindings={"local:fast": binding}, fallback_chains={"local:fast": ()}
    )
    captured: dict[str, str] = {}
    monkeypatch.setattr(
        egress_authority_module,
        "_resolve_local_sanitizer_binding",
        lambda **_kwargs: (binding, registry),
    )

    def run_sanitizer(**kwargs):
        captured["input"] = kwargs["sanitizer_input"]
        return SimpleNamespace(
            status="success",
            response=SimpleNamespace(
                text="Generic bounded structural repair request.",
                provider_id=binding.provider_id,
                model_id=binding.model_id,
            ),
            selected_route_class="local:fast",
            ledger_id="sanitizer-job-1",
            error_type=None,
        )

    monkeypatch.setattr(egress_authority_module, "_run_local_sanitizer", run_sanitizer)
    monkeypatch.setattr(
        egress_authority_module,
        "create_prompt_derivative",
        lambda **kwargs: (
            captured.update(
                version=kwargs["sanitizer_version"],
                config_digest=kwargs["sanitizer_config_digest"],
            )
            or SimpleNamespace(derivative_id="prompt-derivative-1")
        ),
    )
    monkeypatch.setattr(
        egress_authority_module,
        "get_prompt_derivative",
        lambda *_args, **_kwargs: SimpleNamespace(id="prompt-derivative-1"),
    )
    evidence_egress_module._resolve_external_prompt_derivative(
        workspace_id=WORKSPACE_ID,
        raw_prompt="CONFIDENTIAL PROJECT GEOMETRY: raw task.",
        forbidden_spec_json='{"schema_version":"geometry_spec_v0_1"}',
        adapters=None,
    )
    assert captured["version"] == "bluecad_structural_abstraction_v0_1"
    assert captured["input"].startswith(
        "Transform the BLUECAD structural repair task into a bounded generic abstraction."
    )
    generic_digest = egress_authority_module._sanitizer_config_digest(
        policy=evidence_egress_module.load_default_egress_policy(),
        route_class="local:fast",
        template=egress_authority_module._LOCAL_SANITIZER_TEMPLATE,
        version=egress_authority_module._LOCAL_SANITIZER_VERSION,
        registry=registry,
    )
    assert captured["config_digest"] != generic_digest


def test_model_sanitizer_config_identity_binds_renderer_context() -> None:
''',
)

# Preserve current master governance and mark only the active implementation review state.
status_path = ROOT / "docs/specs/STATUS.md"
status = status_path.read_text(encoding="utf-8")
status, replacements = re.subn(
    r"^\| 077 \| ready \| — \|",
    "| 077 | in_review | [#198](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/198) |",
    status,
    count=1,
    flags=re.MULTILINE,
)
if replacements != 1:
    raise RuntimeError(f"STATUS: expected one 077 ready row, found {replacements}")
status_path.write_text(status, encoding="utf-8")

# Exact transfer identity: these are the blobs produced by the independently tested patch.
assert_blob(
    "backend/app/modules/ai/egress_authority.py",
    "1a4ae85eed20c75d933c2e78bf6d01b75d62dfaf",
)
assert_blob(
    "backend/app/modules/ai/egress_runtime.py",
    "1df4a3985dd27b8c241ec150a7903ac36a5d7155",
)
assert_blob(
    "backend/app/modules/bluecad/evidence_egress.py",
    "2e5fe3a162010593f18ca3584fe9c9cf9a12fb46",
)
assert_blob(
    "backend/tests/bluecad/test_evidence_egress.py",
    "05b7255527ed483487179fd136464e18c54fc3dd",
)

if "| 078 | planned | — | PBR-MODELING-0" not in status:
    raise RuntimeError("STATUS: merged 078 governance was not preserved")

print("S3 exact patch and master governance prepared")
