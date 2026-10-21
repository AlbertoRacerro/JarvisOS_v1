"""Spec 195: Relay provider continuity supervisor and Slack outbound monitor (offline, injected Relay)."""
from __future__ import annotations

import importlib.util
import json
import os
import runpy
import shutil
import subprocess
import sys
import time
import urllib.error
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "relay_continuity.py"
SPEC = importlib.util.spec_from_file_location("relay_continuity", SCRIPT)
assert SPEC and SPEC.loader
rc = importlib.util.module_from_spec(SPEC)
sys.modules["relay_continuity"] = rc
SPEC.loader.exec_module(rc)

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "relay_continuity"
T0 = datetime(2026, 10, 18, 8, 0, tzinfo=UTC)
HEAD = "20261018-080000-aaaaaa"
SECRET_URL = "https://hooks.slack.com/services/T000/B000/abcdefghijklmnopqrstuvwx"


# ---------------------------------------------------------------------------
# Harness


class Clock:
    def __init__(self, start: datetime = T0):
        self.t = start
        self.slept: list[float] = []

    def now(self) -> datetime:
        return self.t

    def sleep(self, seconds: float) -> None:
        self.slept.append(seconds)
        self.t += timedelta(seconds=seconds)


def write_turn(session_dir: Path, events: list[dict[str, Any]], *, agent: str = "claude", status: str = "completed",
               prompt: str = "task", number: int = 1) -> Path:
    turn = session_dir / "turns" / f"turn-{number:03d}"
    turn.mkdir(parents=True, exist_ok=True)
    (turn / "output.jsonl").write_text("".join(json.dumps(e) + "\n" for e in events))
    (turn / "state.json").write_text(json.dumps({"agent_key": agent, "status": status}))
    (turn / "prompt.md").write_text(prompt)
    return turn


def relay_prompt(task: str) -> str:
    """Relay's real prompt layout (v0.7.7): rules, then the task, then continuation context."""
    return (f"You are participating in a Relay-managed single-agent session.\n\n## Rules\n- Focus on the task.\n\n"
            f"## Task\n\n{task}\n\n\n## Continuation Context\n\n- This run continues prior relay session: x\n")


def copy_fixture(name: str, session_dir: Path) -> Path:
    turn = session_dir / "turns" / "turn-001"
    shutil.copytree(FIXTURES / name, turn)
    (turn / "prompt.md").write_text("fixture")
    return turn


def claude_result(text: str = "done", *, error: bool = False, status: int | None = None) -> dict[str, Any]:
    return {"type": "result", "subtype": "success", "is_error": error, "result": text, "api_error_status": status,
            "terminal_reason": "api_error" if error else "completed"}


def tool_use(tid: str, name: str, **inp: Any) -> dict[str, Any]:
    return {"type": "assistant", "message": {"content": [{"type": "tool_use", "id": tid, "name": name, "input": inp}]}}


def tool_result(tid: str) -> dict[str, Any]:
    return {"type": "user", "message": {"content": [{"type": "tool_result", "tool_use_id": tid, "is_error": False}]}}


SUCCESS = [claude_result("ok")]
CODEX_SUCCESS = [{"type": "thread.started"}, {"type": "turn.completed"}]
QUOTA = [claude_result("You've hit your session limit · resets 11:50pm (Europe/Rome)", error=True, status=429)]
CODEX_QUOTA = [{"type": "thread.started"}, {"type": "error", "message": "You've hit your usage limit. try again at 11:38 PM."},
               {"type": "turn.failed", "error": {"message": "You've hit your usage limit. try again at 11:38 PM."}}]
EAI = [claude_result("API Error: Can't reach the API server — check your internet or DNS (EAI_AGAIN)", error=True)]


class FakeProc:
    def __init__(self, pid: int | None):
        self.pid = pid


class FakeRelay(rc.RelayAdapter):
    """Relay runner double: each launch consumes one scripted turn and writes a real session directory."""

    def __init__(self, repo: Path, script: list[tuple[str, list[dict[str, Any]]] | None], readings: Any = None):
        super().__init__(repo)
        self.script = list(script)
        self.launches: list[dict[str, Any]] = []
        self.readings = readings
        self.clock: Clock | None = None
        (repo / ".agent-relay" / "sessions").mkdir(parents=True, exist_ok=True)

    def limits(self) -> dict[str, Any] | None:
        return self.readings() if callable(self.readings) else self.readings

    def start(self, agent: str, parent: str, task: str, turns: int) -> FakeProc:
        if not self.script:
            raise AssertionError("unexpected Relay invocation")
        self.launches.append({"agent": agent, "parent": parent, "task": task, "turns": turns,
                              "at": self.clock.now() if self.clock else None})
        step = self.script.pop(0)
        self._current = (step, agent, task)
        return FakeProc(None)

    def finish(self, proc: FakeProc, timeout: float | None = None) -> Any:
        step, agent, task = self._current
        if step is None:
            return rc.RunResult(None, 1, False)
        _, events = step
        if callable(events):  # a reply that depends on the task (a diagnostic answers its own nonce)
            events = events(task)
        sid = f"20261018-{len(self.launches):06d}-{'b' * 6}"
        write_turn(self.sessions_dir() / sid, events, agent=agent, prompt=relay_prompt(task))
        return rc.RunResult(sid, 0, True)


class Env:
    def __init__(self, tmp: Path, script: list[Any] | None = None, *, readings: Any = None,
                 limits: Any = None, sender: Any = None):
        self.tmp = tmp
        self.repo = tmp / "repo"
        self.relay = FakeRelay(self.repo, script or [], readings)
        self.clock = Clock()
        self.relay.clock = self.clock
        self.fp = {"v": "fp0"}
        self.perm = {"v": "perm0"}
        self.conflicts: list[str] = []
        self.ledger: list[tuple[str, str]] = []
        self.logs: list[str] = []
        self.alive: dict[int, int] = {}
        self.sent: list[str] = []
        self.store = rc.Store(tmp / "control")
        self.host = rc.Host(
            relay=self.relay, now=self.clock.now, sleep=self.clock.sleep, fingerprint=lambda: self.fp["v"],
            conflicts=lambda own: list(self.conflicts), pid_alive=self._alive,
            ledger=lambda kind, text: self.ledger.append((kind, text)), permissions_digest=lambda: self.perm["v"],
            log=self.logs.append)
        self.limits = limits or rc.Limits()
        self.sender = sender if sender is not None else self._send
        self.reconcile = False

    def _alive(self, pid: int, start: int | None) -> bool:
        left = self.alive.get(pid, 0)
        if left > 0:
            self.alive[pid] = left - 1
            if left == 1:
                # The adopted Relay run finishes while we wait.
                self.relay.finish_pending()
            return True
        return False

    def _send(self, text: str) -> str | None:
        self.sent.append(text)
        return None

    def head(self, events: list[dict[str, Any]] | None = None, *, fixture: str | None = None, agent: str = "claude",
             sid: str = HEAD) -> Path:
        session = self.relay.sessions_dir() / sid
        return copy_fixture(fixture, session) if fixture else write_turn(session, events or SUCCESS, agent=agent)

    def supervisor(self, turns: int = 1) -> Any:
        return rc.Supervisor(self.store, self.host, self.limits, turns=turns, sender=self.sender,
                             reconcile=self.reconcile)

    def run(self, sid: str = HEAD, task: str | None = None) -> tuple[str, Any]:
        sup = self.supervisor()
        return sup.run(sid, task=task), sup

    def events(self) -> list[str]:
        return [text.splitlines()[0] for text in self.sent]


def reading(agent: str, used: float, resets_at: datetime, as_of: datetime) -> dict[str, Any]:
    return {"agent_key": agent, "status": "ok", "as_of": rc.iso(as_of),
            "windows": [{"id": "session", "used_percent": used, "resets_at": rc.iso(resets_at)}]}


def room(env: Env, *agents: str, exhausted: dict[str, datetime] | None = None) -> Any:
    """Fresh limits readings at the env clock: listed agents have room, `exhausted` agents are capped until a time."""
    def readings() -> dict[str, Any]:
        now = env.clock.now()
        out = {a: reading(a, 5, now + timedelta(hours=5), now) for a in agents}
        for agent, until in (exhausted or {}).items():
            out[agent] = reading(agent, 100, until, now) if now < until else reading(agent, 5, now + timedelta(hours=5), now)
        return out
    return readings


# ---------------------------------------------------------------------------
# Classification from real recorded turns


@pytest.mark.parametrize(("fixture", "outcome", "agent", "relay_status"), [
    ("codex_usage_limit", "quota", "codex", "completed"),
    ("claude_eai_again", "transient", "claude", "completed"),
    ("claude_session_limit", "quota", "claude", "completed"),
    ("claude_session_limit_bg_killed", "quota", "claude", "completed"),
    ("claude_spend_limit", "quota", "claude", "completed"),
    ("claude_crash_no_terminal", "crash", "claude", None),
    ("claude_success", "success", "claude", "completed"),
    ("codex_success_misreported", "success", "codex", "continue"),
    ("claude_invalid_model", "unknown", "claude", "continue"),
])
def test_real_turns_classify_from_raw_evidence(fixture: str, outcome: str, agent: str, relay_status: str | None) -> None:
    report = rc.classify_turn(FIXTURES / fixture, ref=T0)
    assert (report.outcome, report.agent, report.relay_status) == (outcome, agent, relay_status)
    assert report.bad_lines == 0
    assert rc.gate(report, fingerprint_changed=None) is None


def test_relay_completed_status_never_means_success() -> None:
    for name in ("codex_usage_limit", "claude_eai_again", "claude_session_limit", "claude_spend_limit",
                 "claude_session_limit_bg_killed"):
        state = json.loads((FIXTURES / name / "state.json").read_text())
        assert state["status"] == "completed"
        assert rc.classify_turn(FIXTURES / name, ref=T0).outcome != "success"
    misreported = json.loads((FIXTURES / "codex_success_misreported" / "state.json").read_text())
    assert "couldn't reach" in misreported["summary"]
    assert rc.classify_turn(FIXTURES / "codex_success_misreported", ref=T0).outcome == "success"


def test_missing_and_empty_output_are_crashes(tmp_path: Path) -> None:
    turn = tmp_path / "turn-001"
    turn.mkdir()
    assert rc.classify_turn(turn).outcome == "crash"
    (turn / "output.jsonl").write_text("")
    assert rc.classify_turn(turn).detail == "output empty"


def test_torn_output_is_unparseable(tmp_path: Path) -> None:
    turn = write_turn(tmp_path / "s", [tool_use("t1", "Read", file_path="/x")])
    with open(turn / "output.jsonl", "a") as handle:
        handle.write('{"type": "result", "is_err')
    report = rc.classify_turn(turn)
    assert report.outcome == "crash" and report.bad_lines == 1
    assert rc.gate(report, fingerprint_changed=False) == "output_unparseable"


@pytest.mark.parametrize(("text", "status", "expected"), [
    ("You've hit your monthly spend limit · your session limit resets 12:40pm (Europe/Rome)", 429, "spend_limit"),
    ("You've hit your weekly limit · resets Oct 20, 9am (Europe/Rome)", 429, "quota"),
    ("Invalid API key · Please run /login", 401, "auth"),
    ("OAuth token has expired", None, "auth"),
    ("API Error: 529 Overloaded", 529, "transient"),
    ("stream disconnected before completion", None, "transient"),
    ("There's an issue with the selected model", 404, "unknown"),
])
def test_text_classification(text: str, status: int | None, expected: str) -> None:
    assert rc.classify_text(text, status) == expected


def test_reset_times_are_parsed_as_next_occurrence() -> None:
    ref = datetime(2026, 10, 18, 20, 0, tzinfo=UTC)  # 22:00 in Rome
    assert rc.parse_reset("resets 11:50pm (Europe/Rome)", ref) == datetime(2026, 10, 18, 21, 50, tzinfo=UTC)
    assert rc.parse_reset("resets 4:20pm (Europe/Rome)", ref) == ref  # 5h40m behind: stale, due now
    assert rc.parse_reset("resets 1am (Europe/Rome)", ref) == datetime(2026, 10, 18, 23, 0, tzinfo=UTC)
    assert rc.parse_reset("resets Oct 20, 9am (Europe/Rome)", ref) == datetime(2026, 10, 20, 7, 0, tzinfo=UTC)
    rome = ZoneInfo("Europe/Rome")
    assert rc.parse_reset("try again at 11:38 PM.", ref, rome) == datetime(2026, 10, 18, 21, 38, tzinfo=UTC)
    assert rc.parse_reset("no time here", ref) is None
    # A time-only reset slightly behind the turn's end is stale: due now, not tomorrow.
    late = datetime(2026, 10, 18, 10, 45, tzinfo=UTC)  # 12:45 in Rome
    assert rc.parse_reset("resets 12:40pm (Europe/Rome)", late) == late
    assert rc.parse_reset("resets 4:20am (Europe/Rome)", late) == datetime(2026, 10, 19, 2, 20, tzinfo=UTC)


def test_spend_cap_with_timed_reset_is_a_session_quota(tmp_path: Path) -> None:
    report = rc.classify_turn(FIXTURES / "claude_spend_limit", ref=datetime(2026, 9, 24, 9, 0, tzinfo=UTC))
    assert report.outcome == "quota" and report.reset_at == "2026-09-24T10:40:00Z"
    turn = write_turn(tmp_path / "s", [claude_result("You've hit your monthly spend limit", error=True, status=429)])
    assert rc.classify_turn(turn).outcome == "spend_limit"


@pytest.mark.parametrize(("command", "kind"), [
    ("git status && git log -1", "read_only"),
    ("cd /x && git fetch -q && gh pr checks 5", "read_only"),
    ("git push origin HEAD", "external"),
    ("(cd x && git push)", "external"),
    ("echo $(git push)", "external"),
    ("x=`gh pr merge 3`", "external"),
    ("gh pr merge 828 --merge --match-head-commit abc", "external"),
    ("gh api repos/a/b/pulls -X PATCH -f state=closed", "external"),
    ("gh api repos/a/b/pulls", "read_only"),
    ("curl -s https://example.com", "read_only"),
    ("curl -X POST -d x https://example.com", "external"),
    ("git commit -qm \"$(cat <<'EOF'\nmsg; git push\nEOF\n)\"", "local_write"),
    ("cat > f.py <<'EOF'\ngit push\nrm -rf /\nEOF", "local_write"),
    ("echo 'a; git push' | grep x", "read_only"),
    ("sed -i s/a/b/ f", "local_write"),
    ("sleep 30 &", "background"),
    ("nohup python3 run.py > log 2>&1 &", "unknown"),
    ("python3 scripts/devctx.py recover", "read_only"),
    ("python3 scripts/devctx.py note finding x", "local_write"),
    ("find . -name x -exec rm {} \\;", "unknown"),
    ("for f in a b; do cat $f; done", "read_only"),
    ("ls > out.txt", "local_write"),
    ("ls >/dev/null 2>&1", "read_only"),
])
def test_command_effect_classes(command: str, kind: str) -> None:
    assert rc.classify_command(command)[0] == kind


def test_subagent_calls_settle_with_their_parent(tmp_path: Path) -> None:
    child = tool_use("c1", "Bash", command="git push")
    child["parent_tool_use_id"] = "p1"
    turn = write_turn(tmp_path / "s", [tool_use("p1", "Agent"), child, tool_result("p1"), claude_result("ok")])
    report = rc.classify_turn(turn)
    assert report.in_flight == []
    assert {c.label for c in report.effects} == {"Agent", "git push"}


# ---------------------------------------------------------------------------
# Continuation policy


def test_claude_quota_switches_to_codex_and_goes_idle(tmp_path: Path) -> None:
    env = Env(tmp_path, [("codex", CODEX_SUCCESS)])
    env.relay.readings = room(env, "codex")
    env.head(fixture="claude_session_limit")
    result, sup = env.run()
    assert result == "idle"
    assert [launch["agent"] for launch in env.relay.launches] == ["codex"]
    task = env.relay.launches[0]["task"]
    assert "[relay-continuity attempt rc-" in task and "devctx.py recover" in task
    assert "grants no new authority" in task
    cooldown = sup.state["cooldowns"]["claude"]
    assert cooldown["reason"] == "quota" and cooldown["source"] in ("message", "estimate")
    events = env.events()
    assert any("provider switched" in e for e in events) and any("turn completed" in e for e in events)
    assert sup.state["head_session"] != HEAD and sup.state["chain"][0] == HEAD


def test_provider_reported_reset_is_preferred_and_validated(tmp_path: Path) -> None:
    reset = T0 + timedelta(hours=2)
    env = Env(tmp_path, [("codex", CODEX_SUCCESS)],
              readings={"claude": reading("claude", 100, reset, T0), "codex": reading("codex", 10, reset, T0)})
    env.head(QUOTA)
    _, sup = env.run()
    assert sup.state["cooldowns"]["claude"] == {"until": rc.iso(reset), "source": "limits", "reason": "quota",
                                                "since": rc.iso(T0)}


@pytest.mark.parametrize("stale", ["old_as_of", "past_reset"])
def test_stale_limit_readings_are_discarded(tmp_path: Path, stale: str) -> None:
    as_of = T0 - timedelta(hours=3) if stale == "old_as_of" else T0
    reset = T0 + timedelta(hours=2) if stale == "old_as_of" else T0 - timedelta(hours=5)
    env = Env(tmp_path, [("codex", CODEX_SUCCESS)])
    env.relay.readings = lambda: {"claude": reading("claude", 100, reset, as_of),
                                  "codex": reading("codex", 5, T0 + timedelta(hours=5), env.clock.now())}
    env.head(QUOTA)
    _, sup = env.run()
    cooldown = sup.state["cooldowns"]["claude"]
    assert cooldown["source"] in ("message", "estimate")
    assert rc.parse_ts(cooldown["until"]) > T0


def test_codex_quota_returns_to_preferred_claude(tmp_path: Path) -> None:
    env = Env(tmp_path, [("claude", SUCCESS)])
    env.relay.readings = room(env, "claude")
    env.head(fixture="codex_usage_limit")
    result, _ = env.run()
    assert result == "idle" and env.relay.launches[0]["agent"] == "claude"


@pytest.mark.parametrize("readings", ["none", "failed", "stale", "implausible"])
def test_quota_never_fails_over_without_fresh_confirmed_room(tmp_path: Path, readings: str) -> None:
    env = Env(tmp_path, [("claude", SUCCESS)])
    entry = {"none": None,
             "failed": {"codex": {"agent_key": "codex", "status": "error"}},
             "stale": {"codex": reading("codex", 5, T0 + timedelta(hours=5), T0 - timedelta(hours=2))},
             "implausible": {"codex": reading("codex", 100, T0 + timedelta(days=30), T0)}}[readings]
    env.relay.readings = entry
    env.head(QUOTA)
    result, sup = env.run()
    # Codex is never launched on missing evidence; the chain waits for Claude's own printed reset
    # (11:50pm Rome = 21:50Z) and continues on Claude.
    assert result == "idle"
    assert [launch["agent"] for launch in env.relay.launches] == ["claude"]
    assert env.relay.launches[0]["at"] >= datetime(2026, 10, 18, 21, 50, tzinfo=UTC)


def test_transient_retries_same_agent_with_bounded_backoff(tmp_path: Path) -> None:
    env = Env(tmp_path, [("claude", EAI), ("claude", SUCCESS)])
    env.head(fixture="claude_eai_again")
    result, _ = env.run()
    assert result == "idle"
    assert [launch["agent"] for launch in env.relay.launches] == ["claude", "claude"]
    first, second = (launch["at"] for launch in env.relay.launches)
    assert first - T0 == timedelta(seconds=60) and second - first == timedelta(seconds=120)


def test_transient_streak_opens_circuit(tmp_path: Path) -> None:
    env = Env(tmp_path, [("claude", EAI)] * 3, limits=rc.Limits(max_transient_streak=2))
    env.head(EAI)
    result, sup = env.run()
    assert result == "held" and sup.state["hold"]["reason"] == "circuit_transient"
    assert len(env.relay.launches) == 2


def test_crash_retries_once_then_holds(tmp_path: Path) -> None:
    env = Env(tmp_path, [("claude", [tool_use("t1", "Read", file_path="/x"), tool_result("t1")])])
    env.head([tool_use("t1", "Read", file_path="/x"), tool_result("t1")])
    result, sup = env.run()
    assert result == "held" and sup.state["hold"]["reason"] == "crash_repeated"
    assert len(env.relay.launches) == 1


@pytest.mark.parametrize(("events", "reason"), [
    ([claude_result("There's an issue with the selected model", error=True, status=404)], "unknown_failure"),
    ([claude_result("Invalid API key · Please run /login", error=True, status=401)], "auth_failure"),
])
def test_auth_and_unknown_failures_hold_without_switching(tmp_path: Path, events: list[Any], reason: str) -> None:
    env = Env(tmp_path)
    env.head(events)
    result, sup = env.run()
    assert result == "held" and sup.state["hold"]["reason"] == reason
    assert env.relay.launches == []


def test_unavailable_fallback_waits_for_earliest_validated_reset(tmp_path: Path) -> None:
    codex_reset = T0 + timedelta(hours=1)

    def readings() -> dict[str, Any]:
        now = env.clock.now()
        used = 100 if now < codex_reset else 5
        return {"codex": reading("codex", used, codex_reset if now < codex_reset else now + timedelta(hours=5), now)}

    env = Env(tmp_path, [("codex", CODEX_SUCCESS)], readings=readings)
    env.head(QUOTA)  # Claude resets later (message time), Codex resets in one hour
    result, sup = env.run()
    assert result == "idle"
    assert [launch["agent"] for launch in env.relay.launches] == ["codex"]
    assert env.clock.now() >= codex_reset
    assert any("no coordinator provider available" in e for e in env.events())


def test_spend_limits_on_both_agents_hold(tmp_path: Path) -> None:
    spend = [claude_result("You've hit your monthly spend limit", error=True, status=429)]
    codex_spend = [{"type": "thread.started"},
                   {"type": "turn.failed", "error": {"message": "purchase more credits to continue"}}]
    env = Env(tmp_path, [("codex", codex_spend)])
    env.relay.readings = room(env, "codex")
    env.head(spend)
    result, sup = env.run()
    assert result == "held" and sup.state["hold"]["reason"] == "no_provider_available"
    assert [launch["agent"] for launch in env.relay.launches] == ["codex"]
    assert sup.state["cooldowns"]["claude"]["until"] is None and sup.state["cooldowns"]["codex"]["until"] is None


def test_switch_oscillation_is_bounded(tmp_path: Path) -> None:
    claude_reset, codex_reset = T0 + timedelta(minutes=5), T0 + timedelta(hours=1)

    def readings() -> dict[str, Any]:
        now = env.clock.now()
        out = {"claude": reading("claude", 100 if now < claude_reset else 5,
                                 claude_reset if now < claude_reset else now + timedelta(hours=5), now)}
        codex_out = bool(env.relay.launches)
        out["codex"] = reading("codex", 100 if codex_out else 5, codex_reset, now)
        return out

    env = Env(tmp_path, [("codex", CODEX_QUOTA)], readings=readings, limits=rc.Limits(max_switches=1))
    env.head(QUOTA)
    result, sup = env.run()
    # Claude -> Codex is the one allowed switch; returning to Claude five minutes later would be a second
    # switch inside the window, so the circuit opens instead of oscillating.
    assert result == "held" and sup.state["hold"]["reason"] == "circuit_switches"
    assert [launch["agent"] for launch in env.relay.launches] == ["codex"]
    assert env.clock.now() >= claude_reset


