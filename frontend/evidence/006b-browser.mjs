import { chromium } from "playwright";
import assert from "node:assert/strict";

const now = "2026-08-24T00:00:00Z";
const workspace = { id: "ws1", name: "Evidence workspace", slug: "evidence", status: "active", created_at: now, updated_at: now };
const variables = [
  { name: "length", label: "Length", unit: "m", required: true, category: "design", description: "Evidence length." },
  { name: "mass", label: "Mass", unit: "kg", required: false, category: "property", description: "Optional evidence mass." }
];

function implementation(id, label, digest) {
  return {
    id,
    workspace_id: "ws1",
    model_spec_id: `spec-${id}`,
    version_label: label,
    implementation_artifact_id: `artifact-${id}`,
    status: "accepted",
    script_sha256: "a".repeat(64),
    script_path: `${id}.py`,
    created_at: now,
    input_contract_sha256: digest,
    input_contract: { schema_version: 1, evaluation_mode: "forward", variables }
  };
}

const implementations = [
  implementation("model-a", "Model A", "b".repeat(64)),
  implementation("model-b", "Model B", "c".repeat(64))
];

function run(id, label, status, modelVersionId, input) {
  return {
    id,
    workspace_id: "ws1",
    model_version_id: modelVersionId,
    run_label: label,
    status,
    input_payload: input == null ? null : JSON.stringify(input),
    parameter_payload: null,
    output_payload: status === "succeeded" ? JSON.stringify({ ok: true }) : null,
    started_at: now,
    completed_at: status === "succeeded" || status === "failed" ? now : null,
    created_at: now,
    notes: null
  };
}

const runs = [
  run("run-good", "Good baseline", "succeeded", "model-a", {
    length: { value: 12, unit: "m", source_parameter_id: "historical-parameter" },
    mass: { value: 5, unit: "kg" }
  }),
  run("run-alt", "Alt baseline", "succeeded", "model-b", {
    length: { value: 30, unit: "m" },
    mass: { value: 7, unit: "kg" }
  }),
  run("run-optional-empty", "Optional empty", "succeeded", "model-a", {
    length: { value: 18, unit: "m" }
  }),
  run("run-bad-unit", "Bad unit", "succeeded", "model-a", {
    length: { value: 12, unit: "cm" },
    mass: { value: 5, unit: "kg" }
  }),
  run("run-failed", "Failed run", "failed", "model-a", {
    length: { value: 12, unit: "m" },
    mass: { value: 5, unit: "kg" }
  })
];

let previewCalls = 0;
let runnerCreateCalls = 0;
let runnerRunCalls = 0;
let canonicalMutationCalls = 0;
let providerCalls = 0;

const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({ viewport: { width: 1280, height: 900 }, colorScheme: "light", reducedMotion: "reduce" });
const page = await context.newPage();

await page.route("http://127.0.0.1:8000/**", async (route) => {
  const request = route.request();
  const url = new URL(request.url());
  const method = request.method();
  const json = (body, status = 200) => route.fulfill({
    status,
    contentType: "application/json",
    headers: { "Access-Control-Allow-Origin": "*", "Access-Control-Allow-Headers": "Content-Type" },
    body: JSON.stringify(body)
  });

  if (url.pathname.includes("/ai/") || url.pathname.includes("/threads")) providerCalls += 1;
  if (method !== "GET" && (url.pathname.includes("/parameters") || url.pathname.includes("/assumptions") || url.pathname.includes("/decisions"))) canonicalMutationCalls += 1;
  if (method === "POST" && url.pathname.endsWith("/runner-jobs")) runnerCreateCalls += 1;
  if (method === "POST" && /\/runner-jobs\/[^/]+\/run$/.test(url.pathname)) runnerRunCalls += 1;

  if (method === "GET" && url.pathname === "/workspaces") return json([workspace]);
  if (method === "GET" && url.pathname === "/workspaces/ws1/model-implementations") return json(implementations);
  if (method === "GET" && url.pathname === "/workspaces/ws1/parameters") return json([]);
  if (method === "GET" && url.pathname === "/workspaces/ws1/simulation-runs") return json(runs);

  const runMatch = url.pathname.match(/^\/workspaces\/ws1\/simulation-runs\/([^/]+)$/);
  if (method === "GET" && runMatch) {
    const item = runs.find((candidate) => candidate.id === decodeURIComponent(runMatch[1]));
    return item ? json(item) : json({ detail: "not found" }, 404);
  }
  if (method === "GET" && /^\/workspaces\/ws1\/simulation-runs\/[^/]+\/logs$/.test(url.pathname)) return json([]);
  if (method === "GET" && /^\/workspaces\/ws1\/simulation-runs\/[^/]+\/artifacts$/.test(url.pathname)) return json([]);

  const previewMatch = url.pathname.match(/^\/workspaces\/ws1\/model-implementations\/(model-a|model-b)\/binding-preview$/);
  if (method === "POST" && previewMatch) {
    previewCalls += 1;
    const modelId = previewMatch[1];
    const body = request.postDataJSON();
    const bindings = body?.bindings ?? {};
    const rows = variables.map((variable) => {
      const binding = bindings[variable.name];
      const hasValue = binding && typeof binding.value === "number" && Number.isFinite(binding.value);
      return {
        ...variable,
        binding_state: hasValue ? "manual" : "missing",
        value: hasValue ? binding.value : null,
        source_parameter_id: null,
        errors: []
      };
    });
    const missingRequired = rows.filter((row) => row.required && row.binding_state === "missing").length;
    return json({
      model_version_id: modelId,
      contract_sha256: implementations.find((item) => item.id === modelId).input_contract_sha256,
      evaluation_mode: "forward",
      structural_input_dof: variables.length,
      bound_input_dof: variables.length - missingRequired,
      unresolved_input_dof: missingRequired,
      invalid_binding_count: 0,
      state: missingRequired ? "incomplete" : "ready",
      variables: rows,
      errors: [],
      normalized_input_set: missingRequired ? null : bindings
    });
  }

  if (method === "OPTIONS") return route.fulfill({ status: 204, headers: { "Access-Control-Allow-Origin": "*", "Access-Control-Allow-Headers": "Content-Type" } });
  return json({ detail: `Unhandled evidence request ${method} ${url.pathname}` }, 404);
});

