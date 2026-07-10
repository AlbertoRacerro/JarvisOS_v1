from __future__ import annotations

import json
import os
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path

import jarvisos_data_root as jdr
import pytest
from app.core.config import get_settings
from app.modules.runner.safety import validate_run_paths, validate_script_path
from data_root_recovery_support import digest, seed_data_root

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "jarvisos_data_root.py"


def test_cross_root_restore_rebases_all_registered_paths_and_readback(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = tmp_path / "source"
    source.mkdir()
    seed_data_root(source)
    result = jdr.create_snapshot(
        source_root=source,
        destination=tmp_path / "snapshots",
        snapshot_id="roundtrip",
    )
    target = tmp_path / "restored"
    shutil.rmtree(source)

    jdr.restore_snapshot(snapshot_dir=result.snapshot_dir, target_root=target)

    with sqlite3.connect(target / "jarvisos.db") as connection:
        for stored_path, expected_hash in connection.execute("SELECT stored_path, sha256 FROM artifacts ORDER BY id"):
            artifact = Path(stored_path)
            assert target in artifact.parents
            assert artifact.is_file()
            assert digest(artifact) == expected_hash
        runner = connection.execute(
            "SELECT script_path, working_dir, input_file, output_dir, command_json FROM runner_jobs"
        ).fetchone()
        parameter_payload = json.loads(
            connection.execute("SELECT parameter_payload FROM simulation_runs").fetchone()[0]
        )
        assert connection.execute("PRAGMA integrity_check").fetchone() == ("ok",)
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []

    assert all(str(target) in value for value in runner[:4])
    assert str(target) in json.loads(runner[4])["argv"][1]
    assert str(target) in parameter_payload["geometry"]["step_path"]
    assert str(target) in parameter_payload["geometry"]["manifest_path"]

    monkeypatch.setenv("JARVISOS_DATA_ROOT", str(target))
    get_settings.cache_clear()
    assert validate_script_path("ws", runner[0]).is_file()
    validated_run_paths = validate_run_paths(
        "ws",
        "run",
        working_dir=runner[1],
        input_file=runner[2],
        output_dir=runner[3],
    )
    assert all(path.exists() for path in validated_run_paths)


def test_nonempty_target_requires_explicit_approval(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    seed_data_root(source)
    result = jdr.create_snapshot(
        source_root=source,
        destination=tmp_path / "snapshots",
        snapshot_id="destructive",
    )
    target = tmp_path / "target"
    target.mkdir()
    sentinel = target / "keep.txt"
    sentinel.write_text("keep", encoding="utf-8")

    with pytest.raises(jdr.DataRootError, match="explicit"):
        jdr.restore_snapshot(snapshot_dir=result.snapshot_dir, target_root=target)
    assert sentinel.read_text(encoding="utf-8") == "keep"

    jdr.restore_snapshot(
        snapshot_dir=result.snapshot_dir,
        target_root=target,
        allow_nonempty_target=True,
    )
    assert not sentinel.exists()
    assert (target / "jarvisos.db").is_file()


def test_failed_restore_preserves_snapshot_and_existing_target(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    seed_data_root(source)
    result = jdr.create_snapshot(
        source_root=source,
        destination=tmp_path / "snapshots",
        snapshot_id="rollback",
    )
    snapshot_hash = digest(result.snapshot_dir / "jarvisos.db")
    target = tmp_path / "target"
    target.mkdir()
    sentinel = target / "keep.txt"
    sentinel.write_text("keep", encoding="utf-8")

    def fail(_stage: str, _partial: Path) -> None:
        raise jdr.DataRootError("injected")

    with pytest.raises(jdr.DataRootError, match="injected"):
        jdr.restore_snapshot(
            snapshot_dir=result.snapshot_dir,
            target_root=target,
            allow_nonempty_target=True,
            failure_hook=fail,
        )
    assert sentinel.read_text(encoding="utf-8") == "keep"
    assert digest(result.snapshot_dir / "jarvisos.db") == snapshot_hash


def test_restore_rejects_path_outside_source_root(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    seed_data_root(source)
    with sqlite3.connect(source / "jarvisos.db") as connection:
        connection.execute(
            "UPDATE artifacts SET stored_path=? WHERE id=?",
            (str(tmp_path / "outside.txt"), "a1"),
        )
        connection.commit()
    result = jdr.create_snapshot(
        source_root=source,
        destination=tmp_path / "snapshots",
        snapshot_id="outside",
    )
    target = tmp_path / "target"
    with pytest.raises(jdr.DataRootError, match="outside"):
        jdr.restore_snapshot(snapshot_dir=result.snapshot_dir, target_root=target)
    assert not target.exists()
    assert result.snapshot_dir.exists()


def test_restore_rejects_undocumented_old_root_occurrence(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    seed_data_root(source)
    with sqlite3.connect(source / "jarvisos.db") as connection:
        connection.execute(
            "UPDATE runner_jobs SET command_json=?",
            (
                json.dumps(
                    {
                        "executable": "python",
                        "argv": ["python"],
                        "mystery": str(source / "secret"),
                    }
                ),
            ),
        )
        connection.commit()
    result = jdr.create_snapshot(
        source_root=source,
        destination=tmp_path / "snapshots",
        snapshot_id="unknown",
    )
    target = tmp_path / "target"
    with pytest.raises(jdr.DataRootError, match="undocumented"):
        jdr.restore_snapshot(snapshot_dir=result.snapshot_dir, target_root=target)
    assert not target.exists()
    assert result.snapshot_dir.exists()


def test_snapshot_and_restore_target_symlinks_are_rejected(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    seed_data_root(source)
    result = jdr.create_snapshot(
        source_root=source,
        destination=tmp_path / "snapshots",
        snapshot_id="links",
    )
    snapshot_link = tmp_path / "snapshot-link"
    try:
        os.symlink(result.snapshot_dir, snapshot_link, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks unavailable")
    with pytest.raises(jdr.DataRootError, match="symlink"):
        jdr.verify_snapshot(snapshot_link)

    real_target = tmp_path / "real-target"
    real_target.mkdir()
    target_link = tmp_path / "target-link"
    os.symlink(real_target, target_link, target_is_directory=True)
    with pytest.raises(jdr.DataRootError, match="symlink"):
        jdr.restore_snapshot(snapshot_dir=result.snapshot_dir, target_root=target_link)


def test_cli_snapshot_verify_restore(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    seed_data_root(source)
    destination = tmp_path / "snapshots"
    created = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "snapshot",
            "--source-root",
            str(source),
            "--destination",
            str(destination),
            "--snapshot-id",
            "cli",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert created.returncode == 0, created.stderr
    snapshot = destination / "snapshot-cli"
    checked = subprocess.run(
        [sys.executable, str(SCRIPT), "verify", str(snapshot)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert checked.returncode == 0, checked.stderr
    target = tmp_path / "restored"
    restored = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "restore",
            str(snapshot),
            "--target-root",
            str(target),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert restored.returncode == 0, restored.stderr
    assert (target / "jarvisos.db").is_file()
