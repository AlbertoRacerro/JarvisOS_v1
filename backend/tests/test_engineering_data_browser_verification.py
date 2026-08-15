from __future__ import annotations

import os
import subprocess
import time
import urllib.request
from pathlib import Path

import pytest


RUN_PROOF = os.environ.get("RUN_ENGINEERING_DATA_BROWSER_PROOF") == "true"
TARGET_SHA = os.environ.get("TARGET_IMPLEMENTATION_SHA", "1e779a06d9e055509061d133d523c0883f0f7adf")
TARGET_BRANCH = "spec/035-engineering-data-1"


def _run(command: list[str], *, cwd: Path, env: dict[str, str], timeout: int = 300) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(command, cwd=cwd, env=env, text=True, capture_output=True, timeout=timeout, check=False)
    if result.returncode != 0:
        raise AssertionError(f"command failed: {command}\nstdout={result.stdout}\nstderr={result.stderr}")
    return result


def _wait(url: str, timeout: float = 20.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1) as response:
                if response.status < 500:
                    return
        except Exception:
            time.sleep(0.2)
    raise AssertionError(f"server did not become ready: {url}")


def _write_script(path: Path) -> None:
    path.write_text(
        r'''import { chromium } from "playwright";

const app = "http://127.0.0.1:5173";
const api = "http://127.0.0.1:8000";
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
const assert = (value, message) => { if (!value) throw new Error(message); };
const now = "2026-08-15T12:00:00Z";
const longToken = "engineering-long-token-".repeat(150);
const workspaces = [
  { id: "workspace-a", name: "Workspace A", slug: "workspace-a", status: "active", created_at: now, updated_at: now },
  { id: "workspace-b", name: "Workspace B", slug: "workspace-b", status: "active", created_at: now, updated_at: now },
];
const records = {
  "workspace-a": {
    "model-specs": [
      { id: "m-z", workspace_id: "workspace-a", title: "zeta", engineering_question: "Secondary question", scope: null, status: "historical_custom", maturity_status: "draft", schema_version: 1, created_at: now, updated_at: now },
      { id: "m-a", workspace_id: "workspace-a", title: "Alpha", engineering_question: "Pump sizing", scope: longToken, status: "active", maturity_status: "review", schema_version: 2, created_at: now, updated_at: now },
    ],
    assumptions: [{ id: "a-1", workspace_id: "workspace-a", statement: "Sea water density", confidence: null, status: "accepted" }],
    parameters: [{ id: "p-1", workspace_id: "workspace-a", name: "Tube diameter", symbol: longToken, value: "0.05", unit: longToken, status: "active" }],
    decisions: [{ id: "d-1", workspace_id: "workspace-a", title: "Material", decision_text: longToken, status: "recorded" }],
  },
  "workspace-b": {
    "model-specs": [{ id: "m-b", workspace_id: "workspace-b", title: "Workspace B Spec", engineering_question: "B question", scope: "B", status: "active", maturity_status: "draft", schema_version: 1, created_at: now, updated_at: now }],
    assumptions: [], parameters: [], decisions: [],
  },
};
let workspaceMode = "two";
let failKind = null;
let delayWorkspaceB = false;
let removeDecision = false;

const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({ viewport: { width: 640, height: 520 } });
const page = await context.newPage();
const browserErrors = [];
page.on("pageerror", error => browserErrors.push(error.message));
await page.route(`${api}/**`, async route => {
  const path = decodeURIComponent(new URL(route.request().url()).pathname);
  if (path === "/workspaces") {
    if (workspaceMode === "error") return route.fulfill({ status: 503, body: "unavailable" });
    return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(workspaceMode === "empty" ? [] : workspaces) });
  }
  const match = path.match(/^\/workspaces\/([^/]+)\/(model-specs|assumptions|parameters|decisions)$/);
  if (match) {
    const [, ws, kind] = match;
    if (ws === "workspace-b" && delayWorkspaceB) { delayWorkspaceB = false; await sleep(900); }
    if (failKind === kind) return route.fulfill({ status: 503, body: `${kind} unavailable` });
    let rows = records[ws]?.[kind] ?? [];
    if (ws === "workspace-a" && kind === "decisions" && removeDecision) rows = [];
    return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(rows) });
  }
  return route.fulfill({ status: 404, body: "not mocked" });
});

await page.goto(`${app}/engineering-data`, { waitUntil: "domcontentloaded" });
await page.getByRole("heading", { name: "Engineering Data", exact: true }).waitFor();
await page.getByRole("button", { name: /Alpha/ }).waitFor({ timeout: 10000 });
const recordButtons = page.locator(".engineering-record");
assert(await recordButtons.count() === 5, "four supported kinds did not render expected rows");
assert((await recordButtons.nth(0).innerText()).includes("Alpha"), "model-spec primary ordering drift");
assert((await recordButtons.nth(1).innerText()).includes("zeta"), "model-spec stable ordering drift");
assert((await recordButtons.nth(2).innerText()).includes("Sea water density"), "assumption kind order drift");
assert((await recordButtons.nth(3).innerText()).includes("Tube diameter"), "parameter kind order drift");
assert((await recordButtons.nth(4).innerText()).includes("Material"), "decision kind order drift");
await page.getByText("historical_custom", { exact: true }).waitFor();
assert(!(await page.getByText("Fresh", { exact: true }).count()), "fake freshness authority rendered");
assert(!(await page.getByText("Proposed", { exact: true }).count()), "fake proposal authority rendered");

const search = page.getByLabel("Search");
await search.fill("pump sizing");
assert(await recordButtons.count() === 1, "explicit-field search failed");
assert((await recordButtons.first().innerText()).includes("Alpha"), "search returned wrong row");
assert(await search.evaluate(el => document.activeElement === el), "search lost focus");
await search.fill("0.05");
assert(await recordButtons.count() === 1 && (await recordButtons.first().innerText()).includes("Tube diameter"), "parameter persisted value search failed");
await search.fill("");

const decisionsFilter = page.getByLabel("Decisions");
await decisionsFilter.uncheck();
assert(!(await page.getByRole("button", { name: /Material/ }).count()), "kind filter failed");
await decisionsFilter.check();
await page.getByRole("button", { name: /Material/ }).click();
await page.getByRole("heading", { name: "Material", exact: true }).waitFor();

removeDecision = true;
await page.getByRole("button", { name: "Refresh", exact: true }).click();
await page.getByRole("button", { name: /Alpha/ }).waitFor();
await page.getByRole("heading", { name: "Alpha", exact: true }).waitFor();
removeDecision = false;

for (const [kind, label] of [["model-specs", "Model specs unavailable."], ["assumptions", "Assumptions unavailable."], ["parameters", "Parameters unavailable."], ["decisions", "Decisions unavailable."]]) {
  failKind = kind;
  await page.getByRole("button", { name: "Refresh", exact: true }).click();
  await page.getByText(label, { exact: true }).waitFor();
  assert(await page.locator(".engineering-record").count() >= 3, `partial ${kind} failure discarded healthy kinds`);
  failKind = null;
  await page.getByRole("button", { name: "Refresh", exact: true }).click();
  await page.getByRole("button", { name: /Alpha/ }).waitFor();
}

// A -> B -> A with late B responses must not repaint A.
delayWorkspaceB = true;
await page.getByLabel("Workspace").selectOption("workspace-b");
await page.getByLabel("Workspace").selectOption("workspace-a");
await page.getByRole("button", { name: /Alpha/ }).waitFor({ timeout: 10000 });
await sleep(1200);
assert(!(await page.getByRole("button", { name: /Workspace B Spec/ }).count()), "late workspace B response repainted A");

// Null historical fields are explicit and persisted confidence is not reinterpreted.
await page.getByRole("button", { name: /Sea water density/ }).click();
await page.getByText("Confidence (persisted)", { exact: true }).waitFor();
assert((await page.getByText("Unavailable", { exact: true }).count()) >= 1, "nullable historical field fabricated or omitted");

// Keyboard path and containment at effective 200% width.
await search.focus();
await page.keyboard.press("Tab");
assert(await page.evaluate(() => document.activeElement instanceof HTMLElement), "keyboard route lost focus");
const overflow = await page.evaluate(() => ({ scroll: document.documentElement.scrollWidth, client: document.documentElement.clientWidth }));
assert(overflow.scroll <= overflow.client + 1, `page-level overflow at effective 200% width: ${JSON.stringify(overflow)}`);

await page.getByRole("link", { name: "Open lineage" }).click();
await page.waitForURL(/\/design\/flowsheet$/);
await page.goto(`${app}/runs`, { waitUntil: "domcontentloaded" });
await page.getByRole("heading", { name: "Runs", exact: true }).waitFor({ timeout: 10000 });
await page.goto(`${app}/legacy/domain-foundation`, { waitUntil: "domcontentloaded" });
await page.getByRole("heading", { name: "Domain Foundation", exact: true }).first().waitFor({ timeout: 10000 });

workspaceMode = "empty";
await page.goto(`${app}/engineering-data`, { waitUntil: "domcontentloaded" });
await page.getByText("No workspaces are available.", { exact: true }).waitFor();
workspaceMode = "error";
await page.reload({ waitUntil: "domcontentloaded" });
await page.getByText(/Workspace discovery failed/).waitFor();

assert(browserErrors.length === 0, `uncaught browser errors: ${JSON.stringify(browserErrors)}`);
await browser.close();
console.log("ENGINEERING_DATA_BROWSER_PROOF=PASS");
''',
        encoding="utf-8",
    )


