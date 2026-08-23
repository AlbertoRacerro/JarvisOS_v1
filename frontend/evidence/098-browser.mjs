import { chromium } from "playwright";
import assert from "node:assert/strict";

const now = "2026-08-23T10:00:00+00:00";
const later = "2026-08-23T10:01:00+00:00";
const newest = "2026-08-23T10:02:00+00:00";

const base = (id, workspace_id, name, value, unit) => ({
  id, workspace_id, name, symbol: null, value, unit,
  value_status: "accepted", value_min: null, value_max: null,
  source_ref: "Operator", confidence: 1, status: "accepted", notes: null,
  supersedes_parameter_id: null, created_at: now, updated_at: now,
  lifecycle_state: "active"
});

const state = {
  ws1: [
    base("p-edit", "ws1", "Flow rate", "12", "kg/s"),
    base("p-dependent", "ws1", "Dependent parameter", "20", "bar"),
    base("p-free", "ws1", "Free parameter", "5", "m")
  ],
  ws2: [base("p-ws2", "ws2", "Workspace two parameter", "2", "m")]
};

let lastConfirm = "";
let delayedResolve = null;
let delayWorkspaceMutation = false;

function currentRows(ws, includeNoncurrent) {
  const rows = state[ws] ?? [];
  return includeNoncurrent ? rows : rows.filter((row) => row.lifecycle_state === "active");
}

function findParameter(id) {
  for (const rows of Object.values(state)) {
    const row = rows.find((item) => item.id === id);
    if (row) return row;
  }
  return null;
}

const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({ viewport: { width: 1280, height: 900 }, colorScheme: "light", reducedMotion: "no-preference" });
const page = await context.newPage();
page.on("dialog", async (dialog) => { lastConfirm = dialog.message(); await dialog.accept(); });

await page.route("http://127.0.0.1:8000/**", async (route) => {
  const request = route.request();
  const url = new URL(request.url());
  const json = (body, status = 200) => route.fulfill({ status, contentType: "application/json", headers: { "Access-Control-Allow-Origin": "*" }, body: JSON.stringify(body) });

  if (request.method() === "GET" && url.pathname === "/workspaces") return json([
    { id: "ws1", name: "Evidence one", slug: "evidence-one", status: "active", created_at: now, updated_at: now },
    { id: "ws2", name: "Evidence two", slug: "evidence-two", status: "active", created_at: now, updated_at: now }
  ]);

  const wsList = url.pathname.match(/^\/workspaces\/(ws1|ws2)\/(model-specs|assumptions|decisions|parameters)$/);
  if (request.method() === "GET" && wsList) {
    const [, ws, kind] = wsList;
    if (kind !== "parameters") return json([]);
    return json(currentRows(ws, url.searchParams.get("include_noncurrent") === "true"));
  }

  const patch = url.pathname.match(/^\/parameters\/([^/]+)$/);
  if (request.method() === "PATCH" && patch) {
    const row = findParameter(patch[1]);
    if (!row) return json({ detail: { code: "parameter_not_found", message: "Parameter not found" } }, 404);
    const payload = request.postDataJSON();
    if (payload.name === "Stale attempt") {
      Object.assign(row, { name: "Server truth", value: "16", updated_at: newest });
      return json({ detail: { code: "parameter_stale", message: "Stale canonical edit" } }, 409);
    }
    if (delayWorkspaceMutation) {
      await new Promise((resolve) => { delayedResolve = resolve; });
    }
    Object.assign(row, payload, { updated_at: later });
    delete row.expected_updated_at;
    delete row.workspace_id;
    row.workspace_id = payload.workspace_id;
    return json(row);
  }

  const lifecycle = url.pathname.match(/^\/parameters\/([^/]+)\/lifecycle$/);
  if (request.method() === "POST" && lifecycle) {
    const row = findParameter(lifecycle[1]);
    if (!row) return json({ detail: { code: "parameter_not_found", message: "Parameter not found" } }, 404);
    const payload = request.postDataJSON();
    if (row.id === "p-dependent" && ["deactivate", "archive", "delete"].includes(payload.action)) {
      return json({ detail: { code: "parameter_lifecycle_dependents_require_reconciliation", message: "Dependents require reconciliation" } }, 409);
    }
    const target = payload.action === "activate" ? "active" : payload.action === "deactivate" ? "inactive" : payload.action === "archive" ? "archived" : "deleted";
    Object.assign(row, { lifecycle_state: target, updated_at: later });
    return json(row);
  }

  return json({ detail: `Unhandled evidence route ${request.method()} ${url.pathname}` }, 404);
});

await page.goto("http://127.0.0.1:4173/098-evidence.html");
await page.getByRole("heading", { name: "Engineering Data" }).waitFor();
await page.getByText("Flow rate", { exact: true }).first().waitFor();
assert.ok(await page.getByText("Active", { exact: true }).count() > 0, "normal view exposes lifecycle humanly");

