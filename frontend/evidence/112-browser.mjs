import assert from "node:assert/strict";
import fs from "node:fs/promises";
import path from "node:path";
import { chromium, firefox } from "playwright";

const PRODUCT_HEAD = "e4921cdbff74a390aa03123f28f048aea283064e";
const BASE_URL = process.env.JARVISOS_EVIDENCE_URL || "http://127.0.0.1:4173";
const API_ORIGIN = "http://127.0.0.1:8000";
const OUT_DIR = process.env.JARVISOS_EVIDENCE_DIR || "evidence/112-artifacts";
const VIEWPORT = { width: 1600, height: 1000 };
const WORKSPACE_ID = "ws-112-browser-proof";
const R1 = "rev-r1-reconciled";
const W1 = "rev-w1-working";
const OLD = "rev-old-superseded";
const W2 = "rev-w2-working";

await fs.mkdir(OUT_DIR, { recursive: true });

function revision({ id, state, parent = R1, parentKind = "reconciled", digest, snapshot = null, supersededBy = null, origin = "operator" }) {
  return {
    id,
    workspace_id: WORKSPACE_ID,
    parent_revision_id: parent,
    parent_kind: parentKind,
    state,
    change_set_digest: `change-${id}`,
    operations: [],
    projected_state_digest: digest,
    origin,
    created_at: "2026-08-30T00:00:00Z",
    accepted_at: "2026-08-30T00:00:01Z",
    superseded_by_revision_id: supersededBy,
    reconciled_snapshot_id: snapshot
  };
}

const initialRevisions = [
  revision({ id: W1, state: "working", digest: "basis-w1" }),
  revision({ id: R1, state: "reconciled", parent: null, parentKind: "reconciled", digest: "basis-r1", snapshot: "snap-r1" }),
  revision({ id: OLD, state: "superseded", digest: "basis-old", supersededBy: W1 })
];

const workspace = {
  id: WORKSPACE_ID,
  name: "112 Browser Evidence Workspace",
  slug: "112-browser-evidence",
  description: "Proof-only fixture; never production data",
  status: "active",
  created_at: "2026-08-30T00:00:00Z",
  updated_at: "2026-08-30T00:00:00Z"
};
const requirement = {
  id: "req-required",
  workspace_id: WORKSPACE_ID,
  statement: "Proof-only exact Process validation requirement",
  rationale: "Browser evidence fixture",
  status: "active",
  notes: null,
  schema_version: 1,
  created_at: "2026-08-30T00:00:00Z",
  updated_at: "2026-08-30T00:00:00Z"
};
const parameter = { id: "param-proof", workspace_id: WORKSPACE_ID, name: "Proof parameter", symbol: "x", value: "12", unit: "kg", value_status: "known", status: "active", lifecycle_state: "active" };
const decision = { id: "decision-proof", workspace_id: WORKSPACE_ID, title: "Proof decision", decision_text: "Proof-only", rationale: "Browser fixture", status: "active" };
const modelSpec = { id: "model-proof", workspace_id: WORKSPACE_ID, title: "Proof model specification", engineering_question: "Does exact lifecycle context remain inspectable?", scope: "Browser proof only", status: "active", maturity_status: "draft", schema_version: 1, created_at: "2026-08-30T00:00:00Z", updated_at: "2026-08-30T00:00:00Z" };

function revalidation(revisionId) {
  if (revisionId === W2) {
    return {
      working_revision_id: W2,
      complete: true,
      mandatory_requirement_ids: [],
      current_validation_ids: [],
      blocking_requirement_ids: [],
      known_fail_requirement_ids: [],
      recomputation_required: [],
      selected_validation_set_digest: "validation-set-w2",
      diagnostics: []
    };
  }
  return {
    working_revision_id: W1,
    complete: false,
    mandatory_requirement_ids: ["req-required"],
    current_validation_ids: ["val-current-w1"],
    blocking_requirement_ids: ["req-required"],
    known_fail_requirement_ids: [],
    recomputation_required: ["req-required"],
    selected_validation_set_digest: "validation-set-w1",
    diagnostics: ["missing_exact_process_evidence:req-required"]
  };
}

const cors = {
  "access-control-allow-origin": "*",
  "access-control-allow-methods": "GET,POST,PUT,DELETE,OPTIONS",
  "access-control-allow-headers": "content-type"
};
const json = (route, body, status = 200) => route.fulfill({ status, headers: { ...cors, "content-type": "application/json" }, body: JSON.stringify(body) });

