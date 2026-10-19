#!/usr/bin/env python3
"""Relay provider continuity supervisor and Slack outbound monitor (spec 195).

Agent Relay owns sessions, transcripts and execution; this tool only reads its turn artifacts and
invokes its headless runner. It adds what Relay does not do reliably: deterministic classification
of a turn from raw evidence, a side-effect gate that refuses automatic continuation when an
interrupted turn may have left a non-idempotent operation in an unknown state, durable retry and
cooldown policy between Claude (preferred) and Codex (fallback), and sanitized outbound notices.

Standard library only. Never modifies the repository, Relay's configuration, permissions or
session journals. Durable state lives under ~/jarvis-control/work/continuity/.
"""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import importlib.util
import json
import os
import re
import secrets
import shlex
import shutil
import signal
import subprocess
import sys
import time
import tomllib
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

_DEVCTX_PATH = Path(__file__).resolve().parent / "devctx.py"
_spec = importlib.util.spec_from_file_location("devctx", _DEVCTX_PATH)
assert _spec and _spec.loader
devctx = sys.modules.get("devctx") or importlib.util.module_from_spec(_spec)
if "devctx" not in sys.modules:
    sys.modules["devctx"] = devctx
    _spec.loader.exec_module(devctx)

SCHEMA = "relay-continuity.v1"
AGENTS = ("claude", "codex")
PREFERRED = "claude"
OUTCOMES = ("success", "quota", "spend_limit", "transient", "auth", "crash", "unknown")
FAILURES = tuple(o for o in OUTCOMES if o != "success")
EFFECT_ORDER = ("read_only", "local_write", "background", "external", "unknown")
PHASES = ("idle", "running", "waiting", "held", "stopped")
HOLD_REASONS = (
    "effects_uncertain", "output_unparseable", "output_missing", "attempt_unresolved", "auth_failure", "unknown_failure",
    "crash_repeated", "circuit_failures", "circuit_switches", "circuit_attempts", "circuit_transient",
    "no_provider_available", "wait_exceeded", "permissions_changed", "state_corrupt", "repl_active",
    "relay_invocation_failed", "live_work",
)
STOP_REASONS = ("stop_requested", "signal", "idle", "held", "legacy_autopilot", "lock_busy", "error")
DEFAULT_CONTROL = Path.home() / "jarvis-control" / "work" / "continuity"
WEBHOOK_FILE = Path.home() / ".config" / "jarvis" / "slack_webhook_url"
LEGACY_MARKERS = ("jarvis-control/autopilot/run.sh", "jarvis-control/autopilot/watchdog.sh",
                  "jarvis-control/autopilot/resume-after-reset.sh", "jarvis-control/autopilot/drain-guard.sh")


@dataclass
class Limits:
    """Bounds that make every loop finite and prevent provider oscillation."""
    max_consecutive_failures: int = 8
    max_attempts_per_run: int = 40
    max_switches: int = 4
    switch_window: timedelta = timedelta(hours=6)
    min_dwell: timedelta = timedelta(minutes=20)
    max_transient_streak: int = 6
    transient_base: float = 60.0
    transient_cap: float = 1_800.0
    crash_retries: int = 1
    recheck: timedelta = timedelta(minutes=30)
    max_wait: timedelta = timedelta(days=8)
    reading_freshness: timedelta = timedelta(minutes=15)
    max_reset_ahead: timedelta = timedelta(days=8)


def now_utc() -> datetime:
    return datetime.now(UTC)


