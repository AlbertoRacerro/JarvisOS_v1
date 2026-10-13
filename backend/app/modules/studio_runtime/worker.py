"""Sandbox-side entry point. Never import this module in the backend process."""

import json
import resource
import sys
from pathlib import Path
from typing import Any


def main() -> None:
    request = json.loads(Path("/work/request.json").read_text(encoding="utf-8"))
    limits = request["limits"]
    for kind, value in (
        (resource.RLIMIT_CPU, limits["cpu_seconds"]),
        (resource.RLIMIT_AS, limits["memory_bytes"]),
        (resource.RLIMIT_NPROC, limits["processes"]),
        (resource.RLIMIT_FSIZE, limits["file_bytes"]),
    ):
        resource.setrlimit(kind, (value, value))
    namespace: dict[str, Any] = {"__name__": "__studio_user_code__"}
    exec(compile(request["source"], "<studio-source>", "exec"), namespace)  # noqa: S102 - inside bwrap only
    result = namespace["main"](request["inputs"])
    Path("/work/result.json").write_text(json.dumps(result), encoding="utf-8")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # noqa: BLE001 - errors cross only as bounded stderr
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        sys.exit(1)
