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

TARGET_SHA = "999604b6236e5e704c0544c5cb0341a9c0c40bc9"
TARGET_BRANCH = "spec/085-bluecad-workbench-2"
BASE_URL = "http://127.0.0.1:8000"


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
        '''import json\nimport struct\nfrom pathlib import Path\nfrom app.core.database import open_sqlite_connection\nfrom app.modules.bluecad.ledger import create_candidate_record, mark_candidate_valid, register_artifact, update_candidate_artifacts\nfrom app.modules.bluecad.models import BluecadLoopConfig\n\nwith open_sqlite_connection() as connection:\n    row = connection.execute("SELECT id FROM workspaces ORDER BY created_at LIMIT 1").fetchone()\n    if row is None:\n        raise SystemExit("default workspace missing")\n    workspace_id = str(row["id"])\n    connection.execute("UPDATE workspaces SET name = ? WHERE id = ?", ("BLUECAD-" + "LONGWORKSPACENAME" * 12, workspace_id))\n    connection.commit()\n\ncandidate = create_candidate_record(workspace_id, "Browser proof valid candidate", BluecadLoopConfig())\ngltf = {\n    "asset": {"version": "2.0"},\n    "scene": 0,\n    "scenes": [{"nodes": [0]}],\n    "nodes": [{"mesh": 0}],\n    "meshes": [{"primitives": [{"attributes": {"POSITION": 0}}]}],\n    "buffers": [{"byteLength": 36}],\n    "bufferViews": [{"buffer": 0, "byteOffset": 0, "byteLength": 36, "target": 34962}],\n    "accessors": [{"bufferView": 0, "componentType": 5126, "count": 3, "type": "VEC3", "min": [0, 0, 0], "max": [1, 1, 0]}],\n}\njson_bytes = json.dumps(gltf, separators=(",", ":")).encode()\njson_bytes += b" " * ((4 - len(json_bytes) % 4) % 4)\nbin_bytes = struct.pack("<9f", 0,0,0, 1,0,0, 0,1,0)\ntotal = 12 + 8 + len(json_bytes) + 8 + len(bin_bytes)\nglb = struct.pack("<III", 0x46546C67, 2, total)\nglb += struct.pack("<II", len(json_bytes), 0x4E4F534A) + json_bytes\nglb += struct.pack("<II", len(bin_bytes), 0x004E4942) + bin_bytes\nsource = Path("/tmp/bluecad-proof.glb")\nsource.write_bytes(glb)\nglb_id = register_artifact(workspace_id, source, role="bluecad_glb", source_ref=f"bluecad_candidate:{candidate.id}", producer_notes="Temporary exact-head browser proof fixture.")\nupdate_candidate_artifacts(candidate.id, spec_artifact_id=None, glb_artifact_id=glb_id, report_artifact_id=None)\nmark_candidate_valid(candidate.id)\nPath("/tmp/bluecad-proof-seed.json").write_text(json.dumps({"workspace_id": workspace_id, "candidate_id": candidate.id, "glb_artifact_id": glb_id}))\n''',
        encoding="utf-8",
    )