def iso(ts: datetime | None) -> str | None:
    return None if ts is None else ts.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_ts(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        ts = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    return ts if ts.tzinfo else ts.replace(tzinfo=UTC)


# ---------------------------------------------------------------------------
# Turn classification (raw evidence only; Relay's status/run_error never decide)


@dataclass
class ToolCall:
    id: str
    tool: str
    kind: str
    label: str
    done: bool
    background_open: bool = False
    background_closed: bool = False
    parent: str | None = None
    detached: bool = False
    ended_abnormally: bool = False  # killed/failed/stopped task, or an error tool result
    command_detached: bool = False  # the command itself detaches (`&`, nohup, tmux, a daemon): no event proves it ended

    @property
    def pending(self) -> bool:
        """Still possibly executing: no result yet, or a background launch whose completion was never seen
        (its tool result is only the launch acknowledgement)."""
        return (not self.done or self.background_open or (self.detached and not self.background_closed)
                or self.command_detached)


@dataclass
class TurnReport:
    outcome: str
    agent: str | None
    detail: str
    reset_at: str | None = None
    calls: list[ToolCall] = field(default_factory=list)
    bad_lines: int = 0
    terminal: bool = False
    relay_status: str | None = None
    no_evidence: bool = False  # the turn left no output of its own: nothing shows what it did
    turn_id: str | None = None  # "<session>/<turn>" of the classified turn
    spend_cap: bool = False  # the provider message named a spend/credit cap (even if it also printed a reset)

    @property
    def in_flight(self) -> list[ToolCall]:
        return [c for c in self.calls if c.pending and c.kind != "read_only"]

    @property
    def effects(self) -> list[ToolCall]:
        return [c for c in self.calls if not c.pending and c.kind != "read_only"]

    def to_json(self) -> dict[str, Any]:
        data = asdict(self)
        data["in_flight"] = [c.label for c in self.in_flight]
        return data


SPEND_RE = re.compile(r"(?i)monthly spend limit|spend limit|credit balance is too low|purchase more credits to continue")
QUOTA_RE = re.compile(r"(?i)hit your (session|weekly|usage|daily|5-hour|five-hour) limit|usage limit|rate[ _-]?limit|"
                      r"limit reached|too many requests|quota")
AUTH_RE = re.compile(r"(?i)invalid api key|please run /login|/login|oauth token (has )?expired|not logged in|"
                     r"unauthori[sz]ed|authentication (failed|error|required)|log ?in again|credentials? (expired|invalid)")
TRANSIENT_RE = re.compile(r"(?i)EAI_AGAIN|ENOTFOUND|ECONNRESET|ECONNREFUSED|ETIMEDOUT|EPIPE|can'?t reach the api|"
                          r"couldn'?t reach|unable to connect|network error|socket hang up|stream disconnected|"
                          r"error sending request|connection (reset|refused|closed|error)|overloaded|"
                          r"internal server error|bad gateway|service unavailable|gateway timeout|timed? ?out")
CLAUDE_RESET_RE = re.compile(
    r"(?i)resets\s+(?:(?P<mon>[A-Z][a-z]{2})\s+(?P<day>\d{1,2}),?\s+(?:at\s+)?)?"
    r"(?P<h>\d{1,2})(?::(?P<m>\d{2}))?\s*(?P<ap>am|pm)\s*\((?P<tz>[A-Za-z_]+(?:/[A-Za-z_+-]+)+)\)")
CODEX_RESET_RE = re.compile(
    r"(?i)try again (?:at|after)\s+(?:(?P<mon>[A-Z][a-z]{2})[a-z]*\s+(?P<day>\d{1,2})(?:st|nd|rd|th)?,?\s+(?:\d{4}\s+)?)?"
    r"(?P<h>\d{1,2})(?::(?P<m>\d{2}))?\s*(?P<ap>am|pm)")
STALE_RESET_WINDOW = timedelta(hours=6)
MONTHS = {m: i for i, m in enumerate(("jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"), 1)}


def classify_text(text: str, status: int | None) -> str:
    if SPEND_RE.search(text):
        return "spend_limit"
    if status == 429 or QUOTA_RE.search(text):
        return "quota"
    if status in (401, 403) or AUTH_RE.search(text):
        return "auth"
    if (status is not None and (500 <= status <= 599)) or TRANSIENT_RE.search(text):
        return "transient"
    return "unknown"


def parse_reset(text: str, ref: datetime, local_tz: Any = None) -> datetime | None:
    """Next occurrence after `ref` of a provider-printed reset time, or None."""
    if match := CLAUDE_RESET_RE.search(text):
        try:
            tz: Any = ZoneInfo(match["tz"])
        except (ZoneInfoNotFoundError, ValueError):
            return None
    elif match := CODEX_RESET_RE.search(text):
        tz = local_tz or datetime.now().astimezone().tzinfo
    else:
        return None
    hour = int(match["h"]) % 12 + (12 if match["ap"].lower() == "pm" else 0)
    minute = int(match["m"] or 0)
    local_ref = ref.astimezone(tz)
    if match["mon"] and match["mon"][:3].lower() in MONTHS:
        month, day = MONTHS[match["mon"][:3].lower()], int(match["day"])
        for year in (local_ref.year, local_ref.year + 1):
            try:
                cand = datetime(year, month, day, hour, minute, tzinfo=tz)
            except ValueError:
                return None
            if cand > local_ref - timedelta(minutes=1):
                return cand.astimezone(UTC)
        return None
    cand = local_ref.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if cand <= local_ref - timedelta(minutes=1):
        if local_ref - cand < STALE_RESET_WINDOW:
            # A time-only reset just behind the turn's end is a stale message, not tomorrow's reset;
            # report it as due now so the cooldown falls back to a short recheck instead of a day's stall.
            return ref.astimezone(UTC)
        cand += timedelta(days=1)
    return cand.astimezone(UTC)


READ_ONLY_CMDS = {
    "ls", "cat", "head", "tail", "grep", "rg", "egrep", "fgrep", "wc", "sort", "uniq", "cut", "tr", "awk", "echo",
    "printf", "pwd", "which", "type", "file", "stat", "du", "df", "ps", "pgrep", "date", "sleep", "true", "false",
    "test", "[", "diff", "cmp", "sha256sum", "sha1sum", "md5sum", "jq", "column", "basename", "dirname", "realpath",
    "readlink", "id", "whoami", "uname", "hostname", "nproc", "free", "uptime", "tree", "less", "more", "strings",
    "xxd", "od", "hexdump", "nvidia-smi", "comm", "paste", "join", "seq", "cd", "export", "set", "exit", "wait",
    "nl", "fold", "rev", "tac", "zcat", "lsof", "ss", "getent", "printenv", "locale", "tput", ":",
    "read", "mapfile", "readarray", "SUBST", "let", "shopt", "ulimit", "umask", "hash", "alias",
}
SHELL_KEYWORDS = {"for", "do", "done", "while", "until", "if", "then", "elif", "else", "fi", "case", "esac", "in",
                  "{", "}", "(", ")", "!", "function", "select", "time", "local", "declare", "return", "break",
                  "continue", "shift", "unset", "trap"}
LOCAL_WRITE_CMDS = {
    "rm", "mv", "cp", "mkdir", "rmdir", "touch", "chmod", "chown", "ln", "tee", "truncate", "dd", "tar", "unzip",
    "zip", "gzip", "gunzip", "patch", "install", "pip", "pip3", "npm", "pnpm", "yarn", "uv", "make", "pytest",
    "kill", "pkill", "killall", "systemctl", "crontab", "sqlite3", "alembic", "ruff", "mypy", "black", "prettier",
    "eslint", "tsc", "vite", "vitest", "playwright",
}
EXTERNAL_CMDS = {"ssh", "scp", "sftp", "nc", "ncat", "telnet", "sendmail", "mail", "twine", "notify-slack.sh"}
WRAPPERS = {"timeout", "nice", "ionice", "stdbuf", "command", "builtin", "exec", "xvfb-run", "env"}
BACKGROUND_WRAPPERS = {"nohup", "setsid", "disown", "systemd-run", "daemonize"}
DETACH_FLAGS = {"--detach", "--daemon", "--daemonize", "--background"}
TMUX_GLOBAL_VALUE_OPTS = {"-L", "-S", "-f", "-c", "-T"}
SCREEN_VALUE_OPTS = {"-S", "-c", "-e", "-h", "-p", "-s", "-t", "-T", "-Logfile"}
XXD_VALUE_OPTS = {"-c", "-cols", "-g", "-groupsize", "-l", "-len", "-o", "-s", "-seek", "-n", "-name"}
TMUX_LAUNCH = {"new-session", "new", "new-window", "neww", "split-window", "splitw", "send-keys", "send",
               "run-shell", "run", "respawn-pane", "respawnp", "respawn-window", "respawnw"}
GIT_READ = {"status", "log", "diff", "show", "fetch", "rev-parse", "ls-files", "ls-tree", "cat-file", "merge-base",
            "merge-tree", "describe", "blame", "grep", "for-each-ref", "rev-list", "shortlog", "remote", "reflog",
            "show-ref", "name-rev", "check-ignore", "count-objects", "verify-commit", "range-diff", "whatchanged"}
GH_READ = {("pr", "view"), ("pr", "list"), ("pr", "checks"), ("pr", "diff"), ("pr", "status"), ("run", "view"),
           ("run", "list"), ("run", "watch"), ("repo", "view"), ("issue", "view"), ("issue", "list"),
           ("release", "view"), ("release", "list"), ("auth", "status"), ("search", "prs"), ("search", "issues"),
           ("search", "code"), ("workflow", "list"), ("workflow", "view"), ("cache", "list")}
# awk programs that run commands (system(), pipes to/from commands) or print into files.
# awk runs commands through system(), getline from a pipe, or print/printf into a pipe; it writes with
# `print > file`. Any pipe or output redirection in the program is treated as execution (`||` included).
AWK_EXEC = re.compile(r"system\s*\(|\||print[f]?\b[^;}]*>")
SED_ADDRESS = re.compile(r"\s*(?:(?:\d+(?:~\d+)?|\$|/(?:\\.|[^/\\])*/[IM]*|\\(.)(?:\\.|(?!\1).)*\1[IM]*)"
                         r"(?:\s*,\s*(?:[+~]?\d+|\$|/(?:\\.|[^/\\])*/[IM]*))?)?\s*!?\s*")


def sed_scripts(args: list[str]) -> tuple[list[str], bool]:
    """Every sed program text (`-e S`, `-eS`, `--expression=S`, bare S), and whether one is read from a file."""
    scripts, from_file, i = [], False, 0
    while i < len(args):
        a = args[i]
        if a in ("-f", "--file") or a.startswith("--file="):
            from_file = True
        elif a.startswith("--expression="):
            scripts.append(a.split("=", 1)[1])
        elif a in ("-e", "--expression") and i + 1 < len(args):
            scripts.append(args[i + 1])
            i += 1
        elif a.startswith("-") and not a.startswith("--"):
            cluster = a[1:]
            for j, ch in enumerate(cluster):
                if ch == "f":
                    from_file = True
                    break
                if ch == "e":
                    if cluster[j + 1:]:
                        scripts.append(cluster[j + 1:])
                    elif i + 1 < len(args):
                        scripts.append(args[i + 1])
                        i += 1
                    break
        elif not a.startswith("-"):
            scripts.append(a)
        i += 1
    return scripts, from_file


def sed_executes(script: str) -> bool:
    """Whether a sed program can run commands or write files: an `e`, `w` or `W` command, or an `s` command
    with an `e`/`w` flag, after any address. Unparseable programs count as executing."""
    i, n = 0, len(script)
    while i < n:
        while i < n and script[i] in " \t\n;{}":
            i += 1
        if i >= n:
            return False
        match = SED_ADDRESS.match(script, i)
        i = match.end() if match else i
        if i >= n:
            return False
        cmd = script[i]
        if cmd in "ewW":
            return True
        if cmd == "s":
            if i + 1 >= n:
                return True
            delim, j, parts = script[i + 1], i + 2, 0
            while j < n and parts < 2:
                if script[j] == "\\":
                    j += 2
                    continue
                if script[j] == delim:
                    parts += 1
                j += 1
            if parts < 2:
                return True  # unterminated substitution: cannot tell
            flags = re.match(r"[A-Za-z0-9]*", script[j:]).group(0)
            if set(flags) & set("ewW"):
                return True
            i = j + len(flags)
        elif cmd in "aic":
            # text commands consume the rest of the line
            nl = script.find("\n", i)
            i = n if nl == -1 else nl + 1
        elif cmd in "rRbtTvy:#":
            nl = script.find("\n", i)
            if cmd == "y":
                # y/src/dst/: the opening delimiter, then exactly two more
                if i + 1 >= n:
                    return True
                delim, j, parts = script[i + 1], i + 2, 0
                while j < n and parts < 2:
                    if script[j] == "\\":
                        j += 2
                        continue
                    if script[j] == delim:
                        parts += 1
                    j += 1
                if parts < 2:
                    return True
                i = j
            elif cmd in "rR":
                return True  # reads a file: harmless, but its argument runs to end of line; stay conservative
            elif cmd == "#":
                i = n if nl == -1 else nl + 1
            else:  # b/t/T/v/: take a label that ends at `;` or a newline (GNU); later commands still count
                ends = [k for k in (script.find(";", i), nl) if k != -1]
                i = min(ends) + 1 if ends else n
        else:
            i += 1
    return False

REDIRECT = re.compile(r"(?<![<>])(?:[0-9]*|&)>{1,2}(?!&)\s*(?!/dev/(?:null|stdout|stderr)\b)(\S+)")


def _rank(kind: str) -> int:
    return EFFECT_ORDER.index(kind)


def _worst(kinds: list[str]) -> str:
    return max(kinds, key=_rank) if kinds else "read_only"


def _operands(args: list[str], value_opts: set[str]) -> list[str]:
    """Non-option arguments, skipping the separate value of each option in `value_opts`."""
    out: list[str] = []
    skip = False
    for a in args:
        if skip:
            skip = False
        elif a.startswith("-") and a != "-":
            skip = a in value_opts
        else:
            out.append(a)
    return out


TMUX_READ = {"ls", "list-sessions", "has-session", "has", "capture-pane", "capturep", "list-windows", "lsw",
             "list-panes", "lsp", "display-message", "display", "show-options", "show"}


def _tmux_commands(args: list[str]) -> list[str]:
    """The command name of every entry in a tmux command list (`a \\; b`, a `;` word after shlex), after the
    global options."""
    groups: list[list[str]] = [[]]
    for a in args:
        if a in (";", "\\;"):
            groups.append([])
        else:
            groups[-1].append(a)
    first = next(iter(_operands(groups[0], TMUX_GLOBAL_VALUE_OPTS)), "")
    return [c for c in [first, *(g[0] for g in groups[1:] if g)] if c]


def _tmux_launches(command: str) -> bool:
    if command in TMUX_LAUNCH or command in ("source-file", "source"):
        return True
    # tmux accepts any unambiguous prefix (`new-s`); a prefix of a launch command counts as one
    return len(command) >= 3 and any(c.startswith(command) for c in TMUX_LAUNCH | {"source-file"} if "-" in c)


def _screen_detached(args: list[str]) -> bool:
    """`screen -dm`, `screen -d -m`, `screen -DmS name`: the session runs on after screen returns."""
    letters: set[str] = set()
    skip = False
    for a in args:
        if skip:
            skip = False
        elif a.startswith("-") and not a.startswith("--"):
            letters.update(a[1:])
            skip = a in SCREEN_VALUE_OPTS
        else:
            break  # the program and its own arguments
    return bool(letters & {"d", "D"}) and "m" in letters


def _container_detached(args: list[str]) -> bool:
    """`run -d`, `exec -d`, `compose up -d`, `start`/`restart`: containers keep running after the CLI returns."""
    # Token-based on purpose: option values (`-f compose.dev.yml`, `-p name`) make positional subcommand parsing
    # fragile, and an extra hold on a coincidental token is acceptable where a missed detachment is not.
    if any(a in ("--detach", "--wait") or a.startswith("--detach=")  # `up --wait` implies -d
           or (a.startswith("-") and not a.startswith("--") and "d" in a[1:]) for a in args):  # -d, -dt, -itd
        return True
    return (any(a in ("start", "restart", "unpause") for a in args if not a.startswith("-"))
            and "-a" not in args and "--attach" not in args)


GIT_BRANCH_READ_OPTS = {"-a", "--all", "-r", "--remotes", "-v", "-vv", "--verbose", "-l", "--list", "--show-current",
                        "--merged", "--no-merged", "--contains", "--no-contains", "--points-at", "--color",
                        "--no-color", "--column", "--no-column", "-i", "--ignore-case", "--omit-empty"}
GIT_BRANCH_FILTERS = {"-l", "--list", "--merged", "--no-merged", "--contains", "--no-contains", "--points-at"}


def _git_branch_lists(rest: list[str]) -> bool:
    """`git branch` only lists when every option is a listing option; a bare name creates a branch."""
    for a in rest:
        if a.startswith("-") and a not in GIT_BRANCH_READ_OPTS and not a.startswith(
                ("--format=", "--sort=", "--color=", "--column=", "--merged=", "--no-merged=", "--contains=",
                 "--no-contains=", "--points-at=")):
            return False
    names = [a for a in rest if not a.startswith("-")]
    return not names or any(a in GIT_BRANCH_FILTERS for a in rest)


def _git_kind(args: list[str]) -> tuple[str, str]:
    i = 0
    while i < len(args) and args[i].startswith("-"):
        i += 2 if args[i] in ("-C", "-c", "--git-dir", "--work-tree") else 1
    sub = args[i] if i < len(args) else ""
    rest = args[i + 1:]
    label = f"git {sub}".strip()
    if sub == "push":
        return "external", label
    if sub in GIT_READ:
        if any(a == "--output" or a.startswith("--output=") for a in rest):
            return "local_write", f"{label} --output"  # diff-family `--output` creates or truncates a file
        if sub == "remote":
            ops = [a for a in rest if a not in ("-v", "--verbose")]
            return ("read_only" if not ops or ops[0] in ("show", "get-url") else "local_write"), label
        if sub == "reflog" and any(a in ("expire", "delete", "drop") for a in rest):
            return "local_write", label
        return "read_only", label
    if sub == "branch" and _git_branch_lists(rest):
        return "read_only", label
    if sub == "worktree" and rest[:1] == ["list"]:
        return "read_only", "git worktree list"
    if sub == "stash" and rest[:1] in (["list"], ["show"]):
        return "read_only", label
    if sub == "tag" and (not rest or rest[0] in ("-l", "--list")):
        return "read_only", label
    if sub == "config" and rest[:1] in (["--get"], ["--list"], ["-l"], ["--get-all"]):
        return "read_only", label
    return "local_write", label


def _gh_kind(args: list[str]) -> tuple[str, str]:
    words = [a for a in args if not a.startswith("-")]
    pair = tuple(words[:2])
    label = "gh " + " ".join(words[:2])
    if words[:1] == ["api"]:
        method, fields = None, False
        for i, a in enumerate(args):
            if a in ("-X", "--method") and i + 1 < len(args):
                method = args[i + 1].upper()
            elif a.startswith("--method="):
                method = a.split("=", 1)[1].upper()
            elif a.startswith("-X") and len(a) > 2:
                method = a[2:].upper()
            elif a.startswith(("-f", "-F", "--field", "--raw-field", "--input")):
                fields = True  # `-f k=v`, attached `-fk=v`, `--field=k=v`: gh switches to POST
        if "graphql" in words[1:2]:
            method = method or "POST"
        method = method or ("POST" if fields else "GET")
        return ("read_only" if method in ("GET", "HEAD") else "external"), f"gh api {method}"
    if pair in GH_READ:
        return "read_only", label
    return "external", label


def _curl_kind(word: str, args: list[str]) -> tuple[str, str]:
    if word == "curl" and any(a == "--config" or a.startswith("--config=")
                              or (a.startswith("-") and not a.startswith("--") and "K" in a[1:]) for a in args):
        return "unknown", "curl --config"  # a config file can set any method, body or output
    writes = _download_writes(word, args)
    for i, a in enumerate(args):
        nxt = args[i + 1] if i + 1 < len(args) else ""
        if a.startswith(("--request", "--method")):
            method = (a.split("=", 1)[1] if "=" in a else nxt).upper()
            if method not in ("GET", "HEAD"):
                return "external", f"{word} {method or '?'}"
        elif a.startswith(("--data", "--form", "--upload-file", "--json", "--post", "--body", "--put")):
            return "external", f"{word} POST"
        elif a.startswith("-") and not a.startswith("--"):
            # Short-option cluster (`-sXPOST`, `-sd@f`): X/d/F/T take the rest of the cluster or the next word.
            for j, ch in enumerate(a[1:], 1):
                if ch == "X":
                    method = (a[j + 1:] or nxt).upper()
                    if method not in ("GET", "HEAD"):
                        return "external", f"{word} {method or '?'}"
                    break
                if ch in "dFT":
                    return "external", f"{word} POST"
                if ch in "oOHuAeEbcKw":  # options whose value follows; stop scanning the cluster
                    break
    return ("local_write", f"{word} > file") if writes else ("read_only", f"{word} GET")


def _download_writes(word: str, args: list[str]) -> bool:
    """Whether curl/wget writes the response (or headers/cookies) to a file rather than stdout."""
    def to_file(value: str) -> bool:
        return value not in ("-", "/dev/null", "/dev/stdout", "/dev/stderr", "")
    if word == "wget":
        # wget saves to a file unless the output document is stdout or /dev/null, or it only checks (--spider).
        if any(a in ("--output-file", "--append-output", "--background") or a.startswith(("--output-file=", "--append-output="))
               or (a.startswith("-") and not a.startswith("--") and set(a[1:]) & set("oab")) for a in args):
            return True  # -o/-a log files, and -b writes wget-log
        if "--spider" in args:
            return False
        for i, a in enumerate(args):
            if a in ("-O", "--output-document") and i + 1 < len(args):
                return to_file(args[i + 1])
            if a.startswith("--output-document="):
                return to_file(a.split("=", 1)[1])
            if a.startswith("-O") and len(a) > 2:
                return to_file(a[2:])
            if a.startswith("-") and not a.startswith("--") and "O" in a[1:]:
                rest = a[a.index("O") + 1:]
                return to_file(rest or (args[i + 1] if i + 1 < len(args) else ""))
        return True
    for i, a in enumerate(args):
        nxt = args[i + 1] if i + 1 < len(args) else ""
        if a in ("--remote-name", "--remote-name-all", "--output-dir", "--create-dirs"):
            return True
        if a.startswith(("--output", "--dump-header", "--cookie-jar", "--trace", "--stderr")):
            value = a.split("=", 1)[1] if "=" in a else nxt
            if to_file(value):
                return True
        elif a.startswith("-") and not a.startswith("--"):
            for j, ch in enumerate(a[1:], 1):
                if ch == "O":
                    return True
                if ch in "oDc":
                    if to_file(a[j + 1:] or nxt):
                        return True
                    break
                if ch in "XdFTHuAeEbKw":
                    break
    return False


def strip_heredocs(command: str) -> str:
    """Remove heredoc bodies: they are data written somewhere, not commands. An unquoted delimiter's body
    still expands $(...) and backticks, so those substitutions are kept as commands."""
    lines, out, i = command.split("\n"), [], 0
    while i < len(lines):
        line = lines[i]
        out.append(line)
        delims = re.findall(r"(?<!<)<<(?!<)-?\s*(['\"\\]?)([A-Za-z_][A-Za-z0-9_]*)['\"]?", line)
        i += 1
        for quote, delim in delims:
            body = []
            while i < len(lines) and lines[i].strip() != delim:
                body.append(lines[i])
                i += 1
            i += 1
            if not quote:
                out.extend(f"$({sub})" for sub in substitutions("\n".join(body))[0])
    return "\n".join(out)


def split_segments(command: str) -> list[str]:
    """Split on ; & | && || and newlines outside quotes, $(...) and backslash escapes."""
    segments, current, quote, depth, i = [], [], None, 0, 0
    while i < len(command):
        ch = command[i]
        if quote:
            current.append(ch)
            if ch == "\\" and quote == '"' and i + 1 < len(command):
                current.append(command[i + 1])
                i += 1
            elif ch == quote:
                quote = None
        elif ch == "\\" and i + 1 < len(command):
            current.append(command[i:i + 2])
            i += 1
        elif ch in ("'", '"'):
            quote = ch
            current.append(ch)
        elif command.startswith("$(", i):
            depth += 1
            current.append("$(")
            i += 1
        elif ch == ")" and depth:
            depth -= 1
            current.append(ch)
        elif depth == 0 and ch in ";|\n":
            segments.append("".join(current))
            current = []
            if command.startswith(("||", "|&"), i):
                i += 1
        elif depth == 0 and ch == "&":
            if command.startswith("&&", i):
                segments.append("".join(current))
                current = []
                i += 1
            elif i > 0 and command[i - 1] in "<>" or command.startswith("&>", i) or command.startswith("&1", i) or command.startswith("&2", i):
                current.append(ch)
            else:
                current.append(ch)
                segments.append("".join(current))
                current = []
        else:
            current.append(ch)
        i += 1
    segments.append("".join(current))
    return [seg for seg in segments if seg.strip()]


def split_first_word(text: str) -> tuple[str | None, str]:
    """The first shell word of `text` (quotes removed) and the raw text after it, or (None, text)."""
    lexer = shlex.shlex(text, posix=True)
    lexer.whitespace_split = True
    lexer.commenters = ""
    try:
        first = lexer.get_token()
    except ValueError:
        return None, text
    if not first:
        return None, text
    return first, text[lexer.instream.tell():]


def substitutions(command: str) -> tuple[list[str], str]:
    """Bodies of $(...), <(...), >(...) and backtick substitutions (they run as commands), and the
    command text with each substitution replaced by a placeholder word."""
    bodies, outer, i = [], [], 0
    while i < len(command):
        if command.startswith(("$(", "<(", ">("), i) and not command.startswith("$((", i):
            depth, j = 1, i + 2
            while j < len(command) and depth:
                depth += {"(": 1, ")": -1}.get(command[j], 0)
                j += 1
            bodies.append(command[i + 2:j - 1])
            outer.append("SUBST")
            i = j
        elif command[i] == "`":
            j = command.find("`", i + 1)
            end = len(command) if j == -1 else j
            bodies.append(command[i + 1:end])
            outer.append("SUBST")
            i = end + 1
        else:
            outer.append(command[i])
            i += 1
    return [b for b in bodies if b.strip()], "".join(outer)


def classify_command(command: str, _depth: int = 0) -> tuple[str, str]:
    """Worst effect class over every shell segment, with a short label of the worst segment."""
    command = command.strip()
    if _depth > 4:
        return "unknown", "nested substitution"
    for prefix in ("bash -lc ", "bash -c ", "/bin/bash -lc ", "/bin/bash -c ", "sh -c ", "/bin/sh -c "):
        if command.startswith(prefix):
            program, rest = split_first_word(command[len(prefix):])
            if program is not None:
                # The wrapped program is classified as a command; whatever follows it in the outer shell
                # (redirections, `&`, `; more`) is classified too, with the program as a neutral placeholder.
                wrapper = prefix.split()[0]
                parts = [classify_command(program, _depth + 1)]
                if rest.strip():
                    outer_kind, outer_label = classify_command(f"true {rest}", _depth + 1)
                    outer_label = outer_label.replace("true", wrapper, 1)
                    if outer_label.startswith(wrapper) and outer_label.endswith(" &") and not parts[0][1].endswith(" &"):
                        parts[0] = (parts[0][0], f"{parts[0][1]} &")  # an outer `&` detaches the wrapped program
                    parts.append((outer_kind, outer_label))
                # Detachment from either side survives, independently of which side has the worse effect.
                return _combine(parts)
            break
    bodies, outer = substitutions(strip_heredocs(command))
    results: list[tuple[str, str]] = [classify_command(body, _depth + 1) for body in bodies]
    for raw in split_segments(outer):
        seg = raw.strip()
        if not seg:
            continue
        background = seg.endswith("&") and not seg.endswith("&&")
        seg = seg.rstrip("&").strip()
        try:
            words = shlex.split(seg, comments=True)
        except ValueError:
            words = seg.split()
        if words and words[0] == "case":
            # `case WORD in PATTERN) BODY`: the arm body runs, so it is classified; a bare header is skipped.
            arm = next((k for k in range(2, len(words)) if ")" in words[k] and "in" in words[1:k]), None)
            if arm is None:
                continue
            tail = words[arm].split(")", 1)[1]
            words = ([tail] if tail else []) + words[arm + 1:]
        # Subshell parentheses are grouping, not part of a command word.
        words = [w.rstrip(")") if w.count(")") > w.count("(") else w for w in words]
        while words and words[0].startswith("(") and not words[0].startswith("(("):
            words = ([words[0][1:]] if words[0][1:] else []) + words[1:]
        if words and words[0] in ("for", "select"):
            continue  # loop headers bind variables; their bodies are separate segments
        while words and (re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*=.*", words[0]) or words[0] in SHELL_KEYWORDS
                         or re.fullmatch(r"\d*[<>]{1,2}&?\S*", words[0])):
            bare_redirect = bool(re.fullmatch(r"\d*[<>]{1,2}", words[0]))
            words = words[2:] if bare_redirect else words[1:]
        while words and (words[0] in WRAPPERS or words[0] in BACKGROUND_WRAPPERS):
            background = background or words[0] in BACKGROUND_WRAPPERS
            words = words[1:]
            while words and (words[0].startswith("-") or re.fullmatch(r"[0-9.]+[smhd]?", words[0])
                             or re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*=.*", words[0])):
                words = words[1:]
        if not words:
            if REDIRECT.search(seg):
                results.append(("local_write", "> file"))  # a bare redirection truncates or creates a file
            continue
        word = Path(words[0]).name
        args = words[1:]
        if word == "git":
            kind, label = _git_kind(args)
        elif word == "gh":
            kind, label = _gh_kind(args)
        elif word in ("curl", "wget"):
            kind, label = _curl_kind(word, args)
        elif word == "sed":
            scripts, from_file = sed_scripts(args)
            if from_file or any(sed_executes(a) for a in scripts):
                kind, label = "unknown", "sed e/w"  # GNU sed can execute commands and write files
            else:
                in_place = any(a == "--in-place" or a.startswith("--in-place=")
                               or (a.startswith("-") and not a.startswith("--") and "i" in a[1:]) for a in args)
                kind, label = ("local_write" if in_place else "read_only"), "sed"
        elif word in ("awk", "gawk", "mawk", "nawk"):
            from_file = any(a in ("-f", "--file", "-i", "--include", "-l", "--load") or a.startswith(("-f", "--file=", "-i", "--include="))
                            for a in args)
            kind, label = ("unknown" if from_file or any(AWK_EXEC.search(a) for a in args) else "read_only"), word
        elif word == "find":
            if any(a in ("-delete", "-fprint", "-fprint0", "-fprintf", "-fls") for a in args):
                kind, label = "local_write", "find (writes)"
            elif any(a in ("-exec", "-execdir", "-ok", "-okdir") for a in args):
                kind, label = "unknown", "find -exec"
            else:
                kind, label = "read_only", "find"
        elif word == "tmux":
            subs = _tmux_commands(args)
            if launched := next((c for c in subs if _tmux_launches(c)), None):
                # The command keeps running in the tmux server; the tool result only acknowledges the launch.
                kind, label, background = "unknown", f"tmux {launched}", True
            else:
                kind, label = ("read_only" if subs and all(c in TMUX_READ for c in subs) else "local_write"), "tmux"
        elif word == "screen" and (_screen_detached(args) or "-X" in args):
            kind, label, background = "unknown", "screen -dm", True
        elif word == "xxd" and len(_operands(args, XXD_VALUE_OPTS)) >= 2:
            kind, label = "local_write", "xxd > file"  # `xxd IN OUT` (and `xxd -r IN OUT`) writes OUT
        elif word in ("python", "python3") and args[:1] and args[0].endswith("devctx.py"):
            kind = "read_only" if args[1:2] in (["recover"], ["show"], ["search"], ["lanes"]) else "local_write"
            label = "devctx " + (args[1] if len(args) > 1 else "")
        elif word in ("python", "python3") and args[:1] and args[0].endswith("relay_continuity.py"):
            kind = "read_only" if args[1:2] in (["status"], ["classify"]) else "unknown"
            label = "relay_continuity " + (args[1] if len(args) > 1 else "")
        elif word == "rsync":
            kind, label = ("external" if any(":" in a and not a.startswith("-") for a in args) else "local_write"), "rsync"
        elif word in ("docker", "podman") and args[:1] == ["push"]:
            kind, label = "external", f"{word} push"
        elif word == "pm2" and args[:1] and args[0] in ("start", "restart", "reload", "resurrect"):
            kind, label, background = "unknown", f"pm2 {args[0]}", True  # pm2 runs the process under its daemon
        elif word == "gunicorn" and any(a == "-D" or (a.startswith("-") and not a.startswith("--") and "D" in a[1:])
                                        for a in args):
            kind, label, background = "unknown", "gunicorn -D", True
        elif word in ("docker", "podman", "docker-compose", "podman-compose") and _container_detached(args):
            kind, label, background = "unknown", f"{word} detached", True
        elif word in ("npm", "pnpm", "yarn") and args[:1] == ["publish"]:
            kind, label = "external", f"{word} publish"
        elif word == "sort" and any(a == "--output" or a.startswith("--output=")
                                    or (a.startswith("-") and not a.startswith("--") and "o" in a[1:]) for a in args):
            kind, label = "local_write", "sort -o"
        elif word == "uniq" and len([a for a in args if not a.startswith("-")]) >= 2:
            kind, label = "local_write", "uniq > file"  # `uniq IN OUT` writes OUT
        elif word in READ_ONLY_CMDS:
            kind, label = "read_only", word
        elif word in LOCAL_WRITE_CMDS:
            kind, label = "local_write", word
        elif word in EXTERNAL_CMDS:
            kind, label = "external", word
        else:
            kind, label = "unknown", word[:40]
        if REDIRECT.search(seg) and kind == "read_only":
            kind, label = "local_write", f"{label} > file"
        if any(a.split("=", 1)[0] in DETACH_FLAGS for a in args):
            # Any command asked to detach or daemonize outlives its tool result, whatever its kind.
            kind, background = (kind if _rank(kind) > _rank("unknown") else "unknown"), True
        if background:
            # The label keeps the detach marker whatever the kind: its tool result is only a launch.
            kind, label = (kind if _rank(kind) > _rank("background") else "background"), f"{label} &"
        results.append((kind, label))
    if not results:
        return "read_only", "(empty)"
    return _combine(results)


def _combine(results: list[tuple[str, str]]) -> tuple[str, str]:
    kind, label = max(results, key=lambda r: _rank(r[0]))
    detached = [r for r in results if r[1].endswith(" &")]
    if detached:
        # Any detached segment makes the whole call a background launch, whichever segment is the worst; the
        # label names the worst detached job, since that is what may still be running.
        label = max(detached, key=lambda r: _rank(r[0]))[1]
    return kind, label


TASK_DONE = ("completed", "failed", "killed", "stopped")
CLAUDE_TOOL_KINDS = {
    **{t: "read_only" for t in ("Read", "Grep", "Glob", "LS", "ToolSearch", "WebSearch", "WebFetch", "BashOutput",
                                "TaskOutput", "ListAgents", "NotebookRead", "TodoWrite", "Skill", "Monitor",
                                "ReportFindings", "ExitPlanMode")},
    **{t: "local_write" for t in ("Edit", "Write", "MultiEdit", "NotebookEdit", "EnterWorktree", "ExitWorktree",
                                  "TaskStop", "KillShell", "KillBash")},
    **{t: "external" for t in ("PushNotification", "SendMessage", "RemoteTrigger", "CronCreate", "CronDelete",
                               "ScheduleWakeup")},
}


def _claude_call(block: dict[str, Any]) -> ToolCall:
    name = str(block.get("name") or "?")
    inp = block.get("input") or {}
    if name == "Bash":
        kind, label = classify_command(str(inp.get("command") or ""))
    else:
        kind = CLAUDE_TOOL_KINDS.get(name, "unknown")
        label = name if not inp.get("file_path") else f"{name} {Path(str(inp['file_path'])).name}"
    command_detached = label.endswith(" &")
    detached = bool(inp.get("run_in_background")) or command_detached
    if inp.get("run_in_background"):
        # e.g. a background Agent or shell job: its tool result is a launch acknowledgement, not completion
        kind = kind if _rank(kind) > _rank("background") else "background"
        label = label if label.endswith(" &") else f"{label} &"
    return ToolCall(id=str(block.get("id")), tool=name, kind=kind, label=label[:80], done=False, detached=detached,
                    command_detached=command_detached)


def _codex_call(item: dict[str, Any]) -> ToolCall | None:
    typ = item.get("type")
    if typ == "command_execution":
        kind, label = classify_command(str(item.get("command") or ""))
    elif typ == "file_change":
        kind, label = "local_write", "file_change"
    elif typ == "mcp_tool_call":
        kind, label = "unknown", f"mcp {item.get('server', '?')}.{item.get('tool', '?')}"
    elif typ == "web_search":
        kind, label = "read_only", "web_search"
    else:
        return None
    return ToolCall(id=str(item.get("id")), tool=str(typ), kind=kind, label=str(label)[:80], done=False,
                    detached=str(label).endswith(" &"), command_detached=str(label).endswith(" &"))


def read_events(path: Path) -> tuple[list[dict[str, Any]], int]:
    events, bad = [], 0
    if not path.exists():
        return events, 0
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    for line in lines:
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            # Unparseable lines, including a torn final line from an interrupted writer, make effects uncertain.
            bad += 1
            continue
        if isinstance(item, dict):
            events.append(item)
    return events, bad


def classify_turn(turn_dir: Path, *, ref: datetime | None = None, local_tz: Any = None,
                  diagnostics: str = "") -> TurnReport:
    state: dict[str, Any] = {}
    try:
        state = json.loads((turn_dir / "state.json").read_text())
    except (OSError, json.JSONDecodeError):
        pass
    output = turn_dir / "output.jsonl"
    events, bad = read_events(output)
    agent = state.get("agent_key")
    if agent not in AGENTS:
        agent = "codex" if any(e.get("type") == "thread.started" for e in events) else (
            "claude" if any(e.get("type") in ("result", "system") for e in events) else None)
    if ref is None:
        try:
            ref = datetime.fromtimestamp(output.stat().st_mtime, UTC)
        except OSError:
            ref = now_utc()
    calls: dict[str, ToolCall] = {}
    task_calls: dict[str, str] = {}
    report = TurnReport(outcome="crash", agent=agent, detail="no terminal event", bad_lines=bad,
                        relay_status=state.get("status"), turn_id=f"{turn_dir.parent.parent.name}/{turn_dir.name}")
    if not events:
        report.detail = "output missing" if not output.exists() else ("output unparseable" if bad else "output empty")
        report.no_evidence = not bad
        return no_terminal_evidence(report, turn_dir, diagnostics)
    if same_output_as_previous_turn(turn_dir):
        # Relay keeps the previous turn's output when it captures nothing ("No response captured"); the agent
        # may still have worked for hours. Those events are not this turn's evidence.
        report.detail, report.no_evidence = "no output of its own (previous turn's output kept)", True
        return no_terminal_evidence(report, turn_dir, diagnostics)
    terminal: dict[str, Any] | None = None
    terminal_index = -1
    for idx, e in enumerate(events):
        typ = e.get("type")
        if typ == "assistant":
            for block in (e.get("message") or {}).get("content") or []:
                if isinstance(block, dict) and block.get("type") == "tool_use":
                    call = _claude_call(block)
                    call.parent = e.get("parent_tool_use_id")
                    calls[call.id] = call
        elif typ == "user":
            content = (e.get("message") or {}).get("content")
            for block in content if isinstance(content, list) else []:
                if isinstance(block, dict) and block.get("type") == "tool_result" and block.get("tool_use_id") in calls:
                    calls[block["tool_use_id"]].done = True
                    if block.get("is_error") is True:
                        calls[block["tool_use_id"]].ended_abnormally = True
        elif typ == "system" and e.get("subtype") in ("task_started", "task_notification", "task_updated"):
            # Claude reports every tool task (foreground ones too). A task is open only once backgrounded,
            # and closes on a terminal status; updates and some notifications carry only the task id.
            sub, patch = e.get("subtype"), e.get("patch") if isinstance(e.get("patch"), dict) else {}
            if sub == "task_started" and e.get("task_id") and e.get("tool_use_id"):
                task_calls[str(e["task_id"])] = str(e["tool_use_id"])
            call = calls.get(e.get("tool_use_id") or task_calls.get(str(e.get("task_id"))))
            if call is None:
                pass
            elif (status := e.get("status") if sub == "task_notification" else patch.get("status")) in TASK_DONE:
                call.background_open, call.background_closed = False, True
                call.ended_abnormally = call.ended_abnormally or status != "completed"
            elif e.get("is_backgrounded") is True or patch.get("is_backgrounded") is True:
                call.background_open = True
        elif typ in ("item.started", "item.completed"):
            item = e.get("item") or {}
            if (call := _codex_call(item)) is not None:
                existing = calls.setdefault(call.id, call)
                if typ == "item.completed":
                    existing.done = True
        if typ in ("result", "turn.completed", "turn.failed", "error") and not e.get("parent_tool_use_id"):
            # A subagent's own result never decides the coordinator turn; the last top-level terminal does.
            # An empty, reason-less result is an internal restart artifact: it never overrides a real terminal.
            artifact = typ == "result" and not e.get("result") and e.get("terminal_reason") is None
            if not (artifact and terminal is not None):
                terminal, terminal_index = e, idx
    for call in calls.values():
        # A subagent's calls are settled by its parent call (results inside a subagent are not always streamed),
        # but only when the parent truly finished: a background subagent's acknowledgement settles nothing.
        parent = calls.get(call.parent) if call.parent else None
        if parent is not None and not parent.pending and not parent.ended_abnormally:
            call.done = True
    report.calls = list(calls.values())
    if terminal is None:
        return no_terminal_evidence(report, turn_dir, diagnostics)
    report.terminal = True
    typ = terminal.get("type")
    if typ == "result":
        if terminal.get("is_error") is False and terminal.get("terminal_reason") == "completed":
            report.outcome, report.detail = "success", "result ok"
        elif terminal.get("is_error") is not True:
            # Missing/null is_error, or an empty result without a completed reason, is not evidence of success.
            report.outcome, report.detail = "unknown", f"result without completion (reason={terminal.get('terminal_reason')})"
        else:
            text = str(terminal.get("result") or terminal.get("terminal_reason") or "")
            status = terminal.get("api_error_status")
            report.outcome = classify_text(text, status if isinstance(status, int) else None)
            report.detail = f"{terminal.get('terminal_reason') or 'error'} status={status}"
            settle_limit(report, text, ref, local_tz)
    elif typ == "turn.completed":
        report.outcome, report.detail = "success", "turn.completed"
    else:
        # Codex reports failure as `error` then `turn.failed`; take the latest message.
        text = str(terminal.get("message") or (terminal.get("error") or {}).get("message") or "")
        for e in events[terminal_index::-1]:
            if e.get("type") == "turn.completed":
                break
            if e.get("type") in ("error", "turn.failed"):
                text = str(e.get("message") or (e.get("error") or {}).get("message") or text)
                break
        report.outcome = classify_text(text, None)
        report.detail = f"codex {typ}"
        settle_limit(report, text, ref, local_tz)
    return report


def same_output_as_previous_turn(turn_dir: Path) -> bool:
    number = turn_dir.name.split("-")[-1]
    if not number.isdigit() or int(number) <= 1:
        return False
    previous = turn_dir.with_name(f"turn-{int(number) - 1:0{len(number)}d}") / "output.jsonl"
    current = turn_dir / "output.jsonl"
    try:
        if previous.stat().st_size != current.stat().st_size:
            return False
        return hashlib.sha256(previous.read_bytes()).digest() == hashlib.sha256(current.read_bytes()).digest()
    except OSError:
        return False


def no_terminal_evidence(report: TurnReport, turn_dir: Path, diagnostics: str) -> TurnReport:
    """Without a terminal event, an authentication diagnostic (runner stderr/run JSON, or a turn stderr.log)
    makes the turn `auth` (held), never a retryable crash. Nothing here can ever yield success."""
    texts = [diagnostics]
    try:
        texts.append((turn_dir / "stderr.log").read_text(encoding="utf-8", errors="replace")[-8192:])
    except OSError:
        pass
    text = "\n".join(t for t in texts if t)
    if text and classify_text(text, None) == "auth":
        report.outcome, report.detail = "auth", f"{report.detail}; runner reported an authentication failure"
    return report


def settle_limit(report: TurnReport, text: str, ref: datetime, local_tz: Any) -> None:
    """Attach the provider-printed reset. A spend-limit message that also prints a timed reset (Claude's
    "monthly spend limit · your session limit resets 4pm") is a session quota with that reset."""
    if report.outcome not in ("quota", "spend_limit"):
        return
    reset = parse_reset(text, ref, local_tz)
    report.reset_at = iso(reset)
    report.spend_cap = report.outcome == "spend_limit"
    if report.spend_cap and reset is not None and reset <= ref:
        # The cap is still reported after the session reset it prints: this turn alone shows a real spend cap.
        report.detail += " (spend cap outlived its printed session reset)"
        return
    if report.outcome == "spend_limit" and reset is not None:
        report.outcome = "quota"
        report.detail += " (spend cap with timed session reset)"


def gate(report: TurnReport, *, fingerprint_changed: bool | None) -> str | None:
    """Hold reason when automatic continuation could duplicate a non-idempotent operation."""
    if report.bad_lines:
        return "output_unparseable"
    if report.no_evidence:
        return "output_missing"
    if report.in_flight:
        return "effects_uncertain"
    if not report.terminal and fingerprint_changed:
        # The stream ended early and the repository moved: recorded calls may not explain the change.
        return "effects_uncertain"
    return None


def last_turn_dir(session_dir: Path) -> Path | None:
    turns = sorted((p for p in (session_dir / "turns").glob("turn-*") if p.is_dir()),
                   key=lambda p: int(p.name.split("-")[-1]) if p.name.split("-")[-1].isdigit() else -1)
    return turns[-1] if turns else None


# ---------------------------------------------------------------------------
# Durable state


class StateCorrupt(Exception):
    pass


def default_state() -> dict[str, Any]:
    return {
        "schema": SCHEMA, "phase": "idle", "head_session": None, "chain": [], "agent": None,
        "hold": None, "cooldowns": {}, "switches": [], "last_switch_at": None,
        "counters": {"consecutive_failures": 0, "transient_streak": 0, "crash_retries": 0},
        "permissions_digest": None, "permissions_pinned": False, "pending": None, "waiting_since": None, "last_outcome": None,
        "notify": {"sent": {}, "window": [], "last_digest": None, "failures": 0, "retry": None, "dropped": 0},
        "watch": {"seen": {}, "master": None}, "acknowledged": None, "spend_caps": {}, "updated_at": None,
    }


STATE_TYPES: dict[str, tuple[type, ...]] = {
    "head_session": (str, type(None)), "chain": (list,), "agent": (str, type(None)), "hold": (dict, type(None)),
    "cooldowns": (dict,), "switches": (list,), "last_switch_at": (str, type(None)), "counters": (dict,),
    "permissions_digest": (str, type(None)), "permissions_pinned": (bool,), "pending": (dict, type(None)),
    "waiting_since": (str, type(None)), "last_outcome": (str, type(None)), "notify": (dict,), "watch": (dict,),
    "acknowledged": (dict, type(None)), "spend_caps": (dict,), "updated_at": (str, type(None)),
}
PENDING_KEYS = ("nonce", "agent", "parent", "started_at", "pid", "pid_start", "fingerprint", "attempt")


GATE_HOLDS = ("effects_uncertain", "output_unparseable", "output_missing")
FAILURE_HOLDS = ("auth_failure", "unknown_failure")


def waivers(ack: dict[str, Any] | None) -> frozenset[str]:
    """What the maintainer's releases of a held turn reviewed, and so may waive when that turn is continued."""
    reasons = set((ack or {}).get("reasons") or [])
    return frozenset(({"gate"} if reasons & set(GATE_HOLDS) else set()) | ({"failure"} if reasons & set(FAILURE_HOLDS) else set()))


def validate_state(data: dict[str, Any]) -> str | None:
    for key, types in STATE_TYPES.items():
        if key not in data:
            return f"missing {key}"
        if not isinstance(data[key], types):
            return f"bad type for {key}"
    if not all(isinstance(data["counters"].get(k), int) for k in ("consecutive_failures", "transient_streak", "crash_retries")):
        return "bad counters"
    pending = data["pending"]
    if pending is not None and (any(k not in pending for k in PENDING_KEYS) or not isinstance(pending["nonce"], str)):
        return "bad pending attempt"
    return None


def unsettled_nonces(journal: Path) -> list[str]:
    """Launched attempts with no settle record and not dropped by a maintainer release, oldest first."""
    launched: dict[str, None] = {}
    try:
        lines = journal.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    for line in lines:
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue  # a torn final line is the only kind a crash can leave; the state's pending covers it
        if not isinstance(record, dict):
            continue
        if record.get("event") == "launch" and isinstance(record.get("nonce"), str):
            launched[record["nonce"]] = None
        elif record.get("event") == "settle":
            launched.pop(record.get("nonce"), None)
        elif record.get("event") == "release":
            for nonce in record.get("dropped") or []:
                launched.pop(nonce, None)
    return list(launched)


class Store:
    def __init__(self, root: Path):
        self.root = root
        self.state_path = root / "state.json"
        self.journal_path = root / "attempts.jsonl"
        self.stop_path = root / "STOP"

    def load(self) -> dict[str, Any]:
        if not self.state_path.exists():
            return default_state()
        try:
            data = json.loads(self.state_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise StateCorrupt(f"state file unreadable: {type(exc).__name__}") from exc
        if not isinstance(data, dict) or data.get("schema") != SCHEMA or data.get("phase") not in PHASES:
            raise StateCorrupt("state file has an unknown schema or phase")
        if problem := validate_state(data):
            raise StateCorrupt(f"state file is structurally invalid: {problem}")
        return data

    def save(self, state: dict[str, Any], now: datetime) -> None:
        state["updated_at"] = iso(now)
        self.root.mkdir(parents=True, exist_ok=True)
        tmp = self.state_path.with_name(f".state.{os.getpid()}.tmp")
        with open(tmp, "w", encoding="utf-8") as handle:
            json.dump(state, handle, indent=1, sort_keys=True)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, self.state_path)
        dir_fd = os.open(self.root, os.O_RDONLY)
        try:
            os.fsync(dir_fd)
        finally:
            os.close(dir_fd)

    def journal(self, record: dict[str, Any]) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        with open(self.journal_path, "a", encoding="utf-8") as handle:
            fcntl.flock(handle, fcntl.LOCK_EX)
            handle.write(json.dumps(record, sort_keys=True) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
            fcntl.flock(handle, fcntl.LOCK_UN)


class Lock:
    """Exclusive non-blocking flock; released by the kernel if the holder dies."""

    def __init__(self, path: Path):
        self.path = path
        self.handle: Any = None

    def acquire(self) -> bool:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.handle = open(self.path, "a+")
        try:
            fcntl.flock(self.handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            self.handle.close()
            self.handle = None
            return False
        self.handle.seek(0)
        self.handle.truncate()
        self.handle.write(str(os.getpid()))
        self.handle.flush()
        return True

    def release(self) -> None:
        if self.handle:
            fcntl.flock(self.handle, fcntl.LOCK_UN)
            self.handle.close()
            self.handle = None


# ---------------------------------------------------------------------------
# Outbound notification (Phase 2): fixed templates, allowlisted structured fields only

ISO_RE = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$"
FIELD_RULES: dict[str, Callable[[str], bool]] = {
    "session": lambda v: v == "none" or bool(re.fullmatch(r"\d{8}-\d{6}-[0-9a-f]{6}", v)),
    "agent": lambda v: v in AGENTS,
    "from_agent": lambda v: v in AGENTS,
    "outcome": lambda v: v in OUTCOMES,
    "action": lambda v: v in ("switch", "retry", "wait", "hold", "idle", "notify"),
    "reason": lambda v: v in HOLD_REASONS + STOP_REASONS,
    "reset_at": lambda v: v in ("none", "manual") or bool(re.fullmatch(ISO_RE, v)),
    "next_check_at": lambda v: bool(re.fullmatch(ISO_RE, v)),
    "claude_until": lambda v: v in ("none", "manual") or bool(re.fullmatch(ISO_RE, v)),
    "codex_until": lambda v: v in ("none", "manual") or bool(re.fullmatch(ISO_RE, v)),
    "reset_source": lambda v: v in ("limits", "message", "estimate", "manual"),
    "attempt": lambda v: bool(re.fullmatch(r"\d{1,4}", v)),
    "attempts": lambda v: bool(re.fullmatch(r"\d{1,6}", v)),
    "holds": lambda v: bool(re.fullmatch(r"\d{1,6}", v)),
    "sha": lambda v: bool(re.fullmatch(r"[0-9a-f]{7,40}", v)),
    "pr": lambda v: v == "none" or bool(re.fullmatch(r"\d{1,6}", v)),
    "phase": lambda v: v in PHASES,
}
OPTIONAL_FIELDS = ("reset_at", "claude_until", "codex_until", "pr")
EVENTS: dict[str, tuple[str, tuple[str, ...]]] = {
    "supervisor_started": (":large_green_circle: JarvisOS continuity supervisor started", ("session", "agent")),
    "supervisor_stopped": (":white_circle: JarvisOS continuity supervisor stopped", ("session", "reason", "phase")),
    "provider_switched": (":repeat: JarvisOS coordinator provider switched", ("session", "from_agent", "agent", "outcome")),
    "provider_exhausted": (":large_orange_circle: JarvisOS provider limit", ("agent", "outcome", "reset_at", "reset_source")),
    "all_exhausted": (":large_orange_circle: JarvisOS: no coordinator provider available; waiting", ("next_check_at",)),
    "turn_failed": (":large_orange_circle: JarvisOS coordinator turn failed", ("session", "agent", "outcome", "action")),
    "hold": (":red_circle: JarvisOS continuity HOLD: maintainer review needed", ("session", "reason", "attempt")),
    "circuit_open": (":red_circle: JarvisOS continuity circuit open", ("session", "reason")),
    "turn_completed": (":large_green_circle: JarvisOS coordinator turn completed; awaiting maintainer", ("session", "agent")),
    "master_advanced": (":large_green_circle: JarvisOS master advanced", ("sha", "pr")),
    "repl_turn_failed": (":large_orange_circle: JarvisOS REPL turn failed (notify-only)", ("session", "agent", "outcome", "reset_at")),
    "digest": (":clipboard: JarvisOS continuity digest", ("phase", "session", "agent", "attempts", "holds", "claude_until", "codex_until")),
    "test": (":white_check_mark: JarvisOS continuity notification test", ()),
}


def render(event: str, fields: dict[str, Any]) -> str | None:
    """Fixed template text, or None when any field is missing, unexpected or fails its validator."""
    if event not in EVENTS:
        return None
    title, allowed = EVENTS[event]
    if set(fields) - set(allowed):
        return None
    lines = [f"*{title}*"]
    for key in allowed:
        value = fields.get(key)
        if value is None and key in OPTIONAL_FIELDS:
            value = "none"
        if value is None:
            return None
        value = str(value)
        if not FIELD_RULES[key](value):
            return None
        lines.append(f"{key.replace('_', ' ')}: {value}")
    text = "\n".join(lines)
    return None if devctx.find_secret(text) else text


class _RejectRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001, ANN201 - stdlib signature
        raise urllib.error.HTTPError(req.full_url, code, "redirect rejected", headers, fp)


# Proxies disabled and redirects rejected: the webhook body only ever reaches hooks.slack.com directly.
_WEBHOOK_OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}), _RejectRedirects())


def _valid_webhook_url(url: str) -> bool:
    try:
        parts = urllib.parse.urlsplit(url)
        port = parts.port
    except ValueError:
        return False
    return (parts.scheme == "https" and parts.hostname == "hooks.slack.com" and port is None
            and parts.username is None and parts.password is None and parts.path.startswith("/services/")
            and not parts.query and not parts.fragment)


def post_webhook(text: str, *, webhook_file: Path = WEBHOOK_FILE, timeout: float = 10.0) -> str | None:
    """POST to the incoming webhook. Returns None on success, else an error class (never the URL)."""
    try:
        url = webhook_file.read_text().strip()
    except OSError:
        return "webhook_missing"
    if not _valid_webhook_url(url):
        return "webhook_invalid"
    request = urllib.request.Request(url, data=json.dumps({"text": text}).encode(), method="POST",
                                     headers={"Content-Type": "application/json"})
    try:
        with _WEBHOOK_OPENER.open(request, timeout=timeout) as response:
            response.read(256)
        return None
    except urllib.error.HTTPError as exc:
        return f"http_{exc.code}"
    except Exception as exc:  # noqa: BLE001 - delivery must never raise into the supervisor
        return type(exc).__name__


class Notifier:
    def __init__(self, state: dict[str, Any], *, sender: Callable[[str], str | None] | None,
                 log: Callable[[str], None], max_per_hour: int = 12,
                 dedupe: timedelta = timedelta(hours=6)):
        self.state = state
        self.sender = sender
        self.log = log
        self.max_per_hour = max_per_hour
        self.dedupe = dedupe

    def send(self, event: str, now: datetime, *, dedupe_key: str | None = None, **fields: Any) -> bool:
        if self.sender is None:
            return False
        notify = self.state["notify"]
        text = render(event, fields)
        if text is None:
            notify["dropped"] = notify.get("dropped", 0) + 1
            self.log(f"notify: dropped {event} (field validation)")
            return False
        key = hashlib.sha256((dedupe_key or f"{event}|{json.dumps(fields, sort_keys=True)}").encode()).hexdigest()[:20]
        last = parse_ts(notify["sent"].get(key))
        if last and now - last < self.dedupe:
            return False
        window = [t for t in notify["window"] if (ts := parse_ts(t)) and now - ts < timedelta(hours=1)]
        if len(window) >= self.max_per_hour:
            notify["window"] = window
            notify["dropped"] = notify.get("dropped", 0) + 1
            self.log(f"notify: rate-limited {event}")
            return False
        error = self._deliver(text)
        if error:
            notify["failures"] = notify.get("failures", 0) + 1
            notify["retry"] = {"event": event, "fields": fields, "key": key} if notify.get("retry") is None else notify["retry"]
            self.log(f"notify: delivery failed ({error})")
            return False
        window.append(iso(now))
        notify["window"] = window
        notify["sent"][key] = iso(now)
        notify["sent"] = {k: v for k, v in notify["sent"].items() if (ts := parse_ts(v)) and now - ts < timedelta(days=8)}
        return True

    def retry_pending(self, now: datetime) -> None:
        notify = self.state["notify"]
        pending = notify.get("retry")
        if not pending or self.sender is None:
            return
        notify["retry"] = None  # at most one retry; dropped afterwards whatever happens
        window = [t for t in notify["window"] if (ts := parse_ts(t)) and now - ts < timedelta(hours=1)]
        if len(window) >= self.max_per_hour:
            notify["window"] = window
            notify["dropped"] = notify.get("dropped", 0) + 1
            self.log(f"notify: rate-limited retry of {pending['event']}")
            return
        text = render(pending["event"], pending["fields"])
        if text and not self._deliver(text):
            notify["sent"][pending["key"]] = iso(now)
            notify["window"] = window + [iso(now)]

    def _deliver(self, text: str) -> str | None:
        try:
            return self.sender(text) if self.sender else "no_sender"
        except Exception as exc:  # noqa: BLE001
            return type(exc).__name__


# ---------------------------------------------------------------------------
# Relay and host adapters (injectable for tests)


@dataclass
class RunResult:
    session_id: str | None
    exit_code: int | None
    raw_ok: bool
    diagnostics: str = ""


class RelayAdapter:
    def __init__(self, repo: Path, binary: str = "agent-relay"):
        self.repo = repo
        self.binary = binary

    def limits(self) -> dict[str, Any] | None:
        try:
            proc = subprocess.run([self.binary, "--json", "limits", "--refresh"], capture_output=True, text=True,
                                  timeout=90, check=False, cwd="/tmp")
            data = json.loads(proc.stdout)
        except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError):
            return None
        return {a.get("agent_key"): a for a in data.get("agents", []) if isinstance(a, dict)}

    def start(self, agent: str, parent: str, task: str, turns: int) -> subprocess.Popen:
        args = [self.binary, "--json", "run", agent, "--continue", parent, "-t", task, "-n", str(turns), "-y",
                "--repo", str(self.repo)]
        return subprocess.Popen(args, cwd=self.repo, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                                start_new_session=True)

    @staticmethod
    def finish(proc: subprocess.Popen) -> RunResult:
        out, err = proc.communicate()
        diagnostics = (err or "")[-8192:]
        try:
            data = json.loads(out)
            errors = [str(data.get(k)) for k in ("run_error", "error", "stop_reason") if data.get(k)]
            return RunResult(data.get("session_id"), proc.returncode, True, "\n".join([diagnostics, *errors]))
        except (json.JSONDecodeError, TypeError, AttributeError):
            return RunResult(None, proc.returncode, False, diagnostics)

    def sessions_dir(self) -> Path:
        return self.repo / ".agent-relay" / "sessions"

    def find_by_nonce(self, nonce: str, since: datetime) -> str | None:
        root = self.sessions_dir()
        floor = (since - timedelta(minutes=2)).strftime("%Y%m%d-%H%M%S")
        marker = re.compile(r"\[relay-continuity attempt (rc-[0-9TZ]+-[0-9a-f]+)\]")
        found = []
        for session in sorted(root.glob("*-*-*"), reverse=True):
            if session.name[:15] < floor:
                break
            prompt = session / "turns" / "turn-001" / "prompt.md"
            try:
                own = task_marker(prompt.read_text(encoding="utf-8", errors="replace"), marker)
            except OSError:
                continue
            # Only the marker that opens the session's own task counts; a prompt quoting a nonce does not.
            if own == nonce:
                found.append(session.name)
        return found[0] if len(found) == 1 else None


