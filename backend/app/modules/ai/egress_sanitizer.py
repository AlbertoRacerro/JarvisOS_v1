from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import uuid4

from app.core.database import open_sqlite_connection
from app.modules.ai import sensitivity
from app.modules.ai.egress_policy import EgressPolicyConfig, load_default_egress_policy
from app.modules.ai.egress_service import (
    EgressContractError,
    canonical_json,
    sanitizer_sample_value,
    sanitizer_should_sample,
    sha256_text,
)
from app.modules.events.service import log_event

_ALLOWED_FINAL_LEVELS = frozenset({"S0", "S1"})
_ALLOWED_SANITIZER_KINDS = frozenset({"deterministic", "model_local"})
_ALLOWED_AUDIT_DISPOSITIONS = frozenset({"accepted", "rejected"})


@dataclass(frozen=True)
class PromptDerivative:
    id: str
    workspace_id: str | None
    raw_prompt_digest: str
    derivative_digest: str
    final_level: str
    transformations: tuple[str, ...]
    sanitizer_kind: str
    sanitizer_version: str
    sanitizer_config_digest: str
    sanitizer_ai_job_id: str | None
    policy_version: str
    status: str
    created_at: str
    revoked_at: str | None
    revocation_reason: str | None
    derivative_content: str = field(repr=False)


@dataclass(frozen=True)
class SanitizerApproval:
    derivative_kind: str
    derivative_id: str
    derivative_digest: str
    workspace_id: str | None
    final_level: str
    sanitizer_kind: str
    sanitizer_version: str
    sanitizer_config_digest: str
    sanitizer_ai_job_id: str | None
    policy_version: str
    audit_item_id: str | None
    reused: bool


@dataclass(frozen=True)
class SanitizerAuditDisposition:
    audit_item_id: str
    derivative_kind: str
    derivative_id: str
    derivative_digest: str
    state: str
    invalidated_packet_count: int
    revoked_ticket_count: int
    released_reservation_count: int


