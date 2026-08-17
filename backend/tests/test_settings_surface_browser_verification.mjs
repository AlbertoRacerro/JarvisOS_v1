import { chromium } from "playwright";
import assert from "node:assert/strict";

const app = "http://127.0.0.1:5173";
const api = "http://127.0.0.1:8000";
const now = "2026-08-17T12:00:00Z";

const baseSettings = {
  policy_mode: "local_only",
  monthly_api_budget_usd: 10,
  api_spend_month_to_date_usd: 1.25,
  paid_ai_enabled: false,
  default_ai_provider: "fake",
  default_ai_model: "fake-model",
  provider_mode: "fake",
  use_fake_provider_when_budget_zero: true,
  scaleway_enabled: false,
  scaleway_smoke_test_enabled: false,
  scaleway_live_smoke_test_enabled: false,
  scaleway_monthly_token_cap: 1000,
  scaleway_hard_stop_token_cap: 2000,
  scaleway_free_tier_reference_tokens: 500,
  scaleway_input_tokens_month_to_date: 20,
  scaleway_output_tokens_month_to_date: 30,
  usage_total_tokens: 50,
  smoke_test_mode_enabled: false,
  max_direct_continuations: 4,
  max_direct_continuations_min: 0,
  max_direct_continuations_max: 16,
  direct_continuation_policy_version: "v1",
  updated_at: now,
};
const baseStatus = {
  policy_mode: "local_only",
  ai_enabled: true,
  active_provider_mode: "fake",
  provider_mode: "fake",
  provider_id: "fake-provider",
  adapter_enabled: true,
  fake_provider_enabled: true,
  scaleway_enabled: false,
  scaleway_api_key_configured: true,
  scaleway_provider_implementation: "openai-compatible",
  paid_ai_enabled: false,
  monthly_api_budget_usd: 10,
  spend_month_to_date_usd: 1.25,
  scaleway_smoke_test_enabled: false,
  scaleway_live_smoke_test_enabled: false,
  scaleway_monthly_token_cap: 1000,
  scaleway_hard_stop_token_cap: 2000,
  scaleway_free_tier_reference_tokens: 500,
  scaleway_input_tokens_month_to_date: 20,
  scaleway_output_tokens_month_to_date: 30,
  usage_total_tokens: 50,
  budget_status: "within_budget",
  credential_status: "configured",
  external_calls_allowed: false,
  blocking_reason: "<img src=x onerror=alert('owned')> blocked by policy",
  default_ai_provider: "fake",
  default_ai_model: "fake-model",
};
const system = {
  environment: "development",
  data_root_exists: true,
  database: { ready: true },
  ai: { provider_configured: true },
};
const secretPersisted = {
  key_present: true,
  source: "secure_persisted",
  effective_source: "secure_persisted",
  persisted_state: "usable",
  storage_mode: "secure_persisted",
  last_updated_at: now,
  reason_code: null,
  masked_preview: "SHOULD-NOT-RENDER-SECRET",
};

let canonical = structuredClone(baseSettings);
let secret = structuredClone(secretPersisted);
let putBodies = [];
let credentialPosts = [];
let credentialDeletes = 0;
let settingsGetCount = 0;
let failNextCanonicalReread = false;
let secretErrorOnce = false;
let heldPutResolve = null;
const unexpectedExternal = [];
const unexpectedProviderCalls = [];

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 640, height: 720 }, reducedMotion: "reduce" });
page.on("request", (request) => {
  const url = request.url();
  if (!url.startsWith(app) && !url.startsWith(api) && !url.startsWith("data:") && !url.startsWith("blob:")) unexpectedExternal.push(url);
  if (/provider|scaleway.*chat|ai\/tasks\/run/i.test(url)) unexpectedProviderCalls.push(url);
});
page.on("dialog", async (dialog) => { throw new Error(`unexpected dialog: ${dialog.message()}`); });
page.on("pageerror", (error) => { throw error; });

