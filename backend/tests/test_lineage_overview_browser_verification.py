import json
import os
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest

TARGET_BRANCH = "spec/087-lineage-overview-1"
TARGET_SHA = os.getenv("TARGET_IMPLEMENTATION_SHA", "2fd0330cda6903029dfc779cab2d031196b9ef81")
RUN_PROOF = os.getenv("RUN_LINEAGE_BROWSER_PROOF") == "true"


def _run(command: list[str], *, cwd: Path, env: dict[str, str], timeout: int = 300) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(command, cwd=cwd, env=env, text=True, capture_output=True, timeout=timeout, check=False)
    if result.returncode != 0:
        raise AssertionError(
            f"command failed: {command}\nstdout={result.stdout}\nstderr={result.stderr}"
        )
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


def _write_browser_script(path: Path) -> None:
    path.write_text(
        r'''import { chromium } from "playwright";

const app = "http://127.0.0.1:5173";
const api = "http://127.0.0.1:8000";
const assert = (value, message) => { if (!value) throw new Error(message); };
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));

const workspaces = [
  { id: "workspace-a", name: "Workspace A", slug: "workspace-a", status: "active", created_at: "2026-08-15T00:00:00Z", updated_at: "2026-08-15T00:00:00Z" },
  { id: "workspace-b", name: "Workspace B", slug: "workspace-b", status: "active", created_at: "2026-08-15T00:00:00Z", updated_at: "2026-08-15T00:00:00Z" }
];
const longRef = "parameter:" + "very-long-canonical-reference-".repeat(10);
const nodeA = { ref: longRef, kind: "parameter", id: "p-a", label: "Long parameter A", status: "accepted", origin: "fixture", created_at: "2026-08-15T00:00:00Z", metadata: { unit: "kg/s" } };
const nodeB = { ref: "decision:d-b", kind: "decision", id: "d-b", label: "Decision B", status: "accepted", origin: "fixture", created_at: "2026-08-15T00:00:00Z", metadata: {} };
const nodeWorkspaceB = { ref: "parameter:p-b", kind: "parameter", id: "p-b", label: "Workspace B parameter", status: "accepted", origin: "fixture", created_at: "2026-08-15T00:00:00Z", metadata: {} };
const diagnostics = { unsupported_reference_count: 0, malformed_reference_count: 0, dangling_reference_count: 0, cycle_count: 0, manual_binding_count: 0, unresolved_references: [], cycles: [] };
const graphA = { workspace_id: "workspace-a", nodes: [nodeA, nodeB], edges: [
  { id: "e1", upstream_ref: nodeA.ref, downstream_ref: nodeB.ref, relation: "feeds", edge_class: "dependency", authorities: [], source_fields: [] },
  { id: "e2", upstream_ref: nodeA.ref, downstream_ref: nodeB.ref, relation: "derived-from", edge_class: "provenance", authorities: [], source_fields: [] }
], topological_order: [nodeA.ref, nodeB.ref], is_acyclic: true, diagnostics };
const graphB = { workspace_id: "workspace-b", nodes: [nodeWorkspaceB], edges: [], topological_order: [nodeWorkspaceB.ref], is_acyclic: true, diagnostics };
const cycleGraph = { ...graphA, topological_order: null, is_acyclic: false, diagnostics: { ...diagnostics, cycle_count: 1, cycles: [[nodeA.ref, nodeB.ref, nodeA.ref]] } };

let workspaceMode = "two";
let graphMode = "normal";
let nodeMode = "normal";
let freshnessMode = "normal";
let delayNextAGraph = false;

const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({ viewport: { width: 640, height: 360 } });
const page = await context.newPage();
await page.route(`${api}/**`, async route => {
  const url = new URL(route.request().url());
  const path = decodeURIComponent(url.pathname);
  if (path === "/workspaces") {
    if (workspaceMode === "error") return route.fulfill({ status: 503, body: "unavailable" });
    return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(workspaceMode === "empty" ? [] : workspaces) });
  }
  const graphMatch = path.match(/^\/workspaces\/([^/]+)\/flowsheet\/graph$/);
  if (graphMatch) {
    const workspace = graphMatch[1];
    if (graphMode === "error") return route.fulfill({ status: 500, body: "failed" });
    if (workspace === "workspace-a" && delayNextAGraph) {
      delayNextAGraph = false;
      await sleep(900);
    }
    const body = graphMode === "cycle" && workspace === "workspace-a" ? cycleGraph : workspace === "workspace-a" ? graphA : graphB;
    return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(body) });
  }
  const freshMatch = path.match(/^\/workspaces\/([^/]+)\/flowsheet\/nodes\/(.+)\/freshness$/);
  if (freshMatch) {
    if (freshnessMode === "error") return route.fulfill({ status: 503, body: "failed" });
    const ref = freshMatch[2];
    const stale = ref === nodeA.ref;
    return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({
      record_ref: ref,
      state: stale ? "stale" : "fresh",
      invalidation_count: stale ? 1 : 0,
      latest_invalidation: stale ? { id: "inv-1", source_ref: "parameter:old", replacement_ref: nodeA.ref, affected_count: 1, graph_digest: null, reason_code: "superseded", path: ["parameter:old", nodeA.ref], path_digest: null, created_at: "2026-08-15T00:00:00Z" } : null
    }) });
  }
  const nodeMatch = path.match(/^\/workspaces\/([^/]+)\/flowsheet\/nodes\/(.+)$/);
  if (nodeMatch) {
    if (nodeMode === "404") return route.fulfill({ status: 404, body: "missing" });
    const ref = nodeMatch[2];
    const node = ref === nodeA.ref ? nodeA : ref === nodeB.ref ? nodeB : nodeWorkspaceB;
    return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(node) });
  }
  return route.fulfill({ status: 404, body: "not mocked" });
});

async function openNavigator() {
  if (!(await page.getByLabel("Workspace").count())) {
    await page.getByRole("button", { name: "Show navigator", exact: true }).click();
  }
  await page.getByLabel("Workspace").waitFor();
}

workspaceMode = "two"; graphMode = "normal"; nodeMode = "normal"; freshnessMode = "normal";
await page.goto(`${app}/design/flowsheet`, { waitUntil: "domcontentloaded" });
await page.getByText("Long parameter A", { exact: true }).waitFor({ timeout: 10000 });
await page.getByText("dependency", { exact: true }).first().waitFor();
await page.getByText("provenance", { exact: true }).first().waitFor();
await page.getByText(/Historical status remains accepted/).waitFor();

await openNavigator();
delayNextAGraph = true;
await page.reload({ waitUntil: "domcontentloaded" });
await openNavigator();
await page.getByLabel("Workspace").selectOption("workspace-b");
await page.getByText("Workspace B parameter", { exact: true }).waitFor({ timeout: 10000 });
await sleep(1100);
assert(!(await page.getByText("Long parameter A", { exact: true }).count()), "late workspace-a graph replaced workspace-b state");

workspaceMode = "empty";
await page.reload({ waitUntil: "domcontentloaded" });
await page.getByText("No workspaces are available.", { exact: true }).first().waitFor();
workspaceMode = "error";
await page.reload({ waitUntil: "domcontentloaded" });
await page.getByText(/Workspace discovery failed/).first().waitFor();

workspaceMode = "two"; graphMode = "error";
await page.reload({ waitUntil: "domcontentloaded" });
await page.getByText(/Request failed with 500/).waitFor();
graphMode = "cycle";
await page.reload({ waitUntil: "domcontentloaded" });
await page.getByText("Cycles present", { exact: true }).waitFor();
await page.getByRole("button", { name: /Diagnostics/ }).click();
await page.getByText(/Cycle:/).waitFor();

graphMode = "normal"; freshnessMode = "error";
await page.reload({ waitUntil: "domcontentloaded" });
await page.getByText(/Freshness is unavailable for this node/).waitFor();
freshnessMode = "normal"; nodeMode = "404";
await page.reload({ waitUntil: "domcontentloaded" });
await page.getByText(/no longer resolvable/).waitFor();

nodeMode = "normal";
await page.reload({ waitUntil: "domcontentloaded" });
await openNavigator();
const search = page.getByLabel("Search lineage");
await search.focus();
await search.fill("Decision B");
await page.getByText("Selected node is hidden by the current filter.").waitFor();
assert(await search.evaluate(el => document.activeElement === el), "filter moved keyboard focus");
const overflow = await page.evaluate(() => ({ scroll: document.documentElement.scrollWidth, client: document.documentElement.clientWidth }));
assert(overflow.scroll <= overflow.client + 1, `page-level overflow at effective 200% width: ${JSON.stringify(overflow)}`);

for (const [url, heading] of [["/design/model", "Model workbench"], ["/design/results", "Results"], ["/design/review", "Review"]]) {
  await page.goto(app + url, { waitUntil: "domcontentloaded" });
  await page.getByRole("heading", { name: heading }).first().waitFor({ timeout: 10000 });
}

await browser.close();
console.log("LINEAGE_BROWSER_PROOF=PASS");
''',
        encoding="utf-8",
    )


