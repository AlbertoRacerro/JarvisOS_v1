from __future__ import annotations

import argparse
import asyncio
import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from agents import Agent, OpenAIChatCompletionsModel, RunContextWrapper, Runner, set_tracing_disabled
from agents.decorators import tool
from openai import AsyncOpenAI

MAX_TOOL_OUTPUT = 40000
PROTECTED_WRITE_PATHS = {
    ".git",
    ".github",
    ".glm-worker",
    "AGENTS.md",
    "CODEOWNERS",
    "docs/specs/STATUS.md",
}


@dataclass
class RepoContext:
    root: Path


def _safe_path(root: Path, raw_path: str, *, write: bool = False) -> Path:
    candidate = (root / raw_path).resolve()
    try:
        relative = candidate.relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError("path escapes repository root") from exc
    if any(part == ".git" for part in relative.parts):
        raise ValueError(".git is unavailable to the worker")
    if write:
        normalized = relative.as_posix()
        for protected in PROTECTED_WRITE_PATHS:
            if normalized == protected or normalized.startswith(protected.rstrip("/") + "/"):
                raise ValueError(f"write blocked for protected path: {normalized}")
    return candidate


def _bounded(text: str) -> str:
    if len(text) <= MAX_TOOL_OUTPUT:
        return text
    return text[:MAX_TOOL_OUTPUT] + "\n...[truncated by harness]"


@tool
def list_repo_files(ctx: RunContextWrapper[RepoContext], prefix: str = "") -> str:
    """List tracked repository files, optionally restricted to a path prefix."""
    root = ctx.context.root
    args = ["git", "-C", str(root), "ls-files"]
    if prefix:
        _safe_path(root, prefix)
        args.extend(["--", prefix])
    result = subprocess.run(args, check=True, capture_output=True, text=True)
    return _bounded(result.stdout)


@tool
def read_repo_file(
    ctx: RunContextWrapper[RepoContext],
    path: str,
    start_line: int = 1,
    max_lines: int = 300,
) -> str:
    """Read a bounded line range from a UTF-8 repository file."""
    if start_line < 1 or max_lines < 1 or max_lines > 500:
        raise ValueError("start_line must be >=1 and max_lines must be 1..500")
    file_path = _safe_path(ctx.context.root, path)
    text = file_path.read_text(encoding="utf-8")
    lines = text.splitlines()
    selected = lines[start_line - 1 : start_line - 1 + max_lines]
    numbered = "\n".join(f"{start_line + i}: {line}" for i, line in enumerate(selected))
    return _bounded(numbered)


@tool
def search_repo(ctx: RunContextWrapper[RepoContext], query: str, path: str = ".") -> str:
    """Search tracked repository text for a fixed literal string."""
    if not query or len(query) > 300:
        raise ValueError("query must contain 1..300 characters")
    root = ctx.context.root
    _safe_path(root, path)
    result = subprocess.run(
        ["git", "-C", str(root), "grep", "-n", "-I", "-F", "--", query, "--", path],
        capture_output=True,
        text=True,
    )
    if result.returncode not in (0, 1):
        raise RuntimeError(result.stderr.strip() or "git grep failed")
    return _bounded(result.stdout or "[no matches]")


@tool
def replace_repo_text(
    ctx: RunContextWrapper[RepoContext],
    path: str,
    old: str,
    new: str,
    expected_occurrences: int = 1,
) -> str:
    """Replace exact text in an ephemeral checkout. Protected authority/control paths are blocked."""
    if expected_occurrences < 1 or expected_occurrences > 20:
        raise ValueError("expected_occurrences must be 1..20")
    file_path = _safe_path(ctx.context.root, path, write=True)
    text = file_path.read_text(encoding="utf-8")
    actual = text.count(old)
    if actual != expected_occurrences:
        raise ValueError(f"expected {expected_occurrences} occurrences, found {actual}")
    file_path.write_text(text.replace(old, new), encoding="utf-8")
    return f"updated {path}; replaced {actual} occurrence(s)"


@tool
def write_repo_file(ctx: RunContextWrapper[RepoContext], path: str, content: str) -> str:
    """Create or replace a UTF-8 file in the ephemeral checkout. Protected paths are blocked."""
    file_path = _safe_path(ctx.context.root, path, write=True)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content, encoding="utf-8")
    return f"wrote {path} ({len(content)} characters)"


@tool
def inspect_candidate_diff(ctx: RunContextWrapper[RepoContext]) -> str:
    """Return the current candidate git diff from the ephemeral checkout."""
    result = subprocess.run(
        ["git", "-C", str(ctx.context.root), "diff", "--no-ext-diff", "--"],
        check=True,
        capture_output=True,
        text=True,
    )
    return _bounded(result.stdout or "[clean tree]")