await page.route(`${api}/**`, async (route) => {
  const req = route.request();
  const url = new URL(req.url());
  const path = url.pathname;
  const method = req.method();
  const json = (status, body) => route.fulfill({ status, contentType: "application/json", body: JSON.stringify(body) });

  if (method === "GET" && path === "/workspaces") return json(200, []);
  if (method === "GET" && path === "/ai/settings") {
    settingsGetCount += 1;
    if (failNextCanonicalReread && settingsGetCount > 1) {
      failNextCanonicalReread = false;
      return json(503, { detail: { code: "canonical_read_failed", message: "temporary reread failure" } });
    }
    return json(200, canonical);
  }
  if (method === "GET" && path === "/ai/status") return json(200, { ...baseStatus, ...canonical });
  if (method === "GET" && path === "/secrets/scaleway/status") return json(200, secret);
  if (method === "GET" && path === "/system/info") return json(200, system);

  if (method === "PUT" && path === "/ai/settings") {
    const body = req.postDataJSON();
    putBodies.push(body);
    if (body.monthly_api_budget_usd === 77) {
      return new Promise((resolve) => {
        heldPutResolve = () => {
          canonical = { ...canonical, ...body };
          resolve(json(200, canonical));
        };
      });
    }
    canonical = { ...canonical, ...body };
    return json(200, canonical);
  }

  if (method === "POST" && path === "/secrets/scaleway/api-key") {
    const body = req.postDataJSON();
    credentialPosts.push(body);
    if (secretErrorOnce) {
      secretErrorOnce = false;
      return json(409, { detail: { code: "scaleway_api_key_environment_override", message: "Environment credential owns the effective value.", private_debug: "DO-NOT-PROJECT" } });
    }
    secret = { ...secretPersisted, key_present: true };
    return json(200, secret);
  }
  if (method === "DELETE" && path === "/secrets/scaleway/api-key") {
    credentialDeletes += 1;
    secret = { ...secretPersisted, key_present: false, effective_source: "none", persisted_state: "absent", storage_mode: "none" };
    return json(200, secret);
  }

  if (path.startsWith("/ai/threads") || path.startsWith("/ai/context/packs")) {
    if (method === "GET" && path === "/ai/threads") return json(200, { threads: [] });
    if (method === "POST" && path === "/ai/context/packs/preview") return json(200, { context_digest: `sha256:${"a".repeat(64)}`, context_sources_manifest: [], char_count: 0, estimated_token_count: 0, included_count: 0, dropped_count: 0, budget_chars: 4000 });
    return json(404, { detail: "sidecar mock" });
  }
  return json(404, { detail: `unmocked ${method} ${path}` });
});

const field = (name) => page.getByLabel(name, { exact: false });
async function saveWithinLabel(labelText) {
  const label = page.locator("label").filter({ hasText: labelText }).first();
  await label.getByRole("button", { name: "Save" }).click();
  await page.getByText("Saved. Canonical settings reloaded.").waitFor();
}

await page.goto(`${app}/settings`);
await page.getByRole("heading", { name: "Settings", level: 1 }).waitFor();
await page.getByText("SHOULD-NOT-RENDER-SECRET").waitFor({ state: "detached" });
assert.equal(await page.locator("img").count(), 0, "hostile status text must render inertly");
assert.ok((await page.locator("body").innerText()).includes("<img src=x"), "hostile status text should remain inert text");

const cases = [
  ["Monthly API budget", "monthly_api_budget_usd", "12.5"],
  ["Monthly token cap", "scaleway_monthly_token_cap", "1200"],
  ["Hard-stop token cap", "scaleway_hard_stop_token_cap", "2400"],
  ["Direct continuations", "max_direct_continuations", "6"],
];
for (const [labelText, key, value] of cases) {
  const input = field(labelText);
  await input.fill(value);
  const before = putBodies.length;
  await saveWithinLabel(labelText);
  assert.equal(putBodies.length, before + 1, `${key} must perform one write`);
  assert.deepEqual(putBodies.at(-1), { [key]: Number(value) }, `${key} must use one-field payload`);
}

for (const [labelText, key] of [["Paid AI enabled", "paid_ai_enabled"], ["Scaleway enabled", "scaleway_enabled"]]) {
  const input = field(labelText);
  const next = !(await input.isChecked());
  if (next) await input.check(); else await input.uncheck();
  const before = putBodies.length;
  await saveWithinLabel(labelText);
  assert.equal(putBodies.length, before + 1, `${key} must perform one write`);
  assert.deepEqual(putBodies.at(-1), { [key]: next }, `${key} must use one-field payload`);
}

const direct = field("Direct continuations");
await direct.fill("17");
const beforeInvalid = putBodies.length;
await page.locator("label").filter({ hasText: "Direct continuations" }).getByRole("button", { name: "Save" }).click();
await page.getByText("Direct continuations must be an integer from 0 to 16.").waitFor();
assert.equal(putBodies.length, beforeInvalid, "invalid input must not write");

