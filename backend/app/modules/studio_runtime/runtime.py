"""One-shot, fail-closed bubblewrap boundary for user-authored Python."""

import hashlib
import json
import os
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.core.config import get_settings

MECHANISM = "bubblewrap-userns-v1"
MAX_SOURCE_BYTES = 65_536
MAX_REQUEST_BYTES = 131_072
MAX_RESULT_BYTES = 65_536
MAX_LOG_BYTES = 16_384
MAX_WALL_SECONDS = 15
MAX_CPU_SECONDS = 12
MAX_MEMORY_BYTES = 1_073_741_824
MAX_PROCESSES = 32
MAX_FILE_BYTES = 131_072
MAX_SCRATCH_BYTES = 4 * 1024 * 1024


class Limits(BaseModel):
    model_config = ConfigDict(extra="forbid")
    wall_seconds: int = Field(default=10, ge=1, le=MAX_WALL_SECONDS)
    cpu_seconds: int = Field(default=8, ge=1, le=MAX_CPU_SECONDS)
    memory_bytes: int = Field(default=MAX_MEMORY_BYTES, ge=64 * 1024 * 1024, le=MAX_MEMORY_BYTES)
    processes: int = Field(default=MAX_PROCESSES, ge=1, le=MAX_PROCESSES)
    file_bytes: int = Field(default=MAX_FILE_BYTES, ge=1024, le=MAX_FILE_BYTES)


class RunRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source: str = Field(max_length=MAX_SOURCE_BYTES)
    inputs: dict[str, Any] = Field(default_factory=dict)
    limits: Limits = Field(default_factory=Limits)


class RunRecord(BaseModel):
    source_sha256: str
    limits: Limits
    mechanism: str
    duration_seconds: float
    classification: Literal["ok", "error", "timeout", "limit", "invalid_result", "unavailable", "disabled"]
    result: Any = None
    stdout: str = ""
    stderr: str = ""
    logs_truncated: bool = False


def _finite(value: Any) -> bool:
    if isinstance(value, dict):
        return all(isinstance(k, str) and _finite(v) for k, v in value.items())
    if isinstance(value, list):
        return all(_finite(v) for v in value)
    if isinstance(value, float):
        return value == value and abs(value) != float("inf")
    return value is None or isinstance(value, (str, int, bool))


def _paths() -> tuple[str, Path, Path] | None:
    if sys.platform != "linux":
        return None
    bwrap = shutil.which("bwrap")
    venv = Path(sys.prefix).resolve()
    worker = Path(__file__).with_name("worker.py").resolve()
    if not bwrap or not (venv / "bin/python").exists() or not worker.is_file():
        return None
    return bwrap, venv, worker


def _args(bwrap: str, venv: Path, worker: Path, scratch: Path) -> list[str]:
    args = [bwrap, "--unshare-all", "--die-with-parent", "--new-session", "--clearenv",
            "--ro-bind", "/usr", "/usr", "--proc", "/proc", "--dev", "/dev",
            "--dir", "/opt", "--dir", "/work", "--size", str(MAX_SCRATCH_BYTES),
            "--tmpfs", "/work", "--dir", "/work/tmp", "--symlink", "/work/tmp", "/tmp"]
    for directory in ("/lib", "/lib64", "/bin", "/sbin"):
        if Path(directory).exists():
            args += ["--ro-bind", directory, directory]
    for parent in reversed(venv.parents):
        if str(parent) not in ("/", "/usr", "/opt"):
            args += ["--dir", str(parent)]
    args += ["--ro-bind", str(venv), str(venv), "--ro-bind", str(worker), "/opt/worker.py",
             "--ro-bind", str(scratch / "request.json"), "/work/request.json",
             "--bind", str(scratch / "result.json"), "/work/result.json", "--setenv", "HOME", "/tmp",
             "--setenv", "PATH", f"{venv}/bin:/usr/bin:/bin", "--setenv", "PYTHONDONTWRITEBYTECODE", "1",
             "--setenv", "OPENBLAS_NUM_THREADS", "1", "--chdir", "/work", "--",
             str(venv / "bin/python"), "-I", "/opt/worker.py"]
    return args