def create_prompt_derivative(
    *,
    raw_prompt: str,
    derivative_content: str,
    final_level: str,
    transformations: list[str] | tuple[str, ...],
    sanitizer_kind: str,
    sanitizer_version: str,
    sanitizer_config_digest: str,
    sanitizer_ai_job_id: str | None = None,
    workspace_id: str | None = None,
    policy: EgressPolicyConfig | None = None,
    now: datetime | None = None,
) -> SanitizerApproval:
    """Persist one immutable, auto-approved S0/S1 prompt derivative."""

    policy = policy or load_default_egress_policy()
    now_dt = _normalized_now(now)
    raw_prompt = _bounded_text(raw_prompt, "raw_prompt", policy.max_prompt_chars)
    derivative_content = _bounded_text(
        derivative_content,
        "derivative_content",
        policy.max_prompt_chars,
    )
    _validate_final_content(derivative_content, final_level=final_level)
    if sensitivity.deterministic_floor(raw_prompt) == "S4":
        raise sensitivity.SensitivityPolicyError(
            "Raw prompt contains a deterministic secret marker and cannot be sanitized."
        )
    transformations_tuple = _transformations(transformations)
    _validate_provenance(
        sanitizer_kind=sanitizer_kind,
        sanitizer_version=sanitizer_version,
        sanitizer_config_digest=sanitizer_config_digest,
        sanitizer_ai_job_id=sanitizer_ai_job_id,
    )
    raw_digest = sha256_text(raw_prompt)
    derivative_digest = sha256_text(derivative_content)

    with _transaction() as connection:
        _require_workspace_if_present(connection, workspace_id)
        _validate_sanitizer_ai_job(
            connection,
            sanitizer_kind=sanitizer_kind,
            sanitizer_ai_job_id=sanitizer_ai_job_id,
        )
        existing = connection.execute(
            """
            SELECT * FROM egress_prompt_derivatives
            WHERE raw_prompt_digest = ? AND derivative_digest = ? AND policy_version = ?
            """,
            (raw_digest, derivative_digest, policy.policy_version),
        ).fetchone()
        if existing is not None:
            _assert_prompt_derivative_match(
                existing,
                workspace_id=workspace_id,
                derivative_content=derivative_content,
                final_level=final_level,
                transformations=transformations_tuple,
                sanitizer_kind=sanitizer_kind,
                sanitizer_version=sanitizer_version,
                sanitizer_config_digest=sanitizer_config_digest,
                sanitizer_ai_job_id=sanitizer_ai_job_id,
            )
            if existing["status"] != "approved":
                raise sensitivity.SensitivityPolicyError(
                    "A revoked prompt derivative cannot be reused."
                )
            audit_id = _ensure_audit_item(
                connection,
                derivative_kind="prompt",
                derivative_id=str(existing["id"]),
                derivative_digest=derivative_digest,
                workspace_id=workspace_id,
                policy=policy,
                now_dt=now_dt,
            )
            return SanitizerApproval(
                derivative_kind="prompt",
                derivative_id=str(existing["id"]),
                derivative_digest=derivative_digest,
                workspace_id=workspace_id,
                final_level=final_level,
                sanitizer_kind=sanitizer_kind,
                sanitizer_version=sanitizer_version,
                sanitizer_config_digest=sanitizer_config_digest,
                sanitizer_ai_job_id=sanitizer_ai_job_id,
                policy_version=policy.policy_version,
                audit_item_id=audit_id,
                reused=True,
            )

        derivative_id = str(uuid4())
        connection.execute(
            """
            INSERT INTO egress_prompt_derivatives (
                id, workspace_id, raw_prompt_digest, derivative_content,
                derivative_digest, final_level, transformations_json,
                sanitizer_kind, sanitizer_version, sanitizer_config_digest,
                sanitizer_ai_job_id, policy_version, status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'approved', ?)
            """,
            (
                derivative_id,
                workspace_id,
                raw_digest,
                derivative_content,
                derivative_digest,
                final_level,
                canonical_json(list(transformations_tuple)),
                sanitizer_kind,
                sanitizer_version,
                sanitizer_config_digest,
                sanitizer_ai_job_id,
                policy.policy_version,
                now_dt.isoformat(),
            ),
        )
        audit_id = _ensure_audit_item(
            connection,
            derivative_kind="prompt",
            derivative_id=derivative_id,
            derivative_digest=derivative_digest,
            workspace_id=workspace_id,
            policy=policy,
            now_dt=now_dt,
        )
        log_event(
            connection,
            event_type="EgressPromptDerivativeApproved",
            actor="deterministic-policy",
            target_type="EgressPromptDerivative",
            target_id=derivative_id,
            workspace_id=workspace_id,
            payload={
                "raw_prompt_digest": raw_digest,
                "derivative_digest": derivative_digest,
                "final_level": final_level,
                "sanitizer_kind": sanitizer_kind,
                "sanitizer_version": sanitizer_version,
                "sanitizer_config_digest": sanitizer_config_digest,
                "sanitizer_ai_job_id": sanitizer_ai_job_id,
                "policy_version": policy.policy_version,
                "audit_item_id": audit_id,
            },
        )
        return SanitizerApproval(
            derivative_kind="prompt",
            derivative_id=derivative_id,
            derivative_digest=derivative_digest,
            workspace_id=workspace_id,
            final_level=final_level,
            sanitizer_kind=sanitizer_kind,
            sanitizer_version=sanitizer_version,
            sanitizer_config_digest=sanitizer_config_digest,
            sanitizer_ai_job_id=sanitizer_ai_job_id,
            policy_version=policy.policy_version,
            audit_item_id=audit_id,
            reused=False,
        )


