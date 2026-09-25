import fs from "node:fs/promises";
import path from "node:path";
import os from "node:os";
import { createHash } from "node:crypto";
import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";
import { chromium } from "/home/thera/jarvis-control/work/tools/pw/node_modules/playwright/index.mjs";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../../..");
const outputDir = path.dirname(fileURLToPath(import.meta.url));
const backendPython = path.join(root, "backend/.venv/bin/python");
const dwsimPath = "/home/thera/jarvis-control/work/tools/dwsim-10.2.9/mcp-root/opt/dwsim-mcp/dwsim-mcp";
const mambaRoot = "/home/thera/jarvis-control/work/tools/mamba";
const dwsimSha = createHash("sha256").update(await fs.readFile(dwsimPath)).digest("hex");
const dataRoot = await fs.mkdtemp(path.join(os.tmpdir(), "jarvisos-149-ui-"));
const sourceSha = (await import("node:child_process")).execFileSync("git", ["rev-parse", "HEAD"], { cwd: root, encoding: "utf8" }).trim();
const timing = {};
const responses = {};
const children = [];
let browser;

function start(command, args, options) {
  const child = spawn(command, args, { ...options, stdio: ["ignore", "pipe", "pipe"] });
  const logs = { stdout: "", stderr: "" };
  child.stdout.on("data", (chunk) => { logs.stdout = (logs.stdout + chunk.toString()).slice(-12000); });
  child.stderr.on("data", (chunk) => { logs.stderr = (logs.stderr + chunk.toString()).slice(-12000); });
  children.push({ child, logs });
  return { child, logs };
}
async function waitFor(url, logs, timeoutMs = 90000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    try { const response = await fetch(url); if (response.ok) return; } catch { /* startup still in progress */ }
    await new Promise((resolve) => setTimeout(resolve, 350));
    if (children.some(({ child }) => child.exitCode !== null)) throw new Error(`Service exited during startup: ${logs.stderr}`);
  }
  throw new Error(`Timed out waiting for ${url}: ${logs.stderr}`);
}
async function stop() {
  await browser?.close().catch(() => {});
  for (const { child } of children.reverse()) if (child.exitCode === null) child.kill("SIGTERM");
  await Promise.all(children.map(({ child }) => new Promise((resolve) => {
    if (child.exitCode !== null) resolve();
    else { const timer = setTimeout(() => { child.kill("SIGKILL"); resolve(); }, 5000); child.once("exit", () => { clearTimeout(timer); resolve(); }); }
  })));
}
function quantities(fixture) {
  const rows = [];
  for (const [name, [value, unit]] of Object.entries(fixture.coefficients)) rows.push({ name, value: { value, unit, basis_ref: fixture.basis_ref } });
  for (const [name, [rawValue, unit]] of Object.entries(fixture.design)) {
    if (name === "peak_par") continue;
    rows.push({ name, value: { value: name === "duration" ? 1 : rawValue, unit } });
  }
  return rows;
}