def test_transient_and_crash_retries_never_switch_provider(tmp_path: Path) -> None:
    # Codex is the current agent after a switch; Claude has room and the dwell has long passed.
    env = Env(tmp_path, [("codex", EAI), ("codex", [tool_use("r", "Read", file_path="/x"), tool_result("r")]),
                         ("codex", CODEX_SUCCESS)], limits=rc.Limits(min_dwell=timedelta(minutes=2)))
    env.relay.readings = room(env, "claude", "codex")
    state = rc.default_state()
    state.update({"head_session": HEAD, "chain": [HEAD], "permissions_digest": "perm0", "permissions_pinned": True,
                  "last_switch_at": rc.iso(T0 - timedelta(hours=1)), "agent": "codex"})
    env.store.save(state, T0)
    env.head(EAI, agent="codex")
    result, _ = env.run()
    assert result == "idle"
    assert [launch["agent"] for launch in env.relay.launches] == ["codex", "codex", "codex"]


def test_return_to_claude_only_at_a_turn_boundary_after_dwell(tmp_path: Path) -> None:
    env = Env(tmp_path, [("codex", CODEX_SUCCESS), ("claude", SUCCESS)], limits=rc.Limits(min_dwell=timedelta(minutes=30)))
    env.relay.readings = room(env, "claude", "codex")
    state = rc.default_state()
    state.update({"head_session": HEAD, "chain": [HEAD], "permissions_digest": "perm0", "permissions_pinned": True,
                  "last_switch_at": rc.iso(T0 - timedelta(minutes=10)), "agent": "codex"})
    env.store.save(state, T0)
    env.head(CODEX_SUCCESS, agent="codex")
    # Ten minutes after the switch the next maintainer task stays on Codex ...
    assert env.run(task="step one")[0] == "idle"
    env.clock.t += timedelta(minutes=30)
    # ... and past the dwell the next turn boundary returns to the preferred Claude.
    assert env.run(task="step two")[0] == "idle"
    assert [launch["agent"] for launch in env.relay.launches] == ["codex", "claude"]


def test_consecutive_failure_circuit(tmp_path: Path) -> None:
    env = Env(tmp_path, [("claude", EAI)] * 10,
              limits=rc.Limits(max_consecutive_failures=3, max_transient_streak=99))
    env.head(EAI)
    result, sup = env.run()
    assert result == "held" and sup.state["hold"]["reason"] == "circuit_failures"
    assert len(env.relay.launches) == 3


def test_maintainer_task_runs_on_preferred_agent_when_idle(tmp_path: Path) -> None:
    env = Env(tmp_path, [("claude", SUCCESS)])
    env.relay.readings = room(env, "claude")
    env.head(CODEX_SUCCESS, agent="codex")
    result, _ = env.run(task="Next step: reconcile STATUS")
    assert result == "idle"
    assert env.relay.launches[0]["agent"] == "claude"
    assert env.relay.launches[0]["task"].endswith("Next step: reconcile STATUS")


def test_misreported_success_head_needs_nothing(tmp_path: Path) -> None:
    env = Env(tmp_path)
    env.head(fixture="codex_success_misreported")
    assert env.run()[0] == "idle"
    assert env.relay.launches == []


# ---------------------------------------------------------------------------
# Side-effect gate: recovery never silently duplicates a non-idempotent operation


IN_FLIGHT = {
    "git push": tool_use("x", "Bash", command="cd /r && git push origin HEAD"),
    "gh pr merge": tool_use("x", "Bash", command="gh pr merge 1 --merge"),
    "Write": tool_use("x", "Write", file_path="/r/a.py"),
    "subagent": tool_use("x", "Agent", subagent_type="general-purpose"),
    "unknown script": tool_use("x", "Bash", command="./deploy.sh"),
}


@pytest.mark.parametrize("name", sorted(IN_FLIGHT))
@pytest.mark.parametrize("terminal", ["quota", "transient", "crash"])
def test_in_flight_side_effect_holds_and_never_invokes_relay(tmp_path: Path, name: str, terminal: str) -> None:
    tail = {"quota": QUOTA, "transient": EAI, "crash": []}[terminal]
    env = Env(tmp_path)  # an empty script: any Relay invocation fails the test
    env.head([tool_use("r", "Read", file_path="/x"), tool_result("r"), IN_FLIGHT[name], *tail])
    result, sup = env.run()
    assert result == "held" and sup.state["hold"]["reason"] == "effects_uncertain"
    assert env.relay.launches == []
    assert any("HOLD" in e for e in env.events())
    # A restart must not bypass the hold either.
    result, _ = env.run()
    assert result == "held" and env.relay.launches == []


def test_in_flight_read_only_call_does_not_block(tmp_path: Path) -> None:
    env = Env(tmp_path, [("codex", CODEX_SUCCESS)])
    env.head([tool_use("x", "Bash", command="git status"), *QUOTA])
    assert env.run()[0] == "idle"


def test_completed_effects_are_reported_to_the_successor_not_replayed(tmp_path: Path) -> None:
    env = Env(tmp_path, [("codex", CODEX_SUCCESS)])
    env.relay.readings = room(env, "codex")
    env.head([tool_use("p", "Bash", command="git push origin HEAD"), tool_result("p"),
              tool_use("m", "Bash", command="gh pr merge 5 --merge"), tool_result("m"), *QUOTA])
    assert env.run()[0] == "idle"
    task = env.relay.launches[0]["task"]
    assert "[external] git push" in task and "[external] gh pr merge" in task
    assert "do not repeat them blindly" in task


def test_crash_without_output_holds_when_repository_changed(tmp_path: Path) -> None:
    env = Env(tmp_path, [None])  # Relay dies without creating a session
    env.head(EAI)

    def changed_fingerprint() -> str:
        return "fp-after" if env.relay.launches else "fp0"
    env.host.fingerprint = changed_fingerprint
    result, sup = env.run()
    assert result == "held" and sup.state["hold"]["reason"] == "attempt_unresolved"
    assert len(env.relay.launches) == 1


def test_attempt_without_session_holds_even_when_repository_unchanged(tmp_path: Path) -> None:
    # A remote effect (a merge, a PR comment) leaves the local fingerprint unchanged: no proof of no effect.
    env = Env(tmp_path, [None])
    env.head(EAI)
    result, sup = env.run()
    assert result == "held" and sup.state["hold"]["reason"] == "attempt_unresolved"
    assert len(env.relay.launches) == 1
    assert env.run()[0] == "held" and len(env.relay.launches) == 1


def test_crash_with_recorded_calls_holds_when_repository_changed(tmp_path: Path) -> None:
    # The retry records only a Read, but the repository moved: an unrecorded write may have happened.
    env = Env(tmp_path, [("claude", [tool_use("r", "Read", file_path="/x"), tool_result("r")])])
    env.head(EAI)
    env.host.fingerprint = lambda: "fp-after" if env.relay.launches else "fp0"
    result, sup = env.run()
    assert result == "held" and sup.state["hold"]["reason"] == "effects_uncertain"
    assert len(env.relay.launches) == 1


# ---------------------------------------------------------------------------
# Restart recovery and process safety


def _pending(env: Env, nonce: str, pid: int | None) -> None:
    state = rc.default_state()
    state.update({"phase": "running", "head_session": HEAD, "chain": [HEAD], "agent": "codex",
                  "permissions_digest": "perm0",
                  "pending": {"nonce": nonce, "agent": "codex", "parent": HEAD, "started_at": rc.iso(T0),
                              "pid": pid, "pid_start": 42, "fingerprint": "fp0", "attempt": 1}})
    env.store.save(state, T0)


def test_restart_during_failover_adopts_running_attempt_without_relaunch(tmp_path: Path) -> None:
    env = Env(tmp_path)
    env.head(QUOTA)
    nonce = "rc-20261018T080000Z-deadbeef"
    _pending(env, nonce, pid=4242)
    env.alive[4242] = 2

    def finish_pending() -> None:
        write_turn(env.relay.sessions_dir() / "20261018-080100-cccccc", CODEX_SUCCESS, agent="codex",
                   prompt=relay_prompt(f"[relay-continuity attempt {nonce}]"))
    env.relay.finish_pending = finish_pending  # type: ignore[attr-defined]
    result, sup = env.run()
    assert result == "idle"
    assert env.relay.launches == []
    assert sup.state["head_session"] == "20261018-080100-cccccc" and sup.state["pending"] is None


def test_restart_with_dead_attempt_and_changed_repository_holds(tmp_path: Path) -> None:
    env = Env(tmp_path)
    env.head(QUOTA)
    _pending(env, "rc-x", pid=4243)
    env.fp["v"] = "fp-changed"
    result, sup = env.run()
    assert result == "held" and sup.state["hold"]["reason"] == "attempt_unresolved"
    assert env.relay.launches == []


def test_restart_with_dead_attempt_found_by_nonce_settles(tmp_path: Path) -> None:
    env = Env(tmp_path)
    env.head(QUOTA)
    nonce = "rc-20261018T080000Z-cafef00d"
    _pending(env, nonce, pid=None)
    write_turn(env.relay.sessions_dir() / "20261018-080030-dddddd",
               [tool_use("x", "Bash", command="git push"), *CODEX_QUOTA], agent="codex",
               prompt=relay_prompt(f"[relay-continuity attempt {nonce}]"))
    result, sup = env.run()
    assert result == "held" and sup.state["hold"]["reason"] == "effects_uncertain"
    assert env.relay.launches == []


def test_concurrent_supervisors_are_refused(tmp_path: Path) -> None:
    first, second = rc.Lock(tmp_path / "supervisor.lock"), rc.Lock(tmp_path / "supervisor.lock")
    assert first.acquire()
    assert not second.acquire()
    first.release()
    assert second.acquire()
    second.release()