await page.goto("http://127.0.0.1:4173/006b-evidence.html");
await page.getByRole("heading", { name: "Runs", level: 1 }).waitFor();
await page.getByRole("button", { name: /Good baseline/ }).click();
await page.getByRole("button", { name: "Load as working configuration" }).waitFor();

await page.getByRole("button", { name: "Load as working configuration" }).click();
await page.getByText("Good baseline · Previous successful run").waitFor();
const lengthInput = page.getByLabel("Value [m]");
const massInput = page.getByLabel("Value [kg]");
assert.equal(await lengthInput.inputValue(), "12");
assert.equal(await massInput.inputValue(), "5");
await page.getByText("Previous successful run", { exact: true }).first().waitFor();
await page.getByText("Ready", { exact: true }).waitFor();
assert.ok(previewCalls > 0, "loaded baseline must trigger deterministic preflight");
assert.equal(runnerCreateCalls, 0);
assert.equal(runnerRunCalls, 0);
assert.equal(canonicalMutationCalls, 0);
assert.equal(providerCalls, 0);

await lengthInput.fill("13");
await page.getByText(/1 unsaved change/).waitFor();
await page.getByRole("button", { name: /Alt baseline/ }).click();
await page.getByRole("button", { name: "Load as working configuration" }).click();
await page.getByText(/Current unsaved working edits will be replaced/).waitFor();
await page.getByRole("button", { name: "Cancel" }).click();
assert.equal(await lengthInput.inputValue(), "13");

await page.getByRole("button", { name: "Load as working configuration" }).click();
await lengthInput.fill("14");
await page.getByRole("button", { name: "Replace unsaved changes" }).click();
await page.getByText(/Working configuration changed before load completed/).waitFor();
assert.equal(await lengthInput.inputValue(), "14");

await page.getByRole("button", { name: "Load as working configuration" }).click();
await page.getByRole("button", { name: "Replace unsaved changes" }).click();
await page.getByRole("combobox", { name: "Model contract" }).waitFor();
await page.waitForFunction(() => {
  const select = document.querySelector('select');
  return Boolean(select);
});
await page.getByText("Alt baseline · Previous successful run").waitFor();
assert.equal(await lengthInput.inputValue(), "30");
assert.equal(await massInput.inputValue(), "7");
await page.getByText("Ready", { exact: true }).waitFor();

await lengthInput.fill("31");
await page.getByRole("button", { name: "Revert field" }).first().click();
assert.equal(await lengthInput.inputValue(), "30");

await page.getByRole("button", { name: /Optional empty/ }).click();
await page.getByRole("button", { name: "Load as working configuration" }).click();
await page.getByText(/Switching to the run's exact model contract/).waitFor();
await page.getByText("Optional empty · Previous successful run").waitFor();
assert.equal(await lengthInput.inputValue(), "18");
assert.equal(await massInput.inputValue(), "");
await page.getByText("Optional · Empty").waitFor();

await page.getByRole("button", { name: /Bad unit/ }).click();
await page.getByText("Units do not match the current contract").waitFor();
assert.equal(await page.getByRole("button", { name: "Load as working configuration" }).count(), 0);
await page.getByRole("button", { name: /Failed run/ }).click();
await page.getByText("Run did not succeed").waitFor();
assert.equal(await page.getByRole("button", { name: "Load as working configuration" }).count(), 0);

assert.equal(runnerCreateCalls, 0);
assert.equal(runnerRunCalls, 0);
assert.equal(canonicalMutationCalls, 0);
assert.equal(providerCalls, 0);

await page.getByRole("button", { name: /Good baseline/ }).focus();
assert.equal(await page.evaluate(() => document.activeElement?.getAttribute("data-run-id")), "run-good");
await page.setViewportSize({ width: 640, height: 900 });
await page.waitForTimeout(150);
const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
assert.ok(overflow <= 1, `unexpected page-level horizontal overflow: ${overflow}px`);

console.log("006B_BROWSER_EVIDENCE_PASS", {
  previewCalls,
  runnerCreateCalls,
  runnerRunCalls,
  canonicalMutationCalls,
  providerCalls
});
await browser.close();
