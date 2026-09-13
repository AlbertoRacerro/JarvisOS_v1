from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from cloud_delivery_bridge import admit_acquisition, apply_and_verify  # noqa: E402
from codex_result_delivery_dispatch import (  # noqa: E402
    CODEX_MARKER,
    DELIVERY_MARKER,
    request_from_event,
)


def _git(repo: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def test_codex_result_dispatch_to_bridge_exact_head_apply(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init")
    _git(repo, "config", "user.name", "Fixture")
    _git(repo, "config", "user.email", "fixture@example.invalid")
    target = repo / "docs" / "runbooks" / "codex-result-fixture.md"
    target.parent.mkdir(parents=True)
    target.write_text("before\n", encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "fixture base")
    base_sha = _git(repo, "rev-parse", "HEAD")

    changed_path = "docs/runbooks/codex-result-fixture.md"
    patch = (
        f"diff --git a/{changed_path} b/{changed_path}\n"
        f"--- a/{changed_path}\n"
        f"+++ b/{changed_path}\n"
        "@@ -1 +1 @@\n"
        "-before\n"
        "+after\n"
    )
    metadata = {
        "version": 1,
        "pr": 633,
        "base_sha": base_sha,
        "target_ref": "test/codex-result-fixture",
        "patch_sha256": hashlib.sha256(patch.encode("utf-8")).hexdigest(),
        "changed_paths": [changed_path],
        "validation_profile": "docs",
    }
    body = (
        f"{CODEX_MARKER}\n"
        f"{DELIVERY_MARKER}\n"
        f"```json\n{json.dumps(metadata, sort_keys=True)}\n```\n"
        f"```diff\n{patch}\n```"
    )
    event = {
        "action": "created",
        "issue": {
            "number": 633,
            "pull_request": {"url": "https://api.github.test/pr/633"},
        },
        "comment": {
            "id": 123456,
            "author_association": "NONE",
            "user": {"login": "chatgpt-codex-connector[bot]", "type": "Bot"},
            "body": body,
        },
    }

    request = request_from_event(event)
    assert request.pr == 633
    assert request.payload_body_sha256 == hashlib.sha256(body.encode("utf-8")).hexdigest()

    payload = admit_acquisition(
        repository="AlbertoRacerro/JarvisOS_v1",
        pr_number=request.pr,
        acquisition={
            "comment": {
                "issue_url": "https://api.github.com/repos/AlbertoRacerro/JarvisOS_v1/issues/633",
                "body": body,
            },
            "pr": {
                "state": "open",
                "head": {
                    "ref": metadata["target_ref"],
                    "sha": base_sha,
                    "repo": {"full_name": "AlbertoRacerro/JarvisOS_v1"},
                },
            },
        },
    )
    patch_file = tmp_path / "fixture.patch"
    patch_file.write_text(patch, encoding="utf-8")
    apply_and_verify(repo, payload, patch_file)

    assert target.read_text(encoding="utf-8") == "after\n"
    assert _git(repo, "rev-parse", "HEAD") == base_sha
    assert _git(repo, "diff", "--name-only", base_sha, "--") == changed_path
