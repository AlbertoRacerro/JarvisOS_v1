import os
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest

TARGET_BRANCH = "spec/088-runs-workbench-1"
TARGET_SHA = os.getenv("TARGET_IMPLEMENTATION_SHA", "95a96030994d509b20e0c144681c32d2175a8668")
RUN_PROOF = os.getenv("RUN_RUNS_BROWSER_PROOF") == "true"


def _run(command: list[str], *, cwd: Path, env: dict[str, str], timeout: int = 300) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(command, cwd=cwd, env=env, text=True, capture_output=True, timeout=timeout, check=False)
    if result.returncode != 0:
        raise AssertionError(f"command failed: {command}\nstdout={result.stdout}\nstderr={result.stderr}")
    return result


def _wait(url: str, timeout: float = 45.0) -> None:
    deadline = time.monotonic() + timeout
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as response:
                if response.status < 500:
                    return
        except (OSError, urllib.error.URLError) as error:
            last_error = error
        time.sleep(0.5)
    raise AssertionError(f"server did not become ready: {last_error}")


def _write_script(path: Path) -> None:
    path.write_text(
        r'''import { chromium } from "playwright";

const app = "http://127.0.0.1:5173";
const api = "http://127.0.0.1:8000";
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
const assert = (value, message) => { if (!value) throw new Error(message); };
const now = "2026-08-15T08:00:00Z";
const longToken = "long-token-".repeat(90);
const workspaces = [
  { id: "workspace-a", name: "Workspace A", slug: "workspace-a", status: "active", created_at: now, updated_at: now },
  { id: "workspace-b", name: "Workspace B", slug: "workspace-b", status: "active", created_at: now, updated_at: now },
];
const run = (id, label, status, workspace="workspace-a") => ({
  id, workspace_id: workspace, model_version_id: "model-v1", run_label: label, status,
  input_payload: JSON.stringify({ feed: { value: 12, unit: "kg/s" }, long: longToken }),
  parameter_payload: JSON.stringify({ pressure: { value: 4.5, unit: "bar" } }),
  output_payload: JSON.stringify({ result: { value: 42, unit: "kg/h" } }),
  started_at: now, completed_at: "2026-08-15T08:01:00Z", created_at: now, notes: "Persisted evidence only",
});
const x = run("run-x", "Run X", "succeeded");
const y = { ...run("run-y", "Run Y", "historical_custom"), input_payload: null, output_payload: "{" };
const b = run("run-b", "Workspace B Run", "failed", "workspace-b");
let workspaceMode = "two";
let delayBList = false;
let delayYDetail = false;
let detailMode = "normal";
let logsMode = "normal";
let artifactsMode = "normal";

const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({ viewport: { width: 640, height: 500 } });
const page = await context.newPage();
const browserErrors = [];
page.on("pageerror", error => browserErrors.push(error.message));
await page.route(`${api}/**`, async route => {
  const path = decodeURIComponent(new URL(route.request().url()).pathname);
  if (path === "/workspaces") {
    if (workspaceMode === "error") return route.fulfill({ status: 503, body: "unavailable" });
    return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(workspaceMode === "empty" ? [] : workspaces) });
  }
  const list = path.match(/^\/workspaces\/([^/]+)\/simulation-runs$/);
  if (list) {
    const ws = list[1];
    if (ws === "workspace-b" && delayBList) { delayBList = false; await sleep(900); }
    return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(ws === "workspace-a" ? [x, y] : [b]) });
  }
  const artifacts = path.match(/^\/workspaces\/([^/]+)\/simulation-runs\/([^/]+)\/artifacts$/);
  if (artifacts) {
    if (artifactsMode === "error") return route.fulfill({ status: 503, body: "artifact error" });
    const rows = artifactsMode === "empty" ? [] : [{ artifact_id: "artifact-1", workspace_id: artifacts[1], simulation_run_id: artifacts[2], role: "result", artifact_type: "json", filename: longToken + ".json", relative_path: "secret/relative", stored_path: "/secret/absolute", size_bytes: 1234, created_at: now, source_ref: "runner:test", source_module: "fixture", mime_type: "application/json", sha256: "a".repeat(64), status: "ready", under_data_root: false }];
    return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(rows) });
  }
  const logs = path.match(/^\/workspaces\/([^/]+)\/simulation-runs\/([^/]+)\/logs$/);
  if (logs) {
    if (logsMode === "error") return route.fulfill({ status: 503, body: "log error" });
    const rows = logsMode === "empty" ? [] : [{ id: "log-1", workspace_id: logs[1], simulation_run_id: logs[2], stream: "stderr", content: longToken, truncated: true, created_at: now }];
    return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(rows) });
  }
  const detail = path.match(/^\/workspaces\/([^/]+)\/simulation-runs\/([^/]+)$/);
  if (detail) {
    if (detailMode === "404") return route.fulfill({ status: 404, body: "missing" });
    if (detail[2] === "run-y" && delayYDetail) { delayYDetail = false; await sleep(900); }
    const row = detail[2] === "run-x" ? x : detail[2] === "run-y" ? y : b;
    return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(row) });
  }
  return route.fulfill({ status: 404, body: "not mocked" });
});

await page.goto(`${app}/runs`, { waitUntil: "domcontentloaded" });
await page.getByRole("heading", { name: "Runs", exact: true }).waitFor();
await page.getByRole("button", { name: /Run X/ }).waitFor({ timeout: 10000 });
await page.getByRole("heading", { name: "Run X", exact: true }).waitFor();
await page.getByText("succeeded", { exact: true }).first().waitFor();
await page.getByText("truncated", { exact: true }).waitFor();
await page.getByText("Outside configured data root", { exact: true }).waitFor();
assert(!(await page.getByText("/secret/absolute", { exact: true }).count()), "stored_path leaked into UI");
assert(!(await page.getByText("secret/relative", { exact: true }).count()), "relative_path leaked into UI");
assert((await page.getByText("Presentation truncated", { exact: true }).count()) >= 1, "bounded payload presentation not reported");

const search = page.getByLabel("Search");
await search.fill("Run Y");
await page.getByText("Selected run hidden by current filter", { exact: true }).waitFor();
assert(await search.evaluate(el => document.activeElement === el), "filter lost keyboard focus");
await page.getByRole("button", { name: /Run Y/ }).focus();
await page.keyboard.press("Enter");
await page.getByRole("heading", { name: "Run Y", exact: true }).waitFor();
await page.getByText("No persisted input payload", { exact: true }).waitFor();
await page.getByText(/Payload unavailable \/ malformed/).waitFor();
await page.getByText("historical_custom", { exact: true }).first().waitFor();

await search.fill("");
delayYDetail = true;
await page.getByRole("button", { name: /Run Y/ }).click();
await page.getByRole("button", { name: /Run X/ }).click();
await page.getByRole("heading", { name: "Run X", exact: true }).waitFor();
await sleep(1100);
assert(!(await page.getByRole("heading", { name: "Run Y", exact: true }).count()), "late Y detail replaced X state");

delayBList = true;
await page.getByLabel("Workspace").selectOption("workspace-b");
await page.getByLabel("Workspace").selectOption("workspace-a");
await page.getByRole("button", { name: /Run X/ }).waitFor({ timeout: 10000 });
await sleep(1100);
assert(!(await page.getByRole("button", { name: /Workspace B Run/ }).count()), "late workspace B list replaced workspace A");

logsMode = "error";
await page.getByRole("button", { name: "Refresh", exact: true }).click();
await page.getByText(/Logs unavailable/).waitFor();
await page.getByRole("heading", { name: "Run X", exact: true }).waitFor();
logsMode = "empty";
await page.getByText("Logs").locator("..").getByRole("button", { name: "Retry" }).click();
await page.getByText("No persisted logs", { exact: true }).waitFor();

artifactsMode = "error";
await page.getByRole("button", { name: "Refresh", exact: true }).click();
await page.getByText(/Artifacts unavailable/).waitFor();
artifactsMode = "empty";
await page.getByText("Artifacts").locator("..").getByRole("button", { name: "Retry" }).click();
await page.getByText("No persisted artifacts", { exact: true }).waitFor();

detailMode = "404";
await page.getByRole("button", { name: "Refresh", exact: true }).click();
await page.getByText(/Selected run is no longer available/).waitFor();
detailMode = "normal";

const overflow = await page.evaluate(() => ({ scroll: document.documentElement.scrollWidth, client: document.documentElement.clientWidth }));
assert(overflow.scroll <= overflow.client + 1, `page-level overflow at effective 200% width: ${JSON.stringify(overflow)}`);

workspaceMode = "empty";
await page.reload({ waitUntil: "domcontentloaded" });
await page.getByText("No workspaces", { exact: true }).waitFor();
workspaceMode = "error";
await page.reload({ waitUntil: "domcontentloaded" });
await page.getByText(/Workspace discovery failed/).waitFor();

workspaceMode = "two";
await page.goto(`${app}/legacy/domain-foundation`, { waitUntil: "domcontentloaded" });
await page.getByRole("heading", { name: "Domain Foundation", exact: true }).first().waitFor({ timeout: 10000 });
assert(browserErrors.length === 0, `uncaught browser errors: ${JSON.stringify(browserErrors)}`);
await browser.close();
console.log("RUNS_BROWSER_PROOF=PASS");
''',
        encoding="utf-8",
    )


