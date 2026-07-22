import copy

import pytest

from app.modules.bluecad.spec import SpecValidationError, canonicalize_geometry_spec


PARAMETERS = {
    "main_outer_d": 120.0,
    "main_wall_t": 5.0,
    "branch_count": 2,
    "branch_outer_d": 40.0,
    "branch_wall_t": 3.0,
    "branch_gap": 20.0,
    "end_gap": 15.0,
    "branch_stub_length": 60.0,
    "cap_thickness": 8.0,
}


def geometry_spec(**parameter_overrides):
    parameters = dict(PARAMETERS)
    parameters.update(parameter_overrides)
    return {
        "spec_version": "bluecad_geometry_spec_v0_1",
        "name": "capped-manifold-contract",
        "parts": [
            {
                "part_id": "header",
                "kind": "capped_manifold",
                "params": parameters,
            }
        ],
        "connections": [],
    }


def test_capped_manifold_contract_is_value_explicit_and_canonical():
    first = canonicalize_geometry_spec(geometry_spec())
    second = canonicalize_geometry_spec(copy.deepcopy(geometry_spec()))
    assert first == second
    assert first["parts"][0]["params"] == PARAMETERS
    assert first["spec_id"].startswith("sha256:")


@pytest.mark.parametrize("branch_count", [1, 2, 12])
def test_capped_manifold_accepts_bounded_integer_branch_counts(branch_count):
    canonical = canonicalize_geometry_spec(geometry_spec(branch_count=branch_count))
    assert canonical["parts"][0]["params"]["branch_count"] == branch_count


@pytest.mark.parametrize("branch_count", [True, 0, 13, 1.5])
def test_capped_manifold_rejects_invalid_branch_counts(branch_count):
    with pytest.raises(SpecValidationError):
        canonicalize_geometry_spec(geometry_spec(branch_count=branch_count))


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("main_outer_d", 0.0),
        ("main_wall_t", 0.0),
        ("branch_outer_d", 0.0),
        ("branch_wall_t", 0.0),
        ("branch_gap", 0.0),
        ("end_gap", 0.0),
        ("branch_stub_length", 0.0),
        ("cap_thickness", 0.0),
    ],
)
def test_capped_manifold_rejects_nonpositive_dimensions(name, value):
    with pytest.raises(SpecValidationError):
        canonicalize_geometry_spec(geometry_spec(**{name: value}))


def test_capped_manifold_rejects_invalid_wall_domains():
    with pytest.raises(SpecValidationError):
        canonicalize_geometry_spec(geometry_spec(main_wall_t=60.0))
    with pytest.raises(SpecValidationError):
        canonicalize_geometry_spec(geometry_spec(branch_wall_t=20.0))


def test_capped_manifold_rejects_unknown_or_semantic_parameters():
    for name in ("unknown", "split", "flow_rate", "pressure", "material"):
        payload = geometry_spec()
        payload["parts"][0]["params"][name] = 1.0
        with pytest.raises(SpecValidationError):
            canonicalize_geometry_spec(payload)
