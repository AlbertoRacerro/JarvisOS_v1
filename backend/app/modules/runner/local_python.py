from dataclasses import dataclass
from pathlib import Path
import subprocess
import sys


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
    command = [sys.executable, str(script_path), str(input_file), str(output_dir)]
    env = {"PYTHONIOENCODING": "utf-8"}
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
