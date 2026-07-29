from pathlib import Path

path = Path(__file__).with_name("s3_apply_once.py")
text = path.read_text(encoding="utf-8")
old = '''# The first two exact happy-path monkeypatches.
for _ in range(2):
    replace_once(
        "backend/tests/bluecad/test_evidence_egress.py",
        ''' + "'''" + '''        "_current_lineage_sight",
        lambda _lineage: _matching_sight(),
''' + "'''" + ''',
        ''' + "'''" + '''        "_current_lineage_authority_snapshot",
        lambda _lineage: _matching_authority_snapshot(),
''' + "'''" + ''',
    )
'''
new = '''# Replace the two exact happy-path monkeypatches together.
target = ROOT / "backend/tests/bluecad/test_evidence_egress.py"
source = target.read_text(encoding="utf-8")
old_snapshot = ''' + "'''" + '''        "_current_lineage_sight",
        lambda _lineage: _matching_sight(),
''' + "'''" + '''
new_snapshot = ''' + "'''" + '''        "_current_lineage_authority_snapshot",
        lambda _lineage: _matching_authority_snapshot(),
''' + "'''" + '''
count = source.count(old_snapshot)
if count != 2:
    raise RuntimeError(
        "backend/tests/bluecad/test_evidence_egress.py: "
        f"expected two snapshot replacements, found {count}"
    )
target.write_text(source.replace(old_snapshot, new_snapshot, 2), encoding="utf-8")
'''
count = text.count(old)
if count != 1:
    raise RuntimeError(f"s3 transfer loop: expected one block, found {count}")
path.write_text(text.replace(old, new, 1), encoding="utf-8")
Path(__file__).unlink()
