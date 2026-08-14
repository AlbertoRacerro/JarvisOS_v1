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

TARGET_SHA = "1c61b7a4776cd0a56f3c71a9b0237b31da1308d2"
TARGET_BRANCH = "spec/085-bluecad-workbench-2"
BASE_URL = "http://127.0.0.1:8000"
RUN_PROOF = os.getenv("RUN_BLUECAD_WORKBENCH_BROWSER_PROOF") == "true"


def _run(command: list[str], *, cwd: Path, env: dict[str, str], timeout: int = 300) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(command, cwd=cwd, env=env, text=True, capture_output=True, timeout=timeout, check=False)
    if completed.returncode != 0:
        raise AssertionError(
            "command failed\n"
            f"cwd={cwd}\ncommand={command}\nexit={completed.returncode}\n"
            f"stdout={completed.stdout}\nstderr={completed.stderr}"
        )
    return completed


def _wait_for_url(url: str, timeout: float = 60.0) -> None:
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


def _stop(process: subprocess.Popen[str] | None) -> None:
    if process is None or process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=10)


def _write_seed_script(path: Path) -> None:
    path.write_text(
        '''import json
import struct
from pathlib import Path
from app.core.database import open_sqlite_connection
from app.modules.bluecad.ledger import (
    create_candidate_record,
    finish_attempt,
    mark_candidate_valid,
    park_candidate,
    register_artifact,
    start_attempt,
    update_candidate_artifacts,
)
from app.modules.bluecad.models import BluecadLoopConfig

with open_sqlite_connection() as connection:
    row = connection.execute("SELECT id FROM workspaces ORDER BY created_at LIMIT 1").fetchone()
    if row is None:
        raise SystemExit("default workspace missing")
    workspace_id = str(row["id"])
    connection.execute("UPDATE workspaces SET name = ? WHERE id = ?", ("BLUECAD-" + "LONGWORKSPACENAME" * 12, workspace_id))
    connection.commit()

gltf = {
    "asset": {"version": "2.0"},
    "scene": 0,
    "scenes": [{"nodes": [0]}],
    "nodes": [{"mesh": 0}],
    "meshes": [{"primitives": [{"attributes": {"POSITION": 0}}]}],
    "buffers": [{"byteLength": 36}],
    "bufferViews": [{"buffer": 0, "byteOffset": 0, "byteLength": 36, "target": 34962}],
    "accessors": [{"bufferView": 0, "componentType": 5126, "count": 3, "type": "VEC3", "min": [0, 0, 0], "max": [1, 1, 0]}],
}
json_bytes = json.dumps(gltf, separators=(",", ":")).encode()
json_bytes += b" " * ((4 - len(json_bytes) % 4) % 4)
bin_bytes = struct.pack("<9f", 0, 0, 0, 1, 0, 0, 0, 1, 0)
total = 12 + 8 + len(json_bytes) + 8 + len(bin_bytes)
glb = struct.pack("<III", 0x46546C67, 2, total)
glb += struct.pack("<II", len(json_bytes), 0x4E4F534A) + json_bytes
glb += struct.pack("<II", len(bin_bytes), 0x004E4942) + bin_bytes
source = Path("/tmp/bluecad-proof.glb")
source.write_bytes(glb)
report_source = Path("/tmp/bluecad-proof-validation.json")
report_source.write_text(json.dumps({
    "checks": [
        {
            "id": "dimension-check",
            "tier": 1,
            "status": "pass",
            "detail": {"actual": 1.01, "declared": 1.0, "rel_err": 0.01, "rel_tol": 0.02},
            "hint": "Within tolerance",
        },
        {
            "id": "irregular-detail",
            "tier": "2",
            "verdict": "warn",
            "detail": {"message": "irregular", "values": [1, 2]},
            "hint": "Inspect manually",
        },
    ]
}))

parked = create_candidate_record(workspace_id, "Browser proof parked candidate", BluecadLoopConfig())
for attempt_no in (1, 2):
    attempt = start_attempt(parked.id, attempt_no, "local", prompt_version="proof-v1")
    finish_attempt(
        attempt.id,
        proposal_outcome="malformed",
        build_outcome="failed",
        validation_verdict="fail",
        error_detail={"reason": f"fixture attempt {attempt_no}"},
    )
park_candidate(parked.id, "fixture parked after two failed attempts")

def add_valid(brief, with_report=False):
    candidate = create_candidate_record(workspace_id, brief, BluecadLoopConfig())
    glb_id = register_artifact(workspace_id, source, role="bluecad_glb", source_ref=f"bluecad_candidate:{candidate.id}", producer_notes="Temporary exact-head browser proof fixture.")
    report_id = None
    if with_report:
        report_id = register_artifact(workspace_id, report_source, role="bluecad_validation_report", source_ref=f"bluecad_candidate:{candidate.id}", producer_notes="Temporary exact-head browser proof fixture.")
    update_candidate_artifacts(candidate.id, spec_artifact_id=None, glb_artifact_id=glb_id, report_artifact_id=report_id)
    mark_candidate_valid(candidate.id)
    return candidate

valid = add_valid("Browser proof valid candidate", with_report=True)
alternate = add_valid("Browser proof alternate GLB candidate")
Path("/tmp/bluecad-proof-seed.json").write_text(json.dumps({
    "workspace_id": workspace_id,
    "candidate_id": valid.id,
    "alternate_candidate_id": alternate.id,
    "parked_candidate_id": parked.id,
}))
''',
        encoding="utf-8",
    )


