from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.worktree_writer_guard import WriterGuardBusy, exclusive_writer_guard


def test_writer_guard_is_stable_and_non_reentrant(tmp_path: Path) -> None:
    guard = tmp_path / "worktree.guard"

    with exclusive_writer_guard(guard):
        assert guard.exists()
        with pytest.raises(WriterGuardBusy):
            with exclusive_writer_guard(guard):
                pass

    assert guard.exists()
    with exclusive_writer_guard(guard):
        pass
    assert guard.exists()


def test_writer_guard_is_released_by_process_death(tmp_path: Path) -> None:
    guard = tmp_path / "worktree.guard"
    marker = tmp_path / "locked"
    code = """
import sys
import time
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from scripts.worktree_writer_guard import exclusive_writer_guard
with exclusive_writer_guard(Path(sys.argv[2])):
    Path(sys.argv[3]).write_text('locked', encoding='utf-8')
    time.sleep(60)
"""
    proc = subprocess.Popen(
        [sys.executable, "-c", code, str(ROOT), str(guard), str(marker)],
        cwd=ROOT,
    )
    try:
        deadline = time.monotonic() + 10
        while not marker.exists() and time.monotonic() < deadline:
            if proc.poll() is not None:
                pytest.fail(f"guard child exited early with {proc.returncode}")
            time.sleep(0.02)
        assert marker.exists(), "child did not acquire guard"

        with pytest.raises(WriterGuardBusy):
            with exclusive_writer_guard(guard):
                pass
    finally:
        proc.kill()
        proc.wait(timeout=10)

    with exclusive_writer_guard(guard):
        pass
    assert guard.exists()
