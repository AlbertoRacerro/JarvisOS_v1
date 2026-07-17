from __future__ import annotations

from pathlib import Path


def replace_exact(path: str, old: str, new: str, expected: int = 1) -> None:
    file_path = Path(path)
    source = file_path.read_text(encoding="utf-8")
    count = source.count(old)
    if count != expected:
        raise RuntimeError(f"{path}: expected {expected} replacement points, found {count}")
    file_path.write_text(source.replace(old, new), encoding="utf-8")


def main() -> None:
    replace_exact(
        "backend/app/modules/ai/execution.py",
        """    provider_id = response.provider_id if response is not None else decision.provider_id
    model_id = response.model_id if response is not None else decision.model_id
""",
        """    provider_id = decision.provider_id or (response.provider_id if response is not None else None)
    model_id = decision.model_id or (response.model_id if response is not None else None)
""",
    )
    replace_exact(
        "backend/app/modules/ai/execution.py",
        """def _create_local_flow(
    *,
    task_kind: str,
    requested_route_class: str | None,
    workspace_id: str | None,
) -> str:
""",
        """def _flow_workspace_id(workspace_id: str | None) -> str | None:
    if workspace_id is None:
        return None
    with open_sqlite_connection() as connection:
        row = connection.execute(
            "SELECT 1 FROM workspaces WHERE id = ?",
            (workspace_id,),
        ).fetchone()
    return workspace_id if row is not None else None


def _create_local_flow(
    *,
    task_kind: str,
    requested_route_class: str | None,
    workspace_id: str | None,
) -> str:
""",
    )
    replace_exact(
        "backend/app/modules/ai/execution.py",
        """        requested_route_class=_flow_requested_route(requested_route_class),
        workspace_id=workspace_id,
""",
        """        requested_route_class=_flow_requested_route(requested_route_class),
        workspace_id=_flow_workspace_id(workspace_id),
""",
    )

    old_bindings = '''def _bindings() -> dict[str, ProviderBinding]:
    return {route: ProviderBinding(route, "scaleway", "scripted", False, 4000) for route in ["external:cheap", "external:reasoning"]}
'''
    new_bindings = '''def _bindings() -> dict[str, ProviderBinding]:
    return {
        route: ProviderBinding(
            route,
            "scaleway",
            "scripted",
            False,
            4000,
            execution_class="synthetic",
            context_window_tokens=8192,
        )
        for route in ["external:cheap", "external:reasoning"]
    }
'''
    replace_exact("backend/tests/bluecad/test_loop_stage2.py", old_bindings, new_bindings)
    replace_exact("backend/tests/bluecad/test_loop_sim_wire.py", old_bindings, new_bindings)

    replace_exact(
        "backend/tests/test_alpha_gate_enforcement.py",
        '''    binding = ProviderBinding(
        "external:fixture",
        "fixture",
        "scripted",
        False,
        128,
    )
''',
        '''    binding = ProviderBinding(
        "external:fixture",
        "fixture",
        "scripted",
        False,
        128,
        execution_class="synthetic",
        context_window_tokens=4096,
    )
''',
    )


if __name__ == "__main__":
    main()
