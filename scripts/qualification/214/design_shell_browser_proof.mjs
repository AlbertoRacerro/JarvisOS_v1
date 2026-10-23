#!/usr/bin/env node
// Spec 214 acceptance 2: real-Chromium walk of the Design Phase 1 shell in Lumen Light and Dark.
// Isolated data root, built frontend served by the backend, seeded only through public owners.
// Build the frontend same-origin so it talks only to this isolated backend, then run from the repo root:
//   (cd frontend && VITE_API_BASE_URL= npm run build)
//   node scripts/qualification/214/design_shell_browser_proof.mjs [evidence-dir]
import { createHash } from "node:crypto";
import { mkdir, mkdtemp, readFile, writeFile } from "node:fs/promises";
import { openSync } from "node:fs";
import { createServer } from "node:net";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import { spawn, spawnSync } from "node:child_process";
import { setTimeout as delay } from "node:timers/promises";
import { chromium } from "/home/thera/jarvis-control/work/tools/pw/node_modules/playwright/index.mjs";

const root = resolve(new URL("../../../", import.meta.url).pathname);
const backend = join(root, "backend");
const python = process.env.JARVISOS_PROOF_PYTHON ?? join(backend, ".venv/bin/python");
const port = Number(process.env.JARVISOS_PROOF_PORT ?? 8214);
const base = `http://127.0.0.1:${port}`;
const evidence = resolve(process.argv[2] ?? await mkdtemp(join(tmpdir(), "jarvisos-214-ui-")));
await mkdir(evidence, { recursive: true });
const dataRoot = await mkdtemp(join(tmpdir(), "jarvisos-214-data-"));
const env = { ...process.env, JARVISOS_DATA_ROOT: dataRoot, PYTHONPATH: backend };

const assert = (condition, message) => { if (!condition) throw new Error(message); };
// Refuse to run against any server that is not the isolated one started below.
await new Promise((ok, fail) => {
  const probe = createServer().once("error", () => fail(new Error(`port ${port} is in use; refusing to seed a foreign backend`)))
    .once("listening", () => probe.close(ok)).listen(port, "127.0.0.1");
});
const head = spawnSync("git", ["rev-parse", "HEAD"], { cwd: root, encoding: "utf8" }).stdout.trim();
const init = spawnSync(python, ["-c", "from app.core.database import initialize_database; initialize_database()"],
  { cwd: backend, env, encoding: "utf8" });
assert(init.status === 0, `isolated database initialization failed: ${init.stderr}`);
const log = openSync(join(evidence, "backend.log"), "w");
const server = spawn(python, ["-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", String(port)],
  { cwd: backend, env, stdio: ["ignore", log, log] });

async function api(path, init = {}) {
  const response = await fetch(`${base}${path}`, {
    ...init, headers: { "content-type": "application/json", ...(init.headers ?? {}) },
  });
  const body = await response.text();
  assert(response.ok, `${init.method ?? "GET"} ${path} -> ${response.status}: ${body.slice(0, 400)}`);
  return body ? JSON.parse(body) : null;
}

const summary = { spec: "214", acceptance: "2 real-browser walk", head, browser: null, started_at: new Date().toISOString(),
  data_root: "isolated temporary JARVISOS_DATA_ROOT", appearances: {}, placeholders_marked: [], limits: [
    "Selecting a PFD unit opens the existing Process inspector, which re-fits the canvas; the walk selects the unit before double-clicking it.",
    "Studio user-code execution is disabled in this isolated proof backend, so Test and Publish are shown present and refused with the runtime notice rather than executed.",
  ] };

