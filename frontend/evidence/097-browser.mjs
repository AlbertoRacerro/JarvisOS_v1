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
  ["pump_efficiency", "Pump efficiency for the reviewed hydraulic operating configuration with a deliberately long engineering label", "1", "equipment", "Equipment", []]
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

function alternateImplementation(workspaceId) {
  const original = implementation(workspaceId);
  return {
    ...original,
    id: `model-alt-${workspaceId}`,
    version_label: "alternate reviewed 047 contract for stale-action evidence",
    input_contract_sha256: workspaceId === "ws1" ? "d".repeat(64) : "e".repeat(64)
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
    ["p-minor", "Minor loss", "2", "1"]
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
let sourceMutationCalls = 0;

const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({ viewport: { width: 1280, height: 900 }, colorScheme: "light", reducedMotion: "no-preference" });
const page = await context.newPage();

await page.route("http://127.0.0.1:8000/**", async (route) => {
  const request = route.request();
  const url = new URL(request.url());
  if (url.pathname.includes("/ai/") || url.pathname.includes("/threads")) providerCalls += 1;
  if (request.method() !== "GET" && (url.pathname.includes("/parameters") || url.pathname.includes("/bluecad/"))) sourceMutationCalls += 1;
  const json = (body, status = 200) => route.fulfill({ status, contentType: "application/json", headers: { "Access-Control-Allow-Origin": "*" }, body: JSON.stringify(body) });

  const wsMatch = url.pathname.match(/^\/workspaces\/(ws1|ws2)/);
  const ws = wsMatch?.[1];
  if (request.method() === "GET" && url.pathname === "/workspaces") return json([
    { id: "ws1", name: "Evidence one", slug: "evidence-one", status: "active", created_at: "2026-08-22T00:00:00Z", updated_at: "2026-08-22T00:00:00Z" },
    { id: "ws2", name: "Evidence two", slug: "evidence-two", status: "active", created_at: "2026-08-22T00:00:00Z", updated_at: "2026-08-22T00:00:00Z" }
  ]);
  if (ws && request.method() === "GET" && url.pathname === `/workspaces/${ws}/model-implementations`) return json([implementation(ws), alternateImplementation(ws)]);
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
      model_version_id: url.pathname.includes("model-alt-") ? `model-alt-${ws}` : `model-semantic-v3-${ws}`,
      contract_sha256: url.pathname.includes("model-alt-") ? alternateImplementation(ws).input_contract_sha256 : implementation(ws).input_contract_sha256,
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
assert.equal(await page.getByRole("button", { name: /Review safe fix · Pump efficiency/ }).count(), 0, "required blocker without baseline or compatible Parameter gets no invented safe fix");

// A proposal bound to model/contract A must go stale when the selected contract changes.
await page.getByRole("button", { name: /Review safe fix/ }).first().click();
await page.getByLabel("Model contract").selectOption("model-alt-ws1");
await page.getByRole("button", { name: "Confirm", exact: true }).click();
await page.getByText(/This action is stale/).waitFor();
await page.getByLabel("Model contract").selectOption("model-semantic-v3-ws1");
await page.locator("#engineering-property-reservoir_liquid_volume").waitFor();

const firstSafe = page.getByRole("button", { name: /Review safe fix/ }).first();
await firstSafe.click();
await page.getByText("Proposed working-state change", { exact: true }).waitFor();
const proposal = page.getByText(/→/).first();
assert.match(await proposal.textContent(), /→/, "proposal exposes old to proposed value");
assert.match(await proposal.textContent(), /(m|mm|L|m\/s|kg\/m3|Pa\*s|1)/, "proposal exposes exact engineering unit");
assert.ok((await page.locator("text=Compatible linked Parameter").count()) + (await page.locator("text=Working baseline").count()) + (await page.locator("text=CAD source baseline").count()) > 0, "proposal exposes deterministic basis");
assert.ok(await page.getByText(/Restore the|Use the only currently compatible/).count() > 0, "proposal exposes deterministic reason before Confirm");

const editedField = page.locator("#engineering-property-reservoir_liquid_volume");
await editedField.fill("111");
await page.getByRole("button", { name: "Confirm", exact: true }).click();
await page.getByText(/This action is stale/).waitFor();
assert.equal(await editedField.inputValue(), "111", "stale action cannot overwrite later manual edit");

await editedField.fill("");
await page.waitForTimeout(150);
await page.getByRole("button", { name: /Review safe fix · Reservoir liquid volume/ }).click();
const beforePreview = previewCalls;
await page.getByRole("button", { name: "Confirm", exact: true }).click();
await page.getByText(/Applied to the working configuration/).waitFor();
assert.equal(runnerCreateCalls, 0, "working patch creates zero runner jobs");
assert.equal(runnerRunCalls, 0, "working patch does not execute");
assert.equal(sourceMutationCalls, 0, "working patch does not mutate canonical Parameter or CAD source authority");
assert.equal(await page.getByRole("button", { name: "Confirm", exact: true }).count(), 0, "applied card cannot be confirmed twice after state commit");
await page.waitForTimeout(200);
assert.ok(previewCalls > beforePreview, "working revision change triggers fresh deterministic preflight");

for (const [name, value] of [
  ["target_liquid_velocity", "1.2"],
  ["liquid_density", "998"],
  ["dynamic_viscosity", "0.001"],
  ["minor_loss_coefficient", "2"],
  ["pump_efficiency", "0.75"]
]) {
  await page.locator(`#engineering-property-${name}`).fill(value);
}
await page.getByLabel("Run label").fill("097 evidence baseline");
await page.getByText("Ready", { exact: true }).waitFor();
assert.equal(runnerCreateCalls, 0, "becoming ready does not create a run");
assert.equal(runnerRunCalls, 0, "becoming ready does not execute a run");
await page.getByRole("button", { name: "Run", exact: true }).click();
await page.getByText(/Run completed/).waitFor();
assert.equal(runnerCreateCalls, 1, "explicit Run creates exactly one runner job");
assert.equal(runnerRunCalls, 1, "explicit Run dispatches exactly one execution");
assert.equal(sourceMutationCalls, 0, "running through existing 071b route does not rewrite canonical Parameter/CAD source evidence");
await page.getByText("Baseline: current bindings", { exact: true }).waitFor();

await editedField.fill("");
await page.waitForTimeout(150);
await page.getByRole("button", { name: "Other", exact: true }).click();
const other = page.getByPlaceholder("Describe an alternative");
await other.fill('{"tube_length":999}<script>set x=1</script>');
await page.waitForTimeout(50);
assert.equal(runnerCreateCalls, 1);
assert.equal(await other.inputValue(), '{"tube_length":999}<script>set x=1</script>');
assert.equal(await page.getByText(/This text is inert/).count(), 1, "Other explicitly remains inert");

await page.getByRole("button", { name: /Review safe fix · Reservoir liquid volume/ }).click();
await page.getByText("Technical details", { exact: true }).click();
const revisionValue = page.locator("dt", { hasText: "Working revision" }).locator("xpath=following-sibling::dd");
const revisionBeforeDouble = Number(await revisionValue.textContent());
await page.getByRole("button", { name: "Confirm", exact: true }).dblclick();
await page.getByText(/Applied to the working configuration/).waitFor();
await page.waitForTimeout(100);
const revisionAfterDouble = Number(await revisionValue.textContent());
assert.equal(revisionAfterDouble, revisionBeforeDouble + 1, "double Confirm applies a semantic action at most once");

await page.locator("#engineering-property-tube_length").fill("");
await page.locator("#engineering-property-tube_inner_diameter").fill("");
await page.waitForTimeout(150);
const bulk = page.getByRole("button", { name: "Apply safe fixes", exact: true });
await bulk.waitFor();
await bulk.click();
assert.ok(await page.getByText(/Tube length/).count() > 0 && await page.getByText(/Tube inner diameter/).count() > 0, "multi-field preview exposes both operations");
assert.ok(await page.getByText("CAD source baseline", { exact: true }).count() >= 2, "multi-field preview exposes each source basis before Confirm");
await page.locator("#engineering-property-tube_outer_diameter").fill("91");
await page.getByRole("button", { name: "Confirm", exact: true }).click();
await page.getByText(/This action is stale/).waitFor();
assert.equal(await page.locator("#engineering-property-tube_length").inputValue(), "", "stale multi-field action applies zero first operation");
assert.equal(await page.locator("#engineering-property-tube_inner_diameter").inputValue(), "", "stale multi-field action applies zero second operation");
assert.equal(sourceMutationCalls, 0, "stale action does not mutate source authority");

await page.locator("#engineering-property-tube_length").fill("");
await page.waitForTimeout(100);
const objectSafe = page.getByRole("button", { name: /Review safe fix · Tube length/ });
await objectSafe.click();
await page.getByRole("button", { name: "Select B" }).click();
await page.getByRole("button", { name: "Confirm", exact: true }).click();
await page.getByText(/This action is stale/).waitFor();
const discardPrevious = page.getByRole("button", { name: "Discard previous object changes and load selected object", exact: true });
await discardPrevious.waitFor();
await discardPrevious.click();
await page.locator("#engineering-property-tube_length").waitFor();
assert.equal(await page.locator("#engineering-property-tube_length").inputValue(), "20", "B retains its own authoritative geometry after stale A action");
assert.notEqual(await page.locator("#engineering-property-tube_length").inputValue(), "12", "A proposal cannot write A baseline into B");

await page.getByRole("button", { name: "Switch workspace" }).click();
await page.waitForFunction(() => document.querySelector('[data-testid="workspace-state"]')?.textContent === "ws2");
await page.locator("#engineering-property-reservoir_liquid_volume").waitFor();
await page.getByText(/deterministic blocker signal/).waitFor();
assert.equal(providerCalls, 0, "workspace change still requires no AI/thread call");
assert.ok(await page.getByText(/AI suggested — not validated/).count() > 0, "assistant numeric/model advice warning remains visible");

await page.emulateMedia({ colorScheme: "dark", reducedMotion: "reduce" });
await page.setViewportSize({ width: 640, height: 900 });
await page.waitForTimeout(100);
const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
assert.ok(overflow <= 1, `compact/dark/reduced-motion viewport has no page-level horizontal overflow (delta=${overflow})`);
const otherButton = page.getByRole("button", { name: "Other", exact: true });
await otherButton.focus();
assert.equal(await otherButton.evaluate((el) => el === document.activeElement), true, "action controls are keyboard focusable");
assert.equal(sourceMutationCalls, 0, "no working action mutates canonical Parameter/CAD source authority");

console.log("097_BROWSER_EVIDENCE_PASS");
await browser.close();