@pytest.mark.skipif(not RUN_PROOF, reason="temporary exact-head ENGINEERING-DATA browser proof")
def test_exact_head_engineering_data_browser_proof(tmp_path: Path) -> None:
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
            ["python", "scripts/check_spec_status.py", "--self-test"],
            ["python", "scripts/check_ui_foundation.py"],
            ["python", "scripts/check_app_shell.py"],
            ["python", "scripts/check_lineage_overview.py"],
            ["python", "scripts/check_runs_workbench.py"],
            ["python", "scripts/check_engineering_data.py", "--self-test"],
            ["python", "scripts/check_engineering_data.py"],
        ):
            _run(command, cwd=target, env=env)
        frontend = target / "frontend"
        _run(["npm", "ci"], cwd=frontend, env=env, timeout=300)
        harness_out = tmp_path / "harness"
        _run([str(frontend / "node_modules/.bin/tsc"), "src/components/engineering-data/engineeringDataState.ts", "src/components/engineering-data/engineeringDataStateHarness.ts", "--target", "ES2022", "--module", "commonjs", "--moduleResolution", "node", "--skipLibCheck", "--outDir", str(harness_out)], cwd=frontend, env=env, timeout=120)
        _run(["node", str(harness_out / "engineeringDataStateHarness.js")], cwd=frontend, env=env)
        _run(["npm", "run", "build"], cwd=frontend, env=env, timeout=180)
        _run(["npm", "install", "--no-save", "--package-lock=false", "playwright@1.54.2"], cwd=frontend, env=env, timeout=300)
        _run([str(frontend / "node_modules/.bin/playwright"), "install", "--with-deps", "chromium"], cwd=frontend, env=env, timeout=360)
        script = frontend / ".engineering-data-proof.mjs"
        _write_script(script)
        server = subprocess.Popen(["npm", "run", "dev", "--", "--host", "127.0.0.1", "--port", "5173"], cwd=frontend, env=env, text=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        _wait("http://127.0.0.1:5173/engineering-data")
        _run(["node", str(script)], cwd=frontend, env=env, timeout=180)
    finally:
        if server is not None:
            server.terminate()
            try:
                server.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server.kill()
