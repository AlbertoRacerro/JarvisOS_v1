from pathlib import Path

script_path = Path("scripts/daily_development_continuation.py")
test_path = Path("backend/tests/test_daily_development_continuation.py")

script = script_path.read_text(encoding="utf-8")
old = '''    r"oidc=(?P<oidc>[A-Za-z0-9._-]+) -->",
    re.I,
)
MAX_OPEN_PULLS = 1000
'''
new = '''    r"oidc=(?P<oidc>[A-Za-z0-9._-]+) -->"
)
MAX_OPEN_PULLS = 1000
'''
if script.count(old) != 1:
    raise SystemExit("expected exactly one case-insensitive marker regex")
script_path.write_text(script.replace(old, new), encoding="utf-8")

tests = test_path.read_text(encoding="utf-8")
anchor = '''def test_marker_with_result_inconsistent_with_heads_is_ignored():
    forged = marker()
    forged["body"] = forged["body"].replace(
        "result=changed", "result=no_change", 1
    )
    checkpoint, terminal = mod.checkpoint_for(
        candidate(), [forged], verifier=AcceptVerifier()
    )
    assert checkpoint == BASE
    assert terminal is False


'''
addition = '''def test_marker_with_noncanonical_phase_case_is_ignored():
    forged = marker()
    forged["body"] = forged["body"].replace("phase=final", "phase=FINAL", 1)
    checkpoint, terminal = mod.checkpoint_for(
        candidate(), [forged], verifier=AcceptVerifier()
    )
    assert checkpoint == BASE
    assert terminal is False


'''
if tests.count(anchor) != 1:
    raise SystemExit("expected exactly one marker-result test insertion point")
if "test_marker_with_noncanonical_phase_case_is_ignored" in tests:
    raise SystemExit("marker phase-case regression test already exists")
test_path.write_text(tests.replace(anchor, anchor + addition), encoding="utf-8")
