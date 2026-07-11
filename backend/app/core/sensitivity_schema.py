"""Additive schema owned by spec 059a.

Kept separate from the historical foundation schema so the policy tables and
migration record remain a bounded, reviewable sidecar.
"""

SENSITIVITY_SCHEMA_MIGRATION_RECORD = {
    "migration_id": "0009_sensitivity_context_foundation",
    "name": "IP egress sensitivity labels and sanitized derivatives",
    "checksum": None,
}

SENSITIVITY_SCHEMA_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS sensitivity_labels (
        id TEXT PRIMARY KEY,
        workspace_id TEXT NOT NULL,
        subject_ref TEXT NOT NULL,
        content_digest TEXT NOT NULL,
        level TEXT NOT NULL CHECK(level IN ('S0', 'S1', 'S2', 'S3', 'S4')),
        classification_source TEXT NOT NULL CHECK(
            classification_source IN ('human', 'deterministic_floor', 'import', 'sanitized_derivative')
        ),
        policy_version TEXT NOT NULL,
        actor TEXT NOT NULL,
        prior_label_id TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY (workspace_id) REFERENCES workspaces(id),
        FOREIGN KEY (prior_label_id) REFERENCES sensitivity_labels(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS sanitized_derivatives (
        id TEXT PRIMARY KEY,
        workspace_id TEXT NOT NULL,
        source_refs_json TEXT NOT NULL,
        source_digests_json TEXT NOT NULL,
        content TEXT NOT NULL,
        content_digest TEXT NOT NULL,
        effective_level TEXT NOT NULL CHECK(effective_level IN ('S0', 'S1', 'S2')),
        transformations_json TEXT NOT NULL,
        policy_version TEXT NOT NULL,
        status TEXT NOT NULL CHECK(status IN ('draft', 'approved', 'revoked', 'stale')),
        actor TEXT NOT NULL,
        reviewer TEXT,
        reviewed_at TEXT,
        stale_reason TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (workspace_id) REFERENCES workspaces(id)
    )
    """,
]

SENSITIVITY_SCHEMA_INDEX_STATEMENTS = [
    "CREATE INDEX IF NOT EXISTS idx_sensitivity_labels_subject_created ON sensitivity_labels(workspace_id, subject_ref, created_at, id)",
    "CREATE INDEX IF NOT EXISTS idx_sanitized_derivatives_workspace_status ON sanitized_derivatives(workspace_id, status, updated_at, id)",
]
