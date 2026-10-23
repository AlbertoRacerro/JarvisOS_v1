"""Reference solutions, correlations, mesh-convergence estimates and case post-processing."""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np

from . import foam_io, polymesh
from .contract import PipeCase

# ---------------------------------------------------------------- references


def hagen_poiseuille_dpdl(case: PipeCase) -> float:
    """Fully developed laminar pressure gradient [Pa/m]: 32 mu U / D^2."""
    return 32.0 * case.fluid.dynamic_viscosity_pa_s * case.mean_velocity_m_s / case.diameter_m**2


def darcy_from_dpdl(dpdl: float, case: PipeCase) -> float:
    return dpdl * case.diameter_m / (0.5 * case.fluid.density_kg_m3 * case.mean_velocity_m_s**2)


def dpdl_from_darcy(f: float, case: PipeCase) -> float:
    return f * 0.5 * case.fluid.density_kg_m3 * case.mean_velocity_m_s**2 / case.diameter_m


def blasius(re: float) -> float:
    """Blasius smooth-pipe Darcy friction factor, stated validity 4e3 < Re < 1e5."""
    return 0.3164 * re**-0.25


def colebrook_smooth(re: float) -> float:
    """Colebrook (eps=0, i.e. Prandtl–Kármán smooth law) solved by fixed-point iteration."""
    inv_sqrt_f = 2.0 * math.log10(re) - 0.8  # initial guess close to the solution
    for _ in range(100):
        new = -2.0 * math.log10(2.51 * inv_sqrt_f / re)
        if abs(new - inv_sqrt_f) < 1e-13:
            break
        inv_sqrt_f = new
    return 1.0 / inv_sqrt_f**2


def mckeon_smooth(re: float) -> float:
    """McKeon et al. (2005, JFM 538) superpipe fit: 1/sqrt(f) = 1.930 log10(Re sqrt(f)) - 0.537."""
    inv = 2.0 * math.log10(re) - 0.8
    for _ in range(100):
        new = 1.930 * math.log10(re / inv) - 0.537
        if abs(new - inv) < 1e-13:
            break
        inv = new
    return 1.0 / inv**2


def laminar_entrance_length(case: PipeCase) -> float:
    """Common estimate L_e ≈ 0.05 Re D (values 0.05–0.06 are quoted in textbooks)."""
    return 0.05 * case.reynolds * case.diameter_m


# ---------------------------------------------------------------- mesh convergence


@dataclass
class GridConvergence:
    """Roache/Celik GCI for three systematically refined meshes (coarse -> fine)."""

    values: list[float]          # coarse, medium, fine
    refinement_ratio: float
    observed_order: float | None
    convergence: str             # monotonic | oscillatory | divergent
    extrapolated: float | None
    gci_fine: float | None       # relative, fraction

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def grid_convergence(values: list[float], r: float, safety: float = 1.25) -> GridConvergence:
    f3, f2, f1 = values  # coarse, medium, fine
    e32, e21 = f3 - f2, f2 - f1
    if e21 == 0 or e32 == 0:
        return GridConvergence(values, r, None, "converged-to-roundoff", f1, 0.0)
    ratio = e32 / e21
    if ratio < 0:
        return GridConvergence(values, r, None, "oscillatory", None, None)
    p = math.log(ratio) / math.log(r)
    if p <= 0:
        return GridConvergence(values, r, p, "divergent", None, None)
    f_ext = f1 + (f1 - f2) / (r**p - 1)
    gci = safety * abs((f1 - f2) / f1) / (r**p - 1)
    return GridConvergence(values, r, p, "monotonic", f_ext, gci)


# ---------------------------------------------------------------- post-processing


@dataclass
class CaseResult:
    name: str
    reynolds: float
    turbulence: str
    cells: int
    iterations: int
    converged: bool
    final_residuals: dict[str, float]
    window_m: tuple[float, float]
    dpdl_pa_m: float              # from area-averaged pressure, linear fit over the window
    dpdl_wall_shear_pa_m: float   # 4 tau_w / D, averaged over the window
    darcy_f: float
    mass_imbalance: float         # (Q_out - Q_in) / Q_in from boundary fluxes
    flow_rate_error: float        # Q_in(mesh, scaled to 360 deg) / Q_contract - 1
    continuity_cumulative: float
    profile_r_over_R: list[float]
    profile_u_over_umean: list[float]
    profile_x_m: float
    centreline_x_m: list[float]
    centreline_u_over_umean: list[float]
    y_plus: dict[str, float] | None
    local_f_x_m: list[float]      # centres of 20 equal axial windows
    local_darcy_f: list[float]    # f from the pressure gradient in each window (development check)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _columns(x: np.ndarray, n_axial: int) -> tuple[np.ndarray, np.ndarray]:
    """Group cells by axial column. blockMesh numbers x fastest, so column = index % n_axial."""
    idx = np.arange(x.size) % n_axial
    xs = np.bincount(idx, weights=x) / np.bincount(idx)
    return idx, xs


