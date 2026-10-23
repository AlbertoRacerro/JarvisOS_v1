"""Read an ASCII OpenFOAM polyMesh and compute face/cell geometry with OpenFOAM's own
decomposition (triangle fan about the face average; pyramids about the estimated cell
centre). Needed because function objects (writeCellCentres, wallShearStress, yPlus)
abort in the Ubuntu 24.04 openfoam 1912 package: ``dictionary::digest()`` fails on its
SHA-1 stream, so any ``functions`` entry or ``postProcess -func`` is unusable there.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np


def _list_body(text: str) -> tuple[int, str]:
    body = text[text.index("}") + 1:]  # skip FoamFile header
    m = re.search(r"^(\d+)\s*\n\(", body, re.M)
    if m is None:
        raise ValueError("no list in polyMesh file")
    return int(m.group(1)), body[m.end():body.rindex(")")]


def _read_points(path: Path) -> np.ndarray:
    n, body = _list_body(path.read_text())
    pts = np.array([row.split() for row in re.findall(r"\(([^()]+)\)", body)], dtype=float)
    if pts.shape != (n, 3):
        raise ValueError(f"expected {n} points, parsed {pts.shape}")
    return pts


def _read_faces(path: Path) -> list[list[int]]:
    n, body = _list_body(path.read_text())
    faces = [list(map(int, f.split())) for f in re.findall(r"\d+\(([^()]*)\)", body)]
    if len(faces) != n:
        raise ValueError(f"expected {n} faces, parsed {len(faces)}")
    return faces


def _read_labels(path: Path) -> np.ndarray:
    n, body = _list_body(path.read_text())
    arr = np.array(body.split(), dtype=int)
    if arr.size != n:
        raise ValueError(f"expected {n} labels in {path.name}, parsed {arr.size}")
    return arr


def _read_boundary(path: Path) -> dict[str, tuple[int, int]]:
    text = path.read_text()
    patches = {}
    for name, body in re.findall(r"^\s*(\w+)\s*\n\s*\{([^}]*)\}", text[text.index("}") + 1:], re.M):
        n = int(re.search(r"nFaces\s+(\d+);", body).group(1))
        start = int(re.search(r"startFace\s+(\d+);", body).group(1))
        patches[name] = (start, n)
    return patches


@dataclass
class Geometry:
    face_centres: np.ndarray
    face_areas: np.ndarray       # area vectors (owner -> outward)
    cell_centres: np.ndarray
    cell_volumes: np.ndarray
    owner: np.ndarray
    patches: dict[str, tuple[int, int]]

    def patch_slice(self, name: str) -> slice:
        start, n = self.patches[name]
        return slice(start, start + n)


def read_geometry(case_dir: Path) -> Geometry:
    mesh = Path(case_dir) / "constant" / "polyMesh"
    pts = _read_points(mesh / "points")
    faces = _read_faces(mesh / "faces")
    owner = _read_labels(mesh / "owner")
    neigh = _read_labels(mesh / "neighbour")
    n_faces = len(faces)
    n_cells = int(owner.max()) + 1

    fc = np.zeros((n_faces, 3))
    fa = np.zeros((n_faces, 3))
    sizes = np.array([len(f) for f in faces])
    for size in np.unique(sizes):
        idx = np.nonzero(sizes == size)[0]
        p = pts[np.array([faces[i] for i in idx])]          # (m, size, 3)
        if size == 3:
            fc[idx] = p.mean(axis=1)
            fa[idx] = 0.5 * np.cross(p[:, 1] - p[:, 0], p[:, 2] - p[:, 0])
            continue
        pc = p.mean(axis=1)
        sum_n = np.zeros((idx.size, 3))
        sum_a = np.zeros(idx.size)
        sum_ac = np.zeros((idx.size, 3))
        for k in range(size):
            a, b = p[:, k], p[:, (k + 1) % size]
            c = a + b + pc
            nvec = np.cross(b - a, pc - a)
            mag = np.linalg.norm(nvec, axis=1)
            sum_n += nvec
            sum_a += mag
            sum_ac += mag[:, None] * c
        fc[idx] = sum_ac / (3.0 * sum_a[:, None])
        fa[idx] = 0.5 * sum_n

    n_int = neigh.size
    c_est = np.zeros((n_cells, 3))
    count = np.zeros(n_cells)
    np.add.at(c_est, owner, fc)
    np.add.at(count, owner, 1)
    np.add.at(c_est, neigh, fc[:n_int])
    np.add.at(count, neigh, 1)
    c_est /= count[:, None]

    vol3 = np.zeros(n_cells)
    csum = np.zeros((n_cells, 3))
    pyr_o = np.einsum("ij,ij->i", fa, fc - c_est[owner])
    np.add.at(vol3, owner, pyr_o)
    np.add.at(csum, owner, pyr_o[:, None] * (0.75 * fc + 0.25 * c_est[owner]))
    pyr_n = np.einsum("ij,ij->i", fa[:n_int], c_est[neigh] - fc[:n_int])
    np.add.at(vol3, neigh, pyr_n)
    np.add.at(csum, neigh, pyr_n[:, None] * (0.75 * fc[:n_int] + 0.25 * c_est[neigh]))
    centres = csum / vol3[:, None]
    return Geometry(fc, fa, centres, vol3 / 3.0, owner, _read_boundary(mesh / "boundary"))
