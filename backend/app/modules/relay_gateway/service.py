"""Jarvis-owned gateway from Sidecar threads to sandboxed Agent Relay workers (spec 157).

Jarvis classifies and admits the task, prepares the thread's persistent workspace and
read-only context view, writes the sandbox manifest, and runs the installed ``relay``
CLI in the background. Relay stays unmodified; the sandbox shim in ``sandbox.py`` is
first on the ``PATH`` of the Relay processes started here.
"""

from __future__ import annotations

import glob
import hashlib
import json
import os
import shutil
import signal
import sqlite3
import subprocess
import tempfile
import threading
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field

from app.core.database import open_sqlite_connection
from app.core.paths import relay_root
from app.modules.ai import sensitivity
from app.modules.ai.egress_sanitizer import resolve_approved_prompt_derivative
from app.modules.ai.sensitivity import revalidate_sanitized_derivative
from app.modules.events.service import utc_now
from app.modules.relay_gateway import sandbox

REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_CONFIG_PATH = REPOSITORY_ROOT / "configs" / "relay_gateway.json"
LEVELS = ("S0", "S1", "S2", "S3", "S4")
CLOUD_READABLE_LEVELS = frozenset({"S0", "S1"})
MASKED_WORKSPACE_PATHS = (".agent-relay",)
# Command-line-scope git config for every host-side git run in an agent workspace (Relay's and
# Jarvis's): it outranks repository config, so a planted fsmonitor or hooks path never executes.
HOST_GIT_ENV = {
    "GIT_CONFIG_NOSYSTEM": "1",
    "GIT_CONFIG_COUNT": "2",
    "GIT_CONFIG_KEY_0": "core.fsmonitor",
    "GIT_CONFIG_VALUE_0": "false",
    "GIT_CONFIG_KEY_1": "core.hooksPath",
    "GIT_CONFIG_VALUE_1": "/dev/null",
}
AccessMode = Literal["repository", "derivative"]
RunState = Literal["queued", "running", "completed", "failed", "denied"]


class RelayGatewayError(ValueError):
    pass


class RelayRunRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=20000)
    agent: str = Field(pattern=r"^[a-z][a-z0-9_-]{0,31}$")
    cloud_safe_attested: bool = False


class RelayRunRead(BaseModel):
    id: str
    thread_id: str
    relay_workspace_id: str | None
    agent: str
    state: RunState
    reason_code: str | None
    relay_session_id: str | None
    continued_from_session_id: str | None
    turn_index: int
    repository_level: str
    access_mode: AccessMode
    released_derivative_ids: list[str]
    prompt_source: str | None
    stop_reason: str | None
    exit_code: int | None
    result_text: str | None
    workspace_path: str | None
    base_commit: str | None
    head_commit: str | None
    change_summary: str | None
    created_at: str
    started_at: str | None
    finished_at: str | None


class RelayStatusRead(BaseModel):
    enabled: bool
    repository_level: str
    access_mode: AccessMode
    agents: list[str]
    private_domain_data_enabled: bool
    blocked_reason: str | None


class ContextReleaseCreate(BaseModel):
    derivative_id: str = Field(min_length=1, max_length=128)
    scope: Literal["persistent", "thread"]
    thread_id: str | None = None
    purpose: str = Field(min_length=1, max_length=500)
    released_by: str = Field(min_length=1, max_length=128)
    expires_at: datetime | None = None


class ContextReleaseRead(BaseModel):
    id: str
    derivative_id: str
    derivative_digest: str
    scope: str
    thread_id: str | None
    purpose: str
    released_by: str
    state: str
    expires_at: str | None
    revocation_reason: str | None
    created_at: str
    updated_at: str


# ---- policy ---------------------------------------------------------------------------


def load_config(path: Path | None = None) -> dict[str, Any]:
    resolved = path or Path(os.getenv("JARVISOS_RELAY_GATEWAY_CONFIG", str(DEFAULT_CONFIG_PATH)))
    config = json.loads(resolved.read_text(encoding="utf-8"))
    level = config.get("repository", {}).get("level")
    if level not in LEVELS:
        raise RelayGatewayError("relay gateway repository level must be one of S0-S4")
    return config


def gateway_enabled(config: dict[str, Any]) -> bool:
    return bool(config.get("enabled")) or os.getenv("JARVISOS_RELAY_GATEWAY_ENABLED") == "1"


