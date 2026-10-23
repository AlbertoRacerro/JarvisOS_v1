"""Typed contract for a straight smooth circular pipe CFD case.

The contract is the only input to case generation: every OpenFOAM dictionary is
derived from it deterministically (see ``casegen.py``). Validation here rejects
cases that are physically or numerically inconsistent before any file is written.
"""

from __future__ import annotations

import math
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

LAMINAR_RE_MAX = 2000.0
TURBULENT_RE_MIN = 4000.0


class Fluid(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str = "water_20C"
    density_kg_m3: float = Field(998.2, gt=0)
    dynamic_viscosity_pa_s: float = Field(1.002e-3, gt=0)

    @property
    def kinematic_viscosity_m2_s(self) -> float:
        return self.dynamic_viscosity_pa_s / self.density_kg_m3


class Inlet(BaseModel):
    """Exactly one of mean velocity or volumetric flow rate."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    mean_velocity_m_s: float | None = Field(None, gt=0)
    flow_rate_m3_s: float | None = Field(None, gt=0)
    turbulence_intensity: float = Field(0.05, gt=0, le=0.3)
    # Inlet mixing length as a fraction of D (0.07 D is the usual pipe estimate).
    mixing_length_over_d: float = Field(0.07, gt=0, le=0.5)

    @model_validator(mode="after")
    def _one_of(self) -> "Inlet":
        if (self.mean_velocity_m_s is None) == (self.flow_rate_m3_s is None):
            raise ValueError("specify exactly one of mean_velocity_m_s or flow_rate_m3_s")
        return self


class Mesh(BaseModel):
    """Structured 2D-axisymmetric wedge mesh (one cell in the azimuthal direction).

    ``radial_grading`` is the blockMesh expansion ratio (cell at wall / cell at axis);
    values < 1 cluster cells toward the wall.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    radial_cells: int = Field(ge=4, le=400)
    axial_cells: int = Field(ge=10, le=5000)
    radial_grading: float = Field(1.0, gt=0.001, le=1.0)
    wedge_angle_deg: float = Field(2.0, gt=0, le=5)


class Solver(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    max_iterations: int = Field(20000, ge=10)
    residual_target: float = Field(1e-7, gt=0, lt=1e-2)


class PipeCase(BaseModel):
    """Steady incompressible flow in a straight smooth circular pipe."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str = Field(pattern=r"^[A-Za-z0-9_.-]+$")
    diameter_m: float = Field(gt=0)
    length_m: float = Field(gt=0)
    fluid: Fluid = Fluid()
    inlet: Inlet
    outlet_pressure_pa: float = 0.0  # gauge; incompressible, only differences matter
    mesh: Mesh
    turbulence: Literal["laminar", "kOmegaSST", "kEpsilon"] = "laminar"
    solver: Solver = Solver()

    @property
    def area_m2(self) -> float:
        return math.pi * self.diameter_m**2 / 4.0

    @property
    def mean_velocity_m_s(self) -> float:
        if self.inlet.mean_velocity_m_s is not None:
            return self.inlet.mean_velocity_m_s
        return self.inlet.flow_rate_m3_s / self.area_m2  # type: ignore[operator]

    @property
    def flow_rate_m3_s(self) -> float:
        return self.mean_velocity_m_s * self.area_m2

    @property
    def reynolds(self) -> float:
        return self.mean_velocity_m_s * self.diameter_m / self.fluid.kinematic_viscosity_m2_s

    @model_validator(mode="after")
    def _regime_consistent(self) -> "PipeCase":
        re = self.reynolds
        if self.turbulence == "laminar" and re > LAMINAR_RE_MAX:
            raise ValueError(f"laminar model requested at Re={re:.0f} > {LAMINAR_RE_MAX:.0f}")
        if self.turbulence != "laminar" and re < TURBULENT_RE_MIN:
            raise ValueError(f"RANS model requested at Re={re:.0f} < {TURBULENT_RE_MIN:.0f}")
        if self.length_m < 5 * self.diameter_m:
            raise ValueError("length_m must be at least 5 diameters")
        return self