def auto_approve_canonical_derivative(
    *,
    workspace_id: str,
    source_refs: list[str] | tuple[str, ...],
    derivative_content: str,
    final_level: str,
    transformations: list[str] | tuple[str, ...],
    sanitizer_kind: str,
    sanitizer_version: str,
    sanitizer_config_digest: str,
    sanitizer_ai_job_id: str | None = None,
    approval_source: str = "policy-sanitizer-v1",
    policy: EgressPolicyConfig | None = None,
    now: datetime | None = None,
) -> SanitizerApproval:
    """Auto-approve one provenance-bound canonical derivative in one transaction."""

    policy = policy or load_default_egress_policy()
    now_dt = _normalized_now(now)
    workspace_id = _required_text(workspace_id, "workspace_id")
    derivative_content = _bounded_text(
        derivative_content,
        "derivative_content",
        policy.max_context_chars,
    )
    _validate_final_content(derivative_content, final_level=final_level)
    transformations_tuple = _transformations(transformations)
    source_refs_tuple = _source_refs(source_refs)
    approval_source = _required_text(approval_source, "approval_source")
    _validate_provenance(
        sanitizer_kind=sanitizer_kind,
        sanitizer_version=sanitizer_version,
        sanitizer_config_digest=sanitizer_config_digest,
        sanitizer_ai_job_id=sanitizer_ai_job_id,
    )
    derivative_digest = sensitivity._derivative_content_digest(derivative_content)

    with _transaction() as connection:
        sensitivity._require_workspace(connection, workspace_id)
        _validate_sanitizer_ai_job(
            connection,
            sanitizer_kind=sanitizer_kind,
            sanitizer_ai_job_id=sanitizer_ai_job_id,
        )
        resolved = [
            sensitivity._resolve_source_snapshot_and_label_in_connection(
                connection,
                workspace_id,
                source_ref,
            )
            for source_ref in source_refs_tuple
        ]
        source_digests = {
            snapshot.subject_ref: snapshot.content_digest for snapshot, _label in resolved
        }
        source_digests_json = canonical_json(source_digests)
        transformations_json = canonical_json(list(transformations_tuple))
        existing = connection.execute(
            """
            SELECT * FROM sanitized_derivatives
            WHERE workspace_id = ? AND source_digests_json = ?
              AND content_digest = ? AND effective_level = ?
              AND sanitizer_kind = ? AND sanitizer_version = ?
              AND sanitizer_config_digest = ? AND approval_source = ?
              AND auto_approved = 1
            ORDER BY created_at DESC, id ASC
            LIMIT 1
            """,
            (
                workspace_id,
                source_digests_json,
                derivative_digest,
                final_level,
                sanitizer_kind,
                sanitizer_version,
                sanitizer_config_digest,
                approval_source,
            ),
        ).fetchone()
        if existing is not None:
            if existing["status"] != "approved":
                raise sensitivity.SensitivityPolicyError(
                    "A rejected or stale auto-sanitized derivative cannot be reused."
                )
            if existing["content"] != derivative_content:
                raise sensitivity.SensitivityPolicyError(
                    "Canonical derivative digest collision or immutable content mismatch."
                )
            if existing["transformations_json"] != transformations_json:
                raise sensitivity.SensitivityPolicyError(
                    "Canonical derivative provenance mismatch."
                )
            if existing["sanitizer_ai_job_id"] != sanitizer_ai_job_id:
                raise sensitivity.SensitivityPolicyError(
                    "Canonical derivative sanitizer ai_job mismatch."
                )
            derivative_id = str(existing["id"])
            audit_id = _ensure_audit_item(
                connection,
                derivative_kind="canonical",
                derivative_id=derivative_id,
                derivative_digest=derivative_digest,
                workspace_id=workspace_id,
                policy=policy,
                now_dt=now_dt,
            )
            return SanitizerApproval(
                derivative_kind="canonical",
                derivative_id=derivative_id,
                derivative_digest=derivative_digest,
                workspace_id=workspace_id,
                final_level=final_level,
                sanitizer_kind=sanitizer_kind,
                sanitizer_version=sanitizer_version,
                sanitizer_config_digest=sanitizer_config_digest,
                sanitizer_ai_job_id=sanitizer_ai_job_id,
                policy_version=policy.policy_version,
                audit_item_id=audit_id,
                reused=True,
            )

        derivative_id = str(uuid4())
        now_iso = now_dt.isoformat()
        connection.execute(
            """
            INSERT INTO sanitized_derivatives (
                id, workspace_id, source_refs_json, source_digests_json,
                content, content_digest, effective_level, transformations_json,
                policy_version, status, actor, reviewer, reviewed_at,
                stale_reason, created_at, updated_at, sanitizer_kind,
                sanitizer_version, sanitizer_config_digest, sanitizer_ai_job_id,
                approval_source, auto_approved
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'approved',
                      'deterministic-policy', ?, ?, NULL, ?, ?, ?, ?, ?, ?, ?, 1)
            """,
            (
                derivative_id,
                workspace_id,
                canonical_json(list(source_refs_tuple)),
                source_digests_json,
                derivative_content,
                derivative_digest,
                final_level,
                transformations_json,
                sensitivity.POLICY_VERSION,
                approval_source,
                now_iso,
                now_iso,
                now_iso,
                sanitizer_kind,
                sanitizer_version,
                sanitizer_config_digest,
                sanitizer_ai_job_id,
                approval_source,
            ),
        )
        audit_id = _ensure_audit_item(
            connection,
            derivative_kind="canonical",
            derivative_id=derivative_id,
            derivative_digest=derivative_digest,
            workspace_id=workspace_id,
            policy=policy,
            now_dt=now_dt,
        )
        log_event(
            connection,
            event_type="SanitizedDerivativeAutoApproved",
            actor="deterministic-policy",
            target_type="SanitizedDerivative",
            target_id=derivative_id,
            workspace_id=workspace_id,
            payload={
                "source_refs": list(source_refs_tuple),
                "source_digests": source_digests,
                "content_digest": derivative_digest,
                "effective_level": final_level,
                "sanitizer_kind": sanitizer_kind,
                "sanitizer_version": sanitizer_version,
                "sanitizer_config_digest": sanitizer_config_digest,
                "sanitizer_ai_job_id": sanitizer_ai_job_id,
                "approval_source": approval_source,
                "sensitivity_policy_version": sensitivity.POLICY_VERSION,
                "egress_policy_version": policy.policy_version,
                "audit_item_id": audit_id,
            },
        )
        return SanitizerApproval(
            derivative_kind="canonical",
            derivative_id=derivative_id,
            derivative_digest=derivative_digest,
            workspace_id=workspace_id,
            final_level=final_level,
            sanitizer_kind=sanitizer_kind,
            sanitizer_version=sanitizer_version,
            sanitizer_config_digest=sanitizer_config_digest,
            sanitizer_ai_job_id=sanitizer_ai_job_id,
            policy_version=policy.policy_version,
            audit_item_id=audit_id,
            reused=False,
        )


