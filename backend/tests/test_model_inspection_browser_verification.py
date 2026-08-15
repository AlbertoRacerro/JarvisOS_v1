import json
import os
import struct
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import TextIO

import pytest

TARGET_SHA = os.getenv("TARGET_IMPLEMENTATION_SHA", "dca39f2c905df14303eee1ef09ec91188d7497b4")
TARGET_BRANCH = "spec/086-model-inspection-a0"
BASE_URL = "http://127.0.0.1:8000"
RUN_PROOF = os.getenv("RUN_MODEL_INSPECTION_BROWSER_PROOF") == "true"


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


def _glb(mesh_names: tuple[str, ...]) -> bytes:
    positions: list[float] = []
    accessors = []
    buffer_views = []
    meshes = []
    nodes = []
    byte_offset = 0
    for index, name in enumerate(mesh_names):
        x = float(index) * 1.5
        verts = [x, 0.0, 0.0, x + 1.0, 0.0, 0.0, x, 1.0, 0.0]
        positions.extend(verts)
        buffer_views.append({"buffer": 0, "byteOffset": byte_offset, "byteLength": 36, "target": 34962})
        accessors.append({
            "bufferView": index,
            "componentType": 5126,
            "count": 3,
            "type": "VEC3",
            "min": [x, 0.0, 0.0],
            "max": [x + 1.0, 1.0, 0.0],
        })
        meshes.append({"name": name, "primitives": [{"attributes": {"POSITION": index}, "material": index}]})
        nodes.append({"mesh": index, "name": name})
        byte_offset += 36
    gltf = {
        "asset": {"version": "2.0"},
        "scene": 0,
        "scenes": [{"nodes": list(range(len(nodes)))}],
        "nodes": nodes,
        "meshes": meshes,
        "materials": [{"name": f"Material {name}"} for name in mesh_names],
        "buffers": [{"byteLength": byte_offset}],
        "bufferViews": buffer_views,
        "accessors": accessors,
    }
    json_bytes = json.dumps(gltf, separators=(",", ":")).encode()
    json_bytes += b" " * ((4 - len(json_bytes) % 4) % 4)
    bin_bytes = struct.pack(f"<{len(positions)}f", *positions)
    total = 12 + 8 + len(json_bytes) + 8 + len(bin_bytes)
    body = struct.pack("<III", 0x46546C67, 2, total)
    body += struct.pack("<II", len(json_bytes), 0x4E4F534A) + json_bytes
    body += struct.pack("<II", len(bin_bytes), 0x004E4942) + bin_bytes
    return body