async function installApiFixtures(page) {
  let revisions = structuredClone(initialRevisions);
  let draft = null;
  await page.route(`${API_ORIGIN}/**`, async (route) => {
    const req = route.request();
    const url = new URL(req.url());
    const method = req.method();
    const p = url.pathname;
    if (method === "OPTIONS") return route.fulfill({ status: 204, headers: cors });
    if (method === "GET" && p === "/workspaces") return json(route, [workspace]);
    if (method === "GET" && p === `/workspaces/${WORKSPACE_ID}/requirements`) return json(route, [requirement]);
    if (method === "GET" && p === `/workspaces/${WORKSPACE_ID}/parameters`) return json(route, [parameter]);
    if (method === "GET" && p === `/workspaces/${WORKSPACE_ID}/decisions`) return json(route, [decision]);
    if (method === "GET" && p === `/workspaces/${WORKSPACE_ID}/model-specs`) return json(route, [modelSpec]);
    if (method === "GET" && p === `/project-knowledge/workspaces/${WORKSPACE_ID}/revisions`) return json(route, revisions);
    const revalidationMatch = p.match(new RegExp(`^/project-knowledge/workspaces/${WORKSPACE_ID}/revisions/([^/]+)/revalidation$`));
    if (method === "GET" && revalidationMatch) return json(route, revalidation(revalidationMatch[1]));
    if (method === "POST" && p === "/project-knowledge/drafts") {
      const body = JSON.parse(req.postData() || "{}");
      draft = {
        id: "draft-browser-proof",
        workspace_id: WORKSPACE_ID,
        parent_revision_id: body.parent_revision_id ?? null,
        parent_kind: body.parent_kind,
        revision_token: "draft-token-1",
        operations: body.operations || [],
        preview_digest: null,
        created_at: "2026-08-30T00:01:00Z",
        updated_at: "2026-08-30T00:01:00Z"
      };
      return json(route, draft);
    }
    if (method === "GET" && p === `/project-knowledge/workspaces/${WORKSPACE_ID}/drafts/draft-browser-proof/impact`) {
      return json(route, {
        draft_id: "draft-browser-proof",
        draft_revision_token: "draft-token-1",
        parent_kind: draft?.parent_kind || "reconciled",
        parent_revision_id: draft?.parent_revision_id ?? R1,
        ancestor_revision_ids: [R1],
        affected_refs: ["requirement:provisional-browser-proof"],
        owner_tokens: { [`revision:${R1}`]: "basis-r1" },
        applicability_refs: [],
        recomputation_required: [],
        diagnostics: [],
        complete: true,
        digest: "impact-digest-browser-proof"
      });
    }
    if (method === "POST" && p === "/project-knowledge/approvals") {
      revisions = [revision({ id: W2, state: "working", digest: "basis-w2" }), ...revisions];
      return json(route, { request_id: "approval-browser-proof", state: "success", outcome: "working_revision_created", working_revision_id: W2, failure_code: null });
    }
    if (method === "POST" && p.endsWith("/state")) return json(route, revisions.find((item) => item.id === W1) || revisions[0]);
    if (method === "POST" && p === "/project-knowledge/reconcile") return json(route, { request_id: "reconcile-browser-proof", state: "success", outcome: "reconciled", resulting_snapshot_id: "snap-browser-proof", canonical_id_map: {}, failure_code: null });
    return json(route, { detail: `unhandled proof-only route ${method} ${p}` }, 404);
  });
}

async function noOverflow(page) {
  const dims = await page.evaluate(() => ({ scroll: document.documentElement.scrollWidth, client: document.documentElement.clientWidth, body: document.body.scrollWidth }));
  assert.ok(dims.scroll <= dims.client + 2, `document overflow ${dims.scroll}>${dims.client}`);
  assert.ok(dims.body <= dims.client + 2, `body overflow ${dims.body}>${dims.client}`);
}

async function screenshot(page, engine, name, report) {
  const file = `${engine}-${name}-${VIEWPORT.width}x${VIEWPORT.height}.png`;
  await page.screenshot({ path: path.join(OUT_DIR, file), fullPage: true });
  report.screenshots.push(file);
}

