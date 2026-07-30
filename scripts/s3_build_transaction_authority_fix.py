from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SANITIZER = ROOT / "backend/app/modules/ai/egress_sanitizer.py"
EVIDENCE = ROOT / "backend/app/modules/bluecad/evidence_egress.py"
RUNTIME = ROOT / "backend/app/modules/ai/egress_runtime.py"
TEST = ROOT / "backend/tests/bluecad/test_evidence_egress_final_authority.py"


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{path}: expected one replacement, found {count}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


replace_once(
    SANITIZER,
    '''    sanitizer_ai_job_id: str | None = None,
    expected_source_digests: dict[str, str] | None = None,
    approval_source: str = "policy-sanitizer-v1",
''',
    '''    sanitizer_ai_job_id: str | None = None,
    expected_source_digests: dict[str, str] | None = None,
    expected_source_levels: dict[str, str] | None = None,
    approval_source: str = "policy-sanitizer-v1",
''',
)

replace_once(
    SANITIZER,
    '''    expected_source_digests = _validate_expected_source_digests(
        expected_source_digests,
        source_refs=source_refs_tuple,
        required=sanitizer_kind == "model_local",
    )

    derivative_digest = sensitivity._derivative_content_digest(derivative_content)
''',
    '''    expected_source_digests = _validate_expected_source_digests(
        expected_source_digests,
        source_refs=source_refs_tuple,
        required=sanitizer_kind == "model_local",
    )
    expected_source_levels = _validate_expected_source_levels(
        expected_source_levels,
        source_refs=source_refs_tuple,
    )

    derivative_digest = sensitivity._derivative_content_digest(derivative_content)
''',
)

replace_once(
    SANITIZER,
    '''        source_digests = {
            snapshot.subject_ref: snapshot.content_digest
            for snapshot, _label in resolved_sources
        }
        if expected_source_digests is not None and source_digests != expected_source_digests:
            raise sensitivity.SensitivityPolicyError(
                "Canonical sanitizer source snapshot changed before approval."
            )
        source_digests_json = canonical_json(source_digests)
''',
    '''        source_digests = {
            snapshot.subject_ref: snapshot.content_digest
            for snapshot, _label in resolved_sources
        }
        if expected_source_digests is not None and source_digests != expected_source_digests:
            raise sensitivity.SensitivityPolicyError(
                "Canonical sanitizer source snapshot changed before approval."
            )
        source_levels = {
            snapshot.subject_ref: sensitivity._effective_level_for_bound_snapshot(
                snapshot,
                label,
            )
            for snapshot, label in resolved_sources
        }
        if expected_source_levels is not None and source_levels != expected_source_levels:
            raise sensitivity.SensitivityPolicyError(
                "Canonical sanitizer source level changed before approval."
            )
        source_digests_json = canonical_json(source_digests)
''',
)

replace_once(
    SANITIZER,
    '''    return dict(sorted(cleaned.items()))


def _validate_final_content(content: str, *, final_level: str) -> None:
''',
    '''    return dict(sorted(cleaned.items()))


def _validate_expected_source_levels(
    values: dict[str, str] | None,
    *,
    source_refs: tuple[str, ...],
) -> dict[str, str] | None:
    if values is None:
        return None
    if not isinstance(values, dict):
        raise EgressContractError("expected_source_levels must be a mapping")
    allowed_levels = {"S0", "S1", "S2", "S3", "S4", "unknown"}
    cleaned: dict[str, str] = {}
    for raw_ref, raw_level in values.items():
        source_ref = _required_text(raw_ref, "expected_source_level source_ref")
        sensitivity._parse_subject_ref(source_ref)
        level = _required_text(raw_level, "expected_source_level")
        if level not in allowed_levels:
            raise EgressContractError("expected_source_levels contains an invalid level")
        if source_ref in cleaned:
            raise EgressContractError("expected_source_levels contains duplicates")
        cleaned[source_ref] = level
    if set(cleaned) != set(source_refs):
        raise sensitivity.SensitivityPolicyError(
            "Expected canonical source level set does not match source_refs."
        )
    return dict(sorted(cleaned.items()))


def _validate_final_content(content: str, *, final_level: str) -> None:
''',
)