def private_data_gate(config: dict[str, Any]) -> str | None:
    """Pre-IP gate: once private domain data is enabled, runs need an accepted hardened sandbox.

    While ``private_domain_data.enabled`` is false Jarvis holds no strategic/domain IP, so the
    sandbox is used but its hardening is not a release blocker. Enabling private data without
    ``sandbox_isolation_accepted`` refuses every run instead of silently relying on it.
    """
    gate = config.get("private_domain_data", {})
    if gate.get("enabled") is True and gate.get("sandbox_isolation_accepted") is not True:
        return "private_domain_data_sandbox_not_accepted"
    return None


def access_mode_for(level: str) -> AccessMode:
    """S0/S1 source is cloud-readable; anything stricter never mounts the real repository."""
    return "repository" if level in CLOUD_READABLE_LEVELS else "derivative"


def relay_status(config: dict[str, Any] | None = None) -> RelayStatusRead:
    config = config or load_config()
    level = config["repository"]["level"]
    return RelayStatusRead(
        enabled=gateway_enabled(config),
        repository_level=level,
        access_mode=access_mode_for(level),
        agents=sorted(config.get("agents", {})),
        private_domain_data_enabled=config.get("private_domain_data", {}).get("enabled") is True,
        blocked_reason=private_data_gate(config),
    )


@dataclass(frozen=True)
class Admission:
    allowed: bool
    reason_code: str | None
    prompt_source: str | None = None
    effective_prompt: str | None = None
    prompt_derivative_id: str | None = None


def admit_prompt(prompt: str, *, attested: bool, workspace_id: str) -> Admission:
    """Deterministic admission; the local classifier is not consulted."""
    floor = sensitivity.deterministic_floor(prompt)
    if floor == "S4":
        return Admission(False, "prompt_secret_detected")
    if floor in {"S2", "S3"}:
        derivative = resolve_approved_prompt_derivative(raw_prompt=prompt, workspace_id=workspace_id)
        if derivative is None or derivative.final_level not in CLOUD_READABLE_LEVELS:
            return Admission(False, "prompt_sanitization_required")
        return Admission(True, None, "approved_derivative", derivative.derivative_content, derivative.id)
    if not attested:
        return Admission(False, "prompt_classification_required")
    return Admission(True, None, "operator_attested", prompt)


# ---- context releases -----------------------------------------------------------------


def create_context_release(workspace_id: str, payload: ContextReleaseCreate) -> ContextReleaseRead:
    if (payload.scope == "thread") != (payload.thread_id is not None):
        raise RelayGatewayError("thread scope requires thread_id and persistent scope forbids it")
    derivative = revalidate_sanitized_derivative(workspace_id, payload.derivative_id)
    if derivative.status != "approved" or derivative.effective_level not in CLOUD_READABLE_LEVELS:
        raise RelayGatewayError("only approved S0/S1 derivatives can be released to Relay context")
    now = utc_now()
    release_id = str(uuid4())
    expires_at = payload.expires_at.astimezone(UTC).isoformat() if payload.expires_at else None
    with open_sqlite_connection() as connection:
        if payload.thread_id is not None:
            _require_thread(connection, workspace_id, payload.thread_id)
        connection.execute(
            """
            INSERT INTO relay_context_releases (
                id, workspace_id, derivative_id, derivative_digest, scope, thread_id, purpose,
                released_by, state, expires_at, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?, ?)
            """,
            (release_id, workspace_id, derivative.id, derivative.content_digest, payload.scope,
             payload.thread_id, payload.purpose, payload.released_by, expires_at, now, now),
        )
        connection.commit()
        row = connection.execute("SELECT * FROM relay_context_releases WHERE id = ?", (release_id,)).fetchone()
    return _release_read(row)


def revoke_context_release(workspace_id: str, release_id: str, reason: str) -> ContextReleaseRead:
    with open_sqlite_connection() as connection:
        updated = connection.execute(
            """
            UPDATE relay_context_releases SET state = 'revoked', revocation_reason = ?, updated_at = ?
            WHERE id = ? AND workspace_id = ?
            """,
            (reason, utc_now(), release_id, workspace_id),
        ).rowcount
        connection.commit()
        row = connection.execute("SELECT * FROM relay_context_releases WHERE id = ?", (release_id,)).fetchone()
    if not updated or row is None:
        raise LookupError("relay context release not found")
    return _release_read(row)