def get_prompt_derivative(
    derivative_id: str,
    *,
    workspace_id: str | None = None,
) -> PromptDerivative:
    derivative_id = _required_text(derivative_id, "derivative_id")
    with open_sqlite_connection() as connection:
        row = connection.execute(
            """
            SELECT * FROM egress_prompt_derivatives
            WHERE id = ? AND workspace_id IS ?
            """,
            (derivative_id, workspace_id),
        ).fetchone()
    if row is None:
        raise sensitivity.SensitivityNotFoundError(
            f"Prompt derivative not found: {derivative_id}"
        )
    return _prompt_derivative_read(row)


def resolve_approved_prompt_derivative(
    *,
    raw_prompt: str,
    workspace_id: str | None = None,
    policy: EgressPolicyConfig | None = None,
) -> PromptDerivative | None:
    policy = policy or load_default_egress_policy()
    raw_prompt = _bounded_text(raw_prompt, "raw_prompt", policy.max_prompt_chars)
    raw_digest = sha256_text(raw_prompt)
    with open_sqlite_connection() as connection:
        row = connection.execute(
            """
            SELECT * FROM egress_prompt_derivatives
            WHERE raw_prompt_digest = ? AND workspace_id IS ?
              AND policy_version = ? AND status = 'approved'
            ORDER BY created_at DESC, id ASC
            LIMIT 1
            """,
            (raw_digest, workspace_id, policy.policy_version),
        ).fetchone()
    if row is None:
        return None
    derivative = _prompt_derivative_read(row)
    _validate_final_content(
        derivative.derivative_content,
        final_level=derivative.final_level,
    )
    if sha256_text(derivative.derivative_content) != derivative.derivative_digest:
        raise sensitivity.SensitivityPolicyError(
            "Prompt derivative content digest mismatch."
        )
    return derivative


