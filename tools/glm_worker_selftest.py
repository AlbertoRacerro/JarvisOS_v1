from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

import glm_worker_entry as entry


def _run(*args: str, cwd: Path | None = None) -> None:
    subprocess.run(args, cwd=cwd, check=True, capture_output=True, text=True)


def _init_repo(root: Path) -> str:
    _run("git", "init", "-q", cwd=root)
    _run("git", "config", "user.email", "smoke@example.invalid", cwd=root)
    _run("git", "config", "user.name", "GLM Harness Smoke", cwd=root)
    (root / "fixture").mkdir()
    (root / "fixture/existing.txt").write_text("alpha\n", encoding="utf-8")
    (root / "fixture/delete.txt").write_text("delete-me\n", encoding="utf-8")
    (root / "fixture/rename-old.txt").write_text("rename-me\n", encoding="utf-8")
    _run("git", "add", ".", cwd=root)
    _run("git", "commit", "-qm", "fixture base", cwd=root)
    return subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=root, check=True, capture_output=True, text=True
    ).stdout.strip()


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="glm-harness-selftest-") as raw:
        root = Path(raw) / "repo"
        root.mkdir()
        target_sha = _init_repo(root)
        output = Path(raw) / "evidence"
        output.mkdir()

        entry._ALLOWED_PATHS = (
            "fixture/existing.txt",
            "fixture/new.txt",
            "fixture/delete.txt",
            "fixture/rename-old.txt",
            "fixture/rename-new.txt",
        )
        entry._BASE_REF = target_sha

        assert entry._path_is_allowed("fixture/existing.txt")
        assert not entry._path_is_allowed("outside.txt")
        entry.harness._safe_path(root, "fixture/existing.txt", write=True)
        try:
            entry.harness._safe_path(root, "outside.txt", write=True)
        except ValueError as exc:
            assert "outside task allowed_paths" in str(exc)
        else:
            raise AssertionError("allowed-path boundary did not reject outside write")
        try:
            entry.harness._safe_path(root, ".git/config", write=True)
        except ValueError:
            pass
        else:
            raise AssertionError("protected .git write was not rejected")

        (root / "fixture/existing.txt").write_text("alpha\nbeta\n", encoding="utf-8")
        (root / "fixture/new.txt").write_text("new-file\n", encoding="utf-8")
        (root / "fixture/delete.txt").unlink()
        (root / "fixture/rename-old.txt").rename(root / "fixture/rename-new.txt")

        diff, status = entry._capture_workspace_with_manifest(root, output)
        assert "new.txt" in diff
        assert "existing.txt" in diff
        assert "delete.txt" in diff
        assert "rename" in status.lower() or "rename" in diff.lower() or "rename-new.txt" in diff

        manifest = json.loads((output / "artifact_manifest.json").read_text(encoding="utf-8"))
        assert manifest["target_sha"] == target_sha
        assert manifest["patch_apply_to_exact_target"]["clean"] is True
        paths = {item["path"]: item for item in manifest["files"]}
        assert paths["fixture/new.txt"]["exists"] is True
        assert paths["fixture/new.txt"]["sha256"]
        assert paths["fixture/delete.txt"]["exists"] is False
        assert any(item["status"].startswith("R") for item in manifest["files"])

        terminal_dir = Path(raw) / "terminal"
        terminal_dir.mkdir()
        (terminal_dir / "candidate.patch").write_text(diff, encoding="utf-8")
        ready = entry._terminal_state(terminal_dir, "candidate_patch", 0)
        assert ready["state"] == "candidate_ready"
        (terminal_dir / "candidate.patch").write_text("", encoding="utf-8")
        empty = entry._terminal_state(terminal_dir, "candidate_patch", 0)
        assert empty["state"] == "model_failure"
        (terminal_dir / "failure.json").write_text(
            json.dumps({"type": "MaxTurnsExceeded"}), encoding="utf-8"
        )
        model = entry._terminal_state(terminal_dir, "candidate_patch", 1)
        assert model["state"] == "model_failure"
        (terminal_dir / "failure.json").write_text(
            json.dumps({"type": "ValueError"}), encoding="utf-8"
        )
        harness = entry._terminal_state(terminal_dir, "candidate_patch", 1)
        assert harness["state"] == "harness_failure"

    print("glm harness deterministic self-tests: PASS")


if __name__ == "__main__":
    main()