def _write_browser_script(path: Path) -> None:
    path.write_text(
        '''import fs from "node:fs";\nimport { chromium } from "playwright";\n\nconst base = process.env.BASE_URL;\nconst results = [];\nconst errors = [];\nconst assert = (value, message) => { if (!value) throw new Error(message); };\nasync function check(name, fn) {\n  try { await fn(); results.push({ name, status: "PASS" }); }\n  catch (error) { results.push({ name, status: "FAIL", error: error?.stack ?? String(error) }); }\n}\nconst browser = await chromium.launch({ headless: true });\nconst context = await browser.newContext({ viewport: { width: 640, height: 360 } });\nconst page = await context.newPage();\npage.on("pageerror", e => errors.push(`page:${e.message}`));\npage.on("console", m => { if (m.type() === "error") errors.push(`console:${m.text()}`); });\nawait page.goto(`${base}/design/model`, { waitUntil: "domcontentloaded" });\nawait page.locator("#app-main").waitFor({ state: "visible" });\nawait page.getByRole("heading", { name: "Model workbench" }).waitFor();\n\nawait check("effective-200-percent-no-global-overflow", async () => {\n  await page.getByRole("button", { name: "Show navigator", exact: true }).click();\n  await page.locator("#shell-navigator").waitFor();\n  const size = await page.evaluate(() => ({ sw: document.documentElement.scrollWidth, cw: document.documentElement.clientWidth }));\n  assert(size.sw <= size.cw + 1, `document overflow ${JSON.stringify(size)}`);\n  const select = page.getByLabel("Workspace");\n  const contained = await select.evaluate(el => {\n    const a = el.getBoundingClientRect(); const p = el.parentElement?.getBoundingClientRect();\n    return !!p && a.left >= p.left - 1 && a.right <= p.right + 1;\n  });\n  assert(contained, "long workspace selector exceeds navigator label");\n});\n\nawait check("real-glb-loads-and-resizes-with-shell", async () => {\n  await page.getByRole("button", { name: /Browser proof valid candidate/ }).click();\n  const canvas = page.getByRole("img", { name: "Interactive 3D preview of generated BLUECAD geometry" });\n  await canvas.waitFor({ timeout: 15000 });\n  await page.getByText("Orbit, pan, and zoom to inspect the generated geometry.").waitFor({ timeout: 15000 });\n  const before = await canvas.boundingBox();\n  await page.getByRole("button", { name: "Show context", exact: true }).click();\n  await page.waitForTimeout(250);\n  const after = await canvas.boundingBox();\n  assert(before && after && after.width !== before.width, `viewer did not resize ${JSON.stringify({before, after})}`);\n  const doc = await page.evaluate(() => ({ sw: document.documentElement.scrollWidth, cw: document.documentElement.clientWidth }));\n  assert(doc.sw <= doc.cw + 1, `panel-open overflow ${JSON.stringify(doc)}`);\n});\n\nawait check("duplicate-brief-opens-navigator-and-focuses-textarea", async () => {\n  if (await page.locator("#shell-navigator").count()) {\n    await page.locator("#shell-navigator").press("Escape");\n    await page.locator("#shell-navigator").waitFor({ state: "detached" });\n  }\n  await page.getByRole("button", { name: "Duplicate brief", exact: true }).click();\n  const textarea = page.getByLabel("New candidate brief");\n  await textarea.waitFor();\n  await page.waitForFunction(() => document.activeElement?.tagName === "TEXTAREA");\n  assert((await textarea.inputValue()) === "Browser proof valid candidate", "duplicate brief did not preserve source text");\n});\n\nawait check("create-refresh-archive-use-real-api", async () => {\n  const textarea = page.getByLabel("New candidate brief");\n  await textarea.fill("Browser proof created candidate");\n  await page.getByRole("button", { name: "New candidate", exact: true }).click();\n  await page.getByText("Candidate created.").waitFor({ timeout: 15000 });\n  await page.getByText("Browser proof created candidate", { exact: false }).first().waitFor();\n  await page.getByRole("button", { name: "Refresh", exact: true }).click();\n  const archive = page.getByRole("button", { name: "Archive", exact: true });\n  await archive.waitFor();\n  await archive.click();\n  await page.getByText("Candidate archived.").waitFor({ timeout: 15000 });\n  assert(!(await page.getByRole("button", { name: /Browser proof created candidate/ }).count()), "archived candidate remained visible with Show archived off");\n});\n\nawait check("promote-refresh-restores-keyboard-focus", async () => {\n  const valid = page.getByRole("button", { name: /Browser proof valid candidate/ });\n  await valid.click();\n  const promote = page.getByRole("button", { name: "Promote to Decision", exact: true });\n  await promote.waitFor();\n  await promote.focus();\n  await promote.press("Enter");\n  await page.getByText(/Promoted to Decision/).waitFor({ timeout: 15000 });\n  await page.waitForTimeout(150);\n  const focus = await page.evaluate(() => ({ text: document.activeElement?.textContent ?? "", id: document.activeElement?.id ?? "" }));\n  assert(focus.text.includes("Browser proof valid candidate") || focus.id === "bluecad-workbench-title", `unexpected focus ${JSON.stringify(focus)}`);\n});\n\nawait check("no-uncaught-browser-errors", async () => assert(errors.length === 0, errors.join("\\n")));\nawait context.close();\nawait browser.close();\nconst report = { schema: "jarvisos.bluecad-workbench-browser-proof.v1", target_sha: process.env.TARGET_SHA, results, errors, summary: { passed: results.filter(x => x.status === "PASS").length, failed: results.filter(x => x.status === "FAIL").length } };\nfs.writeFileSync(process.env.PROOF_REPORT, JSON.stringify(report, null, 2) + "\\n");\nconsole.log("BLUECAD_WORKBENCH_BROWSER_PROOF=" + JSON.stringify(report));\nif (report.summary.failed) process.exit(1);\n''',
        encoding="utf-8",
    )


@pytest.mark.skipif(os.getenv("GITHUB_ACTIONS") != "true", reason="temporary exact-head BLUECAD browser proof runs only in GitHub Actions")
def test_exact_head_bluecad_workbench_browser_proof(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    repo_root = Path(__file__).resolve().parents[2]
    target = tmp_path / "target"
    data_root = tmp_path / "data"
    report_path = tmp_path / "bluecad-workbench-proof.json"
    browser_script = tmp_path / "proof.mjs"
    seed_script = tmp_path / "seed.py"
    log_path = tmp_path / "fastapi.log"
    server: subprocess.Popen[str] | None = None
    log: TextIO | None = None
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
        _run(["git", "fetch", "origin", TARGET_BRANCH, "--depth=1"], cwd=repo_root, env=env, timeout=120)
        _run(["git", "worktree", "add", "--detach", str(target), "FETCH_HEAD"], cwd=repo_root, env=env, timeout=60)
        actual = _run(["git", "rev-parse", "HEAD"], cwd=target, env=env, timeout=30).stdout.strip()
        assert actual == TARGET_SHA

        for checker in ("scripts/check_app_shell.py", "scripts/check_bluecad_read_model.py", "scripts/check_bluecad_workbench.py"):
            _run([sys.executable, checker], cwd=target, env=env, timeout=120)

        frontend = target / "frontend"
        backend = target / "backend"
        _run(["npm", "ci"], cwd=frontend, env=env, timeout=300)
        _run(["npm", "run", "build"], cwd=frontend, env=env, timeout=180)
        _run(["npm", "install", "--no-save", "--package-lock=false", "tsx@4.20.3", "playwright@1.54.2"], cwd=frontend, env=env, timeout=300)
        _run([str(frontend / "node_modules" / ".bin" / "tsx"), "src/components/bluecad/workbenchStateHarness.ts"], cwd=frontend, env=env, timeout=60)
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

        status = _run(["git", "status", "--short"], cwd=target, env=env, timeout=30).stdout.strip()
        assert status == "", status
        with capsys.disabled():
            print("BLUECAD_WORKBENCH_BROWSER_PROOF_JSON=" + json.dumps(report, separators=(",", ":"), sort_keys=True), flush=True)
    finally:
        _stop(server)
        if log is not None:
            log.close()
        if target.exists():
            subprocess.run(["git", "worktree", "remove", "--force", str(target)], cwd=repo_root, text=True, capture_output=True, timeout=60, check=False)