@pytest.mark.skipif(not RUN_PROOF, reason="temporary exact-head RUNS browser proof")
def test_exact_head_runs_browser_proof(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[2]
    target = tmp_path / "target"
    env = os.environ.copy()
    _run(["git", "fetch", "origin", TARGET_BRANCH, "--depth=200"], cwd=repo_root, env=env, timeout=120)
    initial = _run(["git", "rev-parse", "FETCH_HEAD"], cwd=repo_root, env=env).stdout.strip()
    assert initial == TARGET_SHA, (initial, TARGET_SHA)
    _run(["git", "worktree", "add", "--detach", str(target), TARGET_SHA], cwd=repo_root, env=env, timeout=60)
    server: subprocess.Popen[str] | None = None
    try:
        for command in (
            ["python", "scripts/check_ui_foundation.py"],
            ["python", "scripts/check_app_shell.py"],
            ["python", "scripts/check_lineage_overview.py"],
            ["python", "scripts/check_runs_workbench.py", "--self-test"],
            ["python", "scripts/check_runs_workbench.py"],
        ):
            _run(command, cwd=target, env=env)
        frontend = target / "frontend"
        _run(["npm", "ci"], cwd=frontend, env=env, timeout=300)
        harness_out = tmp_path / "harness"
        _run([str(frontend / "node_modules/.bin/tsc"), "src/components/runs/state.ts", "src/components/runs/stateHarness.ts", "--target", "ES2022", "--module", "commonjs", "--moduleResolution", "node", "--skipLibCheck", "--outDir", str(harness_out)], cwd=frontend, env=env, timeout=120)
        _run(["node", str(harness_out / "stateHarness.js")], cwd=frontend, env=env)
        _run(["npm", "run", "build"], cwd=frontend, env=env, timeout=180)
        _run(["npm", "install", "--no-save", "--package-lock=false", "playwright@1.54.2"], cwd=frontend, env=env, timeout=300)
        _run([str(frontend / "node_modules/.bin/playwright"), "install", "--with-deps", "chromium"], cwd=frontend, env=env, timeout=360)
        script = frontend / ".runs-proof.mjs"
        _write_script(script)
        server = subprocess.Popen(["npm", "run", "dev", "--", "--host", "127.0.0.1", "--port", "5173"], cwd=frontend, env=env, text=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        _wait("http://127.0.0.1:5173/runs")
        _run(["node", str(script)], cwd=frontend, env=env, timeout=420)
        script.unlink(missing_ok=True)
        _run(["git", "fetch", "origin", TARGET_BRANCH, "--depth=1"], cwd=repo_root, env=env, timeout=120)
        final = _run(["git", "rev-parse", "FETCH_HEAD"], cwd=repo_root, env=env).stdout.strip()
        assert final == TARGET_SHA, f"implementation branch moved during proof: {final}"
    finally:
        if server is not None and server.poll() is None:
            server.terminate()
            try:
                server.wait(timeout=10)
            except subprocess.TimeoutExpired:
                server.kill()
        if target.exists():
            subprocess.run(["git", "worktree", "remove", "--force", str(target)], cwd=repo_root, text=True, capture_output=True, timeout=60, check=False)
