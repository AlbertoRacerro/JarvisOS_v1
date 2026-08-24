import { chromium } from "playwright";
import assert from "node:assert/strict";

const now = "2026-08-24T14:00:00Z";
const variables = [
  { name: "length", label: "Length", unit: "m", required: true, category: "design", description: "Tube length." },
  { name: "flow", label: "Flow rate", unit: "m3/s", required: true, category: "operating", description: "Flow rate." },
  { name: "roughness", label: "Roughness", unit: "m", required: false, category: "property", description: "Optional roughness." }
];

function implementation(workspaceId, id, label, digest, semantic = false) {
  return {
    id,
    workspace_id: workspaceId,
    model_spec_id: `spec-${id}`,
    version_label: label,
    implementation_artifact_id: `artifact-${id}`,
    status: "accepted",
    script_sha256: "a".repeat(64),
    script_path: `${id}.py`,
    created_at: now,
    input_contract_sha256: digest,
    input_contract: semantic ? {
      schema_version: 3,
      evaluation_mode: "forward",
      semantic_context: {
        applicable_part_kinds: ["tube_run"],
        model_family_key: "geometry_hydraulics",
        model_family_label: "Geometry & hydraulics",
        model_option_label: "Reviewed tubular-loop V0"
      },
      variables
    } : { schema_version: 1, evaluation_mode: "forward", variables }
  };
}

const ws1Implementations = [
  implementation("ws1", "model-a", "Model A", "b".repeat(64), true),
  implementation("ws1", "model-b", "Model B", "c".repeat(64))
];
const ws2Implementations = [implementation("ws2", "model-c", "Model C", "d".repeat(64))];

function input(length, flow, roughness = undefined, lengthUnit = "m") {
  const payload = { length: { value: length, unit: lengthUnit }, flow: { value: flow, unit: "m3/s" } };
  if (roughness !== undefined) payload.roughness = { value: roughness, unit: "m" };
  return payload;
}
function output(conversion, pressureDrop, pressureUnit = "bar") {
  return { schema_version: 1, status: "succeeded", outputs: { conversion: { value: conversion, unit: "1" }, pressure_drop: { value: pressureDrop, unit: pressureUnit } } };
}
function run(workspaceId, id, label, modelVersionId, inputPayload, outputPayload, status = "succeeded") {
  return {
    id,
    workspace_id: workspaceId,
    model_version_id: modelVersionId,
    run_label: label,
    status,
    input_payload: inputPayload === null ? null : JSON.stringify(inputPayload),
    parameter_payload: null,
    output_payload: outputPayload === null ? null : JSON.stringify(outputPayload),
    started_at: now,
    completed_at: now,
    created_at: now,
    notes: null
  };
}

const ws1Runs = [
  run("ws1", "run-base", "Baseline 600", "model-a", input(10, 0.2), output(0.82, 0.1)),
  run("ws1", "run-alt", "Variant 650", "model-a", input(12, 0.25, 0.0001), output(0.79, 0.42)),
  run("ws1", "run-other-model", "Other model", "model-b", input(10, 0.2, 0.0001), output(0.80, 0.2)),
  run("ws1", "run-bad-unit", "Bad input unit", "model-a", input(10, 0.2, 0.0001, "cm"), output(0.81, 0.3)),
  run("ws1", "run-malformed", "Malformed snapshot", "model-a", { length: { value: 10, unit: "m" } }, output(0.81, 0.3))
];
const ws2Runs = [run("ws2", "run-ws2", "Workspace B run", "model-c", input(20, 0.4, 0.0002), output(0.70, 0.5))];
const workspaces = [
  { id: "ws1", name: "Workspace A", slug: "workspace-a", description: null, status: "active", created_at: now, updated_at: now },
  { id: "ws2", name: "Workspace B", slug: "workspace-b", description: null, status: "active", created_at: now, updated_at: now }
];

let canonicalMutationCalls = 0;
let runnerCreateCalls = 0;
let runnerRunCalls = 0;
let providerCalls = 0;
let delayWs1Models = true;
let failWs1Models = false;

const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({ viewport: { width: 1280, height: 900 }, colorScheme: "dark", reducedMotion: "reduce" });
const page = await context.newPage();