// Canonical edit must be explicit, server-backed and refreshed from returned truth.
await page.getByText("Flow rate", { exact: true }).first().click();
await page.getByRole("button", { name: "Edit canonical Parameter" }).click();
await page.getByText(/Canonical edit\./).waitFor();
assert.match(await page.getByText(/Saving changes the project Parameter/).textContent(), /server-side compare-and-swap/);
await page.getByLabel("Value", { exact: true }).fill("15");
await page.getByRole("button", { name: "Save canonical Parameter" }).click();
await page.getByText(/was updated in canonical Engineering Data/).waitFor();
await page.getByText("15", { exact: true }).waitFor();

// Stale edit must fail closed and refresh current server truth rather than silently retry.
await page.getByRole("button", { name: "Edit canonical Parameter" }).click();
await page.getByLabel("Name", { exact: true }).fill("Stale attempt");
await page.getByRole("button", { name: "Save canonical Parameter" }).click();
await page.getByText(/changed after you reviewed it/).waitFor();
await page.getByText("Server truth", { exact: true }).first().waitFor();
await page.getByText("16", { exact: true }).waitFor();

// Canonical dependent rejection stays visible and leaves lifecycle unchanged.
await page.getByText("Dependent parameter", { exact: true }).first().click();
lastConfirm = "";
await page.getByRole("button", { name: "Deactivate" }).click();
await page.getByText(/Current dependent records prevent a truthful canonical change/).waitFor();
assert.match(lastConfirm, /Dependent parameter/);
assert.match(lastConfirm, /current canonical use/);
await page.getByText("Active", { exact: true }).last().waitFor();

// No-dependent transition removes the Parameter from current view, explicit history reveals it.
await page.getByText("Free parameter", { exact: true }).first().click();
lastConfirm = "";
await page.getByRole("button", { name: "Deactivate" }).click();
await page.getByText(/Free parameter is now Inactive/).waitFor();
assert.match(lastConfirm, /Free parameter/);
assert.match(lastConfirm, /valid alternative/);
await page.waitForTimeout(100);
assert.equal(await page.getByText("Free parameter", { exact: true }).count(), 0, "inactive row leaves normal current view");
await page.getByLabel(/Advanced\/Audit: show noncurrent Parameters/).check();
await page.getByText("Free parameter", { exact: true }).first().waitFor();
await page.getByText("Inactive", { exact: true }).first().waitFor();

// Supersede must not fabricate a replacement; V0 visibly routes conceptually to existing authority.
await page.getByText("Server truth", { exact: true }).first().click();
const supersede = page.locator("p", { hasText: "Supersede:" }).first();
await supersede.waitFor();
assert.match(await supersede.textContent(), /existing Parameter replacement proposal\/review authority/);
assert.match(await supersede.textContent(), /does not invent a replacement record/);

// Workspace switch while a mutation is in flight cannot project the late result into the new workspace.
await page.getByRole("button", { name: "Edit canonical Parameter" }).click();
await page.getByLabel("Value", { exact: true }).fill("99");
delayWorkspaceMutation = true;
const save = page.getByRole("button", { name: "Save canonical Parameter" });
await save.click();
await page.getByLabel("Workspace").selectOption("ws2");
await page.getByText("Workspace two parameter", { exact: true }).first().waitFor();
delayedResolve?.();
await page.waitForTimeout(150);
assert.equal(await page.getByText(/was updated in canonical Engineering Data/).count(), 0, "late mutation response cannot apply notice to new workspace");
assert.equal(await page.getByTestId("evidence-workspace").textContent(), "ws2");

// Keyboard, compact/effective-200%-like containment and dark/reduced-motion rendering.
const workspaceTwoRow = page.getByRole("button", { name: /Workspace two parameter/ }).first();
await workspaceTwoRow.focus();
assert.equal(await page.evaluate(() => document.activeElement?.tagName), "BUTTON");
const compact = await browser.newContext({ viewport: { width: 640, height: 900 }, colorScheme: "dark", reducedMotion: "reduce" });
const compactPage = await compact.newPage();
await compactPage.route("http://127.0.0.1:8000/**", async (route) => {
  const request = route.request(); const url = new URL(request.url());
  const fulfill = (body) => route.fulfill({ status: 200, contentType: "application/json", headers: { "Access-Control-Allow-Origin": "*" }, body: JSON.stringify(body) });
  if (request.method() === "GET" && url.pathname === "/workspaces") return fulfill([{ id: "ws1", name: "Evidence one", slug: "evidence-one", status: "active", created_at: now, updated_at: now }]);
  if (request.method() === "GET" && url.pathname === "/workspaces/ws1/parameters") return fulfill(currentRows("ws1", false));
  if (request.method() === "GET" && /^\/workspaces\/ws1\/(model-specs|assumptions|decisions)$/.test(url.pathname)) return fulfill([]);
  return fulfill([]);
});
await compactPage.goto("http://127.0.0.1:4173/098-evidence.html");
await compactPage.getByRole("heading", { name: "Engineering Data" }).waitFor();
const overflow = await compactPage.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
assert.ok(overflow <= 1, `no page-level horizontal overflow at compact/effective-200% width, got ${overflow}`);
assert.equal(await compactPage.evaluate(() => matchMedia("(prefers-color-scheme: dark)").matches), true);
assert.equal(await compactPage.evaluate(() => matchMedia("(prefers-reduced-motion: reduce)").matches), true);
await compact.close();

console.log("098_BROWSER_EVIDENCE_PASS");
await browser.close();
