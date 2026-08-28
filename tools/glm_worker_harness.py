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
MAX_EVIDENCE_PACKET = 180000
MAX_EVIDENCE_FILE_LINES = 1200
HARD_MAX_TURNS = 36
MODE_MIN_TURNS = {
    "analysis": 14,
    "preflight": 14,
    "adversarial_pre_review": 20,
    "review": 20,
    "candidate_patch": 28,
}
MODE_EXPLORATION_LIMIT = {
    "analysis": 6,
    "preflight": 5,
    "adversarial_pre_review": 7,
    "review": 7,
    "candidate_patch": 10,
}
MODE_WRITE_LIMIT = {
    "analysis": 0,
    "preflight": 0,
    "adversarial_pre_review": 4,
    "review": 4,
    "candidate_patch": 10,
}
MODE_VERIFICATION_LIMIT = {
    "analysis": 3,
    "preflight": 3,
    "adversarial_pre_review": 5,
    "review": 5,
    "candidate_patch": 7,
}
EXPLORATION_TOOLS = {
    "list_repo_files",
    "read_repo_file",
    "read_repo_files",
    "search_repo",
    "inspect_target_diff",
}
WRITE_TOOLS = {"replace_repo_text", "write_repo_file"}
VERIFICATION_TOOLS = {"inspect_candidate_diff", "run_safe_check"}
MANDATORY_CONTEXT_FILES = ("AGENTS.md", "docs/specs/STATUS.md")
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
    exploration_calls: int = 0
    write_calls: int = 0
    verification_calls: int = 0
    exploration_limit: int = 6
    write_limit: int = 0
    verification_limit: int = 3
    evidence_packet_chars: int = 0


def _record_tool(ctx: RunContextWrapper[RepoContext], name: str) -> None:
    ctx.context.tool_counts[name] = ctx.context.tool_counts.get(name, 0) + 1
    if name in EXPLORATION_TOOLS:
        ctx.context.exploration_calls += 1
    elif name in WRITE_TOOLS:
        ctx.context.write_calls += 1
    elif name in VERIFICATION_TOOLS:
        ctx.context.verification_calls += 1


def _exploration_enabled(ctx: RunContextWrapper[RepoContext], _agent: Any) -> bool:
    return ctx.context.exploration_calls < ctx.context.exploration_limit


def _write_enabled(ctx: RunContextWrapper[RepoContext], _agent: Any) -> bool:
    return ctx.context.write_calls < ctx.context.write_limit


def _verification_enabled(ctx: RunContextWrapper[RepoContext], _agent: Any) -> bool:
    return ctx.context.verification_calls < ctx.context.verification_limit


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


def _bounded(text: str, limit: int = MAX_TOOL_OUTPUT) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + "\n...[truncated by harness]"


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


def _mode_limit(table: dict[str, int], mode: str, default: int) -> int:
    return int(table.get(mode, default))


def _read_context_file(root: Path, raw_path: str) -> str:
    path = _safe_path(root, raw_path)
    if not path.exists() or not path.is_file():
        return f"===== {raw_path} =====\n[missing at exact target]"
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()[:MAX_EVIDENCE_FILE_LINES]
    body = "\n".join(f"{i + 1}: {line}" for i, line in enumerate(lines))
    if len(text.splitlines()) > MAX_EVIDENCE_FILE_LINES:
        body += "\n...[file truncated by evidence packet]"
    return f"===== {raw_path} =====\n{body}"