def test_cli_run_refuses_when_lock_is_held(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RELAY_CONTINUITY_DIR", str(tmp_path))
    holder = rc.Lock(tmp_path / "supervisor.lock")
    assert holder.acquire()
    try:
        assert rc.main(["run", "--session", HEAD, "--no-notify"]) == 3
    finally:
        holder.release()


def test_live_conflicts_detects_real_relay_repl_and_legacy_autopilot(tmp_path: Path) -> None:
    repo, elsewhere = tmp_path / "repo", tmp_path / "other"
    repo.mkdir()
    elsewhere.mkdir()
    procs = [subprocess.Popen(["bash", "-c", f"exec -a {name} sleep 30"], cwd=cwd)
             for name, cwd in (("relay", repo), ("relay", elsewhere),
                               ("/home/u/jarvis-control/autopilot/watchdog.sh", elsewhere))]
    try:
        for _ in range(50):
            if all(Path(f"/proc/{p.pid}/cmdline").read_bytes().startswith((b"relay", b"/home")) for p in procs):
                break
            time.sleep(0.05)
        assert rc.live_conflicts(repo, {os.getpid()}) == ["legacy_autopilot", "repl_active"]
        assert rc.live_conflicts(elsewhere, {os.getpid(), procs[1].pid}) == ["legacy_autopilot"]
    finally:
        for proc in procs:
            proc.kill()
            proc.wait()


RELAY_SAFE = Path(__file__).resolve().parents[2] / "scripts" / "relay_safe.py"


def _lease_holder(repo: Path, *argv: str, **env: str) -> subprocess.Popen[bytes]:
    """A process that takes the coordinator lease exactly as scripts/relay_safe.py does, then idles."""
    code = ("import os, runpy, sys, time; from pathlib import Path\n"
            f"lease = runpy.run_path({str(RELAY_SAFE)!r})['hold_coordinator_lease'](sys.argv, Path.cwd(), dict(os.environ))\n"
            "Path('ready').write_text(str(lease is not None)); time.sleep(30)\n")
    proc = subprocess.Popen([sys.executable, "-c", code, *argv], cwd=repo,
                            env={**os.environ, "JARVISOS_MISSION_PROFILE": "", **env})
    deadline = time.monotonic() + 10
    while not (repo / "ready").exists() and time.monotonic() < deadline:
        assert proc.poll() is None
        time.sleep(0.01)
    return proc


@pytest.mark.parametrize(("argv", "env", "held"), [
    ((), {}, True),                                     # a REPL
    (("run", "--agent", "claude"), {}, True),           # a headless coordinator run
    (("daemon",), {}, False),
    (("hook", "pre-tool"), {}, False),
    (("run",), {"JARVISOS_MISSION_PROFILE": "1"}, False),  # the mission owner's own turn
])
def test_coordinator_lease_is_seen_across_pid_namespaces(
    tmp_path: Path, argv: tuple[str, ...], env: dict[str, str], held: bool,
) -> None:
    repo = tmp_path / "repo"
    (repo / ".git").mkdir(parents=True)
    (repo / "sub").mkdir()
    assert rc.coordinator_lease_held(repo) is False  # no lease file yet
    proc = _lease_holder(repo, *argv, **env)
    try:
        assert (repo / "ready").read_text() == str(held)
        # Excluding the holder's pid stands in for another sandbox instance, whose process table is invisible.
        assert rc.live_conflicts(repo, {os.getpid(), proc.pid}) == (["repl_active"] if held else [])
    finally:
        proc.kill()
        proc.wait(timeout=5)
    assert rc.coordinator_lease_held(repo) is False  # the kernel released it with the process


def test_coordinator_lease_found_from_a_subdirectory_and_never_outside_a_repository(tmp_path: Path) -> None:
    safe = runpy.run_path(str(RELAY_SAFE))
    assert safe["hold_coordinator_lease"](["relay"], tmp_path, {}) is None
    (tmp_path / "repo/.git").mkdir(parents=True)
    (tmp_path / "repo/a/b").mkdir(parents=True)
    lease = safe["hold_coordinator_lease"](["relay"], tmp_path / "repo/a/b", {})
    try:
        assert lease is not None and (tmp_path / "repo/.agent-relay/locks/coordinator.lease").exists()
    finally:
        lease.close()


@pytest.mark.parametrize("entry", ["relay", "agent-relay", "relay_safe.py", "unrelated.py"])
@pytest.mark.parametrize("mode", ["interactive", "daemon", "hook"])
def test_python_relay_launchers_are_detected_without_claiming_unrelated_python(
    tmp_path: Path, entry: str, mode: str,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    script = tmp_path / entry
    ready = script.with_suffix(".ready")
    script.write_text(
        "from pathlib import Path\nimport time\n"
        "Path(__file__).with_suffix('.ready').touch()\ntime.sleep(30)\n"
    )
    args = ["--no-tmux", "--no-onboarding"] if mode == "interactive" else [mode]
    proc = subprocess.Popen([sys.executable, str(script), *args], cwd=repo)
    try:
        deadline = time.monotonic() + 5
        while not ready.exists() and time.monotonic() < deadline:
            assert proc.poll() is None
            time.sleep(0.01)
        assert ready.exists()
        recognized = entry != "unrelated.py"
        assert rc.live_conflicts(repo, {os.getpid()}) == (
            ["repl_active"] if recognized and mode == "interactive" else []
        )
        proc_entry = Path(f"/proc/{proc.pid}")
        assert rc._ignorable(rc._argv(proc_entry), proc_entry) is (recognized and mode != "interactive")
        assert rc.live_conflicts(repo, {os.getpid(), proc.pid}) == []
    finally:
        proc.kill()
        proc.wait(timeout=5)


@pytest.mark.parametrize("interpreter", [None, "python", "python3", "python3.12"])
def test_relay_safe_direct_or_python_entry_keeps_command_positions(interpreter: str | None) -> None:
    command = ["/opt/tools/relay_safe.py", "--no-tmux", "daemon"]
    argv = [f"/opt/venv/bin/{interpreter}", *command] if interpreter else command
    assert rc._relay_argv(argv) == command
    assert rc._ignorable(argv, Path("/unused-proc-entry"))
    assert not rc._ignorable([*argv[:-1], "--no-onboarding"], Path("/unused-proc-entry"))


def test_live_repl_on_the_repository_blocks_launch(tmp_path: Path) -> None:
    env = Env(tmp_path)
    env.conflicts = ["repl_active"]
    env.head(QUOTA)
    result, sup = env.run()
    assert result == "held" and sup.state["hold"]["reason"] == "repl_active"
    assert env.relay.launches == []


def test_permission_change_holds(tmp_path: Path) -> None:
    env = Env(tmp_path, [("codex", CODEX_SUCCESS)])
    env.head(SUCCESS)
    assert env.run()[0] == "idle"
    env.perm["v"] = "perm-widened"
    env.head(QUOTA, sid="20261018-090000-eeeeee")
    result, sup = env.run("20261018-090000-eeeeee")
    assert result == "held" and sup.state["hold"]["reason"] == "permissions_changed"
    assert env.relay.launches == []


def test_permission_digest_ignores_model_but_not_authority(tmp_path: Path) -> None:
    path = tmp_path / "permissions.toml"
    base = '[claude.allow]\npatterns = []\n\n[claude.backend]\nmode = "default"\nmodel = "opus"\n'
    path.write_text(base)
    digest = rc.permissions_digest(path)
    path.write_text(base.replace('"opus"', '"haiku"'))
    assert rc.permissions_digest(path) == digest
    path.write_text(base.replace('"default"', '"bypassPermissions"'))
    assert rc.permissions_digest(path) != digest
    path.write_text(base.replace("patterns = []", 'patterns = ["Bash(*)"]'))
    assert rc.permissions_digest(path) != digest
    path.write_text("not = [valid")
    assert rc.permissions_digest(path) == "unreadable"


def test_interrupted_state_write_keeps_previous_state(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    store = rc.Store(tmp_path)
    good = rc.default_state()
    good["head_session"] = HEAD
    store.save(good, T0)

    def crash(*_args: Any) -> None:
        raise OSError("power loss")
    monkeypatch.setattr(rc.os, "replace", crash)
    broken = rc.default_state()
    broken["head_session"] = "20261018-999999-ffffff"
    with pytest.raises(OSError):
        store.save(broken, T0)
    monkeypatch.undo()
    assert store.load()["head_session"] == HEAD


@pytest.mark.parametrize("content", ["{not json", json.dumps({"schema": "other"}),
                                     json.dumps({"schema": rc.SCHEMA, "phase": "bogus"})])
def test_corrupt_state_holds_without_acting(tmp_path: Path, content: str) -> None:
    env = Env(tmp_path, [("codex", CODEX_SUCCESS)])
    env.head(QUOTA)
    env.store.root.mkdir(parents=True, exist_ok=True)
    env.store.state_path.write_text(content)
    result, _ = env.run()
    assert result == "held" and env.relay.launches == []
    assert env.store.state_path.read_text() == content
    assert any("state_corrupt" in text for text in env.sent)


def test_stop_request_and_resume(tmp_path: Path) -> None:
    env = Env(tmp_path, [("codex", CODEX_SUCCESS)])
    env.head(QUOTA)
    env.store.root.mkdir(parents=True, exist_ok=True)
    env.store.stop_path.write_text("now")
    result, sup = env.run()
    assert result == "stopped" and env.relay.launches == []
    assert sup.state["phase"] == "stopped"
    env.store.stop_path.unlink()
    result, _ = env.run()
    assert result == "idle" and len(env.relay.launches) == 1


def test_release_clears_hold_and_records_it(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    env = Env(tmp_path)
    env.head([IN_FLIGHT["git push"], *QUOTA])
    assert env.run()[0] == "held"
    monkeypatch.setenv("RELAY_CONTINUITY_DIR", str(env.store.root))
    monkeypatch.setattr(rc, "make_host", lambda repo: env.host)
    monkeypatch.setattr(rc, "repo_root", lambda: env.repo)
    assert rc.main(["release", "--note", "verified push landed on origin; safe to continue"]) == 0
    state = env.store.load()
    assert state["hold"] is None and state["phase"] == "idle"
    assert "release" in env.store.journal_path.read_text()
    assert any(kind == "decision" for kind, _ in env.ledger)
    assert rc.main(["release", "--note", "token ghp_abcdefghijklmnopqrstuvwxyz0123"]) == 2


def test_released_turn_is_continued_not_regated(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    env = Env(tmp_path, [("claude", SUCCESS)])
    env.head([claude_result("There's an issue with the selected model", error=True, status=404)])
    assert env.run()[0] == "held"
    monkeypatch.setenv("RELAY_CONTINUITY_DIR", str(env.store.root))
    monkeypatch.setattr(rc, "make_host", lambda repo: env.host)
    monkeypatch.setattr(rc, "repo_root", lambda: env.repo)
    assert rc.main(["release", "--note", "model fixed in permissions; continue"]) == 0
    result, sup = env.run(task="Retry the step")
    assert result == "idle"
    assert [launch["agent"] for launch in env.relay.launches] == ["claude"]
    assert env.relay.launches[0]["task"].endswith("Retry the step")
    assert sup.state["acknowledged"] is None
    # The acknowledgement covers only that turn: a new failure on the chain is gated again.
    env.relay.script = [("claude", [claude_result("bad", error=True, status=404)])]
    assert env.run(task="again")[0] == "held"


# ---------------------------------------------------------------------------
# Live work: detached jobs that outlive the call that launched them


def work(identity: str | None = "proc:1:1:x", label: str = "process node", *, recent: bool = True,
         inherited: bool = False) -> Any:
    return rc.Work(identity, label, recent=recent, inherited=inherited)


def test_live_work_in_a_checkout_holds_a_quota_failure_without_relaunch(tmp_path: Path) -> None:
    env = Env(tmp_path, [("codex", CODEX_SUCCESS)])
    seen: list[datetime] = []
    env.host.live_work = lambda since: seen.append(since) or [work()]
    env.head(QUOTA)
    result, sup = env.run()
    assert result == "held" and sup.state["hold"]["reason"] == "live_work"
    assert env.relay.launches == [] and seen
    assert any("live work in the checkout: process node" in line for line in env.logs)


def test_live_work_holds_a_new_task_after_a_successful_turn(tmp_path: Path) -> None:
    env = Env(tmp_path, [("claude", SUCCESS)])
    env.host.live_work = lambda since: [work("ctr:abc:t:e", "docker container abc")]
    env.head(SUCCESS)
    result, sup = env.run(task="Next step")
    assert result == "held" and sup.state["hold"]["reason"] == "live_work" and env.relay.launches == []


def test_failing_live_work_check_holds(tmp_path: Path) -> None:
    def boom(since: datetime) -> list[Any]:
        raise RuntimeError("git worktree list failed")
    env = Env(tmp_path, [("codex", CODEX_SUCCESS)])
    env.host.live_work = boom
    env.head(QUOTA)
    assert env.run()[0] == "held" and env.relay.launches == []


@pytest.mark.parametrize(("works", "acknowledged", "held"), [
    ([], [], False),
    ([work(recent=False)], [], False),                        # older than the window, a plain process
    ([work(recent=False, inherited=True)], [], True),         # a pane program or a container with exec sessions
    ([work(recent=False, inherited=True)], ["proc:1:1:x"], False),  # exactly what the release acknowledged
    ([work(recent=True)], ["proc:1:1:x"], False),
    ([work("proc:1:1:y", recent=False, inherited=True)], ["proc:1:1:x"], True),  # same pid, new program (exec)
    ([work(None, "process unreadable")], [], True),           # an inspection failure is never acknowledged
])
def test_live_work_gate_respects_window_inheritance_and_acknowledgement(
        tmp_path: Path, works: list[Any], acknowledged: list[str], held: bool) -> None:
    env = Env(tmp_path, [("codex", CODEX_SUCCESS)])
    env.host.live_work = lambda since: works
    env.store.root.mkdir(parents=True, exist_ok=True)
    env.store.journal({"event": "release", "at": rc.iso(T0 - timedelta(days=30)), "acknowledged_work": acknowledged})
    env.head(QUOTA)
    assert (env.run()[0] == "held") is held
    assert (env.relay.launches == []) is held


def test_release_acknowledges_the_work_live_at_that_moment(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    env = Env(tmp_path, [("codex", CODEX_SUCCESS)])
    live = [work("proc:7:9:a", recent=False, inherited=True), work(None, "process unreadable")]
    env.host.live_work = lambda since: live[:1]
    env.head(QUOTA)
    assert env.run()[0] == "held"
    monkeypatch.setenv("RELAY_CONTINUITY_DIR", str(env.store.root))
    monkeypatch.setattr(rc, "make_host", lambda repo: rc.Host(relay=env.relay, live_work=lambda since: live))
    monkeypatch.setattr(rc, "repo_root", lambda: env.repo)
    assert rc.main(["release", "--note", "the pane dev server is meant to keep running"]) == 0
    record = json.loads(env.store.journal_path.read_text().splitlines()[-1])
    assert record["event"] == "release" and record["acknowledged_work"] == ["proc:7:9:a"]
    assert env.run()[0] == "idle" and len(env.relay.launches) == 1


def test_work_window_starts_at_the_chain_and_moves_to_the_latest_release(tmp_path: Path) -> None:
    env = Env(tmp_path)
    env.head(SUCCESS)
    session = env.relay.sessions_dir() / HEAD
    created = T0 - timedelta(days=2)
    (session / "session.json").write_text(json.dumps({"created_at": rc.iso(created)}))
    sup = env.supervisor()
    sup.state["head_session"] = HEAD
    assert sup.work_window() == created
    env.store.root.mkdir(parents=True, exist_ok=True)
    released = T0 - timedelta(hours=1)
    env.store.journal({"event": "release", "at": rc.iso(released), "acknowledged_work": ["a"]})
    env.store.journal({"event": "release", "at": rc.iso(created - timedelta(days=1)), "acknowledged_work": ["b"]})
    assert sup.work_window() == released and sup.last_release() == (released, frozenset({"a"}))
    (session / "session.json").write_text("not json")
    env.store.journal_path.unlink()
    assert sup.work_window() == datetime.min.replace(tzinfo=UTC)  # unknown chain start: the widest window


def test_worktree_listing_failure_raises(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(rc.devctx, "run", lambda *a, **k: (128, ""))
    with pytest.raises(RuntimeError):
        rc.worktree_roots(tmp_path)


def fake_proc(root: Path, btime: int = 1_000_000) -> Path:
    proc = root / "proc"
    proc.mkdir()
    (proc / "stat").write_text(f"cpu  1 2 3\nbtime {btime}\n")
    return proc


def add_proc(proc: Path, pid: int, *, argv: list[str], cwd: Path | None, started: datetime, btime: int = 1_000_000,
             ppid: int = 1, state: str = "S", comm: str | None = None, stdin: str = "/dev/pts/3") -> None:
    entry = proc / str(pid)
    entry.mkdir()
    ticks = int((started.timestamp() - btime) * os.sysconf("SC_CLK_TCK"))
    rest = [state, str(ppid)] + ["0"] * 17 + [str(ticks)]
    (entry / "stat").write_text(f"{pid} ({comm or Path(argv[0]).name}) {' '.join(rest)} 0 0\n")
    (entry / "comm").write_text(f"{(comm or Path(argv[0]).name)[:15]}\n")
    (entry / "status").write_text(f"Name:\t{Path(argv[0]).name}\nPPid:\t{ppid}\n")
    (entry / "cmdline").write_bytes(b"\0".join(a.encode() for a in argv) + b"\0")
    (entry / "fd").mkdir()
    os.symlink(stdin, entry / "fd" / "0")
    if cwd is None:
        (entry / "cwd").mkdir()  # readlink fails with EINVAL: unreadable, not gone
    else:
        os.symlink(cwd, entry / "cwd")


def proc_tree(tmp_path: Path) -> tuple[Path, Path, Path]:
    proc = fake_proc(tmp_path)
    repo, worktree, elsewhere = tmp_path / "repo", tmp_path / "wt", tmp_path / "home"
    for d in (repo / "frontend", worktree, elsewhere):
        d.mkdir(parents=True)
    new, old = T0 + timedelta(minutes=5), T0 - timedelta(hours=1)
    add_proc(proc, 10, argv=["node", "vite"], cwd=repo / "frontend", started=new)
    add_proc(proc, 11, argv=["python", "-m", "pytest"], cwd=worktree, started=new, comm="py test$(x)")
    add_proc(proc, 12, argv=["node", "old-server"], cwd=repo, started=old)
    add_proc(proc, 13, argv=["node", "elsewhere"], cwd=elsewhere, started=new)
    add_proc(proc, 14, argv=["bash"], cwd=repo, started=new)                          # idle prompt on a terminal
    add_proc(proc, 15, argv=["bash"], cwd=repo, started=new, stdin="pipe:[4242]", comm="stdin-sh")  # fed a script
    add_proc(proc, 16, argv=["python", "x.py"], cwd=repo, started=new, state="Z", comm="zombie")
    add_proc(proc, 17, argv=["tmux", "new-session"], cwd=repo, started=old, comm="tmux: server")
    add_proc(proc, 23, argv=["tmux: server"], cwd=repo, started=old, comm="tmux: server")  # rewritten title
    add_proc(proc, 24, argv=["python", "-m", "http.server"], cwd=repo, started=old, ppid=23, comm="pane-exec2")
    add_proc(proc, 18, argv=["python", "-m", "pytest", "-q"], cwd=repo, started=old, ppid=17, comm="pane-exec")
    add_proc(proc, 21, argv=["python3", "scripts/relay_continuity.py", "watch"], cwd=repo, started=new, comm="watcher")
    add_proc(proc, 22, argv=["python3", "scripts/relay_continuity.py", "--help"], cwd=repo, started=new, comm="rc-other")
    # The supervisor (20) and its ancestors (19: the pane shell running it) are never reported.
    add_proc(proc, 19, argv=["bash", "-c", "python3 scripts/relay_continuity.py run"], cwd=repo, started=new, comm="pane")
    add_proc(proc, 20, argv=["python3", "scripts/relay_continuity.py", "run"], cwd=repo, started=new, ppid=19,
             comm="supervisor")
    return proc, repo, worktree


def test_live_processes_reports_work_in_any_checkout_with_age_and_inheritance(tmp_path: Path) -> None:
    proc, repo, worktree = proc_tree(tmp_path)
    found = {w.label: w for w in rc.live_processes([repo, worktree], T0, {20}, proc_root=proc)}
    assert set(found) == {"process node", "process py_test__x_", "process stdin-sh", "process pane-exec",
                          "process pane-exec2", "process rc-other"}
    assert found["process pane-exec2"].inherited  # a server that rewrote its argv to `tmux: server`
    assert found["process py_test__x_"].recent and not found["process py_test__x_"].inherited
    assert not found["process pane-exec"].recent and found["process pane-exec"].inherited  # exec in an old pane
    old = [w for w in rc.live_processes([repo, worktree], T0, {20}, proc_root=proc) if w.label == "process node"]
    assert sorted(w.recent for w in old) == [False, True]  # vite (new) and old-server (old)
    assert all(w.identity and w.identity.startswith("proc:") for w in found.values())


def test_pane_exec_changes_the_identity(tmp_path: Path) -> None:
    proc, repo, worktree = proc_tree(tmp_path)
    before = {w.identity for w in rc.live_processes([repo], T0, {20}, proc_root=proc) if w.label == "process pane-exec"}
    (proc / "18" / "cmdline").write_bytes(b"python\0-m\0http.server\0")
    after = {w.identity for w in rc.live_processes([repo], T0, {20}, proc_root=proc) if w.label == "process pane-exec"}
    assert before and after and before != after


def test_unreadable_processes_and_tables_count_as_live_work(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    proc, repo, _ = proc_tree(tmp_path)
    add_proc(proc, 30, argv=["python"], cwd=None, started=T0)
    add_proc(proc, 31, argv=["(sd-pam)"], cwd=None, started=T0 - timedelta(days=3), comm="(sd-pam)")
    unreadable = [w for w in rc.live_processes([repo], T0, {20}, proc_root=proc) if w.label == "process unreadable"]
    assert sorted(w.recent for w in unreadable) == [False, True]  # judged by start time; acknowledgeable
    assert all(w.identity and w.identity.endswith(":unreadable") for w in unreadable)
    (proc / "32").mkdir()  # a process whose stat cannot be read at all
    (proc / "32" / "stat").mkdir()
    assert any(w.identity is None for w in rc.live_processes([repo], T0, {20}, proc_root=proc))
    empty = tmp_path / "noproc"
    empty.mkdir()
    assert [w.label for w in rc.live_processes([repo], T0, set(), proc_root=empty)] == ["process table unreadable"]
    monkeypatch.setattr(rc.os, "getuid", lambda: 4242)  # every process belongs to another user
    assert rc.live_processes([repo], T0, set(), proc_root=proc) == []


def test_live_containers_fail_closed_except_for_an_absent_daemon(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(rc.shutil, "which", lambda tool: f"/usr/bin/{tool}" if tool == "docker" else None)

    def runner(ps: Any, inspect: Any = None) -> Any:
        def run(cmd: list[str], **_kwargs: Any) -> Any:
            out = ps if cmd[1] == "ps" else inspect
            if isinstance(out, BaseException):
                raise out
            return subprocess.CompletedProcess(cmd, out[0], out[1], out[2] if len(out) > 2 else "")
        return run

    def labels(run: Any) -> list[tuple[str, bool, bool, bool]]:
        return [(w.label, w.identity is None, w.recent, w.inherited) for w in rc.live_containers(T0, run=run)]
    down = "Cannot connect to the Docker daemon at unix:///var/run/docker.sock. Is the docker daemon running?"
    assert [w.label for w in rc.live_containers(T0, run=runner((1, "", down)), shims=lambda: False)] == []
    # Live restore: the daemon is down but a container shim still runs, so containers may be running.
    assert [w.label for w in rc.live_containers(T0, run=runner((1, "", down)), shims=lambda: True)] == ["docker check failed"]
    assert labels(runner((1, "", "permission denied while trying to connect"))) == [("docker check failed", True, True, False)]
    assert labels(runner((0, ""))) == []
    rows = (f"aaa{'1' * 20} 2026-10-18T08:05:00.123456789Z null\n"
            "bbb 2026-10-17T08:05:00.1Z [\"e1\"]\n"
            "ccc 2026-10-18T09:59:59.5+02:00 []\n"
            "ddd 0001-garbage null\n")
    assert labels(runner((0, "aaa\nbbb\nccc\nddd\n"), (0, rows))) == [
        ("docker container aaa111111111", False, True, False),
        ("docker container bbb", False, False, True),        # an old container with an exec session
        ("docker container ccc", False, False, False),        # 07:59:59.5Z: half a second before the window
        ("docker container undatable", True, True, False)]
    assert labels(runner((0, "aaa\n"), (1, ""))) == [("docker check failed", True, True, False)]
    assert labels(runner(subprocess.TimeoutExpired("docker", 15))) == [("docker check timed out", True, True, False)]
    assert labels(runner(OSError("exec format error"))) == [("docker check failed", True, True, False)]


def test_container_shims_are_detected_for_any_user(tmp_path: Path) -> None:
    proc = fake_proc(tmp_path)
    add_proc(proc, 40, argv=["sleep"], cwd=tmp_path, started=T0)
    assert rc.container_shims(proc) is False
    add_proc(proc, 41, argv=["/usr/bin/containerd-shim-runc-v2"], cwd=tmp_path, started=T0)
    (proc / "41" / "comm").write_text("containerd-shim\n")
    assert rc.container_shims(proc) is True


def test_container_timestamps_keep_fractions_and_offsets() -> None:
    assert rc._container_ts("2026-10-18T08:00:00.999999999Z") == T0 + timedelta(microseconds=999999)
    assert rc._container_ts("2026-10-18T10:00:00+02:00") == T0
    assert rc._container_ts("garbage") is None


def test_task_notification_never_closes_command_level_detachment(tmp_path: Path) -> None:
    """A notification proves the launching shell ended, not the job it detached."""
    events = [tool_use("x", "Bash", command="npm run dev >/tmp/dev.log 2>&1 &", run_in_background=True),
              tool_result("x"),
              {"type": "system", "subtype": "task_started", "task_id": "t1", "tool_use_id": "x"},
              {"type": "system", "subtype": "task_notification", "task_id": "t1", "tool_use_id": "x",
               "status": "completed"}, *QUOTA]
    turn = write_turn(tmp_path / "s", events)
    assert [c.label for c in rc.classify_turn(turn).in_flight] == ["npm &"]
    plain = [tool_use("y", "Bash", command="python -m pytest -q", run_in_background=True), tool_result("y"),
             {"type": "system", "subtype": "task_started", "task_id": "t2", "tool_use_id": "y"},
             {"type": "system", "subtype": "task_notification", "task_id": "t2", "tool_use_id": "y",
              "status": "completed"}, *QUOTA]
    assert rc.classify_turn(write_turn(tmp_path / "s2", plain)).in_flight == []


# ---------------------------------------------------------------------------
# Slack outbound (Phase 2)


def test_render_accepts_only_allowlisted_validated_fields() -> None:
    assert rc.render("turn_failed", {"session": HEAD, "agent": "claude", "outcome": "quota", "action": "switch"})
    assert rc.render("turn_failed", {"session": HEAD, "agent": "claude", "outcome": "quota", "action": "switch",
                                     "detail": "raw transcript"}) is None
    assert rc.render("hold", {"session": "rm -rf /", "reason": "effects_uncertain", "attempt": "1"}) is None
    assert rc.render("master_advanced", {"sha": "ghp_abcdefghijklmnopqrstuvwxyz0123"}) is None
    assert rc.render("hold", {"session": HEAD, "reason": "free text reason", "attempt": "1"}) is None
    assert rc.render("not_an_event", {}) is None


@pytest.mark.parametrize("failure", ["raises", "error", "timeout"])
def test_webhook_failure_never_interrupts_supervision(tmp_path: Path, failure: str) -> None:
    def sender(_text: str) -> str | None:
        if failure == "raises":
            raise RuntimeError(SECRET_URL)
        return "http_500" if failure == "error" else "TimeoutError"
    env = Env(tmp_path, [("codex", CODEX_SUCCESS)], sender=sender)
    env.head(QUOTA)
    result, sup = env.run()
    assert result == "idle" and len(env.relay.launches) == 1
    assert sup.state["notify"]["failures"] >= 1
    assert SECRET_URL not in env.store.state_path.read_text()
    assert all(SECRET_URL not in line for line in env.logs)


def test_notifications_are_deduplicated_and_rate_limited() -> None:
    state = rc.default_state()
    sent: list[str] = []
    notifier = rc.Notifier(state, sender=lambda t: sent.append(t), log=lambda m: None, max_per_hour=3)
    for _ in range(3):
        notifier.send("turn_completed", T0, session=HEAD, agent="claude")
    assert len(sent) == 1
    for i in range(5):
        notifier.send("master_advanced", T0 + timedelta(minutes=i), sha=f"{i:07d}abc")
    assert len(sent) == 3 and state["notify"]["dropped"] >= 3
    notifier.send("master_advanced", T0 + timedelta(hours=2), sha="fffffff")
    assert len(sent) == 4


def test_failed_delivery_is_retried_at_most_once() -> None:
    state = rc.default_state()
    calls: list[str] = []
    notifier = rc.Notifier(state, sender=lambda t: calls.append(t) or "http_500", log=lambda m: None)
    notifier.send("turn_completed", T0, session=HEAD, agent="claude")
    assert state["notify"]["retry"] is not None
    notifier.retry_pending(T0 + timedelta(minutes=5))
    notifier.retry_pending(T0 + timedelta(minutes=10))
    assert len(calls) == 2 and state["notify"]["retry"] is None


def test_post_webhook_never_exposes_the_url(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    hook = tmp_path / "hook"
    hook.write_text(SECRET_URL + "\n")

    def boom(*_args: Any, **_kwargs: Any) -> Any:
        raise urllib.error.URLError(f"failed to reach {SECRET_URL}")
    monkeypatch.setattr(rc._WEBHOOK_OPENER, "open", boom)
    error = rc.post_webhook("hello", webhook_file=hook)
    assert error == "URLError" and SECRET_URL not in error

    def http_error(*_args: Any, **_kwargs: Any) -> Any:
        raise urllib.error.HTTPError(SECRET_URL, 404, "no_service", {}, None)  # type: ignore[arg-type]
    monkeypatch.setattr(rc._WEBHOOK_OPENER, "open", http_error)
    assert rc.post_webhook("hello", webhook_file=hook) == "http_404"
    hook.write_text("https://evil.example/collect")
    assert rc.post_webhook("hello", webhook_file=hook) == "webhook_invalid"
    assert rc.post_webhook("hello", webhook_file=tmp_path / "missing") == "webhook_missing"


@pytest.mark.parametrize(("url", "valid"), [
    (SECRET_URL, True), ("http://hooks.slack.com/services/T/B/x", False),
    ("https://hooks.slack.com.evil.example/services/T/B/x", False), ("https://hooks.slack.com:8443/services/T/B/x", False),
    ("https://u:p@hooks.slack.com/services/T/B/x", False), ("https://hooks.slack.com/@evil.example/services/x", False),
    ("https://hooks.slack.com/services/T/B/x?redirect=1", False), ("https://hooks.slack.com:bad/services/x", False),
])
def test_webhook_url_is_strictly_validated(url: str, valid: bool) -> None:
    assert rc._valid_webhook_url(url) is valid


def test_webhook_transport_rejects_redirects_and_ignores_proxies(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    handlers = {type(h) for h in rc._WEBHOOK_OPENER.handlers}
    assert rc._RejectRedirects in handlers and urllib.request.HTTPRedirectHandler not in handlers
    # The explicit empty ProxyHandler replaces the default environment-proxy handler and installs no proxy route.
    assert not any(isinstance(h, urllib.request.ProxyHandler) for h in rc._WEBHOOK_OPENER.handlers)
    request = urllib.request.Request(SECRET_URL, data=b"{}", method="POST")
    with pytest.raises(urllib.error.HTTPError) as excinfo:
        rc._RejectRedirects().redirect_request(request, None, 302, "Found", {}, "https://evil.example/x")
    assert excinfo.value.code == 302

    def redirected(*_args: Any, **_kwargs: Any) -> Any:
        raise urllib.error.HTTPError(SECRET_URL, 302, "redirect rejected", {}, None)  # type: ignore[arg-type]
    hook = tmp_path / "hook"
    hook.write_text(SECRET_URL)
    monkeypatch.setattr(rc._WEBHOOK_OPENER, "open", redirected)
    assert rc.post_webhook("hello", webhook_file=hook) == "http_302"


def test_world_readable_webhook_file_is_refused(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    hook = tmp_path / "hook"
    hook.write_text(SECRET_URL)
    os.chmod(hook, 0o644)
    monkeypatch.setattr(rc, "WEBHOOK_FILE", hook)
    assert rc.webhook_sender() is None
    os.chmod(hook, 0o600)
    assert rc.webhook_sender() is not None


def test_every_supervisor_message_is_template_only(tmp_path: Path) -> None:
    env = Env(tmp_path, [("codex", CODEX_SUCCESS)])
    env.head([tool_use("p", "Bash", command="git push https://user:pw@host/repo"), tool_result("p"), *QUOTA])
    env.run()
    assert env.sent
    for text in env.sent:
        assert "git push" not in text and "pw@" not in text and "/home" not in text
        for line in text.splitlines()[1:]:
            key, _, value = line.partition(": ")
            assert rc.FIELD_RULES[key.replace(" ", "_")](value)


def test_watch_notifies_repl_failures_once_and_master_merges(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    sessions = repo / ".agent-relay" / "sessions"
    write_turn(sessions / HEAD, QUOTA)
    write_turn(sessions / "20261018-070000-ababab", SUCCESS)
    write_turn(sessions / "20261018-075000-cdcdcd", EAI)
    state = rc.default_state()
    sent: list[str] = []
    notifier = rc.Notifier(state, sender=lambda t: sent.append(t), log=lambda m: None)
    now = datetime.now(UTC)
    master = iter([("a" * 40, None), ("b" * 40, "830")])
    rc.watch_once(state, notifier, repo, now, supervised={"20261018-075000-cdcdcd"}, master=lambda: next(master))
    rc.watch_once(state, notifier, repo, now, supervised=set(), master=lambda: next(master))
    failed = [t for t in sent if "REPL turn failed" in t]
    assert len(failed) == 1 and HEAD in failed[0]
    merged = [t for t in sent if "master advanced" in t]
    assert len(merged) == 1 and "pr: 830" in merged[0]


def test_watch_alerts_when_claude_repl_effective_mode_is_dont_ask(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    sessions = repo / ".agent-relay" / "sessions"
    write_turn(sessions / HEAD, [
        {"type": "system", "subtype": "init", "permissionMode": "dontAsk"}, *SUCCESS,
    ])
    write_turn(sessions / "20261018-070000-ababab", [
        {"type": "system", "subtype": "init", "permissionMode": "default"}, *SUCCESS,
    ])
    state = rc.default_state()
    sent: list[str] = []
    notifier = rc.Notifier(state, sender=lambda text: sent.append(text), log=lambda message: None)
    now = datetime.now(UTC)
    for _ in range(2):
        rc.watch_once(state, notifier, repo, now, supervised=set(), master=lambda: (None, None))
    alerts = [text for text in sent if "launched in dontAsk" in text]
    assert len(alerts) == 1 and HEAD in alerts[0]


# ---------------------------------------------------------------------------
# Regressions from the independent review of the first implementation head


def test_restart_with_dead_unfound_attempt_holds_even_when_repository_unchanged(tmp_path: Path) -> None:
    env = Env(tmp_path)
    env.head(QUOTA)
    _pending(env, "rc-20261018T080000Z-0badf00d", pid=4244)
    result, sup = env.run()
    assert result == "held" and sup.state["hold"]["reason"] == "attempt_unresolved"
    assert env.relay.launches == []


def test_nonce_lookup_ignores_sessions_that_merely_quote_it(tmp_path: Path) -> None:
    env = Env(tmp_path)
    env.head(QUOTA)
    nonce = "rc-20261018T080000Z-0ddba11e"
    _pending(env, nonce, pid=None)
    # The real attempt pushed and was cut off; a later session's prompt quotes the nonce and failed harmlessly.
    write_turn(env.relay.sessions_dir() / "20261018-080030-ffffff",
               [tool_use("x", "Bash", command="git push"), *CODEX_QUOTA], agent="codex",
               prompt=relay_prompt(f"[relay-continuity attempt {nonce}]\ntask"))
    write_turn(env.relay.sessions_dir() / "20261018-080500-aaaaab", EAI,
               prompt=relay_prompt(f"[relay-continuity attempt rc-20261018T080500Z-12345678]\nAudit of {nonce}:\n"
                                   f"[relay-continuity attempt {nonce}]"))
    assert env.relay.find_by_nonce(nonce, T0) == "20261018-080030-ffffff"
    result, sup = env.run()
    assert result == "held" and sup.state["hold"]["reason"] == "effects_uncertain"
    assert env.relay.launches == []


def test_nonce_lookup_refuses_ambiguous_matches(tmp_path: Path) -> None:
    env = Env(tmp_path)
    nonce = "rc-20261018T080000Z-abad1dea"
    for sid in ("20261018-080030-aaaaaa", "20261018-080040-bbbbbb"):
        write_turn(env.relay.sessions_dir() / sid, SUCCESS, prompt=relay_prompt(f"[relay-continuity attempt {nonce}]"))
    assert env.relay.find_by_nonce(nonce, T0) is None


@pytest.mark.parametrize("command", [
    "env git push origin HEAD", "env -i PATH=/bin git push", "awk 'BEGIN {system(\"git push\")}'",
    "awk '{print > \"out\"}' f", "curl -XPOST https://example.invalid", "curl -sSd@body https://example.invalid",
    "curl --request=DELETE https://example.invalid", "gh api repos/o/r/issues -ftitle=hello",
    "gh api -XPATCH repos/o/r", "gh api graphql -f query=q", "cat <<EOF > notes\n$(git push)\nEOF",
    "cat <<<x\ngh pr merge 1", "sed 's/a/b/e' f", "sed -n '/x/w out' f", "find . -fprint list",
])
def test_execution_capable_arguments_are_not_read_only(command: str) -> None:
    assert rc.classify_command(command)[0] != "read_only"


@pytest.mark.parametrize("command", [
    "env", "awk '{print $1}' f", "curl -sSL -o /dev/null https://example.invalid", "gh api repos/o/r",
    "cat <<'EOF'\n$(git push)\nEOF", "sed 's/x/error/' f", "sed -n 1,5p f",
])
def test_plain_reads_stay_read_only(command: str) -> None:
    assert rc.classify_command(command)[0] == "read_only"


def test_background_acknowledgement_is_not_completion(tmp_path: Path) -> None:
    bg_agent = tool_use("a", "Agent", subagent_type="general-purpose", run_in_background=True)
    child = tool_use("c", "Bash", command="git push")
    child["parent_tool_use_id"] = "a"
    # Real Claude stream-json shapes: tasks are keyed by task_id; only backgrounded ones stay open.
    started = {"type": "system", "subtype": "task_started", "task_id": "t-a", "tool_use_id": "a",
               "is_backgrounded": True, "task_type": "local_agent"}
    turn = write_turn(tmp_path / "s", [bg_agent, tool_result("a"), started, child, *QUOTA])
    report = rc.classify_turn(turn)
    assert {c.label for c in report.in_flight} == {"Agent &", "git push"}
    assert rc.gate(report, fingerprint_changed=None) == "effects_uncertain"
    done = write_turn(tmp_path / "t", [bg_agent, tool_result("a"), started,
                                       {"type": "system", "subtype": "task_notification", "task_id": "t-a",
                                        "tool_use_id": "a", "status": "completed"}, *QUOTA])
    assert rc.classify_turn(done).in_flight == []
    updated = write_turn(tmp_path / "v", [bg_agent, tool_result("a"), started,
                                          {"type": "system", "subtype": "task_updated", "task_id": "t-a",
                                           "patch": {"status": "killed"}}, *QUOTA])
    assert rc.classify_turn(updated).in_flight == []
    # A foreground task reports task_started too; its tool result completes it.
    fg = write_turn(tmp_path / "w", [tool_use("f", "Bash", command="./build.sh"),
                                     {"type": "system", "subtype": "task_started", "task_id": "t-f", "tool_use_id": "f",
                                      "is_backgrounded": False}, tool_result("f"), *QUOTA])
    assert rc.classify_turn(fg).in_flight == []
    # ... unless it was moved to the background while running.
    moved = write_turn(tmp_path / "x", [tool_use("f", "Bash", command="./build.sh"),
                                        {"type": "system", "subtype": "task_started", "task_id": "t-f", "tool_use_id": "f",
                                         "is_backgrounded": False},
                                        {"type": "system", "subtype": "task_updated", "task_id": "t-f",
                                         "patch": {"is_backgrounded": True}}, tool_result("f"), *QUOTA])
    assert [c.label for c in rc.classify_turn(moved).in_flight] == ["build.sh"]
    # A background shell job that was never reported finished is still running.
    shell = write_turn(tmp_path / "u", [tool_use("b", "Bash", command="./deploy.sh", run_in_background=True),
                                        tool_result("b"), *QUOTA])
    assert [c.label for c in rc.classify_turn(shell).in_flight] == ["deploy.sh &"]


def test_creating_permissions_after_an_absent_pin_holds(tmp_path: Path) -> None:
    env = Env(tmp_path, [("codex", CODEX_SUCCESS)])
    env.perm["v"] = None
    env.head(SUCCESS)
    assert env.run()[0] == "idle"
    env.perm["v"] = "perm-created"
    env.head(QUOTA, sid="20261018-090000-eeeeee")
    result, sup = env.run("20261018-090000-eeeeee")
    assert result == "held" and sup.state["hold"]["reason"] == "permissions_changed"
    assert env.relay.launches == []


def test_released_permission_hold_repins_the_reviewed_authority(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    env = Env(tmp_path, [("codex", CODEX_SUCCESS)])
    env.relay.readings = room(env, "codex")
    env.head(SUCCESS)
    assert env.run()[0] == "idle"
    env.perm["v"] = "perm-widened"
    env.head(QUOTA, sid="20261018-090000-eeeeee")
    assert env.run("20261018-090000-eeeeee")[0] == "held"
    monkeypatch.setenv("RELAY_CONTINUITY_DIR", str(env.store.root))
    monkeypatch.setattr(rc, "make_host", lambda repo: env.host)
    monkeypatch.setattr(rc, "repo_root", lambda: env.repo)
    assert rc.main(["release", "--note", "reviewed the new permissions"]) == 0
    assert env.run("20261018-090000-eeeeee")[0] == "idle"
    assert env.store.load()["permissions_digest"] == "perm-widened"


@pytest.mark.parametrize("events", [
    # A subagent's successful result after the coordinator's own failure decides nothing.
    [*QUOTA, {**claude_result("child ok"), "parent_tool_use_id": "p1"}],
    # Missing or null is_error is not success.
    [{"type": "result", "subtype": "success", "result": "x", "terminal_reason": "completed"}],
    [{"type": "result", "subtype": "success", "is_error": None, "result": "x", "terminal_reason": "completed"}],
    # An empty result without a completed reason is not success.
    [{"type": "result", "subtype": "success", "is_error": False, "result": "", "terminal_reason": None}],
])
def test_ambiguous_terminal_evidence_is_never_success(tmp_path: Path, events: list[Any]) -> None:
    assert rc.classify_turn(write_turn(tmp_path / "s", events)).outcome != "success"


def test_auth_diagnostics_without_terminal_hold_instead_of_retrying(tmp_path: Path) -> None:
    turn = write_turn(tmp_path / "s", [{"type": "system", "subtype": "init"}])
    assert rc.classify_turn(turn).outcome == "crash"
    assert rc.classify_turn(turn, diagnostics="Error: Invalid API key · Please run /login").outcome == "auth"
    (turn / "stderr.log").write_text("OAuth token has expired")
    assert rc.classify_turn(turn).outcome == "auth"

    class AuthRelay(FakeRelay):
        def finish(self, proc: FakeProc) -> Any:
            result = super().finish(proc)
            return rc.RunResult(result.session_id, 1, True, "401 Unauthorized: please run /login")
    env = Env(tmp_path / "e")
    env.relay = AuthRelay(env.repo, [("claude", [{"type": "system", "subtype": "init"}])])
    env.relay.clock = env.clock
    env.host.relay = env.relay
    env.head(EAI)
    result, sup = env.run()
    assert result == "held" and sup.state["hold"]["reason"] == "auth_failure"
    assert len(env.relay.launches) == 1


@pytest.mark.parametrize("drop", ["pending", "counters", "permissions_pinned"])
def test_structurally_incomplete_state_is_corrupt_not_repaired(tmp_path: Path, drop: str) -> None:
    env = Env(tmp_path, [("codex", CODEX_SUCCESS)])
    env.head(QUOTA)
    state = rc.default_state()
    state.update({"phase": "running", "head_session": HEAD, "chain": [HEAD]})
    del state[drop]
    env.store.root.mkdir(parents=True, exist_ok=True)
    env.store.state_path.write_text(json.dumps(state))
    result, _ = env.run()
    assert result == "held" and env.relay.launches == []
    assert any("state_corrupt" in text for text in env.sent)


def test_journal_launch_missing_from_state_holds(tmp_path: Path) -> None:
    env = Env(tmp_path, [("codex", CODEX_SUCCESS)])
    env.relay.readings = room(env, "codex")
    env.head(QUOTA)
    env.store.journal({"event": "launch", "nonce": "rc-20261018T075900Z-feedface", "agent": "codex"})
    result, sup = env.run()
    assert result == "held" and sup.state["hold"]["reason"] == "attempt_unresolved"
    assert env.relay.launches == []
    assert rc.unsettled_nonces(env.store.journal_path) == ["rc-20261018T075900Z-feedface"]


def test_release_with_drop_pending_settles_unaccounted_journal_attempts(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    env = Env(tmp_path, [("codex", CODEX_SUCCESS)])
    env.relay.readings = room(env, "codex")
    env.head(QUOTA)
    env.store.journal({"event": "launch", "nonce": "rc-20261018T075900Z-feedface", "agent": "codex"})
    assert env.run()[0] == "held"
    monkeypatch.setenv("RELAY_CONTINUITY_DIR", str(env.store.root))
    monkeypatch.setattr(rc, "make_host", lambda repo: env.host)
    monkeypatch.setattr(rc, "repo_root", lambda: env.repo)
    assert rc.main(["release", "--drop-pending", "--note", "checked: that attempt never ran"]) == 0
    assert rc.unsettled_nonces(env.store.journal_path) == []
    assert env.run()[0] == "idle" and [launch["agent"] for launch in env.relay.launches] == ["codex"]


def test_retried_delivery_counts_against_the_hourly_limit() -> None:
    state = rc.default_state()
    calls: list[str] = []
    outcomes = iter(["http_500", None, None])
    notifier = rc.Notifier(state, sender=lambda t: calls.append(t) or next(outcomes), log=lambda m: None, max_per_hour=1)
    notifier.send("turn_completed", T0, session=HEAD, agent="claude")  # fails, queued for one retry
    notifier.send("master_advanced", T0 + timedelta(minutes=1), sha="abcdef1")  # fills the hour
    notifier.retry_pending(T0 + timedelta(minutes=2))
    assert len(calls) == 2 and state["notify"]["dropped"] >= 1


def test_fixtures_carry_no_coordinator_narrative() -> None:
    placeholder = "<coordinator narrative removed from fixture>"
    for path in FIXTURES.glob("*/output.jsonl"):
        for line in path.read_text().splitlines():
            event = json.loads(line)
            if event.get("type") == "result" and event.get("is_error") is False:
                assert event.get("result") in (placeholder, ""), path
    for path in FIXTURES.glob("*/state.json"):
        summary = json.loads(path.read_text()).get("summary") or ""
        assert summary == placeholder or rc.classify_text(summary, None) != "unknown" or len(summary) < 40, path


# ---------------------------------------------------------------------------
# Regressions from the independent Gemini audit of the historical corpus


def test_turn_that_kept_the_previous_output_has_no_evidence_and_holds(tmp_path: Path) -> None:
    # Relay's "No response captured" turn keeps a byte-identical copy of the previous turn's output, while
    # the agent may have worked (and merged) for hours. It must never inherit the previous outcome.
    env = Env(tmp_path)
    session = env.relay.sessions_dir() / HEAD
    write_turn(session, QUOTA, number=1)
    second = write_turn(session, QUOTA, number=2)
    report = rc.classify_turn(second)
    assert (report.outcome, report.no_evidence, report.calls) == ("crash", True, [])
    assert rc.gate(report, fingerprint_changed=None) == "output_missing"
    result, sup = env.run()
    assert result == "held" and sup.state["hold"]["reason"] == "output_missing"
    assert env.relay.launches == []


@pytest.mark.parametrize("content", [None, ""])
def test_missing_or_empty_output_holds(tmp_path: Path, content: str | None) -> None:
    env = Env(tmp_path)
    turn = write_turn(env.relay.sessions_dir() / HEAD, [])
    if content is None:
        (turn / "output.jsonl").unlink()
    result, sup = env.run()
    assert result == "held" and sup.state["hold"]["reason"] == "output_missing"
    assert env.relay.launches == []


def test_spend_cap_that_survives_its_session_reset_becomes_a_manual_cap(tmp_path: Path) -> None:
    capped = [claude_result("You've hit your monthly spend limit · raise it at claude.ai/settings/usage · "
                            "your session limit resets 11:50pm (Europe/Rome)", error=True, status=429)]
    # Codex has no fresh reading, so the chain waits for Claude's printed reset and retries Claude, which
    # hits the same spend cap again (as in the 2026-09-24 corpus): that is a real cap, held for the maintainer.
    env = Env(tmp_path, [("claude", capped)])
    env.head(capped)
    result, sup = env.run()
    assert [launch["agent"] for launch in env.relay.launches] == ["claude"]
    assert result == "held" and sup.state["hold"]["reason"] == "no_provider_available"
    assert sup.state["cooldowns"]["claude"]["until"] is None
    assert sup.state["cooldowns"]["claude"]["reason"] == "spend_limit"


def test_success_clears_the_spend_cap_memory(tmp_path: Path) -> None:
    capped = [claude_result("You've hit your monthly spend limit · your session limit resets 11:50pm (Europe/Rome)",
                            error=True, status=429)]
    env = Env(tmp_path, [("claude", SUCCESS)])
    env.head(capped)
    result, sup = env.run()
    assert result == "idle" and sup.state["spend_caps"] == {}


def test_real_corpus_no_response_turn_shape() -> None:
    # The fixture pair is synthetic, but the rule mirrors corpus turns d31beb/turn-013 and bb14c2/turn-012.
    assert rc.same_output_as_previous_turn(FIXTURES / "claude_success") is False


def test_empty_reasonless_result_never_overrides_a_real_terminal(tmp_path: Path) -> None:
    artifact = {"type": "result", "subtype": "success", "is_error": False, "result": "", "terminal_reason": None}
    assert rc.classify_turn(write_turn(tmp_path / "a", [*EAI, artifact])).outcome == "transient"
    assert rc.classify_turn(write_turn(tmp_path / "b", [*QUOTA, artifact])).outcome == "quota"
    # Alone, it is still not success.
    assert rc.classify_turn(write_turn(tmp_path / "c", [artifact])).outcome == "unknown"



# ---------------------------------------------------------------------------
# Regressions from the second independent review


def test_unresolved_hold_is_durable_before_the_attempt_is_journalled_settled(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    env = Env(tmp_path, [None])
    env.head(EAI)
    real = env.store.journal

    def dies_on_settle(record: dict[str, Any]) -> None:
        if record.get("event") == "settle":
            raise SystemExit("killed between the hold and its settle record")
        real(record)
    monkeypatch.setattr(env.store, "journal", dies_on_settle)
    with pytest.raises(SystemExit):
        env.run()
    state = env.store.load()
    assert state["phase"] == "held" and state["hold"]["reason"] == "attempt_unresolved" and state["pending"] is None
    monkeypatch.setattr(env.store, "journal", real)
    assert env.run()[0] == "held" and len(env.relay.launches) == 1


def test_marker_quoted_later_in_another_task_is_not_the_attempt(tmp_path: Path) -> None:
    env = Env(tmp_path)
    env.head(QUOTA)
    nonce = "rc-20261018T080000Z-5eedf00d"
    _pending(env, nonce, pid=None)
    # The original session is gone; a maintainer audit prompt quotes the marker on a later line.
    write_turn(env.relay.sessions_dir() / "20261018-080500-aaaaab", SUCCESS,
               prompt=relay_prompt(f"Audit the earlier attempt.\n[relay-continuity attempt {nonce}]"))
    assert env.relay.find_by_nonce(nonce, T0) is None
    result, sup = env.run()
    assert result == "held" and sup.state["hold"]["reason"] == "attempt_unresolved"


@pytest.mark.parametrize("command", [
    "sed -e's/.*/git push/e' input", "sed --expression='s/.*/git push/e' input", "sed -ne 's/x/y/w out' f",
    "sed -f prog.sed f", "awk -f deploy.awk", "gawk -i inplace '{print}' f", "awk --file=deploy.awk",
])
def test_program_text_in_options_or_files_is_not_read_only(command: str) -> None:
    assert rc.classify_command(command)[0] != "read_only"


def test_killed_background_subagent_leaves_its_unanswered_calls_in_flight(tmp_path: Path) -> None:
    parent = tool_use("a", "Agent", subagent_type="general-purpose", run_in_background=True)
    child = tool_use("c", "Bash", command="git push")
    child["parent_tool_use_id"] = "a"
    turn = write_turn(tmp_path / "s", [
        parent, tool_result("a"),
        {"type": "system", "subtype": "task_started", "task_id": "t", "tool_use_id": "a", "is_backgrounded": True},
        child, {"type": "system", "subtype": "task_notification", "task_id": "t", "tool_use_id": "a", "status": "killed"},
        *QUOTA])
    report = rc.classify_turn(turn)
    assert [c.label for c in report.in_flight] == ["git push"]
    assert rc.gate(report, fingerprint_changed=None) == "effects_uncertain"


@pytest.mark.parametrize("windows", [None, [], [{}], [{"id": "s", "used_percent": "100"}], [{"id": "s", "used_percent": True}]])
def test_unusable_usage_windows_are_not_evidence_of_room(tmp_path: Path, windows: Any) -> None:
    env = Env(tmp_path, [("claude", SUCCESS)])
    env.relay.readings = lambda: {"codex": {"agent_key": "codex", "status": "ok", "as_of": rc.iso(env.clock.now()),
                                            "windows": windows}}
    env.head(QUOTA)
    result, _ = env.run()
    assert result == "idle" and [launch["agent"] for launch in env.relay.launches] == ["claude"]


def test_same_agent_retry_waits_for_that_agent(tmp_path: Path) -> None:
    # Codex hits a transient; a fresh reading then shows Codex briefly capped. The retry waits for Codex.
    codex_reset = T0 + timedelta(minutes=12)
    env = Env(tmp_path, [("codex", CODEX_SUCCESS)])
    env.relay.readings = room(env, "claude", exhausted={"codex": codex_reset})
    state = rc.default_state()
    state.update({"head_session": HEAD, "chain": [HEAD], "agent": "codex", "permissions_digest": "perm0",
                  "permissions_pinned": True, "last_switch_at": rc.iso(T0 - timedelta(hours=2))})
    env.store.save(state, T0)
    env.head(EAI, agent="codex")
    assert env.run()[0] == "idle"
    assert [launch["agent"] for launch in env.relay.launches] == ["codex"]
    assert env.relay.launches[0]["at"] >= codex_reset


SPEND_WITH_RESET = [claude_result("You've hit your monthly spend limit · your session limit resets 11:50pm (Europe/Rome)",
                                  error=True, status=429)]


def test_restart_does_not_escalate_the_same_spend_cap_turn(tmp_path: Path) -> None:
    env = Env(tmp_path)  # any Relay invocation fails the test
    env.head(SPEND_WITH_RESET)
    env.store.root.mkdir(parents=True, exist_ok=True)

    def stop_while_waiting(seconds: float) -> None:
        env.store.stop_path.write_text("now")  # the maintainer stops the supervisor during the wait
        env.clock.sleep(seconds)
    env.host.sleep = stop_while_waiting
    for _ in range(2):  # run, stop while waiting, restart on the same head turn, stop again
        assert env.run()[0] == "stopped"
        env.store.stop_path.unlink()
        cooldown = env.store.load()["cooldowns"]["claude"]
        assert cooldown["reason"] == "quota" and cooldown["until"] is not None
    assert env.relay.launches == []


def test_release_clearing_a_spend_cap_retries_the_agent(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    spend = [claude_result("You've hit your monthly spend limit", error=True, status=429)]
    env = Env(tmp_path, [("claude", SUCCESS)])
    env.head(spend)
    result, sup = env.run()
    assert result == "held" and sup.state["hold"]["reason"] == "no_provider_available"
    monkeypatch.setenv("RELAY_CONTINUITY_DIR", str(env.store.root))
    monkeypatch.setattr(rc, "make_host", lambda repo: env.host)
    monkeypatch.setattr(rc, "repo_root", lambda: env.repo)
    assert rc.main(["release", "--clear-cooldown", "claude", "--note", "spend cap raised"]) == 0
    result, sup = env.run()
    assert result == "idle" and [launch["agent"] for launch in env.relay.launches] == ["claude"]
    assert "claude" not in sup.state["cooldowns"]


def test_releasing_a_permissions_hold_does_not_waive_the_side_effect_gate(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    env = Env(tmp_path)  # any Relay invocation fails the test
    env.relay.readings = room(env, "codex")
    env.head(SUCCESS)
    assert env.run()[0] == "idle"
    env.perm["v"] = "perm-widened"
    sid = "20261018-090000-eeeeee"
    env.head([tool_use("x", "Bash", command="git push origin HEAD"), *QUOTA], sid=sid)
    result, sup = env.run(sid)
    assert result == "held" and sup.state["hold"]["reason"] == "permissions_changed"
    monkeypatch.setenv("RELAY_CONTINUITY_DIR", str(env.store.root))
    monkeypatch.setattr(rc, "make_host", lambda repo: env.host)
    monkeypatch.setattr(rc, "repo_root", lambda: env.repo)
    assert rc.main(["release", "--note", "reviewed the permissions change only"]) == 0
    result, sup = env.run(sid)
    assert result == "held" and sup.state["hold"]["reason"] == "effects_uncertain"
    assert env.relay.launches == []


def test_spend_cap_reported_after_its_printed_reset_is_a_spend_limit(tmp_path: Path) -> None:
    # Corpus 20260924-083444-1d5541/turn-004: still capped at 14:27 Rome with "resets 12:40pm".
    late = datetime(2026, 9, 24, 12, 27, 7, tzinfo=UTC)
    turn = write_turn(tmp_path / "s", [claude_result(
        "You've hit your monthly spend limit · raise it at claude.ai/settings/usage · your session limit resets "
        "12:40pm (Europe/Rome)", error=True, status=429)])
    assert rc.classify_turn(turn, ref=late).outcome == "spend_limit"
    assert rc.classify_turn(turn, ref=datetime(2026, 9, 24, 9, 28, tzinfo=UTC)).outcome == "quota"


# ---------------------------------------------------------------------------
# Regressions from the third independent review


@pytest.mark.parametrize(("command", "read_only"), [
    ("sed '1s/.*/git push/e' input", False), ("sed '/x/,/y/s/a/b/w out' f", False), ("sed '$e date' f", False),
    ("sed '2!s/a/b/e' f", False), ("awk 'BEGIN {cmd=\"git push\"; print \"\" | cmd}'", False),
    ("sed 's|a|b|g;s/c/d/' f", True), ("sed '2!d' f", True), ("sed 'y/abc/xyz/' f", True), ("sed '1a hello' f", True),
])
def test_sed_addresses_and_awk_pipes(command: str, read_only: bool) -> None:
    assert (rc.classify_command(command)[0] == "read_only") is read_only


def test_release_acknowledges_only_the_held_turn(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    env = Env(tmp_path)  # any Relay invocation fails the test
    session = env.relay.sessions_dir() / HEAD
    write_turn(session, [tool_use("p", "Bash", command="git push origin HEAD"), *QUOTA], number=1)
    result, sup = env.run()
    assert result == "held" and sup.state["hold"]["turn"] == f"{HEAD}/turn-001"
    # Meanwhile a manual REPL turn on the same session leaves an unanswered merge.
    write_turn(session, [tool_use("m", "Bash", command="gh pr merge 9 --merge"), *QUOTA], number=2)
    monkeypatch.setenv("RELAY_CONTINUITY_DIR", str(env.store.root))
    monkeypatch.setattr(rc, "make_host", lambda repo: env.host)
    monkeypatch.setattr(rc, "repo_root", lambda: env.repo)
    assert rc.main(["release", "--note", "the push from turn 1 landed"]) == 0
    result, sup = env.run()
    assert result == "held" and sup.state["hold"]["reason"] == "effects_uncertain"
    assert sup.state["hold"]["turn"] == f"{HEAD}/turn-002" and env.relay.launches == []


def test_waiting_keeps_the_completed_effects_record(tmp_path: Path) -> None:
    env = Env(tmp_path, [("claude", SUCCESS)])
    env.head([tool_use("c", "Bash", command="gh pr comment 5 --body done"), tool_result("c"), *QUOTA])
    assert env.run()[0] == "idle"
    task = env.relay.launches[0]["task"]
    assert "[external] gh pr comment" in task and "do not repeat them blindly" in task


def test_returned_session_without_turn_files_holds(tmp_path: Path) -> None:
    class NoTurns(FakeRelay):
        def finish(self, proc: FakeProc) -> Any:
            sid = "20261018-090909-ffffff"
            (self.sessions_dir() / sid).mkdir(parents=True)
            return rc.RunResult(sid, 0, True)
    env = Env(tmp_path)
    env.relay = NoTurns(env.repo, [("claude", SUCCESS)])
    env.relay.clock = env.clock
    env.host.relay = env.relay
    env.head(EAI)
    result, sup = env.run()
    assert result == "held" and sup.state["hold"]["reason"] == "output_missing"
    assert len(env.relay.launches) == 1


def test_manual_spend_cap_survives_restart_on_the_same_turn(tmp_path: Path) -> None:
    env = Env(tmp_path)  # any Relay invocation fails the test
    env.head(SPEND_WITH_RESET)
    state = rc.default_state()
    state.update({"head_session": HEAD, "chain": [HEAD], "agent": "claude", "permissions_digest": "perm0",
                  "permissions_pinned": True,
                  "cooldowns": {"claude": {"until": None, "source": "manual", "reason": "spend_limit", "since": rc.iso(T0)}},
                  "spend_caps": {"claude": {"turn": f"{HEAD}/turn-001", "at": rc.iso(T0)}}})
    env.store.save(state, T0)
    result, sup = env.run()
    assert result == "held" and sup.state["cooldowns"]["claude"]["until"] is None
    assert env.relay.launches == []


def test_releases_of_one_turn_accumulate(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    env = Env(tmp_path, [("claude", SUCCESS)])
    env.head([tool_use("p", "Bash", command="git push origin HEAD"),
              claude_result("Invalid API key · Please run /login", error=True, status=401)])
    monkeypatch.setenv("RELAY_CONTINUITY_DIR", str(env.store.root))
    monkeypatch.setattr(rc, "make_host", lambda repo: env.host)
    monkeypatch.setattr(rc, "repo_root", lambda: env.repo)
    result, sup = env.run()
    assert result == "held" and sup.state["hold"]["reason"] == "auth_failure"
    assert rc.main(["release", "--note", "logged in again"]) == 0
    result, sup = env.run()
    assert result == "held" and sup.state["hold"]["reason"] == "effects_uncertain"
    assert rc.main(["release", "--note", "the push landed"]) == 0
    result, sup = env.run()
    assert result == "idle" and [launch["agent"] for launch in env.relay.launches] == ["claude"]


def test_same_agent_wait_ignores_other_agents_expired_cooldowns(tmp_path: Path) -> None:
    codex_reset = T0 + timedelta(minutes=12)
    env = Env(tmp_path, [("codex", CODEX_SUCCESS)])
    env.relay.readings = room(env, "claude", exhausted={"codex": codex_reset})
    state = rc.default_state()
    state.update({"head_session": HEAD, "chain": [HEAD], "agent": "codex", "permissions_digest": "perm0",
                  "permissions_pinned": True, "last_switch_at": rc.iso(T0 - timedelta(hours=2)),
                  "cooldowns": {"claude": {"until": rc.iso(T0 - timedelta(hours=1)), "source": "message",
                                           "reason": "quota", "since": rc.iso(T0 - timedelta(hours=6))}}})
    env.store.save(state, T0)
    env.head(EAI, agent="codex")
    assert env.run()[0] == "idle"
    assert env.relay.launches[0]["agent"] == "codex"
    # No one-second wake/save spin on Claude's long-expired cooldown while Codex stays capped.
    assert sum(1 for seconds in env.clock.slept if seconds <= 1.0) <= 1
    assert env.relay.launches[0]["at"] >= codex_reset



# ---------------------------------------------------------------------------
# Regressions from the fourth independent review


def test_sed_transliteration_does_not_hide_a_following_command() -> None:
    assert rc.classify_command("sed 'y/a/b/;e git push' f")[0] != "read_only"
    assert rc.classify_command("sed 'y/a\\/b/xy/;p' f")[0] == "read_only"


def test_detached_job_in_a_compound_command_stays_in_flight(tmp_path: Path) -> None:
    command = "gh pr comment 5 --body started; nohup git push origin HEAD >/dev/null 2>&1 &"
    assert rc.classify_command(command) == ("external", "git push &")
    turn = write_turn(tmp_path / "s", [tool_use("x", "Bash", command=command), tool_result("x"), *QUOTA])
    report = rc.classify_turn(turn)
    assert [c.label for c in report.in_flight] == ["git push &"]
    assert rc.gate(report, fingerprint_changed=None) == "effects_uncertain"



# ---------------------------------------------------------------------------
# Regressions from the fifth independent review


@pytest.mark.parametrize(("command", "expected"), [
    ("bash -lc 'git push origin HEAD' >/tmp/push.log 2>&1 &", ("external", "git push &")),
    ("bash -lc 'echo hi' > out.txt", ("local_write", "bash > file")),
    ("bash -c 'ls; git push'", ("external", "git push")),
    ("bash -lc 'git status'", ("read_only", "git status")),
    ("bash -lc 'npm run dev >/tmp/dev.log 2>&1 &' ; python scripts/smoke_test.py", ("unknown", "npm &")),
])
def test_shell_wrappers_keep_the_outer_commands_effects(command: str, expected: tuple[str, str]) -> None:
    assert rc.classify_command(command) == expected


def test_inner_detachment_survives_a_worse_outer_command(tmp_path: Path) -> None:
    command = "bash -lc 'npm run dev >/tmp/dev.log 2>&1 &' ; python scripts/smoke_test.py"
    turn = write_turn(tmp_path / "s", [tool_use("x", "Bash", command=command), tool_result("x"), *QUOTA])
    assert [(c.label, c.detached) for c in rc.classify_turn(turn).in_flight] == [("npm &", True)]


@pytest.mark.parametrize("command", ["tmux new-session -d -s dev 'npm run dev'", "tmux send-keys -t dev 'make' Enter",
                                     "screen -dmS dev npm run dev", "tmux -L dev new-session -d -s web 'npm run dev'",
                                     "screen -d -m -S web npm run dev", "docker compose up -d", "docker run -d nginx",
                                     "docker start web", "podman-compose up --detach", "systemd-run --user npm run dev",
                                     "vite preview --background", "docker compose up --wait", "pm2 start server.js",
                                     "gunicorn -D app:app", "redis-server --daemonize yes",
                                     "docker compose -f compose.dev.yml restart backend",
                                     "docker run -dt -v \"$PWD:/work\" -w /work python:3.12 python -m pytest -q",
                                     "docker run -itd img", "docker compose -p dev -f c.yml up --detach"])
def test_terminal_multiplexer_launches_stay_in_flight(tmp_path: Path, command: str) -> None:
    turn = write_turn(tmp_path / "s", [tool_use("x", "Bash", command=command), tool_result("x"), *QUOTA])
    assert [c.detached for c in rc.classify_turn(turn).in_flight] == [True]


@pytest.mark.parametrize("command", ["tmux -L dev ls", "docker compose up", "docker run --rm img pytest",
                                     "docker compose logs -f", "docker compose -f compose.dev.yml build",
                                     "docker run --rm -it -v \"$PWD:/w\" img pytest", "docker ps -a"])
def test_attached_multiplexer_and_container_commands_are_not_detached(command: str) -> None:
    assert not rc.classify_command(command)[1].endswith(" &")


def test_detached_wrapped_push_stays_in_flight(tmp_path: Path) -> None:
    command = "bash -lc 'git push origin HEAD' >/tmp/push.log 2>&1 &"
    turn = write_turn(tmp_path / "s", [tool_use("x", "Bash", command=command), tool_result("x"), *QUOTA])
    assert [c.label for c in rc.classify_turn(turn).in_flight] == ["git push &"]


@pytest.mark.parametrize(("command", "kind"), [
    ('curl -fsSL "$SCHEMA_URL" -o frontend/openapi.json', "local_write"), ("curl -O https://example.invalid/f", "local_write"),
    ("curl --output=x https://example.invalid", "local_write"), ("wget https://example.invalid/f", "local_write"),
    ("curl -sS https://example.invalid", "read_only"), ("curl -sSo /dev/null https://example.invalid", "read_only"),
    ("wget -qO- https://example.invalid", "read_only"), ("wget --spider https://example.invalid", "read_only"),
    ("curl -XPOST -o out https://example.invalid", "external"),
])
def test_downloads_to_files_are_local_writes(command: str, kind: str) -> None:
    assert rc.classify_command(command)[0] == kind



@pytest.mark.parametrize(("command", "kind"), [
    ("> build.log", "local_write"), ("sort -o out.txt in.txt", "local_write"), ("uniq in.txt out.txt", "local_write"),
    ("sort in.txt", "read_only"), ("uniq -c in.txt", "read_only"),
    ("sort -uo names.txt names.txt", "local_write"), ("sort --output names.txt in.txt", "local_write"),
    ("sort -u in.txt", "read_only"), ("git diff --output=/tmp/review.patch HEAD~1 HEAD", "local_write"),
    ("git log -p --output /tmp/log.txt", "local_write"), ("git diff HEAD~1 HEAD", "read_only"),
    ("sed --in-place=.bak 's/old/new/g' config.txt", "local_write"), ("sed -Ei 's/old/new/g' config.txt", "local_write"),
    ("sed -E 's/old/new/' config.txt", "read_only"), ("xxd -r fixture.hex fixture.bin", "local_write"),
    ("xxd -l 16 file.bin", "read_only"), ("xxd -r -p in.hex", "read_only"),
])
def test_other_file_writing_forms(command: str, kind: str) -> None:
    assert rc.classify_command(command)[0] == kind


@pytest.mark.parametrize(("command", "kind"), [
    ('case "$suite" in backend) python -m pytest -q backend/tests ;; esac', "unknown"),
    ('case "$x" in a) echo hi ;; esac', "read_only"),
    ("git diff 1>/tmp/review.patch", "local_write"), ("git status 2>/tmp/status.err", "local_write"),
    ("gh pr checks 831 &>/tmp/checks.log", "local_write"), ("git status 2>>/tmp/err", "local_write"),
    ("git status 2>/dev/null", "read_only"), ("ls 2>&1", "read_only"), ("git log >&2", "read_only"),
    ("sed ':join;N;$!b join;w /tmp/joined.txt' input.txt", "unknown"), (r"sed ':a;N;$!ba;s/\n/ /g' f", "read_only"),
    ("git branch --set-upstream-to=origin/master", "local_write"), ("git branch --unset-upstream", "local_write"),
    ("git branch newfeature", "local_write"), ("git branch -a", "read_only"), ("git branch -vv", "read_only"),
    ("git branch --merged master", "read_only"), ("git reflog expire --expire=now --all", "local_write"),
    ("git reflog", "read_only"), ("git remote -v set-url origin https://example.invalid/r.git", "local_write"),
    ("git remote -v", "read_only"), ("git remote get-url origin", "read_only"),
    ("curl --config /tmp/backend-smoke.curl", "unknown"), ("curl -sK cfg", "unknown"),
    ("curl -s http://127.0.0.1:8000/health", "read_only"),
    ("wget -qO- -o /tmp/health.log http://127.0.0.1:8000/health", "local_write"), ("wget -qO- http://x", "read_only"),
    (r"tmux has-session -t dev \; send-keys -t dev 'python -m pytest -q' Enter", "unknown"),
    ("tmux source-file /tmp/dev.tmux", "unknown"), ("tmux new-s -d -s web 'npm run dev'", "unknown"),
    ("tmux ls", "read_only"), ("tmux list-windows -t dev", "read_only"),
    ("screen -S dev -X screen python -m pytest -q", "unknown"),
])
def test_review_10_write_and_launch_forms(command: str, kind: str) -> None:
    assert rc.classify_command(command)[0] == kind


# ---------------------------------------------------------------------------
# Spec 197: autonomous incident reconciliation of uncertain operations


NONCE_RE = r"\[relay-continuity attempt (rc-[0-9TZ]+-[0-9a-f]+)\]"


def diag_reply(*entries: tuple[str, str], commands: tuple[str, ...] = ("git log --oneline -5",),
               nonce: str | None = None, line: bool = True) -> Any:
    """A Codex diagnostic turn: read-only commands, then the verdict line for its own nonce."""
    def events(task: str) -> list[dict[str, Any]]:
        import re
        own = nonce or re.search(NONCE_RE, task).group(1)  # type: ignore[union-attr]
        verdict = {"nonce": own, "operations": [{"id": i, "verdict": v, "evidence": f"checked {i}"} for i, v in entries]}
        text = "Findings above.\n" + (f"RECONCILE-VERDICT {json.dumps(verdict)}" if line else "no verdict")
        items: list[dict[str, Any]] = [{"type": "thread.started"}]
        for k, cmd in enumerate(commands):
            items.append({"type": "item.completed", "item": {"id": f"c{k}", "type": "command_execution", "command": cmd}})
        items += [{"type": "item.completed", "item": {"id": "m", "type": "agent_message", "text": text}},
                  {"type": "turn.completed"}]
        return items
    return events


class FakeDiagnostic:
    """Read-only Codex runner double: each launch consumes one scripted reply and writes its transcript where
    the real runner would (`<control>/diagnostics/<nonce>/turns/turn-001`)."""

    def __init__(self, env: Env, script: list[Any]):
        self.env = env
        self.script = list(script)
        self.launches: list[dict[str, Any]] = []
        self.problem: str | None = None
        self.layout = rc.ReadOnlyCodex(env.repo, env.store.root)

    def preflight(self) -> str | None:
        return self.problem

    def start(self, nonce: str, prompt: str) -> FakeProc:
        if not self.script:
            raise AssertionError("unexpected diagnostic launch")
        self.launches.append({"nonce": nonce, "task": prompt, "at": self.env.clock.now()})
        self._current = (nonce, prompt, self.script.pop(0))
        return FakeProc(None)

    def finish(self, proc: FakeProc, nonce: str, timeout: float) -> str:
        _, prompt, events = self._current
        self.write(nonce, events(prompt) if callable(events) else events, prompt)
        return ""

    def write(self, nonce: str, events: list[dict[str, Any]], prompt: str = "diagnosis") -> None:
        write_turn(self.layout.root / nonce, events, agent="codex", prompt=prompt)

    def locate(self, nonce: str) -> Path | None:
        return self.layout.locate(nonce)

    def find_pid(self, nonce: str) -> int | None:
        return None


def reconciling(tmp_path: Path, script: list[Any], *, diag: list[Any] | None = None, probe: Any = None) -> Env:
    env = Env(tmp_path, script)
    env.reconcile = True
    env.relay.readings = room(env, "codex")
    env.host.probe = probe or (lambda call: None)
    env.host.evidence = lambda report: "### Worktrees\nworktree /r"
    env.diag = FakeDiagnostic(env, diag or [])  # type: ignore[attr-defined]
    env.host.diagnostic = env.diag  # type: ignore[attr-defined]
    return env


def journal(env: Env) -> list[dict[str, Any]]:
    return [json.loads(line) for line in env.store.journal_path.read_text().splitlines()]


def test_quota_with_a_probed_completed_push_hands_off_to_codex_without_repeating(tmp_path: Path) -> None:
    env = reconciling(tmp_path, [("codex", CODEX_SUCCESS)],
                      probe=lambda call: ("completed", "remote branch b is at the pushed commit abc"))
    env.head([IN_FLIGHT["git push"], *QUOTA])
    result, sup = env.run()
    assert result == "idle"
    assert [launch["agent"] for launch in env.relay.launches] == ["codex"]  # no diagnosis was needed
    task = env.relay.launches[0]["task"]
    assert "git push: COMPLETED: it took effect; do not repeat it" in task and "probe:" in task
    assert sup.state["cooldowns"]["claude"]["reason"] == "quota"
    settled = [r for r in journal(env) if r.get("event") == "reconcile"]
    assert settled[0]["result"] == "settled" and settled[0]["verdicts"][0]["verdict"] == "completed"
    assert any("JarvisOS continuity: uncertain operations settled" in e for e in env.events())
    assert sup.state["reconcile"] is None


def test_interrupted_completed_subagent_is_settled_by_a_codex_diagnosis_not_repeated(tmp_path: Path) -> None:
    env = reconciling(tmp_path, [("codex", CODEX_SUCCESS)], diag=[diag_reply(("x", "completed"))])
    env.head([IN_FLIGHT["subagent"], *QUOTA])
    result, sup = env.run()
    assert result == "idle"
    (diag,), (cont,) = env.diag.launches, env.relay.launches
    assert "Read-only incident diagnosis" in diag["task"] and "read-only sandbox" in diag["task"]
    assert "id `x`: [unknown] Agent" in diag["task"] and "### Worktrees" in diag["task"]
    assert cont["agent"] == "codex" and cont["parent"] == HEAD  # the diagnosis never becomes the chain head
    assert "Agent: COMPLETED" in cont["task"] and "diagnostic codex" in cont["task"]
    assert sup.state["diagnostics"] == [diag["nonce"]]
    assert sup.state["chain"] == [HEAD, "20261018-000001-bbbbbb"]
    events = [(r.get("event"), r.get("purpose")) for r in journal(env)]
    assert events.count(("launch", "diagnostic")) == 1 and events.count(("settle", "diagnostic")) == 1


def test_running_background_worker_is_awaited_and_never_duplicated(tmp_path: Path) -> None:
    worker = tool_use("x", "Bash", command="nohup ./scripts/lane.sh > lane.log &")
    env = reconciling(tmp_path, [("codex", CODEX_SUCCESS)], diag=[diag_reply(("x", "completed"))])
    env.head([worker, tool_result("x"), *QUOTA])
    checks = {"n": 0}

    def live_work(since: datetime) -> list[Any]:
        checks["n"] += 1
        running = checks["n"] <= 3
        launched_while_running.append(running and bool(env.relay.launches or env.diag.launches))
        return [work("proc:9:9:w", "process lane.sh")] if running else []
    launched_while_running: list[bool] = []
    env.host.live_work = live_work
    result, _ = env.run()
    assert result == "idle" and not any(launched_while_running)
    assert sum(env.clock.slept) >= 3 * env.limits.reconcile_poll  # waited for the worker to end
    assert len(env.diag.launches) == 1 and [launch["agent"] for launch in env.relay.launches] == ["codex"]


def test_worker_outliving_the_reconcile_bound_holds_without_launching(tmp_path: Path) -> None:
    env = reconciling(tmp_path, [])
    env.limits = rc.Limits(reconcile_wait=timedelta(minutes=20))
    env.head([tool_use("x", "Bash", command="nohup ./scripts/lane.sh &"), tool_result("x"), *QUOTA])
    env.host.live_work = lambda since: [work("proc:9:9:w", "process lane.sh")]
    result, sup = env.run()
    assert result == "held" and sup.state["hold"]["reason"] == "live_work"
    assert env.relay.launches == []


def test_definitely_unstarted_merge_is_resumed_safely(tmp_path: Path) -> None:
    env = reconciling(tmp_path, [("codex", CODEX_SUCCESS)],
                      probe=lambda call: ("not_started", "PR #1 is still open: the merge did not take effect"))
    env.head([IN_FLIGHT["gh pr merge"], *QUOTA])
    assert env.run()[0] == "idle"
    task = env.relay.launches[0]["task"]
    assert "gh pr merge: NOT STARTED: it did not take effect; perform it only if still required" in task
    assert "approval gates, review requirements and authority boundaries are exactly as before" in task


@pytest.mark.parametrize("verdict", ["not_started", "unresolved"])
def test_genuinely_ambiguous_external_effect_remains_held(tmp_path: Path, verdict: str) -> None:
    # A model alone can never establish that a PR comment was not posted.
    env = reconciling(tmp_path, [], diag=[diag_reply(("x", verdict))])
    env.head([tool_use("x", "Bash", command="gh pr comment 7 --body done"), *QUOTA])
    result, sup = env.run()
    assert result == "held" and sup.state["hold"]["reason"] == "reconcile_unresolved"
    assert len(env.diag.launches) == 1 and env.relay.launches == []  # no continuation
    assert sup.state["hold"]["turn"] == f"{HEAD}/turn-001"
    record = [r for r in journal(env) if r.get("event") == "reconcile"][-1]
    assert record["verdicts"][0]["verdict"] == "unresolved"
    result, _ = env.run()  # a reconciliation hold is never re-examined automatically
    assert result == "held" and len(env.diag.launches) == 1 and env.relay.launches == []


def test_local_write_not_started_from_a_diagnosis_is_admitted(tmp_path: Path) -> None:
    env = reconciling(tmp_path, [("codex", CODEX_SUCCESS)], diag=[diag_reply(("x", "not_started"))])
    env.head([tool_use("x", "Bash", command="cp a.py b.py"), *QUOTA])
    assert env.run()[0] == "idle"
    assert "cp: NOT STARTED" in env.relay.launches[0]["task"]


def _diag_pending(env: Env, nonce: str, pid: int | None) -> None:
    env.head([IN_FLIGHT["subagent"], *QUOTA])
    state = rc.default_state()
    state.update({"phase": "running", "head_session": HEAD, "chain": [HEAD], "agent": "claude",
                  "permissions_digest": "perm0", "permissions_pinned": True,
                  "reconcile": {"turn": f"{HEAD}/turn-001", "since": rc.iso(T0), "attempts": 1, "verdicts": {},
                                "diag": {"nonce": nonce, "agent": "codex", "parent": HEAD, "started_at": rc.iso(T0),
                                         "pid": pid, "pid_start": 42, "fingerprint": "fp0", "attempt": 1,
                                         "ops": ["x"]}}})
    env.store.save(state, T0)
    env.store.journal({"event": "launch", "purpose": "diagnostic", "nonce": nonce, "agent": "codex"})


def test_supervisor_restart_during_diagnosis_adopts_it_without_a_duplicate(tmp_path: Path) -> None:
    nonce = "rc-20261018T080000Z-0d1a9000"
    env = reconciling(tmp_path, [("codex", CODEX_SUCCESS)])
    _diag_pending(env, nonce, pid=4242)
    env.alive[4242] = 2
    env.relay.finish_pending = lambda: env.diag.write(nonce, diag_reply(("x", "completed"), nonce=nonce)(""))  # type: ignore[attr-defined]
    result, sup = env.run()
    assert result == "idle"
    assert env.diag.launches == [] and len(env.relay.launches) == 1
    assert "Agent: COMPLETED" in env.relay.launches[0]["task"]
    assert sup.state["diagnostics"] == [nonce]


def test_restart_with_a_lost_diagnosis_holds_and_never_relaunches(tmp_path: Path) -> None:
    env = reconciling(tmp_path, [])
    _diag_pending(env, "rc-20261018T080000Z-0d1a9001", pid=4243)  # dead, and no transcript carries its nonce
    result, sup = env.run()
    assert result == "held" and sup.state["hold"]["reason"] == "attempt_unresolved"
    assert env.relay.launches == [] and env.diag.launches == []
    assert env.run()[0] == "held" and env.diag.launches == []


def test_diagnosis_past_its_time_bound_is_terminated_on_restart(tmp_path: Path) -> None:
    env = reconciling(tmp_path, [])
    _diag_pending(env, "rc-20261018T080000Z-0d1a9002", pid=4244)
    env.clock.t = T0 + env.limits.reconcile_timeout + timedelta(seconds=1)
    killed: list[int] = []
    env.alive[4244] = 3
    env.relay.finish_pending = lambda: None  # type: ignore[attr-defined]
    env.host.terminate = killed.append
    result, _ = env.run()
    assert killed == [4244] and result == "held" and env.relay.launches == []


def test_insufficient_permissions_are_reported_not_bypassed(tmp_path: Path) -> None:
    env = reconciling(tmp_path, [], diag=[diag_reply(("x", "insufficient_permissions"))])
    env.head([IN_FLIGHT["subagent"], *QUOTA])
    result, sup = env.run()
    assert result == "held" and sup.state["hold"]["reason"] == "reconcile_insufficient_permissions"
    assert len(env.diag.launches) == 1 and env.relay.launches == []
    assert any("reconcile_insufficient_permissions" in text for text in env.sent)
    # A refused probe is reported the same way, with no diagnosis at all.
    env2 = reconciling(tmp_path / "b", [], probe=lambda call: ("insufficient_permissions", "`gh pr view` was refused"))
    env2.head([IN_FLIGHT["gh pr merge"], *QUOTA])
    assert env2.run()[0] == "held" and env2.store.load()["hold"]["reason"] == "reconcile_insufficient_permissions"
    assert env2.relay.launches == [] and env2.diag.launches == []


@pytest.mark.parametrize("violation", ["write", "fingerprint"])
def test_a_diagnosis_that_is_not_read_only_is_void(tmp_path: Path, violation: str) -> None:
    # Defence in depth behind the sandbox: a recorded write attempt or a moved repository voids the findings.
    commands = ("git log", "git commit -am fix") if violation == "write" else ("git log",)
    env = reconciling(tmp_path, [], diag=[diag_reply(("x", "completed"), commands=commands)])
    env.head([IN_FLIGHT["subagent"], *QUOTA])
    if violation == "fingerprint":
        env.host.fingerprint = lambda: "fp-after" if env.diag.launches else "fp0"
    result, sup = env.run()
    assert result == "held" and sup.state["hold"]["reason"] == "reconcile_failed"
    assert len(env.diag.launches) == 1 and env.relay.launches == []


def test_diagnosis_without_a_verdict_is_retried_within_its_bound_then_holds(tmp_path: Path) -> None:
    env = reconciling(tmp_path, [], diag=[diag_reply(("x", "completed"), line=False),
                                          diag_reply(("x", "completed"), nonce="rc-other")])
    env.head([IN_FLIGHT["subagent"], *QUOTA])
    result, sup = env.run()
    assert result == "held" and sup.state["hold"]["reason"] == "reconcile_failed"
    assert len(env.diag.launches) == env.limits.reconcile_attempts == 2 and env.relay.launches == []


def test_a_stale_codex_reading_does_not_block_the_diagnosis(tmp_path: Path) -> None:
    # The 2026-10-19 commissioning shape: Relay refreshes Codex's reading only when Codex runs, so an idle host
    # shows a reading hours old. Waiting for a fresh one would wait until `max_wait`; the diagnosis runs instead.
    env = reconciling(tmp_path, [("codex", CODEX_SUCCESS)], diag=[diag_reply(("x", "completed"))])

    def readings() -> dict[str, Any]:
        now = env.clock.now()
        if env.diag.launches:  # Codex has run: its reading is fresh again
            return {"codex": reading("codex", 5, now + timedelta(hours=5), now)}
        return {"codex": reading("codex", 88, T0 - timedelta(hours=1), T0 - timedelta(hours=5))}
    env.relay.readings = readings
    env.head([IN_FLIGHT["subagent"], *QUOTA])
    result, sup = env.run()
    assert result == "idle"
    (diag,) = env.diag.launches
    assert diag["at"] - T0 < timedelta(minutes=1)  # no wait for a reading that would never come
    assert [launch["agent"] for launch in env.relay.launches] == ["codex"]
    assert [r["result"] for r in journal(env) if r.get("event") == "reconcile"] == ["settled"]


def test_the_diagnosis_prompt_names_the_verifiable_commands_and_forbids_inline_interpreters() -> None:
    # Commissioning 2026-10-19: Codex parsed the transcript with `python3 -` heredocs, which the classifier
    # cannot verify as read-only, voiding an otherwise sound diagnosis. The prompt now says so up front.
    report = rc.TurnReport(outcome="quota", agent="claude", detail="")
    text = rc.diagnostic_prompt(report, [], "")
    assert "Use only these commands" in text and "`jq`" in text
    assert "Do not run any other interpreter or script" in text and "`python3 -`" in text
    assert "run.log" in text  # where a background launch leaves its traces


def test_an_unconfirmed_codex_that_keeps_losing_to_quota_is_bounded_then_held(tmp_path: Path) -> None:
    env = reconciling(tmp_path, [], diag=[CODEX_QUOTA] * 7)
    env.relay.readings = None  # never a fresh reading: each try is lost to quota and waits for the reported reset
    env.head([IN_FLIGHT["subagent"], *QUOTA])
    result, sup = env.run()
    assert result == "held" and sup.state["hold"]["reason"] == "reconcile_failed"
    assert len(env.diag.launches) == env.limits.reconcile_provider_failures + 1 and env.relay.launches == []
    gaps = [b["at"] - a["at"] for a, b in zip(env.diag.launches, env.diag.launches[1:], strict=False)]
    assert all(gap >= timedelta(minutes=1) for gap in gaps)  # each retry waited for Codex's reported reset
    assert max(env.clock.slept) <= 5.0  # interruptible sleeps against the clock


def test_a_held_uncertain_turn_is_reexamined_from_evidence_on_the_next_run(tmp_path: Path) -> None:
    # The 2026-10-18 incident shape: Claude quota with an operation in flight, held by spec 195.
    env = Env(tmp_path, [("codex", CODEX_SUCCESS)])
    env.relay.readings = room(env, "codex")
    env.head([IN_FLIGHT["git push"], *QUOTA])
    assert env.run()[0] == "held" and env.store.load()["hold"]["reason"] == "effects_uncertain"
    env.reconcile = True
    env.host.probe = lambda call: ("completed", "remote branch b is at the pushed commit abc")
    result, sup = env.run()
    assert result == "idle" and [launch["agent"] for launch in env.relay.launches] == ["codex"]
    assert any(r.get("event") == "reconcile_resume" for r in journal(env))


def test_reexamination_keeps_the_hold_when_the_chain_moved(tmp_path: Path) -> None:
    env = reconciling(tmp_path, [], probe=lambda call: ("completed", "x"))
    env.head([IN_FLIGHT["git push"], *QUOTA])
    state = rc.default_state()
    state.update({"phase": "held", "head_session": HEAD, "chain": [HEAD], "permissions_digest": "perm0",
                  "permissions_pinned": True,
                  "hold": {"reason": "effects_uncertain", "at": rc.iso(T0), "attempt": None, "turn": f"{HEAD}/turn-000"}})
    env.store.save(state, T0)
    result, sup = env.run()
    assert result == "held" and sup.state["hold"]["turn"] == f"{HEAD}/turn-000" and env.relay.launches == []


@pytest.mark.parametrize("reason", ["live_work", "auth_failure", "attempt_unresolved", "reconcile_unresolved"])
def test_other_holds_are_never_released_by_reconciliation(tmp_path: Path, reason: str) -> None:
    env = reconciling(tmp_path, [], probe=lambda call: ("completed", "x"))
    env.head([IN_FLIGHT["git push"], *QUOTA])
    state = rc.default_state()
    state.update({"phase": "held", "head_session": HEAD, "chain": [HEAD],
                  "hold": {"reason": reason, "at": rc.iso(T0), "attempt": None, "turn": f"{HEAD}/turn-001"}})
    env.store.save(state, T0)
    assert env.run()[0] == "held" and env.relay.launches == []


def test_state_written_before_reconciliation_still_loads(tmp_path: Path) -> None:
    store = rc.Store(tmp_path)
    state = rc.default_state()
    assert "reconcile" not in state and "diagnostics" not in state
    store.save(state, T0)
    assert store.load()["phase"] == "idle"
    state["reconcile"] = {"turn": "s/t", "since": rc.iso(T0), "attempts": "1", "verdicts": {}, "diag": None}
    store.save(state, T0)
    with pytest.raises(rc.StateCorrupt):
        store.load()


def test_verdict_parsing_is_strict() -> None:
    ops = [rc.ToolCall("a", "Bash", "external", "gh pr comment", False), rc.ToolCall("b", "Agent", "unknown", "Agent", False)]
    line = 'RECONCILE-VERDICT {"nonce": "n1", "operations": [{"id": "a", "verdict": "completed", "evidence": "comment 9 exists"}]}'
    assert rc.parse_verdicts(f"text\n{line}", "n1", ops) == {"a": ("completed", "comment 9 exists"),
                                                            "b": ("unresolved", "not covered by the diagnosis")}
    assert rc.parse_verdicts(line, "n2", ops) is None
    assert rc.parse_verdicts(f"{line}\n{line}", "n1", ops) is None
    assert rc.parse_verdicts(line.replace("completed", "done"), "n1", ops) is None
    assert rc.parse_verdicts(line.replace('"a"', '"zz"'), "n1", ops) is None
    secret = line.replace("comment 9 exists", "token ghp_abcdefghijklmnopqrstuvwxyz0123")
    assert rc.parse_verdicts(secret, "n1", ops)["a"] == ("unresolved", "the diagnosis gave no usable evidence")
    assert rc.admit(ops[0], "not_started", "e")[0] == "unresolved"
    assert rc.admit(ops[0], "completed", "e") == ("completed", "e")
    assert rc.admit(rc.ToolCall("c", "Edit", "local_write", "Edit a.py", False), "not_started", "e")[0] == "not_started"


def fake_runner(responses: dict[str, tuple[int, str]]) -> Any:
    calls: list[list[str]] = []

    def run(args: list[str], cwd: Path | None = None, timeout: float = 20.0) -> tuple[int | None, str]:
        calls.append(args)
        for key, value in responses.items():
            if key in " ".join(args):
                return value
        return 1, "unexpected"
    run.calls = calls  # type: ignore[attr-defined]
    return run


def bash(command: str) -> Any:
    return rc._claude_call({"id": "x", "name": "Bash", "input": {"command": command}})


@pytest.mark.parametrize(("command", "responses", "expected"), [
    ("cd /r && git push origin feat", {"show-ref": (0, ""), "rev-parse --verify": (0, "a" * 40 + "\n"),
                                       "ls-remote": (0, f"{'a' * 40}\trefs/heads/feat\n")}, "completed"),
    ("cd /wt && git push -u origin HEAD:feat 2>&1", {"abbrev-ref HEAD": (0, "feat"), "rev-parse --verify": (0, "a" * 40),
                                                     "ls-remote": (0, "")}, "not_started"),
    ("git push origin feat", {"show-ref": (0, ""), "rev-parse --verify": (0, "a" * 40),
                              "ls-remote": (0, f"{'b' * 40}\trefs/heads/feat"), "merge-base": (0, "")}, "not_started"),
    ("git push origin feat", {"show-ref": (0, ""), "rev-parse --verify": (0, "a" * 40),
                              "ls-remote": (0, f"{'b' * 40}\trefs/heads/feat"), "merge-base": (1, "")}, None),
    ("git push --force origin feat", {"show-ref": (0, ""), "rev-parse --verify": (0, "a" * 40), "ls-remote": (0, "")}, None),
    ("git push origin feat", {"show-ref": (0, ""), "rev-parse --verify": (0, "a" * 40),
                              "ls-remote": (128, "fatal: Authentication failed")}, "insufficient_permissions"),
    # Review 1: the agent's working directory persists across calls, so HEAD/upstream are unknown without a cd.
    ("git push", {"abbrev-ref": (0, "origin/master"), "rev-parse --verify": (0, "a" * 40),
                  "ls-remote": (0, f"{'a' * 40}\trefs/heads/master")}, None),
    ("git push origin HEAD", {"abbrev-ref HEAD": (0, "master"), "rev-parse --verify": (0, "a" * 40),
                              "ls-remote": (0, f"{'a' * 40}\trefs/heads/master")}, None),
    ("cd wt && git push origin feat", {}, None),
    # Review 2: a tag (or any non-branch) push is never probed as a branch.
    ("git push origin v1", {"show-ref": (1, ""), "rev-parse --verify": (0, "a" * 40), "ls-remote": (0, "")}, None),
    ("git push origin refs/tags/v1", {}, None),
    ("git push --tags origin", {}, None),
    ("git push origin feat && gh pr create --fill", {}, None),  # two effectful steps: only a diagnosis can tell
    ("git push origin $BRANCH", {}, None),
    ("gh pr merge 12 --squash", {"pr view 12": (0, '{"number": 12, "state": "MERGED"}')}, "completed"),
    ("gh pr merge 12 --squash", {"pr view 12": (0, '{"number": 12, "state": "OPEN"}')}, "not_started"),
    ("gh pr merge 12 --auto --squash", {}, None),
    ("gh pr merge -m 42", {"pr view 42": (0, '{"number": 42, "state": "MERGED"}')}, "completed"),  # -m is --merge
    ("gh pr merge -r --delete-branch", {"pr view": (0, '{"number": 7, "state": "MERGED"}')}, None),  # target unknown
    ("gh pr create --head feat --fill", {"pr list": (0, '[{"number": 2, "state": "MERGED"}]')}, None),
    ("gh pr create --fill", {}, None),
    ("gh pr merge 12", {"pr view 12": (1, "HTTP 401: Bad credentials (gh auth login)")}, "insufficient_permissions"),
    ("gh pr create --head feat --fill", {"pr list": (0, '[{"number": 3, "state": "OPEN"}]')}, "completed"),
    ("gh pr create --head feat --fill", {"pr list": (0, "[]")}, "not_started"),
    ("gh pr comment 3 --body hi", {}, None),
    ("./deploy.sh", {}, None),
])
def test_deterministic_probes(command: str, responses: dict[str, tuple[int, str]], expected: str | None) -> None:
    run = fake_runner(responses)
    probed = rc.probe_call(bash(command), Path("/r"), run)
    assert (probed[0] if probed else None) == expected
    for args in run.calls:  # probes only read
        assert (args[3] if args[:2] == ["git", "-C"] else " ".join(args[1:3])) in (
            "rev-parse", "ls-remote", "merge-base", "show-ref", "pr view", "pr list")


def test_file_probes(tmp_path: Path) -> None:
    target = tmp_path / "a.py"
    edit = rc._claude_call({"id": "e", "name": "Edit", "input": {"file_path": str(target), "old_string": "x = 1",
                                                                  "new_string": "x = 2"}})
    write = rc._claude_call({"id": "w", "name": "Write", "input": {"file_path": str(target), "content": "x = 2\n"}})
    assert rc.probe_call(write, tmp_path)[0] == "not_started"
    target.write_text("x = 1\n")
    assert rc.probe_call(edit, tmp_path)[0] == "not_started"
    assert rc.probe_call(write, tmp_path) is None
    target.write_text("x = 2\n")
    assert rc.probe_call(edit, tmp_path)[0] == "completed" and rc.probe_call(write, tmp_path)[0] == "completed"
    assert "content" not in json.dumps(rc.TurnReport("crash", "claude", "", calls=[write]).to_json())


def test_evidence_bundle_drops_secret_lines(tmp_path: Path) -> None:
    run = fake_runner({"worktree list": (0, "worktree /r\nghp_abcdefghijklmnopqrstuvwxyz0123"),
                       "ls-remote": (128, "fatal: could not read Username")})
    report = rc.TurnReport("quota", "claude", "x", turn_id=f"{HEAD}/turn-006")
    text = rc.collect_evidence(tmp_path, report, run)
    assert "worktree /r" in text and "ghp_" not in text and "turn-006/output.jsonl" in text
    assert "(unavailable: fatal: could not read Username)" in text


def test_operation_still_running_remotely_is_rechecked_then_held_within_bounds(tmp_path: Path) -> None:
    env = reconciling(tmp_path, [], diag=[diag_reply(("x", "running")), diag_reply(("x", "running"))])
    env.head([IN_FLIGHT["subagent"], *QUOTA])
    result, sup = env.run()
    assert result == "held" and sup.state["hold"]["reason"] == "reconcile_unresolved"
    assert len(env.diag.launches) == 2 and sum(env.clock.slept) >= env.limits.reconcile_poll


def test_running_then_completed_continues_once(tmp_path: Path) -> None:
    env = reconciling(tmp_path, [("codex", CODEX_SUCCESS)],
                      diag=[diag_reply(("x", "running")), diag_reply(("x", "completed"))])
    env.head([IN_FLIGHT["subagent"], *QUOTA])
    assert env.run()[0] == "idle" and len(env.diag.launches) == 2 and len(env.relay.launches) == 1


def test_reexamination_never_rewrites_a_held_chain_for_another_session(tmp_path: Path) -> None:
    env = Env(tmp_path, [])
    env.head([IN_FLIGHT["git push"], *QUOTA])
    assert env.run()[0] == "held"
    before = env.store.load()
    env.reconcile = True
    env.host.probe = lambda call: ("completed", "x")
    env.head(SUCCESS, sid="20261018-090000-ffffff")
    result, sup = env.run("20261018-090000-ffffff")
    assert result == "held" and env.relay.launches == []
    after = env.store.load()
    assert after["hold"] == before["hold"] and after["chain"] == before["chain"] == [HEAD]


def test_repeated_reexamination_is_quiet_and_not_a_new_failure(tmp_path: Path) -> None:
    # A truncated stream after a repository change holds `effects_uncertain` with nothing to reconcile: each
    # re-examination reaches the same hold, which is neither re-announced nor counted as a new failure.
    env = reconciling(tmp_path, [])
    env.head([tool_use("r", "Read", file_path="/x"), tool_result("r")])
    state = rc.default_state()
    state.update({"phase": "held", "head_session": HEAD, "chain": [HEAD], "permissions_digest": "perm0",
                  "permissions_pinned": True, "counters": {"consecutive_failures": 1, "transient_streak": 0,
                                                           "crash_retries": 0},
                  "last_attempt": {"nonce": "rc-1", "agent": "claude", "attempt": 1, "fingerprint": "fp-before"},
                  "hold": {"reason": "effects_uncertain", "at": rc.iso(T0), "attempt": 1, "turn": f"{HEAD}/turn-001"}})
    env.store.save(state, T0)
    for _ in range(3):
        assert env.run()[0] == "held"
    state = env.store.load()
    assert state["hold"]["reason"] == "effects_uncertain" and env.relay.launches == []
    assert state["counters"]["consecutive_failures"] == 1
    assert not any("HOLD" in text for text in env.sent)


def test_moved_chain_hold_is_not_reexamined_again(tmp_path: Path) -> None:
    env = reconciling(tmp_path, [], probe=lambda call: ("completed", "x"))
    env.head([IN_FLIGHT["git push"], *QUOTA])
    state = rc.default_state()
    state.update({"phase": "held", "head_session": HEAD, "chain": [HEAD], "permissions_digest": "perm0",
                  "permissions_pinned": True,
                  "hold": {"reason": "effects_uncertain", "at": rc.iso(T0), "attempt": None, "turn": f"{HEAD}/turn-000"}})
    env.store.save(state, T0)
    assert env.run()[0] == "held" and env.store.load()["hold"]["resumable"] is False
    resumes = sum(r.get("event") == "reconcile_resume" for r in journal(env))
    assert env.run()[0] == "held" and sum(r.get("event") == "reconcile_resume" for r in journal(env)) == resumes


def test_claude_is_never_the_diagnostic_agent(tmp_path: Path) -> None:
    env = reconciling(tmp_path, [("claude", SUCCESS)], diag=[diag_reply(("x", "completed"))])
    env.relay.readings = room(env, "claude")  # only Claude has room; Codex is unconfirmed
    env.head([IN_FLIGHT["subagent"], *EAI])
    result, sup = env.run()
    assert result == "idle" and len(env.diag.launches) == 1  # the read-only Codex runner, not Relay
    assert [launch["agent"] for launch in env.relay.launches] == ["claude"]  # Claude only continues the chain
    assert not any("RECONCILE-VERDICT" in launch["task"] for launch in env.relay.launches)


def test_waived_gate_settles_an_abandoned_diagnosis(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    env = reconciling(tmp_path, [("codex", CODEX_SUCCESS)])
    _diag_pending(env, "rc-20261018T080000Z-0d1a9003", pid=None)
    state = env.store.load()
    state.update({"phase": "held", "hold": {"reason": "reconcile_failed", "at": rc.iso(T0), "attempt": 1,
                                            "turn": f"{HEAD}/turn-001"}})
    env.store.save(state, T0)
    monkeypatch.setenv("RELAY_CONTINUITY_DIR", str(env.store.root))
    monkeypatch.setattr(rc, "make_host", lambda repo: env.host)
    monkeypatch.setattr(rc, "repo_root", lambda: env.repo)
    assert rc.main(["release", "--note", "checked the diagnosis session by hand; nothing ran"]) == 0
    assert env.run()[0] == "idle" and len(env.relay.launches) == 1
    assert rc.unsettled_nonces(env.store.journal_path) == []
    assert env.run()[0] == "idle"



# ---------------------------------------------------------------------------
# Spec 197 review wave 2: durable provider wait and pre-execution read-only enforcement


def test_codex_quota_during_reconciliation_waits_for_the_reported_reset_then_diagnoses_once(tmp_path: Path) -> None:
    env = reconciling(tmp_path, [("codex", CODEX_SUCCESS)], diag=[diag_reply(("x", "completed"))])
    reset = T0 + timedelta(hours=3)
    env.relay.readings = room(env, exhausted={"codex": reset, "claude": T0 + timedelta(hours=6)})
    env.head([IN_FLIGHT["subagent"], *QUOTA])
    result, sup = env.run()
    assert result == "idle"
    (diag,) = env.diag.launches
    assert reset <= diag["at"] <= reset + timedelta(minutes=1)  # woke at the provider-reported reset
    assert [launch["agent"] for launch in env.relay.launches] == ["codex"] and env.relay.launches[0]["at"] >= reset
    assert any("waiting for codex" in line for line in env.logs)
    assert any("no coordinator provider available" in e for e in env.events())


def test_diagnosis_lost_to_codex_quota_is_retried_after_reset_without_using_an_attempt(tmp_path: Path) -> None:
    env = reconciling(tmp_path, [("codex", CODEX_SUCCESS)], diag=[CODEX_QUOTA, diag_reply(("x", "completed"))])
    reset = T0 + timedelta(hours=2)

    def readings() -> dict[str, Any]:
        now = env.clock.now()
        capped = env.diag.launches and now < reset
        return {"codex": reading("codex", 100 if capped else 5, reset if capped else now + timedelta(hours=5), now),
                "claude": reading("claude", 100, T0 + timedelta(hours=8), now)}
    env.relay.readings = readings
    env.head([IN_FLIGHT["subagent"], *QUOTA])
    assert env.run()[0] == "idle"
    first, second = env.diag.launches
    assert second["at"] >= reset and first["nonce"] != second["nonce"]
    assert len(env.relay.launches) == 1


def test_restart_during_the_provider_wait_resumes_it_without_a_duplicate(tmp_path: Path) -> None:
    env = reconciling(tmp_path, [("codex", CODEX_SUCCESS)], diag=[diag_reply(("x", "completed"))])
    reset = T0 + timedelta(hours=3)
    env.relay.readings = room(env, exhausted={"codex": reset, "claude": T0 + timedelta(hours=6)})
    env.head([IN_FLIGHT["subagent"], *QUOTA])

    def stop_during_wait(seconds: float) -> None:  # the machine goes down while the supervisor sleeps
        env.store.stop_path.write_text("x")
        env.clock.sleep(seconds)
    env.host.sleep = stop_during_wait
    assert env.run()[0] == "stopped"
    saved = env.store.load()["reconcile"]
    assert saved["waiting_since"] == rc.iso(T0) and saved["wake_at"] == rc.iso(reset) and env.diag.launches == []
    env.store.stop_path.unlink()
    env.host.sleep = env.clock.sleep
    assert env.run()[0] == "idle"
    assert len(env.diag.launches) == 1 and env.diag.launches[0]["at"] >= reset and len(env.relay.launches) == 1


def test_codex_spend_cap_during_reconciliation_holds_for_the_maintainer(tmp_path: Path) -> None:
    env = reconciling(tmp_path, [], diag=[[{"type": "thread.started"},
                                          {"type": "turn.failed", "error": {"message": "credit balance is too low"}}]])
    env.head([IN_FLIGHT["subagent"], *QUOTA])
    result, sup = env.run()
    assert result == "held" and sup.state["hold"]["reason"] == "no_provider_available"
    assert len(env.diag.launches) == 1 and env.relay.launches == []


def test_codex_authentication_failure_in_a_diagnosis_holds(tmp_path: Path) -> None:
    env = reconciling(tmp_path, [], diag=[[{"type": "thread.started"},
                                          {"type": "turn.failed", "error": {"message": "401 Unauthorized: please run /login"}}]])
    env.head([IN_FLIGHT["subagent"], *QUOTA])
    result, sup = env.run()
    assert result == "held" and sup.state["hold"]["reason"] == "auth_failure" and env.relay.launches == []


def test_provider_lost_diagnoses_are_bounded(tmp_path: Path) -> None:
    eai = [{"type": "thread.started"}, {"type": "turn.failed", "error": {"message": "stream disconnected EAI_AGAIN"}}]
    env = reconciling(tmp_path, [], diag=[eai] * 7)
    env.head([IN_FLIGHT["subagent"], *QUOTA])
    result, sup = env.run()
    assert result == "held" and sup.state["hold"]["reason"] == "reconcile_failed"
    assert len(env.diag.launches) == env.limits.reconcile_provider_failures + 1


@pytest.mark.parametrize("problem", ["codex is not installed", "codex read-only sandbox did not block a write"])
def test_no_diagnosis_runs_without_a_verified_read_only_sandbox(tmp_path: Path, problem: str) -> None:
    env = reconciling(tmp_path, [], diag=[diag_reply(("x", "completed"))])
    env.diag.problem = problem
    env.head([IN_FLIGHT["subagent"], *QUOTA])
    result, sup = env.run()
    assert result == "held" and sup.state["hold"]["reason"] == "reconcile_no_sandbox"
    assert env.diag.launches == [] and env.relay.launches == []
    env2 = reconciling(tmp_path / "b", [])
    env2.host.diagnostic = None
    env2.head([IN_FLIGHT["subagent"], *QUOTA])
    assert env2.run()[0] == "held" and env2.store.load()["hold"]["reason"] == "reconcile_no_sandbox"


FAKE_CODEX = """#!/bin/sh
# Test double for the codex CLI: records its argv and stdin, behaves per $FAKE_CODEX_MODE.
printf '%s\n' "$@" > "$FAKE_CODEX_LOG.argv"
if [ "$1" = exec ] && [ "$2" = --help ]; then
  echo "--sandbox <SANDBOX_MODE> [possible values: read-only, workspace-write] --ignore-user-config --ignore-rules"
  echo "--ephemeral --json --output-last-message"
  exit 0
fi
if [ "$1" = sandbox ]; then
  shift; while [ "$1" != -- ]; do shift; done; shift
  if [ "$FAKE_CODEX_MODE" = leaky ]; then exec "$@"; fi
  echo READONLY-OK; exit 0
fi
cat > "$FAKE_CODEX_LOG.stdin"
last=""; prev=""
for a in "$@"; do [ "$prev" = -o ] && last="$a"; prev="$a"; done
echo '{"type":"thread.started"}'
echo '{"type":"turn.completed"}'
printf 'RECONCILE-VERDICT {}\n' > "$last"
"""


@pytest.fixture
def fake_codex(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    binary = tmp_path / "bin" / "codex"
    binary.parent.mkdir()
    binary.write_text(FAKE_CODEX)
    binary.chmod(0o755)
    monkeypatch.setenv("FAKE_CODEX_LOG", str(tmp_path / "codex"))
    return binary


def test_read_only_codex_launch_enforces_the_sandbox_before_execution(tmp_path: Path, fake_codex: Path) -> None:
    repo = tmp_path / "repo"
    (repo / ".git").mkdir(parents=True)
    runner = rc.ReadOnlyCodex(repo, tmp_path / "control", binary=str(fake_codex))
    assert runner.preflight() is None
    proc = runner.start("rc-1", "diagnose this")
    runner.finish(proc, "rc-1", 30)
    argv = (tmp_path / "codex.argv").read_text().splitlines()
    assert argv[:3] == ["exec", "--sandbox", "read-only"]
    for required in ("--ignore-user-config", "--ignore-rules", "--ephemeral", "--json", 'approval_policy="never"',
                     "mcp_servers={}"):
        assert required in argv
    assert not any("dangerously" in a or a in ("--full-auto", "--approve-for-me", "--add-dir") for a in argv)
    assert argv[-1] == "-" and (tmp_path / "codex.stdin").read_text() == "diagnose this"
    turn = runner.locate("rc-1")
    assert turn is not None and rc.classify_turn(turn).outcome == "success"
    assert rc.final_text(turn).startswith("RECONCILE-VERDICT")
    with pytest.raises(FileExistsError):
        runner.start("rc-1", "again")  # a nonce is launched at most once


def test_preflight_refuses_a_sandbox_that_lets_a_write_through(tmp_path: Path, fake_codex: Path,
                                                                monkeypatch: pytest.MonkeyPatch) -> None:
    repo = tmp_path / "repo"
    (repo / ".git").mkdir(parents=True)
    monkeypatch.setenv("FAKE_CODEX_MODE", "leaky")
    runner = rc.ReadOnlyCodex(repo, tmp_path / "control", binary=str(fake_codex))
    assert runner.preflight() == "codex read-only sandbox did not block a write"
    assert not list(runner.root.glob(".canary-*"))
    assert rc.ReadOnlyCodex(repo, tmp_path / "c2", binary=str(tmp_path / "missing")).preflight() == "codex is not installed"


def test_diagnosis_is_found_by_nonce_after_a_restart_before_its_pid_was_recorded(tmp_path: Path) -> None:
    runner = rc.ReadOnlyCodex(tmp_path, tmp_path / "control")
    proc_root = tmp_path / "proc"
    (proc_root / "77").mkdir(parents=True)
    (proc_root / "77" / "cmdline").write_bytes(b"codex\0exec\0-o\0" + str(runner.turn_dir("rc-9") / "last-message.txt").encode())
    assert runner.find_pid("rc-9", proc_root) == 77 and runner.find_pid("rc-8", proc_root) is None


@pytest.mark.skipif(not os.environ.get("RELAY_CONTINUITY_CODEX"), reason="real codex CLI not configured")
def test_real_codex_read_only_sandbox_blocks_writes(tmp_path: Path) -> None:
    """Host evidence: set RELAY_CONTINUITY_CODEX to the codex binary to prove this machine's sandbox."""
    repo = tmp_path / "repo"
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    assert rc.ReadOnlyCodex(repo, tmp_path / "control").preflight() is None


# ---------------------------------------------------------------------------
# Spec 201: durable missions and the persistent owner

DIRECTIVE = "L20261020085928-0431"


def mission_def(*texts: str, checks: dict[int, dict[str, Any]] | None = None, session: str | None = None,
                mid: str = "m-20261018T075500Z-abc123", submitted: datetime = T0 - timedelta(minutes=5)) -> dict[str, Any]:
    tasks = [{"text": t, **({"check": checks[i]} if checks and i in checks else {})} for i, t in enumerate(texts)]
    return {"schema": rc.MISSION_SCHEMA, "id": mid, "authority": DIRECTIVE, "tasks": tasks,
            "submitted_at": rc.iso(submitted), "session": session, "repo": "/repo"}


def start_mission(env: Env, mission: dict[str, Any]) -> None:
    state = rc.default_state()
    state["mission"] = {"id": mission["id"], "next": 0, "total": len(mission["tasks"]), "done": []}
    env.store.save(state, T0)


def run_mission(env: Env, mission: dict[str, Any], session: str | None = None) -> tuple[str, Any]:
    sup = env.supervisor()
    sup.mission = mission
    return sup.run(session), sup


def journal_events(store: Any) -> list[str]:
    return [json.loads(line)["event"] for line in store.journal_path.read_text().splitlines()]


def test_mission_validation_rejects_unsafe_definitions() -> None:
    assert rc.validate_mission(mission_def("a", checks={0: {"kind": "pr_merged", "pr": 846}})) is None
    assert rc.validate_mission(mission_def("a", checks={0: {"kind": "path_exists", "path": "docs/x.md"}})) is None
    bad = [
        {**mission_def("a"), "authority": "maintainer said so"},
        {**mission_def("a"), "id": "m-1"},
        {**mission_def("a"), "tasks": []},
        mission_def(*["t"] * (rc.MAX_TASKS + 1)),
        mission_def("x" * (rc.MAX_TASK_CHARS + 1)),
        mission_def("use token ghp_" + "a" * 36),
        mission_def("a", checks={0: {"kind": "shell", "cmd": "true"}}),
        mission_def("a", checks={0: {"kind": "path_exists", "path": "/etc/passwd"}}),
        mission_def("a", checks={0: {"kind": "path_exists", "path": "../outside"}}),
        mission_def("a", checks={0: {"kind": "pr_merged", "pr": True}}),
        {**mission_def("a"), "tasks": [{"text": "a", "agent": "codex"}]},
    ]
    assert [n for n, m in enumerate(bad) if rc.validate_mission(m) is None] == []


def test_mission_advances_each_task_only_on_success_and_completes(tmp_path: Path) -> None:
    env = Env(tmp_path, [("claude", SUCCESS), ("claude", SUCCESS), ("claude", SUCCESS)])
    mission = mission_def("first task", "second task", "third task")
    start_mission(env, mission)
    result, sup = run_mission(env, mission)
    assert result == "idle"
    launches = env.relay.launches
    assert [launch["parent"] for launch in launches] == [None, "20261018-000001-bbbbbb", "20261018-000002-bbbbbb"]
    for n, (launch, text) in enumerate(zip(launches, ("first task", "second task", "third task"), strict=True), 1):
        assert f"task {n}/3" in launch["task"] and launch["task"].endswith(f"{rc.MISSION_HEADER}\n{text}")
        assert DIRECTIVE in launch["task"] and "devctx.py recover" in launch["task"]
    rec = sup.state["mission"]
    assert rec["next"] == 3 and rec["completed_at"] and [d["task"] for d in rec["done"]] == [0, 1, 2]
    assert journal_events(env.store).count("task_completed") == 3 and "mission_completed" in journal_events(env.store)
    assert sup.state["phase"] == "idle"
    assert sum("mission task completed" in e for e in env.events()) == 3
    assert any("mission completed" in e for e in env.events())
    assert not any("awaiting maintainer" in e for e in env.events())


def test_mission_quota_fails_over_to_codex_with_task_context_and_continues(tmp_path: Path) -> None:
    env = Env(tmp_path, [("claude", SUCCESS), ("claude", QUOTA), ("codex", CODEX_SUCCESS), ("codex", CODEX_SUCCESS)])
    env.relay.readings = room(env, "codex")
    mission = mission_def("first task", "second task", "third task")
    start_mission(env, mission)
    result, sup = run_mission(env, mission)
    assert result == "idle"
    assert [launch["agent"] for launch in env.relay.launches] == ["claude", "claude", "codex", "codex"]
    takeover = env.relay.launches[2]["task"]
    assert "grants no new authority" in takeover  # the spec 195 recovery prompt, not a fresh task
    assert takeover.endswith(f"task 2/3, which has not been recorded complete:\n{rc.MISSION_HEADER}\nsecond task")
    done = sup.state["mission"]["done"]
    assert [(d["task"], d["agent"]) for d in done] == [(0, "claude"), (1, "codex"), (2, "codex")]
    assert sup.state["cooldowns"]["claude"]["reason"] == "quota"
    assert any("provider switched" in e for e in env.events())


def test_mission_refreshes_stale_codex_quota_once_before_fallback(tmp_path: Path) -> None:
    env = Env(tmp_path, [("claude", QUOTA), ("codex", CODEX_SUCCESS)])
    env.relay.readings = room(env, "claude")  # no fresh Codex reading on an idle host
    probes: list[str] = []

    def refresh() -> None:
        probes.append("read-only")
        env.relay.readings = room(env, "claude", "codex")

    env.host.refresh_codex_quota = refresh
    mission = mission_def("one task")
    start_mission(env, mission)
    result, sup = run_mission(env, mission)
    assert result == "idle" and probes == ["read-only"]
    assert [launch["agent"] for launch in env.relay.launches] == ["claude", "codex"]
    assert sup.state["mission"]["done"][0]["agent"] == "codex"


def test_mission_returns_to_claude_after_its_reset_and_dwell(tmp_path: Path) -> None:
    env = Env(tmp_path)

    reset = T0 + timedelta(hours=14)

    def codex_until_after_reset(_task: str) -> list[dict[str, Any]]:
        reported_reset = rc.parse_ts(env.store.load()["cooldowns"]["claude"]["until"])
        assert reported_reset is not None
        env.clock.t = reported_reset + timedelta(minutes=30)  # the codex task outlasted Claude's reported reset
        return CODEX_SUCCESS
    env.relay.script = [("claude", QUOTA), ("codex", codex_until_after_reset), ("claude", SUCCESS)]
    exhausted, fresh = room(env, "codex", exhausted={"claude": reset}), room(env, "codex", "claude")
    env.relay.readings = lambda: exhausted() if env.relay.launches else fresh()  # claude runs out during task 1
    mission = mission_def("first task", "second task")
    start_mission(env, mission)
    result, sup = run_mission(env, mission)
    assert result == "idle"
    assert [launch["agent"] for launch in env.relay.launches] == ["claude", "codex", "claude"]
    assert [(d["task"], d["agent"]) for d in sup.state["mission"]["done"]] == [(0, "codex"), (1, "claude")]
    assert "claude" not in sup.state["cooldowns"]


def test_mission_restart_adopts_running_attempt_and_continues_remaining_tasks(tmp_path: Path) -> None:
    env = Env(tmp_path, [("claude", SUCCESS)])
    mission = mission_def("first task", "second task")
    env.head(SUCCESS)  # task 1's session
    nonce = "rc-20261018T080000Z-0badf00d"
    state = rc.default_state()
    state.update({"phase": "running", "head_session": HEAD, "chain": [HEAD], "agent": "codex", "permissions_digest": "perm0",
                  "permissions_pinned": True,
                  "mission": {"id": mission["id"], "next": 1, "total": 2,
                              "done": [{"task": 0, "session": HEAD, "agent": "claude", "at": rc.iso(T0)}]},
                  "pending": {"nonce": nonce, "agent": "codex", "parent": HEAD, "started_at": rc.iso(T0), "pid": 4242,
                              "pid_start": 42, "fingerprint": "fp0", "attempt": 1, "task": 1}})
    env.store.save(state, T0)
    env.store.journal({"event": "launch", "nonce": nonce})
    env.alive[4242] = 2

    def finish_pending() -> None:
        write_turn(env.relay.sessions_dir() / "20261018-080100-cccccc", CODEX_SUCCESS, agent="codex",
                   prompt=relay_prompt(f"[relay-continuity attempt {nonce}]"))
    env.relay.finish_pending = finish_pending  # type: ignore[attr-defined]
    result, sup = run_mission(env, mission, HEAD)
    assert result == "idle"
    assert env.relay.launches == []  # the adopted attempt was never relaunched, and it was the last task
    assert sup.state["mission"]["next"] == 2 and sup.state["mission"]["done"][-1]["session"] == "20261018-080100-cccccc"
    assert sup.state["mission"]["completed_at"]


def test_mission_crash_while_settling_success_adopts_instead_of_relaunching(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    env = Env(tmp_path)
    mission = mission_def("one task")
    start_mission(env, mission)
    nonce = "rc-20261018T080000Z-0badf00d"
    pending = {"nonce": nonce, "agent": "claude", "parent": None, "started_at": rc.iso(T0),
               "pid": None, "pid_start": None, "fingerprint": "fp0", "attempt": 1, "task": 0}
    state = env.store.load()
    state["pending"] = pending
    env.store.save(state, T0)
    session = "20261018-080100-cccccc"
    write_turn(env.relay.sessions_dir() / session, SUCCESS, agent="claude",
               prompt=relay_prompt(f"[relay-continuity attempt {nonce}]"))
    sup = env.supervisor()
    sup.mission = mission
    sup.state = env.store.load()

    def crash_before_progress(*_: Any) -> None:
        raise RuntimeError("simulated process death")

    monkeypatch.setattr(sup, "_advance", crash_before_progress)
    with pytest.raises(RuntimeError, match="simulated process death"):
        sup._settle(pending, session)
    assert env.store.load()["pending"]["nonce"] == nonce

    result, restarted = run_mission(env, mission)
    assert result == "idle"
    assert env.relay.launches == []
    assert restarted.state["mission"]["next"] == 1
    assert restarted.state["mission"]["completed_at"]


def test_mission_restart_with_unsettled_journal_launch_holds(tmp_path: Path) -> None:
    env = Env(tmp_path)
    mission = mission_def("first task")
    start_mission(env, mission)
    env.store.journal({"event": "launch", "nonce": "rc-20261018T075900Z-feedface"})  # launched; state lost it
    result, sup = run_mission(env, mission)
    assert result == "held" and sup.state["hold"]["reason"] == "attempt_unresolved"
    assert env.relay.launches == [] and sup.state["mission"]["next"] == 0


def test_mission_uncertain_external_effect_holds_without_advancing(tmp_path: Path) -> None:
    env = Env(tmp_path, [("claude", SUCCESS), ("claude", [tool_use("p", "Bash", command="git push origin x"), *QUOTA])])
    env.relay.readings = room(env, "codex")
    mission = mission_def("first task", "second task", "third task")
    start_mission(env, mission)
    result, sup = run_mission(env, mission)
    assert result == "held" and sup.state["hold"]["reason"] == "effects_uncertain"
    assert sup.state["mission"]["next"] == 1 and len(env.relay.launches) == 2
    assert "mission_completed" not in journal_events(env.store)


def test_mission_task_check_must_pass_before_advancing(tmp_path: Path) -> None:
    env = Env(tmp_path, [("claude", SUCCESS)])
    seen: list[dict[str, Any]] = []
    env.host.task_check = lambda check: seen.append(check) or "PR #846 is OPEN"
    mission = mission_def("merge 846", "next", checks={0: {"kind": "pr_merged", "pr": 846}})
    start_mission(env, mission)
    result, sup = run_mission(env, mission)
    assert result == "held" and sup.state["hold"]["reason"] == "task_check_failed"
    assert seen == [{"kind": "pr_merged", "pr": 846}] and sup.state["mission"]["next"] == 0
    assert len(env.relay.launches) == 1 and "task_check_failed" in journal_events(env.store)


def test_check_task_is_read_only_and_bounded_to_the_repository(tmp_path: Path) -> None:
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "x.md").write_text("x")
    assert rc.check_task(tmp_path, {"kind": "path_exists", "path": "docs/x.md"}) is None
    assert rc.check_task(tmp_path, {"kind": "path_exists", "path": "docs/y.md"})
    calls: list[list[str]] = []

    def gh(args: list[str], **_: Any) -> tuple[int, str]:
        calls.append(args)
        return 0, "MERGED\n"
    assert rc.check_task(tmp_path, {"kind": "pr_merged", "pr": 846}, run=gh) is None
    assert calls == [["gh", "pr", "view", "846", "--json", "state", "-q", ".state"]]
    assert rc.check_task(tmp_path, {"kind": "pr_merged", "pr": 846}, run=lambda *a, **k: (0, "OPEN")) == "PR #846 is OPEN"
    assert rc.check_task(tmp_path, {"kind": "pr_merged", "pr": 846}, run=lambda *a, **k: (1, ""))


def _write_mission(root: Path, mission: dict[str, Any]) -> None:
    rc.write_json_atomic(rc.missions_dir(root) / f"{mission['id']}.json", mission)


def test_serve_step_runs_missions_one_at_a_time_in_submission_order(tmp_path: Path) -> None:
    env = Env(tmp_path, [("claude", SUCCESS), ("claude", SUCCESS)])
    root = tmp_path / "control"
    first = mission_def("first mission", mid="m-20261018T070000Z-aaaaaa", submitted=T0 - timedelta(hours=1))
    second = mission_def("second mission", mid="m-20261018T060000Z-bbbbbb", submitted=T0 - timedelta(minutes=30))
    _write_mission(root, second)
    _write_mission(root, first)  # file names sort the other way: order is by submission time
    factory = lambda store, mission: rc.Supervisor(store, env.host, env.limits, sender=env.sender)  # noqa: E731
    assert rc.serve_step(root, factory, conflicts=lambda: [], now=env.clock.now) == f"ran:{first['id']}:idle"
    assert "first mission" in env.relay.launches[0]["task"]
    assert rc.serve_step(root, factory, conflicts=lambda: [], now=env.clock.now) == f"ran:{second['id']}:idle"
    assert "second mission" in env.relay.launches[1]["task"]
    assert rc.serve_step(root, factory, conflicts=lambda: [], now=env.clock.now) == "empty"
    assert journal_events(rc.mission_store(root, first["id"]))[0] == "mission_started"


def test_serve_step_waits_for_a_live_repl_and_a_held_mission_blocks_the_queue(tmp_path: Path) -> None:
    env = Env(tmp_path)
    root = tmp_path / "control"
    held = mission_def("held one", mid="m-20261018T070000Z-aaaaaa", submitted=T0 - timedelta(hours=1))
    later = mission_def("later one", mid="m-20261018T070100Z-bbbbbb", submitted=T0 - timedelta(minutes=30))
    _write_mission(root, held)
    _write_mission(root, later)
    factory = lambda store, mission: rc.Supervisor(store, env.host, env.limits)  # noqa: E731
    assert rc.serve_step(root, factory, conflicts=lambda: ["repl_active"]) == f"waiting:{held['id']}:repl_active"
    assert env.relay.launches == []
    store = rc.mission_store(root, held["id"])
    state = rc.default_state()
    state.update({"phase": "held", "hold": {"reason": "effects_uncertain", "at": rc.iso(T0), "attempt": 1, "turn": "x"},
                  "mission": {"id": held["id"], "next": 0, "total": 1, "done": []}})
    store.save(state, T0)
    assert rc.serve_step(root, factory, conflicts=lambda: []) == f"held:{held['id']}"
    assert env.relay.launches == []
    busy = rc.Lock(root / "supervisor.lock")
    assert busy.acquire()
    try:
        assert rc.serve_step(root, factory, conflicts=lambda: []) == "busy"
    finally:
        busy.release()


def test_serve_step_holds_on_a_corrupt_earlier_mission(tmp_path: Path) -> None:
    root = tmp_path / "control"
    first = mission_def("first", mid="m-20261018T070000Z-aaaaaa", submitted=T0 - timedelta(hours=1))
    later = mission_def("later", mid="m-20261018T070100Z-bbbbbb", submitted=T0 - timedelta(minutes=30))
    _write_mission(root, first)
    _write_mission(root, later)
    first_path = rc.missions_dir(root) / f"{first['id']}.json"
    first_path.write_text("{")
    assert rc.serve_step(root, lambda *_: pytest.fail("should not execute"), conflicts=lambda: []) == f"corrupt:{first['id']}"
    first_path.write_text(json.dumps(first))
    state = rc.default_state()
    state["mission"] = {"id": first["id"], "next": 0, "total": 2, "done": []}
    rc.mission_store(root, first["id"]).save(state, T0)
    assert rc.serve_step(root, lambda *_: pytest.fail("should not execute"), conflicts=lambda: []) == f"corrupt:{first['id']}"


def test_mission_store_keeps_the_existing_chain_hold_untouched(tmp_path: Path) -> None:
    env = Env(tmp_path, [("claude", SUCCESS)])
    root = tmp_path / "control"
    chain = rc.Store(root)
    held = rc.default_state()
    held.update({"phase": "held", "head_session": HEAD, "chain": [HEAD],
                 "hold": {"reason": "effects_uncertain", "at": rc.iso(T0), "attempt": 6, "turn": f"{HEAD}/turn-006"}})
    chain.save(held, T0)
    before = chain.state_path.read_bytes()
    _write_mission(root, mission_def("independent work"))
    factory = lambda store, mission: rc.Supervisor(store, env.host, env.limits)  # noqa: E731
    assert rc.serve_step(root, factory, conflicts=lambda: []).endswith(":idle")
    assert chain.state_path.read_bytes() == before and not chain.journal_path.exists()


def test_cli_submit_requires_a_recorded_directive_and_is_durable(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = tmp_path / "control"
    monkeypatch.setenv("RELAY_CONTINUITY_DIR", str(root))
    monkeypatch.setattr(rc, "repo_root", lambda: tmp_path)
    ledger = [{"id": DIRECTIVE, "kind": "directive"}, {"id": "L20261020121757-26d5", "kind": "claim"}]
    monkeypatch.setattr(rc.devctx, "read_ledger", lambda env: ledger)
    notes: list[Any] = []
    monkeypatch.setattr(rc.devctx, "append_entry", lambda env, entry: notes.append(entry))
    spec = tmp_path / "m.json"
    spec.write_text(json.dumps({"authority": "L20261020121757-26d5", "tasks": [{"text": "a"}]}))
    assert rc.main(["submit", "--mission-file", str(spec)]) == 2  # a claim is not a maintainer directive
    spec.write_text(json.dumps({"authority": DIRECTIVE, "tasks": [{"text": "a"}], "agent": "codex"}))
    assert rc.main(["submit", "--mission-file", str(spec)]) == 2
    spec.write_text(json.dumps({"authority": DIRECTIVE, "tasks": [{"text": "a"}, {"text": "b"}]}))
    assert rc.main(["submit", "--mission-file", str(spec)]) == 0
    [(mission, mid, problem)] = rc.load_missions(root)
    assert problem is None and mission["tasks"][1]["text"] == "b" and mission["authority"] == DIRECTIVE
    assert rc.mission_status(rc.mission_store(root, mid))[0] == "queued" and len(notes) == 1


def test_cli_serve_refuses_outside_the_sandbox(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RELAY_CONTINUITY_DIR", str(tmp_path))
    monkeypatch.setattr(rc, "in_sandbox", lambda: False)
    assert rc.main(["serve", "--once", "--no-notify"]) == 2
    assert not (tmp_path / "serve.lock").exists()


def test_cli_serve_keeps_an_operator_stop_across_restart(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RELAY_CONTINUITY_DIR", str(tmp_path))
    monkeypatch.setattr(rc, "in_sandbox", lambda: True)
    (tmp_path / "STOP").write_text("operator stop")
    assert rc.main(["serve", "--once", "--no-notify"]) == 0
    assert (tmp_path / "STOP").read_text() == "operator stop"
    assert not (tmp_path / "serve.lock").exists()


def test_cli_serve_pins_the_sandbox_provider_logins(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    home = tmp_path / "home"
    login = home / ".local/share/jarvisos-sandbox/state/claude"
    login.mkdir(parents=True)
    (login / ".credentials.json").write_text("{}")
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("CODEX_HOME", str(home / ".codex"))  # what a Claude shell's launcher leaves behind
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(home / ".claude"))
    monkeypatch.setenv("RELAY_CONTINUITY_DIR", str(tmp_path / "control"))
    monkeypatch.setattr(rc, "in_sandbox", lambda: True)
    monkeypatch.setattr(rc.shutil, "which", lambda _name: None)  # stop right after the environment is set
    assert rc.main(["serve", "--once", "--no-notify"]) == 2
    assert os.environ["CODEX_HOME"] == str(home / ".local/share/jarvisos-sandbox/state/codex")
    assert os.environ["CLAUDE_CONFIG_DIR"] == str(login)
    assert (home / ".claude/.credentials.json").resolve() == (login / ".credentials.json").resolve()


def test_sandbox_provider_env_pins_the_github_login_only_when_installed(tmp_path: Path) -> None:
    state = tmp_path / ".local/share/jarvisos-sandbox/state"
    assert "GH_CONFIG_DIR" not in rc.sandbox_provider_env(tmp_path)
    assert "GIT_CONFIG_GLOBAL" not in rc.sandbox_provider_env(tmp_path)
    (state / "gh").mkdir(parents=True)
    (state / "gh/hosts.yml").write_text("github.com: {}\n")
    (state / "gitconfig").write_text("[credential]\n")
    env = rc.sandbox_provider_env(tmp_path)
    assert env["GH_CONFIG_DIR"] == str(state / "gh") and env["GIT_CONFIG_GLOBAL"] == str(state / "gitconfig")


def test_relay_claude_credentials_link_never_replaces_an_existing_file(tmp_path: Path) -> None:
    login, home = tmp_path / "login", tmp_path / "home"
    rc.link_relay_claude_credentials(login, home)
    assert not (home / ".claude").exists()  # no sandbox login: nothing to point at
    login.mkdir()
    (login / ".credentials.json").write_text("sandbox")
    (home / ".claude").mkdir(parents=True)
    (home / ".claude/.credentials.json").write_text("own")
    rc.link_relay_claude_credentials(login, home)
    assert (home / ".claude/.credentials.json").read_text() == "own"


def test_codex_quota_probe_writes_the_rollout_relay_reads(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    seen: dict[str, Any] = {}
    monkeypatch.setattr(rc.subprocess, "run", lambda args, **kw: seen.update(args=args, **kw))
    rc.refresh_codex_quota(tmp_path)
    assert "--ephemeral" not in seen["args"] and seen["args"][:4] == ["codex", "exec", "--sandbox", "read-only"]
    assert seen["timeout"] == 120


def test_relay_start_opens_a_new_session_with_closed_stdin_and_profile_env(tmp_path: Path,
                                                                            monkeypatch: pytest.MonkeyPatch) -> None:
    seen: dict[str, Any] = {}
    monkeypatch.setattr(rc.subprocess, "Popen", lambda args, **kw: seen.update(args=args, **kw))
    rc.RelayAdapter(tmp_path, env={"AGENT_RELAY_CLAUDE_PERMISSION_MODE": "bypassPermissions"}).start("claude", None, "t", 1)
    assert "--continue" not in seen["args"] and seen["stdin"] is subprocess.DEVNULL
    assert seen["env"]["AGENT_RELAY_CLAUDE_PERMISSION_MODE"] == "bypassPermissions" and "PATH" in seen["env"]
    rc.RelayAdapter(tmp_path).start("codex", HEAD, "t", 1)
    assert seen["args"][4:6] == ["--continue", HEAD] and seen["env"] is None


def test_mission_claude_entrypoint_replaces_relays_default_mode(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    import runpy

    entrypoint = Path(rc.__file__).resolve().parent / "relay_mission_bin" / "claude"
    real = tmp_path / "claude-real"
    real.write_text("real")
    main = runpy.run_path(str(entrypoint))["main"]
    monkeypatch.setattr("socket.gethostname", lambda: "jarvis-sandbox")
    monkeypatch.setenv("JARVISOS_MISSION_PROFILE", "1")
    monkeypatch.setenv("RELAY_CLAUDE_REAL_BIN", str(real))
    monkeypatch.setattr("sys.argv", [str(entrypoint), "--permission-mode", "default", "--settings", "rules.json",
                                    "-p", "task"])
    invoked: list[Any] = []

    def execv(path: str, argv: list[str]) -> None:
        invoked.append((path, argv))
        raise RuntimeError("captured exec")

    monkeypatch.setattr("os.execv", execv)
    with pytest.raises(RuntimeError, match="captured exec"):
        main()
    assert invoked == [(str(real), [str(real), "--settings", "rules.json", "-p", "task",
                                    "--permission-mode", "bypassPermissions"])]
    monkeypatch.setattr("socket.gethostname", lambda: "ordinary-host")
    assert main() == 2


def test_release_mission_hold_and_advance(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    env = Env(tmp_path, [("claude", SUCCESS)])
    root = tmp_path / "control"
    monkeypatch.setenv("RELAY_CONTINUITY_DIR", str(root))
    monkeypatch.setattr(rc, "make_host", lambda repo: env.host)
    mission = mission_def("merge it", "then this", checks={0: {"kind": "pr_merged", "pr": 1}})
    _write_mission(root, mission)
    env.host.task_check = lambda check: "PR #1 is OPEN"
    factory = lambda store, m: rc.Supervisor(store, env.host, env.limits)  # noqa: E731
    assert rc.serve_step(root, factory, conflicts=lambda: [], now=env.clock.now) == f"ran:{mission['id']}:held"
    assert rc.main(["release", "--mission", mission["id"], "--advance", "--note", "merged by hand"]) == 0
    env.relay.script = [("claude", SUCCESS)]
    assert rc.serve_step(root, factory, conflicts=lambda: [], now=env.clock.now) == f"ran:{mission['id']}:idle"
    assert "then this" in env.relay.launches[-1]["task"]
    state = rc.mission_store(root, mission["id"]).load()
    assert [d.get("by") for d in state["mission"]["done"]] == ["maintainer", None] and state["mission"]["completed_at"]
    assert rc.Store(root).state_path.exists() is False  # the `run` chain store was never touched


def test_cancel_refuses_an_unsettled_attempt(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = tmp_path / "control"
    monkeypatch.setenv("RELAY_CONTINUITY_DIR", str(root))
    mission = mission_def("x")
    _write_mission(root, mission)
    store = rc.mission_store(root, mission["id"])
    state = rc.default_state()
    state.update({"mission": {"id": mission["id"], "next": 0, "total": 1, "done": []},
                  "pending": {"nonce": "rc-1", "agent": "claude", "parent": None, "started_at": rc.iso(T0), "pid": None,
                              "pid_start": None, "fingerprint": "f", "attempt": 1, "task": 0}})
    store.save(state, T0)
    assert rc.main(["cancel", mission["id"], "--note", "n"]) == 3
    state["pending"] = None
    store.save(state, T0)
    assert rc.main(["cancel", mission["id"], "--note", "n"]) == 0
    assert rc.mission_status(store)[0] == "cancelled"


# ---------------------------------------------------------------------------
# Spec 203: roadmap continuation cycles


class Roadmap:
    """A control root whose missions are submitted for real and completed or cancelled on demand."""

    def __init__(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, *refs: str | None) -> None:
        self.root, self.repo = tmp_path / "control", tmp_path / "repo"
        self.repo.mkdir()
        monkeypatch.setenv("RELAY_CONTINUITY_DIR", str(self.root))
        monkeypatch.setattr(rc, "repo_root", lambda: self.repo)
        monkeypatch.setattr(rc.devctx, "read_ledger", lambda env: [{"id": DIRECTIVE, "kind": "directive"}])
        monkeypatch.setattr(rc.devctx, "append_entry", lambda env, entry: None)
        self.refs = list(refs)
        self.minute = 0

    def fingerprint(self) -> str | None:
        return self.refs.pop(0) if self.refs else "same"

    def step(self) -> str | None:
        self.minute += 1
        return rc.roadmap_step(self.root, self.repo, fingerprint=self.fingerprint,
                               submit=self.submit, now=lambda: T0 + timedelta(minutes=self.minute))

    def submit(self, authority: str, tasks: list[dict[str, Any]], mission_id: str) -> Any:
        return rc.submit_mission(self.root, self.repo, authority, tasks, mission_id=mission_id,
                                 now=T0 + timedelta(minutes=self.minute))

    def finish(self, mission_id: str, *, relay_status: str = "propose_done", cancelled: bool = False) -> None:
        session = f"20261018-0800{self.minute:02d}-cccccc"
        write_turn(self.repo / ".agent-relay" / "sessions" / session, SUCCESS, status=relay_status)
        state = rc.default_state()
        state["head_session"] = session
        state["mission"] = {"id": mission_id, "next": 1, "total": 1, "done": [],
                            **({"cancelled_at": rc.iso(T0)} if cancelled else {"completed_at": rc.iso(T0)})}
        rc.mission_store(self.root, mission_id).save(state, T0)


def test_roadmap_is_off_until_started_and_needs_a_recorded_directive(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    road = Roadmap(tmp_path, monkeypatch)
    assert road.step() is None and not rc.missions_dir(road.root).exists()
    assert rc.main(["roadmap", "start", "--authority", "L20261020121757-26d5"]) == 2  # not a recorded directive
    assert rc.main(["roadmap", "stop", "--note", "x"]) == 2  # nothing to stop
    assert rc.main(["roadmap", "start", "--authority", DIRECTIVE]) == 0
    outcome = road.step()
    assert outcome and outcome.startswith("roadmap:submitted:")
    [(mission, _, problem)] = rc.load_missions(road.root)
    assert problem is None and mission["authority"] == DIRECTIVE and len(mission["tasks"]) == 1
    assert "cycle 1" in mission["tasks"][0]["text"] and "Generic Frontier Builder Contract" in mission["tasks"][0]["text"]


def test_roadmap_keeps_one_cycle_queued_and_never_runs_beside_a_queued_mission(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    road = Roadmap(tmp_path, monkeypatch, "r0", "r1", "r2")
    rc.main(["roadmap", "start", "--authority", DIRECTIVE])
    first = road.step().split(":")[2]
    assert road.step() == f"roadmap:waiting:{first}"  # its cycle has not finished: no second one
    road.finish(first)
    second = road.step().split(":")[2]
    assert second != first and rc.load_roadmap(road.root)["cycle"] == 2
    road.finish(second)
    assert road.step().startswith("roadmap:submitted:")
    events = [json.loads(line)["event"] for line in (rc.missions_dir(road.root) / "journal.jsonl").read_text().splitlines()]
    assert events.count("roadmap_cycle_submitted") == 3 and events[0] == "roadmap_started"


def test_roadmap_pauses_when_the_coordinator_reports_blocked(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    road = Roadmap(tmp_path, monkeypatch, "r0", "r1")
    rc.main(["roadmap", "start", "--authority", DIRECTIVE])
    first = road.step().split(":")[2]
    road.finish(first, relay_status="blocked")
    assert road.step() == "roadmap:paused:coordinator_blocked"
    assert road.step() == "roadmap:paused:coordinator_blocked" and len(rc.load_missions(road.root)) == 1
    assert rc.main(["roadmap", "start", "--authority", DIRECTIVE]) == 0  # the maintainer resumes it
    assert road.step().startswith("roadmap:submitted:")  # the blocked cycle is not re-judged


def test_roadmap_pauses_after_cycles_without_remote_progress(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    road = Roadmap(tmp_path, monkeypatch, "r0", "r1", "r1", "r1", "r1")
    rc.main(["roadmap", "start", "--authority", DIRECTIVE])
    outcomes = []
    while (outcome := road.step()).startswith("roadmap:submitted:"):
        outcomes.append(outcome)
        road.finish(outcome.split(":")[2])
    # Baseline r0; cycle 1 moved the heads to r1 (progress); cycles 2-4 left them at r1.
    assert outcome == "roadmap:paused:no_progress" and len(outcomes) == 1 + rc.ROADMAP_NO_PROGRESS


def test_roadmap_waits_while_remote_heads_are_unreadable(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    road = Roadmap(tmp_path, monkeypatch, None, "r0", "r1", None, "r2")
    rc.main(["roadmap", "start", "--authority", DIRECTIVE])
    assert road.step() == "roadmap:waiting:remote_unreadable" and not rc.missions_dir(road.root).joinpath("x").exists()
    first = road.step().split(":")[2]
    road.finish(first)
    second = road.step().split(":")[2]
    road.finish(second)
    assert road.step() == "roadmap:waiting:remote_unreadable"
    assert road.step().startswith("roadmap:submitted:") and rc.load_roadmap(road.root)["no_progress"] == 0


def test_roadmap_pauses_on_a_cancelled_cycle_and_on_maintainer_stop(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    road = Roadmap(tmp_path, monkeypatch, "r0", "r1")
    rc.main(["roadmap", "start", "--authority", DIRECTIVE])
    first = road.step().split(":")[2]
    road.finish(first, cancelled=True)
    assert road.step() == "roadmap:paused:cycle_cancelled"
    rc.main(["roadmap", "start", "--authority", DIRECTIVE])
    assert road.step().startswith("roadmap:submitted:")
    assert rc.main(["roadmap", "stop"]) == 2  # a note is required
    assert rc.main(["roadmap", "stop", "--note", "reviewing direction"]) == 0
    assert road.step() == "roadmap:paused:maintainer_stop"
    rc.roadmap_path(road.root).write_text("{")
    assert road.step() == "roadmap:corrupt" and rc.main(["roadmap", "start", "--authority", DIRECTIVE]) == 2


def test_roadmap_pause_notification_uses_the_fixed_template() -> None:
    assert rc.render("roadmap_paused", {"owner": "control-plane", "reason": "no_progress"})
    assert rc.render("roadmap_paused", {"owner": "control-plane", "reason": "anything else"}) is None


def test_owner_ignores_its_own_sandbox_init_in_the_checkout(tmp_path: Path) -> None:
    proc = fake_proc(tmp_path)
    repo = tmp_path / "repo"
    repo.mkdir()
    # Inside jarvis-sandbox, PID 1 is bwrap with --chdir <checkout>; the owner (2) is its child.
    add_proc(proc, 1, argv=["bwrap", "--chdir", str(repo), "--", "python3"], cwd=repo, started=T0, ppid=0)
    add_proc(proc, 2, argv=["python3", "scripts/relay_continuity.py", "serve"], cwd=repo, started=T0, ppid=1)
    add_proc(proc, 3, argv=["python", "-m", "pytest"], cwd=repo, started=T0, ppid=1)
    assert [w.label for w in rc.live_processes([repo], T0, {2}, proc_root=proc)] == ["process python"]


def test_roadmap_stop_is_never_overwritten_by_a_concurrent_owner_step(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    road = Roadmap(tmp_path, monkeypatch, "r0", "r1")
    rc.main(["roadmap", "start", "--authority", DIRECTIVE])
    road.finish(road.step().split(":")[2])
    monkeypatch.setattr(rc, "ROADMAP_LOCK_WAIT", 0.0)
    stops: list[int] = []

    def slow_remote() -> str:  # the maintainer stops while the owner is reading the remote heads
        stops.append(rc.main(["roadmap", "stop", "--note", "stop now"]))
        return "r1"
    road.fingerprint = slow_remote  # type: ignore[method-assign]
    assert road.step().startswith("roadmap:submitted:") and stops == [3]  # refused while the step held the lock
    assert rc.main(["roadmap", "stop", "--note", "stop now"]) == 0
    assert road.step() == "roadmap:paused:maintainer_stop"
    lock = rc.roadmap_lock(road.root)
    assert lock is not None
    try:
        assert road.step() == "roadmap:waiting:busy"  # and a held lock never lets the owner write around a stop
    finally:
        lock.release()


def test_roadmap_cycle_identity_survives_a_crash_around_submission(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    road = Roadmap(tmp_path, monkeypatch, "r0")
    rc.main(["roadmap", "start", "--authority", DIRECTIVE])
    real = road.submit

    def crash_before_queueing(authority: str, tasks: list[dict[str, Any]], mission_id: str) -> Any:
        raise OSError("killed before the mission file was written")
    road.submit = crash_before_queueing  # type: ignore[method-assign]
    with pytest.raises(OSError):
        road.step()
    recorded = rc.load_roadmap(road.root)["last_mission"]
    assert not rc.load_missions(road.root)

    def crash_after_queueing(authority: str, tasks: list[dict[str, Any]], mission_id: str) -> Any:
        real(authority, tasks, mission_id)
        raise OSError("killed during the ledger note")
    road.submit = crash_after_queueing  # type: ignore[method-assign]
    with pytest.raises(OSError):
        road.step()  # the recorded cycle is queued under its own id, not a new one
    [(mission, mid, _)] = rc.load_missions(road.root)
    assert mid == recorded and "cycle 1" in mission["tasks"][0]["text"]
    road.submit = real  # type: ignore[method-assign]
    road.finish(mid, relay_status="blocked")
    assert road.step() == "roadmap:paused:coordinator_blocked"  # the crashed-around cycle is still judged
    assert len(rc.load_missions(road.root)) == 1