def _write_seed_script(path: Path) -> None:
    a = repr(_glb(("A-main", "A-second")))
    b = repr(_glb(("B-only",)))
    path.write_text(
        f'''from pathlib import Path
from app.core.database import open_sqlite_connection
from app.modules.bluecad.ledger import create_candidate_record, mark_candidate_valid, register_artifact, update_candidate_artifacts
from app.modules.bluecad.models import BluecadLoopConfig

with open_sqlite_connection() as connection:
    row = connection.execute("SELECT id FROM workspaces ORDER BY created_at LIMIT 1").fetchone()
    if row is None:
        raise SystemExit("default workspace missing")
    workspace_id = str(row["id"])


def add_valid(brief, data, filename):
    source = Path("/tmp") / filename
    source.write_bytes(data)
    candidate = create_candidate_record(workspace_id, brief, BluecadLoopConfig())
    glb_id = register_artifact(workspace_id, source, role="bluecad_glb", source_ref=f"bluecad_candidate:{{candidate.id}}", producer_notes="Temporary 086 browser proof fixture.")
    update_candidate_artifacts(candidate.id, spec_artifact_id=None, glb_artifact_id=glb_id, report_artifact_id=None)
    mark_candidate_valid(candidate.id)
    return candidate

candidate_a = add_valid("Inspection proof candidate A", {a}, "inspection-a.glb")
candidate_b = add_valid("Inspection proof candidate B", {b}, "inspection-b.glb")
invalid = add_valid("Inspection proof invalid GLB", b"not-a-glb", "inspection-invalid.glb")
Path("/tmp/model-inspection-seed.json").write_text(__import__("json").dumps({{"workspace_id": workspace_id, "a": candidate_a.id, "b": candidate_b.id, "invalid": invalid.id}}))
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
const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({ viewport: { width: 640, height: 360 } });
const page = await context.newPage();
page.on("pageerror", e => errors.push(`page:${e.message}`));
page.on("console", m => { if (m.type() === "error" && !m.text().includes("Unable to load this GLB artifact")) errors.push(`console:${m.text()}`); });
await page.goto(`${base}/design/model`, { waitUntil: "domcontentloaded" });
await page.getByRole("heading", { name: "Model workbench" }).waitFor();
await page.getByRole("button", { name: "Show navigator", exact: true }).click();
await page.getByRole("button", { name: "Show context", exact: true }).click();
const selectCandidate = async text => {
  await page.getByRole("button", { name: new RegExp(text) }).click();
};
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
  await page.getByText("1", { exact: true }).last().waitFor();
  await page.getByText(/unitless/).waitFor();
});

await check("pointer-hit-and-no-hit-share-selection-state", async () => {
  const c = canvas();
  const box = await c.boundingBox();
  assert(box, "canvas box missing");
  await c.click({ position: { x: box.width / 2, y: box.height / 2 } });
  await page.waitForTimeout(250);
  assert((await meshSelect().inputValue()) !== "", "center pointer hit did not select a current mesh");
  await c.click({ position: { x: 4, y: 4 } });
  await page.waitForTimeout(250);
  assert((await meshSelect().inputValue()) === "", "no-hit pointer click did not clear selection");
});

await check("material-drag-does-not-change-inspection", async () => {
  await meshSelect().selectOption({ label: "A-main" });
  const before = await meshSelect().inputValue();
  const c = canvas();
  const box = await c.boundingBox();
  assert(box, "canvas box missing");
  await c.dispatchEvent("pointerdown", { button: 0, pointerId: 77, clientX: box.x + box.width / 2, clientY: box.y + box.height / 2 });
  await c.dispatchEvent("pointerup", { button: 0, pointerId: 77, clientX: box.x + box.width / 2 + 30, clientY: box.y + box.height / 2 + 30 });
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
  await selectCandidate("Inspection proof invalid GLB");
  await page.getByText("Unable to load this GLB artifact.").waitFor({ timeout: 15000 });
  await page.getByText("Geometry inspection is unavailable for this artifact.").waitFor();
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
  schema: "jarvisos.model-inspection-browser-proof.v1",
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
def test_exact_head_model_inspection_browser_proof(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
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

        for checker in (
            [sys.executable, "scripts/check_spec_status.py", "--self-test"],
            [sys.executable, "scripts/check_ui_foundation.py"],
            [sys.executable, "scripts/check_app_shell.py"],
            [sys.executable, "scripts/check_bluecad_read_model.py"],
            [sys.executable, "scripts/check_bluecad_workbench.py"],
            [sys.executable, "scripts/check_model_inspection.py"],
        ):
            _run(checker, cwd=target, env=env, timeout=120)

        frontend = target / "frontend"
        backend = target / "backend"
        browser_script = frontend / ".model-inspection-proof.mjs"
        env["PYTHONPATH"] = str(backend)
        _run(["npm", "ci"], cwd=frontend, env=env, timeout=300)
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
        with capsys.disabled():
            print("MODEL_INSPECTION_BROWSER_PROOF_JSON=" + json.dumps(report, separators=(",", ":"), sort_keys=True), flush=True)
    finally:
        _stop(server)
        if log is not None:
            log.close()
        if browser_script is not None:
            browser_script.unlink(missing_ok=True)
        if target.exists():
            subprocess.run(["git", "worktree", "remove", "--force", str(target)], cwd=repo_root, text=True, capture_output=True, timeout=60, check=False)
