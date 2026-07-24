from __future__ import annotations

from pathlib import Path

SOURCE = Path("scripts/apply_074_contact_fix.py")
source = SOURCE.read_text(encoding="utf-8")
lines = source.splitlines(keepends=True)

helper_start = next(index for index, line in enumerate(lines) if line.startswith("def replace_function"))
constants_start = next(
    index for index, line in enumerate(lines) if line.startswith('if "CONTACT_NEIGHBORHOOD_AXIAL_MM"')
)
helper = '''def replace_function(name: str, replacement: str) -> None:
    global text
    marker = f"def {name}("
    start = text.find(marker)
    if start < 0 or text.find(marker, start + 1) >= 0:
        raise SystemExit(f"expected one function {name}")
    next_function = text.find("\\ndef ", start + 1)
    end = len(text) if next_function < 0 else next_function + 1
    text = text[:start] + replacement.rstrip() + "\\n\\n\\n" + text[end:]


'''
lines[helper_start:constants_start] = helper.splitlines(keepends=True)

loop_start = next(index for index, line in enumerate(lines) if line.startswith("loop_pattern = re.compile"))
loop_replacement_start = next(
    index for index, line in enumerate(lines) if line.startswith("loop_replacement =")
)
loop_setup = '''loop_start_marker = "        topology = _classify_pair_intersection(left.shape, right.shape)\\n"
loop_end_marker = "        if connected or has_contact:\\n"

'''
lines[loop_start:loop_replacement_start] = loop_setup.splitlines(keepends=True)

sub_index = next(
    index for index, line in enumerate(lines) if line.startswith("text = loop_pattern.sub")
)
loop_apply = '''loop_start_index = text.find(loop_start_marker)
if loop_start_index < 0 or text.find(loop_start_marker, loop_start_index + 1) >= 0:
    raise SystemExit("expected one pair-classification start marker")
loop_end_index = text.find(loop_end_marker, loop_start_index)
if loop_end_index < 0:
    raise SystemExit("pair-classification end marker missing")
text = text[:loop_start_index] + loop_replacement + text[loop_end_index:]
'''
lines[sub_index : sub_index + 1] = loop_apply.splitlines(keepends=True)

transformed = "".join(lines)
namespace = {"__name__": "__main__", "__file__": str(SOURCE)}
exec(compile(transformed, str(SOURCE), "exec"), namespace)
