import { chromium } from "playwright";
import assert from "node:assert/strict";

const app = "http://127.0.0.1:5173";
const api = "http://127.0.0.1:8000";
const now = "2026-08-17T00:00:00Z";
const digestA = `sha256:${"a".repeat(64)}`;
const digestB = `sha256:${"b".repeat(64)}`;

const workspace = (id, name) => ({ id, name, slug: id, status: "active", created_at: now, updated_at: now });
const summary = (id, workspaceId, title) => ({ id, workspace_id: workspaceId, title, created_at: now, last_activity_at: now });
const interaction = (id, requestId, prompt, assistant, flowId) => ({
  id,
  request_id: requestId,
  interaction_index: 1,
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
});

const threadsByWorkspace = {
  "workspace-a": [summary("thread-a", "workspace-a", "Thread A"), summary("thread-y", "workspace-a", "Thread Y")],
  "workspace-b": [summary("thread-b", "workspace-b", "Thread B")],
};
const details = {
  "thread-a": { ...threadsByWorkspace["workspace-a"][0], interactions: [], has_older: false },
  "thread-y": { ...threadsByWorkspace["workspace-a"][1], interactions: [], has_older: false },
  "thread-b": { ...threadsByWorkspace["workspace-b"][0], interactions: [], has_older: false },
};

let previewDigest = digestA;
let previewCount = 0;
let submitCount = 0;
let firstUncertainBody = null;
let firstUncertainRequestId = null;
let heldSubmitResolve = null;
let heldSubmitBody = null;
let hostileExternalCalls = [];

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 640, height: 720 } });
page.on("request", (request) => {
  const url = request.url();
  if (!url.startsWith(app) && !url.startsWith(api) && !url.startsWith("data:") && !url.startsWith("blob:")) hostileExternalCalls.push(url);
});
page.on("pageerror", (error) => { throw error; });

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
    return json(200, { threads: threadsByWorkspace[ws] ?? [] });
  }
  const detailMatch = path.match(/^\/ai\/threads\/([^/]+)$/);
  if (method === "GET" && detailMatch) return json(200, details[decodeURIComponent(detailMatch[1])]);

  if (method === "POST" && path === "/ai/context/packs/preview") {
    previewCount += 1;
    const body = req.postDataJSON();
    const ws = body.workspace_id;
    const digest = ws === "workspace-b" ? digestB : previewDigest;
    return json(200, {
      context_digest: digest,
      context_sources_manifest: [{ source: "MemoryStore", type: "Assumption", id: ws === "workspace-b" ? "B-1" : "A-1" }],
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
    const workspaceId = url.searchParams.get("workspace_id");

    if (body.prompt === "uncertain retry") {
      if (!firstUncertainBody) {
        firstUncertainBody = body;
        firstUncertainRequestId = body.request_id;
        return json(503, { detail: "transient" });
      }
      assert.equal(body.request_id, firstUncertainRequestId, "retry must preserve request id");
      assert.equal(body.expected_context_digest, firstUncertainBody.expected_context_digest, "retry must preserve inspected digest");
      const saved = interaction("ix-retry", body.request_id, body.prompt, "retry-safe", "flow-retry");
      details[threadId] = { ...details[threadId], interactions: [saved] };
      return json(200, { interaction: saved });
    }

    if (body.prompt === "held submit") {
      heldSubmitBody = body;
      return new Promise((resolve) => {
        heldSubmitResolve = () => {
          const saved = interaction("ix-held", body.request_id, body.prompt, "held-complete", "flow-held");
          details[threadId] = { ...details[threadId], interactions: [saved] };
          resolve(json(200, { interaction: saved }));
        };
      });
    }

    const saved = interaction(`ix-${submitCount}`, body.request_id, body.prompt, "ok", `flow-${submitCount}`);
    details[threadId] = { ...details[threadId], interactions: [saved] };
    return json(200, { interaction: saved });
  }

  if (method === "POST" && path === "/ai/threads") {
    const body = req.postDataJSON();
    const created = summary(`thread-created-${Date.now()}`, body.workspace_id, body.title);
    threadsByWorkspace[body.workspace_id].unshift(created);
    details[created.id] = { ...created, interactions: [], has_older: false };
    return json(200, created);
  }

  return json(404, { detail: `unmocked ${method} ${path}` });
});

await page.goto(`${app}/runs`);
await page.getByRole("heading", { name: "Runs", level: 1 }).waitFor();
await page.getByRole("button", { name: "Show context" }).click();
await page.getByTestId("jarvis-sidecar").waitFor();
await page.getByText("Contextual engineering assistant").waitFor();
await page.getByText(/Route: runs/).waitFor();
await page.getByText(/Digest/).waitFor();
assert.ok(await page.getByText(digestA).isVisible(), "initial inspected digest must be visible");

