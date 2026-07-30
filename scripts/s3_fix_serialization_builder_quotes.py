from pathlib import Path

path = Path("scripts/s3_build_serialization_level_fix.py")
lines = path.read_text(encoding="utf-8").splitlines()
updated: list[str] = []
replacements = 0
for line in lines:
    stripped = line.strip()
    if stripped.startswith("tail = tail.lstrip("):
        updated.extend(
            [
                "    tail = tail.lstrip()",
                r'''    tail = tail.lstrip("'\\\"")''',
            ]
        )
        replacements += 1
    elif stripped.startswith("candidate = tail.lstrip("):
        updated.extend(
            [
                "    candidate = tail.lstrip()",
                r'''    candidate = candidate.lstrip("'\\\"").casefold()''',
            ]
        )
        replacements += 1
    else:
        updated.append(line)
if replacements != 2:
    raise RuntimeError(f"expected two quote fixes, found {replacements}")
path.write_text("\n".join(updated) + "\n", encoding="utf-8")
