"""PBR solar optics T2 kernel (spec 174): tube-array interception, Fresnel wall, opaque exact shading.

One pure, deterministic numpy kernel. It performs no I/O, keeps no global mutable state and imports nothing
from the dynamic engine. Inputs are sun elevation/azimuth, DNI and DHI already converted to PAR, the tube
diameter D, a representative cross-section module of identical horizontal tubes, the wall and water indices,
the sea albedo and (optionally) the culture extinction kappa. Everything is per metre of tube length and
averaged over the module's tubes, so intensity units are those of the supplied DNI/DHI times metres.

Geometry (decisions 2-6 of the spec)
------------------------------------
* Tubes are infinite parallel horizontal cylinders of equal diameter with axis azimuth alpha. For a unit
  vector s towards the source, a = s . axis is the axial component, c = cos(gamma) = sqrt(1 - a^2) and
  psi = atan2(s_h, s_z) the in-plane direction. A beam strip carries DNI*c per unit lateral width, so an
  isolated tube normal to the beam intercepts DNI*D.
* Shading is exact 2D projected-shadow geometry with opaque upstream tubes: the unshadowed part of tube i is its
  silhouette interval minus the union of overlapping upstream silhouettes, evaluated with sorted breakpoints
  (a sort-by-lower-edge sweep with a running maximum), never a grid.
* Wall: unpolarised, thin, incoherent slab air/wall/water, T = T1*T2/(1 - R1*R2) per polarisation, averaged.
  The local incidence angle at silhouette offset s = R sin(u) satisfies cos(theta) = c cos(u).
* Culture: Beer-Lambert along the refracted straight chord l = D cos(phi_w)/cos(gamma_w); internal
  re-reflection is ignored. Absorbed = sum of T (1 - exp(-kappa l)).
* Sources: beam (DNI), isotropic sky (radiance DHI/pi, upper hemisphere) and isotropic sea reflection
  (radiance rho*GHI/pi, lower hemisphere). The diffuse integrals depend only on the layout and axis, so they
  are integrated once per layout.

Integration variable. Silhouette offsets are integrated in u = asin(s/R), which removes the square-root edge
singularity of the wall transmission; thin-limit/transmission quantities use one 10-point Gauss-Legendre
panel per unshadowed interval and absorption uses a fixed graded panel set that resolves optical depths to 1000.
"""
from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from functools import cache
from typing import Any, Final

import numpy as np
from numpy.polynomial.legendre import leggauss

VERSION: Final = "optics_t2.v1"
MAX_MODULE_TUBES: Final = 64
# Frozen from the midpoint-sun bias table of the evidence file (docs/implementation/174-optics-evidence-*.md).
OPTICS_RESOLUTION_MAX_MIN: Final = 15
# Tolerance frozen from the refracted-versus-T1-shape residual table of the same evidence file.
SHAPE_RESIDUAL_TOLERANCE: Final = 0.15
TAU_MAX: Final = 1000.0

_GAP_NODES: Final = 10  # thin / transmission panel (smooth integrand)
_FINE_NODES: Final = 6  # per graded panel for kappa-dependent absorption
_FINE_DELTAS: Final = (0.0, 1e-3, 4e-3, 1.6e-2, 6.4e-2, 0.25, 0.7)
_EPS_NODES: Final = 12  # axial-angle Gauss-Legendre nodes of the hemisphere rules
_PSI_PANELS: Final = 36
_PSI_NODES: Final = 4
_TAU_GRID_POINTS: Final = 33
_TAU_GRID_MIN: Final = 1e-4
_C_MIN: Final = 1e-9


class OpticsError(ValueError):
    """Typed T2 optics failure; the engine maps ``code`` and ``detail`` to a DynamicError."""

    def __init__(self, code: str, message: str, detail: dict[str, Any] | None = None) -> None:
        super().__init__(message[:600])
        self.code = code
        self.detail = detail or {}


# --------------------------------------------------------------------------------------- configuration


