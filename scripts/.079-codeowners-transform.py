from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    target = Path(path)
    text = target.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected one match, found {count}")
    target.write_text(text.replace(old, new, 1), encoding="utf-8")


replace_once(
    "scripts/daily_development_continuation.py",
    '    "CODEOWNERS",\n    "scripts/daily_development_continuation.py",\n',
    '    "CODEOWNERS",\n    "docs/CODEOWNERS",\n    "scripts/daily_development_continuation.py",\n',
)

replace_once(
    "backend/tests/test_daily_development_continuation.py",
    '        "CODEOWNERS",\n        "scripts/daily_development_continuation.py",\n',
    '        "CODEOWNERS",\n        "docs/CODEOWNERS",\n        "scripts/daily_development_continuation.py",\n',
)
