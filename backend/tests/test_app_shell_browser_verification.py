import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import TextIO

import pytest

TARGET_SHA = "8c65977cafcd7237341fedf7adbf19053713f860"
TARGET_BRANCH = "spec/083-app-shell-1"
BASE_URL = "http://127.0.0.1:8000"
DEV_URL = "http://127.0.0.1:5173"


def _run(
    command: list[str],
    *,
    cwd: Path,
    env: dict[str, str] | None = None,
    timeout: int = 300,
) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        command,
        cwd=cwd,
        env=env,
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )
    if completed.returncode != 0:
        raise AssertionError(
            "command failed\n"
            f"cwd={cwd}\n"
            f"command={command}\n"
            f"exit={completed.returncode}\n"
            f"stdout={completed.stdout}\n"
            f"stderr={completed.stderr}"
        )
    return completed


def _wait_for_url(url: str, *, timeout: float = 60.0) -> None:
    deadline = time.monotonic() + timeout
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as response:
                if response.status < 500:
                    return
        except (OSError, urllib.error.URLError) as error:
            last_error = error
        time.sleep(1)
    raise AssertionError(f"server did not become ready at {url}: {last_error}")


def _stop_process(process: subprocess.Popen[str] | None) -> None:
    if process is None or process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=10)


def _extract_browser_script(repo_root: Path, destination: Path) -> None:
    source = (
        repo_root / ".github" / "workflows" / "verify-app-shell-browser.yml"
    ).read_text(encoding="utf-8")
    start = "          cat > .tmp-app-shell-browser.mjs <<'EOF'\n"
    end = "\n          EOF\n"
    if start not in source:
        raise AssertionError("browser script start marker missing")
    body = source.split(start, 1)[1]
    if end not in body:
        raise AssertionError("browser script end marker missing")
    body = body.split(end, 1)[0]
    lines = [line[10:] if line.startswith("          ") else line for line in body.splitlines()]

    focus_assertion_index = next(
        (
            index
            for index, line in enumerate(lines)
            if "assert(await trigger.evaluate" in line
            and "focus not restored" in line
        ),
        None,
    )
    if focus_assertion_index is None:
        raise AssertionError("focus-restoration assertion marker missing")
    focus_assertion = lines[focus_assertion_index]
    indentation = focus_assertion[: len(focus_assertion) - len(focus_assertion.lstrip())]
    lines.insert(
        focus_assertion_index,
        indentation
        + "await page.waitForFunction((label) => "
        + "document.activeElement?.textContent?.trim() === label, panel.show);",
    )

    destination.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _open_log(path: Path) -> TextIO:
    return path.open("w", encoding="utf-8")


