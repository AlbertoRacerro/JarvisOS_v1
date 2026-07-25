from __future__ import annotations

from app.modules.bluecad.builders import build_part
from app.modules.bluecad.service import build_geometry_spec


def _tube_spec() -> dict[str, object]:
    return {
        "spec_version": "bluecad_geometry_spec_v0_1",
        "name": "spawn_isolation_probe",
        "parts": [
            {
                "part_id": "probe_tube",
                "kind": "tube_run",
                "params": {
                    "outer_d": 20.0,
                    "wall_t": 2.0,
                    "length": 100.0,
                },
            }
        ],
        "connections": [],
    }


def test_build_worker_survives_parent_kernel_initialization(tmp_path) -> None:
    spec = _tube_spec()
    build_part(spec["parts"][0])

    result = build_geometry_spec(spec, tmp_path / "build", timeout_s=20.0)

    assert result.verdict == "pass", result.report
    assert result.manifest_path is not None and result.manifest_path.is_file()
    assert result.report_path is not None and result.report_path.is_file()
    assert (tmp_path / "build" / "model.step").is_file()
    assert (tmp_path / "build" / "model.stl").is_file()
    assert (tmp_path / "build" / "model.glb").is_file()
