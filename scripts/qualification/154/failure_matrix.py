#!/usr/bin/env python3
"""Spec 154 failure-scenario matrix against the real repository, GitHub and a copy of the control room.

Each scenario copies the real ledger into a scratch control dir (lane files are linked, not copied), applies
one failure condition through the devctx Env seams, builds a packet and checks the conservative outcome.
Nothing in the real control room, repository or GitHub is modified.
"""
from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Callable
from datetime import timedelta
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
SPEC = importlib.util.spec_from_file_location("devctx", ROOT / "scripts" / "devctx.py")
assert SPEC and SPEC.loader
devctx = importlib.util.module_from_spec(SPEC)
sys.modules["devctx"] = devctx
SPEC.loader.exec_module(devctx)

REAL_CONTROL = Path(os.environ.get("JARVIS_CONTROL_DIR", Path.home() / "jarvis-control/work"))


def scratch_env(with_ledger: bool = True, with_lanes: bool = True) -> devctx.Env:
    base = devctx.default_env(ROOT)
    control = Path(tempfile.mkdtemp(prefix="devctx-matrix-"))
    if with_ledger and (REAL_CONTROL / "ledger.jsonl").exists():
        shutil.copy2(REAL_CONTROL / "ledger.jsonl", control / "ledger.jsonl")
        shutil.copytree(REAL_CONTROL / "directives", control / "directives")
    if with_lanes and (REAL_CONTROL / "out").exists():
        (control / "out").symlink_to(REAL_CONTROL / "out")
    base.control = control
    base.processes = lambda: devctx.real_processes(REAL_CONTROL / "out")
    return base


def add(env: devctx.Env, kind: str, text: str, **kwargs: Any) -> dict[str, Any]:
    return devctx.append_entry(env, devctx.make_entry(env, kind, text, author="failure-matrix", **kwargs))


def dead_pid() -> int:
    proc = subprocess.Popen([sys.executable, "-c", "pass"])
    proc.wait()
    return proc.pid


def by_id(packet: dict[str, Any], entry: dict[str, Any]) -> dict[str, Any]:
    return next(item for item in packet["ledger"] if item["id"] == entry["id"])


def failing_gh(message: str) -> Callable[[list[str]], Any]:
    def call(args: list[str]) -> Any:
        raise RuntimeError(message)
    return call


def scenario_coordinator_death() -> dict[str, Any]:
    env = scratch_env()
    claim = add(env, "claim", "k154ctx single writer (coordinator that died)",
                claim={"expires": devctx.iso(env.now + timedelta(hours=8)), "pid": dead_pid(), "pid_start": 123})
    packet = devctx.build_packet(env, fetch=True)
    verdict = by_id(packet, claim)["freshness"]["verdict"]
    return {"expect": "dead coordinator's claim is expired; open PR and plan remain visible",
            "observed": {"claim": verdict, "open_prs": [p["number"] for p in packet["open_prs"]],
                         "candidates": packet["candidates"][:3]},
            "pass": verdict == "expired" and bool(packet["open_prs"])}


def scenario_new_relay_session() -> dict[str, Any]:
    env = scratch_env()
    records = devctx.read_ledger(env)
    since = devctx.parse_ts(records[0]["ts"]) - timedelta(days=2) if records else None
    prompts = devctx.relay_prompts(env, since, limit=50)
    packet = devctx.build_packet(env, fetch=True)
    directives = [e for e in packet["ledger"] if e["kind"] == "directive"]
    return {"expect": "a fresh session sees the recorded directive and Relay's verbatim maintainer prompts by path",
            "observed": {"directives": [(e["text"][:80], e["provenance"][:40]) for e in directives],
                         "relay_prompts_visible_48h": len(prompts)},
            "pass": bool(directives) and len(prompts) > 0}


def scenario_network_loss() -> dict[str, Any]:
    env = scratch_env()
    env.gh = failing_gh("error connecting to api.github.com")
    proof = add(env, "proof", "matrix proof bound to master content", refs={"sha": devctx.master_state(env)["sha"],
                                                                             "branch": "master", "paths": ["AGENTS.md"]})
    packet = devctx.build_packet(env, fetch=False)
    text = devctx.render(packet)
    fresh = by_id(packet, proof)["freshness"]
    return {"expect": "authority marked NOT VERIFIED; origin-bound verdicts downgraded to unverified",
            "observed": {"header": "NOT VERIFIED" in text, "proof": fresh["verdict"], "why": fresh["why"][:120],
                         "warnings": [w[:90] for w in packet["warnings"][:2]]},
            "pass": "NOT VERIFIED" in text and fresh["verdict"] == "unverified"}


def scenario_auth_expired() -> dict[str, Any]:
    env = scratch_env()
    env.gh = failing_gh("HTTP 401: Bad credentials (gh auth login required)")
    packet = devctx.build_packet(env, fetch=True)
    text = devctx.render(packet)
    return {"expect": "GitHub state reported UNKNOWN, not 'no open PRs'",
            "observed": {"open_prs_line": "open PRs: UNKNOWN" in text,
                         "warning": next((w for w in packet["warnings"] if "GitHub UNVERIFIED" in w), "")[:100]},
            "pass": "open PRs: UNKNOWN" in text and "open PRs: none" not in text}


