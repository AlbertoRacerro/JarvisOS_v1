from pathlib import Path


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise SystemExit(f"expected one target in {path}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


replace_once(
    Path("backend/app/modules/bluecad/cad_link_topology_execute.py"),
    "SET status = 'parked', parked_reason = 'cad_link_abandoned',",
    "SET status = 'parked', parked_reason = 'cad_link_failed',",
)
replace_once(
    Path("backend/tests/bluecad/test_cad_link_topology_concurrency.py"),
    'assert candidate.parked_reason == "cad_link_abandoned"',
    'assert candidate.parked_reason == "cad_link_failed"',
)
