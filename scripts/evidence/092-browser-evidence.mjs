import { chromium } from "playwright";
import fs from "node:fs/promises";
import path from "node:path";

const PRODUCT_HEAD = "858b49777500d3137435321a85a63ed863691c1c";
const BASE_URL = "http://127.0.0.1:4173/design/model";
const API = "http://127.0.0.1:8000";
const SHA = "a".repeat(64);
const KEY_A = `bluecad-part-sha256-${"1".repeat(64)}`;
const KEY_B = `bluecad-part-sha256-${"2".repeat(64)}`;
const KEY_H = `bluecad-part-sha256-${"3".repeat(64)}`;
const longPartId = `PART-<script>alert(1)</script>-${"X".repeat(520)}`;

const tri = new Float32Array([
  -1, 0, 0, 0, 1, 0, 1, 0, 0,
  -1, 0, 0, 0, -1, 0, 1, 0, 0
]);
const triBytes = Buffer.from(tri.buffer);
const gltf = JSON.stringify({
  asset: { version: "2.0" },
  buffers: [{ uri: `data:application/octet-stream;base64,${triBytes.toString("base64")}`, byteLength: triBytes.length }],
  bufferViews: [
    { buffer: 0, byteOffset: 0, byteLength: 36 },
    { buffer: 0, byteOffset: 36, byteLength: 36 }
  ],
  accessors: [
    { bufferView: 0, componentType: 5126, count: 3, type: "VEC3", min: [-1, 0, 0], max: [1, 1, 0] },
    { bufferView: 1, componentType: 5126, count: 3, type: "VEC3", min: [-1, -1, 0], max: [1, 0, 0] }
  ],
  meshes: [
    { name: "Same display label", primitives: [{ attributes: { POSITION: 0 } }] },
    { name: "Same display label", primitives: [{ attributes: { POSITION: 1 } }] }
  ],
  nodes: [
    { name: "root", children: [1, 3] },
    { name: KEY_A, children: [2] },
    { name: "Same display label", mesh: 0, translation: [-2, 0, 0] },
    { name: KEY_B, children: [4] },
    { name: "Same display label", mesh: 1, translation: [2, 0, 0] }
  ],
  scenes: [{ nodes: [0] }],
  scene: 0
});

const now = "2026-08-20T00:00:00Z";
const workspace = { id: "ws-1", name: "Evidence workspace", slug: "evidence", description: null, status: "active", created_at: now, updated_at: now };
function candidate(id, brief, glbId = `${id}-glb`) {
  return {
    id, workspace_id: workspace.id, brief_text: brief, brief_digest: "d".repeat(64), status: "valid",
    parked_reason: null, spec_artifact_id: null, glb_artifact_id: glbId, report_artifact_id: null,
    promoted_decision_id: null, origin: "evidence", parent_candidate_id: null, loop_config_json: "{}",
    created_at: now, updated_at: now, notes: null, attempts: [{
      id: `${id}-attempt`, candidate_id: id, attempt_no: 1, route_class: "local", proposal_outcome: "success",
      build_outcome: "success", validation_verdict: "pass", manifest_artifact_id: `${id}-manifest`, started_at: now, finished_at: now
    }]
  };
}
const candidates = [
  candidate("bound", "Candidate bound"),
  candidate("switch", "Candidate switch"),
  candidate("historical", "Candidate historical"),
  candidate("malformed", "Candidate malformed"),
  candidate("viewerfail", "Candidate viewer failure"),
  candidate("hostile", "Candidate hostile")
];
function manifestFor(id) {
  if (id === "historical") return { spec_id: "spec-historical", parts: { "PART-A": { kind: "tube" }, "PART-B": { kind: "tube" } }, artifacts: { "model.glb": { sha256: SHA } } };
  if (id === "malformed") return {
    spec_id: "spec-malformed", parts: { "PART-A": { kind: "tube" }, "PART-B": { kind: "tube" } }, artifacts: { "model.glb": { sha256: SHA } },
    scene_binding: { version: "bluecad_scene_binding_v0_1", artifact: "model.glb", spec_id: "spec-malformed", objects: { [KEY_A]: { part_id: "PART-A" }, [KEY_B]: { part_id: "PART-A" } } }
  };
  if (id === "hostile") return {
    spec_id: "spec-hostile", parts: { [longPartId]: { kind: `tube-${"Y".repeat(420)}` }, "PART-B": { kind: "tube" } }, artifacts: { "model.glb": { sha256: SHA } },
    scene_binding: { version: "bluecad_scene_binding_v0_1", artifact: "model.glb", spec_id: "spec-hostile", objects: { [KEY_A]: { part_id: longPartId }, [KEY_B]: { part_id: "PART-B" } } }
  };
  const suffix = id === "switch" ? "S" : "";
  return {
    spec_id: `spec-${id}`,
    parts: { [`PART-A${suffix}`]: { kind: "tube" }, [`PART-B${suffix}`]: { kind: "tube" } },
    artifacts: { "model.glb": { sha256: SHA } },
    scene_binding: {
      version: "bluecad_scene_binding_v0_1", artifact: "model.glb", spec_id: `spec-${id}`,
      objects: { [KEY_A]: { part_id: `PART-A${suffix}` }, [KEY_B]: { part_id: `PART-B${suffix}` } }
    }
  };
}
function aggregate(id) {
  const c = candidates.find((item) => item.id === id);
  return {
    candidate: c,
    artifacts: [
      { id: `${id}-glb`, roles: ["candidate.glb_artifact_id"], filename: "model.glb", mime_type: "model/gltf-binary", sha256: SHA, status: "ready", source_ref: null, created_at: now, content_url: `/workspaces/ws-1/bluecad/artifacts/${id}-glb/content` },
      { id: `${id}-manifest`, roles: ["attempt.manifest_artifact_id"], filename: "manifest.json", mime_type: "application/json", sha256: "b".repeat(64), status: "ready", source_ref: null, created_at: now, content_url: `/workspaces/ws-1/bluecad/artifacts/${id}-manifest/content` }
    ],
    evidence: [], runs: [], freshness: "fresh", diagnostics: []
  };
}

