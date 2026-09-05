import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const read = (relative) => fs.readFileSync(path.join(root, relative), "utf8");
const app = read("src/App.tsx");
const workbench = read("src/pages/CodingWorkbench.tsx");
const api = read("src/api/coding.ts");
const failures = [];
const check = (condition, message) => { if (!condition) failures.push(message); };
const includesAll = (text, fragments, message) => {
  for (const fragment of fragments) check(text.includes(fragment), `${message}: missing ${fragment}`);
};

includesAll(app, [
  'import CodingWorkbench from "./pages/CodingWorkbench"',
  '<CodingWorkbench mode="repository" workspaceId={workspaceId} />',
  '<CodingWorkbench mode="runtime" workspaceId={workspaceId} />'
], "Coding routes are not wired to the accepted 140 surface");

includesAll(api, [
  "/api/coding/repository/ref?",
  "/api/coding/repository/tree?",
  "/api/coding/repository/file?",
  "/api/coding/repository/search?",
  "/api/coding/repository/pull-request?",
  "/api/coding/repository/checks?",
  "/api/coding/repository/reviews?",
  "/api/coding/repository/url?",
  "/api/coding/runtime-truth?",
  "/api/coding/pipeline-state?",
  "/api/coding/actions/inspect",
  "/api/coding/actions/context-preview",
  "/api/coding/actions/suggest-modification"
], "140 API client is missing an accepted backend owner projection");
check(!/api\.github\.com|github\.com\/api|Authorization|GITHUB_TOKEN|ghp_/i.test(api), "browser API client gained provider/credential authority");

includesAll(workbench, [
  "Server-owned 118 repository truth",
  "resolvedSha",
  "readRepositoryTree",
  "readRepositoryFile",
  "searchRepository",
  "readPullRequest",
  "readChecks",
  "readReviews",
  "readSafeGithubUrl",
  "Open server-validated GitHub path",
  "Partial evidence",
  "Truncated evidence is not presented as complete.",
  "treePath",
  "openDirectory",
  ">Root<",
  ">Up<",
  "fileReadGeneration",
  "requestGeneration",
  "requestSha",
  "fileReadGeneration.current !== requestGeneration",
  "fileReadGeneration.current += 1",
  "readRuntimeTruth",
  'relation = runtime?.alignment ?? "unknown"',
  "Process startup identity",
  "Root identity",
  "Observed at",
  "Provenance",
  "Failure identity",
  "The browser performs no SHA ancestry or cleanliness inference.",
  "readPipelineState",
  "pipelineRequestGeneration",
  "invalidatePipelineSelection",
  "No synthetic stages are shown.",
  "inspectCodingTarget",
  "previewCodingContext",
  "Add selected exact file to proposal context",
  "context_digest",
  "added_context_refs",
  "suggestCodingModification",
  "Repository browsing is context-neutral.",
  "READ / CONTEXT / PROPOSE only",
  "they do not commit, apply, execute, push, create a PR, merge, or mutate STATUS"
], "140 operator contract is incomplete");
check(!/api\.github\.com|github\.com\/api|localStorage|sessionStorage|child_process|powershell|cmd\.exe/i.test(workbench), "Coding surface crossed the browser authority boundary");
check(!/fetch\(/.test(workbench), "Coding surface bypasses the shared API client");
check(!/merge-base|rev-list|isAncestor|compareCommits|compare_commits/i.test(workbench), "browser appears to derive repository/runtime relation locally");

if (failures.length) {
  console.error("CODING-FRONTEND-INTEGRATION-1 deterministic acceptance failed:");
  for (const failure of failures) console.error(`- ${failure}`);
  process.exit(1);
}
console.log("CODING-FRONTEND-INTEGRATION-1 deterministic acceptance: PASS");
