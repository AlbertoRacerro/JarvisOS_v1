import sqlite3

from fastapi import APIRouter, HTTPException

from app.modules.workspaces.models import WorkspaceCreate, WorkspaceRead
from app.modules.workspaces.service import create_workspace, get_workspace, list_workspaces

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


@router.post("", response_model=WorkspaceRead, status_code=201)
def create_workspace_endpoint(payload: WorkspaceCreate) -> WorkspaceRead:
    try:
        return create_workspace(payload)
    except sqlite3.IntegrityError as exc:
        raise HTTPException(status_code=409, detail="Workspace slug already exists.") from exc


@router.get("", response_model=list[WorkspaceRead])
def list_workspaces_endpoint() -> list[WorkspaceRead]:
    return list_workspaces()


@router.get("/{workspace_id}", response_model=WorkspaceRead)
def get_workspace_endpoint(workspace_id: str) -> WorkspaceRead:
    workspace = get_workspace(workspace_id)
    if workspace is None:
        raise HTTPException(status_code=404, detail="Workspace not found.")
    return workspace
