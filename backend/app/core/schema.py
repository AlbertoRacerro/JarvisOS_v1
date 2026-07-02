SCHEMA_BASELINE_MIGRATION_ID = "0001_foundation_baseline"
SCHEMA_BASELINE_MIGRATION_NAME = "Foundation schema through Python Runner V0"
SCHEMA_DATA_INFRASTRUCTURE_MIGRATION_ID = "0002_data_infrastructure_hardening"
SCHEMA_DATA_INFRASTRUCTURE_MIGRATION_NAME = "0E-B schema tracking, indexes, and artifact readback"
SCHEMA_AI_POLICY_MIGRATION_ID = "0003_ai_policy_mode_foundation"
SCHEMA_AI_POLICY_MIGRATION_NAME = "0E-D3 pragmatic AI policy mode foundation"
CURRENT_SCHEMA_MIGRATION_ID = "0004_engineering_record_schema_freeze"
CURRENT_SCHEMA_MIGRATION_NAME = "Parameter, assumption, and requirement schema freeze"

SCHEMA_MIGRATION_RECORDS = [
    {
        "migration_id": SCHEMA_BASELINE_MIGRATION_ID,
        "name": SCHEMA_BASELINE_MIGRATION_NAME,
        "checksum": None,
    },
    {
        "migration_id": SCHEMA_DATA_INFRASTRUCTURE_MIGRATION_ID,
        "name": SCHEMA_DATA_INFRASTRUCTURE_MIGRATION_NAME,
        "checksum": None,
    },
    {
        "migration_id": SCHEMA_AI_POLICY_MIGRATION_ID,
        "name": SCHEMA_AI_POLICY_MIGRATION_NAME,
        "checksum": None,
    },
    {
        "migration_id": CURRENT_SCHEMA_MIGRATION_ID,
        "name": CURRENT_SCHEMA_MIGRATION_NAME,
        "checksum": None,
    },
]

