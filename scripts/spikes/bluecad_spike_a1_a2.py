"""BLUECAD A1/A2 environment spike for build123d export and validity checks."""

from __future__ import annotations

import importlib
import importlib.metadata
import math
import platform
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import build123d
from build123d import Cylinder, Torus, export_step, export_stl
from OCP.BRep import BRep_Tool
from OCP.BRepCheck import BRepCheck_Analyzer


OUTER_D = 110.0
WALL_T = 4.0
LENGTH = 1000.0
BEND_RADIUS = 400.0
BEND_ANGLE_DEG = 90.0
STL_TOLERANCE = 0.001
STL_ANGULAR_TOLERANCE = 0.1
GLTF_LINEAR_DEFLECTION = 0.001
GLTF_ANGULAR_DEFLECTION = 0.1

REPO_ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_DIR = REPO_ROOT / "reports" / "bluecad_spike_a1_a2_artifacts"


@dataclass(frozen=True)
class GeometryCase:
    name: str
    shape: Any
    analytic_volume_mm3: float


def package_version(name: str) -> str:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return "not installed"


def build_geometry() -> list[GeometryCase]:
    outer_radius = OUTER_D / 2.0
    inner_radius = outer_radius - WALL_T

    cylinder = Cylinder(outer_radius, LENGTH) - Cylinder(inner_radius, LENGTH + 2.0)
    cylinder_volume = math.pi * (outer_radius**2 - inner_radius**2) * LENGTH

    bend = Torus(
        BEND_RADIUS,
        outer_radius,
        major_angle=BEND_ANGLE_DEG,
    ) - Torus(
        BEND_RADIUS,
        inner_radius,
        major_angle=BEND_ANGLE_DEG,
    )
    bend_volume = (
        (BEND_ANGLE_DEG / 360.0)
        * 2.0
        * math.pi**2
        * BEND_RADIUS
        * (outer_radius**2 - inner_radius**2)
    )

    return [
        GeometryCase("hollow_cylinder", cylinder, cylinder_volume),
        GeometryCase("torus_bend_90", bend, bend_volume),
    ]


def export_native_glb(shape: Any, glb_path: Path) -> str:
    export_gltf = getattr(build123d, "export_gltf", None)
    if export_gltf is None:
        raise AttributeError("build123d.export_gltf does not exist")

    export_gltf(
        shape,
        glb_path,
        binary=True,
        linear_deflection=GLTF_LINEAR_DEFLECTION,
        angular_deflection=GLTF_ANGULAR_DEFLECTION,
    )
    return "build123d.export_gltf(binary=True)"


def export_trimesh_glb(stl_path: Path, glb_path: Path) -> str:
    trimesh = importlib.import_module("trimesh")
    mesh = trimesh.load_mesh(stl_path)
    mesh.export(glb_path, file_type="glb")
    return "trimesh.load_mesh(...).export(file_type='glb')"


def export_case(case: GeometryCase) -> dict[str, Any]:
    step_path = ARTIFACT_DIR / f"{case.name}.step"
    stl_path = ARTIFACT_DIR / f"{case.name}.stl"
    glb_path = ARTIFACT_DIR / f"{case.name}.glb"

    timings: dict[str, float] = {}

    start = time.perf_counter()
    step_ok = export_step(case.shape, step_path)
    timings["step_s"] = time.perf_counter() - start

    start = time.perf_counter()
    stl_ok = export_stl(
        case.shape,
        stl_path,
        tolerance=STL_TOLERANCE,
        angular_tolerance=STL_ANGULAR_TOLERANCE,
    )
    timings["stl_s"] = time.perf_counter() - start

    start = time.perf_counter()
    glb_path_used = "native"
    glb_error = None
    try:
        glb_api = export_native_glb(case.shape, glb_path)
    except Exception as exc:
        glb_path_used = "trimesh_fallback"
        glb_error = f"{type(exc).__name__}: {exc}"
        glb_api = export_trimesh_glb(stl_path, glb_path)
    timings["glb_s"] = time.perf_counter() - start

    return {
        "step_ok": step_ok,
        "stl_ok": stl_ok,
        "glb_path": glb_path_used,
        "glb_api": glb_api,
        "glb_native_error": glb_error,
        "files": {
            "step": step_path.relative_to(REPO_ROOT).as_posix(),
            "stl": stl_path.relative_to(REPO_ROOT).as_posix(),
            "glb": glb_path.relative_to(REPO_ROOT).as_posix(),
        },
        "sizes_bytes": {
            "step": step_path.stat().st_size,
            "stl": stl_path.stat().st_size,
            "glb": glb_path.stat().st_size,
        },
        "timings": timings,
    }


def check_case(case: GeometryCase) -> dict[str, Any]:
    shells = list(case.shape.shells())
    shell_closed = [BRep_Tool.IsClosed_s(shell.wrapped) for shell in shells]

    return {
        "build123d.Shape.is_valid": case.shape.is_valid,
        "build123d.Shape.is_manifold": case.shape.is_manifold,
        "OCP.BRepCheck.BRepCheck_Analyzer.IsValid": BRepCheck_Analyzer(
            case.shape.wrapped
        ).IsValid(),
        "OCP.BRep.BRep_Tool.IsClosed_s(shell.wrapped)": shell_closed,
        "shell_count": len(shells),
    }


def print_versions() -> None:
    print("VERSIONS")
    print(f"python={platform.python_version()} executable={sys.executable}")
    print(f"build123d={package_version('build123d')}")
    print(f"cadquery-ocp-novtk={package_version('cadquery-ocp-novtk')}")
    print(f"cadquery-ocp-proxy={package_version('cadquery-ocp-proxy')}")
    print(f"OCP_distribution={package_version('OCP')}")
    print(f"trimesh={package_version('trimesh')}")
    print()


def main() -> int:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    print_versions()

    start = time.perf_counter()
    cases = build_geometry()
    build_s = time.perf_counter() - start

    print("INPUTS")
    print(
        "outer_d_mm={outer_d} wall_t_mm={wall_t} length_mm={length} "
        "bend_radius_mm={bend_radius} bend_angle_deg={bend_angle}".format(
            outer_d=OUTER_D,
            wall_t=WALL_T,
            length=LENGTH,
            bend_radius=BEND_RADIUS,
            bend_angle=BEND_ANGLE_DEG,
        )
    )
    print()
    print("TIMINGS")
    print(f"build_s={build_s:.6f}")

    for case in cases:
        print()
        print(f"CASE {case.name}")

        start = time.perf_counter()
        checks = check_case(case)
        checks_s = time.perf_counter() - start

        exports = export_case(case)
        export_total_s = sum(exports["timings"].values())

        computed_volume = case.shape.volume
        rel_error = abs(computed_volume - case.analytic_volume_mm3) / case.analytic_volume_mm3

        print(f"computed_volume_mm3={computed_volume:.12f}")
        print(f"analytic_volume_mm3={case.analytic_volume_mm3:.12f}")
        print(f"relative_volume_error={rel_error:.12e}")
        print(f"checks={checks}")
        print(f"checks_s={checks_s:.6f}")
        print(f"exports={exports}")
        print(f"export_total_s={export_total_s:.6f}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
