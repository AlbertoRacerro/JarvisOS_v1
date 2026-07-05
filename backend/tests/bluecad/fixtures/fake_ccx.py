#!/usr/bin/env python3
from __future__ import annotations

import pathlib
import sys
import time

job = sys.argv[1]
cwd = pathlib.Path.cwd()
mode = cwd.name
if "timeout" in mode:
    time.sleep(5)
if "solve_error" in mode:
    print("*ERROR fake solver failure")
    sys.exit(3)
if "diverged" in mode:
    print("non convergence detected")
    sys.exit(2)
if "parse_error" not in mode:
    (cwd / f"{job}.frd").write_text("""# synthetic minimal public-format-inspired fixture\nDISP 1 0 0 0\nDISP 2 3 4 0\nSTRESS 1 1 12.5\nSTRESS 1 2 275.0\n""", encoding="utf-8")
else:
    (cwd / f"{job}.frd").write_text("DISP 1 0 0 0\n", encoding="utf-8")
(cwd / f"{job}.dat").write_text("REACTION 1 -10 0 0\n", encoding="utf-8")
print("fake ccx completed")
