import { chromium } from "playwright";
import assert from "node:assert/strict";

const now = "2026-08-24T12:00:00Z";
const variables = [
  { name: "length", label: "Length", unit: "m", required: true, category: "design", description: "Tube length." },
  { name: "flow", label: "Flow rate", unit: "m3/s", required: true, category: "operating", description: "Flow rate." },
  { name: "roughness", label: "Roughness", unit: "m", required: false, category: "property", description: "Optional roughness." }
];

function implementation(workspaceId, id, label, digest) {
  return { id, workspace_id: workspaceId, model_spec_id: `spec-${id}`, version_label: label, implementation_artifact_id: `artifact-${id}`, status: "accepted", script_sha256: "a".repeat(64), script_path: `${id}.py`, created_at: now, input_contract_sha256: digest, input_contract: { schema_version: 1, evaluation_mode: "forward", variables } };
}
const ws1Implementations = [implementation("ws1", "model-a", "Model A", "b".repeat(64)), implementation("ws1", "model-b", "Model B", "c".repeat(64))];
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
  return { id, workspace_id: workspaceId, model_version_id: modelVersionId, run_label: label, status, input_payload: inputPayload === null ? null : JSON.stringify(inputPayload), parameter_payload: null, output_payload: outputPayload === null ? null : JSON.stringify(outputPayload), started_at: now, completed_at: now, created_at: now, notes: null };
}
const ws1Runs = [
  run("ws1", "run-base", "Baseline 600", "model-a", input(10, 0.2), output(0.82, 0.1)),
  run("ws1", "run-alt", "Variant 650", "model-a", input(12, 0.25, 0.0001), output(0.79, 0.42)),
  run("ws1", "run-other-model", "Other model", "model-b", input(10, 0.2, 0.0001), output(0.80, 0.2)),
  run("ws1", "run-bad-unit", "Bad input unit", "model-a", input(10, 0.2, 0.0001, "cm"), output(0.81, 0.3)),
  run("ws1", "run-malformed", "Malformed snapshot", "model-a", { length: { value: 10, unit: "m" } }, output(0.81, 0.3))
];
const ws2Runs = [run("ws2", "run-ws2", "Workspace B run", "model-c", input(20, 0.4, 0.0002), output(0.7, 0.5))];

let canonicalMutationCalls = 0;
let runnerCreateCalls = 0;
let runnerRunCalls = 0;
let providerCalls = 0;
let ws1ModelRequests = 0;

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
  if (method === "GET" && url.pathname === "/workspaces/ws1/simulation-runs") return json(ws1Runs);
  if (method === "GET" && url.pathname === "/workspaces/ws2/simulation-runs") return json(ws2Runs);
  if (method === "GET" && url.pathname === "/workspaces/ws1/model-implementations") { ws1ModelRequests += 1; if (ws1ModelRequests === 1) await new Promise((resolve) => setTimeout(resolve, 350)); return json(ws1Implementations); }
  if (method === "GET" && url.pathname === "/workspaces/ws2/model-implementations") return json(ws2Implementations);
  if (method === "OPTIONS") return route.fulfill({ status: 204, headers: { "Access-Control-Allow-Origin": "*", "Access-Control-Allow-Headers": "Content-Type" } });
  return json({ detail: `Unhandled evidence request ${method} ${url.pathname}` }, 404);
});

const runCheckbox = (label) => page.locator("label.analytics-run-row").filter({ hasText: label }).locator('input[type="checkbox"]').first();
const baselineRadio = (label) => page.locator("fieldset.analytics-selection label.analytics-run-row").filter({ hasText: label }).locator('input[type="radio"]').first();

await page.goto("http://127.0.0.1:4173/058b-evidence.html");
await page.getByRole("button", { name: "Workspace B" }).click();
await page.getByText("Workspace B run").waitFor();
await page.waitForTimeout(450);
assert.equal(await page.getByText("Baseline 600").count(), 0, "late workspace-A response must not repopulate the dock");
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
assert.equal(await page.getByText(/Model choice/i).count(), 0, "model choice must be omitted without authoritative metadata");

await page.getByRole("heading", { name: "Recorded results" }).waitFor();
await page.getByText("conversion", { exact: true }).waitFor();
await page.getByText("0.82 1", { exact: true }).waitFor();
await page.getByText("0.79 1", { exact: true }).waitFor();

const variantBaseline = baselineRadio("Variant 650");
await variantBaseline.focus();
await variantBaseline.press("Space");
await page.getByRole("columnheader", { name: /Variant 650.*Baseline/ }).waitFor();
await page.getByText("Δ -2 m", { exact: true }).waitFor();

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

const sourceLink = page.getByRole("link", { name: "Open source runs" });
assert.equal(await sourceLink.getAttribute("href"), "/runs");
assert.equal(canonicalMutationCalls, 0);
assert.equal(runnerCreateCalls, 0);
assert.equal(runnerRunCalls, 0);
assert.equal(providerCalls, 0);

await page.setViewportSize({ width: 640, height: 900 });
await page.waitForTimeout(150);
const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
assert.ok(overflow <= 1, `unexpected page-level horizontal overflow: ${overflow}px`);

console.log("058B_BROWSER_EVIDENCE_PASS", { canonicalMutationCalls, runnerCreateCalls, runnerRunCalls, providerCalls, workspaceStaleGuard: "pass" });
await browser.close();
