import json
import os
import subprocess
import sys
from pathlib import Path
from typing import TextIO

import pytest

from test_model_inspection_browser_verification import (
    BASE_URL,
    RUN_PROOF,
    TARGET_BRANCH,
    TARGET_SHA,
    _run,
    _stop,
    _wait_for_url,
    _write_seed_script,
)


def _write_browser_script(path: Path) -> None:
    path.write_text(
        '''import fs from "node:fs";
import { chromium } from "playwright";

const base = process.env.BASE_URL;
const results = [];
const errors = [];
let expectedInvalidGlbError = false;
const assert = (value, message) => { if (!value) throw new Error(message); };
async function check(name, fn) {
  try { await fn(); results.push({ name, status: "PASS" }); }
  catch (error) { results.push({ name, status: "FAIL", error: error?.stack ?? String(error) }); }
}
const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({ viewport: { width: 640, height: 360 } });
const page = await context.newPage();
page.on("pageerror", e => errors.push(`page:${e.message}`));
page.on("console", m => {
  if (m.type() !== "error") return;
  const text = m.text();
  if (expectedInvalidGlbError && /not-a-glb|Unexpected token/.test(text)) return;
  errors.push(`console:${text}`);
});
await page.goto(`${base}/design/model`, { waitUntil: "domcontentloaded" });
await page.getByRole("heading", { name: "Model workbench" }).waitFor();
await page.getByRole("button", { name: "Show navigator", exact: true }).click();
await page.getByRole("button", { name: "Show context", exact: true }).click();
const selectCandidate = async text => page.getByRole("button", { name: new RegExp(text) }).click();
const canvas = () => page.getByRole("img", { name: "Interactive 3D preview and geometry inspection of generated BLUECAD geometry" });
const meshSelect = () => page.getByLabel("Inspectable mesh");

await check("compact-and-effective-200-percent-containment", async () => {
  await selectCandidate("Inspection proof candidate A");
  await canvas().waitFor({ timeout: 15000 });
  await page.getByText("Orbit, pan, zoom, or click a mesh to inspect visible geometry.").waitFor({ timeout: 15000 });
  const size = await page.evaluate(() => ({ sw: document.documentElement.scrollWidth, cw: document.documentElement.clientWidth }));
  assert(size.sw <= size.cw + 1, `document overflow ${JSON.stringify(size)}`);
  const box = await page.locator(".bluecad-workbench__viewport").boundingBox();
  assert(box && box.width >= 180 && box.height >= 120, `viewport unusable ${JSON.stringify(box)}`);
});

await check("keyboard-selector-uses-current-session-inventory", async () => {
  const selector = meshSelect();
  await selector.waitFor({ timeout: 15000 });
  const options = await selector.locator("option").allTextContents();
  assert(options.includes("A-main") && options.includes("A-second"), `missing artifact meshes ${JSON.stringify(options)}`);
  assert(!options.some(x => /grid|light|helper/i.test(x)), `helper leaked into inventory ${JSON.stringify(options)}`);
  await selector.selectOption({ label: "A-second" });
  await page.getByText("A-second", { exact: true }).last().waitFor();
  await page.getByText("Material A-second", { exact: true }).waitFor();
  await page.getByText(/unitless/).waitFor();
});

await check("pointer-hit-and-no-hit-share-selection-state", async () => {
  const c = canvas();
  const box = await c.boundingBox();
  assert(box, "canvas box missing");
  let hit = false;
  for (const fy of [0.35, 0.5, 0.65]) {
    for (const fx of [0.25, 0.4, 0.55, 0.7]) {
      await c.click({ position: { x: box.width * fx, y: box.height * fy } });
      await page.waitForTimeout(80);
      if ((await meshSelect().inputValue()) !== "") { hit = true; break; }
    }
    if (hit) break;
  }
  assert(hit, "no canvas-relative pointer probe selected a current mesh");
  await c.click({ position: { x: 4, y: 4 } });
  await page.waitForTimeout(150);
  assert((await meshSelect().inputValue()) === "", "no-hit pointer click did not clear selection");
});

await check("material-drag-does-not-change-inspection", async () => {
  await meshSelect().selectOption({ label: "A-main" });
  const before = await meshSelect().inputValue();
  const box = await canvas().boundingBox();
  assert(box, "canvas box missing");
  await page.mouse.move(box.x + box.width * 0.5, box.y + box.height * 0.5);
  await page.mouse.down();
  await page.mouse.move(box.x + box.width * 0.5 + 32, box.y + box.height * 0.5 + 28, { steps: 4 });
  await page.mouse.up();
  await page.waitForTimeout(150);
  assert((await meshSelect().inputValue()) === before, "material drag changed geometry inspection");
});

await check("artifact-replacement-clears-stale-inventory-and-hit", async () => {
  await meshSelect().selectOption({ label: "A-main" });
  await selectCandidate("Inspection proof candidate B");
  await page.getByText("Orbit, pan, zoom, or click a mesh to inspect visible geometry.").waitFor({ timeout: 15000 });
  const selector = meshSelect();
  const options = await selector.locator("option").allTextContents();
  assert(options.includes("B-only"), `B inventory missing ${JSON.stringify(options)}`);
  assert(!options.includes("A-main") && !options.includes("A-second"), `stale A inventory survived ${JSON.stringify(options)}`);
  assert((await selector.inputValue()) === "", "stale hit survived artifact replacement");
});

await check("load-failure-clears-inspection-without-crashing-workbench", async () => {
  expectedInvalidGlbError = true;
  await selectCandidate("Inspection proof invalid GLB");
  await page.getByText("Unable to load this GLB artifact.").waitFor({ timeout: 15000 });
  await page.getByText("Geometry inspection is unavailable for this artifact.").waitFor();
  await page.waitForTimeout(200);
  expectedInvalidGlbError = false;
  assert(!(await meshSelect().count()), "inspectable mesh selector survived failed load");
  await page.getByRole("heading", { name: "Model workbench" }).waitFor();
});

await check("085-candidate-lifecycle-remains-functional", async () => {
  const textarea = page.getByLabel("New candidate brief");
  await textarea.fill("Inspection proof lifecycle candidate");
  await page.getByRole("button", { name: "New candidate", exact: true }).click();
  await page.getByText("Candidate created.").waitFor({ timeout: 15000 });
  await page.getByText("Inspection proof lifecycle candidate", { exact: false }).first().waitFor();
  await page.getByRole("button", { name: "Archive", exact: true }).click();
  await page.getByText("Candidate archived.").waitFor({ timeout: 15000 });
});

await check("no-uncaught-browser-errors", async () => assert(errors.length === 0, errors.join("\\n")));
await context.close();
await browser.close();
const report = {
  schema: "jarvisos.model-inspection-browser-proof.v2",
  target_sha: process.env.TARGET_SHA,
  results,
  errors,
  summary: { passed: results.filter(x => x.status === "PASS").length, failed: results.filter(x => x.status === "FAIL").length }
};
fs.writeFileSync(process.env.PROOF_REPORT, JSON.stringify(report, null, 2) + "\\n");
console.log("MODEL_INSPECTION_BROWSER_PROOF=" + JSON.stringify(report));
if (report.summary.failed) process.exit(1);
''',
        encoding="utf-8",
    )