const results = [];
let mutationRequests = [];
let providerRequests = [];
let delayNextManifestMs = 0;
function record(name, pass, detail = "") { results.push({ case: name, pass, detail }); }
async function expectCase(name, fn) {
  try { await fn(); record(name, true); }
  catch (error) { record(name, false, error instanceof Error ? error.message : String(error)); }
}
function assert(value, message) { if (!value) throw new Error(message); }
async function semanticText(page) {
  const locator = page.locator('#shell-sidecar-pane-properties .shell-properties__selection').first();
  return (await locator.count()) ? (await locator.textContent()) ?? "" : "";
}
async function choose(page, label) {
  const button = page.getByRole("button", { name: new RegExp(label) });
  await button.click();
  await page.getByText("Orbit, pan, zoom, or click a mesh to inspect visible geometry.").waitFor({ timeout: 10000 });
  await page.getByRole("button", { name: /Show context|Hide context/ }).click().catch(() => {});
  const context = page.getByRole("button", { name: "Show context" });
  if (await context.count()) await context.click();
  await page.getByRole("tab", { name: "Properties" }).click();
  await page.getByLabel("Inspectable mesh").waitFor({ timeout: 10000 });
}
async function selectMesh(page, value) {
  await page.getByLabel("Inspectable mesh").selectOption(value);
}

await fs.mkdir(path.join("reports", "092-browser-evidence"), { recursive: true });
const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({ viewport: { width: 1440, height: 1000 }, reducedMotion: "no-preference" });
const page = await context.newPage();
page.on("request", (request) => {
  const url = request.url();
  if (["POST", "PUT", "PATCH", "DELETE"].includes(request.method())) mutationRequests.push(`${request.method()} ${url}`);
  if (url.includes("/ai/") || url.includes("provider")) providerRequests.push(`${request.method()} ${url}`);
});
await page.route(`${API}/**`, async (route) => {
  const req = route.request();
  const url = new URL(req.url());
  const p = url.pathname;
  const json = (value, status = 200) => route.fulfill({ status, contentType: "application/json", body: JSON.stringify(value) });
  if (req.method() !== "GET") return json({ error: "mutation forbidden in evidence" }, 409);
  if (p === "/workspaces") return json([workspace]);
  if (p === "/workspaces/ws-1/bluecad/candidates") return json(candidates);
  const agg = p.match(/^\/workspaces\/ws-1\/bluecad\/candidates\/([^/]+)\/aggregate$/);
  if (agg) return json(aggregate(decodeURIComponent(agg[1])));
  const artifact = p.match(/^\/workspaces\/ws-1\/bluecad\/artifacts\/([^/]+)\/content$/);
  if (artifact) {
    const id = decodeURIComponent(artifact[1]);
    if (id.endsWith("-glb")) {
      if (id.startsWith("viewerfail-")) return route.fulfill({ status: 500, contentType: "text/plain", body: "forced viewer failure" });
      return route.fulfill({ status: 200, contentType: "model/gltf+json", body: gltf });
    }
    if (id.endsWith("-manifest")) {
      if (delayNextManifestMs > 0) { const d = delayNextManifestMs; delayNextManifestMs = 0; await new Promise((r) => setTimeout(r, d)); }
      return json(manifestFor(id.replace(/-manifest$/, "")));
    }
  }
  if (/\/model-implementations$/.test(p) || /\/parameters$/.test(p) || /\/ai\/threads/.test(p)) return json([]);
  if (p === "/ai/status") return json({ ai_enabled: false, provider_mode: "fake", external_calls_allowed: false, default_ai_provider: "fake", default_ai_model: "fake" });
  return json([]);
});