const evidence = {
  evidence_kind: "real_local_chromium_operator_execution",
  status: "running",
  source_sha: sourceSha,
  urls: { frontend: "http://127.0.0.1:4173/design/studies", backend: "http://127.0.0.1:8000" },
  runtime: { data_root: dataRoot, mamba_root_prefix: mambaRoot, dwsim_mcp_path: dwsimPath, dwsim_mcp_sha256: dwsimSha },
  fixture: { path: "scripts/qualification/107/synthetic-parameters.json", qualification: "synthetic/unqualified" },
  timings_ms: timing,
  responses
};
try {
  const env = {
    ...process.env,
    JARVISOS_DATA_ROOT: dataRoot,
    JARVISOS_CORS_ORIGINS: "http://127.0.0.1:4173,http://localhost:4173",
    MAMBA_ROOT_PREFIX: mambaRoot,
    JARVISOS_DWSIM_MCP_PATH: dwsimPath,
    JARVISOS_DWSIM_MCP_SHA256: dwsimSha,
    PYTHONPATH: path.join(root, "backend")
  };
  const backend = start(backendPython, ["-c", "from app.core.bootstrap import initialize_storage; initialize_storage(); import uvicorn; uvicorn.run('app.main:app', host='127.0.0.1', port=8000, log_level='warning')"], { cwd: path.join(root, "backend"), env });
  await waitFor("http://127.0.0.1:8000/workspaces", backend.logs);
  const frontend = start(process.execPath, [path.join(root, "frontend/node_modules/vite/bin/vite.js"), "preview", "--host", "127.0.0.1", "--port", "4173", "--strictPort"], { cwd: path.join(root, "frontend"), env });
  await waitFor("http://127.0.0.1:4173/design/studies", frontend.logs);
  browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1120, height: 820 }, deviceScaleFactor: 1 });
  page.on("response", async (response) => {
    const url = response.url();
    try {
      if (url.endsWith("/engineering/evaluators")) responses.evaluators = await response.json();
      if (url.endsWith("/engineering/capabilities")) responses.capabilities = await response.json();
      if (url.endsWith("/engineering/studies") && response.request().method() === "POST") responses.study = await response.json();
      if (url.includes("/envelope?") && response.request().method() === "POST") responses.envelope = await response.json();
      if (url.endsWith("/escalations") && response.request().method() === "POST") responses.escalation = await response.json();
    } catch { /* preserve original page error handling; only successful JSON responses are evidence */ }
  });
  const t0 = Date.now();
  await page.goto("http://127.0.0.1:4173/design/studies", { waitUntil: "domcontentloaded" });
  await page.getByTestId("engineering-studies-surface").waitFor({ timeout: 60000 });
  await page.getByRole("heading", { name: "Evaluator availability" }).waitFor();
  timing.open_surface_ms = Date.now() - t0;
  const evaluator = page.getByLabel("Evaluator");
  await evaluator.selectOption("bluerev.pbr_day_night");
  const fixture = JSON.parse(await fs.readFile(path.join(root, "scripts/qualification/107/synthetic-parameters.json"), "utf8"));
  await page.getByLabel("Study id").fill("pbr-synthetic-operator");
  await page.getByLabel("Subject id").fill("pbr-loop-a");
  await page.getByLabel("Fixed inputs (JSON array of named quantities)").fill(JSON.stringify(quantities(fixture), null, 2));
  const runStarted = Date.now();
  await page.getByRole("button", { name: "Run study" }).click();
  await page.getByText("UNQUALIFIED", { exact: true }).waitFor({ timeout: 90000 });
  timing.study_ms = Date.now() - runStarted;
  await page.getByRole("button", { name: "Create envelope for best feasible point" }).click();
  await page.getByText("Process design envelope", { exact: false }).waitFor({ timeout: 30000 });
  const escalationStarted = Date.now();
  await page.getByRole("button", { name: "Request escalation for best point" }).click();
  await page.getByRole("heading", { name: "Escalation results" }).waitFor({ timeout: 30000 });
  timing.envelope_and_escalation_ms = Date.now() - escalationStarted;
  await page.locator(".engineering-studies__inspection").scrollIntoViewIfNeeded();
  await page.screenshot({ path: path.join(outputDir, "engineering-ui-operator.png"), type: "png" });
  const screenshot = await fs.stat(path.join(outputDir, "engineering-ui-operator.png"));
  if (screenshot.size > 300_000) throw new Error(`Operator screenshot exceeds 300 KB (${screenshot.size})`);
  evidence.status = "passed";
  evidence.workspace_id = "bluerev";
  evidence.screenshot = { path: "scripts/qualification/149/engineering-ui-operator.png", bytes: screenshot.size };
  evidence.fixture.sha256 = createHash("sha256").update(await fs.readFile(path.join(root, evidence.fixture.path))).digest("hex");
  evidence.study = { digest: responses.study.content_digest, qualification_status: responses.study.qualification_status, status: responses.study.status, points: responses.study.points.length, feasible_count: responses.study.feasible_count, best_point_index: responses.study.best_point_index };
  evidence.envelope = { digest: responses.envelope.envelope_digest, point_index: responses.envelope.selected_point_index, qualification_status: responses.envelope.qualification_status };
  evidence.escalation = { digest: responses.escalation.content_digest, point_statuses: responses.escalation.points.map((point) => point.status), reasons: responses.escalation.points.map((point) => point.status_reason) };
  evidence.interpretation = "Real local backend and Chromium UI execution using the committed synthetic 107 parameters. Results are software/runtime evidence only; the PBR run remains unqualified.";
} catch (error) {
  evidence.status = "failed";
  evidence.error = error instanceof Error ? error.message : String(error);
  evidence.service_logs = children.map(({ logs }) => ({ stdout: logs.stdout, stderr: logs.stderr }));
  throw error;
} finally {
  await fs.writeFile(path.join(outputDir, "engineering-ui-operator.runtime-evidence.json"), `${JSON.stringify(evidence, null, 2)}\n`);
  await stop();
}
console.log(JSON.stringify({ status: evidence.status, study: evidence.study, envelope: evidence.envelope, escalation: evidence.escalation, evidence: path.join(outputDir, "engineering-ui-operator.runtime-evidence.json") }, null, 2));
