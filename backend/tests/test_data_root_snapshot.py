from __future__ import annotations

import os
import shutil
import sqlite3
from pathlib import Path

import jarvisos_data_root as jdr
import pytest
from data_root_recovery_support import digest, rewrite_manifest, seed_data_root


def test_wal_snapshot_is_single_file_and_contains_uncheckpointed_commit(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    seed_data_root(source)
    writer = sqlite3.connect(source / "jarvisos.db")
    writer.execute("PRAGMA journal_mode=WAL")
    writer.execute("INSERT INTO workspaces VALUES (?)", ("wal-row",))
    writer.commit()

    result = jdr.create_snapshot(
        source_root=source,
        destination=tmp_path / "snapshots",
        snapshot_id="wal",
    )

    with sqlite3.connect(result.snapshot_dir / "jarvisos.db") as connection:
        assert connection.execute("SELECT COUNT(*) FROM workspaces WHERE id=?", ("wal-row",)).fetchone() == (1,)
    assert not (result.snapshot_dir / "jarvisos.db-wal").exists()
    assert not (result.snapshot_dir / "jarvisos.db-shm").exists()
    writer.close()


def test_snapshot_manifest_hashes_and_logs_exclusion(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    seed_data_root(source)
    result = jdr.create_snapshot(
        source_root=source,
        destination=tmp_path / "snapshots",
        snapshot_id="manifest",
    )

    manifest = jdr.verify_snapshot(result.snapshot_dir)
    assert manifest["excluded_roots"] == ["logs"]
    assert not (result.snapshot_dir / "logs").exists()
    for item in manifest["files"]:
        path = result.snapshot_dir.joinpath(*Path(item["path"]).parts)
        assert path.stat().st_size == item["size"]
        assert digest(path) == item["sha256"]


def test_source_file_mutation_fails_without_publishing(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    seed_data_root(source)

    def mutate(stage: str, root: Path, _connection: sqlite3.Connection) -> None:
        if stage == "after_database_backup":
            (root / "artifacts/ws/report.json").write_text("changed", encoding="utf-8")

    with pytest.raises(jdr.DataRootError):
        jdr.create_snapshot(
            source_root=source,
            destination=tmp_path / "snapshots",
            snapshot_id="file-mutation",
            mutation_hook=mutate,
        )
    assert not (tmp_path / "snapshots/snapshot-file-mutation").exists()


def test_source_database_mutation_fails_without_publishing(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    seed_data_root(source)

    def mutate(stage: str, root: Path, _connection: sqlite3.Connection) -> None:
        if stage == "after_database_backup":
            with sqlite3.connect(root / "jarvisos.db") as writer:
                writer.execute("INSERT INTO workspaces VALUES (?)", ("late",))
                writer.commit()

    with pytest.raises(jdr.DataRootError, match="database changed"):
        jdr.create_snapshot(
            source_root=source,
            destination=tmp_path / "snapshots",
            snapshot_id="db-mutation",
            mutation_hook=mutate,
        )
    assert not (tmp_path / "snapshots/snapshot-db-mutation").exists()


def test_symlink_special_file_and_case_collision_are_rejected(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    seed_data_root(source)
    try:
        os.symlink(
            source / "artifacts/ws/report.json",
            source / "artifacts/ws/link",
        )
    except (OSError, NotImplementedError):
        pytest.skip("symlinks unavailable")
    with pytest.raises(jdr.DataRootError, match="symlink"):
        jdr.create_snapshot(
            source_root=source,
            destination=tmp_path / "snapshots-a",
            snapshot_id="symlink",
        )
    (source / "artifacts/ws/link").unlink()

    if hasattr(os, "mkfifo"):
        fifo = source / "artifacts/ws/fifo"
        os.mkfifo(fifo)
        with pytest.raises(jdr.DataRootError, match="special"):
            jdr.create_snapshot(
                source_root=source,
                destination=tmp_path / "snapshots-b",
                snapshot_id="fifo",
            )
        fifo.unlink()

    (source / "artifacts/ws/Foo").write_text("a", encoding="utf-8")
    (source / "artifacts/ws/foo").write_text("b", encoding="utf-8")
    with pytest.raises(jdr.DataRootError, match="duplicate"):
        jdr.create_snapshot(
            source_root=source,
            destination=tmp_path / "snapshots-c",
            snapshot_id="case",
        )


def test_destination_under_source_and_invalid_retention_are_rejected(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    seed_data_root(source)
    with pytest.raises(jdr.DataRootError, match="outside"):
        jdr.create_snapshot(
            source_root=source,
            destination=source / "backups",
            snapshot_id="inside",
        )
    with pytest.raises(jdr.DataRootError, match="at least 1"):
        jdr.create_snapshot(
            source_root=source,
            destination=tmp_path / "snapshots",
            snapshot_id="retention",
            keep_last=0,
        )
    assert not (tmp_path / "snapshots/snapshot-retention").exists()


def test_partial_extra_corrupt_schema_row_count_and_escape_are_rejected(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    seed_data_root(source)
    destination = tmp_path / "snapshots"

    first = jdr.create_snapshot(source_root=source, destination=destination, snapshot_id="first")
    partial = destination / ".partial-copy"
    shutil.copytree(first.snapshot_dir, partial)
    with pytest.raises(jdr.DataRootError, match="partial"):
        jdr.verify_snapshot(partial)
    (first.snapshot_dir / "unexpected.txt").write_text("x", encoding="utf-8")
    with pytest.raises(jdr.DataRootError, match="file set mismatch"):
        jdr.verify_snapshot(first.snapshot_dir)

    second = jdr.create_snapshot(source_root=source, destination=destination, snapshot_id="second")
    rewrite_manifest(second.snapshot_dir, lambda data: data.__setitem__("schema_version", 999))
    with pytest.raises(jdr.DataRootError, match="unsupported"):
        jdr.verify_snapshot(second.snapshot_dir)

    third = jdr.create_snapshot(source_root=source, destination=destination, snapshot_id="third")
    database = third.snapshot_dir / "jarvisos.db"
    with sqlite3.connect(database) as connection:
        connection.execute("INSERT INTO workspaces VALUES (?)", ("tampered",))
        connection.commit()
        connection.execute("PRAGMA journal_mode=DELETE")

    def update_database_hash(data: dict[str, object]) -> None:
        for item in data["files"]:
            if item["path"] == "jarvisos.db":
                item["size"] = database.stat().st_size
                item["sha256"] = digest(database)

    rewrite_manifest(third.snapshot_dir, update_database_hash)
    with pytest.raises(jdr.DataRootError, match="row counts"):
        jdr.verify_snapshot(third.snapshot_dir)

    fourth = jdr.create_snapshot(source_root=source, destination=destination, snapshot_id="fourth")

    def inject_escape(data: dict[str, object]) -> None:
        data["files"][0]["path"] = "../escape"

    rewrite_manifest(fourth.snapshot_dir, inject_escape)
    with pytest.raises(jdr.DataRootError, match="canonical|relative"):
        jdr.verify_snapshot(fourth.snapshot_dir)


def test_retention_deletes_only_complete_verified_snapshots(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    seed_data_root(source)
    destination = tmp_path / "snapshots"
    jdr.create_snapshot(source_root=source, destination=destination, snapshot_id="a")
    jdr.create_snapshot(source_root=source, destination=destination, snapshot_id="b")
    partial = destination / ".partial-do-not-delete"
    partial.mkdir()
    (partial / "junk").write_text("x", encoding="utf-8")
    corrupt = destination / "snapshot-corrupt"
    corrupt.mkdir()
    (corrupt / "junk").write_text("x", encoding="utf-8")

    jdr.create_snapshot(
        source_root=source,
        destination=destination,
        snapshot_id="c",
        keep_last=2,
    )

    complete = {path.name for path in destination.iterdir() if path.name in {"snapshot-a", "snapshot-b", "snapshot-c"}}
    assert len(complete) == 2
    assert partial.exists()
    assert corrupt.exists()


def test_windows_rebase_is_case_insensitive_without_prefix_collision() -> None:
    assert (
        jdr.rebase_absolute_path(
            r"C:\JarvisOS\workspaces\a",
            r"c:\jarvisos",
            r"D:\Restored",
        )
        == r"D:\Restored\workspaces\a"
    )
    with pytest.raises(jdr.DataRootError):
        jdr.rebase_absolute_path(
            r"C:\JarvisOS-other\x",
            r"C:\JarvisOS",
            r"D:\Restored",
        )
    assert not jdr._string_mentions_source_root(r"C:\JarvisOS-other\x", r"C:\JarvisOS")
    assert jdr._string_mentions_source_root(r"prefix C:\JARVISOS\x suffix", r"C:\JarvisOS")
