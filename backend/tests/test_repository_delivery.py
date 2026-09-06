from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "repository_delivery.py"
spec = importlib.util.spec_from_file_location("repository_delivery", SCRIPT)
assert spec and spec.loader
repository_delivery = importlib.util.module_from_spec(spec)
sys.modules["repository_delivery"] = repository_delivery
spec.loader.exec_module(repository_delivery)

DeliveryCode = repository_delivery.DeliveryCode
DeliveryRefusal = repository_delivery.DeliveryRefusal
RemotePolicy = repository_delivery.RemotePolicy
RepositoryDelivery = repository_delivery.RepositoryDelivery
is_sensitive_path = repository_delivery.is_sensitive_path


def git(cwd: Path, *args: str, check: bool = True) -> str:
    completed = subprocess.run(
        ["git", *args], cwd=cwd, text=True, capture_output=True, check=False
    )
    if check and completed.returncode != 0:
        raise AssertionError(completed.stderr or completed.stdout)
    return completed.stdout.strip()


def repo_pair(tmp_path: Path) -> tuple[Path, Path, str]:
    remote = tmp_path / "remote.git"
    work = tmp_path / "work"
    git(tmp_path, "init", "--bare", str(remote))
    git(tmp_path, "clone", str(remote), str(work))
    git(work, "config", "user.name", "Spec 141 Test")
    git(work, "config", "user.email", "spec141@example.invalid")
    (work / "README.md").write_text("base\n", encoding="utf-8")
    git(work, "add", "README.md")
    git(work, "commit", "-m", "base")
    git(work, "branch", "-M", "feature")
    git(work, "push", "origin", "HEAD:refs/heads/feature")
    return remote, work, git(work, "rev-parse", "HEAD")


def delivery(work: Path) -> RepositoryDelivery:
    return RepositoryDelivery(
        work,
        remote_policy=RemotePolicy(allow_local_path_for_tests=True),
    )


def test_sensitive_path_baseline_and_source_code_carveout() -> None:
    for path in [
        ".github/workflows/ci.yml",
        "AGENTS.md",
        "CODEOWNERS",
        ".github/CODEOWNERS",
        ".env",
        ".env.local",
        "private/token.txt",
        "scripts/repository_delivery.py",
    ]:
        assert is_sensitive_path(path), path
    for path in [
        "backend/app/modules/ai/token_counter.py",
        "backend/app/modules/ai/api_key_handler.py",
        "backend/tests/test_normal.py",
    ]:
        assert not is_sensitive_path(path), path


def test_absent_remote_branch_refuses_without_creation(tmp_path: Path) -> None:
    _remote, work, _base = repo_pair(tmp_path)
    git(work, "checkout", "-b", "other")
    intended = git(work, "rev-parse", "HEAD")
    with pytest.raises(DeliveryRefusal) as exc:
        delivery(work).guarded_push(
            branch="other", intended_local_commit=intended, expected_remote_head="a" * 40
        )
    assert exc.value.code == DeliveryCode.REMOTE_BRANCH_ABSENT
    assert delivery(work).remote_head("other") == ""


def test_stale_expected_remote_head_refuses_before_push(tmp_path: Path) -> None:
    _remote, work, base = repo_pair(tmp_path)
    (work / "README.md").write_text("base\nnext\n", encoding="utf-8")
    git(work, "commit", "-am", "next")
    intended = git(work, "rev-parse", "HEAD")
    with pytest.raises(DeliveryRefusal) as exc:
        delivery(work).guarded_push(
            branch="feature", intended_local_commit=intended, expected_remote_head="b" * 40
        )
    assert exc.value.code == DeliveryCode.STALE_REMOTE_HEAD
    assert delivery(work).remote_head("feature") == base


