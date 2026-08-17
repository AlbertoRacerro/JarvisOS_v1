import { chromium } from "playwright";
import assert from "node:assert/strict";

const app = "http://127.0.0.1:5173";
const api = "http://127.0.0.1:8000";
const now = "2026-08-17T02:00:00Z";
const digestA = `sha256:${"1".repeat(64)}`;
const digestRoute = `sha256:${"2".repeat(64)}`;
const digestOld = `sha256:${"3".repeat(64)}`;

const workspace = (id, name) => ({ id, name, slug: id, status: "active", created_at: now, updated_at: now });
const summary = (id, workspaceId, title) => ({ id, workspace_id: workspaceId, title, created_at: now, last_activity_at: now });
const interaction = (id, requestId, prompt, assistant, flowId, overrides = {}) => ({
  id,
  request_id: requestId,
  interaction_index: Number(id.replace(/\D/g, "")) || 1,
  user_text: prompt,
  assistant_text: assistant,
  assistant_text_truncated: false,
  flow_id: flowId,
  persistence_state: "complete",
  persistence_error: null,
  flow_state: "succeeded",
  terminal_reason: null,
  attempt_count: 1,
  terminal_attempt_id: `attempt-${id}`,
  proposal_ids: [],
  proposal_count: 0,
  proposals_truncated: false,
  created_at: now,
  updated_at: now,
  ...overrides,
});

const threadsByWorkspace = {
  "workspace-a": [
    summary("thread-x", "workspace-a", "Thread X"),
    summary("thread-y", "workspace-a", "Thread Y"),
    summary("thread-terminal", "workspace-a", "Terminal evidence")
  ],
  "workspace-b": [summary("thread-b", "workspace-b", "Thread B")],
};
const hostileText = '<img data-evil src=x onerror="globalThis.__jarvisInjected=true">';
const details = {
  "thread-x": { ...threadsByWorkspace["workspace-a"][0], interactions: [], has_older: false },
  "thread-y": { ...threadsByWorkspace["workspace-a"][1], interactions: [], has_older: false },
  "thread-terminal": {
    ...threadsByWorkspace["workspace-a"][2],
    interactions: [
      interaction("ix-11", "req-confirm", "needs confirmation", "Awaiting operator confirmation", "flow-confirm", {
        flow_state: "confirmation_required",
        terminal_reason: "confirmation_required"
      }),
      interaction("ix-12", "req-failed", "provider failed", "No durable assistant snapshot.", "flow-failed", {
        flow_state: "failed",
        terminal_reason: "provider_error"
      }),
      interaction("ix-13", "req-capture", "capture uncertainty", hostileText, "flow-capture", {
        persistence_state: "capture_failed",
        persistence_error: "assistant snapshot write failed"
      })
    ],
    has_older: false
  },
  "thread-b": { ...threadsByWorkspace["workspace-b"][0], interactions: [], has_older: false },
};

let submitCount = 0;
let successfulDispatches = 0;
let heldSubmitResolve = null;
let heldSubmitStarted = false;
let holdBList = false;
let bListStarted = false;
let bListResolve = null;
let previewMode = "normal";
let heldPreviewResolve = null;
let heldPreviewStarted = false;
let currentDigest = digestA;
let unexpectedExternal = [];

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 700, height: 760 } });
page.on("pageerror", (error) => { throw error; });
page.on("request", (request) => {
  const url = request.url();
  if (!url.startsWith(app) && !url.startsWith(api) && !url.startsWith("data:") && !url.startsWith("blob:")) unexpectedExternal.push(url);
});

