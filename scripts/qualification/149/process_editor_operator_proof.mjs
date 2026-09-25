#!/usr/bin/env node
import { createHash } from "node:crypto";
import { mkdtemp, readFile, rm, writeFile, stat } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import { spawn, spawnSync } from "node:child_process";
import { setTimeout as delay } from "node:timers/promises";
import { chromium } from "/home/thera/jarvis-control/work/tools/pw/node_modules/playwright/index.mjs";

const root = resolve(new URL("../../../", import.meta.url).pathname);
const backend = join(root, "backend");
const output = new URL(".", import.meta.url).pathname;
const runtime =
  "/home/thera/jarvis-control/work/tools/dwsim-10.2.9/mcp-root/opt/dwsim-mcp/dwsim-mcp";
const runtimeBytes = await readFile(runtime);
const runtimeSha = createHash("sha256").update(runtimeBytes).digest("hex");
const dataRoot = await mkdtemp(join(tmpdir(), "jarvisos-149-ui-"));
const tempDir = await mkdtemp(join(tmpdir(), "jarvisos-149-ui-proof-"));
const backendLog = join(tempDir, "backend.log");
const env = {
  ...process.env,
  JARVISOS_DATA_ROOT: dataRoot,
  JARVISOS_DWSIM_MCP_PATH: runtime,
  JARVISOS_DWSIM_MCP_SHA256: runtimeSha,
};
const initialized = spawnSync(
  join(backend, ".venv/bin/python"),
  [
    "-c",
    "from app.core.database import initialize_database; initialize_database()",
  ],
  { cwd: backend, env, encoding: "utf8" },
);
if (initialized.status !== 0)
  throw new Error(
    `isolated database initialization failed: ${initialized.stderr}`,
  );
const backendProc = spawn(
  join(backend, ".venv/bin/python"),
  ["-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"],
  {
    cwd: backend,
    env,
    stdio: [
      "ignore",
      await import("node:fs").then(({ openSync }) => openSync(backendLog, "w")),
      await import("node:fs").then(({ openSync }) => openSync(backendLog, "a")),
    ],
  },
);
const browser = await chromium.launch({ headless: true });
const screenshots = [];
const actions = [];
const timings = [];
const projectionDigests = [];
const revisionChain = [];
const commandTrace = [];
const startedAt = Date.now();
let workspaceId = "";
let originalCaseId = "";
let pageErrors = [];
let browserContext;
let otherContext;