def task_marker(prompt: str, marker: re.Pattern[str]) -> str | None:
    """Nonce of the attempt marker that is the first line of the prompt's `## Task` section, if any."""
    head, sep, rest = prompt.partition("\n## Task\n")
    if not sep:
        return None
    first = next((line for line in rest.splitlines() if line.strip()), "")
    match = marker.fullmatch(first.strip())
    return match.group(1) if match else None


def fingerprint(repo: Path) -> str:
    digest = hashlib.sha256()
    for args in (["for-each-ref", "--format=%(refname) %(objectname)"], ["worktree", "list", "--porcelain"]):
        digest.update((devctx.run(["git", *args], cwd=repo)[1] or "").encode())
    for line in (devctx.run(["git", "worktree", "list", "--porcelain"], cwd=repo)[1] or "").splitlines():
        if line.startswith("worktree ") and Path(line[9:]).is_dir():
            digest.update(line.encode())
            digest.update((devctx.run(["git", "status", "--porcelain=v1"], cwd=Path(line[9:]))[1] or "").encode())
    return digest.hexdigest()


def live_conflicts(repo: Path, own_pids: set[int]) -> list[str]:
    """Reasons another coordinator/supervisor may be acting: legacy autopilot or a live Relay REPL/run."""
    found = []
    proc_root = Path("/proc")
    for entry in proc_root.iterdir() if proc_root.exists() else []:
        if not entry.name.isdigit() or int(entry.name) in own_pids:
            continue
        try:
            argv = [a.decode(errors="replace") for a in (entry / "cmdline").read_bytes().split(b"\0") if a]
            cwd = os.readlink(entry / "cwd")
        except OSError:
            continue
        joined = " ".join(argv)
        if any(marker in joined for marker in LEGACY_MARKERS):
            found.append("legacy_autopilot")
        elif argv and Path(argv[0]).name in ("relay", "agent-relay") and "daemon" not in argv[1:3] \
                and "hook" not in argv[1:3] and Path(cwd).resolve() == repo.resolve():
            found.append("repl_active")
    return sorted(set(found))