await page.goto(BASE_URL);
await page.getByRole("heading", { name: "Model workbench" }).waitFor();
await page.getByRole("button", { name: "Show navigator" }).click();

await expectCase("01 distinct similar parts resolve to distinct semantic targets", async () => {
  await choose(page, "Candidate bound");
  await selectMesh(page, "mesh-1");
  await page.getByText("PART-A", { exact: true }).first().waitFor();
  const a = await semanticText(page);
  await selectMesh(page, "mesh-2");
  await page.getByText("PART-B", { exact: true }).first().waitFor();
  const b = await semanticText(page);
  assert(a.includes("PART-A") && b.includes("PART-B") && a !== b, "semantic targets did not remain distinct");
});

await expectCase("02 clear hit restores neutral candidate state", async () => {
  await selectMesh(page, "");
  await page.waitForTimeout(100);
  const text = await semanticText(page);
  assert(!text.includes("PART-A") && !text.includes("PART-B"), "semantic part remained after clear");
});

await expectCase("03 candidate switch clears prior semantic target before new artifact", async () => {
  await choose(page, "Candidate bound");
  await selectMesh(page, "mesh-1");
  await page.getByText("PART-A", { exact: true }).first().waitFor();
  await page.getByRole("button", { name: /Candidate switch/ }).click();
  await page.waitForTimeout(50);
  const text = await semanticText(page);
  assert(!text.includes("PART-A"), "old semantic target survived candidate switch");
});

await expectCase("04 delayed A resolution cannot overwrite newer B", async () => {
  await choose(page, "Candidate bound");
  delayNextManifestMs = 700;
  await selectMesh(page, "mesh-1");
  await page.waitForTimeout(60);
  await selectMesh(page, "mesh-2");
  await page.getByText("PART-B", { exact: true }).first().waitFor({ timeout: 5000 });
  await page.waitForTimeout(800);
  const text = await semanticText(page);
  assert(text.includes("PART-B") && !text.includes("PART-A"), "late A resolution replaced B");
});

await expectCase("05 historical missing binding stays viewable and explicitly unresolved", async () => {
  await choose(page, "Candidate historical");
  await selectMesh(page, "mesh-1");
  await page.waitForTimeout(250);
  const body = (await page.locator("body").textContent()) ?? "";
  assert(body.includes("Unresolved engineering binding"), "historical unbound hit lacks explicit unresolved engineering-binding state");
});

await expectCase("06 malformed duplicate binding fails closed without crash and is explicit", async () => {
  await choose(page, "Candidate malformed");
  await selectMesh(page, "mesh-1");
  await page.waitForTimeout(250);
  const body = (await page.locator("body").textContent()) ?? "";
  assert(!body.includes("PART-A · tube · selected BLUECAD part"), "malformed binding was promoted");
  assert(body.includes("Unresolved engineering binding") || body.includes("Ambiguous engineering binding"), "malformed binding failure is not explicit to operator");
});

await expectCase("07 duplicate display labels do not alias semantic identity", async () => {
  await choose(page, "Candidate bound");
  const options = await page.getByLabel("Inspectable mesh").locator("option").allTextContents();
  assert(options.filter((x) => x === "Same display label").length === 2, "fixture did not contain duplicate display labels");
  await selectMesh(page, "mesh-1");
  const first = await semanticText(page);
  await selectMesh(page, "mesh-2");
  const second = await semanticText(page);
  assert(first.includes("PART-A") && second.includes("PART-B"), "duplicate display label aliased identity");
});