const assert = (condition, message) => {
  if (!condition) throw new Error(message);
};
const traceCommands = (currentPage) => {
  currentPage.on("request", (request) => {
    if (request.method() === "POST" && request.url().includes("/commands"))
      commandTrace.push({ request: request.postDataJSON() });
  });
  currentPage.on("response", async (response) => {
    if (response.request().method() !== "POST" || !response.url().includes("/commands"))
      return;
    const entry = commandTrace.at(-1);
    if (entry) {
      entry.status = response.status();
      try {
        entry.response = await response.json();
      } catch {
        entry.response = "<non-json response>";
      }
    }
  });
};
const waitForHttp = async (url, timeoutMs = 60_000) => {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    try {
      if ((await fetch(url)).ok) return;
    } catch {
      /* service is still starting */
    }
    await delay(250);
  }
  throw new Error(`service did not become ready: ${url}`);
};
const screenshot = async (currentPage, name) => {
  assert(screenshots.length < 8, "screenshot limit exceeded");
  const path = join(output, `process-editor-${name}.png`);
  await currentPage
    .getByTestId("process-editor-surface")
    .screenshot({ path, animations: "disabled" });
  const sizeBytes = (await stat(path)).size;
  assert(
    sizeBytes <= 300 * 1024,
    `${name} screenshot is ${sizeBytes} bytes, over 300 KiB`,
  );
  screenshots.push({
    path: path.slice(root.length + 1),
    size_bytes: sizeBytes,
  });
};
const loaded = async (currentPage) => {
  const evidence = currentPage.locator(".dwsim-evidence");
  if (!(await evidence.evaluate((node) => node.open)))
    await evidence.locator("summary").click();
  await evidence.locator("pre").waitFor({ state: "visible" });
  const projection = JSON.parse(await evidence.locator("pre").textContent());
  if (
    !revisionChain.length ||
    revisionChain[revisionChain.length - 1] !== projection.revision
  )
    revisionChain.push(projection.revision);
  const digest = createHash("sha256")
    .update(JSON.stringify(projection))
    .digest("hex");
  if (
    !projectionDigests.length ||
    projectionDigests[projectionDigests.length - 1].revision !==
      projection.revision
  )
    projectionDigests.push({ revision: projection.revision, sha256: digest });
  return projection;
};
const waitCommand = async (currentPage) => {
  const started = Date.now();
  const message = currentPage.locator(".dwsim-message[role=status]");
  await currentPage.waitForFunction(
    () =>
      (
        document.querySelector(".dwsim-message[role=status]")?.textContent ?? ""
      ).startsWith("Applying "),
    null,
    { timeout: 30_000 },
  );
  await currentPage.waitForFunction(
    () => {
      const text =
        document.querySelector(".dwsim-message[role=status]")?.textContent ??
        "";
      return text.length > 0 && !text.startsWith("Applying ");
    },
    null,
    { timeout: 180_000 },
  );
  const text = (await message.textContent()) ?? "";
  if (!/read back as revision/.test(text))
    throw new Error(
      `operator command failed in UI: ${text}; last command ${JSON.stringify(commandTrace.at(-1))}`,
    );
  const success = await currentPage
    .getByRole("status")
    .filter({ hasText: /read back as revision/ })
    .textContent();
  timings.push({
    operation: success?.split(" read back")[0] ?? "command",
    duration_ms: Date.now() - started,
  });
  return loaded(currentPage);
};
const waitRestore = async (currentPage) => {
  const started = Date.now();
  const message = currentPage.locator(".dwsim-message[role=status]");
  await currentPage.waitForFunction(
    () =>
      (
        document.querySelector(".dwsim-message[role=status]")?.textContent ?? ""
      ).startsWith("Restoring revision"),
    null,
    { timeout: 30_000 },
  );
  await currentPage.waitForFunction(
    () => {
      const text =
        document.querySelector(".dwsim-message[role=status]")?.textContent ??
        "";
      return text.length > 0 && !text.startsWith("Restoring revision");
    },
    null,
    { timeout: 180_000 },
  );
  const text = (await message.textContent()) ?? "";
  if (!/Restored as revision/.test(text))
    throw new Error(`operator restore failed in UI: ${text}`);
  timings.push({ operation: "restore", duration_ms: Date.now() - started });
  return loaded(currentPage);
};
const waitImport = async (currentPage, previousCaseId) => {
  const started = Date.now();
  await currentPage.waitForFunction(
    (previous) => {
      const text = document.querySelector(".dwsim-evidence pre")?.textContent;
      if (!text) return false;
      try {
        return JSON.parse(text).case_id !== previous;
      } catch {
        return false;
      }
    },
    previousCaseId,
    { timeout: 180_000 },
  );
  timings.push({ operation: "download_reimport", duration_ms: Date.now() - started });
  return loaded(currentPage);
};
const selectObject = async (currentPage, tag) => {
  const object = currentPage.getByRole("button", {
    name: new RegExp(`^${tag},`),
  });
  await object.waitFor({ state: "visible" });
  await object.click();
  await currentPage.waitForFunction(
    (expected) =>
      document
        .querySelector(".dwsim-node rect.is-selected")
        ?.closest(".dwsim-node")
        ?.getAttribute("aria-label")
        ?.startsWith(`${expected},`) ?? false,
    tag,
  );
};
const setPlacement = async (currentPage, tag, x, y) => {
  await currentPage.getByLabel("Object tag").fill(tag);
  await currentPage.getByLabel("Canvas X").fill(String(x));
  await currentPage.getByLabel("Canvas Y").fill(String(y));
};
const addStream = async (currentPage, tag, x, y) => {
  await setPlacement(currentPage, tag, x, y);
  await currentPage
    .getByRole("button", { name: "Material stream", exact: true })
    .click();
  await waitCommand(currentPage);
};
const connect = async (currentPage, unit, stream, role, port) => {
  await currentPage
    .getByLabel("Connect unit", { exact: true })
    .selectOption({ label: unit });
  await currentPage
    .getByLabel("Connect stream", { exact: true })
    .selectOption({ label: stream });
  await currentPage
    .getByLabel("Connect role", { exact: true })
    .selectOption(role);
  await currentPage
    .getByLabel("Connect port", { exact: true })
    .fill(String(port));
  await currentPage
    .getByRole("button", { name: "Connect", exact: true })
    .click();
  await waitCommand(currentPage);
};
const setStreamValues = async (currentPage, tag, flow) => {
  await selectObject(currentPage, tag);
  await currentPage.getByLabel("Temperature (K)").fill("298.15");
  await currentPage.getByLabel("Pressure (Pa)").fill("101325");
  await currentPage.getByLabel("Mass flow (kg/s)").fill(String(flow));
  await currentPage.getByLabel("Mass fractions JSON").fill('{"Water":1}');
  await currentPage
    .getByRole("button", { name: "Apply stream conditions", exact: true })
    .click();
  const projection = await waitCommand(currentPage);
  const stream = renderedObject(projection, tag);
  assert(
    Number(massFlow(stream)) === flow,
    `${tag} mass flow read back as ${massFlow(stream)}, expected ${flow}`,
  );
  assert(
    stream.results?.temperature_K === 298.15,
    `${tag} temperature was not read back in K`,
  );
  assert(
    stream.results?.pressure_Pa === 101325,
    `${tag} pressure was not read back in Pa`,
  );
};
const renderedObject = (projection, tag) =>
  projection.objects.find((item) => item.tag === tag);
