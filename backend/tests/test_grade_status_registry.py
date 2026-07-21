from pathlib import Path

STATUS_PATH = Path(__file__).resolve().parents[2] / "docs" / "specs" / "STATUS.md"


def test_grade_status_registry_lists_backend_slices() -> None:
    text = STATUS_PATH.read_text(encoding="utf-8")
    row = next(line for line in text.splitlines() if line.startswith("| 062 |"))
    cells = [cell.strip() for cell in row.strip().strip("|").split("|")]
    assert cells[1] == "blocked"
    assert cells[2] == "—"
    assert "Backend PRs #166 and #167 are merged" in row
    assert "joint operator design" in row
    assert "autonomous frontend implementation" in row
