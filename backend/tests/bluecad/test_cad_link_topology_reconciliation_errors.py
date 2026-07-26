from __future__ import annotations

from typing import Any

import pytest

from app.modules.bluecad import cad_link_topology as topology_module
from app.modules.bluecad.cad_link import CadLinkError
from app.modules.bluecad.cad_link_topology import (
    CadLink072PreviewRequest,
    _build_preview_evidence,
    _require_representable_source_manifold_volumes,
)


def _manifest() -> dict[str, Any]:
    return {
        "executed_inputs": {
            "split_manifold_liquid_volume": {"value": 1.0, "unit": "L"},
            "merge_manifold_liquid_volume": {"value": 1.0, "unit": "L"},
        }
    }


@pytest.mark.parametrize(
    "zero_name",
    ["split_manifold_liquid_volume", "merge_manifold_liquid_volume"],
)
def test_zero_source_manifold_volume_fails_before_layout_or_reconciliation(
    zero_name: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest = _manifest()
    manifest["executed_inputs"][zero_name]["value"] = 0.0
    monkeypatch.setattr(
        topology_module,
        "load_topology_source",
        lambda *_args: {"manifest": manifest},
    )

    def unexpected_layout(*_args: Any, **_kwargs: Any) -> None:
        raise AssertionError("layout resolution must not run for zero manifold volume")

    monkeypatch.setattr(topology_module, "canonicalize_layout", unexpected_layout)
    payload = CadLink072PreviewRequest(
        source_simulation_run_id="zero-manifold-probe",
        layout_spec={},
        analysis_spec=None,
    )

    with pytest.raises(CadLinkError) as exc_info:
        _build_preview_evidence(
            object(),
            "bluerev",
            payload,
            kernel_preflight={},
        )

    assert exc_info.value.code == "cad_link_manifold_volume_unrepresentable"
    assert exc_info.value.status_code == 422


def test_positive_source_manifold_volumes_convert_to_cubic_metres() -> None:
    manifest = _manifest()
    manifest["executed_inputs"]["split_manifold_liquid_volume"]["value"] = 1.5
    manifest["executed_inputs"]["merge_manifold_liquid_volume"]["value"] = 2.0

    assert _require_representable_source_manifold_volumes(manifest) == pytest.approx(
        (0.0015, 0.002)
    )
