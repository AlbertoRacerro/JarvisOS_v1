#!/usr/bin/env python3
"""Run Relay 0.7.7 with the issue-847 output-parser repair, without editing its installation.

Install the pinned upstream package in a separate virtual environment, then invoke
that environment's Python with this script. All CLI arguments pass through unchanged.
No credentials, permissions, launch templates, journals or provider policy change.
"""
from __future__ import annotations

import hashlib
import importlib.metadata
from pathlib import Path

UPSTREAM_VERSION = "0.7.7"
SESSION_SOURCE_SHA256 = "f104a09fbdd2c1faeeab2cfe1d6fa977f5133d34c3bbbcd989807986e804e493"
SOURCE_SHA256 = "75ed02a50e3815faba2c35def52f92a451a830323a95f1fe9c3d691fc8322601"


def patched_source(source: bytes) -> str:
    """Fail closed on unfamiliar source; repair both quadratic searches in this detector."""
    if hashlib.sha256(source).hexdigest() != SOURCE_SHA256:
        raise RuntimeError("Relay run_errors.py differs from audited 0.7.7; repair refused")
    text = source.decode("utf-8")
    changes = (
        # Without a token boundary, a failing search retries every suffix of a
        # large token (notably successful tool output containing base64 images).
        ('(?:the\\s+)?', '(?<![^\'"\\s])(?:the\\s+)?'),
        # Repeated sandbox words with no denied suffix have the same retry
        # problem. Keep the fixed phrases in regex; test ordering per line.
        ('|sandbox.*denied', ''),
        ('if _PERMISSION.search(combined):', (
         'if _PERMISSION.search(combined) or any(\n'
         '        (sandbox := re.search("sandbox", line, re.IGNORECASE)) is not None\n'
         '        and re.search("denied", line[sandbox.end():], re.IGNORECASE) is not None\n'
         '        for line in combined.split("\\n")\n'
         '    ):')),
    )
    for old, new in changes:
        if text.count(old) != 1:
            raise RuntimeError("Relay patch precondition failed; repair refused")
        text = text.replace(old, new, 1)
    return text


def patched_session_source(source: bytes) -> str:
    """Keep ownership until the collector publishes output, including after child exit."""
    if hashlib.sha256(source).hexdigest() != SESSION_SOURCE_SHA256:
        raise RuntimeError("Relay agent_session.py differs from audited 0.7.7; repair refused")
    text = source.decode("utf-8")
    old = "return self._proc is not None and self._proc.poll() is None"
    if text.count(old) != 1:
        raise RuntimeError("Relay session patch precondition failed; repair refused")
    return text.replace(old, "return self._proc is not None", 1)


def apply_repair() -> None:
    if importlib.metadata.version("agent-relay-tool") != UPSTREAM_VERSION:
        raise RuntimeError("relay_safe requires the audited agent-relay-tool==0.7.7")
    from agent_relay import run_errors

    path = Path(run_errors.__file__)
    repaired = patched_source(path.read_bytes())
    # Execute the audited module with only the three substitutions above, before
    # CLI/session consumers import its functions. Upstream files remain untouched.
    exec(compile(repaired, str(path), "exec"), run_errors.__dict__)  # noqa: S102 — SHA-pinned upstream source
    from agent_relay.repl import agent_session

    session_path = Path(agent_session.__file__)
    repaired_session = patched_session_source(session_path.read_bytes())
    # Do this before CLI consumers import the session classes. A completed
    # subprocess can still have a collector parsing and publishing its output.
    exec(compile(repaired_session, str(session_path), "exec"), agent_session.__dict__)  # noqa: S102 — SHA-pinned upstream source


def main() -> int:
    apply_repair()
    from agent_relay.cli import main as relay_main

    return relay_main()


if __name__ == "__main__":
    raise SystemExit(main())
