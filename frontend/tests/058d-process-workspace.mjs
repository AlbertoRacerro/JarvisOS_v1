import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const read = (path) => readFileSync(resolve(root, path), "utf8");
const assert = (condition, message) => { if (!condition) throw new Error(`058d acceptance failed: ${message}`); };
const includesAll = (text, fragments, message) => { for (const fragment of fragments) assert(text.includes(fragment), `${message}: missing ${fragment}`); };

const routes = read("src/app/routes.ts");
const registry = read("src/stages/registry.ts");
const processStage = read("src/stages/ProcessStage.tsx");
const lineageStage = read("src/stages/LineageStage.tsx");
const app = read("src/App.tsx");

// 100f supersedes the visible 058d Design peer IA while preserving Process and deterministic historical aliases.
includesAll(routes, [
  'id: "design-process", path: "/design/process"',
  'id: "design-bluecad", path: "/design/bluecad"',
  '"/design/lineage": "/memory/models"',
  '"/design/flowsheet": "/memory/models"',
  'pathOnly.replace(/\\/+$/g, "")'
], "100f route migration contract");
const designPeerBlock = routes.match(/design: \[([\s\S]*?)\n  \],\n  memory:/)?.[1] ?? "";
const designLabels = [...designPeerBlock.matchAll(/label: "([^"]+)"/g)].map((match) => match[1]);
assert(JSON.stringify(designLabels) === JSON.stringify(["Process", "BLUECAD"]), `100f Design peers drifted: ${designLabels.join(" -> ")}`);

// Historical registry ownership remains distinct so retained compatibility code does not collapse Process/Lineage semantics.
includesAll(registry, [
  'import LineageStage from "./LineageStage"',
  'import ProcessStage from "./ProcessStage"',
  'process: { kind: "process", label: "Process", render: ProcessStage }',
  'lineage: { kind: "lineage", label: "Lineage", render: LineageStage }'
], "stage registry contract");
assert(!/\bflowsheet\s*:/.test(registry), "registry still exposes a flowsheet stage key");

includesAll(lineageStage, [
  "getLineageGraph", "getLineageNode", "getLineageFreshness", "acceptsLineageResponse",
  "workspaceRef.current !== targetWorkspaceId", "workspaceRef.current !== workspaceId", "selectedRefRef.current !== nodeRef",
  'aria-labelledby="lineage-stage-title"'
], "retained Lineage runtime/stale-guard contract");
assert((lineageStage.match(/acceptsLineageResponse/g) ?? []).length >= 5, "Lineage response guards were reduced unexpectedly");

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

const routeReset = app.match(/useEffect\(\(\) => \{([\s\S]*?)\}, \[route\.id\]\);/)?.[1] ?? "";
includesAll(routeReset, ["setSelection(null)", "setShellRegions({})", "setShellRegionRequest(null)"], "route-id stale-context reset");
includesAll(app, [
  'import AnalyticsDockContent from "./components/analytics/AnalyticsDockContent"',
  'route.id === "design-process"',
  "<AnalyticsDockContent workspaceId={workspaceId} />"
], "Process Analysis Dock reuse");
assert(!/ProcessAnalytics|ProcessKpi|process-specific analytics/i.test(app + processStage), "process-specific analytics authority was introduced");

console.log("058d deterministic frontend acceptance passed");
