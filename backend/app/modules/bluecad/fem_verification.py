"""Verification-only public surface for analytic BLUECAD FEM benchmarks.

The implementation is deliberately separate from the production FEM result
summary parser. It provides closed-form references, component-aware parsing,
location sampling, tensor transforms, pressure-surface audits, and fixture
integrity checks for spec 024-C.
"""

from app.modules.bluecad.fem_verification_analytics import (
    beam_tip_displacement,
    finite_width_hole_factor,
    finite_width_hole_reference,
    lame_open_end_bore_stresses,
)
from app.modules.bluecad.fem_verification_common import (
    FemVerificationError,
    comparison_record,
    deterministic_mean,
    relative_error,
)
from app.modules.bluecad.fem_verification_fixtures import verify_fixture_index
from app.modules.bluecad.fem_verification_parsers import (
    displacement_block,
    latest_frd_block,
    parse_frd_blocks,
    parse_inp_mesh,
    stress_block,
)
from app.modules.bluecad.fem_verification_sampling import (
    audit_segmented_pressure_surface,
    cylindrical_stress_components,
    select_nodes_near,
)

__all__ = [
    "FemVerificationError",
    "audit_segmented_pressure_surface",
    "beam_tip_displacement",
    "comparison_record",
    "cylindrical_stress_components",
    "deterministic_mean",
    "displacement_block",
    "finite_width_hole_factor",
    "finite_width_hole_reference",
    "lame_open_end_bore_stresses",
    "latest_frd_block",
    "parse_frd_blocks",
    "parse_inp_mesh",
    "relative_error",
    "select_nodes_near",
    "stress_block",
    "verify_fixture_index",
]
