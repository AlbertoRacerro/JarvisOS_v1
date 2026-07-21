from pathlib import Path


def test_grade_status_registry_lists_backend_slices() -> None:
    text = Path("../docs/specs/STATUS.md").read_text(encoding="utf-8")
    row = next(line for line in text.splitlines() if line.startswith("| 062 |"))
    assert "in_review" in row
    assert "pull/166" in row
    assert "pull/167" in row
    assert "frontend" in row