def review_sanitizer_audit_item(
    audit_item_id: str,
    *,
    disposition: str,
    reviewer: str = "local-user",
    notes: str | None = None,
    now: datetime | None = None,
) -> SanitizerAuditDisposition:
    """Review one sampled derivative and revoke all unstarted dependent egress work."""

    audit_item_id = _required_text(audit_item_id, "audit_item_id")
    reviewer = _required_text(reviewer, "reviewer")
    if disposition not in _ALLOWED_AUDIT_DISPOSITIONS:
        raise EgressContractError("unsupported sanitizer audit disposition")
    if notes is not None and len(notes) > 2000:
        raise EgressContractError("audit notes exceed 2000 characters")
    now_dt = _normalized_now(now)
    now_iso = now_dt.isoformat()

    with _transaction() as connection:
        audit = connection.execute(
            "SELECT * FROM sanitizer_audit_items WHERE id = ?",
            (audit_item_id,),
        ).fetchone()
        if audit is None:
            raise sensitivity.SensitivityNotFoundError(
                f"Sanitizer audit item not found: {audit_item_id}"
            )
        if audit["state"] != "pending":
            raise sensitivity.SensitivityPolicyError(
                f"Sanitizer audit item is not pending: {audit['state']}"
            )

        packet_ids: set[str] = set()
        invalidated_packet_count = 0
        revoked_ticket_count = 0
        released_reservation_count = 0
        if disposition == "rejected":
            if audit["derivative_kind"] == "prompt":
                updated = connection.execute(
                    """
                    UPDATE egress_prompt_derivatives
                    SET status = 'revoked', revoked_at = ?,
                        revocation_reason = 'sanitizer_audit_rejected'
                    WHERE id = ? AND derivative_digest = ? AND status = 'approved'
                    """,
                    (now_iso, audit["derivative_id"], audit["derivative_digest"]),
                )
                if updated.rowcount != 1:
                    raise sensitivity.SensitivityPolicyError(
                        "Prompt derivative changed before audit rejection."
                    )
                packet_ids = {
                    str(row["id"])
                    for row in connection.execute(
                        "SELECT id FROM egress_packets WHERE prompt_derivative_id = ?",
                        (audit["derivative_id"],),
                    ).fetchall()
                }
            else:
                updated = connection.execute(
                    """
                    UPDATE sanitized_derivatives
                    SET status = 'revoked', stale_reason = 'sanitizer_audit_rejected',
                        updated_at = ?
                    WHERE id = ? AND content_digest = ? AND status = 'approved'
                      AND auto_approved = 1
                    """,
                    (now_iso, audit["derivative_id"], audit["derivative_digest"]),
                )
                if updated.rowcount != 1:
                    raise sensitivity.SensitivityPolicyError(
                        "Canonical derivative changed before audit rejection."
                    )
                packet_ids = _canonical_derivative_packet_ids(
                    connection,
                    derivative_id=str(audit["derivative_id"]),
                )
            invalidated_packet_count = len(packet_ids)
            if packet_ids:
                placeholders = ", ".join("?" for _ in packet_ids)
                packet_values = tuple(sorted(packet_ids))
                tickets = connection.execute(
                    f"""
                    UPDATE egress_confirmation_tickets
                    SET state = 'revoked', version = version + 1,
                        revoked_at = ?, revocation_reason = 'sanitizer_audit_rejected'
                    WHERE state = 'pending' AND packet_id IN ({placeholders})
                    """,
                    (now_iso, *packet_values),
                )
                revoked_ticket_count = tickets.rowcount
                reservations = connection.execute(
                    f"""
                    UPDATE egress_budget_reservations
                    SET state = 'released', version = version + 1,
                        reconciled_at = ?,
                        reconciliation_status = 'sanitizer_audit_rejected_before_start'
                    WHERE state = 'active' AND decision_id IN (
                        SELECT id FROM egress_decisions
                        WHERE packet_id IN ({placeholders})
                    )
                    """,
                    (now_iso, *packet_values),
                )
                released_reservation_count = reservations.rowcount

        updated = connection.execute(
            """
            UPDATE sanitizer_audit_items
            SET state = ?, reviewed_at = ?, reviewer = ?, notes = ?
            WHERE id = ? AND state = 'pending'
            """,
            (disposition, now_iso, reviewer, notes, audit_item_id),
        )
        if updated.rowcount != 1:
            raise sensitivity.SensitivityPolicyError(
                "Sanitizer audit item changed before review."
            )
        log_event(
            connection,
            event_type="SanitizerAuditReviewed",
            actor=reviewer,
            target_type="SanitizerAuditItem",
            target_id=audit_item_id,
            workspace_id=audit["workspace_id"],
            payload={
                "derivative_kind": audit["derivative_kind"],
                "derivative_id": audit["derivative_id"],
                "derivative_digest": audit["derivative_digest"],
                "disposition": disposition,
                "notes_present": notes is not None,
                "notes_digest": sha256_text(notes) if notes is not None else None,
                "invalidated_packet_count": invalidated_packet_count,
                "revoked_ticket_count": revoked_ticket_count,
                "released_reservation_count": released_reservation_count,
            },
        )
        return SanitizerAuditDisposition(
            audit_item_id=audit_item_id,
            derivative_kind=str(audit["derivative_kind"]),
            derivative_id=str(audit["derivative_id"]),
            derivative_digest=str(audit["derivative_digest"]),
            state=disposition,
            invalidated_packet_count=invalidated_packet_count,
            revoked_ticket_count=revoked_ticket_count,
            released_reservation_count=released_reservation_count,
        )


