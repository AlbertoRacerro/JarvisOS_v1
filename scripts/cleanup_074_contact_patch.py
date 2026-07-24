from __future__ import annotations

import ast
import re
from pathlib import Path

PATH = Path("backend/app/modules/bluecad/cad_link_topology_preflight.py")
NAMES = (
    "_terminal_annular_face_evidence",
    "_annular_face_evidence",
    "_face_normal",
    "_validate_no_extra_contact",
    "_allowed_contact_neighborhood",
    "_shape_distance",
)

text = PATH.read_text(encoding="utf-8")
for name in NAMES:
    while True:
        starts = [
            match.start()
            for match in re.finditer(rf"(?m)^def {re.escape(name)}\(", text)
        ]
        if len(starts) <= 1:
            break
        duplicate_start = starts[1]
        next_definition = re.search(r"(?m)^def ", text[duplicate_start + 1 :])
        if next_definition is None:
            duplicate_end = len(text)
        else:
            duplicate_end = duplicate_start + 1 + next_definition.start()
        text = text[:duplicate_start] + text[duplicate_end:]

module = ast.parse(text)
counts: dict[str, int] = {}
for node in module.body:
    if isinstance(node, ast.FunctionDef):
        counts[node.name] = counts.get(node.name, 0) + 1
for name in NAMES:
    if counts.get(name) != 1:
        raise SystemExit(f"expected one top-level definition for {name}, found {counts.get(name, 0)}")

PATH.write_text(text, encoding="utf-8")
