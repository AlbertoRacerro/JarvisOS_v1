"""Zero-write preview for the exact bundled-072 topology CAD link."""

from __future__ import annotations

import sqlite3
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.core.database import open_sqlite_connection
from app.modules.bluecad.cad_link_topology_contract import (
    IMPLEMENTATION_VERSION,
    TRANSFORMATION_VERSION,
    canonicalize_layout,
    resolve_geometry_spec,
)
from app.modules.bluecad.cad_link_topology_preflight import run_kernel_preflight
from app.modules.bluecad.cad_link_topology_reconciliation import (
    TOLERANCES,
    reconcile_topology,
)
from app.modules.bluecad.cad_link_topology_source import (
    GEOMETRY_PARAMETER_INPUTS,
    digest,
    load_topology_source,
)
from app.modules.bluecad.models import BluecadLoopConfig

__all__ = [
    "CadLink072ExecuteRequest",
    "CadLink072PreviewRequest",
    "GEOMETRY_PARAMETER_INPUTS",
    "preview_cad_link_072",
]


class CadLink072PreviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    source_simulation_run_id: str = Field(min_length=1, max_length=256)
    layout_spec: dict[str, Any]
    analysis_spec: dict[str, Any] | None = None

    @model_validator(mode="after")
    def _validate_analysis_spec(self) -> CadLink072PreviewRequest:
        if self.analysis_spec is not None:
            BluecadLoopConfig(analysis_spec=self.analysis_spec)
        return self


class CadLink072ExecuteRequest(CadLink072PreviewRequest):
    preview_digest: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")


def preview_cad_link_072(
    workspace_id: str,
    payload: CadLink072PreviewRequest,
) -> dict[str, Any]:
    """Resolve the exact 072 topology into bounded evidence with zero writes."""

    with open_sqlite_connection() as connection:
        connection.execute("PRAGMA query_only = ON")
        connection.execute("BEGIN")
        try:
            preview = _build_preview(connection, workspace_id, payload)
        finally:
            connection.rollback()
    return preview


def _build_preview(
    connection: sqlite3.Connection,
    workspace_id: str,
    payload: CadLink072PreviewRequest,
) -> dict[str, Any]:
    source = load_topology_source(
        connection,
        workspace_id,
        payload.source_simulation_run_id,
    )
    layout = canonicalize_layout(source["manifest"], payload.layout_spec)
    resolved_spec, boundaries, component_inventory = resolve_geometry_spec(
        source["manifest"],
        layout,
    )
    preflight = run_kernel_preflight(resolved_spec, boundaries)
    process_reconciliation = reconcile_topology(
        source["manifest"],
        layout,
        resolved_spec,
        preflight,
    )
    analysis_contract = _canonical_analysis_contract(payload.analysis_spec)
    layout_digest = digest(layout)
    preflight_digest = digest(preflight)
    reconciliation = {
        "schema_version": "cad_link_072_link_evidence_v0_1",
        "layout_spec": layout,
        "layout_digest": layout_digest,
        "external_boundaries": boundaries,
        "component_inventory": component_inventory,
        "kernel_preflight": preflight,
        "kernel_preflight_digest": preflight_digest,
        "tolerances": dict(TOLERANCES),
        "checks": process_reconciliation["checks"],
        "structural_checks": process_reconciliation["structural_checks"],
        "process_cad_reconciliation": process_reconciliation,
    }

    preview: dict[str, Any] = {
        "workspace_id": workspace_id,
        "source_simulation_run_id": source["simulation_run_id"],
        "source_runner_job_id": source["runner_job_id"],
        "source_model_identity": source["model_identity"],
        "source_model_identity_digest": digest(source["model_identity"]),
        "source_topology_manifest": source["manifest_artifact"],
        "source_geometry_parameters": source["parameter_snapshots"],
        "source_snapshot": source["source_snapshot"],
        "source_snapshot_digest": digest(source["source_snapshot"]),
        "layout_spec": layout,
        "layout_digest": layout_digest,
        "transformation_version": TRANSFORMATION_VERSION,
        "implementation_version": IMPLEMENTATION_VERSION,
        "resolved_spec": resolved_spec,
        "spec_id": resolved_spec["spec_id"],
        "resolved_spec_digest": str(resolved_spec["spec_id"]),
        "resolved_part_count": len(resolved_spec["parts"]),
        "resolved_connection_count": len(resolved_spec.get("connections", [])),
        "external_boundaries": boundaries,
        "component_inventory": component_inventory,
        "kernel_preflight": preflight,
        "kernel_preflight_digest": preflight_digest,
        "tolerances": dict(TOLERANCES),
        "reconciliation": reconciliation,
        "reconciliation_digest": digest(reconciliation),
        "analysis_contract": analysis_contract,
        "analysis_contract_digest": (
            None if analysis_contract is None else digest(analysis_contract)
        ),
    }
    preview["preview_digest"] = digest(preview)
    return preview


def _canonical_analysis_contract(value: dict[str, Any] | None) -> Any:
    return BluecadLoopConfig(analysis_spec=value).analysis_spec
