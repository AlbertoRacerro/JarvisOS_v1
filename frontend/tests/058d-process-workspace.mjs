import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const read = (path) => readFileSync(resolve(root, path), "utf8");
const assert = (condition, message) => {
  if (!condition) throw new Error(`058d acceptance failed: ${message}`);
};
const includesAll = (text, fragments, message) => {
  for (const fragment of fragments) assert(text.includes(fragment), `${message}: missing ${fragment}`);
};

const routes = read("src/app/routes.ts");
const registry = read("src/stages/registry.ts");
const processStage = read("src/stages/ProcessStage.tsx");
const lineageStage = read("src/stages/LineageStage.tsx");
const app = read("src/App.tsx");

// 1-4: canonical Process/Lineage routes and historical replace-style Flowsheet alias.
includesAll(routes, [
  'id: "design-process", path: "/design/process"',
  'id: "design-lineage", path: "/design/lineage"',
  'if (normalized === "/design/flowsheet")',
  'candidate.id === "design-lineage"',
  'canonicalPath: lineageRoute.path',
  'shouldReplace: true',
  'pathOnly.replace(/\\/+$/g, "")'
], "route migration contract");

// 5: Design stage order is exactly Model -> Process -> Results -> Lineage with no visible Flowsheet entry.
const stageBlock = routes.match(/export const DESIGN_STAGE_ITEMS = \[([\s\S]*?)\] as const/)?.[1] ?? "";
assert(stageBlock.length > 0, "DESIGN_STAGE_ITEMS block missing");
const stageLabels = [...stageBlock.matchAll(/label: "([^"]+)"/g)].map((match) => match[1]);
assert(JSON.stringify(stageLabels) === JSON.stringify(["Model", "Process", "Results", "Lineage"]), `unexpected Design stage order: ${stageLabels.join(" -> ")}`);
assert(!stageBlock.includes("Flowsheet"), "visible Flowsheet stage remains");

// 6: registry has distinct Process and Lineage component ownership and no flowsheet stage key.
includesAll(registry, [
  'import LineageStage from "./LineageStage"',
  'import ProcessStage from "./ProcessStage"',
  'process: { kind: "process", label: "Process", render: ProcessStage }',
  'lineage: { kind: "lineage", label: "Lineage", render: LineageStage }'
], "stage registry contract");
assert(!/\bflowsheet\s*:/.test(registry), "registry still exposes a flowsheet stage key");

// 7: renamed Lineage stage preserves graph/node/freshness reads plus stale response guards.
includesAll(lineageStage, [
  "getLineageGraph",
  "getLineageNode",
  "getLineageFreshness",
  "acceptsLineageResponse",
  "workspaceRef.current !== targetWorkspaceId",
  "workspaceRef.current !== workspaceId",
  "selectedRefRef.current !== nodeRef",
  'aria-labelledby="lineage-stage-title"'
], "Lineage runtime/stale-guard contract");
assert((lineageStage.match(/acceptsLineageResponse/g) ?? []).length >= 5, "Lineage response guards were reduced unexpectedly");

// 8-10,13: Process scaffold is presentation-only, selection-neutral, storage-free and inert.
assert(processStage.trimStart().startsWith('import type { PrimaryStageProps } from "./registry";'), "ProcessStage gained a runtime import");
assert(!/from\s+["'][^"']*(?:api|lineage|runner|provider)/i.test(processStage), "ProcessStage imports runtime/domain authority");
assert(!/\b(?:fetch|localStorage|sessionStorage|onSelectionChange|onWorkspaceChange|useEffect|useState)\b/.test(processStage), "ProcessStage gained state, storage, fetch, or selection authority");
assert((processStage.match(/\bdisabled\b/g) ?? []).length >= 2, "Process controls are not deterministically disabled");
assert(!/\bonClick\s*=/.test(processStage), "Process scaffold exposes a mutating click handler");
includesAll(processStage, [
  "Process topology editing is unavailable until server-owned process and evaluator contracts are integrated.",
  "No process topology is loaded.",
  "Not available yet."
], "truthful Process empty-state contract");

// 11: route transitions clear stale selection and shell context before the next stage owns presentation.
const routeReset = app.match(/useEffect\(\(\) => \{([\s\S]*?)\}, \[route\.id\]\);/)?.[1] ?? "";
includesAll(routeReset, ["setSelection(null)", "setShellRegions({})", "setShellRegionRequest(null)"], "route-id stale-context reset");

// 12: Process reuses the existing 089 dock owner and does not introduce process-specific analytics authority.
includesAll(app, [
  'import AnalyticsDockContent from "./components/analytics/AnalyticsDockContent"',
  'route.id === "design-process"',
  "<AnalyticsDockContent workspaceId={workspaceId} />"
], "Process Analysis Dock reuse");
assert(!/ProcessAnalytics|ProcessKpi|process-specific analytics/i.test(app + processStage), "process-specific analytics authority was introduced");

console.log("058d deterministic frontend acceptance passed");