def _write_browser_script(path: Path) -> None:
    path.write_text(
        '''import fs from "node:fs";
import { chromium } from "playwright";

const base = process.env.BASE_URL;
const results = [];
const errors = [];
const assert = (value, message) => { if (!value) throw new Error(message); };
async function check(name, fn) {
  try { await fn(); results.push({ name, status: "PASS" }); }
  catch (error) { results.push({ name, status: "FAIL", error: error?.stack ?? String(error) }); }
}
const candidateListResponse = page => page.waitForResponse(response => {
  const url = new URL(response.url());
  return response.request().method() === "GET" && /\\/workspaces\\/[^/]+\\/bluecad\\/candidates$/.test(url.pathname) && response.ok();
});
const candidateDetailResponse = page => page.waitForResponse(response => {
  const url = new URL(response.url());
  return response.request().method() === "GET" && /\\/workspaces\\/[^/]+\\/bluecad\\/candidates\\/[^/]+\\/aggregate$/.test(url.pathname) && response.ok();
});
const focusSnapshot = page => page.evaluate(() => ({
  tag: document.activeElement?.tagName ?? "",
  id: document.activeElement?.id ?? "",
  className: typeof document.activeElement?.className === "string" ? document.activeElement.className : "",
  text: document.activeElement?.textContent ?? ""
}));
const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({ viewport: { width: 640, height: 360 } });
const page = await context.newPage();
let delayedFirstGlb = false;
let releaseFirstGlb;
const firstGlbGate = new Promise(resolve => { releaseFirstGlb = resolve; });
await page.route("**/bluecad/artifacts/**/content", async route => {
  if (!delayedFirstGlb) {
    delayedFirstGlb = true;
    await firstGlbGate;
  }
  await route.continue();
});
page.on("pageerror", e => errors.push(`page:${e.message}`));
page.on("console", m => { if (m.type() === "error") errors.push(`console:${m.text()}`); });
await page.goto(`${base}/design/model`, { waitUntil: "domcontentloaded" });
await page.locator("#app-main").waitFor({ state: "visible" });
await page.getByRole("heading", { name: "Model workbench" }).waitFor();

await check("compact-layout-and-200-percent-overflow", async () => {
  await page.getByRole("button", { name: "Show navigator", exact: true }).click();
  await page.locator("#shell-navigator").waitFor();
  const size = await page.evaluate(() => ({ sw: document.documentElement.scrollWidth, cw: document.documentElement.clientWidth }));
  assert(size.sw <= size.cw + 1, `document overflow ${JSON.stringify(size)}`);
  const select = page.getByLabel("Workspace");
  const contained = await select.evaluate(el => {
    const a = el.getBoundingClientRect();
    const p = el.parentElement?.getBoundingClientRect();
    return !!p && a.left >= p.left - 1 && a.right <= p.right + 1;
  });
  assert(contained, "long workspace selector exceeds navigator label");
  const viewport = page.locator(".bluecad-workbench__viewport");
  const box = await viewport.boundingBox();
  assert(box && box.width >= 180 && box.height >= 120, `primary viewport collapsed ${JSON.stringify(box)}`);
});

await check("artifact-replacement-and-late-glb-completion", async () => {
  const selected = page.locator(".bluecad-candidate[aria-pressed='true']");
  await selected.waitFor({ timeout: 15000 });
  const selectedText = await selected.textContent();
  const other = selectedText?.includes("alternate GLB")
    ? page.getByRole("button", { name: /Browser proof valid candidate/ })
    : page.getByRole("button", { name: /Browser proof alternate GLB candidate/ });
  const canvas = page.getByRole("img", { name: "Interactive 3D preview of generated BLUECAD geometry" });
  await canvas.waitFor({ timeout: 15000 });
  await canvas.evaluate(el => { el.dataset.proofCanvas = "stale"; });
  await other.click();
  await page.getByText("Orbit, pan, and zoom to inspect the generated geometry.").waitFor({ timeout: 15000 });
  const replacementCanvas = page.getByRole("img", { name: "Interactive 3D preview of generated BLUECAD geometry" });
  assert((await replacementCanvas.evaluate(el => el.dataset.proofCanvas ?? "")) !== "stale", "artifact replacement retained prior canvas");
  releaseFirstGlb();
  await page.waitForTimeout(500);
  await page.getByText("Orbit, pan, and zoom to inspect the generated geometry.").waitFor();
});

await check("real-glb-loads-and-resizes-with-shell", async () => {
  await page.getByRole("button", { name: /Browser proof valid candidate/ }).click();
  const canvas = page.getByRole("img", { name: "Interactive 3D preview of generated BLUECAD geometry" });
  await canvas.waitFor({ timeout: 15000 });
  await page.getByText("Orbit, pan, and zoom to inspect the generated geometry.").waitFor({ timeout: 15000 });
  const before = await canvas.boundingBox();
  await page.getByRole("button", { name: "Show context", exact: true }).click();
  await page.waitForTimeout(250);
  const after = await canvas.boundingBox();
  assert(before && after && after.width !== before.width, `viewer did not resize ${JSON.stringify({ before, after })}`);
});

await check("structured-validation-detail-is-readable", async () => {
  await page.getByRole("button", { name: /Browser proof valid candidate/ }).click();
  await page.getByText("actual 1.01 vs declared 1").waitFor({ timeout: 15000 });
  await page.getByText(/rel err 1.00% \/ tol 2.00%/).waitFor();
  await page.getByText(/message: irregular/).waitFor();
  await page.getByText(/values: \[1,2\]/).waitFor();
  const sidecarText = await page.locator("#shell-sidecar").innerText();
  assert(!sidecarText.includes("[object Object]"), "validation detail rendered opaque object");
});

await check("parked-candidate-reason-and-attempt-trail", async () => {
  await page.getByRole("button", { name: /Browser proof parked candidate/ }).click();
  await page.getByText("Parked reason: fixture parked after two failed attempts").waitFor({ timeout: 15000 });
  await page.getByRole("heading", { name: "Geometry unavailable" }).waitFor();
  if (!(await page.locator("#shell-analysis-dock").count())) await page.getByRole("button", { name: "Show analysis", exact: true }).click();
  await page.getByText(/fixture attempt 1/).waitFor();
  await page.getByText(/fixture attempt 2/).waitFor();
});

await check("duplicate-brief-opens-navigator-and-focuses-textarea", async () => {
  await page.getByRole("button", { name: /Browser proof valid candidate/ }).click();
  if (await page.locator("#shell-navigator").count()) {
    await page.locator("#shell-navigator").press("Escape");
    await page.locator("#shell-navigator").waitFor({ state: "detached" });
  }
  await page.getByRole("button", { name: "Duplicate brief", exact: true }).click();
  const textarea = page.getByLabel("New candidate brief");
  await textarea.waitFor();
  await page.waitForFunction(() => document.activeElement?.tagName === "TEXTAREA");
  assert((await textarea.inputValue()) === "Browser proof valid candidate", "duplicate brief did not preserve source text");
});

await check("create-refresh-archive-use-canonical-reloads", async () => {
  const textarea = page.getByLabel("New candidate brief");
  await textarea.fill("Browser proof created candidate");
  const createReload = candidateListResponse(page);
  await page.getByRole("button", { name: "New candidate", exact: true }).click();
  await createReload;
  await page.getByText("Candidate created.").waitFor({ timeout: 15000 });
  await page.getByText("Browser proof created candidate", { exact: false }).first().waitFor();

  const refreshReload = candidateListResponse(page);
  await page.getByRole("button", { name: "Refresh", exact: true }).click();
  await refreshReload;

  const archiveReload = candidateListResponse(page);
  await page.getByRole("button", { name: "Archive", exact: true }).click();
  await archiveReload;
  await page.getByText("Candidate archived.").waitFor({ timeout: 15000 });
  assert(!(await page.getByRole("button", { name: /Browser proof created candidate/ }).count()), "archived candidate remained visible");
  const selectedReplacement = page.locator(".bluecad-candidate[aria-pressed='true']");
  await selectedReplacement.waitFor();
  assert(await selectedReplacement.evaluate(el => document.activeElement === el), `archive focus ${JSON.stringify(await focusSnapshot(page))}`);
});

await check("promote-reloads-canonical-detail-and-restores-focus", async () => {
  const valid = page.getByRole("button", { name: /Browser proof valid candidate/ });
  await valid.click();
  const promote = page.getByRole("button", { name: "Promote to Decision", exact: true });
  await promote.waitFor();
  const detailReload = candidateDetailResponse(page);
  await promote.focus();
  await promote.press("Enter");
  await detailReload;
  await page.getByText(/Promoted to Decision/).waitFor({ timeout: 15000 });
  await page.waitForTimeout(150);
  const focus = await focusSnapshot(page);
  const candidateFocus = focus.tag === "BUTTON" && focus.className.includes("bluecad-candidate") && focus.text.includes("Browser proof valid candidate");
  assert(candidateFocus || focus.id === "bluecad-workbench-title", `unexpected focus ${JSON.stringify(focus)}`);
});

await check("no-uncaught-browser-errors", async () => assert(errors.length === 0, errors.join("\\n")));
await context.close();
await browser.close();
const report = {
  schema: "jarvisos.bluecad-workbench-browser-proof.v1",
  target_sha: process.env.TARGET_SHA,
  results,
  errors,
  summary: {
    passed: results.filter(x => x.status === "PASS").length,
    failed: results.filter(x => x.status === "FAIL").length
  }
};
fs.writeFileSync(process.env.PROOF_REPORT, JSON.stringify(report, null, 2) + "\\n");
console.log("BLUECAD_WORKBENCH_BROWSER_PROOF=" + JSON.stringify(report));
if (report.summary.failed) process.exit(1);
''',
        encoding="utf-8",
    )


