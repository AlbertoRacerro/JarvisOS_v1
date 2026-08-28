from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from agents import (
    Agent,
    MaxTurnsExceeded,
    OpenAIChatCompletionsModel,
    RunContextWrapper,
    Runner,
    StopAtTools,
    set_tracing_disabled,
)
from agents.decorators import tool
from openai import AsyncOpenAI

MAX_TOOL_OUTPUT = 40000
HARD_MAX_TURNS = 36
MODE_MIN_TURNS = {
    "analysis": 14,
    "preflight": 14,
    "adversarial_pre_review": 20,
    "review": 20,
    "candidate_patch": 28,
}
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
    mode: str
    base_ref: str | None = None
    tool_counts: dict[str, int] = field(default_factory=dict)


def _record_tool(ctx: RunContextWrapper[RepoContext], name: str) -> None:
    ctx.context.tool_counts[name] = ctx.context.tool_counts.get(name, 0) + 1


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


def _validate_exact_sha(value: Any, field_name: str) -> str | None:
    if value in (None, ""):
        return None
    text = str(value)
    if not re.fullmatch(r"[0-9a-f]{40}", text):
        raise ValueError(f"{field_name} must be an exact 40-character lowercase commit SHA")
    return text


def _effective_turn_budget(task: dict[str, Any]) -> tuple[int | None, int]:
    mode = str(task.get("mode", "analysis"))
    minimum = MODE_MIN_TURNS.get(mode, 16)
    raw_requested = task.get("max_turns")
    if raw_requested in (None, ""):
        requested = minimum
    else:
        requested = int(raw_requested)
        if requested < 1:
            raise ValueError("max_turns must be >= 1")
    effective = min(HARD_MAX_TURNS, max(requested, minimum))
    return (None if raw_requested in (None, "") else requested), effective


@tool
def list_repo_files(ctx: RunContextWrapper[RepoContext], prefix: str = "") -> str:
    """List tracked repository files, optionally restricted to a path prefix."""
    _record_tool(ctx, "list_repo_files")
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
    _record_tool(ctx, "read_repo_file")
    if start_line < 1 or max_lines < 1 or max_lines > 500:
        raise ValueError("start_line must be >=1 and max_lines must be 1..500")
    file_path = _safe_path(ctx.context.root, path)
    text = file_path.read_text(encoding="utf-8")
    lines = text.splitlines()
    selected = lines[start_line - 1 : start_line - 1 + max_lines]
    numbered = "\n".join(f"{start_line + i}: {line}" for i, line in enumerate(selected))
    return _bounded(numbered)


@tool
def read_repo_files(
    ctx: RunContextWrapper[RepoContext],
    paths: list[str],
    max_lines_each: int = 300,
) -> str:
    """Batch-read up to 12 known UTF-8 repository files in one tool call."""
    _record_tool(ctx, "read_repo_files")
    if not paths or len(paths) > 12:
        raise ValueError("paths must contain 1..12 repository files")
    if max_lines_each < 1 or max_lines_each > 500:
        raise ValueError("max_lines_each must be 1..500")

    chunks: list[str] = []
    for raw_path in paths:
        file_path = _safe_path(ctx.context.root, raw_path)
        text = file_path.read_text(encoding="utf-8")
        lines = text.splitlines()[:max_lines_each]
        numbered = "\n".join(f"{i + 1}: {line}" for i, line in enumerate(lines))
        chunks.append(f"===== {raw_path} =====\n{numbered}")
    return _bounded("\n\n".join(chunks))