def _ensure_audit_item(
    connection: sqlite3.Connection,
    *,
    derivative_kind: str,
    derivative_id: str,
    derivative_digest: str,
    workspace_id: str | None,
    policy: EgressPolicyConfig,
    now_dt: datetime,
) -> str | None:
    iso_week = f"{now_dt.isocalendar().year:04d}-W{now_dt.isocalendar().week:02d}"
    if not sanitizer_should_sample(
        derivative_kind=derivative_kind,
        derivative_id=derivative_id,
        derivative_digest=derivative_digest,
        iso_week=iso_week,
        policy_version=policy.policy_version,
        sample_rate_bps=policy.sanitizer_sample_rate_bps,
    ):
        return None
    selection_value = sanitizer_sample_value(
        derivative_kind=derivative_kind,
        derivative_id=derivative_id,
        derivative_digest=derivative_digest,
        iso_week=iso_week,
        policy_version=policy.policy_version,
    )
    existing = connection.execute(
        """
        SELECT id FROM sanitizer_audit_items
        WHERE derivative_kind = ? AND derivative_id = ?
          AND derivative_digest = ? AND iso_week = ? AND policy_version = ?
        """,
        (
            derivative_kind,
            derivative_id,
            derivative_digest,
            iso_week,
            policy.policy_version,
        ),
    ).fetchone()
    if existing is not None:
        return str(existing["id"])
    audit_id = str(uuid4())
    connection.execute(
        """
        INSERT INTO sanitizer_audit_items (
            id, workspace_id, derivative_kind, derivative_id,
            derivative_digest, iso_week, policy_version,
            selection_value, sample_rate_bps, state, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?)
        """,
        (
            audit_id,
            workspace_id,
            derivative_kind,
            derivative_id,
            derivative_digest,
            iso_week,
            policy.policy_version,
            selection_value,
            policy.sanitizer_sample_rate_bps,
            now_dt.isoformat(),
        ),
    )
    return audit_id