await page.route(`${api}/**`, async (route) => {
  const req = route.request();
  const url = new URL(req.url());
  const path = url.pathname;
  const method = req.method();
  const json = (status, body) => route.fulfill({ status, contentType: "application/json", body: JSON.stringify(body) });

  if (method === "GET" && path === "/workspaces") return json(200, [workspace("workspace-a", "Workspace A"), workspace("workspace-b", "Workspace B")]);
  if (method === "GET" && /^\/workspaces\/[^/]+\/simulation-runs$/.test(path)) return json(200, []);

  if (method === "GET" && path === "/ai/threads") {
    const ws = url.searchParams.get("workspace_id");
    if (ws === "workspace-b" && holdBList) {
      bListStarted = true;
      return new Promise((resolve) => {
        bListResolve = () => resolve(json(200, { threads: threadsByWorkspace["workspace-b"] }));
      });
    }
    return json(200, { threads: threadsByWorkspace[ws] ?? [] });
  }

  const detailMatch = path.match(/^\/ai\/threads\/([^/]+)$/);
  if (method === "GET" && detailMatch) return json(200, details[decodeURIComponent(detailMatch[1])]);

  if (method === "POST" && path === "/ai/context/packs/preview") {
    if (previewMode === "fail") {
      previewMode = "normal";
      return json(500, { detail: "preview failure" });
    }
    if (previewMode === "hold") {
      previewMode = "normal";
      heldPreviewStarted = true;
      return new Promise((resolve) => {
        heldPreviewResolve = () => resolve(json(200, {
          context_digest: digestOld,
          context_sources_manifest: [{ source: "MemoryStore", type: "Assumption", id: "old" }],
          char_count: 10,
          estimated_token_count: 3,
          included_count: 1,
          dropped_count: 0,
          budget_chars: 4000,
        }));
      });
    }
    const ws = req.postDataJSON().workspace_id;
    const digest = ws === "workspace-b" ? digestRoute : currentDigest;
    return json(200, {
      context_digest: digest,
      context_sources_manifest: [{ source: "MemoryStore", type: "Assumption", id: ws === "workspace-b" ? "B" : "A" }],
      char_count: 120,
      estimated_token_count: 30,
      included_count: 1,
      dropped_count: 0,
      budget_chars: 4000,
    });
  }

  const submitMatch = path.match(/^\/ai\/threads\/([^/]+)\/interactions$/);
  if (method === "POST" && submitMatch) {
    submitCount += 1;
    const threadId = decodeURIComponent(submitMatch[1]);
    const body = req.postDataJSON();

    if (body.prompt === "digest mismatch") {
      return json(409, { detail: "context digest mismatch" });
    }

    if (body.prompt === "stale X" || body.prompt === "duplicate guard") {
      heldSubmitStarted = true;
      return new Promise((resolve) => {
        heldSubmitResolve = () => {
          successfulDispatches += 1;
          const saved = interaction(`ix-${40 + submitCount}`, body.request_id, body.prompt, `${body.prompt} complete`, `flow-${submitCount}`);
          details[threadId] = { ...details[threadId], interactions: [...details[threadId].interactions, saved] };
          resolve(json(200, { interaction: saved }));
        };
      });
    }

    successfulDispatches += 1;
    const saved = interaction(`ix-${40 + submitCount}`, body.request_id, body.prompt, "ok", `flow-${submitCount}`);
    details[threadId] = { ...details[threadId], interactions: [...details[threadId].interactions, saved] };
    return json(200, { interaction: saved });
  }

  if (method === "POST" && path === "/ai/threads") {
    const body = req.postDataJSON();
    const created = summary(`thread-created-${Date.now()}`, body.workspace_id, body.title ?? "Jarvis advisory");
    threadsByWorkspace[body.workspace_id].unshift(created);
    details[created.id] = { ...created, interactions: [], has_older: false };
    return json(200, created);
  }

  return json(404, { detail: `unmocked ${method} ${path}` });
});

async function openSidecar() {
  const show = page.getByRole("button", { name: "Show context" });
  if (await show.count()) await show.click();
  await page.getByTestId("jarvis-sidecar").waitFor();
}

async function selectSidecarThread(id) {
  await page.getByTestId("jarvis-sidecar").locator("select").selectOption(id);
  await page.waitForTimeout(30);
}

// Explicit no-workspace state.
await page.goto(`${app}/home`);
await openSidecar();
await page.getByText("Select a workspace to use Jarvis.").waitFor();

// Establish workspace A on a real application surface.
await page.getByRole("link", { name: "Runs" }).click();
await page.getByRole("heading", { name: "Runs", level: 1 }).waitFor();
await openSidecar();
await page.getByText(digestA).waitFor();
await selectSidecarThread("thread-x");

// Preview failure is bounded and recoverable.
previewMode = "fail";
await page.getByRole("button", { name: "Refresh context preview" }).click();
await page.getByText("Project context preview could not be loaded.").waitFor();
currentDigest = digestA;
await page.getByRole("button", { name: "Refresh context preview" }).click();
await page.getByText(digestA).waitFor();

// Stale preview after route ownership changes must not overwrite the new route preview.
previewMode = "hold";
await page.getByRole("button", { name: "Refresh context preview" }).click();
await page.waitForFunction(() => true);
while (!heldPreviewStarted) await page.waitForTimeout(10);
currentDigest = digestRoute;
await page.getByRole("link", { name: "Engineering Data" }).click();
await page.getByRole("heading", { name: "Engineering Data", level: 1 }).waitFor();
await openSidecar();
await page.getByText(digestRoute).waitFor();
heldPreviewResolve();
await page.waitForTimeout(80);
assert.equal(await page.getByText(digestOld).count(), 0, "stale route-owned preview must be ignored");

