#!/usr/bin/env node
// Real Chromium proof for the existing Jarvis Sidecar, following the isolated
// backend/frontend lifecycle used by qualification 149.
import { mkdir, mkdtemp, rm, stat, writeFile } from "node:fs/promises";
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
const runtime = arg("--runtime", "ollama");
if (!["ollama", "llamacpp"].includes(runtime)) throw new Error(`unsupported runtime: ${runtime}`);
const isLlamaCpp = runtime === "llamacpp";
const route = isLlamaCpp ? "local:llamacpp" : routeClass;
const proofFile = join(output, isLlamaCpp ? "sidecar_operator_proof.llamacpp.json" : "sidecar_operator_proof.json");
const runtimeKind = arg("--runtime-kind", isLlamaCpp ? "Jarvis-owned llama.cpp runtime" : "Windows Ollama via temporary dev bridge");
const llamaBinaryDir = "/home/thera/jarvis-control/work/tools/llama.cpp/b11178/dist/llama-b11178";
const llamaConfig = {
  binary_path: `${llamaBinaryDir}/llama-server`,
  library_dirs: [llamaBinaryDir, "/home/thera/jarvis-control/work/tools/llama.cpp/b11178/dist/cudart-llama-b11178-bin-ubuntu-cuda-12.8-x64"],
  model_path: "/mnt/d/Sovereign-AI/models/Qwen3.8-27B/gguf/Qwen3.8-27B-UD-Q4_K_XL.gguf",
  model_sha256: "bee238bbeb3dc0a34bde4d0dedbaee1f98c009e8bb4226f03070054c12fb1372",
  pinned_build_id: "b11178-f9af9be21",
  port: 18081,
  ctx_size: 8192,
};
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
const runtimeSnapshots = [];
const loadingSnapshots = [];
const runtimeActions = [];
let server;
let browser;
let context;
let page;
let workspaceId;
let succeeded = false;
let runtimeStarted = false;
let llamaLogPath;
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
  };
  if (!isLlamaCpp) {
    env.JARVISOS_DEV_MESSAGE_ROUTE_ENDPOINT = devEndpoint;
    env.JARVISOS_DEV_MESSAGE_ROUTE_MODEL = model;
    env.JARVISOS_DEV_MESSAGE_ROUTE_TIMEOUT_S = timeoutSeconds;
  } else {
    delete env.JARVISOS_DEV_MESSAGE_ROUTE_ENDPOINT;
    delete env.JARVISOS_DEV_MESSAGE_ROUTE_MODEL;
    delete env.JARVISOS_DEV_MESSAGE_ROUTE_TIMEOUT_S;
    for (const name of Object.keys(env)) {
      if (name.startsWith("JARVISOS_LLAMACPP_") && name !== "JARVISOS_LLAMACPP_CONFIG") delete env[name];
    }
    delete env.JARVISOS_MANAGE_LLAMACPP;
    env.JARVISOS_LLAMACPP_CONFIG = join(dataRoot, "settings", "llama_cpp.json");
  }
  const log = join(tempDir, `backend-${devEndpoint.includes("11436") ? "unreachable" : "reachable"}.log`);
  server = spawn(join(backend, ".venv/bin/python"), ["-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", String(backendPort)], {
    cwd: backend, env, stdio: ["ignore", openSync(log, "w"), openSync(log, "a")],
  });
  await waitForHttp(`${backendUrl}/health`);
};
const snap = async (name) => {
  const path = join(output, `sidecar-${isLlamaCpp ? "llamacpp-" : ""}${name}.jpg`);
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
row=c.execute("""SELECT f.state,f.terminal_reason,f.usage_totals_json,j.normalized_finish_reason,j.input_tokens,j.output_tokens,j.reasoning_tokens,j.normalized_usage_source
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
  await entry.waitFor({ state: "visible", timeout: 900_000 });
  await page.waitForFunction((text) => {
    const item = [...document.querySelectorAll('[aria-label="Jarvis thread transcript"] li')].find((node) => node.textContent?.includes(text));
    return Boolean(item && item.querySelector("details") && /Canonical state/.test(item.textContent ?? "") && !/Submitting/.test(item.textContent ?? ""));
  }, prompt, { timeout: 900_000 });
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
    reasoning_tokens: metrics.reasoning_tokens,
    duration_ms: Date.now() - started,
  };
  timings.push({ prompt, duration_ms: flow.duration_ms });
  flows.push(flow);
  return { entry, flow };
};

const runtimeRequest = async (action) => {
  const response = await fetch(`${backendUrl}/local-ai/runtime/llama-cpp${action ? `/${action}` : ""}`, {
    method: action ? "POST" : "GET",
  });
  assert(response.ok, `llama.cpp ${action || "status"} returned ${response.status}`);
  const body = await response.json();
  runtimeSnapshots.push({ at: new Date().toISOString(), action: action || "status", status: body });
  if (body.reason_code === "LLAMACPP_LOADING") loadingSnapshots.push({ at: new Date().toISOString(), status: body });
  if (action) runtimeActions.push({ action, status: body });
  return body;
};

const waitForLlamaLoaded = async (phase, maxWait = 15 * 60_000) => {
  const started = Date.now();
  const deadline = started + maxWait;
  let latest;
  while (Date.now() < deadline) {
    latest = await runtimeRequest("");
    if (latest.runtime_reachable && latest.model_loaded) {
      return { phase, duration_ms: Date.now() - started, status: latest };
    }
    await delay(2_000);
  }
  throw new Error(`${phase} llama.cpp runtime did not load within ${maxWait}ms: ${JSON.stringify(latest)}`);
};

const readLlamaLogEvidence = async () => {
  const { readFile } = await import("node:fs/promises");
  let log = "";
  try { log = await readFile(llamaLogPath, "utf8"); } catch { /* failure path may precede log creation */ }
  const lines = log.split(/\r?\n/).filter((line) => /build|cuda|offload|buffer|n_ctx|ctx|slot|model loader|server is listening/i.test(line));
  return { path: llamaLogPath, relevant_lines: lines.slice(-100) };
};

const processIds = () => {
  const result = spawnSync("pgrep", ["-x", "llama-server"], { encoding: "utf8" });
  return result.status === 0 ? result.stdout.trim().split(/\s+/).filter(Boolean).map(Number) : [];
};

const waitForGpuGate = async () => {
  const qualificationPath = "/home/thera/jarvis-control/work/out/w3/llamacpp-qualification.json";
  while (true) {
    const qualificationExists = await stat(qualificationPath).then(() => true, () => false);
    const busyPids = processIds();
    if (qualificationExists && busyPids.length === 0) return { qualification_path: qualificationPath, qualification_exists: true, llama_server_pids: [] };
    console.log(JSON.stringify({ waiting_for_gpu_gate: true, qualification_exists: qualificationExists, llama_server_pids: busyPids }));
    await delay(5_000);
  }
};

const unloadOllamaModels = async () => {
  let response;
  try { response = await fetch("http://127.0.0.1:11435/api/ps", { signal: AbortSignal.timeout(3_000) }); }
  catch (error) { return { checked: false, reason: `Ollama API unavailable: ${error}` }; }
  if (!response.ok) return { checked: false, reason: `Ollama /api/ps returned ${response.status}` };
  const data = await response.json();
  const models = Array.isArray(data.models) ? data.models : [];
  const unloaded = [];
  for (const item of models) {
    const name = item.name ?? item.model;
    if (!name) continue;
    const result = await fetch("http://127.0.0.1:11435/api/generate", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ model: name, keep_alive: 0, stream: false }),
      signal: AbortSignal.timeout(30_000),
    });
    assert(result.ok, `Ollama unload for ${name} returned ${result.status}`);
    unloaded.push(name);
  }
  let remaining = models;
  const deadline = Date.now() + 30_000;
  while (remaining.length && Date.now() < deadline) {
    await delay(1_000);
    const check = await fetch("http://127.0.0.1:11435/api/ps", { signal: AbortSignal.timeout(3_000) });
    assert(check.ok, `Ollama post-unload /api/ps returned ${check.status}`);
    const current = await check.json();
    remaining = Array.isArray(current.models) ? current.models : [];
  }
  assert(remaining.length === 0, `Ollama still has loaded models: ${JSON.stringify(remaining)}`);
  return { checked: true, models_before: models.map((item) => item.name ?? item.model), unloaded, models_after: [] };
};

const readLaunchArguments = async (pid) => {
  if (!pid) return null;
  const { readFile } = await import("node:fs/promises");
  const bytes = await readFile(`/proc/${pid}/cmdline`);
  return { pid, source: `/proc/${pid}/cmdline`, argv: bytes.toString("utf8").split("\0").filter(Boolean) };
};

try {
  if (isLlamaCpp) {
    await mkdir(join(dataRoot, "settings"), { recursive: true });
    llamaLogPath = join(dataRoot, "logs", "llama-server.log");
    await writeFile(join(dataRoot, "settings", "llama_cpp.json"), `${JSON.stringify({
      ...llamaConfig,
      manage: false,
      startup_wait_s: 0.1,
      request_timeout_s: 900,
      log_path: llamaLogPath,
    }, null, 2)}\n`, "utf8");
  }
  const initialized = spawnSync(join(backend, ".venv/bin/python"), ["-c", "from app.core.database import initialize_database; initialize_database()"], { cwd: backend, env: baseEnv, encoding: "utf8" });
  assert(initialized.status === 0, `database initialization failed: ${initialized.stderr}`);
  browser = await chromium.launch({ headless: true });
  context = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
  page = await context.newPage();
  page.on("console", (message) => { if (message.type() === "error") consoleErrors.push(message.text()); });
  page.on("pageerror", (error) => pageErrors.push(String(error)));
  await startBackend(isLlamaCpp ? "" : "http://127.0.0.1:11436/api/generate");
  const firstPassStatus = isLlamaCpp ? await runtimeRequest("") : null;
  if (isLlamaCpp) {
    assert(!firstPassStatus.runtime_reachable && !firstPassStatus.pid && !firstPassStatus.spawned_by_jarvis,
      `llama.cpp runtime was expected to be stopped in pass 1: ${JSON.stringify(firstPassStatus)}`);
  }
  const workspaceResponse = await fetch(`${backendUrl}/workspaces`, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ name: "151 Sidecar Operator Proof", slug: `sidecar-${Date.now()}` }) });
  assert(workspaceResponse.ok, `workspace creation failed: ${workspaceResponse.status}`);
  workspaceId = (await workspaceResponse.json()).id;
  await page.goto(`${backendUrl}/design/process`, { waitUntil: "networkidle" });
  await openSidecar();
  const unreachableOptions = await optionRecords();
  const unreachable = unreachableOptions.find((item) => item.value === route);
  assert(unreachable?.disabled && /not reachable|loading/i.test(unreachable.text), `unreachable route not disabled with reason: ${JSON.stringify(unreachableOptions)}`);
  const testResponder = unreachableOptions.find((item) => item.value === "local:fake");
  assert(testResponder && /test responder/i.test(testResponder.text), `test responder is not labelled test-only: ${JSON.stringify(testResponder)}`);
  await page.getByLabel("Jarvis responder").selectOption("local:fake");
  await page.getByText("Test responder only — synthetic output, not an AI answer.", { exact: true }).waitFor();
  await snap("unreachable-routes");

  let loadedEvidence;
  let restartEvidence;
  let ollamaUnload = null;
  let gpuGate = null;
  let launchArguments = null;
  if (isLlamaCpp) {
    gpuGate = await waitForGpuGate();
    ollamaUnload = await unloadOllamaModels();
    const startAt = Date.now();
    const initialStart = await runtimeRequest("start");
    runtimeStarted = true;
    if (initialStart.runtime_reachable && initialStart.model_loaded) {
      loadedEvidence = { phase: "cold_start", duration_ms: Date.now() - startAt, status: initialStart };
    } else {
      assert(initialStart.reason_code === "LLAMACPP_LOADING" || !initialStart.runtime_reachable,
        `unexpected start response: ${JSON.stringify(initialStart)}`);
      loadedEvidence = await waitForLlamaLoaded("cold_start");
      loadedEvidence.duration_ms += Date.now() - startAt;
    }
    launchArguments = await readLaunchArguments(loadedEvidence.status.pid);
    await page.reload({ waitUntil: "networkidle" });
    await openSidecar();
    await page.waitForFunction((selectedRoute) => [...document.querySelectorAll('[aria-label="Jarvis responder"] option')].some((option) => option.value === selectedRoute && !option.disabled), route, { timeout: 60_000 });
  } else {
    await startBackend(endpoint);
    await page.reload({ waitUntil: "networkidle" });
    await openSidecar();
    await page.waitForFunction((selectedRoute) => [...document.querySelectorAll('[aria-label="Jarvis responder"] option')].some((option) => option.value === selectedRoute && !option.disabled), route, { timeout: 60_000 });
  }
  const reachableOptions = await optionRecords();
  const localRoute = page.getByLabel("Jarvis responder");
  await localRoute.selectOption(route);
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

  let length;
  if (isLlamaCpp) {
    const truncated = await send("Scrivi i numeri da 1 a 3000, uno per riga, senza commenti.");
    const truncatedText = await truncated.entry.innerText();
    assert(truncated.flow.state !== "complete", `long answer unexpectedly complete: ${JSON.stringify(truncated.flow)}`);
    assert(truncated.flow.finish_reason === "length", `long answer finish was ${truncated.flow.finish_reason}`);
    assert(/This answer is incomplete/i.test(truncatedText), "length-finished answer did not render the incomplete warning");
    const continueButton = truncated.entry.getByRole("button", { name: "Continue as a new message" });
    await continueButton.waitFor({ state: "visible", timeout: 10_000 });
    await snap("incomplete-answer");
    await continueButton.click();
    const continuationPrompt = await page.getByLabel("Message", { exact: true }).inputValue();
    assert(continuationPrompt.length > 0, "continue button did not populate the next-message prompt");
    const continuation = await send(continuationPrompt);
    length = {
      status: "observed",
      interaction: truncated.flow,
      hidden_reasoning_empty_visible_answer: !truncated.flow.answer,
      incomplete_warning_rendered: true,
      continue_button_rendered: true,
      continuation_clicked: true,
      continuation_prompt: continuationPrompt,
      continuation_result: continuation.flow,
    };
  } else {
    // Preserve the existing Ollama proof behavior while marking this lane-specific observation N/A.
    length = { status: "not_run", reason: "Length-finish proof is specific to the llamacpp lane." };
  }

  if (isLlamaCpp) {
    const restartAt = Date.now();
    const restarted = await runtimeRequest("restart");
    if (restarted.runtime_reachable && restarted.model_loaded) {
      restartEvidence = { duration_ms: Date.now() - restartAt, status: restarted };
    } else {
      restartEvidence = await waitForLlamaLoaded("warm_restart");
      restartEvidence.duration_ms += Date.now() - restartAt;
    }
    const restartCiao = await send("ciao");
    assert(restartCiao.flow.state === "complete" && restartCiao.flow.finish_reason === "stop",
      `post-restart ciao did not complete: ${JSON.stringify(restartCiao.flow)}`);
  }
  assert(consoleErrors.length === 0, `browser console errors: ${consoleErrors.join(" | ")}`);
  assert(pageErrors.length === 0, `browser page errors: ${pageErrors.join(" | ")}`);
  let llamaLogEvidence = null;
  let remainingLlamaPids = [];
  if (isLlamaCpp) {
    await runtimeRequest("stop");
    runtimeStarted = false;
    remainingLlamaPids = processIds();
    assert(remainingLlamaPids.length === 0, `llama-server processes remain after stop: ${remainingLlamaPids.join(", ")}`);
    llamaLogEvidence = await readLlamaLogEvidence();
  }
  const evidence = {
    schema: "jarvisos.151-sidecar-operator-proof.v1",
    source_sha: execFileSync("git", ["rev-parse", "HEAD"], { cwd: root, encoding: "utf8" }).trim(),
    workspace_id: workspaceId,
    runtime_endpoint_kind: runtimeKind,
    runtime_endpoint: isLlamaCpp ? "Jarvis-owned loopback llama.cpp runtime on port 18081" : endpoint,
    route_class: route,
    model_id: isLlamaCpp ? "qwen3.8-27b-q4kxl" : model,
    runtime_configuration: isLlamaCpp ? llamaConfig : undefined,
    runtime_actions: runtimeActions,
    first_pass_runtime_status: firstPassStatus,
    runtime_status_snapshots: runtimeSnapshots,
    loading_snapshots: loadingSnapshots,
    cold_load: loadedEvidence,
    warm_restart: restartEvidence,
    server_log: llamaLogEvidence,
    ollama_unload: ollamaUnload,
    gpu_gate: gpuGate,
    launch_arguments: launchArguments,
    remaining_llama_server_pids: remainingLlamaPids,
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
  await writeFile(proofFile, `${JSON.stringify(evidence, null, 2)}\n`, "utf8");
  console.log(JSON.stringify(evidence, null, 2));
  succeeded = true;
  await stopBackend();
} finally {
  if (runtimeStarted && isLlamaCpp) {
    await runtimeRequest("stop").catch(() => {});
  }
  await context?.close().catch(() => {});
  await browser?.close().catch(() => {});
  await stopBackend();
  if (succeeded) {
    await rm(dataRoot, { recursive: true, force: true });
    await rm(tempDir, { recursive: true, force: true });
  }
}