await expectCase("08 viewer load failure clears semantic target", async () => {
  await choose(page, "Candidate bound");
  await selectMesh(page, "mesh-1");
  await page.getByText("PART-A", { exact: true }).first().waitFor();
  await page.getByRole("button", { name: /Candidate viewer failure/ }).click();
  await page.getByText("Unable to load this GLB artifact.").waitFor({ timeout: 10000 });
  const text = await semanticText(page);
  assert(!text.includes("PART-A"), "semantic target survived viewer failure");
});

await expectCase("09 hostile long machine/human tokens are inert and do not create page overflow", async () => {
  await choose(page, "Candidate hostile");
  await selectMesh(page, "mesh-1");
  await page.getByText(longPartId, { exact: true }).first().waitFor();
  const scripts = await page.locator("script").count();
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
  assert(scripts >= 1, "document script baseline unexpectedly absent");
  assert(overflow <= 1, `page horizontal overflow ${overflow}px`);
  const literal = await semanticText(page);
  assert(literal.includes("<script>alert(1)</script>"), "hostile token did not render inertly as text");
});

await expectCase("10 keyboard reaches inspection selector and clears with visible focus", async () => {
  await choose(page, "Candidate bound");
  const select = page.getByLabel("Inspectable mesh");
  await select.focus();
  assert(await select.evaluate((el) => el === document.activeElement), "inspection select did not receive focus");
  await select.selectOption("mesh-1");
  const clear = page.getByRole("button", { name: "Clear inspection" });
  await clear.focus();
  assert(await clear.evaluate((el) => el === document.activeElement), "clear button did not receive focus");
  await clear.press("Enter");
  await page.waitForTimeout(100);
  const text = await semanticText(page);
  assert(!text.includes("PART-A"), "keyboard clear did not clear semantic selection");
});

await expectCase("11 compact Jarvis/Properties tab switching preserves semantic target", async () => {
  await choose(page, "Candidate bound");
  await selectMesh(page, "mesh-2");
  await page.getByText("PART-B", { exact: true }).first().waitFor();
  await page.setViewportSize({ width: 650, height: 900 });
  await page.getByRole("tab", { name: "Jarvis" }).click();
  await page.getByRole("tab", { name: "Properties" }).click();
  const text = await semanticText(page);
  assert(text.includes("PART-B"), "semantic target changed/remounted across compact tab switching");
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
  assert(overflow <= 1, `compact page horizontal overflow ${overflow}px`);
  await page.setViewportSize({ width: 1440, height: 1000 });
});

await expectCase("12 light/dark/system and reduced-motion invariants remain intact", async () => {
  const appearance = page.getByLabel("Appearance preference");
  await appearance.selectOption("light");
  assert(await page.evaluate(() => document.documentElement.dataset.theme) === "light", "light appearance not applied");
  await appearance.selectOption("dark");
  assert(await page.evaluate(() => document.documentElement.dataset.theme) === "dark", "dark appearance not applied");
  await appearance.selectOption("system");
  assert(["light", "dark"].includes(await page.evaluate(() => document.documentElement.dataset.theme)), "system appearance unresolved");
  await page.emulateMedia({ reducedMotion: "reduce" });
  assert((await semanticText(page)).includes("PART-B"), "reduced-motion media change disturbed semantic target");
});

await expectCase("13 selection causes zero run/canonical/working/provider mutation", async () => {
  mutationRequests = [];
  providerRequests = [];
  await choose(page, "Candidate bound");
  await selectMesh(page, "mesh-1");
  await page.getByText("PART-A", { exact: true }).first().waitFor();
  await selectMesh(page, "mesh-2");
  await page.getByText("PART-B", { exact: true }).first().waitFor();
  await selectMesh(page, "");
  await page.waitForTimeout(150);
  assert(mutationRequests.length === 0, `selection emitted mutation requests: ${mutationRequests.join(", ")}`);
  assert(providerRequests.length === 0, `selection emitted provider requests: ${providerRequests.join(", ")}`);
});

await page.screenshot({ path: "reports/092-browser-evidence/final.png", fullPage: true });
await browser.close();
const payload = { product_head: PRODUCT_HEAD, generated_at: new Date().toISOString(), results, passed: results.every((r) => r.pass) };
await fs.writeFile("reports/092-browser-evidence.json", JSON.stringify(payload, null, 2));
console.log(JSON.stringify(payload, null, 2));
if (!payload.passed) process.exit(1);