INTERACTIVE_SHELLS = {"bash", "-bash", "sh", "-sh", "zsh", "-zsh", "fish", "-fish", "dash"}
MULTIPLEXER_SERVERS = {"tmux", "screen", "SCREEN"}
CONTAINER_SHIMS = ("containerd-shim", "conmon")  # one per running container, whatever its daemon's state


def _multiplexer(name: str) -> bool:
    """tmux/screen under any title: `tmux`, or the server's rewritten `tmux: server`."""
    return name in MULTIPLEXER_SERVERS or name.startswith(("tmux:", "tmux "))
DAEMON_UNREACHABLE = ("cannot connect to the docker daemon", "is the docker daemon running", "unable to connect to podman",
                      "cannot connect to podman", "no such file or directory")


@dataclass(frozen=True)
class Work:
    """Something running that may belong to this chain. `identity` is what a maintainer release acknowledges
    (None: an inspection failure, never acknowledgeable). `recent`: started inside the chain window.
    `inherited`: may run work newer than its own start (a multiplexer pane's program, a container with exec
    sessions), so it counts unless this exact identity was acknowledged."""
    identity: str | None
    label: str
    recent: bool = True
    inherited: bool = False


def inspection_failed(label: str) -> Work:
    return Work(None, label)


def worktree_roots(repo: Path) -> list[Path]:
    code, out = devctx.run(["git", "worktree", "list", "--porcelain"], cwd=repo)
    if code != 0:
        raise RuntimeError("git worktree list failed")  # partial coverage would read as "no live work"
    return [repo] + [Path(line[9:]) for line in out.splitlines() if line.startswith("worktree ")]


