from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUTHORITY = ROOT / "backend/app/modules/ai/egress_authority.py"
EVIDENCE = ROOT / "backend/app/modules/bluecad/evidence_egress.py"
TEST = ROOT / "backend/tests/bluecad/test_evidence_egress_final_authority.py"


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{path}: expected one replacement, found {count}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


replace_once(
    AUTHORITY,
    '''    policy: EgressPolicyConfig | None = None,
    config_context: dict[str, Any] | None = None,
) -> SanitizerApproval:
''',
    '''    policy: EgressPolicyConfig | None = None,
    config_context: dict[str, Any] | None = None,
    expected_source_levels: dict[str, str] | None = None,
) -> SanitizerApproval:
''',
)

replace_once(
    AUTHORITY,
    '''        sanitizer_ai_job_id=outcome.ledger_id,
        expected_source_digests=source_digests,
        policy=policy,
''',
    '''        sanitizer_ai_job_id=outcome.ledger_id,
        expected_source_digests=source_digests,
        expected_source_levels=expected_source_levels,
        policy=policy,
''',
)

replace_once(
    EVIDENCE,
    '''            adapters=adapters,
            config_context=renderer_context,
        )
''',
    '''            adapters=adapters,
            config_context=renderer_context,
            expected_source_levels=dict(
                zip(ordered_source_refs, effective_levels, strict=True)
            ),
        )
''',
)

with TEST.open("a", encoding="utf-8") as handle:
    handle.write(
        '''


def test_model_evidence_approval_forwards_transaction_source_levels(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    monkeypatch.setattr(
        evidence_egress,
        "_resolve_reusable_model_evidence_derivative",
        lambda **_kwargs: None,
    )

    def sanitize(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(derivative_id="derivative-model-transaction")

    monkeypatch.setattr(
        evidence_egress,
        "sanitize_canonical_sources_with_local_model",
        sanitize,
    )
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
        effective_levels=("S2", "unknown"),
        adapters={},
    )

    assert resolved == {"id": "derivative-model-transaction"}
    assert captured["expected_source_levels"] == {
        "evidence:e2": "S2",
        "evidence:e1": "unknown",
    }
'''
    )

print("S3 model-backed source-level propagation fix prepared")