def list_context_releases(workspace_id: str) -> list[ContextReleaseRead]:
    with open_sqlite_connection() as connection:
        rows = connection.execute(
            "SELECT * FROM relay_context_releases WHERE workspace_id = ? ORDER BY created_at, id",
            (workspace_id,),
        ).fetchall()
    return [_release_read(row) for row in rows]


def effective_releases(workspace_id: str, thread_id: str) -> list[tuple[ContextReleaseRead, Any]]:
    """Active, unexpired releases whose derivative is still approved, cloud-readable and unchanged."""
    now = datetime.now(UTC)
    with open_sqlite_connection() as connection:
        rows = connection.execute(
            """
            SELECT * FROM relay_context_releases
            WHERE workspace_id = ? AND state = 'active'
              AND (scope = 'persistent' OR thread_id = ?)
            ORDER BY created_at, id
            """,
            (workspace_id, thread_id),
        ).fetchall()
    effective = []
    for row in rows:
        release = _release_read(row)
        if release.expires_at and datetime.fromisoformat(release.expires_at) <= now:
            continue
        derivative = revalidate_sanitized_derivative(workspace_id, release.derivative_id)
        if (
            derivative.status != "approved"
            or derivative.effective_level not in CLOUD_READABLE_LEVELS
            or derivative.content_digest != release.derivative_digest
        ):
            continue
        effective.append((release, derivative))
    return effective


# ---- runtime --------------------------------------------------------------------------


@dataclass
class RelayRuntime:
    """Host facts and process launch, injectable so tests never start Relay or agents."""

    root: Path
    source_repo: Path
    relay_binary: str
    resolve_agent: Callable[[str], str | None]
    launch: Callable[[list[str], Path, dict[str, str], Path], subprocess.Popen[bytes]]


def _launch(argv: list[str], cwd: Path, env: dict[str, str], log_path: Path) -> subprocess.Popen[bytes]:
    with open(log_path, "wb") as log:
        return subprocess.Popen(argv, cwd=cwd, env=env, stdout=log, stderr=subprocess.STDOUT,
                                stdin=subprocess.DEVNULL, start_new_session=True)


def _host_which(command: str) -> str | None:
    """Resolve a host CLI; services started by the launcher do not inherit a login PATH."""
    entries = [str(Path.home() / ".local" / "bin")]
    entries += sorted(glob.glob(str(Path.home() / ".nvm" / "versions" / "node" / "*" / "bin")), reverse=True)
    entries.append(os.getenv("PATH", "/usr/bin:/bin"))
    found = shutil.which(command, path=os.pathsep.join(entries))
    return os.path.realpath(found) if found else None


def default_runtime() -> RelayRuntime:
    source = Path(os.getenv("JARVISOS_RELAY_SOURCE_REPO", str(REPOSITORY_ROOT)))
    relay_binary = _host_which("relay") or str(Path.home() / ".local" / "bin" / "relay")
    return RelayRuntime(relay_root(), source, relay_binary, _host_which, _launch)


_runtime_override: RelayRuntime | None = None
_active_waiters: set[str] = set()
_waiters_lock = threading.Lock()


def set_runtime(runtime: RelayRuntime | None) -> None:
    global _runtime_override
    _runtime_override = runtime


def _runtime() -> RelayRuntime:
    return _runtime_override or default_runtime()


# ---- runs -----------------------------------------------------------------------------