await page.route("http://127.0.0.1:8000/**", async (route) => {
  const request = route.request();
  const url = new URL(request.url());
  const method = request.method();
  const json = (body, status = 200) => route.fulfill({ status, contentType: "application/json", headers: { "Access-Control-Allow-Origin": "*", "Access-Control-Allow-Headers": "Content-Type" }, body: JSON.stringify(body) });

  if (url.pathname.includes("/ai/") || url.pathname.includes("/threads")) providerCalls += 1;
  if (method !== "GET" && (url.pathname.includes("/parameters") || url.pathname.includes("/assumptions") || url.pathname.includes("/decisions") || url.pathname.includes("/specifications") || url.pathname.includes("/constraints"))) canonicalMutationCalls += 1;
  if (method === "POST" && url.pathname.endsWith("/runner-jobs")) runnerCreateCalls += 1;
  if (method === "POST" && /\/runner-jobs\/[^/]+\/run$/.test(url.pathname)) runnerRunCalls += 1;

  if (method === "OPTIONS") return route.fulfill({ status: 204, headers: { "Access-Control-Allow-Origin": "*", "Access-Control-Allow-Headers": "Content-Type" } });
  if (method === "GET" && url.pathname === "/workspaces") return json(workspaces);
  if (method === "GET" && url.pathname === "/workspaces/ws1/simulation-runs") return json(ws1Runs);
  if (method === "GET" && url.pathname === "/workspaces/ws2/simulation-runs") return json(ws2Runs);
  if (method === "GET" && url.pathname === "/workspaces/ws1/model-implementations") {
    if (delayWs1Models) await new Promise((resolve) => setTimeout(resolve, 350));
    if (failWs1Models) return json({ detail: "evidence model read unavailable" }, 503);
    return json(ws1Implementations);
  }
  if (method === "GET" && url.pathname === "/workspaces/ws2/model-implementations") return json(ws2Implementations);

  const detailMatch = url.pathname.match(/^\/workspaces\/(ws1|ws2)\/simulation-runs\/([^/]+)$/);
  if (method === "GET" && detailMatch) {
    const rows = detailMatch[1] === "ws1" ? ws1Runs : ws2Runs;
    const found = rows.find((item) => item.id === decodeURIComponent(detailMatch[2]));
    return found ? json(found) : json({ detail: "not found" }, 404);
  }
  if (method === "GET" && /^\/workspaces\/(ws1|ws2)\/simulation-runs\/[^/]+\/logs$/.test(url.pathname)) return json([]);
  if (method === "GET" && /^\/workspaces\/(ws1|ws2)\/simulation-runs\/[^/]+\/artifacts$/.test(url.pathname)) return json([]);

  return json({ detail: `Unhandled evidence request ${method} ${url.pathname}` }, 404);
});

const runCheckbox = (label) => page.locator("label.analytics-run-row").filter({ hasText: label }).locator('input[type="checkbox"]').first();
const baselineRadio = (label) => page.locator("fieldset.analytics-selection label.analytics-run-row").filter({ hasText: label }).locator('input[type="radio"]').first();

await page.goto("http://127.0.0.1:4173/058b-evidence.html");
await page.getByRole("button", { name: "Workspace B" }).click();
await page.getByText("Workspace B run").waitFor();
await page.waitForTimeout(450);
assert.equal(await page.getByText("Baseline 600").count(), 0, "late workspace-A response must not repopulate the dock");

delayWs1Models = false;
await page.getByRole("button", { name: "Workspace A" }).click();
await page.getByText("Baseline 600").waitFor();
await runCheckbox("Baseline 600").check();
await runCheckbox("Variant 650").check();
await page.getByRole("heading", { name: "Engineering configuration" }).waitFor();
await page.getByRole("columnheader", { name: /Baseline 600.*Baseline/ }).waitFor();
await page.getByRole("rowheader", { name: /Length/ }).waitFor();
await page.getByText("10 m", { exact: true }).waitFor();
await page.getByText("12 m", { exact: true }).waitFor();
await page.getByText("Δ +2 m", { exact: true }).waitFor();
await page.getByText("Empty", { exact: true }).waitFor();
await page.getByRole("rowheader", { name: /Geometry & hydraulics.*Model choice/ }).waitFor();
assert.equal(await page.getByText("Reviewed tubular-loop V0", { exact: true }).count(), 2, "authoritative schema-v3 model choice was not rendered for both selected runs");

