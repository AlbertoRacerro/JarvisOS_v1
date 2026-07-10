#!/usr/bin/env python3
from __future__ import annotations

import pathlib
import sys

args = sys.argv[1:]
out = pathlib.Path(args[args.index("-o") + 1])
cwd = str(pathlib.Path.cwd())
mode = "fail" if "failcase" in cwd else ("empty" if "emptycase" in cwd else "ok")

if mode == "fail":
    print("Error: meshing failed", file=sys.stderr)
    sys.exit(2)

ok_mesh = """*Heading
 fake real-style Gmsh Abaqus export
*NODE
1,0,0,0
2,1,0,0
3,0,1,0
4,0,0,1
*ELEMENT, TYPE=C3D4, ELSET=Volume1
1,1,2,3,4
*ELSET, ELSET=BODY
1,
*NSET, NSET=BC_run1_port_a
1,2,3,
*NSET, NSET=LOAD_joint1_port_b
1,3,4,
"""
empty_mesh = """*Heading
 fake real-style Gmsh Abaqus export
*NODE
1,0,0,0
2,1,0,0
3,0,1,0
4,0,0,1
*ELEMENT, TYPE=C3D4, ELSET=Volume1
1,1,2,3,4
*ELSET, ELSET=BODY
1,
*NSET, NSET=BC_run1_port_a
*NSET, NSET=LOAD_joint1_port_b
1,3,4,
"""
out.write_text(ok_mesh if mode != "empty" else empty_mesh, encoding="utf-8")
(pathlib.Path.cwd() / "mesh.msh").write_text("$MeshFormat\n", encoding="utf-8")
print("Info: fake gmsh quality ok")
