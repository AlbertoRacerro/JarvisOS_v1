#!/usr/bin/env node
// Real Chromium proof for the existing Jarvis Sidecar, following the isolated
// backend/frontend lifecycle used by qualification 149.
import { mkdtemp, rm, stat, writeFile } from "node:fs/promises";
import { openSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import { spawn, spawnSync, execFileSync } from "node:child_process";
import { setTimeout as delay } from "node:timers/promises";
import { chromium } from "/home/thera/jarvis-control/work/tools/pw/node_modules/playwright/index.mjs";

const root = resolve(new URL("../../../", import.meta.url).pathname);
const backend = join(root, "backend");
const output = new URL(".", import.meta.url).pathname;
const backendPort = Number(process.env.JARVISOS_PROOF_BACKEND_PORT ?? 8041);
const backendUrl = `http://127.0.0.1:${backendPort}`;
const args = process.argv.slice(2);
const arg = (name, fallback) => {
  const index = args.indexOf(name);
  return index >= 0 ? args[index + 1] : process.env[name.slice(2).replaceAll("-", "_").toUpperCase()] ?? fallback;
};
const endpoint = arg("--endpoint", "http://127.0.0.1:11435/api/generate");
const model = arg("--model", process.env.JARVISOS_DEV_MESSAGE_ROUTE_MODEL ?? "gemma4:12b-it-qat");
const timeoutSeconds = arg("--timeout", "180");
const routeClass = arg("--route", "local:general");
const runtimeKind = arg("--runtime-kind", "Windows Ollama via temporary dev bridge");
const dataRoot = await mkdtemp(join(tmpdir(), "jarvisos-151p-data-"));
const tempDir = await mkdtemp(join(tmpdir(), "jarvisos-151p-proof-"));
const baseEnv = {
  ...process.env,
  JARVISOS_DATA_ROOT: dataRoot,
};
const screenshots = [];
const consoleErrors = [];
const pageErrors = [];
const flows = [];
const timings = [];
let server;
let browser;
let context;
let page;
let workspaceId;
let succeeded = false;
const proofStartedAt = Date.now();

const assert = (condition, message) => { if (!condition) throw new Error(message); };
const waitForHttp = async (url, timeout = 60_000) => {
  const deadline = Date.now() + timeout;
  while (Date.now() < deadline) {
    try { if ((await fetch(url)).ok) return; } catch { /* starting */ }
    await delay(250);
  }
  throw new Error(`service did not become ready: ${url}`);
};
const stopBackend = async () => {
  if (!server) return;
  server.kill("SIGTERM");
  if (server.exitCode === null) await new Promise((done) => server.once("exit", done));
  server = undefined;
};
const startBackend = async (devEndpoint) => {
  await stopBackend();
  const env = {
    ...baseEnv,
    JARVISOS_DEV_MESSAGE_ROUTE_ENDPOINT: devEndpoint,
    JARVISOS_DEV_MESSAGE_ROUTE_MODEL: model,
    JARVISOS_DEV_MESSAGE_ROUTE_TIMEOUT_S: timeoutSeconds,
  };
  const log = join(tempDir, `backend-${devEndpoint.includes("11436") ? "unreachable" : "reachable"}.log`);
  server = spawn(join(backend, ".venv/bin/python"), ["-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", String(backendPort)], {
    cwd: backend, env, stdio: ["ignore", openSync(log, "w"), openSync(log, "a")],
  });
  await waitForHttp(`${backendUrl}/health`);
};
const snap = async (name) => {
  const path = join(output, `sidecar-${name}.jpg`);
  await page.screenshot({ path, type: "jpeg", quality: 65, fullPage: false, animations: "disabled" });
  const sizeBytes = (await stat(path)).size;
  assert(sizeBytes <= 150 * 1024, `${name} screenshot is ${sizeBytes} bytes, over 150 KiB`);
  screenshots.push({ path: path.slice(root.length + 1), size_bytes: sizeBytes });
};
const openSidecar = async () => {
  const toggle = page.getByRole("button", { name: "Show context" });
  if (await toggle.count()) {
    await toggle.waitFor({ state: "visible", timeout: 20_000 });
    await toggle.click();
  }
  try {
    await page.getByTestId("jarvis-sidecar").waitFor({ state: "visible", timeout: 20_000 });
  } catch {
    const detail = await page.evaluate(() => ({
      title: document.title,
      body: document.body.innerText.slice(0, 2000),
      appErrors: [...document.querySelectorAll('[role="status"]')].map((item) => item.textContent),
      sidecar: document.querySelector("#shell-sidecar")?.outerHTML.slice(0, 1000),
    }));
    throw new Error(`Sidecar did not render: ${JSON.stringify(detail)}`);
  }
  const settings = page.locator(".jarvis-conversation-settings");
  if (!(await settings.evaluate((node) => node.open))) await settings.locator("summary").click();
  try {
    await page.getByLabel("Jarvis responder").waitFor({ timeout: 20_000 });
  } catch {
    const detail = await page.evaluate(() => ({
      viewport: [innerWidth, innerHeight],
      sidecar: document.querySelector(".jarvis-sidecar")?.parentElement?.outerHTML.slice(0, 2000),
      workspace: document.querySelector(".workspace-bootstrap")?.textContent,
      errors: [...document.querySelectorAll('[role="status"]')].map((item) => item.textContent),
    }));
    throw new Error(`Sidecar responder selector remained hidden: ${JSON.stringify(detail)}`);
  }
};
const optionRecords = async () => page.getByLabel("Jarvis responder").locator("option").evaluateAll((options) => options.map((option) => ({
  text: option.textContent?.trim() ?? "", value: option.value, disabled: option.disabled,
})).filter((item) => item.value));
const persistedRuntimeMetrics = (prompt) => {
  const query = `import json,sqlite3,sys
db,prompt=sys.argv[1:]
c=sqlite3.connect(db); c.row_factory=sqlite3.Row
row=c.execute("""SELECT f.state,f.terminal_reason,f.usage_totals_json,j.normalized_finish_reason,j.input_tokens,j.output_tokens,j.normalized_usage_source
FROM ai_thread_interactions i JOIN ai_flows f ON f.id=i.flow_id
LEFT JOIN ai_jobs j ON j.id=f.terminal_attempt_id
WHERE i.user_text=? ORDER BY i.created_at DESC LIMIT 1""",(prompt,)).fetchone()
print(json.dumps(dict(row) if row else {}))`;
  const result = spawnSync(join(backend, ".venv/bin/python"), ["-c", query, join(dataRoot, "jarvisos.db"), prompt], { encoding: "utf8" });
  assert(result.status === 0, `runtime metric read failed: ${result.stderr}`);
  return JSON.parse(result.stdout);
};
const send = async (prompt) => {
  const started = Date.now();
  await page.getByLabel("Message", { exact: true }).fill(prompt);
  await page.getByRole("button", { name: /Send without project context/ }).click();
  const transcript = page.getByRole("list", { name: "Jarvis thread transcript" });
  const entry = transcript.locator("li").filter({ hasText: prompt });
  await entry.waitFor({ state: "visible", timeout: 240_000 });
  await page.waitForFunction((text) => {
    const item = [...document.querySelectorAll('[aria-label="Jarvis thread transcript"] li')].find((node) => node.textContent?.includes(text));
    return Boolean(item && item.querySelector("details") && /Canonical state/.test(item.textContent ?? "") && !/Submitting/.test(item.textContent ?? ""));
  }, prompt, { timeout: 240_000 });
  const details = entry.getByText("Interaction details", { exact: true });
  await details.click();
  await entry.getByText("Canonical state", { exact: true }).waitFor();
  const text = (await entry.innerText()) ?? "";
  const state = (text.match(/Canonical state\s+(\S+)/) ?? [])[1] ?? "unknown";
  const answer = await entry.locator("p").evaluateAll((paragraphs) => {
    const answerParagraph = paragraphs.find((item) => item.querySelector("strong")?.textContent?.trim() === "Jarvis");
    return answerParagraph?.textContent?.replace(/^Jarvis\s*/, "").trim() ?? "";
  });
  const metrics = persistedRuntimeMetrics(prompt);
  const usage = JSON.parse(metrics.usage_totals_json ?? "{}");
  const flow = {
    prompt,
    answer,
    state,
    finish_reason: metrics.normalized_finish_reason,
    eval_counts: {
      prompt: metrics.input_tokens,
      output: metrics.output_tokens,
      source: metrics.normalized_usage_source,
    },
    usage_totals: usage,
    duration_ms: Date.now() - started,
  };
  timings.push({ prompt, duration_ms: flow.duration_ms });
  flows.push(flow);
  return { entry, flow };
};

try {
  const initialized = spawnSync(join(backend, ".venv/bin/python"), ["-c", "from app.core.database import initialize_database; initialize_database()"], { cwd: backend, env: baseEnv, encoding: "utf8" });
  assert(initialized.status === 0, `database initialization failed: ${initialized.stderr}`);
  browser = await chromium.launch({ headless: true });
  context = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
  page = await context.newPage();
  page.on("console", (message) => { if (message.type() === "error") consoleErrors.push(message.text()); });
  page.on("pageerror", (error) => pageErrors.push(String(error)));
  await startBackend("http://127.0.0.1:11436/api/generate");
  const workspaceResponse = await fetch(`${backendUrl}/workspaces`, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ name: "151 Sidecar Operator Proof", slug: `sidecar-${Date.now()}` }) });
  assert(workspaceResponse.ok, `workspace creation failed: ${workspaceResponse.status}`);
  workspaceId = (await workspaceResponse.json()).id;
  await page.goto(`${backendUrl}/design/process`, { waitUntil: "networkidle" });
  await openSidecar();
  const unreachableOptions = await optionRecords();
  const unreachable = unreachableOptions.find((item) => item.value === routeClass);
  assert(unreachable?.disabled && /not reachable/i.test(unreachable.text), `unreachable route not disabled with reason: ${JSON.stringify(unreachableOptions)}`);
  const testResponder = unreachableOptions.find((item) => item.value === "local:fake");
  assert(testResponder && /test responder/i.test(testResponder.text), `test responder is not labelled test-only: ${JSON.stringify(testResponder)}`);
  await page.getByLabel("Jarvis responder").selectOption("local:fake");
  await page.getByText("Test responder only — synthetic output, not an AI answer.", { exact: true }).waitFor();
  await snap("unreachable-routes");

  await startBackend(endpoint);
  await page.reload({ waitUntil: "networkidle" });
  await openSidecar();
  await page.waitForFunction((route) => [...document.querySelectorAll('[aria-label="Jarvis responder"] option')].some((option) => option.value === route && !option.disabled), routeClass, { timeout: 60_000 });
  const reachableOptions = await optionRecords();
  const localRoute = page.getByLabel("Jarvis responder");
  await localRoute.selectOption(routeClass);
  await page.getByLabel("Message", { exact: true }).waitFor();
  const jarvis = await send("funzioni jarvis?");
  assert(jarvis.flow.state === "complete", `funzioni jarvis? interaction was ${JSON.stringify(jarvis.flow)}`);
  assert(jarvis.flow.finish_reason === "stop", `funzioni jarvis? finish was ${jarvis.flow.finish_reason}`);
  assert(/jarvisos/i.test(jarvis.flow.answer) && !/marvel/i.test(jarvis.flow.answer), `identity answer did not identify JarvisOS: ${jarvis.flow.answer}`);
  assert(!/incomplete/i.test(await jarvis.entry.innerText()), "complete identity response shows an incomplete warning");
  const ciao = await send("ciao");
  assert(ciao.flow.state === "complete", `ciao interaction was ${JSON.stringify(ciao.flow)}`);
  assert(ciao.flow.finish_reason === "stop", `ciao finish was ${ciao.flow.finish_reason}`);
  assert(/[àèéìòù]|\b(ciao|buongiorno|salve|sono|posso|come|aiutarti|aiuto)\b/i.test(ciao.flow.answer), `Italian response not observed: ${ciao.flow.answer}`);
  await snap("complete-answers");

  // No supported provider-registry route-budget override exists in this build.
  const length = { status: "skipped", reason: "No existing config/env override exposes a smaller local route budget; product code and registry config were left unchanged." };
  assert(consoleErrors.length === 0, `browser console errors: ${consoleErrors.join(" | ")}`);
  assert(pageErrors.length === 0, `browser page errors: ${pageErrors.join(" | ")}`);
  const evidence = {
    schema: "jarvisos.151-sidecar-operator-proof.v1",
    source_sha: execFileSync("git", ["rev-parse", "HEAD"], { cwd: root, encoding: "utf8" }).trim(),
    workspace_id: workspaceId,
    runtime_endpoint_kind: runtimeKind,
    runtime_endpoint: endpoint,
    route_class: routeClass,
    model_id: model,
    browser: "Chromium via Playwright",
    route_options: { unreachable: unreachableOptions, reachable: reachableOptions },
    flows,
    length_finish: length,
    screenshots,
    console_errors: consoleErrors,
    page_errors: pageErrors,
    timings_ms: timings,
    elapsed_seconds: (Date.now() - proofStartedAt) / 1000,
  };
  await writeFile(join(output, "sidecar_operator_proof.json"), `${JSON.stringify(evidence, null, 2)}\n`, "utf8");
  console.log(JSON.stringify(evidence, null, 2));
  succeeded = true;
  await stopBackend();
} finally {
  await context?.close().catch(() => {});
  await browser?.close().catch(() => {});
  await stopBackend();
  if (succeeded) {
    await rm(dataRoot, { recursive: true, force: true });
    await rm(tempDir, { recursive: true, force: true });
  }
}
