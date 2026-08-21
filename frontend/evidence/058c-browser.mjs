import { chromium } from "playwright";
import assert from "node:assert/strict";

const variables = [
  ["tube_length", "Tube length", "m", "design", "Geometry", ["tube_run"]],
  ["tube_inner_diameter", "Tube inner diameter", "mm", "design", "Geometry", ["tube_run"]],
  ["tube_outer_diameter", "Tube outer diameter", "mm", "design", "Geometry", ["tube_run"]],
  ["reservoir_liquid_volume", "Reservoir liquid volume", "L", "design", "Model configuration", []],
  ["target_liquid_velocity", "Target liquid velocity", "m/s", "operating", "Operating", []],
  ["liquid_density", "Liquid density", "kg/m3", "property", "Properties", []],
  ["dynamic_viscosity", "Dynamic viscosity", "Pa*s", "property", "Properties", []],
  ["minor_loss_coefficient", "Minor loss coefficient", "1", "model_parameter", "Model configuration", []],
  ["pump_efficiency", "Pump efficiency", "1", "equipment", "Equipment", []]
].map(([name, label, unit, category, property_group, applicable_part_kinds]) => ({
  name, label, unit, required: true, category, property_group, applicable_part_kinds,
  description: `${label} evidence field.`
}));

const implementation = {
  id: "model-semantic-v3",
  workspace_id: "ws1",
  model_spec_id: "spec-047",
  version_label: "bluerev-geometry-hydraulics-semantic-v0-bundled",
  implementation_artifact_id: "artifact-script",
  status: "accepted",
  script_sha256: "a".repeat(64),
  script_path: "reviewed-047.py",
  created_at: "2026-08-21T00:00:00Z",
  input_contract_sha256: "b".repeat(64),
  input_contract: {
    schema_version: 3,
    evaluation_mode: "forward",
    semantic_context: {
      applicable_part_kinds: ["tube_run"],
      model_family_key: "geometry_hydraulics",
      model_family_label: "Geometry and hydraulics model",
      model_option_label: "Reviewed 047 tubular-loop V0"
    },
    variables
  }
};

const parameters = [
  ["p-length", "Tube length", "12", "m"],
  ["p-inner", "Tube inner diameter", "80", "mm"],
  ["p-outer", "Tube outer diameter", "90", "mm"],
  ["p-reservoir", "Reservoir volume", "100", "L"],
  ["p-velocity", "Target velocity", "1.2", "m/s"],
  ["p-density", "Liquid density", "998", "kg/m3"],
  ["p-viscosity", "Dynamic viscosity", "0.001", "Pa*s"],
  ["p-minor", "Minor loss", "2", "1"],
  ["p-eff", "Pump efficiency", "0.75", "1"]
].map(([id, name, value, unit]) => ({ id, workspace_id: "ws1", name, value, unit, status: "accepted" }));

function candidateAggregate(id, length, inner, outer) {
  return {
    candidate: { id, workspace_id: "ws1", status: "built", origin: "evidence", attempts: [] },
    artifacts: [], evidence: [], runs: [], freshness: "fresh", diagnostics: [],
    semantic_source: {
      schema_version: 1,
      kind: "cad_link_047_m0",
      transformation_version: "bluerev_047_m0_tube_proxy_v0_1",
      source_simulation_run_id: `run-${id}`,
      source_model_version_id: "model-semantic-v3",
      geometry_bindings: {
        tube_length: { value: length, unit: "m", source_parameter_id: "p-length" },
        tube_inner_diameter: { value: inner, unit: "mm", source_parameter_id: "p-inner" },
        tube_outer_diameter: { value: outer, unit: "mm", source_parameter_id: "p-outer" }
      }
    }
  };
}

let delayA = false;
let providerCalls = 0;
const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({ viewport: { width: 1280, height: 900 }, colorScheme: "light" });
const page = await context.newPage();

