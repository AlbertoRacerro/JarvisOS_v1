from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

OWNER_LOCK_NAME = ".jarvis-runner-owner.lock"


@dataclass(frozen=True)
class LocalPythonResult:
    return_code: int | None
    timed_out: bool
    stdout: str
    stderr: str
    stdout_truncated: bool
    stderr_truncated: bool
    command_metadata: dict[str, object]
    environment_metadata: dict[str, object]


class ExecutionOwnerBusy(RuntimeError):
    pass


class _ExecutionOwnerSession:
    def __init__(self, working_dir: Path) -> None:
        self.working_dir = working_dir.resolve()
        self.lock_path = ownership_lock_path(self.working_dir)
        self.process: subprocess.Popen[str] | None = None
        self.executed = False

    def start(self) -> None:
        owner_dir = self.working_dir.parent
        owner_dir.mkdir(parents=True, exist_ok=True)
        owner_script = Path(__file__).with_name("_execution_owner.py")
        owner_env = {"PYTHONHASHSEED": "0", "PYTHONIOENCODING": "utf-8"}
        process = subprocess.Popen(
            [sys.executable, str(owner_script), str(self.lock_path)],
            cwd=str(owner_dir),
            env=owner_env,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        self.process = process
        assert process.stdout is not None
        line = process.stdout.readline()
        if not line:
            stderr = process.stderr.read() if process.stderr is not None else ""
            process.wait(timeout=5)
            raise RuntimeError(f"Runner execution owner failed to start: {stderr.strip()}")
        payload = json.loads(line)
        if payload.get("state") == "busy":
            process.wait(timeout=5)
            raise ExecutionOwnerBusy("Runner execution ownership is already held.")
        if payload.get("state") != "ready":
            process.terminate()
            process.wait(timeout=5)
            raise RuntimeError("Runner execution owner returned an invalid readiness state.")

    def execute(
        self,
        *,
        script_path: Path,
        input_file: Path,
        output_dir: Path,
        timeout_seconds: int,
        max_stdout_bytes: int,
        max_stderr_bytes: int,
    ) -> LocalPythonResult:
        if self.process is None or self.process.stdin is None or self.process.stdout is None:
            raise RuntimeError("Runner execution owner is not started.")
        if self.executed:
            raise RuntimeError("Runner execution owner can execute only once.")
        self.executed = True

        command = [sys.executable, str(script_path), str(input_file), str(output_dir)]
        env = {"PYTHONHASHSEED": "0", "PYTHONIOENCODING": "utf-8"}
        if (script_path.parent / "process_kernel").is_dir():
            env["PYTHONDONTWRITEBYTECODE"] = "1"
        request = {
            "action": "run",
            "command": command,
            "env": env,
            "cwd": str(self.working_dir),
            "timeout_seconds": timeout_seconds,
            "max_stdout_bytes": max_stdout_bytes,
            "max_stderr_bytes": max_stderr_bytes,
        }
        self.process.stdin.write(json.dumps(request, sort_keys=True, separators=(",", ":")) + "\n")
        self.process.stdin.flush()
        line = self.process.stdout.readline()
        if not line:
            stderr = self.process.stderr.read() if self.process.stderr is not None else ""
            raise RuntimeError(f"Runner execution owner exited before returning a result: {stderr.strip()}")
        payload = json.loads(line)
        if payload.get("state") != "completed":
            raise RuntimeError("Runner execution owner returned an invalid completion state.")

        command_metadata = {
            "executable": Path(sys.executable).name,
            "argv": [Path(command[0]).name, str(script_path), str(input_file), str(output_dir)],
            "shell": False,
        }
        environment_metadata = {
            "inherited_environment": False,
            "allowlisted_keys": sorted(env.keys()),
        }
        return LocalPythonResult(
            return_code=payload.get("return_code"),
            timed_out=bool(payload["timed_out"]),
            stdout=str(payload["stdout"]),
            stderr=str(payload["stderr"]),
            stdout_truncated=bool(payload["stdout_truncated"]),
            stderr_truncated=bool(payload["stderr_truncated"]),
            command_metadata=command_metadata,
            environment_metadata=environment_metadata,
        )

    def release(self) -> None:
        process = self.process
        if process is None:
            return
        try:
            if process.poll() is None and process.stdin is not None:
                try:
                    process.stdin.write("release\n")
                    process.stdin.flush()
                    process.stdin.close()
                except (BrokenPipeError, OSError):
                    pass
            if process.poll() is None:
                process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
        finally:
            self.process = None


_sessions: dict[Path, _ExecutionOwnerSession] = {}
_sessions_lock = threading.Lock()


def ownership_lock_path(working_dir: Path) -> Path:
    resolved = working_dir.resolve()
    return resolved.parent / f".{resolved.name}{OWNER_LOCK_NAME}"


def child_ownership_lock_path(working_dir: Path) -> Path:
    owner_lock_path = ownership_lock_path(working_dir)
    return owner_lock_path.with_name(f"{owner_lock_path.name}.child")


@contextmanager
def prepare_execution_owner(working_dir: Path) -> Iterator[None]:
    key = working_dir.resolve()
    session = _ExecutionOwnerSession(key)
    with _sessions_lock:
        if key in _sessions:
            raise ExecutionOwnerBusy("Runner execution ownership is already held in this process.")
        _sessions[key] = session
    try:
        session.start()
        yield
    finally:
        with _sessions_lock:
            if _sessions.get(key) is session:
                _sessions.pop(key, None)
        session.release()


def _lock_state(lock_path: Path) -> str:
    if not lock_path.exists():
        return "unknown"
    handle = lock_path.open("r+b")
    try:
        handle.seek(0)
        if os.name == "nt":
            import msvcrt

            locking = msvcrt.locking  # type: ignore[attr-defined]
            lk_nblck = msvcrt.LK_NBLCK  # type: ignore[attr-defined]
            lk_unlck = msvcrt.LK_UNLCK  # type: ignore[attr-defined]
            try:
                locking(handle.fileno(), lk_nblck, 1)
            except OSError:
                return "live"
            locking(handle.fileno(), lk_unlck, 1)
            return "gone"
        import fcntl

        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return "live"
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        return "gone"
    finally:
        handle.close()


def execution_ownership_state(working_dir: Path) -> str:
    """Return live, gone, or unknown from runner-specific OS lock evidence."""

    owner_state = _lock_state(ownership_lock_path(working_dir))
    if owner_state == "live":
        return "live"

    child_state = _lock_state(child_ownership_lock_path(working_dir))
    if child_state == "live":
        return "live"
    if owner_state == "gone" or child_state == "gone":
        return "gone"
    return "unknown"


def execute_python_script(
    *,
    script_path: Path,
    input_file: Path,
    output_dir: Path,
    working_dir: Path,
    timeout_seconds: int,
    max_stdout_bytes: int,
    max_stderr_bytes: int,
) -> LocalPythonResult:
    key = working_dir.resolve()
    with _sessions_lock:
        session = _sessions.get(key)
    if session is not None:
        return session.execute(
            script_path=script_path,
            input_file=input_file,
            output_dir=output_dir,
            timeout_seconds=timeout_seconds,
            max_stdout_bytes=max_stdout_bytes,
            max_stderr_bytes=max_stderr_bytes,
        )

    command = [sys.executable, str(script_path), str(input_file), str(output_dir)]
    env = {"PYTHONHASHSEED": "0", "PYTHONIOENCODING": "utf-8"}
    if (script_path.parent / "process_kernel").is_dir():
        env["PYTHONDONTWRITEBYTECODE"] = "1"
    command_metadata = {
        "executable": Path(sys.executable).name,
        "argv": [Path(command[0]).name, str(script_path), str(input_file), str(output_dir)],
        "shell": False,
    }
    environment_metadata = {
        "inherited_environment": False,
        "allowlisted_keys": sorted(env.keys()),
    }

    try:
        completed = subprocess.run(
            command,
            cwd=str(working_dir),
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            shell=False,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        stdout, stdout_truncated = _bounded_text(exc.stdout or "", max_stdout_bytes)
        stderr, stderr_truncated = _bounded_text(exc.stderr or "", max_stderr_bytes)
        return LocalPythonResult(
            return_code=None,
            timed_out=True,
            stdout=stdout,
            stderr=stderr,
            stdout_truncated=stdout_truncated,
            stderr_truncated=stderr_truncated,
            command_metadata=command_metadata,
            environment_metadata=environment_metadata,
        )

    stdout, stdout_truncated = _bounded_text(completed.stdout, max_stdout_bytes)
    stderr, stderr_truncated = _bounded_text(completed.stderr, max_stderr_bytes)
    return LocalPythonResult(
        return_code=completed.returncode,
        timed_out=False,
        stdout=stdout,
        stderr=stderr,
        stdout_truncated=stdout_truncated,
        stderr_truncated=stderr_truncated,
        command_metadata=command_metadata,
        environment_metadata=environment_metadata,
    )


def _bounded_text(value: str | bytes, max_bytes: int) -> tuple[str, bool]:
    if isinstance(value, bytes):
        text = value.decode("utf-8", errors="replace")
    else:
        text = value
    encoded = text.encode("utf-8")
    if len(encoded) <= max_bytes:
        return text, False
    truncated = encoded[:max_bytes].decode("utf-8", errors="ignore")
    return truncated, True
