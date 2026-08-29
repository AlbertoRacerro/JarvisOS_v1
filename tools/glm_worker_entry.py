from __future__ import annotations

import asyncio
import subprocess
from pathlib import Path

import glm_worker_harness as harness


# The original harness remains the safety/authority implementation. This thin
# development-only entrypoint only reduces request/context size and shifts
# candidate_patch budget from broad exploration toward coding/verification.
# 112 candidate attempts proved that large preloads and large read-tool outputs
# can time out before the model reaches its first write.
harness.MAX_EVIDENCE_PACKET = 70_000
harness.MAX_TOOL_OUTPUT = 12_000
harness.MODE_EXPLORATION_LIMIT["candidate_patch"] = 4
harness.MODE_WRITE_LIMIT["candidate_patch"] = 16
harness.MODE_VERIFICATION_LIMIT["candidate_patch"] = 10


def _bounded_context_file(root: Path, raw_path: str) -> str:
    path = harness._safe_path(root, raw_path)
    if not path.exists() or not path.is_file():
        return f"===== {raw_path} =====\n[missing at exact target]"

    # Mandatory process files need only their live operating sections here; the
    # task packet supplies the exact target and selected spec/readiness authority.
    # Requested implementation authority gets a larger bounded excerpt.
    line_limit = {
        "AGENTS.md": 120,
        "docs/specs/STATUS.md": 75,
    }.get(raw_path, 160)

    text = path.read_text(encoding="utf-8", errors="replace")
    all_lines = text.splitlines()
    lines = all_lines[:line_limit]
    body = "\n".join(f"{i + 1}: {line}" for i, line in enumerate(lines))
    if len(all_lines) > line_limit:
        body += f"\n...[file truncated after {line_limit} lines by bounded entrypoint]"
    return f"===== {raw_path} =====\n{body}"


harness._read_context_file = _bounded_context_file


# `git diff` does not include untracked files. Candidate workers are allowed to
# create bounded new files, so a final artifact could otherwise claim success
# while silently omitting most of the candidate. Before the base harness captures
# its final patch, mark only the worker-created untracked paths as intent-to-add
# in the *ephemeral* checkout. This changes no repository commit or remote state,
# but makes ordinary `git diff` include complete new-file patches. Every path is
# revalidated through the same protected-write boundary before touching the index.
_original_capture_workspace = harness._capture_workspace


def _capture_workspace_with_new_files(root: Path, output_dir: Path) -> tuple[str, str]:
    raw = subprocess.run(
        ["git", "-C", str(root), "ls-files", "--others", "--exclude-standard", "-z"],
        check=True,
        capture_output=True,
    ).stdout
    untracked = [item.decode("utf-8") for item in raw.split(b"\0") if item]
    for raw_path in untracked:
        harness._safe_path(root, raw_path, write=True)
    if untracked:
        subprocess.run(
            ["git", "-C", str(root), "add", "--intent-to-add", "--", *untracked],
            check=True,
        )
    return _original_capture_workspace(root, output_dir)


harness._capture_workspace = _capture_workspace_with_new_files


if __name__ == "__main__":
    raise SystemExit(asyncio.run(harness.run(harness.parse_args())))
