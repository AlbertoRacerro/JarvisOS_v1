from pathlib import Path

STATUS_PATH = Path(__file__).resolve().parents[2] / "docs" / "specs" / "STATUS.md"


def test_grade_status_registry_lists_backend_slices() -> None:
    text = STATUS_PATH.read_text(encoding="utf-8")
    row = next(line for line in text.splitlines() if line.startswith("| 062 |"))
    assert "| 062 | blocked |" in row
    assert "Backend PRs #166 and #167 are merged" in row
    assert "blocked pending joint operator design" in row
    assert "no autonomous frontend implementation is authorized" in row