def _build_evidence_packet(root: Path, task: dict[str, Any], base_ref: str | None) -> str:
    requested = task.get("context_files") or []
    if not isinstance(requested, list) or len(requested) > 20:
        raise ValueError("context_files must be a list of at most 20 repository paths")

    ordered_files: list[str] = []
    for raw in [*MANDATORY_CONTEXT_FILES, *[str(item) for item in requested]]:
        if raw not in ordered_files:
            ordered_files.append(raw)

    chunks = [
        "PRELOADED IMMUTABLE EVIDENCE PACKET",
        "This packet is deterministic harness evidence from the exact checkout. Use it before spending exploration calls.",
    ]
    for raw_path in ordered_files:
        chunks.append(_read_context_file(root, raw_path))

    if base_ref:
        names = subprocess.run(
            ["git", "-C", str(root), "diff", "--name-only", f"{base_ref}...HEAD", "--"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout
        diff = subprocess.run(
            ["git", "-C", str(root), "diff", "--no-ext-diff", f"{base_ref}...HEAD", "--"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout
        chunks.append(f"===== EXACT CHANGED FILES {base_ref}...HEAD =====\n{names or '[none]'}")
        chunks.append(f"===== EXACT TARGET DIFF {base_ref}...HEAD =====\n{_bounded(diff or '[no target diff]', 90000)}")

    packet = "\n\n".join(chunks)
    return _bounded(packet, MAX_EVIDENCE_PACKET)


@tool(is_enabled=_exploration_enabled)
def list_repo_files(ctx: RunContextWrapper[RepoContext], prefix: str = "") -> str:
    """List tracked repository files, optionally restricted to a path prefix. Exploration-budgeted."""
    _record_tool(ctx, "list_repo_files")
    root = ctx.context.root
    args = ["git", "-C", str(root), "ls-files"]
    if prefix:
        _safe_path(root, prefix)
        args.extend(["--", prefix])
    result = subprocess.run(args, check=True, capture_output=True, text=True)
    return _bounded(result.stdout)


@tool(is_enabled=_exploration_enabled)
def read_repo_file(
    ctx: RunContextWrapper[RepoContext],
    path: str,
    start_line: int = 1,
    max_lines: int = 300,
) -> str:
    """Read a bounded line range from a UTF-8 repository file. Exploration-budgeted."""
    _record_tool(ctx, "read_repo_file")
    if start_line < 1 or max_lines < 1 or max_lines > 500:
        raise ValueError("start_line must be >=1 and max_lines must be 1..500")
    file_path = _safe_path(ctx.context.root, path)
    text = file_path.read_text(encoding="utf-8")
    lines = text.splitlines()
    selected = lines[start_line - 1 : start_line - 1 + max_lines]
    numbered = "\n".join(f"{start_line + i}: {line}" for i, line in enumerate(selected))
    return _bounded(numbered)


@tool(is_enabled=_exploration_enabled)
def read_repo_files(
    ctx: RunContextWrapper[RepoContext],
    paths: list[str],
    max_lines_each: int = 300,
) -> str:
    """Batch-read up to 12 known UTF-8 repository files in one exploration call."""
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


@tool(is_enabled=_exploration_enabled)
def search_repo(ctx: RunContextWrapper[RepoContext], query: str, path: str = ".") -> str:
    """Search tracked repository text for a fixed literal string. Exploration-budgeted."""
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


@tool(is_enabled=_exploration_enabled)
def inspect_target_diff(ctx: RunContextWrapper[RepoContext]) -> str:
    """Read the immutable target diff against task.base_ref. Exploration-budgeted; normally preloaded already."""
    _record_tool(ctx, "inspect_target_diff")
    base_ref = ctx.context.base_ref
    if not base_ref:
        return "[base_ref not supplied by task packet]"
    result = subprocess.run(
        ["git", "-C", str(ctx.context.root), "diff", "--no-ext-diff", f"{base_ref}...HEAD", "--"],
        check=True,
        capture_output=True,
        text=True,
    )
    return _bounded(result.stdout or "[no target diff]")


@tool(is_enabled=_write_enabled)
def replace_repo_text(
    ctx: RunContextWrapper[RepoContext],
    path: str,
    old: str,
    new: str,
    expected_occurrences: int = 1,
) -> str:
    """Replace exact text in the ephemeral checkout. Write-budgeted; protected paths are blocked."""
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


@tool(is_enabled=_write_enabled)
def write_repo_file(ctx: RunContextWrapper[RepoContext], path: str, content: str) -> str:
    """Create or replace a UTF-8 file in the ephemeral checkout. Write-budgeted; protected paths are blocked."""
    _record_tool(ctx, "write_repo_file")
    file_path = _safe_path(ctx.context.root, path, write=True)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content, encoding="utf-8")
    return f"wrote {path} ({len(content)} characters)"


@tool(is_enabled=_verification_enabled)
def inspect_candidate_diff(ctx: RunContextWrapper[RepoContext]) -> str:
    """Return the current candidate git diff from the ephemeral checkout. Verification-budgeted."""
    _record_tool(ctx, "inspect_candidate_diff")
    result = subprocess.run(
        ["git", "-C", str(ctx.context.root), "diff", "--no-ext-diff", "--"],
        check=True,
        capture_output=True,
        text=True,
    )
    return _bounded(result.stdout or "[clean tree]")


@tool(is_enabled=_verification_enabled)
def run_safe_check(ctx: RunContextWrapper[RepoContext], check_name: str) -> str:
    """Run one deterministic, network-free check from the fixed allow-list. Verification-budgeted."""
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
    """Terminal action. Submit the completed concise report; this immediately ends the agent run."""
    _record_tool(ctx, "submit_result")
    cleaned = report.strip()
    if not cleaned:
        raise ValueError("report must not be empty")
    return _bounded(cleaned)


def _task_prompt(
    task: dict[str, Any],
    target_sha: str,
    effective_turns: int,
    context: RepoContext,
    evidence_packet: str,
) -> str:
    mode = str(task.get("mode", "analysis"))
    base_ref = task.get("base_ref") or "[none]"
    return f"""You are a bounded JarvisOS repository worker running on an ephemeral checkout.

Exact target SHA: {target_sha}
Exact base SHA for review diff: {base_ref}
Task id: {task['task_id']}
Mode: {mode}
Effective completion budget: up to {effective_turns} model turns.
Exploration tool-call budget: {context.exploration_limit} total calls.
Write tool-call budget: {context.write_limit} total calls.
Verification tool-call budget: {context.verification_limit} total calls.

Binding repository rules:
- Treat the PRELOADED IMMUTABLE EVIDENCE PACKET below as authoritative evidence from this exact checkout.
- Read its AGENTS.md and STATUS sections before substantive claims; do not reread them unless a precise missing line is necessary.
- Treat model output and edits as proposals only.
- Never modify protected authority/control paths; the harness blocks them.
- Prefer the smallest sufficient change.
- Do not invent repository state, tests, outputs, metrics, or validation evidence.
- Use only provided repository tools. You have no shell, network, GitHub credential, or secret access.
- Report unknowns instead of guessing.

Completion policy — binding:
- Optimize for a correct completed task, not minimum token spend.
- The initial packet already contains authority/context files requested by the task and, when base_ref exists, exact changed-file list plus exact base-to-target diff.
- Exploration tools are a scarce supplement, not the primary way to reconstruct the task. Use them only for specific unresolved questions.
- Exploration tools disappear automatically after {context.exploration_limit} total exploration calls. When they disappear, DO NOT try to recover exploration indirectly; finish from existing evidence.
- Write tools disappear after {context.write_limit} calls and verification tools after {context.verification_limit} calls.
- If editing, inspect the candidate diff and run required safe checks before completion while verification budget remains.
- As soon as the verdict/candidate is supportable, call submit_result exactly once. It is terminal and ends the run immediately.
- If a bounded unknown remains after exploration budget, record it in RISKS_OR_UNKNOWNS and still submit the best evidence-grounded verdict. Do not loop.

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

{evidence_packet}
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
        "request_timeout_seconds": args.request_timeout,
        "max_retries": args.max_retries,
        "requested_max_turns": requested_turns,
        "effective_max_turns": effective_turns,
        "hard_max_turns": HARD_MAX_TURNS,
        "exploration_limit": context.exploration_limit,
        "write_limit": context.write_limit,
        "verification_limit": context.verification_limit,
        "evidence_packet_chars": context.evidence_packet_chars,
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
    context = RepoContext(
        root=root,
        mode=mode,
        base_ref=base_ref,
        exploration_limit=_mode_limit(MODE_EXPLORATION_LIMIT, mode, 7),
        write_limit=_mode_limit(MODE_WRITE_LIMIT, mode, 0),
        verification_limit=_mode_limit(MODE_VERIFICATION_LIMIT, mode, 4),
    )
    evidence_packet = _build_evidence_packet(root, task, base_ref)
    context.evidence_packet_chars = len(evidence_packet)
    (output_dir / "evidence_packet.txt").write_text(evidence_packet, encoding="utf-8")

    set_tracing_disabled(True)
    client = AsyncOpenAI(
        api_key=api_key,
        base_url=args.base_url,
        timeout=float(args.request_timeout),
        max_retries=int(args.max_retries),
    )
    model = OpenAIChatCompletionsModel(model=args.model, openai_client=client)
    agent = Agent[RepoContext](
        name="JarvisOS GLM Worker",
        instructions=(
            "Use the preloaded exact evidence first. Spend bounded exploration only on unresolved questions. "
            "Finish the task rather than maximizing investigation. Submit the supported result via submit_result."
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
            _task_prompt(task, target_sha, effective_turns, context, evidence_packet),
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
                    "exploration_calls": context.exploration_calls,
                    "write_calls": context.write_calls,
                    "verification_calls": context.verification_calls,
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
        "exploration_calls": context.exploration_calls,
        "write_calls": context.write_calls,
        "verification_calls": context.verification_calls,
        "tool_counts": dict(sorted(context.tool_counts.items())),
        "finalized_via_submit_result": context.tool_counts.get("submit_result", 0) > 0,
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
    parser.add_argument("--request-timeout", type=float, default=120.0)
    parser.add_argument("--max-retries", type=int, default=2)
    return parser.parse_args()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run(parse_args())))
