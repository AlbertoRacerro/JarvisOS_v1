from __future__ import annotations

from pathlib import Path

SERVICE = Path("backend/app/modules/flowsheet/service.py")
TEST = Path("backend/tests/test_cad_link_topology_execute.py")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one target, found {count}")
    return text.replace(old, new, 1)


service = SERVICE.read_text(encoding="utf-8")
service = replace_once(
    service,
    '''        "cad_link": (
            "SELECT source_simulation_run_id, child_candidate_id "
            "FROM bluecad_cad_links WHERE workspace_id = ?"
        ),
''',
    '''        "cad_link": (
            "SELECT source_simulation_run_id, child_candidate_id, transformation_version "
            "FROM bluecad_cad_links WHERE workspace_id = ?"
        ),
''',
    "cad-link row projection",
)
service = replace_once(
    service,
    '''    for row in rows["cad_link"]:
        _add_typed_edge(
            builder,
            "simulation_run",
            row.get("source_simulation_run_id"),
            _ref("bluecad_candidate", row.get("child_candidate_id")),
            "m0_geometry_link",
            "dependency",
            "bluecad_cad_links.source_simulation_run_id",
        )
''',
    '''    for row in rows["cad_link"]:
        relation = (
            "m1_topology_geometry_link"
            if row.get("transformation_version")
            == "bluerev_072_m1_planar_tubing_v0_1"
            else "m0_geometry_link"
        )
        _add_typed_edge(
            builder,
            "simulation_run",
            row.get("source_simulation_run_id"),
            _ref("bluecad_candidate", row.get("child_candidate_id")),
            relation,
            "dependency",
            "bluecad_cad_links.source_simulation_run_id",
        )
''',
    "cad-link lineage relation",
)
SERVICE.write_text(service, encoding="utf-8")

test = TEST.read_text(encoding="utf-8")
marker = '''    second = client.post(
        "/workspaces/bluerev/bluecad/cad-link/072/execute",
        json=request,
    )
'''
insert = '''    from app.modules.flowsheet.service import get_flowsheet_graph

    graph = get_flowsheet_graph("bluerev")
    lineage_edges = [
        edge
        for edge in graph.edges
        if edge.upstream_ref == f"simulation_run:{simulation_run_id}"
        and edge.downstream_ref
        == f"bluecad_candidate:{first_payload['candidate']['id']}"
    ]
    assert len(lineage_edges) == 1
    assert lineage_edges[0].relation == "m1_topology_geometry_link"
    assert lineage_edges[0].edge_class == "dependency"

''' + marker
if "m1_topology_geometry_link" not in test:
    test = replace_once(test, marker, insert, "execute lineage assertion")
TEST.write_text(test, encoding="utf-8")
