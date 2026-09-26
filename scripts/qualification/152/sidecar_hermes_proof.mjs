#!/usr/bin/env node
// Exact-head Chromium + real Hermes + local llama.cpp proof for spec 152.
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
const proofFile = join(output, "sidecar_hermes_proof.json");
const args = process.argv.slice(2);
const untilArg = args.find((item) => item.startsWith("--until="));
const until = untilArg?.slice("--until=".length) ?? (args.includes("--until") ? args[args.indexOf("--until") + 1] : "complete");
if (!["complete", "unavailable"].includes(until)) throw new Error(`unsupported --until value: ${until}`);
const responseWaitMs = Number(process.env.JARVISOS_PROOF_RESPONSE_TIMEOUT_MS ?? 1_800_000);
const idleStopWaitMs = Number(process.env.JARVISOS_HERMES_IDLE_STOP_WAIT_MS ?? 360_000);
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
  // Agent mode re-sends Hermes' system prompt, tool schemas and tool results each
  // relay call; 8192 overflowed (8654-token request). A q8_0 KV cache keeps 16k
  // fully on the GPU (measured 10.8 of 12.2 GB, same prompt/generation speed).
  ctx_size: 16384,
  n_gpu_layers: 99,
  extra_args: ["-fa", "on", "-ctk", "q8_0", "-ctv", "q8_0"],
};
const dataRoot = await mkdtemp(join(tmpdir(), "jarvisos-152p-data-"));
const tempDir = await mkdtemp(join(tmpdir(), "jarvisos-152p-proof-"));
await mkdir(join(dataRoot, "settings"), { recursive: true });
const llamaLogPath = join(dataRoot, "logs", "llama-server.log");
await writeFile(join(dataRoot, "settings", "llama_cpp.json"), `${JSON.stringify({
  ...llamaConfig, manage: false, startup_wait_s: 0.1, request_timeout_s: 900, log_path: llamaLogPath,
}, null, 2)}\n`);

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

const env = { ...process.env, JARVISOS_DATA_ROOT: dataRoot,
  JARVISOS_LLAMACPP_CONFIG: join(dataRoot, "settings", "llama_cpp.json"),
  JARVISOS_HERMES_INFERENCE_ROUTE: "local:llamacpp" };