def _ancestors(pid: int, proc_root: Path) -> set[int]:
    seen: set[int] = set()
    while pid > 1 and pid not in seen:
        seen.add(pid)
        try:
            status = (proc_root / str(pid) / "status").read_text()
            pid = int(next(line.split()[1] for line in status.splitlines() if line.startswith("PPid:")))
        except (OSError, ValueError, StopIteration):
            break
    return seen


def _argv(entry: Path) -> list[str]:
    return [a.decode(errors="replace") for a in (entry / "cmdline").read_bytes().split(b"\0") if a]


def _ignorable(argv: list[str], entry: Path) -> bool:
    """Processes that do no work themselves: their children are checked on their own."""
    if not argv:
        return False
    name = Path(argv[0]).name
    if name in INTERACTIVE_SHELLS and all(a in ("-l", "-i", "--login", "--interactive") for a in argv[1:]):
        try:  # an idle prompt reads a terminal; a shell fed a script on stdin or a pipe is working
            return os.readlink(entry / "fd" / "0").startswith(("/dev/pts/", "/dev/tty"))
        except OSError:
            return False
    if _multiplexer(name):
        return True
    if name in ("relay", "agent-relay") and any(a in ("daemon", "hook") for a in argv[1:3]):
        return True
    # this supervisor or its notify-only watch
    return name.startswith("python") and len(argv) > 2 and Path(argv[1]).name == "relay_continuity.py" \
        and argv[2] in ("run", "watch")


def live_processes(roots: list[Path], since: datetime, own_pids: set[int], *,
                   proc_root: Path = Path("/proc")) -> list[Work]:
    """This user's live processes working in the repository or a worktree.

    Detached work (a `&` job, tmux/screen, nohup, a daemon) outlives the tool call that launched it, and no
    shell classifier can recognize every way to start it. This check looks at what is actually running instead.
    A process that vanishes while being read is gone; one that cannot be read is assumed to be working.
    """
    try:
        btime = int(next(line.split()[1] for line in (proc_root / "stat").read_text().splitlines()
                         if line.startswith("btime ")))
    except (OSError, ValueError, StopIteration):
        return [inspection_failed("process table unreadable")]
    ticks, uid = os.sysconf("SC_CLK_TCK"), os.getuid()
    exclude: set[int] = set()
    for pid in own_pids:
        exclude |= _ancestors(pid, proc_root)
    resolved = [r.resolve() for r in roots]
    found: dict[str | None, Work] = {}
    for entry in proc_root.iterdir():
        if not entry.name.isdigit() or int(entry.name) in exclude:
            continue
        try:
            if entry.stat().st_uid != uid:
                continue  # another user's process cannot be this chain's work
            stat = (entry / "stat").read_text()
            fields = stat.rsplit(")", 1)[1].split()
            if fields[0] in ("Z", "X"):
                continue
            started = datetime.fromtimestamp(btime + int(fields[19]) / ticks, UTC)
        except (FileNotFoundError, ProcessLookupError):
            continue
        except (OSError, ValueError, IndexError):
            found[None] = inspection_failed("process unreadable")
            continue
        try:
            cwd = Path(os.readlink(entry / "cwd")).resolve()
            if not any(cwd == r or r in cwd.parents for r in resolved):
                continue
            argv = _argv(entry)
            if _ignorable(argv, entry):
                continue
            try:
                parent = [*_argv(proc_root / fields[1])[:1], (proc_root / fields[1] / "comm").read_text().strip()]
            except OSError:
                parent = []
        except (FileNotFoundError, ProcessLookupError):
            continue
        except OSError:
            # Its working directory cannot be read (a non-dumpable process such as `(sd-pam)`): it might be in a
            # checkout. Its start time is known, so it is judged like any process and a release can acknowledge it.
            unreadable = f"proc:{entry.name}:{fields[19]}:unreadable"
            found[unreadable] = Work(unreadable, "process unreadable", recent=started >= since)
            continue
        comm = re.sub(r"[^A-Za-z0-9_.:-]", "_", stat[stat.find("(") + 1:stat.rfind(")")])[:32]
        identity = f"proc:{entry.name}:{fields[19]}:{hashlib.sha256(chr(0).join(argv).encode()).hexdigest()[:16]}"
        pane = any(_multiplexer(Path(name).name) or _multiplexer(name) for name in parent)
        found[identity] = Work(identity, f"process {comm}", recent=started >= since, inherited=pane)  # names only
    return sorted(found.values(), key=lambda w: (w.label, w.identity or ""))


