"""Spec 195: Relay provider continuity supervisor and Slack outbound monitor (offline, injected Relay)."""
from __future__ import annotations

import importlib.util
import json
import os
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

    def finish(self, proc: FakeProc) -> Any:
        step, agent, task = self._current
        if step is None:
            return rc.RunResult(None, 1, False)
        _, events = step
        sid = f"20261018-{len(self.launches):06d}-{'b' * 6}"
        write_turn(self.sessions_dir() / sid, events, agent=agent, prompt=task)
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
        return rc.Supervisor(self.store, self.host, self.limits, turns=turns, sender=self.sender)

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
                   prompt=f"[relay-continuity attempt {nonce}]")
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
               prompt=f"[relay-continuity attempt {nonce}]")
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
    monkeypatch.setattr(rc.urllib.request, "urlopen", boom)
    error = rc.post_webhook("hello", webhook_file=hook)
    assert error == "URLError" and SECRET_URL not in error

    def http_error(*_args: Any, **_kwargs: Any) -> Any:
        raise urllib.error.HTTPError(SECRET_URL, 404, "no_service", {}, None)  # type: ignore[arg-type]
    monkeypatch.setattr(rc.urllib.request, "urlopen", http_error)
    assert rc.post_webhook("hello", webhook_file=hook) == "http_404"
    hook.write_text("https://evil.example/collect")
    assert rc.post_webhook("hello", webhook_file=hook) == "webhook_invalid"
    assert rc.post_webhook("hello", webhook_file=tmp_path / "missing") == "webhook_missing"


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
               prompt=f"[relay-continuity attempt {nonce}]\ntask")
    write_turn(env.relay.sessions_dir() / "20261018-080500-aaaaab", EAI,
               prompt=f"[relay-continuity attempt rc-20261018T080500Z-12345678]\nAudit of {nonce}:\n"
                      f"[relay-continuity attempt {nonce}]")
    assert env.relay.find_by_nonce(nonce, T0) == "20261018-080030-ffffff"
    result, sup = env.run()
    assert result == "held" and sup.state["hold"]["reason"] == "effects_uncertain"
    assert env.relay.launches == []


def test_nonce_lookup_refuses_ambiguous_matches(tmp_path: Path) -> None:
    env = Env(tmp_path)
    nonce = "rc-20261018T080000Z-abad1dea"
    for sid in ("20261018-080030-aaaaaa", "20261018-080040-bbbbbb"):
        write_turn(env.relay.sessions_dir() / sid, SUCCESS, prompt=f"[relay-continuity attempt {nonce}]")
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
