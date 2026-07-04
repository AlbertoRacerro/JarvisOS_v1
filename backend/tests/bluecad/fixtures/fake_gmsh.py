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

ok_mesh = """*NODE
1,0,0,0
2,1,0,0
3,0,1,0
4,0,0,1
*ELEMENT, TYPE=C3D4, ELSET=BODY
1,1,2,3,4
*ELEMENT, TYPE=S3, ELSET=BC_run1_port_a
2,1,2,3
*ELEMENT, TYPE=S3, ELSET=LOAD_joint1_port_b
3,1,3,4
"""
empty_mesh = """*NODE
1,0,0,0
2,1,0,0
3,0,1,0
4,0,0,1
*ELEMENT, TYPE=C3D4, ELSET=BODY
1,1,2,3,4
*ELEMENT, TYPE=S3, ELSET=BC_run1_port_a
*ELEMENT, TYPE=S3, ELSET=LOAD_joint1_port_b
3,1,3,4
"""
out.write_text(ok_mesh if mode != "empty" else empty_mesh)
(pathlib.Path.cwd() / "mesh.msh").write_text("$MeshFormat\n")
print("Info: fake gmsh quality ok")