def _container_ts(value: str) -> datetime | None:
    match = re.fullmatch(r"(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d)(?:\.(\d+))?(Z|[+-]\d\d:\d\d)", value.strip())
    if not match:
        return None
    frac = (match.group(2) or "0")[:6].ljust(6, "0")
    zone = "+00:00" if match.group(3) == "Z" else match.group(3)
    return parse_ts(f"{match.group(1)}.{frac}{zone}")


def container_shims(proc_root: Path = Path("/proc")) -> bool:
    """Whether any container runtime shim is running (readable for every user's processes)."""
    for entry in proc_root.iterdir() if proc_root.exists() else []:
        if entry.name.isdigit():
            try:
                if (entry / "comm").read_text().strip().startswith(CONTAINER_SHIMS):
                    return True
            except OSError:
                continue
    return False


def live_containers(since: datetime, *, run: Callable[..., subprocess.CompletedProcess] = subprocess.run,
                    shims: Callable[[], bool] = container_shims) -> list[Work]:
    """Running docker/podman containers; they may bind-mount a checkout. An unreachable daemon proves nothing
    (live restore keeps containers running), so it is clear only when no container shim runs; any other failure
    to list or date them counts as live work."""
    found: list[Work] = []
    for tool in ("docker", "podman"):
        exe = shutil.which(tool)
        if not exe:
            continue
        try:
            listed = run([exe, "ps", "-q", "--no-trunc"], capture_output=True, text=True, timeout=15)
            if listed.returncode != 0:
                if not any(m in (listed.stderr or "").lower() for m in DAEMON_UNREACHABLE) or shims():
                    found.append(inspection_failed(f"{tool} check failed"))
                continue
            ids = listed.stdout.split()
            if not ids:
                continue
            inspected = run([exe, "inspect", "--format", "{{.Id}} {{.State.StartedAt}} {{json .ExecIDs}}", *ids],
                            capture_output=True, text=True, timeout=15)
        except subprocess.TimeoutExpired:
            found.append(inspection_failed(f"{tool} check timed out"))
            continue
        except OSError:
            found.append(inspection_failed(f"{tool} check failed"))
            continue
        if inspected.returncode != 0:
            found.append(inspection_failed(f"{tool} check failed"))
            continue
        for line in inspected.stdout.splitlines():
            parts = line.split(" ", 2)
            ts = _container_ts(parts[1]) if len(parts) > 1 else None
            try:
                execs = sorted(json.loads(parts[2]) or []) if len(parts) > 2 else []
            except ValueError:
                execs = ["?"]
            if ts is None:
                found.append(inspection_failed(f"{tool} container undatable"))
                continue
            identity = f"ctr:{parts[0]}:{parts[1]}:{hashlib.sha256(','.join(execs).encode()).hexdigest()[:16]}"
            # `docker exec` starts work without restarting the container: exec sessions keep it counted.
            found.append(Work(identity, f"{tool} container {parts[0][:12]}", recent=ts >= since, inherited=bool(execs)))
    return found


# ---------------------------------------------------------------------------
# Supervisor

RECOVERY_PROMPT = """[relay-continuity attempt {nonce}]
Automatic continuation by the spec 195 continuity supervisor. The previous coordinator turn ({prev_agent}) ended with outcome `{outcome}`; you are now running as {agent}.
This message is not a new maintainer instruction and grants no new authority: approval gates, review requirements and authority boundaries are exactly as before.
Before acting, run `python3 scripts/devctx.py recover` and verify fresh Git/GitHub state, then continue the interrupted work from where it actually stands.
Operations the interrupted turn completed (they already happened; verify their effect, do not repeat them blindly):
{effects}
If the work now needs a maintainer decision, stop and report instead of continuing."""


@dataclass
class Host:
    relay: Any
    now: Callable[[], datetime] = now_utc
    sleep: Callable[[float], None] = time.sleep
    fingerprint: Callable[[], str] = lambda: ""
    conflicts: Callable[[set[int]], list[str]] = lambda own: []
    pid_alive: Callable[[int, int | None], bool] = lambda pid, start: devctx.pid_start(pid) == start and start is not None
    ledger: Callable[[str, str], None] = lambda kind, text: None
    permissions_digest: Callable[[], str | None] = lambda: None
    log: Callable[[str], None] = lambda msg: print(msg, file=sys.stderr, flush=True)
    live_work: Callable[[datetime], list[Any]] = lambda since: []


