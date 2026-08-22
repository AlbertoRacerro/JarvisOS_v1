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

function implementation(workspaceId) {
  return {
    id: `model-semantic-v3-${workspaceId}`,
    workspace_id: workspaceId,
    model_spec_id: "spec-047",
    version_label: "bluerev-geometry-hydraulics-semantic-v0-bundled",
    implementation_artifact_id: "artifact-script",
    status: "accepted",
    script_sha256: "a".repeat(64),
    script_path: "reviewed-047.py",
    created_at: "2026-08-22T00:00:00Z",
    input_contract_sha256: workspaceId === "ws1" ? "b".repeat(64) : "c".repeat(64),
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
}

function parameters(workspaceId) {
  const prefix = workspaceId === "ws1" ? "" : "2-";
  return [
    ["p-length", "Tube length", "12", "m"],
    ["p-inner", "Tube inner diameter", "80", "mm"],
    ["p-outer", "Tube outer diameter", "90", "mm"],
    ["p-reservoir", "Reservoir volume", "100", "L"],
    ["p-velocity", "Target velocity", "1.2", "m/s"],
    ["p-density", "Liquid density", "998", "kg/m3"],
    ["p-viscosity", "Dynamic viscosity", "0.001", "Pa*s"],
    ["p-minor", "Minor loss", "2", "1"],
    ["p-eff", "Pump efficiency", "0.75", "1"]
  ].map(([id, name, value, unit]) => ({ id: `${prefix}${id}`, workspace_id: workspaceId, name, value, unit, status: "accepted" }));
}

function candidateAggregate(workspaceId, id, length, inner, outer) {
  const prefix = workspaceId === "ws1" ? "" : "2-";
  return {
    candidate: { id, workspace_id: workspaceId, status: "built", origin: "evidence", attempts: [] },
    artifacts: [], evidence: [], runs: [], freshness: "fresh", diagnostics: [],
    semantic_source: {
      schema_version: 1,
      kind: "cad_link_047_m0",
      transformation_version: "bluerev_047_m0_tube_proxy_v0_1",
      source_simulation_run_id: `run-${id}`,
      source_model_version_id: `model-semantic-v3-${workspaceId}`,
      geometry_bindings: {
        tube_length: { value: length, unit: "m", source_parameter_id: `${prefix}p-length` },
        tube_inner_diameter: { value: inner, unit: "mm", source_parameter_id: `${prefix}p-inner` },
        tube_outer_diameter: { value: outer, unit: "mm", source_parameter_id: `${prefix}p-outer` }
      }
    }
  };
}

let providerCalls = 0;
let runnerCreateCalls = 0;
let runnerRunCalls = 0;
let previewCalls = 0;

const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({ viewport: { width: 1280, height: 900 }, colorScheme: "light" });
const page = await context.newPage();

await page.route("http://127.0.0.1:8000/**", async (route) => {
  const request = route.request();
  const url = new URL(request.url());
  if (url.pathname.includes("/ai/") || url.pathname.includes("/threads")) providerCalls += 1;
  const json = (body, status = 200) => route.fulfill({ status, contentType: "application/json", headers: { "Access-Control-Allow-Origin": "*" }, body: JSON.stringify(body) });

  const wsMatch = url.pathname.match(/^\/workspaces\/(ws1|ws2)/);
  const ws = wsMatch?.[1];
  if (request.method() === "GET" && url.pathname === "/workspaces") return json([
    { id: "ws1", name: "Evidence one", slug: "evidence-one", status: "active", created_at: "2026-08-22T00:00:00Z", updated_at: "2026-08-22T00:00:00Z" },
    { id: "ws2", name: "Evidence two", slug: "evidence-two", status: "active", created_at: "2026-08-22T00:00:00Z", updated_at: "2026-08-22T00:00:00Z" }
  ]);
  if (ws && request.method() === "GET" && url.pathname === `/workspaces/${ws}/model-implementations`) return json([implementation(ws)]);
  if (ws && request.method() === "GET" && url.pathname === `/workspaces/${ws}/parameters`) return json(parameters(ws));
  if (ws && request.method() === "GET" && url.pathname === `/workspaces/${ws}/model-specs`) return json([]);
  if (ws && request.method() === "GET" && url.pathname === `/workspaces/${ws}/assumptions`) return json([]);
  if (ws && request.method() === "GET" && url.pathname === `/workspaces/${ws}/decisions`) return json([]);
  if (ws && request.method() === "GET" && url.pathname.includes("/bluecad/candidates/")) {
    const candidateId = url.pathname.split("/candidates/")[1].split("/")[0];
    const values = candidateId === "cand-b" ? [20, 100, 112] : candidateId === "cand-c" ? [30, 120, 134] : [12, 80, 90];
    return json(candidateAggregate(ws, candidateId, ...values));
  }
  if (ws && request.method() === "POST" && url.pathname.includes("/binding-preview")) {
    previewCalls += 1;
    const payload = request.postDataJSON()?.bindings ?? {};
    const rows = variables.map((v) => {
      const binding = payload[v.name];
      const value = binding?.value ?? null;
      const invalid = value != null && value !== "" && !Number.isFinite(Number(value));
      return { ...v, binding_state: invalid ? "invalid" : binding ? "manual" : "missing", value, source_parameter_id: binding?.source_parameter_id ?? null, errors: invalid ? ["non-finite"] : [] };
    });
    const missing = rows.filter((v) => v.required && v.binding_state === "missing").length;
    const invalid = rows.filter((v) => v.binding_state === "invalid").length;
    return json({
      model_version_id: `model-semantic-v3-${ws}`,
      contract_sha256: implementation(ws).input_contract_sha256,
      evaluation_mode: "forward",
      structural_input_dof: 9,
      bound_input_dof: 9 - missing,
      unresolved_input_dof: missing,
      invalid_binding_count: invalid,
      state: missing || invalid ? "incomplete" : "ready",
      variables: rows,
      errors: invalid ? ["One or more input bindings are invalid."] : [],
      normalized_input_set: missing || invalid ? null : payload
    });
  }
  if (ws && request.method() === "POST" && url.pathname === `/workspaces/${ws}/runner-jobs`) {
    runnerCreateCalls += 1;
    return json({ runner_job: { id: `job-${ws}`, status: "queued" }, simulation_run: { id: `run-${ws}`, workspace_id: ws, status: "queued", created_at: "2026-08-22T00:00:00Z" } });
  }
  if (request.method() === "POST" && url.pathname.startsWith("/runner-jobs/") && url.pathname.endsWith("/run")) {
    runnerRunCalls += 1;
    const wsid = url.pathname.includes("ws2") ? "ws2" : "ws1";
    return json({ runner_job: { id: `job-${wsid}`, status: "succeeded" }, simulation_run: { id: `run-${wsid}`, workspace_id: wsid, status: "succeeded", created_at: "2026-08-22T00:00:00Z" }, output: {}, error: null });
  }
  return json({ detail: `Unhandled evidence route ${request.method()} ${url.pathname}` }, 404);
});

await page.goto("http://127.0.0.1:4173/097-evidence.html");
await page.locator("#engineering-property-reservoir_liquid_volume").waitFor();
await page.getByText(/deterministic blocker signal/).waitFor();
assert.equal(providerCalls, 0, "deterministic action surface requires no provider/thread call");

// Safe fix preview must disclose complete operator-visible change data.
const firstSafe = page.getByRole("button", { name: /Review safe fix/ }).first();
await firstSafe.click();
await page.getByText("Proposed working-state change", { exact: true }).waitFor();
const proposal = page.getByText(/→/).first();
assert.match(await proposal.textContent(), /→/, "proposal exposes old to proposed value");
assert.ok((await page.locator("text=Compatible linked Parameter").count()) + (await page.locator("text=Working baseline").count()) + (await page.locator("text=CAD source baseline").count()) > 0, "proposal exposes deterministic basis");

// Manual edit after proposal must stale old confirm and never overwrite the new value.
const editedField = page.locator("#engineering-property-reservoir_liquid_volume");
await editedField.fill("111");
await page.getByRole("button", { name: "Confirm", exact: true }).click();
await page.getByText(/This action is stale/).waitFor();
assert.equal(await editedField.inputValue(), "111", "stale action cannot overwrite later manual edit");

// Recreate a valid single safe fix and apply exactly once; patch alone makes zero runner calls.
await editedField.fill("");
await page.waitForTimeout(150);
await page.getByRole("button", { name: /Review safe fix · Reservoir liquid volume/ }).click();
const beforePreview = previewCalls;
await page.getByRole("button", { name: "Confirm", exact: true }).click();
await page.getByText(/Applied to the working configuration/).waitFor();
assert.equal(runnerCreateCalls, 0, "working patch creates zero runner jobs");
assert.equal(runnerRunCalls, 0, "working patch does not execute");
assert.equal(await page.getByRole("button", { name: "Confirm", exact: true }).count(), 0, "applied card cannot be confirmed twice");
await page.waitForTimeout(200);
assert.ok(previewCalls > beforePreview, "working revision change triggers fresh deterministic preflight");

// Hostile Other content remains inert.
await page.getByRole("button", { name: "Other", exact: true }).click();
const other = page.getByPlaceholder("Describe an alternative");
await other.fill('{"tube_length":999}<script>set x=1</script>');
await page.waitForTimeout(50);
assert.equal(runnerCreateCalls, 0);
assert.equal(await other.inputValue(), '{"tube_length":999}<script>set x=1</script>');
assert.equal(await page.getByText(/This text is inert/).count(), 1, "Other explicitly remains inert");

// Dirty two fields produce only an atomic Revert-all bulk safe-fix; a later revision change stales the whole action.
await page.locator("#engineering-property-tube_length").fill("");
await page.locator("#engineering-property-tube_inner_diameter").fill("");
await page.waitForTimeout(150);
const bulk = page.getByRole("button", { name: "Apply safe fixes", exact: true });
await bulk.waitFor();
await bulk.click();
assert.ok(await page.getByText(/Tube length/).count() > 0 && await page.getByText(/Tube inner diameter/).count() > 0, "multi-field preview exposes both operations");
await page.locator("#engineering-property-tube_outer_diameter").fill("91");
await page.getByRole("button", { name: "Confirm", exact: true }).click();
await page.getByText(/This action is stale/).waitFor();
assert.equal(await page.locator("#engineering-property-tube_length").inputValue(), "", "stale multi-field action applies zero first operation");
assert.equal(await page.locator("#engineering-property-tube_inner_diameter").inputValue(), "", "stale multi-field action applies zero second operation");

// Object switch invalidates old proposal and cannot mutate B.
await page.locator("#engineering-property-tube_length").fill("");
await page.waitForTimeout(100);
const objectSafe = page.getByRole("button", { name: /Review safe fix · Tube length/ });
await objectSafe.click();
await page.getByRole("button", { name: "Select B" }).click();
await page.getByRole("button", { name: "Confirm", exact: true }).click();
await page.getByText(/This action is stale/).waitFor();
await page.waitForTimeout(200);
assert.notEqual(await page.locator("#engineering-property-tube_length").inputValue(), "12", "A proposal cannot write A baseline into B");

// Workspace switch similarly makes prior action inert and provider failure is irrelevant to deterministic UI.
await page.getByRole("button", { name: "Switch workspace" }).click();
await page.waitForFunction(() => document.querySelector('[data-testid="workspace-state"]')?.textContent === "ws2");
await page.locator("#engineering-property-reservoir_liquid_volume").waitFor();
await page.getByText(/deterministic blocker signal/).waitFor();
assert.equal(providerCalls, 0, "workspace change still requires no AI/thread call");
assert.ok(await page.getByText(/AI suggested — not validated/).count() > 0, "assistant numeric/model advice warning remains visible");

// Effective-200%-like containment and keyboard reachability.
await page.setViewportSize({ width: 640, height: 900 });
await page.waitForTimeout(100);
const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
assert.ok(overflow <= 1, `compact viewport has no page-level horizontal overflow (delta=${overflow})`);
const otherButton = page.getByRole("button", { name: "Other", exact: true });
await otherButton.focus();
assert.equal(await otherButton.evaluate((el) => el === document.activeElement), true, "action controls are keyboard focusable");

console.log("097_BROWSER_EVIDENCE_PASS");
await browser.close();
