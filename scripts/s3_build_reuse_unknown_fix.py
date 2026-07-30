from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CODE = ROOT / "backend/app/modules/bluecad/evidence_egress.py"
TEST = ROOT / "backend/tests/bluecad/test_evidence_egress_final_authority.py"


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{path}: expected one replacement, found {count}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


replace_once(
    CODE,
    '''from app.modules.ai.egress_authority import (
    _sanitizer_config_digest,
''',
    '''from app.modules.ai.egress_authority import (
    _CANONICAL_SANITIZER_TEMPLATE,
    _CANONICAL_SANITIZER_VERSION,
    _sanitizer_config_digest,
''',
)

replace_once(
    CODE,
    '''    else:
        approval = sanitize_canonical_sources_with_local_model(
            workspace_id=workspace_id,
            source_refs=ordered_source_refs,
            adapters=adapters,
            config_context=renderer_context,
        )
    return _canonical_derivative_row(workspace_id, approval.derivative_id)


def _resolve_external_prompt_derivative(
''',
    '''    else:
        reusable = _resolve_reusable_model_evidence_derivative(
            workspace_id=workspace_id,
            ordered_source_refs=ordered_source_refs,
            source_digests=source_digests,
            renderer_context=renderer_context,
        )
        if reusable is not None:
            _validate_evidence_derivative(
                reusable,
                workspace_id=workspace_id,
                ordered_source_refs=ordered_source_refs,
                source_digests=source_digests,
            )
            return reusable
        approval = sanitize_canonical_sources_with_local_model(
            workspace_id=workspace_id,
            source_refs=ordered_source_refs,
            adapters=adapters,
            config_context=renderer_context,
        )
    return _canonical_derivative_row(workspace_id, approval.derivative_id)


def _resolve_reusable_model_evidence_derivative(
    *,
    workspace_id: str,
    ordered_source_refs: tuple[str, ...],
    source_digests: dict[str, str],
    renderer_context: dict[str, Any],
) -> dict[str, Any] | None:
    policy = load_default_egress_policy()
    registry = load_default_provider_registry()
    config_digest = _sanitizer_config_digest(
        policy=policy,
        route_class="local:fast",
        template=_CANONICAL_SANITIZER_TEMPLATE,
        version=_CANONICAL_SANITIZER_VERSION,
        registry=registry,
        config_context=renderer_context,
    )
    with open_sqlite_connection() as connection:
        row = connection.execute(
            """
            SELECT *
            FROM sanitized_derivatives
            WHERE workspace_id = ?
              AND source_refs_json = ?
              AND source_digests_json = ?
              AND effective_level = 'S1'
              AND sanitizer_kind = 'model_local'
              AND sanitizer_version = ?
              AND sanitizer_config_digest = ?
              AND sanitizer_ai_job_id IS NOT NULL
              AND policy_version = ?
              AND approval_source = 'policy-sanitizer-v1'
              AND auto_approved = 1
              AND status = 'approved'
            ORDER BY created_at DESC, id ASC
            LIMIT 1
            """,
            (
                workspace_id,
                canonical_json(sorted(ordered_source_refs)),
                canonical_json(source_digests),
                _CANONICAL_SANITIZER_VERSION,
                config_digest,
                policy.policy_version,
            ),
        ).fetchone()
    return dict(row) if row is not None else None


def _resolve_external_prompt_derivative(
''',
)

replace_once(
    CODE,
    '''        or any(level not in {"S0", "S1", "S2", "S3", "S4"} for level in levels)
''',
    '''        or any(
            level not in {"S0", "S1", "S2", "S3", "S4", "unknown"}
            for level in levels
        )
''',
)

with TEST.open("a", encoding="utf-8") as handle:
    handle.write(
        '''


def test_sensitive_evidence_reuses_matching_derivative_before_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    existing = {"id": "derivative-existing"}
    monkeypatch.setattr(
        evidence_egress,
        "_resolve_reusable_model_evidence_derivative",
        lambda **_kwargs: existing,
    )
    monkeypatch.setattr(
        evidence_egress,
        "_validate_evidence_derivative",
        lambda *_args, **_kwargs: None,
    )
    monkeypatch.setattr(
        evidence_egress,
        "sanitize_canonical_sources_with_local_model",
        lambda **_kwargs: (_ for _ in ()).throw(
            AssertionError("matching authority must be reused before model execution")
        ),
    )
    sight = EvidenceSight(
        "EVIDENCE_SIGHT_V0\\nevidence:e1",
        "sha256:" + "1" * 64,
        ("e1",),
    )

    resolved = evidence_egress._resolve_evidence_derivative(
        workspace_id="bluerev",
        candidate_id="candidate-1",
        source_attempt_id="attempt-1",
        sight=sight,
        ordered_source_refs=("evidence:e1",),
        source_digests={"evidence:e1": "sha256:" + "5" * 64},
        effective_levels=("S2",),
        adapters={},
    )

    assert resolved is existing


def test_lineage_accepts_unknown_raw_source_level() -> None:
    lineage = _lineage()
    lineage["source_effective_levels"] = ["unknown", "S1"]

    with evidence_egress.bind_evidence_lineage(lineage):
        pass
'''
    )

print("S3 reuse and unknown-level patch prepared")
