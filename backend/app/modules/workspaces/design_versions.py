"""One backend-owned Design version context over existing workspace-scoped engines."""

from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core.database import open_sqlite_connection
from app.modules.events.service import log_event, utc_now

router = APIRouter(prefix="/workspaces/{project_id}/design-versions", tags=["design"])


class VersionCreate(BaseModel):
    label: str = Field(min_length=1, max_length=80)
    expected_active_version_id: str


class VersionActivate(BaseModel):
    version_id: str
    expected_active_version_id: str


class DesignVersion(BaseModel):
    id: str
    project_id: str
    data_workspace_id: str
    parent_version_id: str | None
    label: str
    active: bool
    starts_empty: bool
    created_at: str


class DesignVersionSet(BaseModel):
    project_id: str
    active_version_id: str
    versions: list[DesignVersion]


def _project(connection, project_id: str):
    project = connection.execute(
        "SELECT * FROM workspaces WHERE id = ? AND status != 'design_version'", (project_id,)
    ).fetchone()
    if project is None:
        raise HTTPException(404, detail="Project not found.")
    return project


def _read(connection, project_id: str) -> DesignVersionSet:
    rows = connection.execute(
        "SELECT * FROM design_project_versions WHERE project_id = ? ORDER BY created_at, id", (project_id,)
    ).fetchall()
    versions = [DesignVersion(
        id=row["id"], project_id=row["project_id"], data_workspace_id=row["data_workspace_id"],
        parent_version_id=row["parent_version_id"], label=row["label"], active=bool(row["active"]),
        starts_empty=row["data_workspace_id"] != project_id, created_at=row["created_at"],
    ) for row in rows]
    active = next((version.id for version in versions if version.active), None)
    if active is None:
        raise HTTPException(409, detail="Project has no active Design version.")
    return DesignVersionSet(project_id=project_id, active_version_id=active, versions=versions)


@router.get("", response_model=DesignVersionSet)
def list_design_versions(project_id: str) -> DesignVersionSet:
    with open_sqlite_connection() as connection:
        _project(connection, project_id)
        return _read(connection, project_id)


@router.post("", response_model=DesignVersionSet, status_code=201)
def create_design_version(project_id: str, payload: VersionCreate) -> DesignVersionSet:
    label = payload.label.strip()
    if not label:
        raise HTTPException(422, detail="Version label cannot be empty.")
    with open_sqlite_connection() as connection:
        connection.execute("BEGIN IMMEDIATE")
        project = _project(connection, project_id)
        current = _read(connection, project_id)
        if current.active_version_id != payload.expected_active_version_id:
            raise HTTPException(409, detail="Active Design version changed; reload before creating a version.")
        version_id, workspace_id, now = str(uuid4()), str(uuid4()), utc_now()
        connection.execute(
            "INSERT INTO workspaces (id, name, slug, description, status, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, 'design_version', ?, ?)",
            (workspace_id, f"{project['name']} · {label}", f"design-{workspace_id}",
             "Independent Design version data context", now, now),
        )
        connection.execute(
            "INSERT INTO design_project_versions "
            "(id, project_id, data_workspace_id, parent_version_id, label, active, created_at) "
            "VALUES (?, ?, ?, ?, ?, 0, ?)",
            (version_id, project_id, workspace_id, current.active_version_id, label, now),
        )
        log_event(connection, event_type="DesignVersionCreated", actor="local-user",
                  target_type="DesignVersion", target_id=version_id, workspace_id=project_id,
                  payload={"parent_version_id": current.active_version_id, "starts_empty": True})
        result = _read(connection, project_id)
        connection.commit()
        return result


@router.post("/activate", response_model=DesignVersionSet)
def activate_design_version(project_id: str, payload: VersionActivate) -> DesignVersionSet:
    with open_sqlite_connection() as connection:
        connection.execute("BEGIN IMMEDIATE")
        _project(connection, project_id)
        current = _read(connection, project_id)
        if current.active_version_id != payload.expected_active_version_id:
            raise HTTPException(409, detail="Active Design version changed; reload before switching.")
        if not any(version.id == payload.version_id for version in current.versions):
            raise HTTPException(404, detail="Design version not found in this project.")
        if payload.version_id != current.active_version_id:
            connection.execute("UPDATE design_project_versions SET active = 0 WHERE project_id = ? AND active = 1", (project_id,))
            connection.execute("UPDATE design_project_versions SET active = 1 WHERE id = ? AND project_id = ?",
                               (payload.version_id, project_id))
            log_event(connection, event_type="DesignVersionActivated", actor="local-user",
                      target_type="DesignVersion", target_id=payload.version_id, workspace_id=project_id,
                      payload={"previous_version_id": current.active_version_id})
        result = _read(connection, project_id)
        connection.commit()
        return result