const budget = field("Monthly API budget");
await budget.fill("77");
const budgetLabel = page.locator("label").filter({ hasText: "Monthly API budget" }).first();
await budgetLabel.getByRole("button", { name: "Save" }).click();
await page.waitForFunction(() => [...document.querySelectorAll("button")].some((b) => b.textContent === "Save" && b.disabled));
const writesDuringHold = putBodies.length;
await budgetLabel.getByRole("button", { name: "Save" }).evaluate((button) => button.click());
await page.waitForTimeout(50);
assert.equal(putBodies.length, writesDuringHold, "busy lock must suppress duplicate settings write");
heldPutResolve();
await page.getByText("Saved. Canonical settings reloaded.").waitFor();

await budget.fill("88");
failNextCanonicalReread = true;
await budgetLabel.getByRole("button", { name: "Save" }).click();
await page.getByText(/State uncertain/i).first().waitFor();
assert.equal(await budgetLabel.getByRole("button", { name: "Save" }).isDisabled(), true, "uncertain state must block mutations");
const beforeBlocked = putBodies.length;
await budgetLabel.getByRole("button", { name: "Save" }).evaluate((button) => button.click());
await page.waitForTimeout(30);
assert.equal(putBodies.length, beforeBlocked, "uncertain state must not retry/write");
await page.getByRole("button", { name: "Reload" }).click();
await page.getByText("Canonical state reloaded.").waitFor();

const secretInput = field("Replace API key");
secretErrorOnce = true;
await secretInput.fill("super-secret-value");
await page.getByRole("button", { name: "Store securely" }).click();
await page.getByText(/scaleway_api_key_environment_override/).waitFor();
assert.equal(await secretInput.inputValue(), "", "credential input must clear after settlement");
const bodyText = await page.locator("body").innerText();
assert.ok(!bodyText.includes("super-secret-value"), "credential must never be rendered after submit");
assert.ok(!bodyText.includes("DO-NOT-PROJECT"), "private error detail must not be projected");
assert.equal(credentialPosts.length, 1);

secret = { ...secretPersisted, effective_source: "environment", source: "environment", storage_mode: "environment" };
await page.reload();
await page.getByRole("heading", { name: "Settings", level: 1 }).waitFor();
await page.getByText(/Environment credentials override persisted credentials/i).waitFor();
assert.equal(await field("Replace API key").isDisabled(), true, "environment override must disable replacement");

secret = structuredClone(secretPersisted);
await page.reload();
await page.getByRole("heading", { name: "Settings", level: 1 }).waitFor();
const deleteTrigger = page.getByRole("button", { name: "Delete persisted credential" });
await deleteTrigger.focus();
await deleteTrigger.click();
const deleteButton = page.getByRole("group", { name: "Confirm credential deletion" }).getByRole("button", { name: "Delete" });
await page.waitForFunction(() => document.activeElement?.textContent?.trim() === "Delete");
assert.equal(await deleteButton.evaluate((el) => el === document.activeElement), true, "delete confirmation must receive focus");
await page.keyboard.press("Escape");
await deleteTrigger.waitFor();
await page.waitForFunction(() => document.activeElement?.textContent?.trim() === "Delete persisted credential");
await deleteTrigger.click();
await deleteButton.click();
await page.getByText("Credential deleted. Canonical secure status reloaded.").waitFor();
assert.equal(credentialDeletes, 1, "credential delete must execute once");
await page.waitForFunction(() => document.activeElement?.getAttribute("type") === "password");

assert.ok(await page.getByText("Advanced diagnostics").isVisible());
assert.ok(await page.locator('a[href="/legacy/system-status"]').count() + await page.locator('a[href="/legacy/ai-draft"]').count() >= 1, "legacy diagnostics links must remain reachable");

const showContext = page.getByRole("button", { name: "Show context" });
await showContext.click();
await page.getByTestId("jarvis-sidecar").waitFor();

const overflow = await page.evaluate(() => ({ root: document.documentElement.scrollWidth - document.documentElement.clientWidth, body: document.body.scrollWidth - document.body.clientWidth }));
assert.ok(overflow.root <= 1 && overflow.body <= 1, `global overflow detected at effective-200%-like width: ${JSON.stringify(overflow)}`);

assert.deepEqual(unexpectedExternal, [], `unexpected external requests: ${unexpectedExternal.join(", ")}`);
assert.deepEqual(unexpectedProviderCalls, [], `unexpected provider/task calls: ${unexpectedProviderCalls.join(", ")}`);

await browser.close();
console.log("SETTINGS-1 browser proof passed");
