from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "repository_delivery.py"
spec = importlib.util.spec_from_file_location("repository_delivery_config_escape", SCRIPT)
assert spec and spec.loader
repository_delivery = importlib.util.module_from_spec(spec)
sys.modules["repository_delivery_config_escape"] = repository_delivery
spec.loader.exec_module(repository_delivery)

DeliveryCode = repository_delivery.DeliveryCode
DeliveryRefusal = repository_delivery.DeliveryRefusal
RemotePolicy = repository_delivery.RemotePolicy
RepositoryDelivery = repository_delivery.RepositoryDelivery


def git(cwd: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", *args], cwd=cwd, text=True, capture_output=True, check=False
    )
    if completed.returncode != 0:
        raise AssertionError(completed.stderr or completed.stdout)
    return completed.stdout.strip()


def delivery(work: Path) -> RepositoryDelivery:
    return RepositoryDelivery(
        work,
        remote_policy=RemotePolicy(allow_local_path_for_tests=True),
    )


def test_local_include_cannot_import_unsafe_git_authority(tmp_path: Path) -> None:
    work = tmp_path / "work"
    work.mkdir()
    git(work, "init")
    included = tmp_path / "hostile.inc"
    included.write_text(
        "[core]\n\thooksPath = /tmp/hostile-hooks\n"
        "[credential]\n\thelper = !echo hostile\n",
        encoding="utf-8",
    )
    git(work, "config", "include.path", str(included))

    # Git would consume the imported executable/credential config on normal
    # operations, so the local include directive itself must fail closed.
    assert git(work, "config", "--get", "core.hooksPath") == "/tmp/hostile-hooks"
    with pytest.raises(DeliveryRefusal) as exc:
        delivery(work).assert_safe_config()
    assert exc.value.code == DeliveryCode.GIT_CONFIG_UNSAFE


def test_includeif_directive_is_structurally_refused() -> None:
    d = RepositoryDelivery(Path.cwd())
    with pytest.raises(DeliveryRefusal) as exc:
        d._assert_config_entries_safe(
            "includeif.gitdir:/tmp/project.path\n/tmp/hostile.inc\0"
        )
    assert exc.value.code == DeliveryCode.GIT_CONFIG_UNSAFE


def test_core_worktree_cannot_redirect_assigned_worktree(tmp_path: Path) -> None:
    work = tmp_path / "work"
    outside = tmp_path / "outside"
    work.mkdir()
    outside.mkdir()
    git(work, "init")
    (outside / "outside.txt").write_text("outside\n", encoding="utf-8")
    git(work, "config", "core.worktree", str(outside))

    # This demonstrates the causal filesystem escape: normal Git now treats the
    # external directory as its worktree. RepositoryDelivery must refuse before
    # status/stage/commit/push can inherit that redirected root.
    assert git(work, "rev-parse", "--show-toplevel") == str(outside.resolve())
    with pytest.raises(DeliveryRefusal) as exc:
        delivery(work).assert_safe_config()
    assert exc.value.code == DeliveryCode.GIT_CONFIG_UNSAFE
