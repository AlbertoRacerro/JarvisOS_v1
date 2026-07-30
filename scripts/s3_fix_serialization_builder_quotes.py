from pathlib import Path

path = Path("scripts/s3_build_serialization_level_fix.py")
lines = path.read_text(encoding="utf-8").splitlines()
replacements = 0
for index, line in enumerate(lines):
    stripped = line.strip()
    if stripped == 'tail = tail.lstrip(" \\t\'\\"")':
        lines[index] = r'''    tail = tail.lstrip(" \\t'\\\"")'''
        replacements += 1
    elif stripped == 'candidate = tail.lstrip(" \\t\'\\"").casefold()':
        lines[index] = r'''    candidate = tail.lstrip(" \\t'\\\"").casefold()'''
        replacements += 1
if replacements != 2:
    raise RuntimeError(f"expected two quote fixes, found {replacements}")
path.write_text("\n".join(lines) + "\n", encoding="utf-8")