@pytest.mark.skipif(not RUN_PROOF, reason="temporary exact-head 086 browser proof runs only in its dedicated workflow")
def test_exact_head_model_inspection_browser_proof_v2(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    repo_root = Path(__file__).resolve().parents[2]
    target = tmp_path / "target"
    data_root = tmp_path / "data"
    report_path = tmp_path / "model-inspection-proof.json"
    seed_script = tmp_path / "seed.py"
    log_path = tmp_path / "fastapi.log"
    server: subprocess.Popen[str] | None = None
    log: TextIO | None = None
    browser_script: Path | None = None
    env = os.environ.copy()
    env.update({
        "JARVISOS_DATA_ROOT": str(data_root), "JARVISOS_AI_PROVIDER": "none",
        "JARVISOS_ENV": "browser-verification", "BASE_URL": BASE_URL,
        "TARGET_SHA": TARGET_SHA, "PROOF_REPORT": str(report_path),
    })
    try:
        _run(["git", "fetch", "origin", TARGET_BRANCH, "--depth=200"], cwd=repo_root, env=env, timeout=120)
        assert _run(["git", "rev-parse", "FETCH_HEAD"], cwd=repo_root, env=env, timeout=30).stdout.strip() == TARGET_SHA
        _run(["git", "worktree", "add", "--detach", str(target), TARGET_SHA], cwd=repo_root, env=env, timeout=60)
        for checker in (
            [sys.executable, "scripts/check_spec_status.py", "--self-test"],
            [sys.executable, "scripts/check_ui_foundation.py"],
            [sys.executable, "scripts/check_app_shell.py"],
            [sys.executable, "scripts/check_bluecad_read_model.py"],
            [sys.executable, "scripts/check_bluecad_workbench.py"],
            [sys.executable, "scripts/check_model_inspection.py"],
        ):
            _run(checker, cwd=target, env=env, timeout=120)
        frontend, backend = target / "frontend", target / "backend"
        browser_script = frontend / ".model-inspection-proof.mjs"
        env["PYTHONPATH"] = str(backend)
        _run(["npm", "ci"], cwd=frontend, env=env, timeout=300)
        _run(["npm", "run", "build"], cwd=frontend, env=env, timeout=180)
        _run(["npm", "install", "--no-save", "--package-lock=false", "playwright@1.54.2"], cwd=frontend, env=env, timeout=300)
        _run([str(frontend / "node_modules/.bin/playwright"), "install", "--with-deps", "chromium"], cwd=frontend, env=env, timeout=360)
        data_root.mkdir(parents=True, exist_ok=True)
        _run([sys.executable, "-m", "app.core.bootstrap"], cwd=backend, env=env, timeout=120)
        _write_seed_script(seed_script)
        _run([sys.executable, str(seed_script)], cwd=backend, env=env, timeout=60)
        log = log_path.open("w", encoding="utf-8")
        server = subprocess.Popen([sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"], cwd=backend, env=env, text=True, stdout=log, stderr=subprocess.STDOUT)
        _wait_for_url(f"{BASE_URL}/health")
        _write_browser_script(browser_script)
        completed = _run(["node", str(browser_script)], cwd=frontend, env=env, timeout=420)
        report = json.loads(report_path.read_text(encoding="utf-8"))
        assert report["target_sha"] == TARGET_SHA
        assert report["summary"]["failed"] == 0, json.dumps(report, indent=2)
        _run(["git", "fetch", "origin", TARGET_BRANCH, "--depth=1"], cwd=repo_root, env=env, timeout=120)
        assert _run(["git", "rev-parse", "FETCH_HEAD"], cwd=repo_root, env=env, timeout=30).stdout.strip() == TARGET_SHA
        with capsys.disabled():
            print("MODEL_INSPECTION_BROWSER_PROOF_JSON=" + json.dumps(report, separators=(",", ":"), sort_keys=True), flush=True)
    finally:
        _stop(server)
        if log is not None: log.close()
        if browser_script is not None: browser_script.unlink(missing_ok=True)
        if target.exists(): subprocess.run(["git", "worktree", "remove", "--force", str(target)], cwd=repo_root, text=True, capture_output=True, timeout=60, check=False)