def _canonical_derivative_packet_ids(
    connection: sqlite3.Connection,
    *,
    derivative_id: str,
) -> set[str]:
    packet_ids: set[str] = set()
    for row in connection.execute(
        "SELECT id, included_manifest_json FROM egress_packets"
    ).fetchall():
        manifests = json.loads(row["included_manifest_json"])
        if any(
            isinstance(item, dict) and item.get("derivative_id") == derivative_id
            for item in manifests
        ):
            packet_ids.add(str(row["id"]))
    return packet_ids


def _validate_sanitizer_ai_job(
    connection: sqlite3.Connection,
    *,
    sanitizer_kind: str,
    sanitizer_ai_job_id: str | None,
) -> None:
    if sanitizer_kind == "deterministic":
        if sanitizer_ai_job_id is not None:
            raise sensitivity.SensitivityPolicyError(
                "Deterministic sanitizer must not claim an ai_job."
            )
        return
    if sanitizer_ai_job_id is None:
        raise sensitivity.SensitivityPolicyError(
            "Model-backed sanitizer requires an ai_job."
        )
    row = connection.execute(
        """
        SELECT status, selected_route_class, provider_id
        FROM ai_jobs WHERE id = ?
        """,
        (sanitizer_ai_job_id,),
    ).fetchone()
    if row is None:
        raise sensitivity.SensitivityPolicyError("Sanitizer ai_job was not found.")
    route = str(row["selected_route_class"] or "")
    if row["status"] != "completed" or not route.startswith("local:"):
        raise sensitivity.SensitivityPolicyError(
            "Sanitizer ai_job must be a completed local-route attempt."
        )


def _validate_final_content(content: str, *, final_level: str) -> None:
    if final_level not in _ALLOWED_FINAL_LEVELS:
        raise sensitivity.SensitivityPolicyError(
            "Auto-approved sanitizer output must be effective S0 or S1."
        )
    floor = sensitivity.deterministic_floor(content)
    if floor is not None:
        raise sensitivity.SensitivityPolicyError(
            f"Sanitizer output remains external-ineligible at deterministic floor {floor}."
        )


def _validate_provenance(
    *,
    sanitizer_kind: str,
    sanitizer_version: str,
    sanitizer_config_digest: str,
    sanitizer_ai_job_id: str | None,
) -> None:
    if sanitizer_kind not in _ALLOWED_SANITIZER_KINDS:
        raise EgressContractError("unsupported sanitizer_kind")
    _required_text(sanitizer_version, "sanitizer_version")
    _required_text(sanitizer_config_digest, "sanitizer_config_digest")
    if len(sanitizer_config_digest) != 64 or any(
        char not in "0123456789abcdef" for char in sanitizer_config_digest
    ):
        raise EgressContractError(
            "sanitizer_config_digest must be a lowercase SHA-256 digest"
        )
    if sanitizer_ai_job_id is not None:
        _required_text(sanitizer_ai_job_id, "sanitizer_ai_job_id")