await page.route("http://127.0.0.1:8000/**", async (route) => {
  const request = route.request();
  const url = new URL(request.url());
  if (url.pathname.includes("/ai/")) providerCalls += 1;
  const json = (body, status = 200) => route.fulfill({ status, contentType: "application/json", headers: { "Access-Control-Allow-Origin": "*" }, body: JSON.stringify(body) });

  if (request.method() === "GET" && url.pathname === "/workspaces") return json([{ id: "ws1", name: "Evidence workspace", slug: "evidence", status: "active", created_at: "2026-08-21T00:00:00Z", updated_at: "2026-08-21T00:00:00Z" }]);
  if (request.method() === "GET" && url.pathname === "/workspaces/ws1/model-implementations") return json([implementation]);
  if (request.method() === "GET" && url.pathname === "/workspaces/ws1/parameters") return json(parameters);
  if (request.method() === "GET" && url.pathname === "/workspaces/ws1/model-specs") return json([]);
  if (request.method() === "GET" && url.pathname === "/workspaces/ws1/assumptions") return json([]);
  if (request.method() === "GET" && url.pathname === "/workspaces/ws1/decisions") return json([]);
  if (request.method() === "GET" && url.pathname.endsWith("/bluecad/candidates/cand-a/aggregate")) {
    if (delayA) await new Promise((resolve) => setTimeout(resolve, 650));
    return json(candidateAggregate("cand-a", 12, 80, 90));
  }
  if (request.method() === "GET" && url.pathname.endsWith("/bluecad/candidates/cand-b/aggregate")) return json(candidateAggregate("cand-b", 20, 100, 112));
  if (request.method() === "POST" && url.pathname.includes("/binding-preview")) {
    const payload = request.postDataJSON()?.bindings ?? {};
    const rows = variables.map((v) => ({ ...v, binding_state: payload[v.name] ? "manual" : "missing", value: payload[v.name]?.value ?? null, source_parameter_id: payload[v.name]?.source_parameter_id ?? null, errors: [] }));
    const missing = rows.filter((v) => v.required && v.binding_state === "missing").length;
    return json({
      model_version_id: "model-semantic-v3", contract_sha256: "b".repeat(64), evaluation_mode: "forward",
      structural_input_dof: 9, bound_input_dof: 9 - missing, unresolved_input_dof: missing, invalid_binding_count: 0,
      state: missing ? "incomplete" : "ready", variables: rows, errors: [], normalized_input_set: missing ? null : payload
    });
  }
  if (request.method() === "POST" && url.pathname === "/workspaces/ws1/runner-jobs") return json({ runner_job: { id: "job-evidence", status: "queued" }, simulation_run: { id: "run-evidence", workspace_id: "ws1", status: "queued", created_at: "2026-08-21T00:00:00Z" } });
  if (request.method() === "POST" && url.pathname === "/runner-jobs/job-evidence/run") return json({ runner_job: { id: "job-evidence", status: "succeeded" }, simulation_run: { id: "run-evidence", workspace_id: "ws1", status: "succeeded", created_at: "2026-08-21T00:00:00Z" }, output: {}, error: null });
  return json({ detail: `Unhandled evidence route ${request.method()} ${url.pathname}` }, 404);
});

const gotoHarness = async () => {
  await page.goto("http://127.0.0.1:4173/058c-evidence.html");
  await page.locator("#engineering-property-tube_length").waitFor();
  await page.waitForFunction(() => document.querySelector("#engineering-property-tube_length")?.value === "12");
};

await gotoHarness();
assert.equal(await page.locator("#engineering-property-tube_length").inputValue(), "12", "exact reviewed object adopts immutable CAD-link snapshot");
assert.equal(await page.getByRole("heading", { name: "Geometry" }).count(), 1, "selected-object Geometry group is visible");
assert.equal(await page.getByText("Model configuration", { exact: true }).count() > 0, true, "generic model configuration remains reachable");