// Analytics contribution survives the global Jarvis sidecar composition.
await page.getByRole("button", { name: "Show analysis" }).click();
await page.getByRole("heading", { name: "Run comparison" }).waitFor();
await page.getByText("No persisted runs are available for analytics.").waitFor();

// Context-off submit must omit context fields.
await page.getByLabel("Use inspected project context").uncheck();
const prompt = page.getByLabel("Message");
await prompt.fill("without context");
const noContextRequest = page.waitForRequest((r) => r.url().includes("/interactions") && r.method() === "POST");
await page.getByRole("button", { name: "Send without project context" }).click();
const noContextBody = (await noContextRequest).postDataJSON();
assert.ok(!("context_selection" in noContextBody));
assert.ok(!("expected_context_digest" in noContextBody));
await page.getByText("ok").waitFor();

// Context-on submit must bind the server-previewed digest.
await page.getByLabel("Use inspected project context").check();
await page.getByText(digestA).waitFor();
await prompt.fill("with context");
const contextRequest = page.waitForRequest((r) => r.url().includes("/interactions") && r.method() === "POST");
await page.getByRole("button", { name: "Send with inspected context" }).click();
const contextBody = (await contextRequest).postDataJSON();
assert.equal(contextBody.expected_context_digest, digestA);
assert.deepEqual(contextBody.context_selection, {});
await page.getByText("ok").waitFor();

// Uncertain failure retains request id + original inspected digest even after preview drift.
await prompt.fill("uncertain retry");
await page.getByRole("button", { name: "Send with inspected context" }).click();
await page.getByText(/durable result is uncertain/i).waitFor();
previewDigest = digestB;
await page.getByRole("button", { name: "Refresh context preview" }).click();
await page.getByText(digestB).waitFor();
assert.ok(await page.getByText(/retains its inspected digest/i).isVisible());
await page.getByRole("button", { name: "Retry with original context" }).click();
await page.getByText("retry-safe").waitFor();

// Close/reopen during in-flight submit preserves App-owned operation state and does not redispatch.
previewDigest = digestB;
await prompt.fill("held submit");
await page.getByRole("button", { name: "Send with inspected context" }).click();
await page.getByRole("button", { name: "Submitting…" }).waitFor();
const beforeHeldCount = submitCount;
await page.getByRole("button", { name: "Close sidecar" }).click();
await page.getByRole("button", { name: "Show context" }).click();
await page.getByRole("button", { name: "Submitting…" }).waitFor();
assert.equal(submitCount, beforeHeldCount, "visual close/reopen must not redispatch");
assert.equal(heldSubmitBody.expected_context_digest, digestB);
heldSubmitResolve();
await page.getByText("held-complete").waitFor();

// Workspace change invalidates old ownership and installs the new workspace preview/thread.
await page.getByLabel("Workspace").selectOption("workspace-b");
await page.getByText(digestB).waitFor();
await page.getByLabel("Thread").selectOption("thread-b");
await page.getByText(/Route: runs/).waitFor();

// Keyboard behavior: Shift+Enter inserts a newline; Enter submits.
await page.getByLabel("Use inspected project context").uncheck();
await prompt.fill("line one");
await prompt.press("Shift+Enter");
await prompt.type("line two");
assert.equal(await prompt.inputValue(), "line one\nline two");
const enterRequest = page.waitForRequest((r) => r.url().includes("/interactions") && r.method() === "POST");
await prompt.press("Enter");
await enterRequest;
await page.getByText("ok").waitFor();

// Escape closes the sidecar and restores focus to the toggle.
await page.getByRole("heading", { name: "Context", level: 2 }).focus();
await page.keyboard.press("Escape");
await page.getByRole("button", { name: "Show context" }).waitFor();
assert.equal(await page.getByRole("button", { name: "Show context" }).evaluate((el) => el === document.activeElement), true);

// Effective-200%-width proof: no global horizontal overflow at a compact viewport.
const overflow = await page.evaluate(() => ({ root: document.documentElement.scrollWidth - document.documentElement.clientWidth, body: document.body.scrollWidth - document.body.clientWidth }));
assert.ok(overflow.root <= 1 && overflow.body <= 1, `global overflow detected: ${JSON.stringify(overflow)}`);

assert.ok(previewCount >= 3, "context preview path was not materially exercised");
assert.ok(submitCount >= 5, "submit path was not materially exercised");
assert.deepEqual(hostileExternalCalls, [], `unexpected external calls: ${hostileExternalCalls.join(", ")}`);

await browser.close();
console.log("JARVIS-SIDECAR browser proof passed");