def _assert_prompt_derivative_match(
    row: sqlite3.Row,
    *,
    workspace_id: str | None,
    derivative_content: str,
    final_level: str,
    transformations: tuple[str, ...],
    sanitizer_kind: str,
    sanitizer_version: str,
    sanitizer_config_digest: str,
    sanitizer_ai_job_id: str | None,
) -> None:
    expected = {
        "workspace_id": workspace_id,
        "derivative_content": derivative_content,
        "final_level": final_level,
        "transformations_json": canonical_json(list(transformations)),
        "sanitizer_kind": sanitizer_kind,
        "sanitizer_version": sanitizer_version,
        "sanitizer_config_digest": sanitizer_config_digest,
        "sanitizer_ai_job_id": sanitizer_ai_job_id,
    }
    if any(row[key] != value for key, value in expected.items()):
        raise sensitivity.SensitivityPolicyError(
            "Prompt derivative digest collision or immutable provenance mismatch."
        )


def _prompt_derivative_read(row: sqlite3.Row) -> PromptDerivative:
    return PromptDerivative(
        id=str(row["id"]),
        workspace_id=row["workspace_id"],
        raw_prompt_digest=str(row["raw_prompt_digest"]),
        derivative_digest=str(row["derivative_digest"]),
        final_level=str(row["final_level"]),
        transformations=tuple(json.loads(row["transformations_json"])),
        sanitizer_kind=str(row["sanitizer_kind"]),
        sanitizer_version=str(row["sanitizer_version"]),
        sanitizer_config_digest=str(row["sanitizer_config_digest"]),
        sanitizer_ai_job_id=row["sanitizer_ai_job_id"],
        policy_version=str(row["policy_version"]),
        status=str(row["status"]),
        created_at=str(row["created_at"]),
        revoked_at=row["revoked_at"],
        revocation_reason=row["revocation_reason"],
        derivative_content=str(row["derivative_content"]),
    )


def _source_refs(values: list[str] | tuple[str, ...]) -> tuple[str, ...]:
    cleaned = tuple(_required_text(value, "source_ref") for value in values)
    if not cleaned:
        raise EgressContractError("source_refs must not be empty")
    if len(cleaned) > 20:
        raise EgressContractError("source_refs exceeds 20 entries")
    if len(set(cleaned)) != len(cleaned):
        raise EgressContractError("source_refs must not contain duplicates")
    for value in cleaned:
        sensitivity._parse_subject_ref(value)
    return tuple(sorted(cleaned))


def _transformations(values: list[str] | tuple[str, ...]) -> tuple[str, ...]:
    cleaned = tuple(_required_text(value, "transformation") for value in values)
    if not cleaned:
        raise EgressContractError("transformations must not be empty")
    if len(cleaned) > 50:
        raise EgressContractError("transformations exceeds 50 entries")
    return cleaned


def _bounded_text(value: str, field_name: str, maximum: int) -> str:
    cleaned = _required_text(value, field_name)
    if len(cleaned) > maximum:
        raise EgressContractError(f"{field_name} exceeds configured character cap")
    return cleaned


def _required_text(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise EgressContractError(f"{field_name} must be non-empty text")
    return value.strip()


def _require_workspace_if_present(
    connection: sqlite3.Connection,
    workspace_id: str | None,
) -> None:
    if workspace_id is not None:
        sensitivity._require_workspace(connection, workspace_id)


def _normalized_now(value: datetime | None) -> datetime:
    result = value or datetime.now(UTC)
    if result.tzinfo is None:
        raise EgressContractError("now must include timezone information")
    return result.astimezone(UTC)


class _transaction:
    def __enter__(self) -> sqlite3.Connection:
        self._manager = open_sqlite_connection()
        self._connection = self._manager.__enter__()
        self._connection.execute("BEGIN IMMEDIATE")
        return self._connection

    def __exit__(self, exc_type, exc, traceback) -> bool:
        try:
            if exc_type is None:
                self._connection.commit()
            else:
                self._connection.rollback()
        finally:
            self._manager.__exit__(exc_type, exc, traceback)
        return False