@pytest.mark.skipif(
    os.getenv("GITHUB_ACTIONS") != "true",
    reason="temporary exact-head browser verification runs only in GitHub Actions",
)
def test_exact_head_app_shell_browser_matrix(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo_root = Path(__file__).resolve().parents[2]
    target = tmp_path / "target"
    data_root = tmp_path / "data"
    report_path = tmp_path / "app-shell-browser-matrix.json"
    fastapi_log_path = tmp_path / "fastapi.log"
    vite_log_path = tmp_path / "vite.log"
    browser_script = target / "frontend" / ".tmp-app-shell-browser.mjs"
    fastapi_process: subprocess.Popen[str] | None = None
    vite_process: subprocess.Popen[str] | None = None
    fastapi_log: TextIO | None = None
    vite_log: TextIO | None = None

    environment = os.environ.copy()
    environment.update(
        {
            "JARVISOS_DATA_ROOT": str(data_root),
            "JARVISOS_AI_PROVIDER": "none",
            "JARVISOS_ENV": "browser-verification",
            "BASE_URL": BASE_URL,
            "DEV_URL": DEV_URL,
            "MATRIX_REPORT": str(report_path),
            "TARGET_SHA": TARGET_SHA,
        }
    )

    try:
        _run(
            ["git", "fetch", "origin", TARGET_BRANCH, "--depth=1"],
            cwd=repo_root,
            timeout=120,
        )
        _run(
            ["git", "worktree", "add", "--detach", str(target), "FETCH_HEAD"],
            cwd=repo_root,
            timeout=60,
        )
        actual_sha = _run(
            ["git", "rev-parse", "HEAD"], cwd=target, timeout=30
        ).stdout.strip()
        assert actual_sha == TARGET_SHA

        frontend = target / "frontend"
        backend = target / "backend"
        _run(["npm", "ci"], cwd=frontend, env=environment, timeout=300)
        _run(["npm", "run", "build"], cwd=frontend, env=environment, timeout=180)

        forbidden = (
            "/legacy/dev-local-chat",
            "Development Local Chat",
            "Dev Local Chat",
        )
        matches: list[str] = []
        for path in (frontend / "dist").rglob("*"):
            if not path.is_file():
                continue
            content = path.read_text(encoding="utf-8", errors="ignore")
            if any(marker in content or marker in path.name for marker in forbidden):
                matches.append(str(path.relative_to(frontend)))
        assert matches == [], f"production DEV markers found: {matches}"

        _run(
            [
                "npm",
                "install",
                "--no-save",
                "--package-lock=false",
                "playwright@1.54.2",
            ],
            cwd=frontend,
            env=environment,
            timeout=300,
        )
        _run(
            ["npx", "playwright", "install", "--with-deps", "chromium"],
            cwd=frontend,
            env=environment,
            timeout=360,
        )

        data_root.mkdir(parents=True, exist_ok=True)
        _run(
            [sys.executable, "-m", "app.core.bootstrap"],
            cwd=backend,
            env=environment,
            timeout=120,
        )
        _extract_browser_script(repo_root, browser_script)

        fastapi_log = _open_log(fastapi_log_path)
        fastapi_process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "app.main:app",
                "--host",
                "127.0.0.1",
                "--port",
                "8000",
            ],
            cwd=backend,
            env=environment,
            text=True,
            stdout=fastapi_log,
            stderr=subprocess.STDOUT,
        )
        _wait_for_url(f"{BASE_URL}/health")

        vite_log = _open_log(vite_log_path)
        vite_process = subprocess.Popen(
            ["npm", "run", "dev", "--", "--host", "127.0.0.1", "--port", "5173"],
            cwd=frontend,
            env=environment,
            text=True,
            stdout=vite_log,
            stderr=subprocess.STDOUT,
        )
        _wait_for_url(f"{DEV_URL}/home")

        completed = _run(
            ["node", browser_script.name],
            cwd=frontend,
            env=environment,
            timeout=420,
        )
        assert report_path.is_file(), completed.stdout
        report = json.loads(report_path.read_text(encoding="utf-8"))
        assert report["target_sha"] == TARGET_SHA
        assert report["provider"] == "none"
        assert report["provider_calls"] == 0
        assert report["summary"]["failed"] == 0, json.dumps(report, indent=2)

        browser_script.unlink(missing_ok=True)
        status = _run(["git", "status", "--short"], cwd=target, timeout=30)
        assert status.stdout.strip() == ""

        summary_path = os.getenv("GITHUB_STEP_SUMMARY")
        if summary_path:
            with Path(summary_path).open("a", encoding="utf-8") as summary:
                summary.write("## APP-SHELL exact-head browser matrix\n\n")
                summary.write(f"- target: `{TARGET_SHA}`\n")
                summary.write(f"- browser: `{report['browser']}`\n")
                summary.write(f"- passed: `{report['summary']['passed']}`\n")
                summary.write(f"- failed: `{report['summary']['failed']}`\n")
                summary.write("- provider calls: `0`\n")

        with capsys.disabled():
            print(
                "APP_SHELL_BROWSER_MATRIX_JSON="
                + json.dumps(report, separators=(",", ":"), sort_keys=True),
                flush=True,
            )
    finally:
        _stop_process(vite_process)
        _stop_process(fastapi_process)
        if vite_log is not None:
            vite_log.close()
        if fastapi_log is not None:
            fastapi_log.close()
        browser_script.unlink(missing_ok=True)
        if target.exists():
            subprocess.run(
                ["git", "worktree", "remove", "--force", str(target)],
                cwd=repo_root,
                text=True,
                capture_output=True,
                timeout=60,
                check=False,
            )
