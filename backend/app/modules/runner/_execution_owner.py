from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


def _lock_file(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = path.open("a+b")
    handle.seek(0, os.SEEK_END)
    if handle.tell() == 0:
        handle.write(b"\0")
        handle.flush()
    handle.seek(0)
    if os.name == "nt":
        import msvcrt

        locking = getattr(msvcrt, "locking")
        lk_nblck = getattr(msvcrt, "LK_NBLCK")
        try:
            locking(handle.fileno(), lk_nblck, 1)
        except OSError:
            handle.close()
            return None
    else:
        import fcntl

        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            handle.close()
            return None
    return handle


def _unlock_file(handle) -> None:
    try:
        handle.seek(0)
        if os.name == "nt":
            import msvcrt

            locking = getattr(msvcrt, "locking")
            lk_unlck = getattr(msvcrt, "LK_UNLCK")
            locking(handle.fileno(), lk_unlck, 1)
        else:
            import fcntl

            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
    finally:
        handle.close()


def _bounded_text(value: str | bytes, max_bytes: int) -> tuple[str, bool]:
    if isinstance(value, bytes):
        text = value.decode("utf-8", errors="replace")
    else:
        text = value
    encoded = text.encode("utf-8")
    if len(encoded) <= max_bytes:
        return text, False
    return encoded[:max_bytes].decode("utf-8", errors="ignore"), True


def _emit(payload: dict[str, object]) -> bool:
    try:
        sys.stdout.write(json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n")
        sys.stdout.flush()
        return True
    except BrokenPipeError:
        return False


def main() -> int:
    if len(sys.argv) != 2:
        return 2
    lock_path = Path(sys.argv[1])
    lock_handle = _lock_file(lock_path)
    if lock_handle is None:
        _emit({"state": "busy"})
        return 3

    try:
        if not _emit({"state": "ready"}):
            return 0
        request_line = sys.stdin.readline()
        if not request_line:
            return 0
        request = json.loads(request_line)
        if request.get("action") != "run":
            return 0

        command = [str(value) for value in request["command"]]
        env = {str(key): str(value) for key, value in dict(request["env"]).items()}
        cwd = str(request["cwd"])
        timeout_seconds = int(request["timeout_seconds"])
        max_stdout_bytes = int(request["max_stdout_bytes"])
        max_stderr_bytes = int(request["max_stderr_bytes"])

        try:
            completed = subprocess.run(
                command,
                cwd=cwd,
                env=env,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                shell=False,
                check=False,
            )
            stdout, stdout_truncated = _bounded_text(completed.stdout, max_stdout_bytes)
            stderr, stderr_truncated = _bounded_text(completed.stderr, max_stderr_bytes)
            result = {
                "state": "completed",
                "return_code": completed.returncode,
                "timed_out": False,
                "stdout": stdout,
                "stderr": stderr,
                "stdout_truncated": stdout_truncated,
                "stderr_truncated": stderr_truncated,
            }
        except subprocess.TimeoutExpired as exc:
            stdout, stdout_truncated = _bounded_text(exc.stdout or "", max_stdout_bytes)
            stderr, stderr_truncated = _bounded_text(exc.stderr or "", max_stderr_bytes)
            result = {
                "state": "completed",
                "return_code": None,
                "timed_out": True,
                "stdout": stdout,
                "stderr": stderr,
                "stdout_truncated": stdout_truncated,
                "stderr_truncated": stderr_truncated,
            }

        if not _emit(result):
            return 0

        # Keep ownership alive through the caller's durable result/failure commit.
        # If the caller dies, pipe EOF releases the lock after child completion.
        sys.stdin.readline()
        return 0
    finally:
        _unlock_file(lock_handle)


if __name__ == "__main__":
    raise SystemExit(main())