class Supervisor:
    def __init__(self, store: Store, host: Host, limits: Limits | None = None, *, turns: int = 1,
                 sender: Callable[[str], str | None] | None = None):
        self.store = store
        self.host = host
        self.limits = limits or Limits()
        self.turns = turns
        self.sender = sender
        self.state: dict[str, Any] = default_state()
        self.notifier = Notifier(self.state, sender=sender, log=host.log)
        self.signalled = False
        self.attempts = 0
        self.deciding: str | None = None
        self._reading: dict[str, Any] | None = None
        self._reading_at: datetime | None = None

    # -- persistence helpers
    def save(self) -> None:
        self.store.save(self.state, self.host.now())

    def notify(self, event: str, **fields: Any) -> None:
        try:
            self.notifier.send(event, self.host.now(), **fields)
        except Exception as exc:  # noqa: BLE001 - notification can never interrupt supervision
            self.host.log(f"notify: internal error {type(exc).__name__}")

    def record(self, kind: str, text: str) -> None:
        try:
            self.host.ledger(kind, text)
        except Exception as exc:  # noqa: BLE001
            self.host.log(f"ledger: append failed {type(exc).__name__}")

    def stop_requested(self) -> bool:
        return self.signalled or self.store.stop_path.exists()

    def hold(self, reason: str, attempt: int | None = None, turn: str | None = None) -> str:
        """Refuse automatic continuation. `turn` names the turn whose evidence the maintainer must review; a
        release acknowledges exactly that turn and nothing later."""
        assert reason in HOLD_REASONS
        turn = turn or self.deciding  # holds raised while deciding a turn (waits, circuits) name that turn
        now = self.host.now()
        self.state["phase"] = "held"
        self.state["hold"] = {"reason": reason, "at": iso(now), "attempt": attempt, "turn": turn}
        self.save()
        self.store.journal({"event": "hold", "at": iso(now), "reason": reason, "session": self.state["head_session"]})
        event = "circuit_open" if reason.startswith("circuit_") else "hold"
        fields = {"session": self.state["head_session"], "reason": reason}
        if event == "hold":
            fields["attempt"] = str(attempt or 0)
        self.notify(event, **fields)
        self.record("blocker", f"relay-continuity HOLD ({reason}) on session {self.state['head_session']}; "
                               f"automatic continuation refused until `relay_continuity.py release`.")
        self.host.log(f"hold: {reason}")
        return "held"

    # -- provider availability
    def reading(self, agent: str) -> dict[str, Any] | None:
        now = self.host.now()
        if self._reading is None or self._reading_at is None or now - self._reading_at > timedelta(minutes=2):
            self._reading = self.host.relay.limits() or {}
            self._reading_at = now
        entry = self._reading.get(agent)
        if not isinstance(entry, dict) or entry.get("status") not in (None, "ok"):
            return None
        as_of = parse_ts(entry.get("as_of"))
        if as_of is None or abs(now - as_of) > self.limits.reading_freshness:
            return None
        return entry

    def exhausted_until(self, agent: str) -> datetime | None | bool:
        """Validated reset time when a fresh reading shows the agent out of quota; False when it shows room."""
        entry = self.reading(agent)
        if entry is None:
            return None
        now = self.host.now()
        resets = []
        windows = entry.get("windows")
        if not isinstance(windows, list) or not windows:
            return None  # no usage windows: no evidence either way
        for window in windows:
            used = window.get("used_percent") if isinstance(window, dict) else None
            if isinstance(used, bool) or not isinstance(used, (int, float)):
                return None  # an unusable window is not evidence of room
            reset = parse_ts(window.get("resets_at"))
            if used >= 99.5:
                if reset and now < reset <= now + self.limits.max_reset_ahead:
                    resets.append(reset)
                else:
                    return None  # exhausted but the reset time is stale or implausible: not evidence
        return max(resets) if resets else False

    def available(self, agent: str, *, confirm: bool) -> bool:
        """Whether `agent` may run now. A cooldown ends at its reset. With `confirm` (switching to `agent`) a
        fresh, plausible limits reading must also positively show room: missing, stale or failed readings are
        not evidence, and the unconfirmed agent gets a short recheck cooldown so waits stay bounded."""
        now = self.host.now()
        cooldown = self.state["cooldowns"].get(agent)
        if cooldown:
            until = parse_ts(cooldown.get("until"))
            if until is None or now < until:
                return False
        reading = self.exhausted_until(agent)
        if isinstance(reading, datetime):
            self.state["cooldowns"][agent] = {"until": iso(reading), "source": "limits", "reason": "quota",
                                              "since": iso(now)}
            return False
        if reading is None and confirm:
            self.state["cooldowns"][agent] = {"until": iso(now + self.limits.recheck), "source": "estimate",
                                              "reason": (cooldown or {}).get("reason") or "unconfirmed",
                                              "since": (cooldown or {}).get("since") or iso(now)}
            return False
        if cooldown:
            self.state["cooldowns"].pop(agent, None)
        return True

    def set_cooldown(self, agent: str, report: TurnReport) -> None:
        now = self.host.now()
        existing = self.state["cooldowns"].get(agent)
        if isinstance(existing, dict) and existing.get("until") is None:
            return  # a manual cap stays until `release --clear-cooldown`; no reclassification shortens it
        caps = self.state["spend_caps"]
        earlier = caps.get(agent)
        if report.spend_cap and report.outcome == "quota" and isinstance(earlier, dict) \
                and earlier.get("turn") != report.turn_id:
            # A second turn hit the spend cap after the session reset it printed (no success since): a real cap.
            report.outcome = "spend_limit"
        if report.spend_cap:
            caps[agent] = {"turn": report.turn_id, "at": iso(now)}
        if report.outcome == "spend_limit":
            until, source = None, "manual"
        else:
            reading = self.exhausted_until(agent)
            message = parse_ts(report.reset_at)
            if isinstance(reading, datetime):
                until, source = reading, "limits"
            elif message and now < message <= now + self.limits.max_reset_ahead:
                until, source = message, "message"
            else:
                until, source = now + self.limits.recheck, "estimate"
        self.state["cooldowns"][agent] = {"until": iso(until), "source": source, "reason": report.outcome,
                                          "since": iso(now)}
        self.notify("provider_exhausted", dedupe_key=f"exhausted|{agent}|{iso(until)}", agent=agent,
                    outcome=report.outcome, reset_at=iso(until) or "manual", reset_source=source)
        self.record("finding", f"relay-continuity: {agent} {report.outcome}; cooldown until "
                               f"{iso(until) or 'maintainer release'} (source {source}).")

    # -- main loop
    def run(self, session: str, *, task: str | None = None) -> str:
        now = self.host.now()
        try:
            self.state = self.store.load()
        except StateCorrupt:
            self.host.log("state file corrupt; refusing to act (hold). Inspect and move it aside to reset.")
            Notifier(default_state(), sender=self.sender, log=self.host.log).send(
                "hold", now, session=session, reason="state_corrupt", attempt="0")
            return "held"
        self.notifier = Notifier(self.state, sender=self.sender, log=self.host.log)
        if self.state["phase"] == "held":
            self.host.log(f"chain is held ({self.state['hold']}); run `release` after review")
            return "held"
        head = self.state.get("head_session")
        if self.state.get("pending") and head and head != session:
            self.host.log(f"a launched attempt from chain {head} is unresolved; resume that chain first")
            return "held"
        if head != session and session not in self.state.get("chain", []):
            self.state.update({"head_session": session, "chain": [session], "agent": None, "switches": [],
                               "last_switch_at": None, "waiting_since": None, "last_attempt": None,
                               "counters": {"consecutive_failures": 0, "transient_streak": 0, "crash_retries": 0}})
        if (unsettled := [n for n in unsettled_nonces(self.store.journal_path)
                          if n != (self.state.get("pending") or {}).get("nonce")]):
            # The journal records a launch that the state does not account for: never assume it did not run.
            self.host.log(f"journal has unsettled attempts not in state: {', '.join(unsettled)}")
            return self.hold("attempt_unresolved")
        digest = self.host.permissions_digest()
        if self.state.get("permissions_pinned") and digest != self.state["permissions_digest"]:
            return self.hold("permissions_changed")
        self.state["permissions_digest"] = digest
        self.state["permissions_pinned"] = True
        self.state["phase"] = "running"
        self.save()
        self.notify("supervisor_started", dedupe_key=f"start|{self.state['head_session']}|{iso(now)[:13]}",
                    session=self.state["head_session"], agent=self.state.get("agent") or PREFERRED)
        self.notifier.retry_pending(now)
        try:
            result = self._loop(task)
        finally:
            if self.state["phase"] == "running":
                self.state["phase"] = "stopped"
            self.save()
        reason = {"held": "held", "idle": "idle", "stopped": "stop_requested", "signal": "signal"}.get(result, "error")
        self.notify("supervisor_stopped", dedupe_key=f"stop|{self.state['head_session']}|{result}|{iso(self.host.now())[:13]}",
                    session=self.state["head_session"], reason=reason, phase=self.state["phase"])
        return result

    def _loop(self, task: str | None) -> str:
        report = self._resolve_pending()
        acknowledged: dict[str, Any] | None = None
        if report == "held":
            return "held"
        if report is None:
            turn = last_turn_dir(self.host.relay.sessions_dir() / self.state["head_session"])
            if turn is None:
                self.host.log("head session has no turns")
                return self.hold("attempt_unresolved")
            report = classify_turn(turn)
            report.agent = report.agent or self.state.get("agent")
            ack = self.state.get("acknowledged") or {}
            if ack.get("turn") and ack.get("turn") == report.turn_id:
                acknowledged = ack
        while True:
            if self.stop_requested():
                self.state["phase"] = "stopped"
                return "signal" if self.signalled else "stopped"
            self.state["last_outcome"] = report.outcome
            self.state["agent"] = report.agent or self.state.get("agent") or PREFERRED
            self.deciding = report.turn_id
            decision = self._decide(report, task, waive=waivers(acknowledged), cleared=tuple((acknowledged or {}).get("cleared") or ()))
            acknowledged = None
            if decision in ("held", "idle", "stopped", "signal"):
                return decision
            agent, prompt = decision
            task = None
            new_report = self._launch(agent, prompt, report)
            if isinstance(new_report, str):
                return new_report
            report = new_report

    def _decide(self, report: TurnReport, task: str | None, *, waive: frozenset[str] = frozenset(),
                cleared: tuple[str, ...] = ()) -> tuple[str, str] | str:
        """Next (agent, prompt) or a terminal result. `waive` holds what a maintainer release of this turn
        actually reviewed ("gate": its side-effect evidence; "failure": an auth/unknown failure, retried on the
        same agent). `cleared`: agents whose cooldown the release cleared. Everything else still applies."""
        released = bool(waive or cleared)
        counters = self.state["counters"]
        failed_agent = report.agent or self.state.get("agent") or PREFERRED
        if report.outcome == "success":
            counters.update({"consecutive_failures": 0, "transient_streak": 0, "crash_retries": 0})
            self.state["spend_caps"].pop(failed_agent, None)
            self.state["waiting_since"] = None
            if task is None:
                self.state["phase"] = "idle"
                self.save()
                self.notify("turn_completed", dedupe_key=f"done|{self.state['head_session']}",
                            session=self.state["head_session"], agent=failed_agent)
                return "idle"
            if (held := self._live_work_hold(report)) is not None:
                return held
            agent = self._choose(failed_agent, mode="prefer")
            if agent is None:
                return self._wait_or_hold("prefer", lambda _agent: f"[relay-continuity attempt {{nonce}}]\n{task}")
            return agent, f"[relay-continuity attempt {{nonce}}]\n{task}"

        counters["consecutive_failures"] += 1
        if counters["consecutive_failures"] > self.limits.max_consecutive_failures:
            return self.hold("circuit_failures")
        if self.attempts >= self.limits.max_attempts_per_run:
            return self.hold("circuit_attempts")
        if report.outcome in ("auth", "unknown") and "failure" not in waive:
            self.notify("turn_failed", session=self.state["head_session"], agent=failed_agent,
                        outcome=report.outcome, action="hold")
            return self.hold("auth_failure" if report.outcome == "auth" else "unknown_failure", self.attempts or None,
                             report.turn_id)
        changed = None
        pending_fp = (self.state.get("last_attempt") or {}).get("fingerprint")
        if not report.terminal and pending_fp:
            changed = self.host.fingerprint() != pending_fp
        if "gate" not in waive and (reason := gate(report, fingerprint_changed=changed)) is not None:
            self.notify("turn_failed", session=self.state["head_session"], agent=failed_agent,
                        outcome=report.outcome, action="hold")
            return self.hold(reason, self.attempts or None, report.turn_id)
        if (held := self._live_work_hold(report)) is not None:
            return held

        if report.outcome in ("quota", "spend_limit") and failed_agent in cleared:
            # The maintainer cleared this agent's cap/cooldown on release: the old turn does not reinstate it.
            counters["transient_streak"] = 0
            mode = "same"
            agent = self._choose(failed_agent, mode=mode)
        elif report.outcome in ("quota", "spend_limit"):
            self.set_cooldown(failed_agent, report)
            counters["transient_streak"] = 0
            mode = "switch"
            agent = self._choose(failed_agent, mode=mode)
        elif report.outcome == "transient":
            counters["transient_streak"] += 1
            if counters["transient_streak"] > self.limits.max_transient_streak:
                return self.hold("circuit_transient")
            delay = min(self.limits.transient_base * 2 ** (counters["transient_streak"] - 1), self.limits.transient_cap)
            self.save()
            if self._sleep(delay):
                return "signal" if self.signalled else "stopped"
            mode = "same"
            agent = self._choose(failed_agent, mode=mode)
        elif report.outcome in ("auth", "unknown"):  # released by the maintainer: one same-agent retry
            mode = "same"
            agent = self._choose(failed_agent, mode=mode)
        else:  # crash
            counters["crash_retries"] += 1
            if counters["crash_retries"] > self.limits.crash_retries:
                return self.hold("crash_repeated")
            mode = "same"
            agent = self._choose(failed_agent, mode=mode)
        listed = report.effects + (report.in_flight if "gate" in waive else [])
        effects = "\n".join(f"- [{c.kind}] {c.label}" for c in listed) or "- none recorded"
        if released:
            effects += "\n(The maintainer reviewed and released this turn.)"

        def make_prompt(chosen: str) -> str:
            if released and task is not None:
                return f"[relay-continuity attempt {{nonce}}]\n{task}"
            return RECOVERY_PROMPT.format(nonce="{nonce}", prev_agent=failed_agent, outcome=report.outcome,
                                          agent=chosen, effects=effects)

        if agent is None:
            return self._wait_or_hold(mode, make_prompt)
        action = "switch" if agent != failed_agent else "retry"
        self.notify("turn_failed", session=self.state["head_session"], agent=failed_agent,
                    outcome=report.outcome, action=action)
        return agent, make_prompt(agent)

    def last_release(self) -> tuple[datetime | None, frozenset[str]]:
        """The latest maintainer release in the journal, and the live-work identities it acknowledged."""
        at, acknowledged = None, frozenset()
        try:
            for line in self.store.journal_path.read_text().splitlines():
                record = json.loads(line)
                if record.get("event") == "release" and (ts := parse_ts(record.get("at"))) and (at is None or ts > at):
                    at, acknowledged = ts, frozenset(record.get("acknowledged_work") or [])
        except (OSError, ValueError, AttributeError):
            pass
        return at, acknowledged

    def work_window(self) -> datetime:
        """Start of the period whose launched work may still be running: the chain's first session, or the
        latest maintainer release (which reviewed whatever was live then), whichever is later."""
        starts = []
        for sid in {*(self.state.get("chain") or []), self.state.get("head_session")} - {None}:
            try:
                created = json.loads((self.host.relay.sessions_dir() / sid / "session.json").read_text()).get("created_at")
            except (OSError, ValueError, AttributeError):
                created = None
            starts.append(parse_ts(created) or datetime.min.replace(tzinfo=UTC))  # unknown: the widest window
        since = min(starts) if starts else datetime.min.replace(tzinfo=UTC)
        released, _ = self.last_release()
        return max(since, released) if released else since

    def _live_work_hold(self, report: TurnReport) -> str | None:
        """Hold while work launched in this chain is still running in a checkout: continuing would overlap it."""
        _, acknowledged = self.last_release()
        try:
            works = self.host.live_work(self.work_window())
        except Exception as exc:  # noqa: BLE001 - an unreadable process table is not evidence of no work
            works = [inspection_failed(f"check failed ({type(exc).__name__})")]
        live = [w for w in works if w.identity is None
                or (w.identity not in acknowledged and (w.recent or w.inherited))]
        if not live:
            return None
        self.host.log(f"live work in the checkout: {', '.join(sorted({w.label for w in live})[:10])}")
        self.notify("turn_failed", session=self.state["head_session"], agent=report.agent or self.state.get("agent") or PREFERRED,
                    outcome=report.outcome, action="hold")
        return self.hold("live_work", self.attempts or None, report.turn_id)

    def _choose(self, current: str, *, mode: str) -> str | None:
        """`same`: retry the current agent only (transient, crash). `switch`: another agent only (quota).
        `prefer`: at a turn boundary, the preferred agent first, returning to it only after the dwell time.
        Every switch is bounded and needs fresh confirmation that the target has quota."""
        now = self.host.now()
        last_switch = parse_ts(self.state.get("last_switch_at"))
        dwell_ok = last_switch is None or now - last_switch >= self.limits.min_dwell
        if mode == "same":
            order = [current]
        elif mode == "switch":
            order = [a for a in [PREFERRED] + [a for a in AGENTS if a != PREFERRED] if a != current]
        else:
            order = [PREFERRED] + [a for a in AGENTS if a != PREFERRED]
            if current != PREFERRED and not dwell_ok and self.available(current, confirm=False):
                order = [current]  # too soon after a switch to return; stay while the current agent is usable
        for agent in order:
            if self.available(agent, confirm=agent != current):
                if agent != current:
                    recent = [t for t in self.state["switches"] if (ts := parse_ts(t)) and now - ts < self.limits.switch_window]
                    if len(recent) >= self.limits.max_switches:
                        self.hold("circuit_switches")
                        return None
                    recent.append(iso(now))
                    self.state["switches"] = recent
                    self.state["last_switch_at"] = iso(now)
                    self.notify("provider_switched", session=self.state["head_session"], from_agent=current,
                                agent=agent, outcome=self.state.get("last_outcome") or "success")
                    self.record("decision", f"relay-continuity: switched coordinator {current} -> {agent} "
                                            f"after {self.state.get('last_outcome')} on {self.state['head_session']}.")
                return agent
        return None

    def _wait_or_hold(self, mode: str = "prefer", make_prompt: Callable[[str], str] | None = None
                      ) -> tuple[str, str] | str:
        """No usable agent: sleep to the earliest validated reset that matters (rechecking periodically), bounded.
        `mode` "same" waits for the current agent only. `make_prompt(agent)` builds the eventual prompt, so the
        failed turn's effects record (or the maintainer's task) survives the wait."""
        current = self.state.get("agent") or PREFERRED
        while True:
            if self.state["phase"] == "held":
                return "held"
            now = self.host.now()
            # Only a real reset is worth waiting for; an agent that merely lacks a fresh reading is not one.
            relevant = {a: c for a, c in self.state["cooldowns"].items() if mode != "same" or a == current}
            known = [u for c in relevant.values()
                     if c.get("reason") != "unconfirmed" and (u := parse_ts(c.get("until"))) is not None]
            if not known:
                return self.hold("no_provider_available")
            since = parse_ts(self.state.get("waiting_since")) or now
            self.state["waiting_since"] = iso(since)
            if now - since > self.limits.max_wait:
                return self.hold("wait_exceeded")
            # This is entered only after a choice just failed, so an already-passed reset is not worth an
            # immediate retry: wait for the next future reset, at most one recheck interval.
            future = [u for u in known if u > now]
            wake = min(min(future), now + self.limits.recheck) if future else now + self.limits.recheck
            self.state["phase"] = "waiting"
            self.save()
            self.notify("all_exhausted", dedupe_key=f"all|{iso(min(known))}", next_check_at=iso(wake))
            if self._sleep((wake - now).total_seconds()):
                return "signal" if self.signalled else "stopped"
            self.state["phase"] = "running"
            self._reading = None
            # A same-agent retry stays on that agent; a failover wait takes whichever agent becomes usable.
            agent = self._choose(current, mode="same" if mode == "same" else "prefer")
            if agent is not None:
                self.state["waiting_since"] = None
                if make_prompt is not None:
                    return agent, make_prompt(agent)
                return agent, RECOVERY_PROMPT.format(
                    nonce="{nonce}", prev_agent=current, outcome=self.state.get("last_outcome") or "quota",
                    agent=agent, effects="- see the previous attempt record; nothing new since it was gated")

    def _sleep(self, seconds: float) -> bool:
        """Interruptible sleep in short chunks against the host clock; True when a stop was requested."""
        deadline = self.host.now() + timedelta(seconds=seconds)
        while True:
            if self.stop_requested():
                return True
            remaining = (deadline - self.host.now()).total_seconds()
            if remaining <= 0:
                return False
            self.host.sleep(min(5.0, remaining))

    def _launch(self, agent: str, prompt: str, previous: TurnReport) -> TurnReport | str:
        # Only this process is excluded: a Relay REPL that is our ancestor is still a live coordinator.
        if conflicts := self.host.conflicts({os.getpid()}):
            return self.hold("repl_active" if "repl_active" in conflicts else "attempt_unresolved")
        digest = self.host.permissions_digest()
        if digest != self.state.get("permissions_digest"):
            return self.hold("permissions_changed")
        now = self.host.now()
        self.attempts += 1
        nonce = f"rc-{now.strftime('%Y%m%dT%H%M%SZ')}-{secrets.token_hex(4)}"
        text = prompt.replace("{nonce}", nonce)
        pending = {"nonce": nonce, "agent": agent, "parent": self.state["head_session"], "started_at": iso(now),
                   "pid": None, "pid_start": None, "fingerprint": self.host.fingerprint(), "attempt": self.attempts}
        self.state["pending"] = pending  # intent is durable before anything is launched
        self.state["acknowledged"] = None  # the reviewed turn is now behind the chain
        self.state["agent"] = agent
        self.save()
        self.store.journal({"event": "launch", **{k: v for k, v in pending.items() if k != "fingerprint"}})
        try:
            proc = self.host.relay.start(agent, self.state["head_session"], text, self.turns)
        except OSError:
            # Relay could not be executed at all: nothing started, so the attempt settles as not started.
            self.state["pending"] = None
            self.store.journal({"event": "settle", "nonce": nonce, "session": None, "outcome": "not_started"})
            return self.hold("relay_invocation_failed", self.attempts)
        pending["pid"] = getattr(proc, "pid", None)
        pending["pid_start"] = devctx.pid_start(pending["pid"]) if pending["pid"] else None
        self.save()
        result = self.host.relay.finish(proc)
        return self._settle(pending, result.session_id, result.diagnostics)

    def _settle(self, pending: dict[str, Any], session_id: str | None, diagnostics: str = "") -> TurnReport | str:
        session_id = session_id or self.host.relay.find_by_nonce(pending["nonce"], parse_ts(pending["started_at"]) or self.host.now())
        self.state["last_attempt"] = {k: pending[k] for k in ("nonce", "agent", "attempt", "fingerprint")}
        self.state["pending"] = None
        if session_id is None:
            # Remote effects (a merge, a PR comment) leave no local trace, so an unchanged fingerprint proves
            # nothing: the attempt's outcome is unknown and only the maintainer can resolve it. The hold is
            # saved together with the cleared pending record, and only then is the attempt journalled settled.
            result = self.hold("attempt_unresolved", pending.get("attempt"))
            self.store.journal({"event": "settle", "nonce": pending["nonce"], "session": None, "outcome": "unresolved"})
            return result
        turn = last_turn_dir(self.host.relay.sessions_dir() / session_id)
        report = classify_turn(turn, diagnostics=diagnostics) if turn else TurnReport(
            outcome="crash", agent=pending["agent"], detail="session without turns", no_evidence=True,
            turn_id=f"{session_id}/none")
        report.agent = pending["agent"]
        self.state["head_session"] = session_id
        self.state["chain"] = (self.state.get("chain") or []) + [session_id]
        self.store.journal({"event": "settle", "nonce": pending["nonce"], "session": session_id,
                            "outcome": report.outcome, "agent": report.agent,
                            "effects": [c.label for c in report.effects], "in_flight": [c.label for c in report.in_flight]})
        self.save()
        return report

    def _resolve_pending(self) -> TurnReport | str | None:
        """Restart recovery: settle a launched attempt whose outcome was never recorded."""
        pending = self.state.get("pending")
        if not pending:
            return None
        self.host.log(f"resolving unsettled attempt {pending['nonce']}")
        if pending.get("pid") and self.host.pid_alive(pending["pid"], pending.get("pid_start")):
            self.host.log(f"attempt still running as pid {pending['pid']}; waiting for it (never relaunched)")
            while self.host.pid_alive(pending["pid"], pending.get("pid_start")):
                if self._sleep(30.0):
                    return "signal" if self.signalled else "stopped"
        session_id = self.host.relay.find_by_nonce(pending["nonce"], parse_ts(pending["started_at"]) or self.host.now())
        return self._settle(pending, session_id)


