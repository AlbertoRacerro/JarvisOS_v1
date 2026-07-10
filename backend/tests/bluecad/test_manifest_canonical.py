from __future__ import annotations

import hashlib

from app.modules.bluecad.export import _manifest
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


def test_canonical_manifest_excludes_runtime_and_binary_serialization_noise() -> None:
    spec = {"spec_id": "sha256:" + "1" * 64}
    first = _manifest(spec, _parts())
    second = _manifest(spec, _parts())

    assert first == second
    assert "timing" not in first
    assert first["artifacts"] == {
        "model.step": {"role": "step"},
        "model.stl": {"role": "stl"},
        "model.glb": {"role": "glb"},
    }
    assert all("sha256" not in metadata and "bytes" not in metadata for metadata in first["artifacts"].values())
    payload = {key: value for key, value in first.items() if key != "manifest_digest"}
    assert first["manifest_digest"] == hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()