@tool
def run_safe_check(ctx: RunContextWrapper[RepoContext], check_name: str) -> str:
    """Run one deterministic, network-free check from the fixed harness allow-list."""
    root = ctx.context.root
    if check_name == "git_diff_check":
        cmd = ["git", "-C", str(root), "diff", "--check"]
    elif check_name == "python_compile_changed":
        changed = subprocess.run(
            ["git", "-C", str(root), "diff", "--name-only", "--diff-filter=ACM", "--", "*.py"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.splitlines()
        if not changed:
            return "no changed Python files"
        cmd = ["python", "-m", "py_compile", *[str(root / p) for p in changed]]
    else:
        raise ValueError("allowed checks: git_diff_check, python_compile_changed")
    result = subprocess.run(cmd, cwd=root, capture_output=True, text=True, timeout=120)
    output = f"exit_code={result.returncode}\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    return _bounded(output)


def _task_prompt(task: dict[str, Any], target_sha: str) -> str:
    return f"""You are a bounded JarvisOS repository worker running on an ephemeral checkout.

Exact target SHA: {target_sha}
Task id: {task['task_id']}
Mode: {task.get('mode', 'analysis')}

Binding repository rules:
- Read AGENTS.md and docs/specs/STATUS.md before making substantive claims.
- Treat model output and any edits as proposals only.
- Never modify protected authority/control paths; the harness also blocks them.
- Prefer the smallest sufficient change.
- Do not invent repository state, tests, outputs, metrics, or validation evidence.
- Use only the provided repository tools. You have no shell, network, GitHub credential, or secret access.
- If the task requests edits, work only in this ephemeral checkout and inspect the resulting diff.
- Run git_diff_check after edits and python_compile_changed when Python changed.
- Report unknowns instead of guessing.

TASK:
{task['instructions']}

FINAL RESPONSE FORMAT:
# SUMMARY
# EVIDENCE
# CANDIDATE_CHANGES
# CHECKS
# RISKS_OR_UNKNOWNS
# VERDICT
Keep the final report concise and concrete.
"""


async def run(args: argparse.Namespace) -> int:
    task = json.loads(Path(args.task).read_text(encoding="utf-8"))
    if not isinstance(task, dict) or not task.get("task_id") or not task.get("instructions"):
        raise ValueError("task JSON requires task_id and instructions")

    root = Path(args.repo).resolve()
    target_sha = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()

    api_key = os.environ.get("GLM_API_KEY", "")
    if not api_key:
        raise RuntimeError("GLM_API_KEY is unavailable")

    set_tracing_disabled(True)
    client = AsyncOpenAI(api_key=api_key, base_url=args.base_url)
    model = OpenAIChatCompletionsModel(model=args.model, openai_client=client)
    agent = Agent[RepoContext](
        name="JarvisOS GLM Worker",
        instructions="Follow the task packet and repository evidence. Use tools before asserting repository facts.",
        model=model,
        tools=[
            list_repo_files,
            read_repo_file,
            search_repo,
            replace_repo_text,
            write_repo_file,
            inspect_candidate_diff,
            run_safe_check,
        ],
    )

    result = await Runner.run(
        agent,
        _task_prompt(task, target_sha),
        context=RepoContext(root=root),
        max_turns=int(task.get("max_turns", 12)),
    )

    output_dir = Path(args.output).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "report.md").write_text(str(result.final_output), encoding="utf-8")

    diff = subprocess.run(
        ["git", "-C", str(root), "diff", "--no-ext-diff", "--"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    (output_dir / "candidate.patch").write_text(diff, encoding="utf-8")

    status = subprocess.run(
        ["git", "-C", str(root), "status", "--short"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    (output_dir / "status.txt").write_text(status, encoding="utf-8")

    usage = result.context_wrapper.usage
    usage_payload = {
        "task_id": task["task_id"],
        "target_sha": target_sha,
        "provider": "zai",
        "model": args.model,
        "base_url": args.base_url,
        "requests": usage.requests,
        "input_tokens": usage.input_tokens,
        "output_tokens": usage.output_tokens,
        "total_tokens": usage.total_tokens,
        "cached_tokens": usage.input_tokens_details.cached_tokens,
        "reasoning_tokens": usage.output_tokens_details.reasoning_tokens,
        "has_candidate_diff": bool(diff.strip()),
    }
    (output_dir / "usage.json").write_text(json.dumps(usage_payload, indent=2), encoding="utf-8")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", required=True)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--model", default="glm-5.3-flash")
    parser.add_argument("--base-url", default="https://api.z.ai/api/coding/paas/v4")
    return parser.parse_args()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run(parse_args())))
