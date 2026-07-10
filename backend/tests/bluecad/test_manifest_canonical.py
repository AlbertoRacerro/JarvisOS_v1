from __future__ import annotations

import hashlib
from pathlib import Path

from app.modules.bluecad.export import ARTIFACT_NAMES, _manifest, sha256_file
from app.modules.bluecad.models import BuiltPart, PortFrame
from app.modules.bluecad.spec import canonical_json


class _Shape:
    is_valid = True
    is_manifold = True


def _parts() -> dict[str, BuiltPart]:
    return {
        "tube1": BuiltPart(
            part_id="tube1",
            kind="tube_run",
            volume_mm3=123.456,
            bbox_mm=((0.0, -5.0, -5.0), (100.0, 5.0, 5.0)),
            ports={
                "port_a": PortFrame((0.0, 0.0, 0.0), (-1.0, 0.0, 0.0), outer_d=10.0, wall_t=1.0),
                "port_b": PortFrame((100.0, 0.0, 0.0), (1.0, 0.0, 0.0), outer_d=10.0, wall_t=1.0),
            },
            shape=_Shape(),
        )
    }


def test_canonical_manifest_excludes_runtime_timing_and_preserves_artifact_integrity(tmp_path: Path) -> None:
    for index, name in enumerate(ARTIFACT_NAMES, start=1):
        (tmp_path / name).write_bytes(f"stable-{index}-{name}\n".encode())

    spec = {"spec_id": "sha256:" + "1" * 64}
    first = _manifest(spec, _parts(), tmp_path)
    second = _manifest(spec, _parts(), tmp_path)

    assert first == second
    assert "timing" not in first
    for name in ARTIFACT_NAMES:
        path = tmp_path / name
        assert first["artifacts"][name] == {
            "sha256": sha256_file(path),
            "bytes": path.stat().st_size,
        }
    payload = {key: value for key, value in first.items() if key != "manifest_digest"}
    assert first["manifest_digest"] == hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()
