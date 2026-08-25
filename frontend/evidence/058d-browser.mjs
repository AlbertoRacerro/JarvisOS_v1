import { chromium } from "playwright";
import assert from "node:assert/strict";

const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({ viewport: { width: 1280, height: 900 }, colorScheme: "dark", reducedMotion: "reduce" });
const page = await context.newPage();

const consoleErrors = [];
const pageErrors = [];
let mutationCalls = 0;
let providerCalls = 0;
let runnerCalls = 0;

page.on("console", (message) => { if (message.type() === "error") consoleErrors.push(message.text()); });
page.on("pageerror", (error) => pageErrors.push(String(error)));

await page.route("http://127.0.0.1:8000/**", async (route) => {
  const request = route.request();
  const url = new URL(request.url());
  const method = request.method();
  if (method !== "GET" && method !== "OPTIONS") mutationCalls += 1;
  if (url.pathname.includes("/ai/") || url.pathname.includes("/threads") || url.pathname.includes("/providers")) providerCalls += 1;
  if (url.pathname.includes("runner-jobs")) runnerCalls += 1;
  if (method === "OPTIONS") return route.fulfill({ status: 204, headers: { "Access-Control-Allow-Origin": "*", "Access-Control-Allow-Headers": "Content-Type" } });
  return route.fulfill({ status: 200, contentType: "application/json", headers: { "Access-Control-Allow-Origin": "*" }, body: "[]" });
});

const origin = "http://127.0.0.1:4173";

await page.goto(`${origin}/design/process`);
await page.getByRole("heading", { name: "Process workspace" }).waitFor();
assert.equal(new URL(page.url()).pathname, "/design/process");
await page.reload();
await page.getByRole("heading", { name: "Process workspace" }).waitFor();
assert.equal(new URL(page.url()).pathname, "/design/process");

const processButtons = page.getByRole("button", { name: /Add equipment|Connect/ });
assert.equal(await processButtons.count(), 2);
for (let i = 0; i < 2; i += 1) assert.equal(await processButtons.nth(i).isDisabled(), true);
await page.getByText("No process topology is loaded.", { exact: true }).waitFor();
await page.getByText("Not available yet.", { exact: true }).waitFor();

await page.getByRole("button", { name: "Show navigator" }).click();
const stageNav = page.getByRole("navigation", { name: "Design stages" });
await stageNav.waitFor();
const designHrefs = await stageNav.locator("a").evaluateAll((anchors) => anchors.map((anchor) => anchor.getAttribute("href")));
const designLabels = await stageNav.locator("a").allTextContents();
assert.deepEqual(designHrefs, ["/design/model", "/design/process", "/design/results", "/design/lineage"]);
assert.deepEqual(designLabels, ["Model", "Process", "Results", "Lineage"]);
await page.getByRole("button", { name: "Close navigator" }).click();

await page.getByRole("button", { name: "Show context" }).click();
await page.getByRole("heading", { name: "Jarvis & Properties" }).waitFor();
await page.getByRole("heading", { name: "Properties", exact: true }).waitFor();
assert.equal(await page.getByText(/selected BLUECAD part/i).count(), 0, "Process must not fabricate a semantic target");
await page.getByRole("button", { name: "Close sidecar" }).click();

await page.getByRole("button", { name: "Show analysis" }).click();
await page.getByRole("heading", { name: "Analysis dock" }).waitFor();
await page.getByRole("button", { name: "Close analysis dock" }).click();

await page.goto(`${origin}/design/lineage`);
await page.getByRole("heading", { name: "Dependency & provenance" }).waitFor();
assert.equal(new URL(page.url()).pathname, "/design/lineage");
await page.reload();
await page.getByRole("heading", { name: "Dependency & provenance" }).waitFor();
assert.equal(new URL(page.url()).pathname, "/design/lineage");

for (const legacyPath of ["/design/flowsheet", "/design/flowsheet/"]) {
  await page.goto(`${origin}/design/process`);
  await page.getByRole("heading", { name: "Process workspace" }).waitFor();
  await page.goto(`${origin}${legacyPath}`);
  await page.getByRole("heading", { name: "Dependency & provenance" }).waitFor();
  assert.equal(new URL(page.url()).pathname, "/design/lineage", `${legacyPath} must canonicalize to Lineage`);
  await page.goBack();
  await page.getByRole("heading", { name: "Process workspace" }).waitFor();
  assert.equal(new URL(page.url()).pathname, "/design/process", "replace alias must not leave flowsheet as a history entry");
}

for (const path of ["/design/model", "/design/process", "/design/results", "/design/lineage", "/design/process"]) {
  await page.goto(`${origin}${path}`);
  assert.equal(new URL(page.url()).pathname, path);
}
await page.getByRole("heading", { name: "Process workspace" }).waitFor();

await page.setViewportSize({ width: 640, height: 900 });
await page.waitForTimeout(150);
const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
assert.ok(overflow <= 1, `unexpected page-level horizontal overflow: ${overflow}px`);

await page.getByRole("button", { name: "Show context" }).click();
await page.getByRole("heading", { name: "Jarvis & Properties" }).waitFor();
const propertiesTab = page.getByRole("tab", { name: "Properties" });
await propertiesTab.waitFor();
await propertiesTab.click();
await page.getByRole("heading", { name: "Properties", exact: true }).waitFor();
assert.equal(await page.getByText(/selected BLUECAD part/i).count(), 0, "Compact Process context must remain target-neutral");
await page.getByRole("button", { name: "Close sidecar" }).click();

assert.equal(mutationCalls, 0, "058d route/scaffold navigation must not mutate backend state");
assert.equal(runnerCalls, 0, "058d scaffold must not call runner APIs");
assert.equal(providerCalls, 0, "058d scaffold must not call provider/thread APIs");
assert.deepEqual(pageErrors, [], `unhandled page errors: ${pageErrors.join(" | ")}`);
assert.deepEqual(consoleErrors, [], `console errors: ${consoleErrors.join(" | ")}`);

console.log("058D_BROWSER_EVIDENCE_PASS", { mutationCalls, runnerCalls, providerCalls, overflow, aliasReplace: "pass" });
await browser.close();