# ---------------------------------------------------------------------------
# Notify-only watch (REPL sessions and integration events)


def watch_once(state: dict[str, Any], notifier: Notifier, repo: Path, now: datetime, *,
               supervised: set[str], master: Callable[[], tuple[str | None, str | None]],
               horizon: timedelta = timedelta(hours=24)) -> None:
    seen = state["watch"]["seen"]
    sessions = repo / ".agent-relay" / "sessions"
    floor = (now - horizon).strftime("%Y%m%d-%H%M%S")
    for session in sorted(sessions.glob("*-*-*")) if sessions.is_dir() else []:
        turn = last_turn_dir(session)
        if turn is None:
            continue
        if session.name in supervised:
            seen[f"{session.name}/{turn.name}"] = "supervised"  # the supervisor reports its own chain
            continue
        try:
            mtime = (turn / "state.json").stat().st_mtime
        except OSError:
            continue  # a turn without state.json is still running
        if datetime.fromtimestamp(mtime, UTC) < now - horizon and session.name < floor:
            continue
        key = f"{session.name}/{turn.name}"
        if seen.get(key):
            continue
        report = classify_turn(turn)
        seen[key] = report.outcome
        if report.outcome != "success" and report.agent in AGENTS:
            notifier.send("repl_turn_failed", now, session=session.name, agent=report.agent,
                          outcome=report.outcome, reset_at=report.reset_at or "none")
    state["watch"]["seen"] = dict(list(seen.items())[-500:])
    sha, pr = master()
    previous = state["watch"].get("master")
    if sha and previous and sha != previous:
        fields = {"sha": sha[:12]}
        if pr:
            fields["pr"] = pr
        notifier.send("master_advanced", now, **fields)
    if sha:
        state["watch"]["master"] = sha


def real_master(repo: Path) -> tuple[str | None, str | None]:
    devctx.run(["git", "fetch", "-q", "origin", "master"], cwd=repo, timeout=60)
    code, sha = devctx.run(["git", "rev-parse", "origin/master"], cwd=repo)
    if code != 0:
        return None, None
    _, subject = devctx.run(["git", "log", "-1", "--format=%s", "origin/master"], cwd=repo)
    match = re.match(r"Merge pull request #(\d+)", subject or "")
    return sha.strip(), match.group(1) if match else None


def digest_fields(state: dict[str, Any], holds: int) -> dict[str, Any]:
    cooldowns = state.get("cooldowns") or {}

    def until(agent: str) -> str:
        cd = cooldowns.get(agent)
        return "none" if not cd else (cd.get("until") or "manual")
    fields: dict[str, Any] = {"phase": state.get("phase") or "idle", "agent": state.get("agent") or PREFERRED,
                              "attempts": str(len(state.get("chain") or [])), "holds": str(holds),
                              "claude_until": until("claude"), "codex_until": until("codex")}
    fields["session"] = state.get("head_session") or "none"
    return fields


# ---------------------------------------------------------------------------
# CLI


def control_root() -> Path:
    return Path(os.environ.get("RELAY_CONTINUITY_DIR", DEFAULT_CONTROL)).expanduser()


def repo_root() -> Path:
    code, out = devctx.run(["git", "rev-parse", "--path-format=absolute", "--git-common-dir"])
    return Path(out.strip()).parent if code == 0 and out.strip() else Path.cwd()


def permissions_digest(path: Path) -> str | None:
    """Digest of the authority-bearing Relay permission settings. Relay rewrites `model` whenever `--model`
    is passed; a model choice grants no authority, so it is excluded. An unreadable file digests as such."""
    if not path.exists():
        return None
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):
        return "unreadable"
    for section in data.values():
        if isinstance(section, dict) and isinstance(section.get("backend"), dict):
            section["backend"].pop("model", None)
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()


def make_host(repo: Path) -> Host:
    env = devctx.default_env(repo)
    author = f"relay-continuity pid {os.getpid()}"

    def ledger(kind: str, text: str) -> None:
        devctx.append_entry(env, devctx.make_entry(env, kind, text, refs={"spec": "195"}, author=author))

    def permissions() -> str | None:
        return permissions_digest(repo / ".agent-relay" / "permissions.toml")

    def live_work(since: datetime) -> list[str]:
        return live_processes(worktree_roots(repo), since, {os.getpid()}) + live_containers(since)

    return Host(relay=RelayAdapter(repo), fingerprint=lambda: fingerprint(repo),
                conflicts=lambda own: live_conflicts(repo, own), ledger=ledger, permissions_digest=permissions,
                live_work=live_work)


def webhook_sender() -> Callable[[str], str | None] | None:
    if not WEBHOOK_FILE.exists():
        return None
    mode = WEBHOOK_FILE.stat().st_mode & 0o077
    if mode:
        print("refusing to use the webhook file: it must not be group/world readable (chmod 600)", file=sys.stderr)
        return None
    return lambda text: post_webhook(text)


def command_run(args: argparse.Namespace) -> int:
    root = control_root()
    lock = Lock(root / "supervisor.lock")
    if not lock.acquire():
        print("another continuity supervisor holds the lock; refusing to start", file=sys.stderr)
        return 3
    repo = repo_root()
    try:
        conflicts = live_conflicts(repo, {os.getpid()})
        if "legacy_autopilot" in conflicts:
            print("legacy autopilot scripts are running; stop them first (no concurrent supervisors)", file=sys.stderr)
            return 3
        task = None
        if args.task_file:
            task = Path(args.task_file).read_text(encoding="utf-8")
            if devctx.find_secret(task):
                print("task file matches a secret pattern; refusing", file=sys.stderr)
                return 2
        store = Store(root)
        store.stop_path.unlink(missing_ok=True)
        supervisor = Supervisor(store, make_host(repo), turns=args.turns,
                                sender=None if args.no_notify else webhook_sender())

        def on_signal(signum: int, _frame: Any) -> None:
            supervisor.signalled = True
        signal.signal(signal.SIGTERM, on_signal)
        signal.signal(signal.SIGINT, on_signal)
        result = supervisor.run(args.session, task=task)
        print(json.dumps({"result": result, "head_session": supervisor.state.get("head_session"),
                          "phase": supervisor.state.get("phase"), "hold": supervisor.state.get("hold")}))
        return {"idle": 0, "stopped": 0, "signal": 0, "held": 4}.get(result, 1)
    finally:
        lock.release()


def command_classify(args: argparse.Namespace) -> int:
    print(json.dumps(classify_turn(Path(args.turn_dir)).to_json(), indent=1))
    return 0


def command_status(args: argparse.Namespace) -> int:
    store = Store(control_root())
    try:
        state = store.load()
    except StateCorrupt as exc:
        print(f"state corrupt: {exc}")
        return 4
    view = {k: state.get(k) for k in ("phase", "head_session", "agent", "hold", "cooldowns", "counters",
                                      "pending", "last_outcome", "switches", "updated_at")}
    view["chain_length"] = len(state.get("chain") or [])
    view["stop_requested"] = store.stop_path.exists()
    view["notify"] = {k: state["notify"].get(k) for k in ("failures", "dropped", "last_digest")}
    print(json.dumps(view, indent=1))
    return 0


def command_stop(args: argparse.Namespace) -> int:
    store = Store(control_root())
    store.root.mkdir(parents=True, exist_ok=True)
    store.stop_path.write_text(iso(now_utc()) or "")
    print("stop requested; the supervisor exits at its next safe point and never kills a running turn")
    return 0


def command_release(args: argparse.Namespace) -> int:
    root = control_root()
    lock = Lock(root / "supervisor.lock")
    if not lock.acquire():
        print("a supervisor is running; stop it before releasing", file=sys.stderr)
        return 3
    try:
        if devctx.find_secret(args.note):
            print("note matches a secret pattern; refusing", file=sys.stderr)
            return 2
        store = Store(root)
        state = store.load()
        released = state.get("hold")
        held_turn = (released or {}).get("turn")
        previous = state.get("acknowledged") or {}
        if held_turn:
            same = previous.get("turn") == held_turn
            state["acknowledged"] = {
                "turn": held_turn,
                "reasons": sorted(set(previous.get("reasons") or [] if same else []) | {released["reason"]}),
                "cleared": sorted(set(previous.get("cleared") or [] if same else []) | set(args.clear_cooldown or [])),
            }
        elif args.clear_cooldown and previous.get("turn"):
            previous["cleared"] = sorted(set(previous.get("cleared") or []) | set(args.clear_cooldown))
        state["hold"] = None
        state["phase"] = "idle"
        state["counters"] = {"consecutive_failures": 0, "transient_streak": 0, "crash_retries": 0}
        for agent in args.clear_cooldown or []:
            state["cooldowns"].pop(agent, None)
            state["spend_caps"].pop(agent, None)  # e.g. the maintainer raised a spend cap
        dropped = []
        if args.drop_pending:
            dropped = unsettled_nonces(store.journal_path)
            state["pending"] = None
        if (released or {}).get("reason") == "permissions_changed":
            # The maintainer reviewed the new authority; the next run pins it.
            state["permissions_pinned"] = False
        store.save(state, now_utc())
        try:
            acknowledged = sorted({w.identity for w in make_host(repo_root()).live_work(datetime.min.replace(tzinfo=UTC))
                                   if w.identity})
        except Exception as exc:  # noqa: BLE001 - nothing acknowledged: live work still holds
            print(f"live-work snapshot failed: {type(exc).__name__}", file=sys.stderr)
            acknowledged = []
        store.journal({"event": "release", "at": iso(now_utc()), "hold": released, "note": args.note[:500],
                       "cleared": args.clear_cooldown or [], "dropped_pending": bool(args.drop_pending),
                       "dropped": dropped, "acknowledged_work": acknowledged})
        try:
            make_host(repo_root()).ledger("decision", f"relay-continuity hold released ({(released or {}).get('reason')}): "
                                                       f"{args.note[:400]}")
        except Exception as exc:  # noqa: BLE001
            print(f"ledger append failed: {type(exc).__name__}", file=sys.stderr)
        print(json.dumps({"released": released, "cleared": args.clear_cooldown or []}))
        return 0
    finally:
        lock.release()


def command_notify_test(args: argparse.Namespace) -> int:
    sender = webhook_sender()
    if sender is None:
        print("no usable webhook configured")
        return 2
    error = sender(render("test", {}) or "")
    print("sent" if error is None else f"failed: {error}")
    return 0 if error is None else 1


def command_watch(args: argparse.Namespace) -> int:
    root = control_root()
    lock = Lock(root / "watch.lock")
    if not lock.acquire():
        print("another watch instance is running", file=sys.stderr)
        return 3
    repo = repo_root()
    store = Store(root / "watch")
    stop = {"flag": False}
    signal.signal(signal.SIGTERM, lambda *_: stop.update(flag=True))
    signal.signal(signal.SIGINT, lambda *_: stop.update(flag=True))
    try:
        while not stop["flag"]:
            now = now_utc()
            try:
                state = store.load()
            except StateCorrupt:
                state = default_state()
            notifier = Notifier(state, sender=None if args.no_notify else webhook_sender(), log=lambda m: print(m, file=sys.stderr))
            try:
                supervised_state = Store(root).load()
            except StateCorrupt:
                supervised_state = default_state()
            supervised = set(supervised_state.get("chain") or [])
            first = not state["watch"].get("seen")
            if first:
                # Baseline: never alert on history that predates this watch.
                watch_once(state, Notifier(state, sender=None, log=lambda m: None), repo, now, supervised=supervised,
                           master=lambda: real_master(repo))
            else:
                notifier.retry_pending(now)
                watch_once(state, notifier, repo, now, supervised=supervised, master=lambda: real_master(repo))
            last = parse_ts(state["notify"].get("last_digest"))
            if not first and (last is None or now - last >= timedelta(hours=args.digest_hours)):
                journal = root / "attempts.jsonl"
                holds = sum('"event": "hold"' in line for line in journal.read_text().splitlines()) if journal.exists() else 0
                notifier.send("digest", now, dedupe_key=f"digest|{iso(now)}", **digest_fields(supervised_state, holds))
                state["notify"]["last_digest"] = iso(now)
            store.save(state, now)
            if args.once:
                break
            for _ in range(int(args.interval)):
                if stop["flag"]:
                    break
                time.sleep(1)
        return 0
    finally:
        lock.release()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="relay_continuity.py", description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="action", required=True)
    p = sub.add_parser("run", help="supervise continuation of one Relay session chain")
    p.add_argument("--session", required=True)
    p.add_argument("--task-file", help="maintainer task for the next turn (when the chain is idle)")
    p.add_argument("--turns", type=int, default=1, help="Relay turns per invocation (default 1)")
    p.add_argument("--no-notify", action="store_true")
    p.set_defaults(func=command_run)
    p = sub.add_parser("classify", help="classify one Relay turn directory")
    p.add_argument("turn_dir")
    p.set_defaults(func=command_classify)
    sub.add_parser("status", help="show durable supervisor state").set_defaults(func=command_status)
    sub.add_parser("stop", help="request a graceful stop").set_defaults(func=command_stop)
    p = sub.add_parser("release", help="clear a manual hold after maintainer review")
    p.add_argument("--note", required=True, help="why it is safe to continue (recorded)")
    p.add_argument("--clear-cooldown", action="append", choices=AGENTS)
    p.add_argument("--drop-pending", action="store_true", help="forget an unresolved launched attempt")
    p.set_defaults(func=command_release)
    sub.add_parser("notify-test", help="send one fixed test notification").set_defaults(func=command_notify_test)
    p = sub.add_parser("watch", help="notify-only monitor of REPL sessions and master")
    p.add_argument("--interval", type=float, default=60.0)
    p.add_argument("--digest-hours", type=float, default=6.0)
    p.add_argument("--once", action="store_true")
    p.add_argument("--no-notify", action="store_true")
    p.set_defaults(func=command_watch)
    args = parser.parse_args(argv)
    return int(args.func(args) or 0)


if __name__ == "__main__":
    sys.exit(main())