@tool
def search_repo(ctx: RunContextWrapper[RepoContext], query: str, path: str = ".") -> str:
    """Search tracked repository text for a fixed literal string."""
    _record_tool(ctx, "search_repo")
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
def inspect_target_diff(ctx: RunContextWrapper[RepoContext]) -> str:
    """Read the immutable target diff against task.base_ref when an exact base SHA was supplied."""
    _record_tool(ctx, "inspect_target_diff")
    base_ref = ctx.context.base_ref
    if not base_ref:
        return "[base_ref not supplied by task packet]"
    result = subprocess.run(
        [
            "git",
            "-C",
            str(ctx.context.root),
            "diff",
            "--no-ext-diff",
            f"{base_ref}...HEAD",
            "--",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return _bounded(result.stdout or "[no target diff]")


@tool
def replace_repo_text(
    ctx: RunContextWrapper[RepoContext],
    path: str,
    old: str,
    new: str,
    expected_occurrences: int = 1,
) -> str:
    """Replace exact text in an ephemeral checkout. Protected authority/control paths are blocked."""
    _record_tool(ctx, "replace_repo_text")
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
    _record_tool(ctx, "write_repo_file")
    file_path = _safe_path(ctx.context.root, path, write=True)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content, encoding="utf-8")
    return f"wrote {path} ({len(content)} characters)"


@tool
def inspect_candidate_diff(ctx: RunContextWrapper[RepoContext]) -> str:
    """Return the current candidate git diff from the ephemeral checkout."""
    _record_tool(ctx, "inspect_candidate_diff")
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
    _record_tool(ctx, "run_safe_check")
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


@tool
def submit_result(ctx: RunContextWrapper[RepoContext], report: str) -> str:
    """Terminal action. Submit the completed concise report after evidence, edits, diff inspection, and checks."""
    _record_tool(ctx, "submit_result")
    cleaned = report.strip()
    if not cleaned:
        raise ValueError("report must not be empty")
    return _bounded(cleaned)


def _task_prompt(task: dict[str, Any], target_sha: str, effective_turns: int) -> str:
    mode = str(task.get("mode", "analysis"))
    base_ref = task.get("base_ref") or "[none]"
    context_files = task.get("context_files") or []
    context_hint = ", ".join(str(path) for path in context_files) if context_files else "[none supplied]"
    return f"""You are a bounded JarvisOS repository worker running on an ephemeral checkout.

Exact target SHA: {target_sha}
Exact base SHA for review diff: {base_ref}
Task id: {task['task_id']}
Mode: {mode}
Effective completion budget: up to {effective_turns} model turns.

Binding repository rules:
- Read AGENTS.md and docs/specs/STATUS.md before making substantive claims.
- Treat model output and any edits as proposals only.
- Never modify protected authority/control paths; the harness also blocks them.
- Prefer the smallest sufficient change.
- Do not invent repository state, tests, outputs, metrics, or validation evidence.
- Use only the provided repository tools. You have no shell, network, GitHub credential, or secret access.
- If the task requests edits, work only in this ephemeral checkout and inspect the resulting diff.
- Report unknowns instead of guessing.

Completion policy:
- Optimize for a correct completed task, not minimum token spend. Do not stop early merely to save turns.
- Avoid wasteful exploration: once evidence is sufficient, move to implementation/review and completion.
- Prefer read_repo_files when several known files must be read; do not serially reread unchanged files.
- When an exact base SHA is supplied, use inspect_target_diff early for review work.
- For edits, run git_diff_check and python_compile_changed when Python changed before completion.
- When the task is complete, call submit_result exactly once with the final report as the sole terminal tool call.
- Do not spend another turn emitting ordinary assistant text after completion; submit_result is the preferred terminal path.
- If evidence remains genuinely unavailable, state the bounded unknown in submit_result rather than looping.

Suggested context files from the task packet:
{context_hint}

TASK:
{task['instructions']}

FINAL REPORT FORMAT passed to submit_result:
# SUMMARY
# EVIDENCE
# CANDIDATE_CHANGES
# CHECKS
# RISKS_OR_UNKNOWNS
# VERDICT
Keep the report concise and concrete.
"""


def _capture_workspace(root: Path, output_dir: Path) -> tuple[str, str]:
    diff = subprocess.run(
        ["git", "-C", str(root), "diff", "--no-ext-diff", "--"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    status = subprocess.run(
        ["git", "-C", str(root), "status", "--short"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    (output_dir / "candidate.patch").write_text(diff, encoding="utf-8")
    (output_dir / "status.txt").write_text(status, encoding="utf-8")
    return diff, status


def _usage_payload(
    *,
    task: dict[str, Any],
    target_sha: str,
    args: argparse.Namespace,
    requested_turns: int | None,
    effective_turns: int,
    context: RepoContext,
    usage: Any | None,
    diff: str,
    completed: bool,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "task_id": task["task_id"],
        "target_sha": target_sha,
        "base_ref": context.base_ref,
        "mode": context.mode,
        "provider": "zai",
        "model": args.model,
        "base_url": args.base_url,
        "requested_max_turns": requested_turns,
        "effective_max_turns": effective_turns,
        "hard_max_turns": HARD_MAX_TURNS,
        "completed": completed,
        "has_candidate_diff": bool(diff.strip()),
        "tool_counts": dict(sorted(context.tool_counts.items())),
        "finalized_via_submit_result": context.tool_counts.get("submit_result", 0) > 0,
    }
    if usage is not None:
        payload.update(
            {
                "requests": usage.requests,
                "input_tokens": usage.input_tokens,
                "output_tokens": usage.output_tokens,
                "total_tokens": usage.total_tokens,
                "cached_tokens": usage.input_tokens_details.cached_tokens,
                "reasoning_tokens": usage.output_tokens_details.reasoning_tokens,
            }
        )
    return payload


async def run(args: argparse.Namespace) -> int:
    task = json.loads(Path(args.task).read_text(encoding="utf-8"))
    if not isinstance(task, dict) or not task.get("task_id") or not task.get("instructions"):
        raise ValueError("task JSON requires task_id and instructions")

    mode = str(task.get("mode", "analysis"))
    base_ref = _validate_exact_sha(task.get("base_ref"), "base_ref")
    requested_turns, effective_turns = _effective_turn_budget(task)

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

    output_dir = Path(args.output).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    context = RepoContext(root=root, mode=mode, base_ref=base_ref)

    set_tracing_disabled(True)
    client = AsyncOpenAI(api_key=api_key, base_url=args.base_url)
    model = OpenAIChatCompletionsModel(model=args.model, openai_client=client)
    agent = Agent[RepoContext](
        name="JarvisOS GLM Worker",
        instructions=(
            "Follow the immutable task packet and repository evidence. "
            "Use tools before asserting repository facts. Finish via submit_result once the task is complete."
        ),
        model=model,
        tools=[
            list_repo_files,
            read_repo_file,
            read_repo_files,
            search_repo,
            inspect_target_diff,
            replace_repo_text,
            write_repo_file,
            inspect_candidate_diff,
            run_safe_check,
            submit_result,
        ],
        tool_use_behavior=StopAtTools(stop_at_tool_names=["submit_result"]),
    )

    result = None
    failure: Exception | None = None
    usage = None
    try:
        result = await Runner.run(
            agent,
            _task_prompt(task, target_sha, effective_turns),
            context=context,
            max_turns=effective_turns,
        )
        usage = result.context_wrapper.usage
        (output_dir / "report.md").write_text(str(result.final_output), encoding="utf-8")
    except Exception as exc:
        failure = exc
        if isinstance(exc, MaxTurnsExceeded) and exc.run_data is not None:
            usage = exc.run_data.context_wrapper.usage
        (output_dir / "failure.json").write_text(
            json.dumps(
                {
                    "type": type(exc).__name__,
                    "message": str(exc),
                    "requested_max_turns": requested_turns,
                    "effective_max_turns": effective_turns,
                },
                indent=2,
            ),
            encoding="utf-8",
        )

    diff, _status = _capture_workspace(root, output_dir)
    usage_payload = _usage_payload(
        task=task,
        target_sha=target_sha,
        args=args,
        requested_turns=requested_turns,
        effective_turns=effective_turns,
        context=context,
        usage=usage,
        diff=diff,
        completed=failure is None,
    )
    (output_dir / "usage.json").write_text(json.dumps(usage_payload, indent=2), encoding="utf-8")

    diagnostic = {
        "task_id": task["task_id"],
        "target_sha": target_sha,
        "base_ref": base_ref,
        "mode": mode,
        "completed": failure is None,
        "failure_type": type(failure).__name__ if failure else None,
        "failure_message": str(failure) if failure else None,
        "tool_counts": dict(sorted(context.tool_counts.items())),
    }
    (output_dir / "diagnostic.json").write_text(json.dumps(diagnostic, indent=2), encoding="utf-8")
    return 0 if failure is None else 1


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