try {
  for (let i = 0; ; i++) {
    assert(server.exitCode === null, "isolated backend exited; see backend.log");
    try { if ((await fetch(`${base}/health`)).ok) break; } catch { /* starting */ }
    assert(i < 120, "backend did not become healthy");
    await delay(500);
  }
  // Seed one project with a Process PBR unit carrying typed tube dimensions (C1 tube inner diameter,
  // one 8 m straight segment). Seeding uses the same Process draft REST owner the editor calls.
  const project = await api("/workspaces", { method: "POST", body: JSON.stringify({ name: "214 Design shell proof", slug: `design-214-${Date.now()}` }) });
  const created = await api(`/workspaces/${project.id}/process/drafts`, { method: "POST", body: JSON.stringify({ name: "Plant" }) });
  const seeded = await api(`/workspaces/${project.id}/process/drafts/${created.draft_id}/patch`, { method: "POST", body: JSON.stringify({
    expected_revision: created.revision, ops: [
      { op: "add_unit", id: "pbr", type: "PhotobioreactorT1", tag: "PBR1", x: 160, y: 120 },
      { op: "set_unit_params", unit: "pbr", values: {
        tube_inner_diameter: { value: 0.046, unit: "m" }, tube_length: { value: 8, unit: "m" } } },
    ] }) });
  summary.seed = { project_id: project.id, draft_id: created.draft_id, draft_revision: seeded.revision };

  const browser = await chromium.launch({ headless: true });
  summary.browser = `chromium ${browser.version()}`;
  for (const appearance of ["light", "dark"]) {
    const record = { screenshots: [], console_errors: [], page_errors: [], steps: [] };
    summary.appearances[appearance] = record;
    const context = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
    await context.addInitScript(([key, value]) => { try { localStorage.setItem(key, value); } catch { /* ignore */ } },
      ["jarvisos:appearance:v1", appearance]);
    const page = await context.newPage();
    page.on("console", (message) => { if (message.type() === "error") record.console_errors.push(message.text()); });
    page.on("pageerror", (error) => record.page_errors.push(String(error)));
    const shot = async (name) => {
      const file = join(evidence, `${appearance}-${String(record.screenshots.length + 1).padStart(2, "0")}-${name}.png`);
      await page.screenshot({ path: file, fullPage: true });
      record.screenshots.push({ file: file.slice(evidence.length + 1), sha256: createHash("sha256").update(await readFile(file)).digest("hex") });
    };
    const step = (name, detail = {}) => record.steps.push({ step: name, ...detail });

    page.on("request", (request) => { if (!request.url().startsWith(base) && !request.url().startsWith("data:") && !request.url().startsWith("blob:")) record.foreign_requests = [...(record.foreign_requests ?? []), request.url()]; });
    await page.goto(`${base}/design/project`, { waitUntil: "networkidle" });
    assert(await page.evaluate(() => document.documentElement.dataset.theme) === appearance, `Lumen ${appearance} not applied`);
    await page.getByRole("heading", { name: "214 Design shell proof" }).waitFor();
    const version = page.getByLabel("Project version");
    step("project_version_visible", { version: await version.locator("option:checked").textContent() });
    const unit = page.getByTestId("node-PBR1");
    await unit.waitFor();
    await shot("plant-flowsheet");
    // The existing Process editor opens its setup drawer over the canvas while species are unset.
    const closeSetup = page.getByRole("button", { name: "Close setup", exact: true }).filter({ hasText: "Close setup" });
    if (await closeSetup.isVisible()) { await closeSetup.click(); step("process_setup_drawer_closed"); }

    // PFD entry: keyboard in light, double-click in dark; both proven across the two appearances.
    if (appearance === "light") { await unit.focus(); await page.keyboard.press("Enter"); }
    else { await unit.click(); await page.waitForTimeout(300); await unit.dblclick(); }
    await page.getByRole("heading", { level: 2, name: /PBR1/ }).waitFor();
    step("pfd_unit_opened", { via: appearance === "light" ? "keyboard Enter" : "double-click" });
    const tree = page.getByRole("group", { name: "Component model tree" }).or(page.locator("[aria-label='Component model tree']"));
    await tree.first().waitFor();
    await page.getByRole("button", { name: "Parameters", exact: true }).click();
    await page.getByText("tube_inner_diameter").waitFor();
    step("component_parameters_from_process", { text: (await page.locator("section[aria-label='Parameters details']").innerText()).slice(0, 300) });
    await shot("component-parameters");

    await page.getByRole("button", { name: "Geometry", exact: true }).click();
    assert(await page.getByRole("navigation", { name: "Design stages" }).getByRole("button", { name: "CAD" }).getAttribute("aria-current") === "step", "Geometry node did not focus CAD stage");
    await page.getByText(/Deepen from Process: PhotobioreactorT1 → BlueCad tube/).waitFor();
    step("tree_jump_geometry_focuses_cad");
    await shot("component-geometry-deepen");

    const stages = page.getByRole("navigation", { name: "Design stages" });
    await stages.getByRole("button", { name: "Motion/Mechanics" }).click();
    await page.getByText("Motion/Mechanics is a navigation placeholder in this Phase 1 checkpoint.").waitFor();
    if (appearance === "light") summary.placeholders_marked.push("Motion/Mechanics");
    await stages.getByRole("button", { name: "Optics" }).click();
    assert(await page.getByRole("button", { name: "Physics", exact: true }).getAttribute("aria-pressed") === "true", "Optics stage did not focus Physics node");
    await page.getByText("Optics is a navigation placeholder in this Phase 1 checkpoint.").waitFor();
    if (appearance === "light") summary.placeholders_marked.push("Optics");
    step("stage_jumps", { motion: "placeholder labelled", optics: "focuses Physics node, placeholder labelled" });
    await shot("stage-placeholder");

    await stages.getByRole("button", { name: "Plant" }).click();
    await page.getByTestId("node-PBR1").waitFor();
    step("plant_return_same_version", { version: await version.locator("option:checked").textContent() });

    await page.getByRole("button", { name: "Generate new in Workshop" }).click();
    const workshop = page.getByRole("region", { name: "Workshop" });
    await workshop.getByText("Guided initialization · step 1 of 7").waitFor();
    await shot("workshop-step1");
    const next = () => workshop.getByRole("button", { name: "Next" }).click();
    await workshop.getByRole("button", { name: "Custom · no preset" }).click();
    await next();
    await workshop.getByLabel("Model name").fill(`Tube hold-up ${appearance}`);
    await workshop.getByLabel("Engineering question").fill("What liquid volume does one straight tube hold?");
    await next();
    await workshop.getByLabel("What approach should the model use?").fill("Cylinder volume pi*d^2*L/4.");
    await next();
    // Custom calculation: one input and one output with units.
    const variable = async (legend, name, label, unit, description) => {
      const set = workshop.locator("fieldset.studio-variables", { has: page.locator("legend", { hasText: legend }) });
      await set.getByLabel("Python name", { exact: true }).first().fill(name);
      await set.getByLabel("Label", { exact: true }).first().fill(label);
      await set.getByLabel("Unit", { exact: true }).first().fill(unit);
      if (description) await set.getByLabel("Description", { exact: true }).first().fill(description);
    };
    await variable("Inputs", "d", "Tube inner diameter", "meter", "");
    await variable("Outputs", "area", "Liquid cross-section", "meter**2", "");
    // The Studio contract requires a description for every variable; guided Next must wait for it.
    assert(await workshop.getByRole("button", { name: "Next" }).isDisabled(), "Next enabled without required descriptions");
    await variable("Inputs", "d", "Tube inner diameter", "meter", "Inner diameter of one straight tube.");
    await variable("Outputs", "area", "Liquid cross-section", "meter**2", "Liquid volume per metre of tube.");
    assert(await workshop.getByRole("button", { name: "Next" }).isEnabled(), "typed fields with descriptions did not enable Next");
    await shot("workshop-fields");
    await next();
    await workshop.getByLabel("What assumptions bound this model?").fill("Straight circular tube, inner diameter only.");
    await next();
    await workshop.getByLabel("How should it be tested?").fill("d = 0.046 m gives 1.662e-3 m2 per metre.");
    await next();
    await workshop.getByRole("region", { name: "Guided contract review" }).or(workshop.locator("section[aria-label='Guided contract review']")).first().waitFor();
    await shot("workshop-review");
    step("workshop_guided_seven_steps");
    await workshop.getByRole("button", { name: "Create draft and Python scaffold" }).click();
    const saveDraft = workshop.getByRole("button", { name: "Save Draft" });
    await saveDraft.waitFor({ timeout: 60_000 });
    await page.waitForLoadState("networkidle");
    await shot("workshop-two-column-editor");
    const publish = workshop.getByRole("button", { name: "Publish", exact: true });
    record.editor_controls = { save_draft_present: true, publish_present: await publish.count() > 0,
      publish_enabled: await publish.count() > 0 ? await publish.isEnabled() : false,
      runtime_notice: await workshop.locator(".studio-warning[role='status']").first().textContent().catch(() => null) };
    step("workshop_full_editor_with_existing_test_publish_path", record.editor_controls);
    await workshop.getByRole("button", { name: "Back to Design" }).click();
    await page.getByRole("button", { name: "Generate new in Workshop" }).waitFor();

    // Explicit old/new Design switch.
    await page.getByRole("link", { name: "Open old Design" }).click();
    await page.waitForURL(/\/design\/bluecad$/);
    await page.waitForLoadState("networkidle");
    await shot("old-design");
    await page.getByRole("link", { name: "New Design" }).click();
    await page.waitForURL(/\/design\/project$/);
    await page.getByRole("heading", { name: "214 Design shell proof" }).waitFor();
    step("old_new_design_switch", { old: "/design/bluecad", back: "/design/project" });
    await context.close();
  }
  await browser.close();
} finally {
  server.kill("SIGTERM");
  summary.finished_at = new Date().toISOString();
  await writeFile(join(evidence, "summary.json"), `${JSON.stringify(summary, null, 2)}\n`);
  console.log(JSON.stringify({ evidence, summary }, null, 2));
}