replace_once(
    EVIDENCE,
    '''            sanitizer_config_digest=config_digest,
            expected_source_digests=source_digests,
            approval_source="evidence-egress-v0",
''',
    '''            sanitizer_config_digest=config_digest,
            expected_source_digests=source_digests,
            expected_source_levels=dict(zip(ordered_source_refs, effective_levels, strict=True)),
            approval_source="evidence-egress-v0",
''',
)

replace_once(
    RUNTIME,
    '''    if authority.result != "eligible":
        raise _stop(
            result="pause",
            reason_code="manual_context_not_authorized",
            prompt_level=_prompt_floor_or_unknown(prompt),
            context_digest=raw_digest,
            source_count=len(blocks),
            included_count=len(authority.included_manifest),
            withheld_count=len(authority.withheld_manifest),
        )
''',
    '''    if authority.result != "eligible":
        if has_active_evidence_lineage():
            raise _stop(
                result="deny",
                reason_code="bluecad_evidence_authority_changed",
                prompt_level=_prompt_floor_or_unknown(prompt),
                context_digest=raw_digest,
                source_count=len(blocks),
                included_count=len(authority.included_manifest),
                withheld_count=len(authority.withheld_manifest),
                detail_reason="bluecad_evidence_authority_changed",
                ai_error_type="sensitivity_policy_error",
            )
        raise _stop(
            result="pause",
            reason_code="manual_context_not_authorized",
            prompt_level=_prompt_floor_or_unknown(prompt),
            context_digest=raw_digest,
            source_count=len(blocks),
            included_count=len(authority.included_manifest),
            withheld_count=len(authority.withheld_manifest),
        )
''',
)

with TEST.open("a", encoding="utf-8") as handle:
    handle.write(
        '''


def test_deterministic_evidence_approval_binds_transaction_source_levels(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    def approve(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(derivative_id="derivative-transaction")

    monkeypatch.setattr(evidence_egress, "auto_approve_canonical_derivative", approve)
    monkeypatch.setattr(
        evidence_egress,
        "_canonical_derivative_row",
        lambda _workspace_id, derivative_id: {"id": derivative_id},
    )
    sight = EvidenceSight(
        "EVIDENCE_SIGHT_V0\\nevidence:e2\\nevidence:e1",
        "sha256:" + "1" * 64,
        ("e2", "e1"),
    )

    resolved = evidence_egress._resolve_evidence_derivative(
        workspace_id="bluerev",
        candidate_id="candidate-1",
        source_attempt_id="attempt-1",
        sight=sight,
        ordered_source_refs=("evidence:e2", "evidence:e1"),
        source_digests={
            "evidence:e2": "sha256:" + "5" * 64,
            "evidence:e1": "sha256:" + "6" * 64,
        },
        effective_levels=("S0", "S1"),
        adapters={},
    )

    assert resolved == {"id": "derivative-transaction"}
    assert captured["expected_source_levels"] == {
        "evidence:e2": "S0",
        "evidence:e1": "S1",
    }


def test_noneligible_bluecad_context_authority_is_blocked_prepacket(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    authority = SimpleNamespace(
        result="pause",
        included_manifest=(),
        withheld_manifest=({"source_ref": "derivative:stale"},),
    )
    monkeypatch.setattr(
        egress_runtime,
        "authorize_manual_context",
        lambda **_kwargs: authority,
    )

    with evidence_egress.bind_evidence_lineage(_lineage()):
        with pytest.raises(egress_runtime._PrepacketStop) as caught:
            egress_runtime._authorize_context(
                context_blocks=[
                    {
                        "source": "BLUECAD evidence",
                        "content": "sanitized structural evidence",
                    }
                ],
                workspace_id="bluerev",
                policy=SimpleNamespace(max_context_chars=2000),
                prompt="CONFIDENTIAL PROJECT GEOMETRY: raw task.",
            )

    stop = caught.value
    assert stop.result == "deny"
    assert stop.reason_code == "bluecad_evidence_authority_changed"
    assert stop.ai_error_type == "sensitivity_policy_error"
'''
    )

print("S3 transaction and noneligible-authority fixes prepared")