def submit_relay_run(workspace_id: str, thread_id: str, payload: RelayRunRequest) -> RelayRunRead:
    config = load_config()
    if not gateway_enabled(config):
        raise RelayGatewayError("relay_gateway_disabled")
    if (blocked := private_data_gate(config)) is not None:
        raise RelayGatewayError(blocked)
    if payload.agent not in config.get("agents", {}):
        raise RelayGatewayError("relay_agent_not_allowed")
    level = config["repository"]["level"]
    mode = access_mode_for(level)
    with open_sqlite_connection() as connection:
        _require_thread(connection, workspace_id, thread_id)
    admission = admit_prompt(payload.prompt, attested=payload.cloud_safe_attested, workspace_id=workspace_id)
    run_id = str(uuid4())
    now = utc_now()
    state = "queued" if admission.allowed else "denied"
    with open_sqlite_connection() as connection:
        try:
            connection.execute(
                """
                INSERT INTO relay_runs (
                    id, workspace_id, thread_id, agent, state, reason_code, prompt_digest, prompt_source,
                    prompt_derivative_id, repository_level, access_mode, created_at, finished_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (run_id, workspace_id, thread_id, payload.agent, state, admission.reason_code,
                 hashlib.sha256(payload.prompt.encode("utf-8")).hexdigest(), admission.prompt_source,
                 admission.prompt_derivative_id, level, mode, now, None if admission.allowed else now),
            )
        except sqlite3.IntegrityError as exc:
            raise RelayGatewayError("relay_run_in_progress") from exc
        connection.commit()
    if admission.allowed:
        assert admission.effective_prompt is not None
        try:
            _start_run(config, workspace_id, thread_id, run_id, payload.agent, mode, level,
                       admission.effective_prompt)
        except (OSError, subprocess.SubprocessError, RelayGatewayError) as exc:
            _finish(run_id, "failed", reason_code="relay_run_launch_failed", result_text=str(exc)[:500])
    return get_relay_run(workspace_id, thread_id, run_id)


def list_relay_runs(workspace_id: str, thread_id: str) -> list[RelayRunRead]:
    with open_sqlite_connection() as connection:
        rows = connection.execute(
            "SELECT id FROM relay_runs WHERE workspace_id = ? AND thread_id = ? ORDER BY created_at, id",
            (workspace_id, thread_id),
        ).fetchall()
    return [get_relay_run(workspace_id, thread_id, row["id"]) for row in rows]


def get_relay_run(workspace_id: str, thread_id: str, run_id: str) -> RelayRunRead:
    with open_sqlite_connection() as connection:
        row = _run_row(connection, workspace_id, thread_id, run_id)
    if row["state"] in {"queued", "running"} and not _still_owned(row):
        _finish(run_id, "failed", reason_code="relay_run_interrupted")
        with open_sqlite_connection() as connection:
            row = _run_row(connection, workspace_id, thread_id, run_id)
    return _run_read(row)


def _still_owned(row: sqlite3.Row) -> bool:
    with _waiters_lock:
        if row["id"] in _active_waiters:
            return True
    return row["state"] == "queued" and row["pid"] is None and _recent(row["created_at"])


def _recent(timestamp: str) -> bool:
    return (datetime.now(UTC) - datetime.fromisoformat(timestamp)).total_seconds() < 60


def _start_run(config: dict[str, Any], workspace_id: str, thread_id: str, run_id: str, agent: str,
               mode: AccessMode, level: str, prompt: str) -> None:
    runtime = _runtime()
    relay_workspace = _ensure_relay_workspace(runtime, config, workspace_id, thread_id, agent, mode)
    releases = effective_releases(workspace_id, thread_id)
    context_dir = _materialize_context(runtime, config, relay_workspace["id"], level, mode, releases)
    home = runtime.root / "homes" / relay_workspace["id"]
    _write_manifest(runtime, config, agent, Path(relay_workspace["path"]), context_dir, home, mode)
    _write_shims(runtime, config)
    run_dir = runtime.root / "runs" / run_id
    run_dir.mkdir(parents=True, mode=0o700)
    # Relay may link each --continue to a new session id; always continue from the newest one.
    continued_from = relay_workspace["relay_session_id"]
    argv = [runtime.relay_binary, "--json", "run", agent, "--yes", "--repo", relay_workspace["path"],
            "--max-turns", str(int(config.get("max_turns", 10)))]
    if continued_from:
        argv += ["--continue", continued_from]
    if config["agents"][agent].get("model"):
        argv += ["--model", config["agents"][agent]["model"]]
    argv += ["--task", _framed_prompt(prompt, relay_workspace["path"], mode)]
    env = {
        "PATH": f"{runtime.root / 'bin'}:/usr/local/bin:/usr/bin:/bin",
        "HOME": str(Path.home()),
        "USER": os.getenv("USER", ""),
        "LOGNAME": os.getenv("LOGNAME", ""),
        "LANG": "C.UTF-8",
        "TERM": "dumb",
        "GIT_CEILING_DIRECTORIES": str(runtime.root / "workspaces"),
        **HOST_GIT_ENV,
    }
    turn_index = _turn_index(relay_workspace["id"])
    start_commit = _head_commit(Path(relay_workspace["path"]))
    with _waiters_lock:
        _active_waiters.add(run_id)
    try:
        process = runtime.launch(argv, Path(relay_workspace["path"]), env, run_dir / "relay.json")
    except BaseException:
        with _waiters_lock:
            _active_waiters.discard(run_id)
        raise
    with open_sqlite_connection() as connection:
        connection.execute(
            """
            UPDATE relay_runs SET state = 'running', relay_workspace_id = ?, pid = ?, started_at = ?,
                turn_index = ?, released_derivatives_json = ?, continued_from_session_id = ?
            WHERE id = ?
            """,
            (relay_workspace["id"], process.pid, utc_now(), turn_index,
             json.dumps([derivative.id for _, derivative in releases]), continued_from, run_id),
        )
        connection.commit()
    threading.Thread(target=_wait_for_run, args=(config, run_id, relay_workspace["id"], process,
                                                 run_dir / "relay.json", start_commit), daemon=True).start()


def _framed_prompt(prompt: str, workspace: str, mode: AccessMode) -> str:
    access = ("the real JarvisOS repository (cloud-safe)" if mode == "repository"
              else "a derivative workspace without source code")
    return (
        f"[Jarvis Relay gateway] Your workspace is {workspace}: {access}. Approved read-only context is in "
        f"{sandbox.SANDBOX_CONTEXT} (see MANIFEST.json there). Nothing else from Jarvis is reachable. "
        "Commit finished work locally on the current branch; publishing is done by Jarvis.\n\nTask:\n"
        f"{prompt}"
    )


def _wait_for_run(config: dict[str, Any], run_id: str, relay_workspace_id: str,
                  process: subprocess.Popen[bytes], output_path: Path, start_commit: str | None) -> None:
    try:
        try:
            process.wait(timeout=int(config.get("run_timeout_seconds", 3600)))
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGTERM)
            process.wait(timeout=30)
            _finish(run_id, "failed", reason_code="relay_run_timeout")
            return
        _record_result(config, run_id, relay_workspace_id, process.returncode, output_path, start_commit)
    except Exception as exc:  # noqa: BLE001 - a waiter must always terminalize its run
        _finish(run_id, "failed", reason_code="relay_run_result_unreadable", result_text=str(exc)[:500])
    finally:
        with _waiters_lock:
            _active_waiters.discard(run_id)


def _record_result(config: dict[str, Any], run_id: str, relay_workspace_id: str, returncode: int,
                   output_path: Path, start_commit: str | None = None) -> None:
    _record_changes(run_id, relay_workspace_id, start_commit)
    raw = output_path.read_text(encoding="utf-8", errors="replace")
    try:
        result = json.loads(raw[raw.index("{"):])
    except ValueError:
        _finish(run_id, "failed", reason_code="relay_output_unparseable", exit_code=returncode,
                result_text=raw[-2000:])
        return
    session_id = result.get("session_id")
    turns = result.get("turns") or []
    last = turns[-1] if turns else {}
    exit_code = last.get("exit_code", returncode)
    text = str(last.get("text") or last.get("summary") or "")[: int(config.get("result_max_chars", 20000))]
    if session_id:
        with open_sqlite_connection() as connection:
            connection.execute(
                "UPDATE relay_workspaces SET relay_session_id = ?, updated_at = ? WHERE id = ?",
                (session_id, utc_now(), relay_workspace_id),
            )
            connection.commit()
    succeeded = returncode == 0 and exit_code == 0
    _finish(run_id, "completed" if succeeded else "failed",
            reason_code=None if succeeded else "relay_agent_error", exit_code=exit_code,
            stop_reason=result.get("stop_reason"), result_text=text, session_id=session_id)


def _finish(run_id: str, state: str, *, reason_code: str | None = None, exit_code: int | None = None,
            stop_reason: str | None = None, result_text: str | None = None, session_id: str | None = None) -> None:
    with open_sqlite_connection() as connection:
        connection.execute(
            """
            UPDATE relay_runs SET state = ?, reason_code = ?, exit_code = ?, stop_reason = ?,
                result_text = ?, relay_session_id = COALESCE(?, relay_session_id), finished_at = ?
            WHERE id = ? AND state IN ('queued', 'running')
            """,
            (state, reason_code, exit_code, stop_reason, result_text, session_id, utc_now(), run_id),
        )
        connection.commit()


def _head_commit(workspace: Path) -> str | None:
    try:
        return _git("rev-parse", "--verify", "HEAD", cwd=workspace)
    except (subprocess.CalledProcessError, OSError):
        return None


def _record_changes(run_id: str, relay_workspace_id: str, start_commit: str | None) -> None:
    """Record what the run left in the workspace: new commits, their diffstat and uncommitted files."""
    with open_sqlite_connection() as connection:
        row = connection.execute("SELECT path FROM relay_workspaces WHERE id = ?", (relay_workspace_id,)).fetchone()
    workspace = Path(row["path"])
    # The shim already restored git metadata when the sandbox exited; repeat it before host git runs.
    sandbox.restore_workspace_git(str(workspace), str(trusted_git_config(_runtime(), workspace)))
    head = _head_commit(workspace)
    sections = []
    try:
        if start_commit and head and head != start_commit:
            sections.append("Commits:\n" + _git("log", "--oneline", f"{start_commit}..{head}", cwd=workspace))
            sections.append("Diffstat:\n" + _git("diff", "--stat", "--no-ext-diff", "--no-textconv",
                                                  start_commit, head, cwd=workspace))
        status = _git("status", "--short", "--ignore-submodules=all", cwd=workspace)
        if status:
            sections.append("Uncommitted:\n" + status)
    except (subprocess.CalledProcessError, OSError) as exc:
        sections.append(f"Change evidence unavailable: {exc}")
    summary = "\n\n".join(sections) or "No changes."
    with open_sqlite_connection() as connection:
        connection.execute("UPDATE relay_runs SET head_commit = ?, change_summary = ? WHERE id = ?",
                           (head, summary[:8000], run_id))
        connection.commit()


def _turn_index(relay_workspace_id: str) -> int:
    with open_sqlite_connection() as connection:
        row = connection.execute(
            "SELECT COUNT(*) AS n FROM relay_runs WHERE relay_workspace_id = ? AND state IN ('completed', 'failed')",
            (relay_workspace_id,),
        ).fetchone()
    return int(row["n"])


# ---- workspace, context, manifest -----------------------------------------------------


def _ensure_relay_workspace(runtime: RelayRuntime, config: dict[str, Any], workspace_id: str, thread_id: str,
                            agent: str, mode: AccessMode) -> sqlite3.Row:
    with open_sqlite_connection() as connection:
        row = connection.execute(
            "SELECT * FROM relay_workspaces WHERE thread_id = ? AND access_mode = ? AND agent = ?",
            (thread_id, mode, agent),
        ).fetchone()
        if row is None:
            relay_workspace_id = str(uuid4())
            path = runtime.root / "workspaces" / relay_workspace_id
            now = utc_now()
            connection.execute(
                """
                INSERT INTO relay_workspaces (id, workspace_id, thread_id, access_mode, agent, path, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (relay_workspace_id, workspace_id, thread_id, mode, agent, str(path), now, now),
            )
            connection.commit()
            row = connection.execute("SELECT * FROM relay_workspaces WHERE id = ?", (relay_workspace_id,)).fetchone()
    path = Path(row["path"])
    if not (path / ".git").exists():
        base = _create_workspace(runtime, config, path, mode, row["id"])
        with open_sqlite_connection() as connection:
            connection.execute("UPDATE relay_workspaces SET base_commit = ?, updated_at = ? WHERE id = ?",
                               (base, utc_now(), row["id"]))
            connection.commit()
            row = connection.execute("SELECT * FROM relay_workspaces WHERE id = ?", (row["id"],)).fetchone()
    return row


def _git(*args: str, cwd: Path | None = None) -> str:
    env = {**os.environ, **HOST_GIT_ENV}
    if cwd is not None:
        env["GIT_CEILING_DIRECTORIES"] = str(Path(cwd).parent)
    return subprocess.run(["git", *args], cwd=cwd, env=env, check=True, capture_output=True, text=True,
                          timeout=600).stdout.rstrip()


def trusted_git_config(runtime: RelayRuntime, workspace: Path) -> Path:
    """Jarvis-owned copy of a workspace's git config, outside anything the agent can write."""
    return runtime.root / "git-config" / sandbox.manifest_name(str(workspace))


def _save_trusted_git_config(runtime: RelayRuntime, workspace: Path) -> None:
    target = trusted_git_config(runtime, workspace)
    target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    shutil.copyfile(workspace / ".git" / "config", target)
    target.chmod(0o600)


def _create_workspace(runtime: RelayRuntime, config: dict[str, Any], path: Path, mode: AccessMode,
                      relay_workspace_id: str) -> str | None:
    """Create the thread's workspace and return its base commit (None for a derivative workspace)."""
    base: str | None
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    if path.exists():
        shutil.rmtree(path)
    if mode == "repository":
        source = runtime.source_repo
        try:
            base = _git("rev-parse", "--verify", "origin/master", cwd=source)
        except subprocess.CalledProcessError:
            base = _git("rev-parse", "HEAD", cwd=source)
        # --no-hardlinks: the agent may rewrite files in its clone; never share inodes with the source.
        _git("clone", "--quiet", "--no-hardlinks", "--no-checkout", str(source), str(path))
        _git("checkout", "--quiet", "-b", f"relay/{relay_workspace_id[:8]}", base, cwd=path)
        try:
            _git("remote", "set-url", "origin", _git("remote", "get-url", "origin", cwd=source), cwd=path)
        except subprocess.CalledProcessError:
            _git("remote", "remove", "origin", cwd=path)
    else:
        path.mkdir(mode=0o700)
        _git("init", "--quiet", "-b", "main", cwd=path)
        (path / "README.md").write_text(
            "# Derivative workspace\n\nThe repository is classified above cloud-safe, so its source is not "
            "available here. Work only from the approved context in /workspace/context.\n",
            encoding="utf-8",
        )
        base = None
    exclude = path / ".git" / "info" / "exclude"
    exclude.parent.mkdir(parents=True, exist_ok=True)
    with open(exclude, "a", encoding="utf-8") as handle:
        handle.write("\n.agent-relay/\n")
    _save_trusted_git_config(runtime, path)
    return base


def _materialize_context(runtime: RelayRuntime, config: dict[str, Any], relay_workspace_id: str, level: str,
                         mode: AccessMode, releases: list[tuple[ContextReleaseRead, Any]]) -> Path:
    """Rebuild the read-only view from current authority; nothing stale survives a run boundary."""
    target = runtime.root / "context" / relay_workspace_id
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True, mode=0o700)
    stable = runtime.source_repo / config.get("stable_context_dir", "docs/relay-context")
    if stable.is_dir():
        shutil.copytree(stable, target / "stable", symlinks=False,
                        ignore=lambda _dir, names: [name for name in names if name.startswith(".")])
    derivatives_dir = target / "derivatives"
    derivatives_dir.mkdir()
    entries = []
    for release, derivative in releases:
        (derivatives_dir / f"{derivative.id}.md").write_text(derivative.content, encoding="utf-8")
        entries.append({
            "release_id": release.id,
            "derivative_id": derivative.id,
            "digest": derivative.content_digest,
            "level": derivative.effective_level,
            "scope": release.scope,
            "purpose": release.purpose,
            "expires_at": release.expires_at,
        })
    manifest = {"repository_level": level, "access_mode": mode, "generated_at": utc_now(), "derivatives": entries}
    (target / "MANIFEST.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return target


def _agent_spec(runtime: RelayRuntime, config: dict[str, Any], agent: str, home: Path) -> dict[str, Any]:
    spec = config["agents"][agent]
    binary = runtime.resolve_agent(spec["command"])
    if binary is None:
        raise RelayGatewayError(f"relay_agent_binary_missing:{agent}")
    binary_path = Path(binary)
    credentials = []
    for relative in spec.get("credentials", []):
        source = Path.home() / relative
        if not source.is_file() or source.is_symlink():
            raise RelayGatewayError(f"relay_agent_login_missing:{agent}")
        (home / relative).parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        (home / relative).touch(mode=0o600, exist_ok=True)
        credentials.append({"source": str(source), "target": relative})
    return {
        "binary": str(binary_path),
        "tool_roots": [str(binary_path.parents[1])],
        "path_prefix": [str(binary_path.parent)],
        "credentials": credentials,
        "environment": dict(spec.get("environment", {})),
        "sandbox_args": [str(argument) for argument in spec.get("sandbox_args", [])],
    }


def build_manifest(runtime: RelayRuntime, config: dict[str, Any], agent: str, workspace: Path, context_dir: Path,
                   home: Path, mode: AccessMode) -> dict[str, Any]:
    home.mkdir(parents=True, exist_ok=True, mode=0o700)
    dependency_mounts = []
    if mode == "repository":
        for mount in config.get("dependency_mounts", []):
            source = runtime.source_repo / mount["source"]
            if source.is_dir():
                dependency_mounts.append({"source": str(source), "target": mount["target"]})
    allow = sorted({*config.get("common_egress", []), *config["agents"][agent].get("egress", [])})
    git_config = trusted_git_config(runtime, workspace)
    if not git_config.is_file():
        # Only workspaces Jarvis created (and recorded a trusted config for) may be handed to agents.
        raise RelayGatewayError("relay_workspace_git_config_untrusted")
    return {
        "version": sandbox.MANIFEST_VERSION,
        "workspace": os.path.realpath(workspace),
        "context_dir": str(context_dir),
        "home": str(home),
        "runtime_root": str(runtime.root / "sandbox-runs"),
        "agents": {agent: _agent_spec(runtime, config, agent, home)},
        "masked": list(MASKED_WORKSPACE_PATHS),
        "dependency_mounts": dependency_mounts,
        "egress_allow": allow,
        "git_config": str(git_config),
    }


def _write_manifest(runtime: RelayRuntime, config: dict[str, Any], agent: str, workspace: Path, context_dir: Path,
                    home: Path, mode: AccessMode) -> dict[str, Any]:
    manifest = build_manifest(runtime, config, agent, workspace, context_dir, home, mode)
    directory = runtime.root / "manifests"
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    descriptor, temporary = tempfile.mkstemp(dir=directory, prefix=".manifest-")
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2)
    os.chmod(temporary, 0o600)
    os.replace(temporary, directory / sandbox.manifest_name(str(workspace)))
    return manifest