def test_non_fast_forward_intended_commit_refuses(tmp_path: Path) -> None:
    _remote, work, base = repo_pair(tmp_path)
    git(work, "checkout", "--orphan", "unrelated")
    git(work, "rm", "-rf", ".")
    (work / "OTHER.md").write_text("unrelated\n", encoding="utf-8")
    git(work, "add", "OTHER.md")
    git(work, "commit", "-m", "unrelated")
    unrelated = git(work, "rev-parse", "HEAD")
    git(work, "branch", "-M", "feature")
    with pytest.raises(DeliveryRefusal) as exc:
        delivery(work).guarded_push(
            branch="feature", intended_local_commit=unrelated, expected_remote_head=base
        )
    assert exc.value.code == DeliveryCode.NON_FAST_FORWARD_REFUSED
    assert delivery(work).remote_head("feature") == base


def test_guarded_push_requires_exact_post_push_remote_sha(tmp_path: Path) -> None:
    _remote, work, base = repo_pair(tmp_path)
    (work / "README.md").write_text("base\nnext\n", encoding="utf-8")
    git(work, "commit", "-am", "next")
    intended = git(work, "rev-parse", "HEAD")
    result = delivery(work).guarded_push(
        branch="feature", intended_local_commit=intended, expected_remote_head=base
    )
    assert result.code == DeliveryCode.REMOTE_VERIFIED
    assert result.remote_head == intended
    assert result.changed_paths == ("README.md",)
    assert delivery(work).remote_head("feature") == intended


def test_replace_ref_refuses_before_network_mutation(tmp_path: Path) -> None:
    _remote, work, base = repo_pair(tmp_path)
    (work / "README.md").write_text("base\nnext\n", encoding="utf-8")
    git(work, "commit", "-am", "next")
    intended = git(work, "rev-parse", "HEAD")
    git(work, "replace", base, intended)
    with pytest.raises(DeliveryRefusal) as exc:
        delivery(work).guarded_push(
            branch="feature", intended_local_commit=intended, expected_remote_head=base
        )
    assert exc.value.code == DeliveryCode.GIT_HISTORY_REPLACEMENT_REFUSED
    assert delivery(work).remote_head("feature") == base


def test_legacy_grafts_refuses(tmp_path: Path) -> None:
    _remote, work, base = repo_pair(tmp_path)
    (work / "README.md").write_text("base\nnext\n", encoding="utf-8")
    git(work, "commit", "-am", "next")
    intended = git(work, "rev-parse", "HEAD")
    common = Path(git(work, "rev-parse", "--path-format=absolute", "--git-common-dir"))
    (common / "info").mkdir(exist_ok=True)
    (common / "info" / "grafts").write_text(f"{intended} {base}\n", encoding="utf-8")
    with pytest.raises(DeliveryRefusal) as exc:
        delivery(work).guarded_push(
            branch="feature", intended_local_commit=intended, expected_remote_head=base
        )
    assert exc.value.code == DeliveryCode.GIT_HISTORY_REPLACEMENT_REFUSED
    assert delivery(work).remote_head("feature") == base


def test_unsafe_git_config_refuses(tmp_path: Path) -> None:
    _remote, work, base = repo_pair(tmp_path)
    (work / "README.md").write_text("base\nnext\n", encoding="utf-8")
    git(work, "commit", "-am", "next")
    intended = git(work, "rev-parse", "HEAD")
    git(work, "config", "url.https://evil.invalid/.insteadOf", "https://github.com/")
    with pytest.raises(DeliveryRefusal) as exc:
        delivery(work).guarded_push(
            branch="feature", intended_local_commit=intended, expected_remote_head=base
        )
    assert exc.value.code == DeliveryCode.GIT_CONFIG_UNSAFE


def test_default_branch_and_generic_invalid_ref_are_structurally_refused(tmp_path: Path) -> None:
    _remote, work, _base = repo_pair(tmp_path)
    d = delivery(work)
    for branch in ["master", "main", "refs/heads/feature", "../feature", "-force"]:
        with pytest.raises(DeliveryRefusal) as exc:
            d.assert_branch_allowed(branch)
        assert exc.value.code == DeliveryCode.PROTECTED_BRANCH
