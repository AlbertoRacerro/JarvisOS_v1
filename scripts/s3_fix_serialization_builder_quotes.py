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
    elif stripped.startswith("return re.search(rf") and "str(value).lower()" in stripped:
        updated.append(
            '        return re.search(rf"(?i)^{str(value).lower()}(?![A-Za-z0-9_])", tail) is not None'
        )
        replacements += 1
    elif stripped.startswith("number = re.match("):
        updated.append(
            r'''        number = re.match(r"^([-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?)", tail)'''
        )
        replacements += 1
    else:
        updated.append(line)
if replacements != 4:
    raise RuntimeError(f"expected four serialization quote fixes, found {replacements}")
path.write_text("\n".join(updated) + "\n", encoding="utf-8")
