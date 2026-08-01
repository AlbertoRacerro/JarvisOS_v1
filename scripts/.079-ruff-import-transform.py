from pathlib import Path

script_path = Path("scripts/daily_development_continuation.py")
test_path = Path("backend/tests/test_daily_development_continuation.py")

script = script_path.read_text(encoding="utf-8")
old = "from typing import Callable, Protocol\n"
new = "from collections.abc import Callable\nfrom typing import Protocol\n"
if script.count(old) != 1:
    raise SystemExit("expected exactly one legacy Callable import")
script_path.write_text(script.replace(old, new), encoding="utf-8")

tests = test_path.read_text(encoding="utf-8")
name = "test_control_script_uses_modern_callable_import"
if name in tests:
    raise SystemExit("Ruff import regression test already exists")
tests += "\n\ndef test_control_script_uses_modern_callable_import():\n    text = SCRIPT.read_text(encoding=\"utf-8\")\n    assert \"from collections.abc import Callable\" in text\n    assert \"from typing import Callable\" not in text\n"
test_path.write_text(tests, encoding="utf-8")
