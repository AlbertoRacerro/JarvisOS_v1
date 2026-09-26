#!/usr/bin/env node
// Exact-head Chromium + real Hermes + local llama.cpp proof for spec 153.
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
const backendPort = Number(process.env.JARVISOS_PROOF_BACKEND_PORT ?? 8152);
const backendUrl = `http://127.0.0.1:${backendPort}`;
const proofFile = join(output, "sidecar_laya_proof.json");
const args = process.argv.slice(2);
const untilArg = args.find((item) => item.startsWith("--until="));
const until = untilArg?.slice("--until=".length) ?? (args.includes("--until") ? args[args.indexOf("--until") + 1] : "complete");
if (!["complete", "unavailable"].includes(until)) throw new Error(`unsupported --until value: ${until}`);
const responseWaitMs = Number(process.env.JARVISOS_PROOF_RESPONSE_TIMEOUT_MS ?? 1_800_000);
const modelPath = "/mnt/d/Sovereign-AI/models/Qwen3.8-27B/gguf/Qwen3.8-27B-IQ2_M.gguf";
const modelSha256 = "9cea2418408b6dd2a98ac5b1c9561fd95a5689fb1b8e851288a9e249431b4b06";
const llamaBinaryDir = "/home/thera/jarvis-control/work/tools/llama.cpp/b11178/dist/llama-b11178";
const llamaConfig = {
  binary_path: `${llamaBinaryDir}/llama-server`,
  library_dirs: [llamaBinaryDir, "/home/thera/jarvis-control/work/tools/llama.cpp/b11178/dist/cudart-llama-b11178-bin-ubuntu-cuda-12.8-x64"],
  model_path: modelPath,
  model_sha256: modelSha256,
  model_id: "qwen3.8-27b-iq2m",
  pinned_build_id: "b11178-f9af9be21",
  port: 18081,
  // Same agent-mode sizing as the 152 proof: 8192 overflows Hermes relay prompts.
  ctx_size: 16384,
  n_gpu_layers: 99,
  extra_args: ["-fa", "on", "-ctk", "q8_0", "-ctv", "q8_0"],
};
const dataRoot = await mkdtemp(join(tmpdir(), "jarvisos-153p-data-"));
const tempDir = await mkdtemp(join(tmpdir(), "jarvisos-153p-proof-"));
await mkdir(join(dataRoot, "settings"), { recursive: true });
const llamaLogPath = join(dataRoot, "logs", "llama-server.log");
await writeFile(join(dataRoot, "settings", "llama_cpp.json"), `${JSON.stringify({
  ...llamaConfig, manage: false, startup_wait_s: 0.1, request_timeout_s: 900, log_path: llamaLogPath,
}, null, 2)}\n`);

const env = { ...process.env, JARVISOS_DATA_ROOT: dataRoot,
  JARVISOS_LLAMACPP_CONFIG: join(dataRoot, "settings", "llama_cpp.json"),
  JARVISOS_HERMES_INFERENCE_ROUTE: "local:llamacpp", JARVISOS_LAYA_BACKEND: "rules" };