async function proveProjectBasis(page, engine, report) {
  const errors = [];
  page.on("pageerror", (err) => errors.push(String(err)));
  await installApiFixtures(page);
  await page.goto(`${BASE_URL}/memory/project-basis`, { waitUntil: "networkidle" });
  assert.equal(new URL(page.url()).pathname, "/memory/project-basis");
  assert.ok(await page.getByText("Current reconciled snapshot", { exact: false }).count());
  assert.ok(await page.getByText("Working revisions · 1", { exact: false }).count());
  assert.ok(await page.getByText("Deterministic revalidation", { exact: true }).count());
  assert.ok(await page.getByText("Blocked", { exact: true }).count());
  assert.ok(await page.getByText("req-required", { exact: false }).count());
  assert.ok(await page.getByText("missing_exact_process_evidence:req-required", { exact: false }).count());
  const reconcile = page.getByRole("button", { name: "Final reconcile", exact: true });
  assert.equal(await reconcile.isDisabled(), true, "blocked revalidation must fail closed");
  const contextLink = page.getByRole("link", { name: "Open Process with context", exact: true });
  const href = await contextLink.getAttribute("href");
  assert.ok(href, "recomputation context link missing");
  const contextUrl = new URL(href, BASE_URL);
  assert.equal(contextUrl.pathname, "/design/process");
  assert.equal(contextUrl.searchParams.get("project_knowledge_revision_id"), W1);
  assert.equal(contextUrl.searchParams.get("project_knowledge_basis_digest"), "basis-w1");
  assert.equal(contextUrl.searchParams.get("project_knowledge_validation_set_digest"), "validation-set-w1");
  assert.deepEqual(contextUrl.searchParams.getAll("project_knowledge_requirement_id"), ["req-required"]);
  await screenshot(page, engine, "project-basis-blocked-recomputation", report);

  const select = page.getByRole("combobox", { name: "Project Knowledge revision" });
  await select.selectOption(OLD);
  await page.getByText("State · superseded", { exact: true }).waitFor();
  assert.ok(await page.getByText(`Superseded by · ${W1}`, { exact: true }).count());
  assert.equal(await page.getByRole("textbox", { name: "Requirement statement" }).isDisabled(), true, "superseded revision must be inspect-only");
  await screenshot(page, engine, "project-basis-superseded-history", report);

  await select.selectOption(R1);
  await page.getByText("State · reconciled", { exact: true }).waitFor();
  const requirementInput = page.getByRole("textbox", { name: "Requirement statement" });
  assert.equal(await requirementInput.isEnabled(), true, "historical reconciled revision must remain selectable as branch basis");
  await requirementInput.fill("Browser-proof staged requirement");
  await page.getByRole("button", { name: "Preview impact", exact: true }).click();
  await page.getByText("Impact complete", { exact: true }).waitFor();
  assert.ok(await page.getByText("Impact digest · impact-digest-browser-proof", { exact: true }).count());
  await screenshot(page, engine, "project-basis-impact-preview", report);
  await page.getByLabel("Project Knowledge", { exact: true }).getByRole("button", { name: "Approve all", exact: true }).click();
  await page.getByText(`Revision · ${W2}`, { exact: true }).waitFor();
  assert.ok(await page.getByText("State · working", { exact: true }).count());
  assert.ok(await page.getByText("Terminal", { exact: true }).count());
  await screenshot(page, engine, "project-basis-post-approve-working", report);
  await noOverflow(page);
  assert.deepEqual(errors, [], `Project Basis page errors: ${errors.join(" | ")}`);
  report.assertions.push("project-basis: exact working/reconciled/superseded lifecycle visible");
  report.assertions.push("project-basis: blocked revalidation fails closed and exact recomputation context is encoded");
  report.assertions.push("project-basis: historical reconciled revision can stage/preview/approve a new working revision");
}

async function proveModels(page, engine, report) {
  const errors = [];
  page.on("pageerror", (err) => errors.push(String(err)));
  await installApiFixtures(page);
  await page.goto(`${BASE_URL}/memory/models`, { waitUntil: "networkidle" });
  assert.equal(new URL(page.url()).pathname, "/memory/models");
  assert.ok(await page.getByText("Proof model specification", { exact: true }).count());
  const select = page.getByRole("combobox", { name: "Project Knowledge revision" });
  const values = await select.locator("option").evaluateAll((options) => options.map((option) => option.value));
  for (const id of [W1, R1, OLD]) assert.ok(values.includes(id), `Models lifecycle missing ${id}`);
  await select.selectOption(OLD);
  await page.getByText("State · superseded", { exact: true }).waitFor();
  assert.equal(await page.getByRole("textbox", { name: "Requirement statement" }).count(), 0, "Models lifecycle projection must be read-only");
  assert.equal(await page.getByRole("button", { name: "Final reconcile", exact: true }).count(), 0, "Models lifecycle projection must not expose reconcile mutation");
  await screenshot(page, engine, "models-readonly-history", report);
  await noOverflow(page);
  assert.deepEqual(errors, [], `Models page errors: ${errors.join(" | ")}`);
  report.assertions.push("models: exact Project Knowledge lifecycle/history is visible read-only");
  report.assertions.push("models: no Project Knowledge mutation controls are exposed");
}

const report = {
  productHead: PRODUCT_HEAD,
  generatedAt: new Date().toISOString(),
  proofMode: "evidence-branch Playwright with deterministic browser-only API fixtures; production runtime files unchanged",
  viewport: VIEWPORT,
  engines: [],
  routes: ["/memory/project-basis", "/memory/models"],
  screenshots: [],
  assertions: [],
  status: "PASS"
};

for (const engine of [{ name: "chromium", impl: chromium }, { name: "firefox", impl: firefox }]) {
  const browser = await engine.impl.launch({ headless: true });
  try {
    const context = await browser.newContext({ viewport: VIEWPORT, reducedMotion: "reduce" });
    const projectBasis = await context.newPage();
    await proveProjectBasis(projectBasis, engine.name, report);
    await projectBasis.close();
    const models = await context.newPage();
    await proveModels(models, engine.name, report);
    await models.close();
    await context.close();
    report.engines.push(engine.name);
  } finally {
    await browser.close();
  }
}

assert.deepEqual(report.engines, ["chromium", "firefox"]);
assert.equal(report.screenshots.length, 10, "five required screenshots per browser expected");
await fs.writeFile(path.join(OUT_DIR, "manifest.json"), `${JSON.stringify(report, null, 2)}\n`);
console.log(`112 browser evidence PASS on exact product head ${PRODUCT_HEAD}: ${report.screenshots.length} screenshots across ${report.engines.join(", ")}`);