// A→B→A list ownership rejects the late B response.
holdBList = true;
await page.getByLabel("Workspace").selectOption("workspace-b");
while (!bListStarted) await page.waitForTimeout(10);
await page.getByLabel("Workspace").selectOption("workspace-a");
await page.getByText(digestRoute).waitFor();
bListResolve();
await page.waitForTimeout(80);
const threadOptions = await page.getByTestId("jarvis-sidecar").locator("select option").allTextContents();
assert.ok(threadOptions.includes("Thread X"), "workspace A threads must remain current after A→B→A");
assert.ok(!threadOptions.includes("Thread B"), "late workspace B list must not poison workspace A");
holdBList = false;

// Submit on X then select Y: stale completion cannot lock or poison Y.
await selectSidecarThread("thread-x");
const prompt = page.getByLabel("Message");
await prompt.fill("stale X");
await page.getByRole("button", { name: "Send with inspected context" }).click();
while (!heldSubmitStarted) await page.waitForTimeout(10);
await page.getByRole("button", { name: "Submitting…" }).waitFor();
await selectSidecarThread("thread-y");
assert.equal(await prompt.isEnabled(), true, "newly selected thread must be usable immediately");
await prompt.fill("Y remains current");
heldSubmitResolve();
heldSubmitStarted = false;
heldSubmitResolve = null;
await page.waitForTimeout(100);
assert.equal(await prompt.inputValue(), "Y remains current", "stale X completion must not clear Y prompt");
assert.equal(await page.getByText("stale X complete").count(), 0, "stale X completion must not repaint Y transcript");

// Browser-visible digest mismatch: one interaction request, bounded state, zero successful dispatch.
await prompt.fill("digest mismatch");
const beforeMismatchPosts = submitCount;
const beforeMismatchDispatch = successfulDispatches;
await page.getByRole("button", { name: "Send with inspected context" }).click();
await page.getByText(/Project context changed before dispatch/i).waitFor();
assert.equal(submitCount, beforeMismatchPosts + 1, "digest mismatch must issue only the attempted interaction request");
assert.equal(successfulDispatches, beforeMismatchDispatch, "digest mismatch must not become a successful dispatch");

// Duplicate Enter/click suppression while a request is unresolved.
await prompt.fill("duplicate guard");
await page.getByRole("button", { name: "Send with inspected context" }).click();
while (!heldSubmitStarted) await page.waitForTimeout(10);
const beforeDuplicate = submitCount;
await page.keyboard.press("Enter");
await page.getByRole("button", { name: "Submitting…" }).evaluate((button) => button.click());
await page.waitForTimeout(60);
assert.equal(submitCount, beforeDuplicate, "duplicate Enter/click must not create a second interaction request");
heldSubmitResolve();
heldSubmitStarted = false;
heldSubmitResolve = null;
await page.getByText("duplicate guard complete").waitFor();

// Terminal/capture distinctions and hostile markup remain inert.
await selectSidecarThread("thread-terminal");
await page.getByText("confirmation_required", { exact: true }).waitFor();
await page.getByText("failed", { exact: true }).waitFor();
await page.getByText("capture_failed", { exact: true }).waitFor();
await page.getByText("Terminal reason: provider_error").waitFor();
await page.getByText("Persistence diagnostic: assistant snapshot write failed").waitFor();
await page.getByText(hostileText, { exact: true }).waitFor();
assert.equal(await page.locator("img[data-evil]").count(), 0, "markup-like assistant text must render inertly");
assert.equal(await page.evaluate(() => globalThis.__jarvisInjected === true), false, "hostile text must not execute");

// Same persisted thread surface stays reachable on /ai-threads without remounting workspace ownership.
await page.evaluate(() => {
  history.pushState({}, "", "/ai-threads");
  window.dispatchEvent(new PopStateEvent("popstate"));
});
await page.getByRole("heading", { name: "AI Threads", level: 1 }).waitFor();
await page.getByRole("button", { name: /Terminal evidence/ }).click();
await page.getByText("assistant snapshot write failed").waitFor();
await page.getByText(hostileText, { exact: true }).waitFor();
assert.equal(await page.locator("img[data-evil]").count(), 0, "/ai-threads must preserve inert rendering");

assert.deepEqual(unexpectedExternal, [], `unexpected external/provider calls: ${unexpectedExternal.join(", ")}`);
await browser.close();
console.log("JARVIS-SIDECAR adversarial browser matrix passed");