def _write_shims(runtime: RelayRuntime, config: dict[str, Any]) -> None:
    directory = runtime.root / "bin"
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    script = os.path.abspath(sandbox.__file__)
    manifests = runtime.root / "manifests"
    for agent in config["agents"]:
        shim = directory / agent
        shim.write_text(
            f"#!/bin/sh\nexec /usr/bin/python3 '{script}' shim '{agent}' '{manifests}' -- \"$@\"\n",
            encoding="utf-8",
        )
        shim.chmod(0o700)


# ---- rows -----------------------------------------------------------------------------


def _require_thread(connection: sqlite3.Connection, workspace_id: str, thread_id: str) -> None:
    row = connection.execute(
        "SELECT 1 FROM ai_threads WHERE id = ? AND workspace_id = ?", (thread_id, workspace_id)
    ).fetchone()
    if row is None:
        raise LookupError("thread not found in workspace")


def _run_row(connection: sqlite3.Connection, workspace_id: str, thread_id: str, run_id: str) -> sqlite3.Row:
    row = connection.execute(
        """
        SELECT r.*, w.path AS workspace_path, w.base_commit AS base_commit FROM relay_runs r
        LEFT JOIN relay_workspaces w ON w.id = r.relay_workspace_id
        WHERE r.id = ? AND r.workspace_id = ? AND r.thread_id = ?
        """,
        (run_id, workspace_id, thread_id),
    ).fetchone()
    if row is None:
        raise LookupError("relay run not found")
    return row


def _run_read(row: sqlite3.Row) -> RelayRunRead:
    return RelayRunRead(
        id=row["id"],
        thread_id=row["thread_id"],
        relay_workspace_id=row["relay_workspace_id"],
        agent=row["agent"],
        state=row["state"],
        reason_code=row["reason_code"],
        relay_session_id=row["relay_session_id"],
        continued_from_session_id=row["continued_from_session_id"],
        turn_index=row["turn_index"],
        repository_level=row["repository_level"],
        access_mode=row["access_mode"],
        released_derivative_ids=json.loads(row["released_derivatives_json"]),
        prompt_source=row["prompt_source"],
        stop_reason=row["stop_reason"],
        exit_code=row["exit_code"],
        result_text=row["result_text"],
        workspace_path=row["workspace_path"],
        base_commit=row["base_commit"],
        head_commit=row["head_commit"],
        change_summary=row["change_summary"],
        created_at=row["created_at"],
        started_at=row["started_at"],
        finished_at=row["finished_at"],
    )


def _release_read(row: sqlite3.Row) -> ContextReleaseRead:
    return ContextReleaseRead(**{key: row[key] for key in ContextReleaseRead.model_fields})
