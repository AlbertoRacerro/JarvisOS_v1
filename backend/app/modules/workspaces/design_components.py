"""Version-scoped Design component tree with optimistic edits."""

import math
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, ValidationError

from app.core.database import open_sqlite_connection
from app.modules.bluecad.template import TemplateError, TubeTemplateCreate, create_template_candidate
from app.modules.events.service import log_event, utc_now
from app.modules.process_stack import draft
from app.modules.process_stack.draft import DraftError

router = APIRouter(
    prefix="/workspaces/{project_id}/design-versions/{version_id}/components",
    tags=["design"],
)


class ComponentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    parent_id: str | None = None
    expected_active_version_id: str


class ComponentEdit(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    parent_id: str | None = None
    expected_revision: int = Field(ge=1)
    expected_active_version_id: str


class ComponentRead(BaseModel):
    id: str
    project_id: str
    version_id: str
    parent_id: str | None
    name: str
    revision: int
    created_at: str
    updated_at: str
    source_draft_id: str | None = None
    source_unit_id: str | None = None
    geometry_candidate_id: str | None = None
    geometry_source_draft_revision: str | None = None


class UnitEntry(BaseModel):
    draft_id: str
    unit_id: str
    expected_draft_revision: str
    expected_active_version_id: str


class GeometryAttachment(BaseModel):
    candidate_id: str
    expected_revision: int = Field(ge=1)
    expected_active_version_id: str
    expected_draft_revision: str | None = None


class ProcessGeometryHandoff(BaseModel):
    wall_t_mm: float = Field(gt=0)
    expected_revision: int = Field(ge=1)
    expected_active_version_id: str
    expected_draft_revision: str


class ProcessGeometryMapping(BaseModel):
    supported: bool
    unit_type: str
    template: str | None = None
    inner_d_mm: float | None = None
    length_mm: float | None = None
    basis: str
    draft_revision: str


def _si(unit: dict, key: str) -> float | None:
    value = (unit.get("params") or {}).get(key)
    return float(value["si"]) if isinstance(value, dict) and value.get("si") is not None else None


def _tube_mapping(unit: dict, draft_revision: str) -> ProcessGeometryMapping:
    """Map typed Process unit parameters onto the BlueCad tube template, or say why not."""

    kind = unit.get("type", "")
    inner = length = None
    if kind == "PhotobioreactorT1":
        inner, length = _si(unit, "tube_inner_diameter"), _si(unit, "tube_length")
        basis = "One representative PBR tube from tube_inner_diameter and tube_length; tube_count and layout are not modelled."
    elif kind == "PFR":
        volume, length = _si(unit, "volume"), _si(unit, "length")
        inner = math.sqrt(4 * volume / (math.pi * length)) if volume and length else None
        basis = "PFR as one straight tube; inner diameter derived as sqrt(4·volume/(π·length))."
    else:
        return ProcessGeometryMapping(
            supported=False, unit_type=kind, draft_revision=draft_revision,
            basis=f"No parametric BlueCad geometry mapping exists for Process unit type {kind or 'unknown'} yet.",
        )
    if not inner or not length:
        return ProcessGeometryMapping(
            supported=False, unit_type=kind, draft_revision=draft_revision,
            basis="The Process unit is missing the typed dimensions this mapping needs.",
        )
    return ProcessGeometryMapping(
        supported=True, unit_type=kind, template="tube", inner_d_mm=inner * 1000, length_mm=length * 1000,
        basis=basis, draft_revision=draft_revision,
    )


def _process_unit(connection, project_id: str, version_id: str, component_id: str) -> tuple[str, dict, str]:
    _component(connection, project_id, version_id, component_id)
    source = connection.execute(
        "SELECT draft_id, unit_id FROM design_component_units WHERE component_id = ?", (component_id,)
    ).fetchone()
    if source is None:
        raise HTTPException(422, detail="This component has no Process unit source.")
    version = connection.execute(
        "SELECT data_workspace_id FROM design_project_versions WHERE id = ? AND project_id = ?",
        (version_id, project_id),
    ).fetchone()
    try:
        process = draft.projection(version["data_workspace_id"], source["draft_id"])
    except DraftError as error:
        raise HTTPException(error.status, detail=str(error)) from error
    unit = next((item for item in process["objects"] if item["id"] == source["unit_id"]
                 and item["kind"] == "unit"), None)
    if unit is None:
        raise HTTPException(404, detail="Process unit not found in this version.")
    return version["data_workspace_id"], unit, process["revision"]


def _read_component(connection, row) -> ComponentRead:
    source = connection.execute(
        "SELECT draft_id, unit_id FROM design_component_units WHERE component_id = ?", (row["id"],)
    ).fetchone()
    geometry = connection.execute(
        "SELECT candidate_id, source_draft_revision FROM design_component_geometry WHERE component_id = ?", (row["id"],)
    ).fetchone()
    return ComponentRead(**dict(row), source_draft_id=source["draft_id"] if source else None,
                         source_unit_id=source["unit_id"] if source else None,
                         geometry_candidate_id=geometry["candidate_id"] if geometry else None,
                         geometry_source_draft_revision=geometry["source_draft_revision"] if geometry else None)


def _active_version(connection, project_id: str, version_id: str, expected: str) -> None:
    row = connection.execute(
        "SELECT id FROM design_project_versions WHERE project_id = ? AND active = 1",
        (project_id,),
    ).fetchone()
    if row is None:
        raise HTTPException(404, detail="Project not found.")
    if row["id"] != expected or row["id"] != version_id:
        raise HTTPException(409, detail="Active Design version changed; reload before editing.")


def _component(connection, project_id: str, version_id: str, component_id: str):
    row = connection.execute(
        "SELECT * FROM design_components WHERE id = ? AND project_id = ? AND version_id = ?",
        (component_id, project_id, version_id),
    ).fetchone()
    if row is None:
        raise HTTPException(404, detail="Component not found in this Design version.")
    return row


def _parent(connection, project_id: str, version_id: str, parent_id: str | None) -> None:
    if parent_id is not None:
        _component(connection, project_id, version_id, parent_id)


@router.get("", response_model=list[ComponentRead])
def list_design_components(project_id: str, version_id: str) -> list[ComponentRead]:
    with open_sqlite_connection() as connection:
        version = connection.execute(
            "SELECT id FROM design_project_versions WHERE project_id = ? AND id = ?",
            (project_id, version_id),
        ).fetchone()
        if version is None:
            raise HTTPException(404, detail="Design version not found in this project.")
        rows = connection.execute(
            "SELECT * FROM design_components WHERE project_id = ? AND version_id = ? ORDER BY created_at, id",
            (project_id, version_id),
        ).fetchall()
        return [_read_component(connection, row) for row in rows]


@router.post("/from-unit", response_model=ComponentRead)
def open_unit_component(project_id: str, version_id: str, payload: UnitEntry) -> ComponentRead:
    with open_sqlite_connection() as connection:
        connection.execute("BEGIN IMMEDIATE")
        _active_version(connection, project_id, version_id, payload.expected_active_version_id)
        version = connection.execute(
            "SELECT data_workspace_id FROM design_project_versions WHERE id = ? AND project_id = ?",
            (version_id, project_id),
        ).fetchone()
        try:
            process = draft.projection(version["data_workspace_id"], payload.draft_id)
        except DraftError as error:
            raise HTTPException(error.status, detail=str(error)) from error
        if process["revision"] != payload.expected_draft_revision:
            raise HTTPException(409, detail="Process draft changed; reload before opening its unit.")
        unit = next((item for item in process["objects"] if item["id"] == payload.unit_id
                     and item["kind"] == "unit"), None)
        if unit is None:
            raise HTTPException(404, detail="Process unit not found in this version.")
        existing = connection.execute(
            "SELECT c.* FROM design_components c JOIN design_component_units u ON u.component_id = c.id "
            "WHERE u.version_id = ? AND u.draft_id = ? AND u.unit_id = ?",
            (version_id, payload.draft_id, payload.unit_id),
        ).fetchone()
        if existing:
            return _read_component(connection, existing)
        component_id, now = str(uuid4()), utc_now()
        connection.execute(
            "INSERT INTO design_components "
            "(id, project_id, version_id, parent_id, name, revision, created_at, updated_at) "
            "VALUES (?, ?, ?, NULL, ?, 1, ?, ?)",
            (component_id, project_id, version_id, unit["tag"], now, now),
        )
        connection.execute(
            "INSERT INTO design_component_units (component_id, version_id, draft_id, unit_id) "
            "VALUES (?, ?, ?, ?)", (component_id, version_id, payload.draft_id, payload.unit_id),
        )
        log_event(connection, event_type="DesignComponentOpenedFromProcess", actor="local-user",
                  target_type="DesignComponent", target_id=component_id, workspace_id=project_id,
                  payload={"version_id": version_id, "draft_id": payload.draft_id,
                           "unit_id": payload.unit_id, "draft_revision": process["revision"]})
        row = _component(connection, project_id, version_id, component_id)
        connection.commit()
        return _read_component(connection, row)


@router.post("", response_model=ComponentRead, status_code=201)
def create_design_component(project_id: str, version_id: str, payload: ComponentCreate) -> ComponentRead:
    name = payload.name.strip()
    if not name:
        raise HTTPException(422, detail="Component name cannot be empty.")
    with open_sqlite_connection() as connection:
        connection.execute("BEGIN IMMEDIATE")
        _active_version(connection, project_id, version_id, payload.expected_active_version_id)
        _parent(connection, project_id, version_id, payload.parent_id)
        component_id, now = str(uuid4()), utc_now()
        connection.execute(
            "INSERT INTO design_components "
            "(id, project_id, version_id, parent_id, name, revision, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, 1, ?, ?)",
            (component_id, project_id, version_id, payload.parent_id, name, now, now),
        )
        log_event(connection, event_type="DesignComponentCreated", actor="local-user",
                  target_type="DesignComponent", target_id=component_id, workspace_id=project_id,
                  payload={"version_id": version_id, "parent_id": payload.parent_id})
        row = _component(connection, project_id, version_id, component_id)
        connection.commit()
        return _read_component(connection, row)


@router.put("/{component_id}", response_model=ComponentRead)
def edit_design_component(
    project_id: str, version_id: str, component_id: str, payload: ComponentEdit,
) -> ComponentRead:
    name = payload.name.strip()
    if not name:
        raise HTTPException(422, detail="Component name cannot be empty.")
    with open_sqlite_connection() as connection:
        connection.execute("BEGIN IMMEDIATE")
        _active_version(connection, project_id, version_id, payload.expected_active_version_id)
        current = _component(connection, project_id, version_id, component_id)
        if current["revision"] != payload.expected_revision:
            raise HTTPException(409, detail="Component changed; reload before editing.")
        _parent(connection, project_id, version_id, payload.parent_id)
        ancestor = payload.parent_id
        while ancestor is not None:
            if ancestor == component_id:
                raise HTTPException(409, detail="Component nesting would create a cycle.")
            ancestor = _component(connection, project_id, version_id, ancestor)["parent_id"]
        connection.execute(
            "UPDATE design_components SET name = ?, parent_id = ?, revision = revision + 1, "
            "updated_at = ? WHERE id = ?",
            (name, payload.parent_id, utc_now(), component_id),
        )
        log_event(connection, event_type="DesignComponentEdited", actor="local-user",
                  target_type="DesignComponent", target_id=component_id, workspace_id=project_id,
                  payload={"version_id": version_id, "revision": payload.expected_revision + 1,
                           "parent_id": payload.parent_id})
        row = _component(connection, project_id, version_id, component_id)
        connection.commit()
        return _read_component(connection, row)


@router.put("/{component_id}/geometry", response_model=ComponentRead)
def attach_component_geometry(
    project_id: str, version_id: str, component_id: str, payload: GeometryAttachment,
) -> ComponentRead:
    with open_sqlite_connection() as connection:
        connection.execute("BEGIN IMMEDIATE")
        _active_version(connection, project_id, version_id, payload.expected_active_version_id)
        current = _component(connection, project_id, version_id, component_id)
        if current["revision"] != payload.expected_revision:
            raise HTTPException(409, detail="Component changed; reload before attaching geometry.")
        version = connection.execute(
            "SELECT data_workspace_id FROM design_project_versions WHERE id = ? AND project_id = ?",
            (version_id, project_id),
        ).fetchone()
        candidate = connection.execute(
            "SELECT id, status FROM bluecad_candidates WHERE id = ? AND workspace_id = ?",
            (payload.candidate_id, version["data_workspace_id"]),
        ).fetchone()
        if candidate is None:
            raise HTTPException(404, detail="BlueCad candidate not found in this Design version.")
        if candidate["status"] != "valid":
            raise HTTPException(409, detail="Only a validated BlueCad candidate can be attached.")
        source = connection.execute(
            "SELECT draft_id FROM design_component_units WHERE component_id = ?", (component_id,)
        ).fetchone()
        if source:
            if payload.expected_draft_revision is None:
                raise HTTPException(422, detail="Process draft revision is required for this component.")
            try:
                process = draft.projection(version["data_workspace_id"], source["draft_id"])
            except DraftError as error:
                raise HTTPException(error.status, detail=str(error)) from error
            if process["revision"] != payload.expected_draft_revision:
                raise HTTPException(409, detail="Process draft changed; reload before attaching geometry.")
        elif payload.expected_draft_revision is not None:
            raise HTTPException(422, detail="This component has no Process draft source.")
        now = utc_now()
        connection.execute(
            "INSERT INTO design_component_geometry (component_id, candidate_id, source_draft_revision, updated_at) "
            "VALUES (?, ?, ?, ?) ON CONFLICT(component_id) DO UPDATE SET candidate_id = excluded.candidate_id, "
            "source_draft_revision = excluded.source_draft_revision, updated_at = excluded.updated_at",
            (component_id, payload.candidate_id, payload.expected_draft_revision, now),
        )
        connection.execute(
            "UPDATE design_components SET revision = revision + 1, updated_at = ? WHERE id = ?", (now, component_id),
        )
        log_event(connection, event_type="DesignComponentGeometryAttached", actor="local-user",
                  target_type="DesignComponent", target_id=component_id, workspace_id=project_id,
                  payload={"version_id": version_id, "candidate_id": payload.candidate_id,
                           "source_draft_revision": payload.expected_draft_revision})
        row = _component(connection, project_id, version_id, component_id)
        connection.commit()
        return _read_component(connection, row)


@router.get("/{component_id}/geometry/process-mapping", response_model=ProcessGeometryMapping)
def process_geometry_mapping(project_id: str, version_id: str, component_id: str) -> ProcessGeometryMapping:
    with open_sqlite_connection() as connection:
        _, unit, revision = _process_unit(connection, project_id, version_id, component_id)
    return _tube_mapping(unit, revision)


@router.post("/{component_id}/geometry/from-process", response_model=ComponentRead)
def deepen_component_geometry(
    project_id: str, version_id: str, component_id: str, payload: ProcessGeometryHandoff,
) -> ComponentRead:
    """Build a template candidate from typed Process dimensions, then attach it through the guarded owner."""

    with open_sqlite_connection() as connection:
        _active_version(connection, project_id, version_id, payload.expected_active_version_id)
        if _component(connection, project_id, version_id, component_id)["revision"] != payload.expected_revision:
            raise HTTPException(409, detail="Component changed; reload before generating geometry.")
        workspace_id, unit, revision = _process_unit(connection, project_id, version_id, component_id)
    if revision != payload.expected_draft_revision:
        raise HTTPException(409, detail="Process draft changed; reload before generating geometry.")
    mapping = _tube_mapping(unit, revision)
    if not mapping.supported:
        raise HTTPException(422, detail=mapping.basis)
    try:
        request = TubeTemplateCreate(template="tube", params={
            "outer_d_mm": mapping.inner_d_mm + 2 * payload.wall_t_mm,
            "wall_t_mm": payload.wall_t_mm, "length_mm": mapping.length_mm,
        })
    except ValidationError as error:
        raise HTTPException(422, detail="Process dimensions are outside the BlueCad tube template range: "
                            + "; ".join(item["msg"] for item in error.errors())) from error
    try:
        candidate = create_template_candidate(workspace_id, request)
    except TemplateError as error:
        raise HTTPException(error.status_code, detail=error.message) from error
    if candidate.status != "valid":
        raise HTTPException(409, detail=f"BlueCad candidate {candidate.id} did not validate; it was not attached.")
    return attach_component_geometry(project_id, version_id, component_id, GeometryAttachment(
        candidate_id=candidate.id, expected_revision=payload.expected_revision,
        expected_active_version_id=payload.expected_active_version_id,
        expected_draft_revision=payload.expected_draft_revision,
    ))
