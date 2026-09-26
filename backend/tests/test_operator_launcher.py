"""Safety decisions for the human desktop launcher."""

import importlib.util
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "jarvisos_launcher.py"
SPEC = importlib.util.spec_from_file_location("jarvisos_launcher", SCRIPT)
assert SPEC and SPEC.loader
launcher = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = launcher
SPEC.loader.exec_module(launcher)


def state(**changes):
    base = dict(branch="master", head="a" * 40, dirty=[], fetched=True,
                remote="b" * 40, ahead=0, behind=0)
    base.update(changes)
    return launcher.GitState(**base)


@pytest.mark.parametrize(
    ("changes", "action"),
    [
        ({}, "none"),
        ({"behind": 1}, "fast-forward"),
        ({"dirty": [" M AGENTS.md"], "behind": 1}, "skip"),
        ({"ahead": 1, "behind": 1}, "skip"),
        ({"branch": "feature", "behind": 1}, "skip"),
        ({"fetched": False, "fetch_error": "network unavailable", "behind": 1}, "skip"),
    ],
)
def test_update_plan_preserves_local_work_and_offline_state(changes, action):
    assert launcher.plan_update(state(**changes)).action == action


def test_manual_jarvisos_port_is_reported_without_termination(monkeypatch):
    info = launcher.ProcInfo(123, ["python", "-m", "uvicorn", "app.main:app"],
                             str(launcher.REPO / "backend"), "/usr/bin/python", 1, 42)
    monkeypatch.setattr(launcher, "listening_pids", lambda port: [123])
    monkeypatch.setattr(launcher, "proc_info", lambda pid: info)
    monkeypatch.setattr(launcher, "terminate", lambda *args: pytest.fail("manual process was terminated"))
    with pytest.raises(launcher.LaunchError, match="manually started JarvisOS"):
        launcher.resolve_port_conflict(8000)


def test_launcher_rejects_noncanonical_worktree(monkeypatch, tmp_path):
    monkeypatch.setattr(launcher, "REPO", tmp_path)
    with pytest.raises(launcher.LaunchError, match="canonical checkout"):
        launcher.start(SimpleNamespace(no_update=True, no_browser=True))


def test_wsl_distro_without_inherited_environment(monkeypatch):
    monkeypatch.delenv("WSL_DISTRO_NAME", raising=False)
    monkeypatch.setattr(launcher.subprocess, "run", lambda *args, **kwargs: SimpleNamespace(
        stdout="Ubuntu-24.04\r\n".encode("utf-16-le")))
    assert launcher.wsl_distro({}) == "Ubuntu-24.04"


def test_windows_tools_resolve_without_windows_path(monkeypatch):
    monkeypatch.setattr(launcher.shutil, "which", lambda name: None)
    if not (Path("/mnt/c/Windows/System32/cmd.exe")).is_file():
        pytest.skip("Windows interop tools unavailable outside WSL")
    assert launcher.running_under_wsl()
    assert launcher.windows_tool("cmd.exe") == "/mnt/c/Windows/System32/cmd.exe"


def test_readiness_requires_loaded_local_model(monkeypatch):
    monkeypatch.setattr(launcher, "http_text", lambda *args, **kwargs: (200, '<div id="root"></div>'))
    def response(url, **kwargs):
        if url.endswith("/health"):
            return 200, {"status": "ok"}
        return 200, {"routes": [
            {"route_class": "local:llamacpp", "model_id": "local-model", "availability": {
                "runtime_reachable": True, "model_loaded": False, "reason_code": "LLAMACPP_AUTH_REQUIRED",
                "message": "Local model requires a key."}},
            {"route_class": "hermes:agent", "availability": {"runtime_reachable": True}},
        ]}
    monkeypatch.setattr(launcher, "http_json", response)
    assert launcher.readiness(8000)[0] == "degraded"


@pytest.mark.parametrize("url", ["https://127.0.0.1:8000/health", "http://example.com/health",
                                   "http://127.0.0.1.evil.test:8000/health", "file:///etc/passwd"])
def test_health_transport_rejects_non_loopback_endpoints(url):
    with pytest.raises(launcher.LaunchError, match="127.0.0.1"):
        launcher.http_json(url)


def test_real_git_fast_forward_then_dirty_and_offline_safe_mode(monkeypatch, tmp_path):
    def git(*args, cwd=None):
        return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()

    bare = tmp_path / "origin.git"
    writer = tmp_path / "writer"
    checkout = tmp_path / "canonical"
    git("init", "--bare", str(bare))
    git("init", str(writer))
    git("config", "user.name", "Launcher Test", cwd=writer)
    git("config", "user.email", "launcher@example.invalid", cwd=writer)
    (writer / "operator.txt").write_text("one\n")
    git("add", ".", cwd=writer)
    git("commit", "-m", "one", cwd=writer)
    git("branch", "-M", "master", cwd=writer)
    git("remote", "add", "origin", str(bare), cwd=writer)
    git("push", "-u", "origin", "master", cwd=writer)
    git("clone", "--branch", "master", str(bare), str(checkout))
    monkeypatch.setattr(launcher, "REPO", checkout)
    monkeypatch.setattr(launcher, "say", lambda message: None)

    (writer / "operator.txt").write_text("two\n")
    git("commit", "-am", "two", cwd=writer)
    git("push", cwd=writer)
    state_after_update = launcher.update_checkout(False)
    assert state_after_update.head == git("rev-parse", "HEAD", cwd=writer)
    assert (checkout / "operator.txt").read_text() == "two\n"

    (checkout / "operator.txt").write_text("private work\n")
    (writer / "operator.txt").write_text("three\n")
    git("commit", "-am", "three", cwd=writer)
    git("push", cwd=writer)
    assert launcher.update_checkout(False).head == state_after_update.head
    assert (checkout / "operator.txt").read_text() == "private work\n"

    git("remote", "set-url", "origin", str(tmp_path / "missing-origin"), cwd=checkout)
    assert launcher.update_checkout(False).head == state_after_update.head
    assert (checkout / "operator.txt").read_text() == "private work\n"
