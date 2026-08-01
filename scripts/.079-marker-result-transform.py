from pathlib import Path

script_path = Path("scripts/daily_development_continuation.py")
test_path = Path("backend/tests/test_daily_development_continuation.py")

script = script_path.read_text(encoding="utf-8")
old = '''            if user.get("login") != "github-actions[bot]":
                continue
            audience = marker_audience(
'''
new = '''            if user.get("login") != "github-actions[bot]":
                continue
            expected_result = (
                "changed"
                if match.group("input") != match.group("output")
                else "no_change"
            )
            if match.group("result") != expected_result:
                continue
            audience = marker_audience(
'''
if script.count(old) != 1:
    raise SystemExit("expected exactly one marker authentication insertion point")
script_path.write_text(script.replace(old, new), encoding="utf-8")

tests = test_path.read_text(encoding="utf-8")
anchor = '''def test_marker_from_human_is_ignored_even_with_valid_token():
    checkpoint, _ = mod.checkpoint_for(
        candidate(), [marker(actor="AlbertoRacerro")],
        verifier=AcceptVerifier(),
    )
    assert checkpoint == BASE


'''
addition = '''def test_marker_with_result_inconsistent_with_heads_is_ignored():
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
if tests.count(anchor) != 1:
    raise SystemExit("expected exactly one marker test insertion point")
if "test_marker_with_result_inconsistent_with_heads_is_ignored" in tests:
    raise SystemExit("marker result regression test already exists")
test_path.write_text(tests.replace(anchor, anchor + addition), encoding="utf-8")
