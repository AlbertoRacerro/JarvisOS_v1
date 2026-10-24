"""Three-mesh observed order and grid-convergence index (spec 216 contract 5c).

Follows Celik et al. (2008), "Procedure for estimation and reporting of
uncertainty due to discretization in CFD applications", J. Fluids Eng. 130,
078001, for a constant refinement ratio. Only monotonic convergence yields an
uncertainty; oscillatory or divergent triplets are reported as such and never
turned into a GCI.
"""

from __future__ import annotations

import math
from typing import Literal

from pydantic import BaseModel, ConfigDict

GCI_SAFETY_FACTOR = 1.25

Convergence = Literal["monotonic", "oscillatory", "divergent", "converged"]


class MeshStudyError(ValueError):
    pass


class MeshStudy(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    refinement_ratio: float
    fine: float
    medium: float
    coarse: float
    convergence: Convergence
    observed_order: float | None
    extrapolated: float | None
    gci_fine: float | None


def refinement_ratio(cells: tuple[int, int, int]) -> float:
    """Constant 3D refinement ratio from fine, medium and coarse cell counts."""
    fine, medium, coarse = cells
    if not fine > medium > coarse > 0:
        raise MeshStudyError("cell counts must be strictly decreasing from fine to coarse")
    r21 = (fine / medium) ** (1.0 / 3.0)
    r32 = (medium / coarse) ** (1.0 / 3.0)
    if not math.isclose(r21, r32, rel_tol=1e-3):
        raise MeshStudyError(f"refinement ratio is not constant ({r21:.4f} vs {r32:.4f})")
    if r21 < 1.3:
        raise MeshStudyError(f"refinement ratio {r21:.3f} is below the recommended 1.3")
    return r21


def three_mesh_study(values: tuple[float, float, float], ratio: float) -> MeshStudy:
    """Observed order, Richardson extrapolation and fine-mesh GCI for (fine, medium, coarse)."""
    fine, medium, coarse = values
    if not all(math.isfinite(v) for v in values) or not math.isfinite(ratio) or ratio <= 1.0:
        raise MeshStudyError("mesh study needs finite values and a refinement ratio above 1")
    e21, e32 = medium - fine, coarse - medium
    base = {"refinement_ratio": ratio, "fine": fine, "medium": medium, "coarse": coarse}
    if e21 == 0.0 and e32 == 0.0:
        return MeshStudy(**base, convergence="converged", observed_order=None, extrapolated=fine, gci_fine=0.0)
    if e32 == 0.0 or e21 / e32 < 0.0:
        return MeshStudy(**base, convergence="oscillatory", observed_order=None, extrapolated=None, gci_fine=None)
    if abs(e21) >= abs(e32):
        return MeshStudy(**base, convergence="divergent", observed_order=None, extrapolated=None, gci_fine=None)
    order = math.log(abs(e32 / e21)) / math.log(ratio)
    rp = ratio**order
    extrapolated = (rp * fine - medium) / (rp - 1.0)
    if fine == 0.0:
        raise MeshStudyError("fine-mesh value is zero; relative GCI is undefined")
    gci = GCI_SAFETY_FACTOR * abs(e21 / fine) / (rp - 1.0)
    return MeshStudy(**base, convergence="monotonic", observed_order=order, extrapolated=extrapolated, gci_fine=gci)
