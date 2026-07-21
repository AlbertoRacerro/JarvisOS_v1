from pathlib import Path


STATUS_PATH = Path(__file__).resolve().parents[2] / "docs" / "specs" / "STATUS.md"


def test_grade_status_registry_lists_backend_slices() -> None:
    text = STATUS_PATH.read_text(encoding="utf-8")
    row = next(line for line in text.splitlines() if line.startswith("| 062 |"))
    assert "| 062 | in_review |" in row or "| 062 | blocked |" in row
    assert "pull/166" in row
    assert "pull/167" in row
    assert "frontend" in row
