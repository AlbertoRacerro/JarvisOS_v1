"""Run OpenFOAM utilities and parse their ASCII outputs (logs and fields).

Only what the prototype needs: internal fields and patch ``value`` entries of
ASCII volScalar/volVector/surfaceScalar fields, and simpleFoam residual logs.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

FOAM_ETC_CANDIDATES = ("/usr/share/openfoam", "/usr/lib/openfoam/openfoam1912", "/opt/openfoam1912")


def foam_env() -> dict[str, str] | None:
    """Environment able to run the OpenFOAM binaries, or None if OpenFOAM is absent."""
    if shutil.which("simpleFoam") is None or shutil.which("blockMesh") is None:
        return None
    env = dict(os.environ)
    if "WM_PROJECT_DIR" not in env:
        for cand in FOAM_ETC_CANDIDATES:
            if Path(cand, "etc", "controlDict").is_file():
                env["WM_PROJECT_DIR"] = cand
                break
        else:
            return None
    env.setdefault("OMP_NUM_THREADS", "1")
    return env


def openfoam_version() -> str:
    env = foam_env()
    if env is None:
        return "absent"
    header = Path(env["WM_PROJECT_DIR"], "etc", "controlDict").read_text(errors="replace")
    match = re.search(r"Version:\s*(\S+)", header)
    pkg = subprocess.run(["dpkg-query", "-W", "-f=${Version}", "openfoam"], capture_output=True, text=True,
                         check=False)
    return f"OpenFOAM {match.group(1) if match else 'unknown'} (ESI), Ubuntu package {pkg.stdout.strip() or 'n/a'}"


def run(cmd: list[str], case_dir: Path, log_name: str) -> str:
    env = foam_env()
    if env is None:
        raise RuntimeError("OpenFOAM is not installed")
    proc = subprocess.run(cmd + ["-case", str(case_dir)], env=env, capture_output=True, text=True, check=False)
    log = proc.stdout + proc.stderr
    (Path(case_dir) / log_name).write_text(log)
    if proc.returncode != 0 or "FOAM FATAL" in log:
        raise RuntimeError(f"{' '.join(cmd)} failed in {case_dir}; see {log_name}:\n{log[-2000:]}")
    return log


# ---------------------------------------------------------------- logs

@dataclass
class SolverLog:
    iterations: int
    converged: bool
    initial_residuals: dict[str, list[float]] = field(default_factory=dict)
    continuity_local: list[float] = field(default_factory=list)
    continuity_cumulative: list[float] = field(default_factory=list)

    def final_residuals(self) -> dict[str, float]:
        return {k: v[-1] for k, v in self.initial_residuals.items() if v}


_RES = re.compile(r"Solving for (\w+), Initial residual = ([-\d.eE+]+)")
_CONT = re.compile(r"continuity errors : sum local = ([-\d.eE+]+), global = [-\d.eE+]+, cumulative = ([-\d.eE+]+)")
_TIME = re.compile(r"^Time = (\d+)\s*$", re.M)


def parse_solver_log(text: str) -> SolverLog:
    residuals: dict[str, list[float]] = {}
    # Only the first solve of each variable per iteration (GAMG p may print once; keep all U comps).
    for block in re.split(r"^Time = \d+\s*$", text, flags=re.M)[1:]:
        seen: set[str] = set()
        for name, val in _RES.findall(block):
            if name in seen:
                continue
            seen.add(name)
            residuals.setdefault(name, []).append(float(val))
    cont = _CONT.findall(text)
    times = _TIME.findall(text)
    converged = re.search(r"SIMPLE solution converged in", text) is not None
    return SolverLog(
        iterations=int(times[-1]) if times else 0,
        converged=converged,
        initial_residuals=residuals,
        continuity_local=[float(a) for a, _ in cont],
        continuity_cumulative=[float(b) for _, b in cont],
    )


# ---------------------------------------------------------------- fields

_NUM = r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?"


def _parse_values(body: str, count: int, vector: bool) -> np.ndarray:
    if vector:
        arr = np.array(re.findall(rf"\(({_NUM}) ({_NUM}) ({_NUM})\)", body), dtype=float)
        if arr.shape != (count, 3):
            raise ValueError(f"expected {count} vectors, parsed {arr.shape}")
        return arr
    arr = np.array(re.findall(_NUM, body), dtype=float)
    if arr.shape != (count,):
        raise ValueError(f"expected {count} scalars, parsed {arr.shape}")
    return arr


def _value_entry(text: str, start: int, key: str) -> tuple[np.ndarray, bool] | None:
    """Parse ``key uniform X;`` or ``key nonuniform List<T> N ( ... );`` at/after ``start``."""
    m = re.compile(rf"\b{key}\s+(uniform|nonuniform)\s+").search(text, start)
    if m is None:
        return None
    pos = m.end()
    if m.group(1) == "uniform":
        end = text.index(";", pos)
        tok = text[pos:end].strip()
        if tok.startswith("("):
            return np.array([float(v) for v in tok.strip("()").split()]), True
        return np.array([float(tok)]), True
    hm = re.compile(r"List<(scalar|vector)>\s+(\d+)\s*\(").match(text, pos)
    if hm is None:
        # zero-size lists are written as "List<scalar> 0()"
        hz = re.compile(r"List<(scalar|vector)>\s+0\s*\(\s*\)").match(text, pos)
        if hz:
            return np.zeros((0, 3) if hz.group(1) == "vector" else 0), False
        raise ValueError(f"cannot parse {key} entry")
    vector, count = hm.group(1) == "vector", int(hm.group(2))
    # Short lists are written inline ("8(a b ...)"), long ones one entry per line: match parens.
    depth, i = 1, hm.end()
    while depth:
        ch = text[i]
        depth += (ch == "(") - (ch == ")")
        i += 1
    return _parse_values(text[hm.end():i - 1], count, vector), False


def read_internal(path: Path) -> np.ndarray:
    text = Path(path).read_text()
    res = _value_entry(text, 0, "internalField")
    if res is None:
        raise ValueError(f"no internalField in {path}")
    return res[0]


def read_patch_value(path: Path, patch: str) -> np.ndarray:
    text = Path(path).read_text()
    bf = text.index("boundaryField")
    m = re.compile(rf"^\s*{re.escape(patch)}\s*\n\s*\{{", re.M).search(text, bf)
    if m is None:
        raise ValueError(f"patch {patch} not in {path}")
    res = _value_entry(text, m.end(), "value")
    if res is None:
        raise ValueError(f"patch {patch} has no value in {path}")
    return res[0]


def latest_time_dir(case_dir: Path) -> Path:
    times = []
    for p in Path(case_dir).iterdir():
        try:
            times.append((float(p.name), p))
        except ValueError:
            continue
    times.sort()
    if not times or times[-1][0] == 0:
        raise ValueError(f"no solution time directory in {case_dir}")
    return times[-1][1]