await page.getByRole("heading", { name: "Recorded results" }).waitFor();
await page.getByText("conversion", { exact: true }).waitFor();
await page.getByText("0.82 1", { exact: true }).first().waitFor();
await page.getByText("0.79 1", { exact: true }).first().waitFor();

const variantBaseline = baselineRadio("Variant 650");
await variantBaseline.focus();
await variantBaseline.press("Space");
await page.getByRole("columnheader", { name: /Variant 650.*Baseline/ }).waitFor();
await page.getByText("Δ -2 m", { exact: true }).waitFor();

failWs1Models = true;
await page.getByRole("button", { name: "Refresh" }).click();
await page.getByText(/Model contracts unavailable:/).waitFor();
assert.equal(await baselineRadio("Variant 650").isChecked(), true, "baseline disappeared when configuration evidence became unavailable");
await baselineRadio("Baseline 600").focus();
await baselineRadio("Baseline 600").press("Space");
assert.equal(await baselineRadio("Baseline 600").isChecked(), true, "baseline could not be changed while configuration evidence was unavailable");
await page.getByText("conversion", { exact: true }).waitFor();

failWs1Models = false;
await page.getByRole("button", { name: "Refresh" }).click();
await page.getByRole("rowheader", { name: /Geometry & hydraulics.*Model choice/ }).waitFor();

await runCheckbox("Variant 650").uncheck();
await runCheckbox("Other model").check();
await page.getByText(/one exact model version/i).first().waitFor();
await runCheckbox("Other model").uncheck();
await runCheckbox("Bad input unit").check();
await page.getByText(/Units do not match the current contract/i).waitFor();
await page.getByRole("heading", { name: "Recorded results" }).waitFor();
await runCheckbox("Bad input unit").uncheck();
await runCheckbox("Malformed snapshot").check();
await page.getByText(/Run snapshot is incomplete/i).waitFor();
await runCheckbox("Malformed snapshot").uncheck();
await runCheckbox("Variant 650").check();

const variantSourceLink = page.getByRole("link", { name: "Open Variant 650" });
assert.equal(await variantSourceLink.getAttribute("href"), "/runs?workspace=ws1&run=run-alt", "source link did not carry exact workspace+run identity");

assert.equal(canonicalMutationCalls, 0);
assert.equal(runnerCreateCalls, 0);
assert.equal(runnerRunCalls, 0);
assert.equal(providerCalls, 0);

await page.setViewportSize({ width: 640, height: 900 });
await page.waitForTimeout(150);
const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
assert.ok(overflow <= 1, `unexpected page-level horizontal overflow: ${overflow}px`);

await page.goto("http://127.0.0.1:4173/058b-evidence.html?evidenceRunLanding=1&workspace=ws1&run=run-alt");
await page.getByRole("heading", { name: "Runs" }).waitFor();
await page.getByRole("combobox", { name: "Workspace" }).waitFor();
assert.equal(await page.getByRole("combobox", { name: "Workspace" }).inputValue(), "ws1", "source-run target did not restore exact workspace in RunsWorkbench");
const selectedRun = page.locator('button[data-run-id="run-alt"]');
await selectedRun.waitFor();
assert.equal(await selectedRun.getAttribute("aria-pressed"), "true", "source-run target did not select exact run identity in RunsWorkbench");
await page.getByRole("heading", { name: "Variant 650" }).waitFor();

assert.equal(canonicalMutationCalls, 0);
assert.equal(runnerCreateCalls, 0);
assert.equal(runnerRunCalls, 0);
assert.equal(providerCalls, 0);

console.log("058B_BROWSER_EVIDENCE_PASS", {
  canonicalMutationCalls,
  runnerCreateCalls,
  runnerRunCalls,
  providerCalls,
  workspaceStaleGuard: "pass",
  schemaV3ModelChoice: "pass",
  partialBaseline: "pass",
  sourceRunIdentity: "pass"
});
await browser.close();