const proof = {
  schema: "jarvisos.153-sidecar-laya-proof.v1",
  source_sha: execFileSync("git", ["rev-parse", "HEAD"], { cwd: root, encoding: "utf8" }).trim(),
  hermes_venv: env.JARVIS_HERMES_VENV ?? null,
  hermes_venv_python: env.JARVIS_HERMES_VENV ? join(env.JARVIS_HERMES_VENV, "bin/python") : null,
  workspace_id: null, thread_id: null, seeded_decision: null,
  runtime_configuration: llamaConfig, route_options: {}, screenshots: [], turns: [],
  console_errors: [], page_errors: [], worker_status: [], runtime_status: [],
  rss_vram_samples: [], proof_failures: [], proof_status: "incomplete", laya_latency_ms: null,
  started_at: new Date().toISOString(),
};
let server;
let browser;
let context;
let page;
let llamaStarted = false;
let evidenceWritten = false;
let fatalError;
const assert = (ok, message) => { if (!ok) throw new Error(message); };
const waitForHttp = async (url, timeout = 60_000) => {
  const deadline = Date.now() + timeout;
  while (Date.now() < deadline) {
    try { if ((await fetch(url, { signal: AbortSignal.timeout(2_000) })).ok) return; } catch { /* server starting */ }
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
const startBackend = async () => {
  const log = join(tempDir, "backend.log");
  server = spawn(join(backend, ".venv/bin/python"), ["-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", String(backendPort)], {
    cwd: backend, env, stdio: ["ignore", openSync(log, "w"), openSync(log, "a")],
  });
  await waitForHttp(`${backendUrl}/health`);
};
const api = async (path, init) => {
  const response = await fetch(`${backendUrl}${path}`, init);
  const body = await response.json().catch(() => ({}));
  assert(response.ok, `${init?.method ?? "GET"} ${path} returned ${response.status}: ${JSON.stringify(body)}`);
  return body;
};
const snap = async (name) => {
  const path = join(output, `sidecar-laya-${name}.jpg`);
  await page.screenshot({ path, type: "jpeg", quality: 68, fullPage: false, animations: "disabled" });
  const sizeBytes = (await stat(path)).size;
  proof.screenshots.push({ path: path.slice(root.length + 1), size_bytes: sizeBytes });
};
const openSidecar = async () => {
  const toggle = page.getByRole("button", { name: "Show context" });
  if (await toggle.count()) await toggle.click();
  await page.getByTestId("jarvis-sidecar").waitFor({ state: "visible", timeout: 20_000 });
  const settings = page.locator(".jarvis-conversation-settings");
  if (!(await settings.evaluate((node) => node.open))) await settings.locator("summary").click();
  await page.getByLabel("Jarvis responder").waitFor({ timeout: 20_000 });
};
const optionRecords = async () => page.getByLabel("Jarvis responder").locator("option").evaluateAll((options) => options.map((option) => ({
  text: option.textContent?.trim() ?? "", value: option.value, disabled: option.disabled,
})).filter((item) => item.value));
const showHermesUnavailable = async () => {
  // Disabled options cannot be picked by a user. Select the disabled value only in
  // the rendered DOM so the screenshot exposes its truthful active-route status.
  await page.getByLabel("Jarvis responder").evaluate((select) => {
    const setter = Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype, "value").set;
    setter.call(select, "hermes:agent");
    select.dispatchEvent(new Event("change", { bubbles: true }));
  });
  // Best effort: the controlled select may reject a disabled value; the option text
  // assertions carry the truthful-unavailable evidence either way.
  return page.locator(".jarvis-sidecar__status").filter({
    hasText: /Hermes agent runtime|Hermes requires|configured local inference runtime is unavailable|Hermes agent is unavailable/i,
  }).first().waitFor({ timeout: 5_000 }).then(() => true, () => false);
};
const runtimeRequest = async (action) => api(`/local-ai/runtime/llama-cpp${action ? `/${action}` : ""}`, { method: action ? "POST" : "GET" });
const hermesStatus = async () => api("/agents/hermes/status");

const metricSnapshot = (interactionId) => {
  const query = `import json,sqlite3,sys
db,interaction=sys.argv[1:]
c=sqlite3.connect(db); c.row_factory=sqlite3.Row
i=c.execute("SELECT id,user_text,assistant_text,flow_id,persistence_state FROM ai_thread_interactions WHERE id=?",(interaction,)).fetchone()
if not i: print("{}"); raise SystemExit
ev=[dict(r) for r in c.execute("SELECT event_type,target_id,payload FROM events WHERE event_type IN ('hermes.interaction_flows','hermes.tool_result','hermes.agent_event') AND (target_id=? OR payload LIKE ?)",(interaction,'%'+interaction+'%'))]
for e in ev:
 try:e['payload']=json.loads(e['payload'] or '{}')
 except Exception:pass
ids={i["flow_id"]}
for e in ev:
 if e["event_type"]=='hermes.interaction_flows':
  ids.add(e['payload'].get('reservation_flow_id'))
  ids.update(e['payload'].get('relay_flow_ids') or [])
ids.discard(None)
flows=[dict(r) for r in c.execute("SELECT id,state,terminal_reason,terminal_attempt_id,usage_totals_json FROM ai_flows WHERE id IN (%s)" % ','.join('?'*len(ids)),tuple(ids))] if ids else []
jobs=[dict(r) for r in c.execute("SELECT id,flow_id,status,selected_route_class,model_id,input_tokens,output_tokens,latency_ms,usage_source FROM ai_jobs WHERE flow_id IN (%s) ORDER BY created_at,flow_attempt_index" % ','.join('?'*len(ids)),tuple(ids))] if ids else []
print(json.dumps({"interaction":dict(i),"flows":flows,"ai_jobs":jobs,"events":ev}))`;
  const result = spawnSync(join(backend, ".venv/bin/python"), ["-c", query, join(dataRoot, "jarvisos.db"), interactionId], { encoding: "utf8" });
  assert(result.status === 0, `runtime evidence query failed: ${result.stderr}`);
  return JSON.parse(result.stdout);
};
const sampleGpu = async (turn) => {
  const status = await runtimeRequest("");
  const pid = status.pid;
  let rssKb = null;
  if (pid) {
    try {
      const procStatus = await (await import("node:fs/promises")).readFile(`/proc/${pid}/status`, "utf8");
      const value = procStatus.match(/^VmRSS:\s+(\d+)/m)?.[1];
      rssKb = value ? Number(value) : null;
    } catch { /* sampled after process exit */ }
  }
  const gpu = spawnSync("nvidia-smi", ["--query-compute-apps=pid,used_memory", "--format=csv,noheader,nounits"], { encoding: "utf8" });
  const vramMb = gpu.status === 0 ? gpu.stdout.trim().split(/\r?\n/).map((line) => line.split(",").map((part) => part.trim())).filter((parts) => Number(parts[0]) === Number(pid)).map((parts) => Number(parts[1])).at(0) ?? null : null;
  proof.rss_vram_samples.push({ turn, at: new Date().toISOString(), llama_pid: pid ?? null,
    rss_kb: Number.isFinite(rssKb) ? rssKb : null, vram_mb: vramMb,
    nvidia_smi_available: gpu.status === 0 });
};
const send = async (prompt, label) => {
  const started = Date.now();
  const requestId = `proof153-${label}-${Date.now()}`;
  await page.getByLabel("Message", { exact: true }).fill(prompt);
  const sampler = setInterval(() => { void sampleGpu(label).catch((error) => proof.proof_failures.push(`GPU sampler: ${error}`)); }, 1_000);
  await page.getByRole("button", { name: /Send without project context/ }).click();
  const transcript = page.getByRole("list", { name: "Jarvis thread transcript" });
  const marker = prompt.replace(/\s+/g, " ").trim().slice(0, 120);
  const entry = transcript.locator("li").filter({ hasText: marker }).last();
  try {
    await entry.waitFor({ state: "visible", timeout: responseWaitMs });
    await page.waitForFunction((text) => {
      const item = [...document.querySelectorAll('[aria-label="Jarvis thread transcript"] li')].filter((node) => (node.textContent ?? "").replace(/\s+/g, " ").includes(text)).at(-1);
      return Boolean(item && item.querySelector("details") && /Canonical state/.test(item.textContent ?? "") && !/Submitting/.test(item.textContent ?? ""));
    }, marker, { timeout: responseWaitMs });
  } finally { clearInterval(sampler); }
  const detail = await threadDetail();
  const interaction = [...detail.interactions].find((item) => item.request_id === requestId)
    ?? [...detail.interactions].find((item) => item.user_text === prompt);
  assert(interaction, `canonical interaction not found for ${label}`);
  const evidence = metricSnapshot(interaction.id);
  const answer = interaction.assistant_text ?? "";
  const record = { label, prompt, interaction_id: interaction.id, interaction_index: interaction.interaction_index,
    answer, interaction_state: interaction.flow_state, persistence_state: interaction.persistence_state,
    flow_id: interaction.flow_id, terminal_reason: interaction.terminal_reason,
    duration_ms: Date.now() - started, durable_evidence: evidence };
  proof.turns.push(record);
  proof.worker_status.push({ label, status: await hermesStatus() });
  return { entry, interaction, evidence, record };
};
const waitForLlamaLoaded = async () => {
  const deadline = Date.now() + 15 * 60_000;
  let latest;
  while (Date.now() < deadline) {
    latest = await runtimeRequest("");
    proof.runtime_status.push({ at: new Date().toISOString(), status: latest });
    if (latest.runtime_reachable && latest.model_loaded) return latest;
    await delay(2_000);
  }
  throw new Error(`llama.cpp did not report loaded within 15 minutes: ${JSON.stringify(latest)}`);
};

try {
  // Build the bundle from this exact checkout and reject a bundle aimed at another API.
  execFileSync("node", ["node_modules/vite/bin/vite.js", "build"], {
    cwd: join(root, "frontend"),
    env: { ...process.env, VITE_API_BASE_URL: backendUrl },
    stdio: ["ignore", "ignore", "inherit"],
  });
  const bundleFiles = execFileSync("rg", ["--no-ignore", "-l", backendUrl, "dist/assets"], {
    cwd: join(root, "frontend"), encoding: "utf8",
  }).trim().split(/\r?\n/).filter(Boolean);
  if (!bundleFiles.length) throw new Error(`stale-bundle guard: built frontend does not contain ${backendUrl}`);
  const initialized = spawnSync(join(backend, ".venv/bin/python"), ["-c", "from app.core.database import initialize_database; initialize_database()"], { cwd: backend, env, encoding: "utf8" });
  assert(initialized.status === 0, `database initialization failed: ${initialized.stderr}`);
  browser = await chromium.launch({ headless: true });
  context = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
  page = await context.newPage();
  page.on("console", (message) => { if (message.type() === "error") proof.console_errors.push(message.text()); });
  page.on("pageerror", (error) => proof.page_errors.push(String(error)));
  await startBackend();

  const workspace = await api("/workspaces", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ name: "153 Laya proof", slug: `laya-${Date.now()}` }) });
  proof.workspace_id = workspace.id;
  await page.goto(`${backendUrl}/design/process`, { waitUntil: "networkidle" });
  await openSidecar();
  const statusDown = await runtimeRequest("");
  proof.runtime_status.push({ phase: "runtime_down", status: statusDown });
  const optionsDown = await optionRecords();
  proof.route_options.runtime_down = optionsDown;
  const agentDown = optionsDown.find((item) => item.value === "hermes:agent");
  assert(agentDown?.disabled, `Hermes mode should be unavailable while llama.cpp is down: ${JSON.stringify(agentDown)}`);
  assert(/not configured|unavailable|not reachable|not installed|not match|requires/i.test(agentDown.text), `Hermes unavailable option lacks a truthful reason: ${JSON.stringify(agentDown)}`);
  proof.unavailable_status_rendered_down = await showHermesUnavailable();
  await snap("runtime-down");
  if (until === "unavailable") {
    proof.proof_status = "incomplete";
    proof.proof_failures.push("intentional --until=unavailable dry run; runtime turns were not executed");
  } else {
    const loadStarted = Date.now();
    const started = await runtimeRequest("start");
    llamaStarted = true;
    proof.runtime_status.push({ phase: "start", status: started });
    const loaded = await waitForLlamaLoaded();
    proof.runtime_status.push({ phase: "loaded", status: loaded });
    proof.cold_load_ms = Date.now() - loadStarted;
    await page.reload({ waitUntil: "networkidle" });
    await openSidecar();
    const optionsReady = await optionRecords();
    proof.route_options.runtime_ready = optionsReady;
    const agentReady = optionsReady.find((item) => item.value === "hermes:agent");
    assert(agentReady && !agentReady.disabled, `Hermes mode did not become available: ${JSON.stringify(agentReady)}`);
    await page.getByLabel("Jarvis responder").selectOption("hermes:agent");
    await page.getByRole("button", { name: "New thread" }).click();
    const threadSelect = page.getByLabel("Conversation");
    // The Conversation select is labelled by its wrapping <label>, not an aria-label attribute.
    const threadDeadline = Date.now() + 30_000;
    while (!(await threadSelect.inputValue()) && Date.now() < threadDeadline) await delay(250);
    proof.thread_id = await threadSelect.inputValue();
    assert(proof.thread_id, "Sidecar did not create and select a canonical thread");
    const prompt = "A tool step failed with a retryable error on its first attempt. Consult Jarvis using the jarvis_decide tool with kind retry_or_stop, previous_outcome failed, attempt_count 0, and retryable true. Report Jarvis's recommendation and whether it abstained.";
    const first = await send(prompt, "retry-advice");
    assert(first.interaction.flow_state === "complete" && first.interaction.persistence_state === "captured", `canonical interaction did not complete and capture: ${JSON.stringify(first.interaction)}`);
    assert(first.evidence.ai_jobs.length > 0 && first.evidence.ai_jobs.every((job) => job.selected_route_class === "local:llamacpp" && job.model_id === llamaConfig.model_id), `relay ai_jobs did not prove local:llamacpp and model ${llamaConfig.model_id}: ${JSON.stringify(first.evidence.ai_jobs)}`);
    assert(first.evidence.ai_jobs.every((job) => job.status === "success"), `relay job did not succeed: ${JSON.stringify(first.evidence.ai_jobs)}`);
    assert(!first.evidence.ai_jobs.some((job) => job.model_id === "local:fake"), "a relay ai_job used local:fake");
    const decideEvents = first.evidence.events.map((item) => item.payload).filter((item) => item?.tool_name === "jarvis_decide");
    const decideEvent = decideEvents.find((item) => item.capability_id === "jarvis.decide" && item.status === "succeeded");
    assert(decideEvent, `no successful jarvis.decide tool_result event: ${JSON.stringify(first.evidence.events)}`);
    assert(decideEvent.interaction_id === first.interaction.id, `decision evidence is not linked to canonical interaction ${first.interaction.id}`);
    assert(decideEvent.kind === "retry_or_stop" && decideEvent.outcome === "decided" && decideEvent.recommendation === "retry", `unexpected Laya result: ${JSON.stringify(decideEvent)}`);
    assert(typeof decideEvent.request_digest === "string" && /^sha256:[0-9a-f]{64}$/.test(decideEvent.request_digest), `decision request digest missing or malformed: ${JSON.stringify(decideEvent)}`);
    assert(typeof decideEvent.backend_model_ref === "string" && decideEvent.backend_model_ref.length > 0, "decision backend model ref missing");
    assert(Number.isFinite(decideEvent.latency_ms) && decideEvent.latency_ms >= 0, "decision latency missing");
    assert(typeof decideEvent.current_relay_flow_id === "string" && first.evidence.flows.some((flow) => flow.id === decideEvent.current_relay_flow_id), `decision relay flow is not present for interaction: ${JSON.stringify(decideEvent)}`);
    const interactionFlowEvent = first.evidence.events.map((item) => item.payload).find((item) => item?.relay_flow_ids);
    assert(interactionFlowEvent?.relay_flow_ids?.includes(decideEvent.current_relay_flow_id), `decision event flow is not a relay flow of this interaction: ${JSON.stringify(interactionFlowEvent)}`);
    assert(decideEvent.arguments?.kind === "retry_or_stop" && decideEvent.arguments?.request_digest === decideEvent.request_digest, "decision event arguments do not contain only bounded digest metadata");
    assert(!JSON.stringify(decideEvent).includes("previous_outcome") && !JSON.stringify(decideEvent).includes("retryable"), "raw decision request leaked into durable tool evidence");
    assert(first.record.answer.toLowerCase().includes("retry"), `Hermes response did not report the recommendation: ${first.record.answer}`);
    proof.laya_latency_ms = decideEvent.latency_ms;
    proof.turns[0].tool_events = decideEvents;
    proof.turns[0].relay_flow_ids = interactionFlowEvent.relay_flow_ids;
    await snap("laya-advice");
    const stop = await runtimeRequest("stop");
    llamaStarted = false;
    proof.runtime_status.push({ phase: "stop", status: stop });
    assert(proof.console_errors.length === 0, `browser console errors: ${proof.console_errors.join(" | ")}`);
    assert(proof.page_errors.length === 0, `browser page errors: ${proof.page_errors.join(" | ")}`);
    proof.proof_status = "passed";
    proof.proof_failures = [];
  }
} catch (error) {
  fatalError = String(error);
  proof.proof_failures.push(fatalError);
} finally {
  if (llamaStarted && server) await runtimeRequest("stop").catch((error) => proof.proof_failures.push(`llama cleanup failed: ${error}`));
  await context?.close().catch(() => {});
  await browser?.close().catch(() => {});
  await stopBackend();
  proof.finished_at = new Date().toISOString();
  proof.elapsed_seconds = (Date.now() - Date.parse(proof.started_at)) / 1000;
  if (proof.proof_status !== "passed") proof.proof_status = "incomplete";
  await writeFile(proofFile, `${JSON.stringify(proof, null, 2)}\n`);
  evidenceWritten = true;
  // Failed runs keep their data root (backend log, Hermes worker stderr, database) for diagnosis.
  if (proof.proof_status === "passed" || env.JARVISOS_PROOF_DISCARD_FAILED === "1") {
    await rm(dataRoot, { recursive: true, force: true });
    await rm(tempDir, { recursive: true, force: true });
  }
}
console.log(JSON.stringify(proof, null, 2));
if (fatalError || proof.proof_status !== "passed") process.exitCode = 1;