const massFlow = (object) => object?.results?.mass_flow_kg_s ?? null;

try {
  await waitForHttp("http://127.0.0.1:8000/health");
  await waitForHttp("http://127.0.0.1:8000/");
  const createdWorkspace = await fetch("http://127.0.0.1:8000/workspaces", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({
      name: "149 Process Editor Operator Proof",
      slug: `process-editor-${Date.now()}`,
    }),
  });
  assert(
    createdWorkspace.ok,
    `workspace creation failed: ${createdWorkspace.status}`,
  );
  workspaceId = (await createdWorkspace.json()).id;
  browserContext = await browser.newContext({
    viewport: { width: 1440, height: 1000 },
    acceptDownloads: true,
  });
  const page = await browserContext.newPage();
  traceCommands(page);
  page.on("pageerror", (error) => pageErrors.push(String(error)));
  await page.goto("http://127.0.0.1:8000/design/process", {
    waitUntil: "networkidle",
  });
  await page.getByRole("button", { name: "New blank case" }).click();
  await page
    .getByText("DWSIM available", { exact: true })
    .waitFor({ timeout: 180_000 });
  await page
    .getByText("Create or import a DWSIM case to begin.")
    .waitFor({ state: "hidden" })
    .catch(() => {});
  let projection = await loaded(page);
  originalCaseId = projection.case_id;
  actions.push({
    action: "create_case",
    case_id: originalCaseId,
    revision: projection.revision,
  });
  const dynamics = page.getByRole("region", {
    name: "DWSIM dynamics controls",
  });
  await dynamics.getByRole("heading", { name: "Dynamics" }).waitFor();
  const dynamicsUnavailable = Boolean(projection.dynamics?.unavailable_reason);
  const runDynamics = dynamics.getByRole("button", { name: "Run dynamics" });
  assert(
    (await runDynamics.isDisabled()) === dynamicsUnavailable,
    "dynamics run availability does not match the server projection",
  );
  await dynamics.getByLabel("New state name").fill("operator-proof");
  const saveState = dynamics.getByRole("button", {
    name: "Save current state",
  });
  assert(
    (await saveState.isDisabled()) === dynamicsUnavailable,
    "state-save availability does not match the server projection",
  );
  actions.push({
    action: "dynamics_availability",
    unavailable_reason: projection.dynamics?.unavailable_reason ?? null,
    run_enabled: !dynamicsUnavailable,
    state_save_enabled: !dynamicsUnavailable,
  });
  await screenshot(page, "blank-case");

  await page.getByLabel("Compounds (comma separated)").fill("Water");
  await page
    .getByRole("button", { name: "Add compounds", exact: true })
    .click();
  projection = await waitCommand(page);
  assert(
    projection.compounds.includes("Water"),
    "Water not shown in returned projection",
  );
  await page
    .getByLabel("Property package", { exact: true })
    .fill("Steam Tables (IAPWS-IF97)");
  await page
    .getByRole("button", { name: "Set property package", exact: true })
    .click();
  projection = await waitCommand(page);
  assert(
    String(projection.property_package).toLowerCase().includes("steam tables"),
    "Steam Tables package was not read back",
  );
  actions.push({
    action: "thermodynamics",
    compounds: projection.compounds,
    property_package: projection.property_package,
  });

  await addStream(page, "FeedA", 45, 80);
  await addStream(page, "FeedB", 45, 190);
  await addStream(page, "Product", 440, 135);
  await setPlacement(page, "Mixer1", 230, 135);
  await page.getByRole("button", { name: "Add unit", exact: true }).click();
  projection = await waitCommand(page);
  assert(
    renderedObject(projection, "Mixer1"),
    "Mixer missing from returned projection",
  );
  await screenshot(page, "native-graph");

  await connect(page, "Mixer1", "FeedA", "feed", 0);
  await connect(page, "Mixer1", "FeedB", "feed", 1);
  await connect(page, "Mixer1", "Product", "product", 0);
  projection = await loaded(page);
  assert(
    projection.connections.length === 3,
    `expected 3 native connections, got ${projection.connections.length}`,
  );
  const mixer = renderedObject(projection, "Mixer1");
  const mixerNode = page.getByRole("button", { name: /^Mixer1,/ });
  const box = await mixerNode.boundingBox();
  assert(box, "Mixer node has no browser bounding box");
  await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
  await page.mouse.down();
  await page.mouse.move(
    box.x + box.width / 2 + 42,
    box.y + box.height / 2 + 28,
    { steps: 5 },
  );
  await page.mouse.up();
  projection = await waitCommand(page);
  const moved = renderedObject(projection, "Mixer1");
  const transform = await page
    .getByRole("button", { name: /^Mixer1,/ })
    .getAttribute("transform");
  assert(
    moved.x !== mixer.x || moved.y !== mixer.y,
    "server did not read back a changed Mixer position",
  );
  assert(
    transform === `translate(${moved.x},${moved.y})`,
    `canvas transform ${transform} differs from server position ${moved.x},${moved.y}`,
  );
  actions.push({
    action: "drag_move",
    from: { x: mixer.x, y: mixer.y },
    readback: { x: moved.x, y: moved.y },
    canvas_transform: transform,
  });

  await selectObject(page, "FeedA");
  await page.getByLabel("Rename selected object").fill("FeedA_Renamed");
  await page.getByRole("button", { name: "Rename", exact: true }).click();
  projection = await waitCommand(page);
  assert(
    renderedObject(projection, "FeedA_Renamed"),
    "renamed feed missing from projection",
  );
  await setStreamValues(page, "FeedA_Renamed", 1.0);
  await setStreamValues(page, "FeedB", 1.0);
  await page.getByRole("button", { name: "Solve", exact: true }).click();
  projection = await waitCommand(page);
  const productFlow = massFlow(renderedObject(projection, "Product"));
  const feedFlow =
    Number(massFlow(renderedObject(projection, "FeedA_Renamed"))) +
    Number(massFlow(renderedObject(projection, "FeedB")));
  assert(
    typeof productFlow === "number" && Math.abs(productFlow - feedFlow) <= 1e-6,
    `Mixer product flow ${productFlow} did not equal feed sum ${feedFlow}`,
  );
  assert(
    projection.last_solve?.solve_status,
    "solve status missing from returned projection",
  );
  assert(
    projection.last_solve?.mass_balance_status === "calculated",
    "server did not calculate the mass balance from native boundary streams",
  );
  const returnedResidual = projection.last_solve?.mass_balance_residual_kg_s;
  const residual = returnedResidual;
  const residualSource = "last_solve.mass_balance_residual_kg_s";
  assert(Number.isFinite(residual), "operator residual is not numeric");
  assert(
    (await page.getByText(/Residual · .* kg\/s · source:/).count()) === 1,
    "UI does not show residual and source",
  );
  actions.push({
    action: "solve",
    solve_status: projection.last_solve.solve_status,
    feed_mass_flow_kg_s: feedFlow,
    product_mass_flow_kg_s: productFlow,
    mass_balance_residual_kg_s: residual,
    mass_balance_residual_source: residualSource,
    server_mass_balance_status: projection.last_solve.mass_balance_status,
  });
  await screenshot(page, "solved");

  otherContext = await browser.newContext({
    viewport: { width: 1280, height: 900 },
  });
  const otherPage = await otherContext.newPage();
  traceCommands(otherPage);
  otherPage.on("pageerror", (error) => pageErrors.push(String(error)));
  await otherPage.goto("http://127.0.0.1:8000/design/process", {
    waitUntil: "networkidle",
  });
  await otherPage.getByText("DWSIM available", { exact: true }).waitFor();
  await addStream(otherPage, "ConcurrentStream", 600, 330);
  await selectObject(page, "FeedB");
  await page.getByLabel("Rename selected object").fill("FeedB_Stale");
  await page.getByRole("button", { name: "Rename", exact: true }).click();
  await page
    .getByRole("status")
    .filter({ hasText: "Changed elsewhere. The stale edit was discarded" })
    .waitFor({ timeout: 180_000 });
  projection = await loaded(page);
  assert(
    renderedObject(projection, "ConcurrentStream"),
    "409 refetch did not replace first context with the current projection",
  );
  actions.push({
    action: "stale_edit",
    status: 409,
    message: "Changed elsewhere; stale edit discarded",
    refreshed_revision: projection.revision,
  });
  await screenshot(page, "revision-conflict");

  const sourceShape = projection.objects
    .map((item) => [item.tag, item.x, item.y])
    .sort((a, b) => String(a[0]).localeCompare(String(b[0])));
  const sourceConnections = projection.connections;
  const latestDownloadLink = page
    .getByRole("link", { name: "Download", exact: true })
    .first();
  const [download] = await Promise.all([
    page.waitForEvent("download"),
    latestDownloadLink.click(),
  ]);
  const downloadPath = join(tempDir, "roundtrip.dwxmz");
  await download.saveAs(downloadPath);
  const sourceCaseId = projection.case_id;
  await page.locator('input[type="file"]').setInputFiles(downloadPath);
  projection = await waitImport(page, sourceCaseId);
  const importedCaseId = projection.case_id;
  const importedShape = projection.objects
    .map((item) => [item.tag, item.x, item.y])
    .sort((a, b) => String(a[0]).localeCompare(String(b[0])));
  assert(
    JSON.stringify(importedShape) === JSON.stringify(sourceShape),
    "download/re-import changed object layout",
  );
  assert(
    JSON.stringify(projection.connections) ===
      JSON.stringify(sourceConnections),
    "download/re-import changed native connection records",
  );
  actions.push({
    action: "download_reimport",
    imported_case_id: importedCaseId,
    imported_revision: projection.revision,
    object_count: projection.objects.length,
    connection_count: projection.connections.length,
    layout_and_connections_match: true,
  });
  await screenshot(page, "roundtrip");

  await page.getByLabel("DWSIM case").selectOption(originalCaseId);
  projection = await loaded(page);
  const oldRevision = page
    .getByRole("button", { name: "Restore", exact: true })
    .last();
  await oldRevision.click();
  projection = await waitRestore(page);
  assert(
    projection.objects.length === 0,
    "restoring the initial revision did not restore the original empty case",
  );
  actions.push({
    action: "restore",
    revision: projection.revision,
    restored_object_count: projection.objects.length,
  });
  await screenshot(page, "restored");

  assert(
    pageErrors.length === 0,
    `browser emitted page errors: ${pageErrors.join(" | ")}`,
  );
  const sourceSha = (await import("node:child_process"))
    .execFileSync("git", ["rev-parse", "HEAD"], { cwd: root, encoding: "utf8" })
    .trim();
  const finalProjection = await loaded(page);
  const uiProjectionDigest = createHash("sha256")
    .update(JSON.stringify(finalProjection))
    .digest("hex");
  const evidence = {
    schema: "jarvisos.149-process-editor-operator-proof.v1",
    source_sha: sourceSha,
    workspace_id: workspaceId,
    case_id: originalCaseId,
    imported_case_id: importedCaseId,
    dwsim_version: finalProjection.dwsim_version,
    mcp_sha256: runtimeSha,
    revision_chain: revisionChain,
    projection_digests_rendered_by_ui: projectionDigests,
    actions,
    final_ui_projection_sha256: uiProjectionDigest,
    elapsed_seconds: (Date.now() - startedAt) / 1000,
    timings_ms: timings,
    screenshots,
    page_errors: pageErrors,
  };
  await writeFile(
    join(output, "process_editor_operator_proof.json"),
    `${JSON.stringify(evidence, null, 2)}\n`,
    "utf8",
  );
  console.log(JSON.stringify(evidence, null, 2));
} finally {
  await otherContext?.close().catch(() => {});
  await browserContext?.close().catch(() => {});
  await browser.close().catch(() => {});
  backendProc.kill("SIGTERM");
  if (backendProc.exitCode === null)
    await new Promise((resolveWait) => backendProc.once("exit", resolveWait));
  await rm(dataRoot, { recursive: true, force: true });
  await rm(tempDir, { recursive: true, force: true });
}
