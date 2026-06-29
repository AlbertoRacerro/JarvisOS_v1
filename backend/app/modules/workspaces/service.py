from uuid import uuid4

from app.core.database import open_sqlite_connection
from app.core.repository import optional_row_to_model, row_to_model, rows_to_models
from app.modules.events.service import log_event, utc_now
from app.modules.workspaces.models import WorkspaceCreate, WorkspaceRead

DEFAULT_BLUEREV_WORKSPACE = WorkspaceCreate(
    name="BlueRev Model Foundry",
    slug="bluerev",
    description="Default workspace for early BlueRev engineering model work.",
    status="active",
)


def create_workspace(payload: WorkspaceCreate, *, actor: str = "local-user") -> WorkspaceRead:
    now = utc_now()
    workspace_id = str(uuid4())
    with open_sqlite_connection() as connection:
        connection.execute(
            """
            INSERT INTO workspaces (
                id, name, slug, description, status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                workspace_id,
                payload.name,
                payload.slug,
                payload.description,
                payload.status,
                now,
                now,
            ),
        )
        log_event(
            connection,
            event_type="WorkspaceCreated",
            actor=actor,
            target_type="Workspace",
            target_id=workspace_id,
            workspace_id=workspace_id,
            payload={"slug": payload.slug},
        )
        connection.commit()
        row = connection.execute("SELECT * FROM workspaces WHERE id = ?", (workspace_id,)).fetchone()
    return row_to_model(row, WorkspaceRead)


def list_workspaces() -> list[WorkspaceRead]:
    with open_sqlite_connection() as connection:
        rows = connection.execute("SELECT * FROM workspaces ORDER BY created_at ASC").fetchall()
    return rows_to_models(rows, WorkspaceRead)


def get_workspace(workspace_id: str) -> WorkspaceRead | None:
    with open_sqlite_connection() as connection:
        row = connection.execute("SELECT * FROM workspaces WHERE id = ?", (workspace_id,)).fetchone()
    return optional_row_to_model(row, WorkspaceRead)


def get_workspace_by_slug(slug: str) -> WorkspaceRead | None:
    with open_sqlite_connection() as connection:
        row = connection.execute("SELECT * FROM workspaces WHERE slug = ?", (slug,)).fetchone()
    return optional_row_to_model(row, WorkspaceRead)


def seed_default_workspace() -> WorkspaceRead:
    existing = get_workspace_by_slug(DEFAULT_BLUEREV_WORKSPACE.slug)
    if existing:
        return existing

    now = utc_now()
    with open_sqlite_connection() as connection:
        connection.execute(
            """
            INSERT INTO workspaces (
                id, name, slug, description, status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "bluerev",
                DEFAULT_BLUEREV_WORKSPACE.name,
                DEFAULT_BLUEREV_WORKSPACE.slug,
                DEFAULT_BLUEREV_WORKSPACE.description,
                DEFAULT_BLUEREV_WORKSPACE.status,
                now,
                now,
            ),
        )
        log_event(
            connection,
            event_type="WorkspaceCreated",
            actor="system",
            target_type="Workspace",
            target_id="bluerev",
            workspace_id="bluerev",
            payload={"seed": "default"},
        )
        connection.commit()

    seeded = get_workspace("bluerev")
    if seeded is None:
        raise RuntimeError("Default workspace seed failed.")
    return seeded


def get_default_workspace() -> WorkspaceRead:
    existing = get_workspace_by_slug(DEFAULT_BLUEREV_WORKSPACE.slug)
    if existing:
        return existing
    return WorkspaceRead(
        id="bluerev",
        name=DEFAULT_BLUEREV_WORKSPACE.name,
        slug=DEFAULT_BLUEREV_WORKSPACE.slug,
        description=DEFAULT_BLUEREV_WORKSPACE.description,
        status="not_initialized",
        created_at="",
        updated_at="",
    )
