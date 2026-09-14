import fs from "node:fs";

const page = fs.readFileSync(new URL("../src/pages/DevelopmentBrainstorm.tsx", import.meta.url), "utf8");
const api = fs.readFileSync(new URL("../src/api/development.ts", import.meta.url), "utf8");
const app = fs.readFileSync(new URL("../src/App.tsx", import.meta.url), "utf8");

function check(condition, message) {
  if (!condition) throw new Error(message);
}

for (const token of [
  "RAW capture",
  "Capture RAW",
  "Immutable RAW",
  "Reconciled ideas",
  "Record discussion",
  "Append reconciled revision",
  "Inspect synthesis and provenance",
  "Exact provenance",
  "Discussion provenance",
  "RAW discussion provenance",
  "Immutable revisions",
  "Supersede lineage",
  "Supersede with successor",
  "Add to Roadmap proposal",
  "Promotion proposals",
  "Speech capture:",
  "unavailable"
]) {
  check(page.includes(token), `Brainstorm surface must expose ${token}`);
}

check(page.includes('["roadmap", "design", "coding"] as const'), "Brainstorm must expose proposal actions for all accepted targets");
check(page.includes('<option value="generic_artifact">Artifact</option>'), "Brainstorm must expose the accepted generic artifact attachment path");
check(page.includes("await refresh(selectedWorkspaceId)"), "Brainstorm mutations must reconcile from server-owned state");
check(page.includes("activeWorkspaceRef.current !== selectedWorkspaceId"), "Brainstorm loads must reject stale workspace projections");
check(page.includes("projectionWorkspaceId !== null && projectionWorkspaceId === workspaceId"), "Brainstorm rendering must suppress a projection from a prior workspace synchronously");
check(page.includes("setProjectionWorkspaceId(null)"), "Brainstorm must invalidate stale projections on workspace/load failure boundaries");
check(page.includes("retryKeysRef"), "Brainstorm ambiguous retries must retain component-memory idempotency identity");
check(page.includes("clearRetryIdentity"), "Brainstorm retry identities must clear only after confirmed mutation success");
check(page.includes("retryKeysRef.current.clear()"), "Workspace changes must discard retry identities from the prior authority scope");
check(page.includes("raw.discussions"), "Brainstorm RAW cards must render server-owned unreconciled discussion provenance after reload");
check(page.includes("discussion.source_refs"), "Brainstorm detail must render persisted discussion source provenance");
check(page.includes("discussion.bound_revision"), "Brainstorm detail must disclose the exact reconciled revision bound to discussion provenance");
check(page.includes("getBrainstormIdea"), "Brainstorm detail must fetch canonical server-owned revisions");
check(!page.includes("localStorage"), "Brainstorm must not introduce browser-owned canonical state");
check(api.includes('"NEW" | "DISCUSSED" | "RECONCILED" | "SUPERSEDED"'), "Brainstorm client must preserve the accepted lineage vocabulary");
check(api.includes('"generic_artifact"'), "Brainstorm client contract must preserve generic artifact refs");
check(api.includes('/development/brainstorm/raw'), "Brainstorm API must remain beneath Development authority");
check(api.includes("bound_revision: number"), "Brainstorm client must type exact discussion-to-revision provenance");
check(api.includes("idempotencyKey: string"), "Brainstorm mutation APIs must accept caller-retained idempotency keys");
check(!api.includes('mutationId("raw")'), "Brainstorm API helpers must not mint a fresh key per retry attempt");
check(api.includes('proposal_only: true'), "Promotion API payload must remain explicitly proposal-only");
check(api.includes("source_revision: idea.current_revision"), "Promotion must bind to an exact source revision");
check(app.includes('<DevelopmentBrainstorm workspaceId={workspaceId} onWorkspaceChange={setWorkspaceId} />'), "Brainstorm route must activate the server-owned surface");

console.log("117 brainstorm frontend contract: OK");