def scenario_suspend_restart() -> dict[str, Any]:
    env = scratch_env()
    env.processes = list
    lanes = devctx.lane_state(env, [])
    running = [lane["lane"] for lane in lanes if lane["state"] == "running"]
    unfinished = [lane["lane"] for lane in lanes if lane["state"].startswith("incomplete")]
    return {"expect": "after restart no lane is reported running; unfinished lanes are flagged incomplete",
            "observed": {"running": running, "incomplete_count": len(unfinished), "incomplete_sample": unfinished[:5]},
            "pass": not running and bool(unfinished)}


def scenario_stale_git_state_in_old_notes() -> dict[str, Any]:
    env = scratch_env()
    entry = add(env, "blocker", "PR #715 is open and waiting for its registry gate", refs={"pr": 715})
    packet = devctx.build_packet(env, fetch=True)
    why = by_id(packet, entry)["freshness"]["why"]
    return {"expect": "an old note about an open PR is annotated with the PR's current MERGED state",
            "observed": {"why": why}, "pass": "now MERGED" in why}


def scenario_worker_report_conflicts_with_master() -> dict[str, Any]:
    env = scratch_env()
    entry = add(env, "finding", "worker: STATUS row 153 is still ready (registry gate failing)",
                refs={"sha": "248291cc2ef2c2c10f10b2eb2e54e677b4e789b8", "paths": ["docs/specs/STATUS.md"]})
    packet = devctx.build_packet(env, fetch=True)
    fresh = by_id(packet, entry)["freshness"]
    return {"expect": "a finding bound to content that master has since changed is stale",
            "observed": fresh, "pass": fresh["verdict"] == "stale"}


def scenario_proof_then_code_changed() -> dict[str, Any]:
    env = scratch_env()
    first = subprocess.run(["git", "log", "--format=%H", "--reverse", "origin/master..HEAD", "--", "scripts/devctx.py"],
                           cwd=ROOT, capture_output=True, text=True, check=True).stdout.split()[0]
    entry = add(env, "proof", "devctx tests passed at the first implementation commit",
                refs={"sha": first, "branch": "impl/154-persistent-development-context", "paths": ["scripts/devctx.py"]})
    packet = devctx.build_packet(env, fetch=True)
    fresh = by_id(packet, entry)["freshness"]
    return {"expect": "a proof whose bound code changed on the branch afterwards is stale and names the file",
            "observed": fresh, "pass": fresh["verdict"] == "stale" and "scripts/devctx.py" in fresh.get("changed", [])}


def scenario_incomplete_worker_lane() -> dict[str, Any]:
    env = scratch_env()
    lanes = devctx.lane_state(env, env.processes() if env.processes else [])
    states = {lane["lane"]: lane["state"] for lane in lanes}
    incomplete = sorted(name for name, state in states.items() if state.startswith("incomplete"))
    return {"expect": "lanes with logs but no done marker and no live process are reported incomplete, not done",
            "observed": {"incomplete": incomplete[:8], "done_count": sum(s == "done" for s in states.values())},
            "pass": bool(incomplete) and all(states[n] != "done" for n in incomplete)}


def scenario_contradictory_findings() -> dict[str, Any]:
    env = scratch_env()
    one = add(env, "finding", "worker A: devctx lane detection misses reparented codex workers")
    two = add(env, "finding", "worker B: reparented codex workers are detected via cmdline/-o", conflicts=[one["id"]])
    packet = devctx.build_packet(env, fetch=True)
    warning = next((w for w in packet["warnings"] if "UNRESOLVED CONFLICT" in w), "")
    return {"expect": "contradictory findings surface as an unresolved conflict until a decision supersedes one",
            "observed": {"warning": warning}, "pass": one["id"] in warning and two["id"] in warning}


def scenario_missing_local_history() -> dict[str, Any]:
    env = scratch_env(with_ledger=False, with_lanes=False)
    packet = devctx.build_packet(env, fetch=True)
    return {"expect": "with no ledger/lanes the packet still recovers authority, open PRs and candidates from GitHub/Git",
            "observed": {"open_prs": [p["number"] for p in packet["open_prs"]], "master": packet["authority"]["master"]["sha"],
                         "warning": next((w for w in packet["warnings"] if "no control ledger" in w), "")[:90],
                         "candidates": packet["candidates"][:3]},
            "pass": bool(packet["authority"]["master"]["sha"]) and packet["authority"]["github_ok"]
            and any("no control ledger" in w for w in packet["warnings"])}


SCENARIOS = {
    "coordinator_process_dies": scenario_coordinator_death,
    "new_relay_session": scenario_new_relay_session,
    "network_loss": scenario_network_loss,
    "authentication_expired": scenario_auth_expired,
    "machine_suspend_restart": scenario_suspend_restart,
    "old_session_stale_git_state": scenario_stale_git_state_in_old_notes,
    "worker_report_conflicts_with_master": scenario_worker_report_conflicts_with_master,
    "proof_then_code_changed": scenario_proof_then_code_changed,
    "incomplete_worker_lane": scenario_incomplete_worker_lane,
    "two_contradictory_findings": scenario_contradictory_findings,
    "missing_local_history_github_intact": scenario_missing_local_history,
}


def main() -> int:
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    results = {name: run() for name, run in SCENARIOS.items()}
    report = {"source_sha": head, "generated_at": devctx.iso(devctx.now_utc()),
              "provider_switch": "exercised separately by the Codex acceptance probe (see acceptance.json)",
              "passed": sum(r["pass"] for r in results.values()), "total": len(results), "scenarios": results}
    print(json.dumps(report, indent=1, ensure_ascii=False, default=str))
    return 0 if report["passed"] == report["total"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