await page.locator("#engineering-property-tube_length").fill("13");
await page.getByRole("button", { name: "A new viewer session" }).click();
await page.waitForTimeout(250);
assert.equal(await page.locator("#engineering-property-tube_length").inputValue(), "13", "same engineering target/new viewer session preserves dirty draft");
assert.equal(await page.getByText(/Unsaved object changes belong/).count(), 0, "same target does not enter conflict");

await page.getByRole("button", { name: "Select B" }).click();
await page.getByText(/Unsaved object changes belong to the previous engineering target/).waitFor();
assert.equal(await page.locator("#engineering-property-tube_length").inputValue(), "13", "dirty A draft is not rebased onto B");
await page.getByRole("button", { name: "Discard previous object changes and load selected object" }).click();
await page.waitForFunction(() => document.querySelector("#engineering-property-tube_length")?.value === "20");
assert.equal(await page.locator("#engineering-property-tube_length").inputValue(), "20", "explicit discard adopts B baseline");

await page.getByRole("button", { name: "Non-matching part" }).click();
await page.getByText(/No reviewed object-specific model semantics/).waitFor();
for (const [name] of variables) await page.locator(`#engineering-property-${name}`).fill(name === "pump_efficiency" ? "0.75" : "1");
await page.getByText("Ready", { exact: true }).waitFor();
await page.getByLabel("Run label").fill("generic-v3-evidence");
assert.equal(await page.getByRole("button", { name: "Run", exact: true }).isEnabled(), true, "non-matching v3 part retains generic 071b Run usability");

// A delayed stale candidate response must not overwrite the newer B target.
delayA = true;
await page.getByRole("button", { name: "Select A" }).click();
await page.waitForTimeout(50);
await page.getByRole("button", { name: "Select B" }).click();
await page.waitForTimeout(900);
assert.match(await page.getByTestId("selection-state").textContent(), /^cand-b:/, "newer selection remains current after stale A response");
assert.equal(await page.locator("#engineering-property-tube_length").inputValue(), "20", "stale A aggregate does not rebase current B geometry");
delayA = false;

// Exact linked source navigation must target the canonical Parameter id.
await page.getByRole("button", { name: "Select A" }).click();
await page.waitForFunction(() => document.querySelector("#engineering-property-tube_length")?.value === "12");
const firstInspect = page.locator("details.shell-properties__inspect").first();
await firstInspect.locator("summary").click();
const openSource = firstInspect.getByRole("button", { name: "Open source" });
await openSource.focus();
assert.equal(await openSource.evaluate((el) => el === document.activeElement), true, "Open source is keyboard focusable");
await openSource.press("Enter");
await page.getByRole("heading", { name: "Engineering Data" }).waitFor();
await page.getByRole("heading", { name: "Tube length" }).waitFor();
assert.match(page.url(), /kind=parameter&id=p-length/, "Open source deep-link uses exact canonical Parameter id");

// Missing deep-link fails truthfully in current workspace.
await page.goto("http://127.0.0.1:4173/engineering-data?kind=parameter&id=missing-source");
await page.getByText(/Linked source unavailable/).waitFor();

// Compact/effective-200%-like width must remain contained; themes stay usable.
await gotoHarness();
await page.setViewportSize({ width: 640, height: 900 });
await page.waitForTimeout(150);
const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
assert.ok(overflow <= 1, `compact viewport has no page-level horizontal overflow (delta=${overflow})`);
await page.getByRole("button", { name: "Dark" }).click();
assert.equal(await page.evaluate(() => document.documentElement.dataset.theme), "dark");
await page.getByRole("button", { name: "Light" }).click();
assert.equal(await page.evaluate(() => document.documentElement.dataset.theme), "light");
await page.getByRole("button", { name: "System" }).click();
assert.ok(["light", "dark"].includes(await page.evaluate(() => document.documentElement.dataset.theme ?? "")));

assert.equal(providerCalls, 0, "semantic selection/edit/navigation causes zero AI provider calls");
console.log("058c_BROWSER_EVIDENCE_PASS");
await browser.close();