const proof = {
  schema: "jarvisos.152-sidecar-hermes-proof.v1",
  source_sha: execFileSync("git", ["rev-parse", "HEAD"], { cwd: root, encoding: "utf8" }).trim(),
  hermes_venv: env.JARVIS_HERMES_VENV ?? null,
  hermes_venv_python: env.JARVIS_HERMES_VENV ? join(env.JARVIS_HERMES_VENV, "bin/python") : null,
  workspace_id: null, thread_id: null, seeded_decision: null,
  runtime_configuration: llamaConfig, route_options: {}, screenshots: [], turns: [],
  console_errors: [], page_errors: [], worker_status: [], runtime_status: [],
  rss_vram_samples: [], proof_failures: [], proof_status: "incomplete",
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
  const path = join(output, `sidecar-hermes-${name}.jpg`);
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
const threadDetail = async () => api(`/ai/threads/${proof.thread_id}?workspace_id=${proof.workspace_id}`);

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
  const requestId = `proof152-${label}-${Date.now()}`;
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
const waitForWorkerStopped = async () => {
  const deadline = Date.now() + idleStopWaitMs;
  let latest;
  while (Date.now() < deadline) {
    latest = await hermesStatus();
    proof.worker_status.push({ label: "idle_stop_poll", status: latest });
    if (latest.state === "stopped") return latest;
    await delay(2_000);
  }
  throw new Error(`Hermes supervisor did not stop its idle worker within ${idleStopWaitMs}ms: ${JSON.stringify(latest)}`);
};
const waitForProcessExit = async (pid) => {
  const deadline = Date.now() + 10_000;
  while (Date.now() < deadline) {
    try { process.kill(pid, 0); } catch (error) {
      if (error.code === "ESRCH") return true;
      throw error;
    }
    await delay(250);
  }
  return false;
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
  const initialized = spawnSync(join(backend, ".venv/bin/python"), ["-c", "from app.core.database import initialize_database; initialize_database()"], { cwd: backend, env, encoding: "utf8" });
  assert(initialized.status === 0, `database initialization failed: ${initialized.stderr}`);
  browser = await chromium.launch({ headless: true });
  context = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
  page = await context.newPage();
  page.on("console", (message) => { if (message.type() === "error") proof.console_errors.push(message.text()); });
  page.on("pageerror", (error) => proof.page_errors.push(String(error)));
  await startBackend();

  const workspace = await api("/workspaces", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ name: "152 Hermes proof", slug: `hermes-${Date.now()}` }) });
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
    // Seed canonical Second Brain data through the product API (no direct DB writes).
    // The unique beacon token is only obtainable through retrieval (the prompt names the
    // decision id but never the token), so it is the grounding check; wording may vary.
    const beacon = `ORCHID-${Date.now()}`;
    const fact = `The 152 proof beacon is ${beacon}.`;
    const decision = await api(`/workspaces/${proof.workspace_id}/decisions`, {
      method: "POST", headers: { "content-type": "application/json" },
      body: JSON.stringify({ title: "152 Hermes retrieval beacon", decision_text: fact,
        rationale: "Unique factual marker seeded through the canonical Decision API for retrieval qualification.", status: "accepted" }),
    });
    assert(decision.decision_text === fact, `seeded Decision API response differed from requested fact: ${JSON.stringify(decision)}`);
    proof.seeded_decision = { id: decision.id, title: decision.title, fact, source_ref: `modeling:decision:${decision.id}` };

    const start = await runtimeRequest("start");
    llamaStarted = true;
    proof.runtime_status.push({ phase: "start", status: start });
    const digestStart = await runtimeRequest("verify-digest");
    proof.runtime_status.push({ phase: "verify_digest", status: digestStart });
    const loaded = start.model_loaded && start.runtime_reachable ? start : await waitForLlamaLoaded();
    proof.runtime_status.push({ phase: "loaded", status: loaded });
    assert(loaded.model_loaded && loaded.runtime_reachable, `llama.cpp did not reach loaded state: ${JSON.stringify(loaded)}`);
    assert(loaded.configured_sha256 === modelSha256, `configured GGUF SHA changed: ${loaded.configured_sha256}`);
    const digestDeadline = Date.now() + 15 * 60_000;
    let digestStatus = loaded;
    while (digestStatus.digest_state !== "verified" && Date.now() < digestDeadline) {
      await delay(2_000);
      digestStatus = await runtimeRequest("");
      proof.runtime_status.push({ phase: "verify_digest_poll", status: digestStatus });
      if (digestStatus.digest_state === "mismatch") throw new Error(`IQ2_M GGUF digest mismatch: ${digestStatus.model_sha256}`);
    }
    assert(digestStatus.digest_state === "verified" && digestStatus.model_sha256 === modelSha256,
      `IQ2_M GGUF SHA was not verified: ${JSON.stringify(digestStatus)}`);
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
    const prompt = `Use jarvis_retrieval_query in the Second Brain to find the accepted decision with the 152 proof beacon. Answer with the exact beacon fact and cite the decision id ${decision.id}. Do not guess; only report what the retrieval result supports.`;
    const first = await send(prompt, "retrieval-grounding");
    const answer = first.record.answer;
    assert(first.interaction.flow_state === "complete" && first.interaction.persistence_state === "captured", `first canonical interaction did not complete and capture: ${JSON.stringify(first.interaction)}`);
    assert(answer.includes(beacon) && answer.includes(decision.id), `grounded answer did not render the seeded fact and evidence ref ${decision.id}: ${answer}`);
    assert(first.evidence.ai_jobs.length > 0 && first.evidence.ai_jobs.every((job) => job.selected_route_class === "local:llamacpp" && job.model_id === llamaConfig.model_id), `relay ai_jobs did not prove local:llamacpp and model ${llamaConfig.model_id}: ${JSON.stringify(first.evidence.ai_jobs)}`);
    assert(first.evidence.ai_jobs.every((job) => job.status === "success"), `relay job did not succeed: ${JSON.stringify(first.evidence.ai_jobs)}`);
    assert(!first.evidence.ai_jobs.some((job) => job.model_id === "local:fake"), "a relay ai_job used local:fake");
    const toolEvents = first.evidence.events.map((item) => item.payload).filter((item) => item?.tool_name === "jarvis_retrieval_query");
    assert(toolEvents.some((item) => item.status === "succeeded" && item.evidence_refs?.some((ref) => String(ref).includes(decision.id))), `no successful retrieval tool event with decision evidence ref: ${JSON.stringify(first.evidence.events)}`);
    const flowEvent = first.evidence.events.map((item) => item.payload).find((item) => item?.relay_flow_ids);
    assert(flowEvent && flowEvent.reservation_flow_id && flowEvent.final_flow_id, `reservation/relay flow event missing: ${JSON.stringify(first.evidence.events)}`);
    const reservationFlow = first.evidence.flows.find((item) => item.id === flowEvent.reservation_flow_id);
    assert(reservationFlow?.state === "cancelled_terminal" && reservationFlow.terminal_reason === "agent_relayed", `reservation flow was not terminally linked to relay: ${JSON.stringify(reservationFlow)}`);
    proof.turns[0].reservation_flow_id = flowEvent.reservation_flow_id;
    proof.turns[0].relay_flow_ids = flowEvent.relay_flow_ids;
    proof.turns[0].tool_events = toolEvents;
    await snap("grounded-answer");

    const generation1 = (await hermesStatus()).threads?.[proof.thread_id]?.generation;
    assert(Number.isInteger(generation1), `worker generation unavailable after first turn: ${JSON.stringify(await hermesStatus())}`);
    const second = await send("In one sentence, repeat the 152 proof beacon from the same thread.", "worker-reuse");
    const generation2 = (await hermesStatus()).threads?.[proof.thread_id]?.generation;
    assert(second.interaction.flow_state === "complete", `second turn did not complete: ${JSON.stringify(second.interaction)}`);
    assert(generation2 === generation1, `same thread did not reuse Hermes generation ${generation1}; got ${generation2}`);
    proof.worker_reuse = { generation_first: generation1, generation_second: generation2 };

    // Product supervisor owns the stop: its bounded idle-stop timer removes the worker after 300 s.
    const workerPid1 = (await hermesStatus()).threads?.[proof.thread_id]?.worker_pid;
    const stopped = await waitForWorkerStopped();
    const workerExited1 = workerPid1 ? await waitForProcessExit(workerPid1) : false;
    assert(workerExited1, `Hermes supervisor reported stopped but worker PID ${workerPid1} still exists`);
    proof.worker_stop = { mechanism: "HermesSessionPool scheduled idle stop (300 seconds)", worker_pid: workerPid1, process_exited: workerExited1, status: stopped };
    const third = await send("Use jarvis_retrieval_query again to retrieve the 152 proof beacon, then state the exact beacon fact and its decision id.", "worker-restart");
    const status3 = await hermesStatus();
    const generation3 = status3.threads?.[proof.thread_id]?.generation;
    assert(third.interaction.flow_state === "complete", `post-stop turn did not complete: ${JSON.stringify(third.interaction)}`);
    assert(Number.isInteger(generation3) && generation3 > generation2, `worker did not restart with a new generation: ${JSON.stringify(status3)}`);
    const persisted = await threadDetail();
    assert(persisted.interactions.length === 3 && persisted.interactions.every((item) => item.persistence_state === "captured"), "canonical transcript was not intact after worker restart");
    proof.worker_restart = { generation_before_stop: generation2, generation_after_restart: generation3, status: status3, transcript_interactions: persisted.interactions.length };
    assert(third.record.answer.includes(beacon) && third.record.answer.includes(decision.id), `post-restart answer lost its grounded evidence: ${third.record.answer}`);
    assert(second.record.answer.includes(beacon), `worker-reuse answer lost the beacon: ${second.record.answer}`);
    proof.worker_restart.retrieval_tool_events = third.evidence.events.map((item) => item.payload)
      .filter((item) => item?.tool_name === "jarvis_retrieval_query" && item.status === "succeeded").length;

    const workerPid3 = status3.threads?.[proof.thread_id]?.worker_pid;
    const finalWorkerStop = await waitForWorkerStopped();
    const workerExited3 = workerPid3 ? await waitForProcessExit(workerPid3) : false;
    assert(workerExited3, `Hermes supervisor reported stopped but worker PID ${workerPid3} still exists`);
    proof.final_worker_cleanup = { worker_pid: workerPid3, process_exited: workerExited3, status: finalWorkerStop };
    const stop = await runtimeRequest("stop");
    llamaStarted = false;
    proof.runtime_status.push({ phase: "stop", status: stop });
    await page.reload({ waitUntil: "networkidle" });
    await openSidecar();
    const optionsStopped = await optionRecords();
    proof.route_options.runtime_stopped = optionsStopped;
    const agentStopped = optionsStopped.find((item) => item.value === "hermes:agent");
    assert(agentStopped?.disabled && /unavailable|not configured|not reachable/i.test(agentStopped.text), `Hermes mode did not show a truthful stopped-runtime reason: ${JSON.stringify(agentStopped)}`);
    proof.unavailable_status_rendered_stopped = await showHermesUnavailable();
    await snap("runtime-stopped");
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
  } else {
    proof.retained_data_root = dataRoot;
  }
}
console.log(JSON.stringify(proof, null, 2));
if (fatalError || proof.proof_status !== "passed") process.exitCode = 1;