def _launch(args: list[str], scratch: Path, limits: Limits) -> tuple[int | None, bool]:
    with (scratch / "stdout.log").open("wb") as stdout, (scratch / "stderr.log").open("wb") as stderr:
        process = subprocess.Popen(args, stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr,
                                   env={}, start_new_session=True)
        try:
            return process.wait(timeout=limits.wall_seconds), False
        except subprocess.TimeoutExpired:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait()
            return process.returncode, True


def _log(path: Path) -> tuple[str, bool]:
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode):
            raise ValueError("not a regular file")
        data = os.read(fd, MAX_LOG_BYTES)
    finally:
        os.close(fd)
    return data.decode("utf-8", errors="replace"), info.st_size > MAX_LOG_BYTES


def _result(path: Path) -> Any:
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_size > MAX_RESULT_BYTES:
            raise ValueError("invalid result file")
        data = os.read(fd, MAX_RESULT_BYTES + 1)
    finally:
        os.close(fd)
    value = json.loads(data.decode("utf-8"), parse_constant=lambda _: float("nan"))
    if not _finite(value):
        raise ValueError("non-finite result")
    return value


def status() -> dict[str, Any]:
    enabled = get_settings().studio_user_code_enabled
    paths = _paths()
    if not enabled:
        return {"enabled": False, "available": False, "mechanism": MECHANISM, "reason": "disabled"}
    if paths is None:
        return {"enabled": True, "available": False, "mechanism": MECHANISM, "reason": "bubblewrap_or_python_unavailable"}
    with tempfile.TemporaryDirectory(prefix="jarvis-studio-probe-") as directory:
        (Path(directory) / "request.json").touch()
        (Path(directory) / "result.json").touch()
        args = _args(*paths, Path(directory))
        args[-3:] = [str(paths[1] / "bin/python"), "-c", "print('studio-probe-ok')"]
        try:
            probe = subprocess.run(args, capture_output=True, timeout=3, env={}, check=False)
        except (OSError, subprocess.TimeoutExpired):
            probe = None
    available = probe is not None and probe.returncode == 0 and probe.stdout == b"studio-probe-ok\n"
    return {"enabled": True, "available": available, "mechanism": MECHANISM,
            "reason": None if available else "bubblewrap_probe_failed"}


def run(request: RunRequest) -> RunRecord:
    started = time.monotonic()
    digest = hashlib.sha256(request.source.encode("utf-8")).hexdigest()
    record = RunRecord(source_sha256=digest, limits=request.limits, mechanism=MECHANISM,
                       duration_seconds=0, classification="unavailable")
    if len(request.source.encode("utf-8")) > MAX_SOURCE_BYTES:
        record.classification = "invalid_result"
        return record
    state = status()
    if not state["enabled"] or not state["available"]:
        record.classification = "disabled" if not state["enabled"] else "unavailable"
        return record
    if not _finite(request.inputs):
        record.classification = "invalid_result"
        return record
    try:
        payload = json.dumps({"source": request.source, "inputs": request.inputs,
                              "limits": request.limits.model_dump()}, allow_nan=False).encode("utf-8")
    except (TypeError, ValueError):
        record.classification = "invalid_result"
        return record
    if len(payload) > MAX_REQUEST_BYTES:
        record.classification = "invalid_result"
        return record
    paths = _paths()
    if paths is None:
        return record
    with tempfile.TemporaryDirectory(prefix="jarvis-studio-run-") as directory:
        scratch = Path(directory)
        (scratch / "request.json").write_bytes(payload)
        (scratch / "result.json").touch()
        try:
            code, timed_out = _launch(_args(*paths, scratch), scratch, request.limits)
        except OSError:
            record.duration_seconds = time.monotonic() - started
            return record
        try:
            record.stdout, out_cut = _log(scratch / "stdout.log")
            record.stderr, err_cut = _log(scratch / "stderr.log")
        except (OSError, ValueError):
            record.classification = "invalid_result"
            record.duration_seconds = time.monotonic() - started
            return record
        record.logs_truncated = out_cut or err_cut
        record.duration_seconds = time.monotonic() - started
        if timed_out:
            record.classification = "timeout"
        elif code is not None and code < 0 and -code in (signal.SIGXCPU, signal.SIGXFSZ, signal.SIGKILL):
            record.classification = "limit"
        elif code != 0:
            record.classification = "error"
        else:
            try:
                data = _result(scratch / "result.json")
            except (OSError, UnicodeError, ValueError, RecursionError):
                record.classification = "invalid_result"
            else:
                record.classification = "ok"
                record.result = data
    return record