SCHEMA_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS schema_migrations (
        migration_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        applied_at TEXT NOT NULL,
        checksum TEXT,
        status TEXT NOT NULL DEFAULT 'applied'
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS workspaces (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        slug TEXT NOT NULL UNIQUE,
        description TEXT,
        status TEXT NOT NULL DEFAULT 'active',
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS entities (
        id TEXT PRIMARY KEY,
        workspace_id TEXT NOT NULL,
        entity_type TEXT NOT NULL,
        title TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'active',
        maturity_status TEXT NOT NULL DEFAULT 'draft',
        schema_version INTEGER NOT NULL DEFAULT 1,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        raw_payload TEXT,
        FOREIGN KEY (workspace_id) REFERENCES workspaces(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS entity_links (
        id TEXT PRIMARY KEY,
        workspace_id TEXT NOT NULL,
        source_entity_id TEXT NOT NULL,
        target_entity_id TEXT NOT NULL,
        link_type TEXT NOT NULL,
        confidence REAL,
        created_at TEXT NOT NULL,
        notes TEXT,
        FOREIGN KEY (workspace_id) REFERENCES workspaces(id),
        FOREIGN KEY (source_entity_id) REFERENCES entities(id),
        FOREIGN KEY (target_entity_id) REFERENCES entities(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS events (
        id TEXT PRIMARY KEY,
        workspace_id TEXT,
        event_type TEXT NOT NULL,
        actor TEXT NOT NULL,
        target_type TEXT NOT NULL,
        target_id TEXT,
        payload TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY (workspace_id) REFERENCES workspaces(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS artifacts (
        id TEXT PRIMARY KEY,
        workspace_id TEXT NOT NULL,
        filename TEXT NOT NULL,
        stored_path TEXT NOT NULL,
        artifact_type TEXT NOT NULL,
        mime_type TEXT,
        sha256 TEXT,
        source_ref TEXT,
        status TEXT NOT NULL DEFAULT 'registered',
        created_at TEXT NOT NULL,
        notes TEXT,
        FOREIGN KEY (workspace_id) REFERENCES workspaces(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS model_specs (
        id TEXT PRIMARY KEY,
        workspace_id TEXT NOT NULL,
        title TEXT NOT NULL,
        engineering_question TEXT NOT NULL,
        scope TEXT,
        status TEXT NOT NULL DEFAULT 'draft',
        maturity_status TEXT NOT NULL DEFAULT 'draft',
        assumptions_summary TEXT,
        inputs_summary TEXT,
        outputs_summary TEXT,
        raw_payload TEXT,
        schema_version INTEGER NOT NULL DEFAULT 1,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (workspace_id) REFERENCES workspaces(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS assumptions (
        id TEXT PRIMARY KEY,
        workspace_id TEXT NOT NULL,
        statement TEXT NOT NULL,
        scope TEXT,
        confidence TEXT,
        status TEXT NOT NULL DEFAULT 'proposed',
        source_ref TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        notes TEXT,
        FOREIGN KEY (workspace_id) REFERENCES workspaces(id)
    )
    """,

    """
    CREATE TABLE IF NOT EXISTS requirements (
        id TEXT PRIMARY KEY,
        workspace_id TEXT NOT NULL,
        statement TEXT NOT NULL,
        rationale TEXT,
        status TEXT NOT NULL DEFAULT 'draft',
        notes TEXT,
        schema_version INTEGER NOT NULL DEFAULT 1,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (workspace_id) REFERENCES workspaces(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS parameters (
        id TEXT PRIMARY KEY,
        workspace_id TEXT NOT NULL,
        name TEXT NOT NULL,
        symbol TEXT,
        value TEXT,
        unit TEXT NOT NULL DEFAULT 'unspecified',
        value_status TEXT NOT NULL DEFAULT 'candidate',
        value_min REAL,
        value_max REAL,
        source_ref TEXT,
        confidence REAL,
        status TEXT NOT NULL DEFAULT 'draft',
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        notes TEXT,
        FOREIGN KEY (workspace_id) REFERENCES workspaces(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS model_versions (
        id TEXT PRIMARY KEY,
        workspace_id TEXT NOT NULL,
        model_spec_id TEXT NOT NULL,
        version_label TEXT NOT NULL,
        implementation_artifact_id TEXT,
        status TEXT NOT NULL DEFAULT 'draft',
        changelog TEXT,
        created_at TEXT NOT NULL,
        notes TEXT,
        FOREIGN KEY (workspace_id) REFERENCES workspaces(id),
        FOREIGN KEY (model_spec_id) REFERENCES model_specs(id),
        FOREIGN KEY (implementation_artifact_id) REFERENCES artifacts(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS simulation_runs (
        id TEXT PRIMARY KEY,
        workspace_id TEXT NOT NULL,
        model_version_id TEXT,
        run_label TEXT,
        status TEXT NOT NULL DEFAULT 'planned',
        input_payload TEXT,
        parameter_payload TEXT,
        output_payload TEXT,
        started_at TEXT,
        completed_at TEXT,
        created_at TEXT NOT NULL,
        notes TEXT,
        FOREIGN KEY (workspace_id) REFERENCES workspaces(id),
        FOREIGN KEY (model_version_id) REFERENCES model_versions(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS runner_jobs (
        id TEXT PRIMARY KEY,
        workspace_id TEXT NOT NULL,
        simulation_run_id TEXT NOT NULL UNIQUE,
        runner_type TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'queued',
        script_path TEXT NOT NULL,
        script_sha256 TEXT NOT NULL,
        command_json TEXT,
        environment_json TEXT,
        working_dir TEXT NOT NULL,
        input_file TEXT,
        output_dir TEXT NOT NULL,
        timeout_seconds INTEGER NOT NULL,
        max_stdout_bytes INTEGER NOT NULL,
        max_stderr_bytes INTEGER NOT NULL,
        max_output_json_bytes INTEGER NOT NULL,
        max_artifact_bytes INTEGER NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (workspace_id) REFERENCES workspaces(id),
        FOREIGN KEY (simulation_run_id) REFERENCES simulation_runs(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS run_logs (
        id TEXT PRIMARY KEY,
        workspace_id TEXT NOT NULL,
        simulation_run_id TEXT NOT NULL,
        stream TEXT NOT NULL,
        content TEXT NOT NULL,
        truncated INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL,
        FOREIGN KEY (workspace_id) REFERENCES workspaces(id),
        FOREIGN KEY (simulation_run_id) REFERENCES simulation_runs(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS run_artifacts (
        id TEXT PRIMARY KEY,
        workspace_id TEXT NOT NULL,
        simulation_run_id TEXT NOT NULL,
        artifact_id TEXT NOT NULL,
        role TEXT NOT NULL,
        created_at TEXT NOT NULL,
        notes TEXT,
        FOREIGN KEY (workspace_id) REFERENCES workspaces(id),
        FOREIGN KEY (simulation_run_id) REFERENCES simulation_runs(id),
        FOREIGN KEY (artifact_id) REFERENCES artifacts(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS decisions (
        id TEXT PRIMARY KEY,
        workspace_id TEXT NOT NULL,
        title TEXT NOT NULL,
        decision_text TEXT NOT NULL,
        rationale TEXT,
        status TEXT NOT NULL DEFAULT 'draft',
        linked_run_id TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        notes TEXT,
        FOREIGN KEY (workspace_id) REFERENCES workspaces(id),
        FOREIGN KEY (linked_run_id) REFERENCES simulation_runs(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS ai_jobs (
        id TEXT PRIMARY KEY,
        created_at TEXT NOT NULL,
        status TEXT NOT NULL,
        task_kind TEXT NOT NULL,
        requested_route_class TEXT,
        selected_route_class TEXT,
        provider_id TEXT,
        model_id TEXT,
        route_reason_json TEXT NOT NULL,
        prompt_digest TEXT,
        context_digest TEXT,
        context_sources_json TEXT,
        output_digest TEXT,
        input_tokens INTEGER,
        output_tokens INTEGER,
        cost_estimate REAL,
        latency_ms INTEGER,
        error_type TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS ai_settings (
        id TEXT PRIMARY KEY,
        policy_mode TEXT NOT NULL DEFAULT 'FAST_DEV',
        monthly_api_budget_usd REAL NOT NULL DEFAULT 0,
        api_spend_month_to_date_usd REAL NOT NULL DEFAULT 0,
        paid_ai_enabled INTEGER NOT NULL DEFAULT 0,
        default_ai_provider TEXT NOT NULL DEFAULT 'fake',
        default_ai_model TEXT NOT NULL DEFAULT 'fake-modeling-draft-v1',
        provider_mode TEXT NOT NULL DEFAULT 'fake',
        use_fake_provider_when_budget_zero INTEGER NOT NULL DEFAULT 1,
        scaleway_enabled INTEGER NOT NULL DEFAULT 0,
        scaleway_token_cap INTEGER NOT NULL DEFAULT 0,
        scaleway_tokens_month_to_date INTEGER NOT NULL DEFAULT 0,
        scaleway_smoke_test_enabled INTEGER NOT NULL DEFAULT 0,
        scaleway_live_smoke_test_enabled INTEGER NOT NULL DEFAULT 0,
        scaleway_monthly_token_cap INTEGER NOT NULL DEFAULT 500000,
        scaleway_hard_stop_token_cap INTEGER NOT NULL DEFAULT 800000,
        scaleway_free_tier_reference_tokens INTEGER NOT NULL DEFAULT 1000000,
        scaleway_input_tokens_month_to_date INTEGER NOT NULL DEFAULT 0,
        scaleway_output_tokens_month_to_date INTEGER NOT NULL DEFAULT 0,
        smoke_test_mode_enabled INTEGER NOT NULL DEFAULT 0,
        updated_at TEXT NOT NULL
    )
    """,
]

SCHEMA_MIGRATION_STATEMENTS = [
    "ALTER TABLE ai_settings ADD COLUMN policy_mode TEXT NOT NULL DEFAULT 'FAST_DEV'",
    "ALTER TABLE ai_settings ADD COLUMN scaleway_smoke_test_enabled INTEGER NOT NULL DEFAULT 0",
    "ALTER TABLE ai_settings ADD COLUMN scaleway_live_smoke_test_enabled INTEGER NOT NULL DEFAULT 0",
    "ALTER TABLE ai_settings ADD COLUMN scaleway_monthly_token_cap INTEGER NOT NULL DEFAULT 500000",
    "ALTER TABLE ai_settings ADD COLUMN scaleway_hard_stop_token_cap INTEGER NOT NULL DEFAULT 800000",
    "ALTER TABLE ai_settings ADD COLUMN scaleway_free_tier_reference_tokens INTEGER NOT NULL DEFAULT 1000000",
    "ALTER TABLE ai_settings ADD COLUMN scaleway_input_tokens_month_to_date INTEGER NOT NULL DEFAULT 0",
    "ALTER TABLE ai_settings ADD COLUMN scaleway_output_tokens_month_to_date INTEGER NOT NULL DEFAULT 0",
    # Repair (Stage 3-fix): these two columns shipped in CREATE TABLE ai_settings
    # but were omitted from the catch-up migrations above, so a legacy DB created
    # before they existed could never gain them on upgrade. Definitions mirror the
    # current CREATE exactly. Idempotent on fresh DBs via duplicate-column swallow.
    "ALTER TABLE ai_settings ADD COLUMN scaleway_token_cap INTEGER NOT NULL DEFAULT 0",
    "ALTER TABLE ai_settings ADD COLUMN scaleway_tokens_month_to_date INTEGER NOT NULL DEFAULT 0",
    # POS-2: source manifest for context blocks. Legacy DBs created at POS-1 have
    # ai_jobs without this column; this upgrades them in place.
    "ALTER TABLE ai_jobs ADD COLUMN context_sources_json TEXT",
    "ALTER TABLE parameters ADD COLUMN unit TEXT NOT NULL DEFAULT 'unspecified'",
    "ALTER TABLE parameters ADD COLUMN value_status TEXT NOT NULL DEFAULT 'candidate'",
    "ALTER TABLE parameters ADD COLUMN value_min REAL",
    "ALTER TABLE parameters ADD COLUMN value_max REAL",
    "ALTER TABLE parameters ADD COLUMN source_ref TEXT",
    "ALTER TABLE assumptions ADD COLUMN status TEXT NOT NULL DEFAULT 'proposed'",
    "ALTER TABLE assumptions ADD COLUMN confidence TEXT",
]

SCHEMA_INDEX_STATEMENTS = [
    "CREATE INDEX IF NOT EXISTS idx_events_workspace_created_at ON events(workspace_id, created_at)",
    "CREATE INDEX IF NOT EXISTS idx_artifacts_workspace_created_at ON artifacts(workspace_id, created_at)",
    "CREATE INDEX IF NOT EXISTS idx_run_artifacts_workspace_run ON run_artifacts(workspace_id, simulation_run_id)",
    "CREATE INDEX IF NOT EXISTS idx_simulation_runs_workspace_created_at ON simulation_runs(workspace_id, created_at)",
    "CREATE INDEX IF NOT EXISTS idx_simulation_runs_workspace_status ON simulation_runs(workspace_id, status)",
    "CREATE INDEX IF NOT EXISTS idx_runner_jobs_workspace_status ON runner_jobs(workspace_id, status)",
    "CREATE INDEX IF NOT EXISTS idx_model_versions_workspace_model_spec ON model_versions(workspace_id, model_spec_id)",
]