@dataclass(frozen=True)
class Optics:
    """Layout, wall and sea inputs. All lengths in metres, angles in radians; validated at construction."""

    diameter: float
    tubes_across: int
    layers: int
    pitch_h: float
    pitch_v: float
    stagger: float
    axis_azimuth: float
    centre_height: float
    n_wall: float
    n_water: float
    sea_albedo: float

    def __post_init__(self) -> None:
        numbers = (self.diameter, self.pitch_h, self.pitch_v, self.stagger, self.axis_azimuth, self.centre_height,
                   self.n_wall, self.n_water, self.sea_albedo)
        if not all(isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) for v in numbers):
            raise OpticsError("OPTICS_PARAMETER_INVALID", "Optics inputs must be finite numbers.")
        for name in ("tubes_across", "layers"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                raise OpticsError("OPTICS_LAYOUT_INVALID", f"{name} must be a whole number of at least 1.",
                                  {"field": name})
        if not 0.0 < self.diameter <= 0.5:
            raise OpticsError("OPTICS_PARAMETER_INVALID", "Tube diameter must be in (0, 0.5] m.", {"field": "diameter"})
        if self.tubes_across * self.layers > MAX_MODULE_TUBES:
            raise OpticsError("OPTICS_LAYOUT_INVALID",
                              f"The cross-section module has {self.tubes_across * self.layers} tubes; the limit is "
                              f"{MAX_MODULE_TUBES}.", {"module_tubes": self.tubes_across * self.layers})
        tolerance = 1e-12 * self.diameter
        if self.pitch_h < self.diameter - tolerance or self.pitch_v < self.diameter - tolerance:
            raise OpticsError("OPTICS_LAYOUT_INVALID", "Tube pitch must be at least the tube diameter.",
                              {"pitch_h": self.pitch_h, "pitch_v": self.pitch_v, "diameter": self.diameter})
        if abs(self.stagger) > self.pitch_h:
            raise OpticsError("OPTICS_LAYOUT_INVALID", "The stagger offset must not exceed the horizontal pitch.",
                              {"field": "stagger_offset"})
        if self.centre_height < self.diameter / 2.0 - tolerance:
            raise OpticsError("OPTICS_LAYOUT_INVALID", "The lowest tube centre must be at least one tube radius "
                              "above the sea.", {"field": "centre_height_above_sea"})
        if not (1.0 <= self.n_wall <= 5.0 and 1.0 <= self.n_water <= 5.0):
            raise OpticsError("OPTICS_PARAMETER_INVALID", "Refractive indices must lie in [1, 5].",
                              {"n_wall": self.n_wall, "n_water": self.n_water})
        if not 0.0 <= self.sea_albedo <= 1.0:
            raise OpticsError("OPTICS_PARAMETER_INVALID", "Sea albedo must lie in [0, 1].",
                              {"field": "sea_albedo"})
        centres = self.centres()
        if len(centres) > 1:
            offsets = centres[:, None, :] - centres[None, :, :]
            distance = np.sqrt((offsets**2).sum(-1)) + np.eye(len(centres)) * 1e9
            if distance.min() < self.diameter * (1.0 - 1e-9):
                raise OpticsError("OPTICS_LAYOUT_INVALID", "Tubes in the layout overlap.", {})

    @property
    def module_tubes(self) -> int:
        return self.tubes_across * self.layers

    def centres(self) -> np.ndarray:
        """Tube centres (h, z) in the cross-section plane, shape (N, 2); h along the horizontal normal of the axis."""
        rows = []
        for layer in range(self.layers):
            shift = self.stagger if layer % 2 else 0.0
            for index in range(self.tubes_across):
                rows.append(((index - (self.tubes_across - 1) / 2.0) * self.pitch_h + shift,
                             self.centre_height + layer * self.pitch_v))
        return np.asarray(rows, dtype=np.float64)

    def digest(self) -> str:
        payload = json.dumps([VERSION, self.diameter, self.tubes_across, self.layers, self.pitch_h, self.pitch_v,
                              self.stagger, self.axis_azimuth, self.centre_height, self.n_wall, self.n_water,
                              self.sea_albedo], separators=(",", ":"))
        return hashlib.sha256(payload.encode()).hexdigest()


# -------------------------------------------------------------------------------------------- Fresnel


def _fresnel_amplitudes(n1: float, n2: float, cos_i: np.ndarray, cos_t: np.ndarray) -> tuple[np.ndarray, ...]:
    """Amplitude reflection/transmission coefficients (rs, rp, ts, tp); 0/0 (equal media) is no interface."""
    den_s = n1 * cos_i + n2 * cos_t
    den_p = n2 * cos_i + n1 * cos_t
    safe_s = np.where(den_s > 0.0, den_s, 1.0)
    safe_p = np.where(den_p > 0.0, den_p, 1.0)
    rs = np.where(den_s > 0.0, (n1 * cos_i - n2 * cos_t) / safe_s, 0.0)
    rp = np.where(den_p > 0.0, (n2 * cos_i - n1 * cos_t) / safe_p, 0.0)
    ts = np.where(den_s > 0.0, 2.0 * n1 * cos_i / safe_s, 1.0)
    tp = np.where(den_p > 0.0, 2.0 * n1 * cos_i / safe_p, 1.0)
    return rs, rp, ts, tp


def fresnel_interface(cos_i: np.ndarray | float, n1: float, n2: float) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Power coefficients (Rs, Rp, Ts, Tp) of one interface n1 -> n2 at incidence cosine ``cos_i``.

    Transmittance is computed independently from the amplitude coefficient (T = n2 cos_t/(n1 cos_i) t^2) so
    R + T = 1 is a genuine energy-conservation check. Total internal reflection returns R = 1, T = 0.
    """
    cos_i = np.clip(np.asarray(cos_i, dtype=np.float64), 0.0, 1.0)
    sin2_t = (n1 / n2) ** 2 * (1.0 - cos_i**2)
    total = sin2_t >= 1.0
    cos_t = np.sqrt(np.maximum(0.0, 1.0 - sin2_t))
    rs, rp, ts, tp = _fresnel_amplitudes(n1, n2, cos_i, cos_t)
    with np.errstate(divide="ignore", invalid="ignore"):
        ratio = np.where(cos_i > 0.0, n2 * cos_t / (n1 * np.where(cos_i > 0.0, cos_i, 1.0)), 0.0)
    r_s, r_p = rs**2, rp**2
    t_s = np.where(cos_i > 0.0, ratio * ts**2, np.where(n1 == n2, 1.0, 0.0))
    t_p = np.where(cos_i > 0.0, ratio * tp**2, np.where(n1 == n2, 1.0, 0.0))
    r_s = np.where(total, 1.0, r_s)
    r_p = np.where(total, 1.0, r_p)
    t_s = np.where(total, 0.0, t_s)
    t_p = np.where(total, 0.0, t_p)
    return r_s, r_p, t_s, t_p


def wall_transmittance(cos_theta: np.ndarray | float, n_wall: float, n_water: float) -> np.ndarray:
    """Unpolarised thin-slab transmittance air / wall / water with incoherent multiple reflections."""
    return fresnel_slab(cos_theta, n_wall, n_water)[0]


def fresnel_slab(cos_theta: np.ndarray | float, n_wall: float, n_water: float) -> tuple[np.ndarray, np.ndarray]:
    """(T, R) of the slab, polarisation averaged, no absorption. R is computed independently of T."""
    cos0 = np.clip(np.asarray(cos_theta, dtype=np.float64), 0.0, 1.0)
    sin2 = 1.0 - cos0**2
    cos_wall = np.sqrt(np.maximum(0.0, 1.0 - sin2 / n_wall**2))
    r1s, r1p, _, _ = fresnel_interface(cos0, 1.0, n_wall)
    r2s, r2p, _, _ = fresnel_interface(cos_wall, n_wall, n_water)
    transmitted = np.zeros_like(cos0)
    reflected = np.zeros_like(cos0)
    for r1, r2 in ((r1s, r2s), (r1p, r2p)):
        t1, t2 = 1.0 - r1, 1.0 - r2
        denominator = 1.0 - r1 * r2
        safe = np.where(denominator > 0.0, denominator, 1.0)
        transmitted += 0.5 * np.where(denominator > 0.0, t1 * t2 / safe, 0.0)
        reflected += 0.5 * np.where(denominator > 0.0, r1 + t1 * t1 * r2 / safe, 1.0)
    return transmitted, reflected


# ------------------------------------------------------------------------------------------ geometry


def sun_unit_vector(elevation_deg: np.ndarray, azimuth_deg: np.ndarray) -> np.ndarray:
    """Unit vectors towards the sun in (east, north, up); azimuth clockwise from north."""
    el, az = np.radians(np.asarray(elevation_deg, float)), np.radians(np.asarray(azimuth_deg, float))
    return np.stack([np.cos(el) * np.sin(az), np.cos(el) * np.cos(az), np.sin(el)], axis=-1)


def decompose(vectors: np.ndarray, axis_azimuth: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Axial component a, cos(gamma) and in-plane angle psi for (east, north, up) unit vectors."""
    axis = np.array([math.sin(axis_azimuth), math.cos(axis_azimuth), 0.0])
    normal = np.array([math.cos(axis_azimuth), -math.sin(axis_azimuth), 0.0])
    a = np.clip(vectors @ axis, -1.0, 1.0)
    horizontal = vectors @ normal
    up = vectors[..., 2]
    c = np.hypot(horizontal, up)
    return a, c, np.arctan2(horizontal, up)


def lit_gaps(centres: np.ndarray, diameter: float, psi: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Unshadowed intervals of every tube for in-plane source directions ``psi`` (shape (M,)).

    Returns lower/upper local offsets (M, N, N + 1) in [-R, R]; zero-length candidates mean 'none'. The unshadowed
    set of tube i is its silhouette minus the union of overlapping upstream silhouettes, found by sorting the
    upstream intervals by lower edge and sweeping a running maximum (exact; no grid).
    """
    psi = np.atleast_1d(np.asarray(psi, dtype=np.float64))
    radius = diameter / 2.0
    towards = np.stack([np.sin(psi), np.cos(psi)], axis=-1)  # (M, 2) direction towards the source
    across = np.stack([np.cos(psi), -np.sin(psi)], axis=-1)  # silhouette normal
    along = towards @ centres.T  # (M, N)
    offset = across @ centres.T  # (M, N)
    upstream = ((along[:, None, :] - along[:, :, None]) > 1e-12 * diameter) & (
        np.abs(offset[:, None, :] - offset[:, :, None]) < diameter)  # [m, i, j]: j shadows i
    window_low = offset - radius  # (M, N)
    window_high = offset + radius
    low_i = window_low[:, :, None]
    high_i = window_high[:, :, None]
    shadow_low = np.where(upstream, np.clip(offset[:, None, :] - radius, low_i, high_i), low_i)
    shadow_high = np.where(upstream, np.clip(offset[:, None, :] + radius, low_i, high_i), low_i)
    order = np.argsort(shadow_low, axis=-1, kind="stable")
    sorted_low = np.take_along_axis(shadow_low, order, axis=-1)
    sorted_high = np.take_along_axis(shadow_high, order, axis=-1)
    covered = np.maximum.accumulate(np.maximum(sorted_high, low_i), axis=-1)
    gap_low = np.concatenate([window_low[:, :, None], covered], axis=-1)  # (M, N, N + 1)
    gap_high = np.concatenate([sorted_low, window_high[:, :, None]], axis=-1)
    gap_high = np.maximum(gap_high, gap_low)
    shift = offset[:, :, None]
    return gap_low - shift, gap_high - shift


@cache
def _gauss(n: int) -> tuple[np.ndarray, np.ndarray]:
    nodes, weights = leggauss(n)
    return nodes, weights


def _panel_edges(fine: bool) -> np.ndarray:
    if not fine:
        return np.array([-math.pi / 2, math.pi / 2])
    half = math.pi / 2
    upper = [half - d for d in _FINE_DELTAS]
    return np.array(sorted(set([-v for v in upper] + upper)))


# ------------------------------------------------------------------------------------- integration


def _node_terms(c: np.ndarray, a: np.ndarray, u: np.ndarray, optics: Optics) -> tuple[np.ndarray, np.ndarray]:
    """Wall transmittance and refracted chord length at nodes u (any shape broadcastable with c, a)."""
    cos_theta = c * np.cos(u)
    transmittance = wall_transmittance(cos_theta, optics.n_wall, optics.n_water)
    n = optics.n_water
    cos_gamma_w = np.sqrt(np.maximum(1.0 - (a / n) ** 2, 1e-300))
    sin_phi_w = np.clip(c * np.sin(u) / (n * cos_gamma_w), -1.0, 1.0)
    chord = optics.diameter * np.sqrt(np.maximum(0.0, 1.0 - sin_phi_w**2)) / cos_gamma_w
    return transmittance, chord


def _integrate(optics: Optics, gap_low: np.ndarray, gap_high: np.ndarray, c: np.ndarray, a: np.ndarray,
               kappa: np.ndarray | None, fine: bool) -> dict[str, np.ndarray]:
    """Per-direction module sums over unshadowed intervals: width W, transmitted Tw, thin T.l, absorbed A(kappa)."""
    radius = optics.diameter / 2.0
    steps = gap_low.shape[0]
    width = gap_high - gap_low
    total_width = width.sum(axis=(1, 2))
    m_idx, _, _ = np.nonzero(width > 1e-14 * optics.diameter)
    lows = gap_low[width > 1e-14 * optics.diameter]
    highs = gap_high[width > 1e-14 * optics.diameter]
    result = {"width": total_width, "transmitted": np.zeros(steps), "thin": np.zeros(steps),
              "absorbed": np.zeros(steps)}
    if not len(m_idx):
        return result
    u0 = np.arcsin(np.clip(lows / radius, -1.0, 1.0))
    u1 = np.arcsin(np.clip(highs / radius, -1.0, 1.0))
    if fine:
        base = _panel_edges(True)
        edges = np.clip(base[None, :], u0[:, None], u1[:, None])
        nodes_x, nodes_w = _gauss(_FINE_NODES)
    else:
        edges = np.stack([u0, u1], axis=1)
        nodes_x, nodes_w = _gauss(_GAP_NODES)
    mid = 0.5 * (edges[:, 1:] + edges[:, :-1])
    half = 0.5 * (edges[:, 1:] - edges[:, :-1])
    u = mid[..., None] + half[..., None] * nodes_x
    weight = half[..., None] * nodes_w * radius * np.cos(u)
    cc, aa = c[m_idx][:, None, None], a[m_idx][:, None, None]
    transmittance, chord = _node_terms(cc, aa, u, optics)
    result["transmitted"] = np.bincount(m_idx, weights=(weight * transmittance).sum(axis=(1, 2)), minlength=steps)
    result["thin"] = np.bincount(m_idx, weights=(weight * transmittance * chord).sum(axis=(1, 2)), minlength=steps)
    if kappa is not None:
        k = kappa[m_idx][:, None, None]
        absorbed = weight * transmittance * -np.expm1(-k * chord)
        result["absorbed"] = np.bincount(m_idx, weights=absorbed.sum(axis=(1, 2)), minlength=steps)
    return result


def _directions(optics: Optics, vectors: np.ndarray, kappa: np.ndarray | None, fine: bool,
                chunk: int) -> dict[str, np.ndarray]:
    a, c, psi = decompose(vectors, optics.axis_azimuth)
    centres = optics.centres()
    count = len(a)
    out = {key: np.zeros(count) for key in ("width", "transmitted", "thin", "absorbed")}
    for start in range(0, count, chunk):
        sl = slice(start, min(count, start + chunk))
        gap_low, gap_high = lit_gaps(centres, optics.diameter, psi[sl])
        part = _integrate(optics, gap_low, gap_high, c[sl], a[sl], None if kappa is None else kappa[sl], fine)
        for key in out:
            out[key][sl] = part[key]
    out["c"] = c
    out["a"] = a
    return out


# ---------------------------------------------------------------------------------------------- model


@dataclass(frozen=True)
class HemisphereRule:
    """Fixed quadrature directions of one hemisphere: unit vectors (east, north, up) and weights (sr)."""

    vectors: np.ndarray
    weights: np.ndarray  # cos(eps) d(eps) d(psi): the solid-angle measure


def _hemisphere_rule(lower: bool) -> HemisphereRule:
    eps_x, eps_w = _gauss(_EPS_NODES)
    eps = eps_x * math.pi / 2
    eps_weight = eps_w * math.pi / 2
    psi_x, psi_w = _gauss(_PSI_NODES)
    start = math.pi / 2 if lower else -math.pi / 2
    width = math.pi / _PSI_PANELS
    psis, psi_weights = [], []
    for panel in range(_PSI_PANELS):
        centre = start + (panel + 0.5) * width
        psis.extend(centre + psi_x * width / 2)
        psi_weights.extend(psi_w * width / 2)
    psi_arr, psi_weight = np.asarray(psis), np.asarray(psi_weights)
    # Direction in the (axis, horizontal-normal, up) frame, then rotated by the axis azimuth in the model.
    e_grid, p_grid = np.meshgrid(eps, psi_arr, indexing="ij")
    a = np.sin(e_grid).ravel()
    c = np.cos(e_grid).ravel()
    h = (c * np.sin(p_grid.ravel()))
    z = (c * np.cos(p_grid.ravel()))
    weights = (np.cos(e_grid) * eps_weight[:, None] * psi_weight[None, :]).ravel()
    frame = np.stack([a, h, z], axis=-1)
    return HemisphereRule(frame, weights)


class ArrayModel:
    """Evaluator for one validated layout; diffuse integrals are computed once and cached on the instance."""

    def __init__(self, optics: Optics) -> None:
        self.optics = optics
        self.module_tubes = optics.module_tubes
        self._rules = {name: _hemisphere_rule(lower) for name, lower in (("sky", False), ("sea", True))}
        self._cache: dict[str, Any] = {}

    # -- frame handling
    def _world_vectors(self, frame: np.ndarray) -> np.ndarray:
        """Convert (axis, normal, up) frame vectors to (east, north, up) for ``decompose``."""
        alpha = self.optics.axis_azimuth
        axis = np.array([math.sin(alpha), math.cos(alpha), 0.0])
        normal = np.array([math.cos(alpha), -math.sin(alpha), 0.0])
        east_north = frame[:, 0:1] * axis[None, :2] + frame[:, 1:2] * normal[None, :2]
        return np.concatenate([east_north, frame[:, 2:3]], axis=1)

    def _hemisphere(self, name: str) -> dict[str, float]:
        key = f"hemisphere:{name}"
        if key not in self._cache:
            rule = self._rules[name]
            parts = _directions(self.optics, self._world_vectors(rule.vectors), None, False, 4096)
            c, w = parts["c"], rule.weights
            self._cache[key] = {
                "intercept": float((w * c * parts["width"]).sum()),
                "transmitted": float((w * c * parts["transmitted"]).sum()),
                "thin": float((w * c * parts["thin"]).sum()),
            }
        return self._cache[key]  # type: ignore[no-any-return]

    def _absorption_table(self, name: str) -> tuple[np.ndarray, np.ndarray]:
        key = f"absorption:{name}"
        if key not in self._cache:
            rule = self._rules[name]
            vectors = self._world_vectors(rule.vectors)
            taus = np.concatenate([[0.0], np.geomspace(_TAU_GRID_MIN, TAU_MAX, _TAU_GRID_POINTS - 1)])
            values = np.zeros(len(taus))
            for index, tau in enumerate(taus[1:], start=1):
                kappa = np.full(len(vectors), tau / self.optics.diameter)
                parts = _directions(self.optics, vectors, kappa, True, 512)
                values[index] = float((rule.weights * parts["c"] * parts["absorbed"]).sum())
            self._cache[key] = (taus, values)
        return self._cache[key]  # type: ignore[no-any-return]

    def diffuse_absorption(self, name: str, kappa: np.ndarray) -> np.ndarray:
        """Absorption integral for hemisphere ``name`` at extinction ``kappa`` (interpolated table, ln tau axis)."""
        taus, values = self._absorption_table(name)
        thin = self._hemisphere(name)["thin"]
        tau = np.asarray(kappa, dtype=np.float64) * self.optics.diameter
        if np.any(tau > TAU_MAX * (1 + 1e-9)):
            raise OpticsError("OPTICS_TAU_RANGE", f"Optical depth exceeds the supported limit {TAU_MAX:g}.")
        low = tau <= taus[1]
        from scipy.interpolate import PchipInterpolator

        spline = PchipInterpolator(np.log(taus[1:]), values[1:], extrapolate=False)
        interpolated = spline(np.log(np.maximum(tau, taus[1])))
        return np.where(low, thin * np.asarray(kappa, dtype=np.float64), np.nan_to_num(interpolated))

    # -- public evaluation
    def beam(self, elevation_deg: np.ndarray, azimuth_deg: np.ndarray, kappa: np.ndarray | None = None,
             *, fine: bool | None = None) -> dict[str, np.ndarray]:
        """Beam geometry integrals per direction, in metres (multiply by c * DNI for power per tube length)."""
        el = np.atleast_1d(np.asarray(elevation_deg, dtype=np.float64))
        az = np.atleast_1d(np.asarray(azimuth_deg, dtype=np.float64))
        if el.shape != az.shape or not (np.all(np.isfinite(el)) and np.all(np.isfinite(az))):
            raise OpticsError("OPTICS_INPUT_INVALID", "Sun elevation and azimuth must be finite arrays of equal length.")
        use_fine = kappa is not None if fine is None else fine
        if kappa is not None:
            kappa = np.broadcast_to(np.asarray(kappa, dtype=np.float64), el.shape)
        vectors = sun_unit_vector(el, az)
        parts = _directions(self.optics, vectors, kappa, use_fine, 128 if use_fine else 512)
        up = (el > 0.0) & (parts["c"] > _C_MIN)
        for key in ("width", "transmitted", "thin", "absorbed"):
            parts[key] = np.where(up, parts[key], 0.0)
        return parts

    def evaluate(self, elevation_deg: np.ndarray, azimuth_deg: np.ndarray, dni: np.ndarray, dhi: np.ndarray,
                 kappa: np.ndarray | None = None) -> dict[str, np.ndarray]:
        """Per-step module-mean quantities for DNI/DHI (already PAR), per metre of tube length.

        Keys: intercepted, transmitted, thin (coefficient: thin-limit absorbed = kappa * thin), i0_eq, diffuse_share,
        beam_unshaded_fraction, and absorbed when ``kappa`` is given.
        """
        el = np.atleast_1d(np.asarray(elevation_deg, dtype=np.float64))
        dni = np.atleast_1d(np.asarray(dni, dtype=np.float64))
        dhi = np.atleast_1d(np.asarray(dhi, dtype=np.float64))
        if dni.shape != el.shape or dhi.shape != el.shape:
            raise OpticsError("OPTICS_INPUT_INVALID", "Sun and irradiance arrays must have equal length.")
        if not (np.all(np.isfinite(dni)) and np.all(np.isfinite(dhi))) or np.any(dni < 0.0) or np.any(dhi < 0.0):
            raise OpticsError("OPTICS_INPUT_INVALID", "DNI and DHI must be finite and nonnegative.")
        n = float(self.module_tubes)
        beam_active = dni > 0.0
        parts = self.beam(np.where(beam_active, el, -1.0), np.atleast_1d(azimuth_deg), kappa)
        c = parts["c"]
        sin_el = np.sin(np.radians(np.maximum(el, 0.0)))
        ghi = dni * sin_el + dhi
        sky, sea = self._hemisphere("sky"), self._hemisphere("sea")
        sky_scale, sea_scale = dhi / math.pi, self.optics.sea_albedo * ghi / math.pi
        beam_scale = dni * c
        out: dict[str, np.ndarray] = {
            "beam_intercepted": beam_scale * parts["width"] / n,
            "sky_intercepted": sky_scale * sky["intercept"] / n,
            "sea_intercepted": sea_scale * sea["intercept"] / n,
        }
        out["intercepted"] = out["beam_intercepted"] + out["sky_intercepted"] + out["sea_intercepted"]
        out["transmitted"] = (beam_scale * parts["transmitted"] + sky_scale * sky["transmitted"]
                              + sea_scale * sea["transmitted"]) / n
        beam_thin = beam_scale * parts["thin"] / n
        diffuse_thin = (sky_scale * sky["thin"] + sea_scale * sea["thin"]) / n
        out["thin"] = beam_thin + diffuse_thin
        area = math.pi * (self.optics.diameter / 2.0) ** 2
        out["i0_eq"] = out["thin"] / area
        with np.errstate(divide="ignore", invalid="ignore"):
            out["diffuse_share"] = np.where(out["thin"] > 0.0, diffuse_thin / np.where(out["thin"] > 0.0, out["thin"], 1.0), 0.0)
        lit = np.where(beam_active & (parts["width"] > 0.0) | beam_active, parts["width"] / (n * self.optics.diameter), 0.0)
        out["beam_unshaded_fraction"] = np.where(beam_active & (el > 0.0) & (c > _C_MIN), lit, np.nan)
        if kappa is not None:
            kappa_arr = np.broadcast_to(np.asarray(kappa, dtype=np.float64), el.shape)
            sky_abs = self.diffuse_absorption("sky", kappa_arr) if np.any(dhi > 0.0) else np.zeros(el.shape)
            sea_abs = (self.diffuse_absorption("sea", kappa_arr)
                       if np.any(sea_scale > 0.0) else np.zeros(el.shape))
            out["absorbed"] = (beam_scale * parts["absorbed"] + sky_scale * sky_abs + sea_scale * sea_abs) / n
        return out


@cache
def array_model(optics: Optics) -> ArrayModel:
    return ArrayModel(optics)


# ------------------------------------------------------------------------------------- engine hand-off


def sun_position(epochs: np.ndarray, site: dict[str, Any], conditions: dict[str, float]) -> tuple[np.ndarray, np.ndarray]:
    """Apparent solar elevation and azimuth (degrees) at UTC epochs, pvlib SPA with the profile's conditions."""
    import pandas as pd
    import pvlib

    index = pd.DatetimeIndex(pd.to_datetime(np.asarray(epochs, dtype=np.float64), unit="s", utc=True))
    frame = pvlib.solarposition.spa_python(
        index, float(site["latitude"]), float(site["longitude"]), altitude=float(site["elevation_m"]),
        pressure=float(conditions["pressure_pa"]), temperature=float(conditions["temperature_c"]),
        delta_t=float(conditions["delta_t"]))
    return frame["apparent_elevation"].to_numpy(dtype=np.float64), frame["azimuth"].to_numpy(dtype=np.float64)


def build_handoff(optics: Optics, epochs_mid: np.ndarray, site: dict[str, Any], conditions: dict[str, float],
                  dni_par: np.ndarray, dhi_par: np.ndarray) -> dict[str, np.ndarray]:
    """Per-interval arrays the engine indexes in its right-hand side (sun at each interval midpoint)."""
    elevation, azimuth = sun_position(epochs_mid, site, conditions)
    if not (np.all(np.isfinite(elevation)) and np.all(np.isfinite(azimuth))):
        raise OpticsError("OPTICS_INPUT_INVALID", "The solar position is not finite for the profile times.")
    values = array_model(optics).evaluate(elevation, azimuth, dni_par, dhi_par)
    return {"elevation_deg": elevation, "azimuth_deg": azimuth, "i0_eq": values["i0_eq"],
            "diffuse_fraction": np.clip(values["diffuse_share"], 0.0, 1.0),
            "intercepted": values["intercepted"], "beam_unshaded_fraction": values["beam_unshaded_fraction"]}