@pytest.mark.skipif(not RUN_PROOF, reason="temporary exact-head BLUECAD browser proof runs only in its dedicated workflow")
def test_exact_head_bluecad_workbench_browser_proof(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    repo_root = Path(__file__).resolve().parents[2]
    target = tmp_path / "target"
    data_root = tmp_path / "data"
    report_path = tmp_path / "bluecad-workbench-proof.json"
    seed_script = tmp_path / "seed.py"
    log_path = tmp_path / "fastapi.log"
    harness_out = tmp_path / "harness"
    server: subprocess.Popen[str] | None = None
    log: TextIO | None = None
    browser_script: Path | None = None
    env = os.environ.copy()
    env.update({
        "JARVISOS_DATA_ROOT": str(data_root),
        "JARVISOS_AI_PROVIDER": "none",
        "JARVISOS_ENV": "browser-verification",
        "BASE_URL": BASE_URL,
        "TARGET_SHA": TARGET_SHA,
        "PROOF_REPORT": str(report_path),
    })
    try:
        _run(["git", "fetch", "origin", TARGET_BRANCH, "--depth=200"], cwd=repo_root, env=env, timeout=120)
        initial_remote_head = _run(["git", "rev-parse", "FETCH_HEAD"], cwd=repo_root, env=env, timeout=30).stdout.strip()
        assert initial_remote_head == TARGET_SHA
        _run(["git", "worktree", "add", "--detach", str(target), TARGET_SHA], cwd=repo_root, env=env, timeout=60)
        assert _run(["git", "rev-parse", "HEAD"], cwd=target, env=env, timeout=30).stdout.strip() == TARGET_SHA

        _run([sys.executable, "scripts/check_spec_status.py", "--self-test"], cwd=target, env=env, timeout=120)
        _run([sys.executable, "scripts/check_ui_foundation.py"], cwd=target, env=env, timeout=120)
        _run([sys.executable, "scripts/check_app_shell.py"], cwd=target, env=env, timeout=120)
        _run([sys.executable, "scripts/check_bluecad_read_model.py"], cwd=target, env=env, timeout=120)
        _run([sys.executable, "scripts/check_bluecad_workbench.py", "--self-test"], cwd=target, env=env, timeout=120)
        _run([sys.executable, "scripts/check_bluecad_workbench.py"], cwd=target, env=env, timeout=120)

        frontend = target / "frontend"
        backend = target / "backend"
        browser_script = frontend / ".bluecad-workbench-proof.mjs"
        env["PYTHONPATH"] = str(backend)
        _run(["npm", "ci"], cwd=frontend, env=env, timeout=300)
        _run([
            str(frontend / "node_modules" / ".bin" / "tsc"),
            "src/components/bluecad/workbenchState.ts",
            "src/components/bluecad/workbenchStateHarness.ts",
            "--target", "ES2022",
            "--module", "commonjs",
            "--moduleResolution", "node",
            "--skipLibCheck",
            "--outDir", str(harness_out),
        ], cwd=frontend, env=env, timeout=120)
        _run(["node", str(harness_out / "workbenchStateHarness.js")], cwd=frontend, env=env, timeout=60)
        _run(["npm", "run", "build"], cwd=frontend, env=env, timeout=180)
        _run(["npm", "install", "--no-save", "--package-lock=false", "playwright@1.54.2"], cwd=frontend, env=env, timeout=300)
        _run([str(frontend / "node_modules" / ".bin" / "playwright"), "install", "--with-deps", "chromium"], cwd=frontend, env=env, timeout=360)

        data_root.mkdir(parents=True, exist_ok=True)
        _run([sys.executable, "-m", "app.core.bootstrap"], cwd=backend, env=env, timeout=120)
        _write_seed_script(seed_script)
        _run([sys.executable, str(seed_script)], cwd=backend, env=env, timeout=60)

        log = log_path.open("w", encoding="utf-8")
        server = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"],
            cwd=backend,
            env=env,
            text=True,
            stdout=log,
            stderr=subprocess.STDOUT,
        )
        _wait_for_url(f"{BASE_URL}/health")
        _write_browser_script(browser_script)
        completed = _run(["node", str(browser_script)], cwd=frontend, env=env, timeout=420)
        assert report_path.is_file(), completed.stdout
        report = json.loads(report_path.read_text(encoding="utf-8"))
        assert report["target_sha"] == TARGET_SHA
        assert report["summary"]["failed"] == 0, json.dumps(report, indent=2)

        _run(["git", "fetch", "origin", TARGET_BRANCH, "--depth=1"], cwd=repo_root, env=env, timeout=120)
        final_remote_head = _run(["git", "rev-parse", "FETCH_HEAD"], cwd=repo_root, env=env, timeout=30).stdout.strip()
        assert final_remote_head == TARGET_SHA, f"target branch moved during proof: {final_remote_head}"

        browser_script.unlink(missing_ok=True)
        status = _run(["git", "status", "--short"], cwd=target, env=env, timeout=30).stdout.strip()
        assert status == "", status
        with capsys.disabled():
            print("BLUECAD_WORKBENCH_BROWSER_PROOF_JSON=" + json.dumps(report, separators=(",", ":"), sort_keys=True), flush=True)
    finally:
        _stop(server)
        if log is not None:
            log.close()
        if browser_script is not None:
            browser_script.unlink(missing_ok=True)
        if target.exists():
            subprocess.run(["git", "worktree", "remove", "--force", str(target)], cwd=repo_root, text=True, capture_output=True, timeout=60, check=False)