def postprocess(case: PipeCase, case_dir: Path, window: tuple[float, float],
                profile_x: float) -> CaseResult:
    """Extract developed-flow quantities. Fields must already exist (see study.run_case)."""
    t = foam_io.latest_time_dir(case_dir)
    log = foam_io.parse_solver_log((case_dir / "log.simpleFoam").read_text())
    rho, d = case.fluid.density_kg_m3, case.diameter_m
    radius = d / 2.0
    n_axial = case.mesh.axial_cells

    geo = polymesh.read_geometry(case_dir)
    c, vol = geo.cell_centres, geo.cell_volumes
    u = foam_io.read_internal(t / "U")
    p = foam_io.read_internal(t / "p") * rho  # kinematic -> Pa
    if u.shape[0] != c.shape[0] or p.shape[0] != c.shape[0]:
        raise ValueError("field size does not match mesh")
    col, xs = _columns(c[:, 0], n_axial)

    # Area-averaged pressure per column (volume weights == area weights within a column).
    p_bar = np.bincount(col, weights=p * vol) / np.bincount(col, weights=vol)
    sel = (xs >= window[0]) & (xs <= window[1])
    slope = np.polyfit(xs[sel], p_bar[sel], 1)[0]
    dpdl = -slope
    edges = np.linspace(xs.min(), xs.max(), 21)
    local_x, local_f = [], []
    for a, b in zip(edges[:-1], edges[1:], strict=True):
        m = (xs >= a) & (xs <= b)
        local_x.append(float(0.5 * (a + b)))
        local_f.append(darcy_from_dpdl(float(-np.polyfit(xs[m], p_bar[m], 1)[0]), case))

    # Wall shear stress, as OpenFOAM's wallShearStress computes it on an orthogonal mesh:
    # tau_w = rho (nu + nut_wall) |U_t,P| / y_P with y_P the wall-normal centre distance.
    wall = geo.patch_slice("wall")
    cells = geo.owner[wall]
    n_hat = geo.face_areas[wall] / np.linalg.norm(geo.face_areas[wall], axis=1)[:, None]
    y_p = np.einsum("ij,ij->i", geo.face_centres[wall] - c[cells], n_hat)
    u_p = u[cells]
    u_t = np.linalg.norm(u_p - np.einsum("ij,ij->i", u_p, n_hat)[:, None] * n_hat, axis=1)
    nu = case.fluid.kinematic_viscosity_m2_s
    nut_w = foam_io.read_patch_value(t / "nut", "wall") if (t / "nut").exists() else np.zeros(1)
    tau_kin = (nu + nut_w) * u_t / y_p
    xw = geo.face_centres[wall, 0]
    wsel = (xw >= window[0]) & (xw <= window[1])
    tau_w = float(np.mean(tau_kin[wsel])) * rho
    dpdl_wall = 4.0 * tau_w / d

    # Mass conservation from boundary face fluxes (phi is volumetric for incompressible).
    phi_in = foam_io.read_patch_value(t / "phi", "inlet")
    phi_out = foam_io.read_patch_value(t / "phi", "outlet")
    q_in, q_out = -float(np.sum(phi_in)), float(np.sum(phi_out))
    q_full = q_in * 360.0 / case.mesh.wedge_angle_deg

    # Radial profile at the column nearest profile_x.
    k = int(np.argmin(np.abs(xs - profile_x)))
    in_col = col == k
    r = np.hypot(c[in_col, 1], c[in_col, 2]) / radius
    order = np.argsort(r)
    u_prof = u[in_col, 0][order] / case.mean_velocity_m_s

    # Centreline (first radial cell) development.
    first = np.zeros(c.shape[0], dtype=bool)
    first[:n_axial] = True  # radial index 0 is the first n_axial cells
    u_cl = u[first, 0] / case.mean_velocity_m_s

    y_plus = None
    if case.turbulence != "laminar":
        yp = y_p * np.sqrt(tau_kin) / nu  # y+ of the wall-adjacent cell centre, from u_tau
        y_plus = {"min": float(yp[wsel].min()), "mean": float(yp[wsel].mean()), "max": float(yp[wsel].max())}

    return CaseResult(
        name=case.name,
        reynolds=case.reynolds,
        turbulence=case.turbulence,
        cells=int(c.shape[0]),
        iterations=log.iterations,
        converged=log.converged,
        final_residuals=log.final_residuals(),
        window_m=window,
        dpdl_pa_m=float(dpdl),
        dpdl_wall_shear_pa_m=dpdl_wall,
        darcy_f=darcy_from_dpdl(float(dpdl), case),
        mass_imbalance=(q_out - q_in) / q_in,
        flow_rate_error=q_full / case.flow_rate_m3_s - 1.0,
        continuity_cumulative=log.continuity_cumulative[-1] if log.continuity_cumulative else float("nan"),
        profile_r_over_R=[float(v) for v in r[order]],
        profile_u_over_umean=[float(v) for v in u_prof],
        profile_x_m=float(xs[k]),
        centreline_x_m=[float(v) for v in xs],
        centreline_u_over_umean=[float(v) for v in u_cl],
        y_plus=y_plus,
        local_f_x_m=local_x,
        local_darcy_f=local_f,
    )


def parabolic_profile_error(result: CaseResult) -> dict[str, float]:
    """Error of u/U_mean against 2(1-(r/R)^2), normalised by the analytic centreline value 2."""
    r = np.array(result.profile_r_over_R)
    u = np.array(result.profile_u_over_umean)
    exact = 2.0 * (1.0 - r**2)
    err = (u - exact) / 2.0
    return {"max_abs": float(np.max(np.abs(err))), "rms": float(np.sqrt(np.mean(err**2))),
            "centreline_u_over_umean": float(u[0]), "centreline_r_over_R": float(r[0])}