@pytest.mark.skipif(not RUN_PROOF, reason="temporary exact-head lineage browser proof")
def test_exact_head_lineage_browser_proof(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[2]
    target = tmp_path / "target"
    env = os.environ.copy()
    _run(["git", "fetch", "origin", TARGET_BRANCH, "--depth=200"], cwd=repo_root, env=env, timeout=120)
    initial = _run(["git", "rev-parse", "FETCH_HEAD"], cwd=repo_root, env=env).stdout.strip()
    assert initial == TARGET_SHA, (initial, TARGET_SHA)
    _run(["git", "worktree", "add", "--detach", str(target), TARGET_SHA], cwd=repo_root, env=env, timeout=60)
    server: subprocess.Popen[str] | None = None
    try:
        _run(["python", "scripts/check_lineage_overview.py", "--self-test"], cwd=target, env=env)
        _run(["python", "scripts/check_lineage_overview.py"], cwd=target, env=env)
        frontend = target / "frontend"
        _run(["npm", "ci"], cwd=frontend, env=env, timeout=300)
        _run(["npm", "run", "build"], cwd=frontend, env=env, timeout=180)
        _run(["npm", "install", "--no-save", "--package-lock=false", "playwright@1.54.2"], cwd=frontend, env=env, timeout=300)
        _run([str(frontend / "node_modules/.bin/playwright"), "install", "--with-deps", "chromium"], cwd=frontend, env=env, timeout=360)
        script = frontend / ".lineage-proof.mjs"
        _write_browser_script(script)
        server = subprocess.Popen(
            ["npm", "run", "dev", "--", "--host", "127.0.0.1", "--port", "5173"],
            cwd=frontend,
            env=env,
            text=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.STDOUT,
        )
        _wait("http://127.0.0.1:5173/design/flowsheet")
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
