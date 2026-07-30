from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
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
    EVIDENCE,
    '''_ACTIVE_LINEAGE: ContextVar[dict[str, Any] | None] = ContextVar(
    "bluecad_evidence_egress_lineage",
    default=None,
)


@dataclass(frozen=True)
''',
    '''_ACTIVE_LINEAGE: ContextVar[dict[str, Any] | None] = ContextVar(
    "bluecad_evidence_egress_lineage",
    default=None,
)


def has_active_evidence_lineage() -> bool:
    """Return whether BLUECAD packet authority is active in this execution context."""

    return _ACTIVE_LINEAGE.get() is not None


@dataclass(frozen=True)
''',
)

replace_once(
    RUNTIME,
    '''    try:
        authority = authorize_manual_context(
            workspace_id=workspace_id,
            raw_blocks=blocks,
            budget_chars=policy.max_context_chars,
        )
    except ValueError as exc:
        raise _stop(
            result="pause",
            reason_code="manual_context_not_authorized",
            prompt_level=_prompt_floor_or_unknown(prompt),
            context_digest=raw_digest,
            source_count=len(blocks),
            withheld_count=len(blocks),
        ) from exc
''',
    '''    from app.modules.bluecad.evidence_egress import has_active_evidence_lineage

    try:
        authority = authorize_manual_context(
            workspace_id=workspace_id,
            raw_blocks=blocks,
            budget_chars=policy.max_context_chars,
        )
    except sensitivity.SensitivityPolicyError as exc:
        if has_active_evidence_lineage():
            raise _stop(
                result="deny",
                reason_code="bluecad_evidence_authority_changed",
                prompt_level=_prompt_floor_or_unknown(prompt),
                context_digest=raw_digest,
                source_count=len(blocks),
                withheld_count=len(blocks),
                detail_reason="bluecad_evidence_authority_changed",
                ai_error_type="sensitivity_policy_error",
            ) from exc
        raise _stop(
            result="pause",
            reason_code="manual_context_not_authorized",
            prompt_level=_prompt_floor_or_unknown(prompt),
            context_digest=raw_digest,
            source_count=len(blocks),
            withheld_count=len(blocks),
        ) from exc
    except ValueError as exc:
        raise _stop(
            result="pause",
            reason_code="manual_context_not_authorized",
            prompt_level=_prompt_floor_or_unknown(prompt),
            context_digest=raw_digest,
            source_count=len(blocks),
            withheld_count=len(blocks),
        ) from exc
''',
)

with TEST.open("a", encoding="utf-8") as handle:
    handle.write(
        '''


def test_late_evidence_drift_becomes_bluecad_blocked_prepacket(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        egress_runtime,
        "authorize_manual_context",
        lambda **_kwargs: (_ for _ in ()).throw(
            sensitivity.SensitivityPolicyError("concurrent evidence authority drift")
        ),
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
    assert stop.detail_reason == "bluecad_evidence_authority_changed"
    assert stop.ai_error_type == "sensitivity_policy_error"
'''
    )

print("S3 blocked-authority audit fix prepared")
