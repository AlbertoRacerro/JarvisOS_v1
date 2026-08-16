AI_THREAD_SCHEMA_MIGRATION_ID = "0013_ai_threads_0"
AI_THREAD_SCHEMA_MIGRATION_NAME = "Workspace AI thread persistence and canonical flow linkage"
AI_THREAD_SCHEMA_MIGRATION_RECORD = {
    "migration_id": AI_THREAD_SCHEMA_MIGRATION_ID,
    "name": AI_THREAD_SCHEMA_MIGRATION_NAME,
    "checksum": None,
}

AI_THREAD_SCHEMA_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS ai_threads (
        id TEXT PRIMARY KEY,
        workspace_id TEXT NOT NULL,
        title TEXT,
        created_at TEXT NOT NULL,
        last_activity_at TEXT NOT NULL,
        FOREIGN KEY (workspace_id) REFERENCES workspaces(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS ai_thread_interactions (
        id TEXT PRIMARY KEY,
        thread_id TEXT NOT NULL,
        request_id TEXT NOT NULL,
        request_digest TEXT NOT NULL,
        interaction_index INTEGER NOT NULL CHECK (interaction_index >= 0),
        user_text TEXT NOT NULL,
        assistant_text TEXT,
        assistant_text_truncated INTEGER NOT NULL DEFAULT 0
            CHECK (assistant_text_truncated IN (0, 1)),
        flow_id TEXT NOT NULL,
        persistence_state TEXT NOT NULL CHECK (
            persistence_state IN ('reserved', 'dispatching', 'captured', 'capture_failed')
        ),
        persistence_error TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (thread_id) REFERENCES ai_threads(id),
        FOREIGN KEY (flow_id) REFERENCES ai_flows(id),
        UNIQUE(thread_id, request_id),
        UNIQUE(thread_id, interaction_index),
        UNIQUE(flow_id)
    )
    """,
]

AI_THREAD_SCHEMA_INDEX_STATEMENTS = [
    """
    CREATE INDEX IF NOT EXISTS idx_ai_threads_workspace_activity
    ON ai_threads(workspace_id, last_activity_at DESC, id ASC)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_ai_thread_interactions_thread_index
    ON ai_thread_interactions(thread_id, interaction_index)
    """,
]
