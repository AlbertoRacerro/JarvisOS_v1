#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "frontend/src/App.tsx"
REGISTRY = ROOT / "frontend/src/stages/registry.ts"
STAGE = ROOT / "frontend/src/stages/FlowsheetStage.tsx"
CLIENT = ROOT / "frontend/src/api/client.ts"
API = ROOT / "frontend/src/components/lineage/api.ts"
STATE = ROOT / "frontend/src/components/lineage/state.ts"
SELECTION = ROOT / "frontend/src/app/selection.ts"
STATUS = ROOT / "docs/specs/STATUS.md"


def fail(message: str) -> None:
    raise SystemExit(f"LINEAGE-OVERVIEW-1 check failed: {message}")


def require(text: str, needle: str, label: str) -> None:
    if needle not in text:
        fail(f"missing {label}: {needle}")


def request_accepts(current: tuple[int, str, str | None] | None, request: tuple[int, str, str | None]) -> bool:
    return current == request


def ordered(nodes: list[str], topo: list[str] | None, acyclic: bool) -> list[str]:
    if not acyclic or topo is None:
        return list(nodes)
    seen: set[str] = set()
    result: list[str] = []
    for ref in topo:
        if ref in nodes and ref not in seen:
            result.append(ref)
            seen.add(ref)
    result.extend(ref for ref in nodes if ref not in seen)
    return result


def mapped(kind: str) -> str | None:
    return {
        "model_spec": "model-spec",
        "assumption": "assumption",
        "parameter": "parameter",
        "simulation_run": "simulation-run",
        "decision": "decision",
        "bluecad_candidate": "bluecad-candidate",
    }.get(kind)


def self_test() -> None:
    late_a = (1, "workspace-a", None)
    current_a = (3, "workspace-a", None)
    if request_accepts(current_a, late_a):
        fail("self-test accepted stale A→B→A graph response")
    late_x = (4, "workspace-a", "parameter:x")
    current_x = (6, "workspace-a", "parameter:x")
    if request_accepts(current_x, late_x):
        fail("self-test accepted stale X→Y→X node response")
    if not request_accepts(current_x, current_x):
        fail("self-test rejected exact current request")
    if ordered(["b", "a", "c"], ["a", "b"], True) != ["a", "b", "c"]:
        fail("self-test deterministic topological ordering failed")
    if ordered(["b", "a"], ["a", "b"], False) != ["b", "a"]:
        fail("self-test cyclic ordering must preserve response order")
    if ordered(["b", "a"], None, True) != ["b", "a"]:
        fail("self-test nullable topological order must preserve response order")
    if mapped("parameter") != "parameter" or mapped("artifact") is not None:
        fail("self-test selection mapping boundary failed")


def check() -> None:
    for path in (APP, REGISTRY, STAGE, CLIENT, API, STATE, SELECTION, STATUS):
        if not path.exists():
            fail(f"missing required file {path.relative_to(ROOT)}")

    app = APP.read_text(encoding="utf-8")
    registry = REGISTRY.read_text(encoding="utf-8")
    stage = STAGE.read_text(encoding="utf-8")
    client = CLIENT.read_text(encoding="utf-8")
    api = API.read_text(encoding="utf-8")
    state = STATE.read_text(encoding="utf-8")
    selection = SELECTION.read_text(encoding="utf-8")
    status = STATUS.read_text(encoding="utf-8")

    for placeholder in ("Lineage is future work under spec 087", "Editable flowsheets are unavailable"):
        if placeholder in stage:
            fail("Flowsheet stage is still placeholder-only")

    for needle, label in (
        ("getLineageGraph", "typed graph client"),
        ("getLineageNode", "typed node client"),
        ("getLineageFreshness", "typed freshness client"),
        ('topological_order: string[] | null', "nullable backend topological order"),
        ('edge_class: \"dependency\" | \"provenance\"', "edge-class union"),
        ('state: \"fresh\" | \"stale\"', "freshness union"),
    ):
        require(api, needle, label)

    for needle, label in (
        ("acceptsLineageResponse", "request-generation guard"),
        ("orderedLineageNodes", "deterministic ordering helper"),
        ("stageSelectionForLineageNode", "bounded selection mapping"),
        ("nodeMatchesFilter", "presentation-only filter helper"),
    ):
        require(state, needle, label)

    for needle, label in (
        ("Dependency & provenance", "lineage product label"),
        ("Upstream", "upstream semantics"),
        ("Downstream", "downstream semantics"),
        ("dependency", "dependency text semantics"),
        ("provenance", "provenance text semantics"),
        ("Freshness", "freshness inspector"),
        ("Cycles present", "cycle diagnostics"),
        ("aria-pressed", "selected-node semantics"),
        ("hidden by the current filter", "hidden-selection explanation"),
        ("LineageRequestError", "404 drift handling"),
        ("listWorkspaces", "workspace discovery"),
        ("workspaceDiscoveryGeneration", "stale workspace-discovery guard"),
        ("requestWorkspaceChange", "shell workspace change path"),
        ("No workspaces are available.", "workspace empty state"),
        ("Workspace discovery failed", "workspace failure state"),
    ):
        require(stage, needle, label)

    require(client, "export function listWorkspaces()", "existing shared workspace client")
    require(registry, "onWorkspaceChange(next: string | null): void", "typed primary-stage workspace callback")
    require(app, "const [workspaceId, setWorkspaceId] = useState<string | null>(null)", "transient App workspace owner")
    require(app, "workspaceId={workspaceId}", "primary-stage workspace binding")
    require(app, "onWorkspaceChange={setWorkspaceId}", "primary-stage workspace callback binding")
    if "workspaceId={null}" in app:
        fail("primary stages remain permanently bound to null workspace")

    forbidden_controls = ("recompute", "rerun", "clear stale", "promote to decision")
    lowered = stage.lower()
    for phrase in forbidden_controls:
        if phrase in lowered:
            fail(f"forbidden mutation control/text present: {phrase}")

    fake_authority = ("confidence score", "health score", "impact score", "recompute estimate")
    for phrase in fake_authority:
        if phrase in lowered:
            fail(f"invented authority present: {phrase}")

    expected_selection = (
        '"workspace"', '"model-spec"', '"assumption"', '"parameter"',
        '"simulation-run"', '"decision"', '"bluecad-candidate"'
    )
    for value in expected_selection:
        require(selection, value, "preserved RecordResource taxonomy")
    for forbidden in ('"artifact"', '"runner-job"', '"evidence"', '"bluecad-attempt"'):
        if forbidden in selection:
            fail(f"087 expanded global RecordResource taxonomy with {forbidden}")

    lifecycle_ok = (
        "| 087 | in_review |" in status
        or "| 087 | ready | — |" in status
        or "| 087 | merged | [#250](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/250) |" in status
    )
    if not lifecycle_ok:
        fail("registry lifecycle for 087 is not a canonical readiness, implementation, or merged state")

    self_test()
    print("LINEAGE-OVERVIEW-1 check passed")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        print("LINEAGE-OVERVIEW-1 self-test passed")
        return
    check()


if __name__ == "__main__":
    main()
