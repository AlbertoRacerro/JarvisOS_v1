from uuid import uuid4

from app.core.database import open_sqlite_connection
from app.modules.engineering.models import (
    EngineeringBoundary,
    EntityCreate,
    EntityLinkCreate,
    EntityLinkRead,
    EntityRead,
)
from app.modules.events.service import utc_now


def create_entity(workspace_id: str, payload: EntityCreate) -> EntityRead:
    now = utc_now()
    record_id = str(uuid4())
    with open_sqlite_connection() as connection:
        connection.execute(
            """
            INSERT INTO entities (
                id, workspace_id, entity_type, title, status, maturity_status,
                schema_version, created_at, updated_at, raw_payload
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record_id,
                workspace_id,
                payload.entity_type,
                payload.title,
                payload.status,
                payload.maturity_status,
                1,
                now,
                now,
                payload.raw_payload,
            ),
        )
        connection.commit()
        row = connection.execute("SELECT * FROM entities WHERE id = ?", (record_id,)).fetchone()
    return EntityRead(**dict(row))


def create_entity_link(workspace_id: str, payload: EntityLinkCreate) -> EntityLinkRead:
    record_id = str(uuid4())
    created_at = utc_now()
    with open_sqlite_connection() as connection:
        connection.execute(
            """
            INSERT INTO entity_links (
                id, workspace_id, source_entity_id, target_entity_id,
                link_type, confidence, created_at, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record_id,
                workspace_id,
                payload.source_entity_id,
                payload.target_entity_id,
                payload.link_type,
                payload.confidence,
                created_at,
                payload.notes,
            ),
        )
        connection.commit()
        row = connection.execute("SELECT * FROM entity_links WHERE id = ?", (record_id,)).fetchone()
    return EntityLinkRead(**dict(row))


def describe_engineering_boundary() -> EngineeringBoundary:
    return EngineeringBoundary(
        id="architecture-spine",
        entity_type="placeholder",
        title="Engineering objects will be introduced in later milestones.",
    )
