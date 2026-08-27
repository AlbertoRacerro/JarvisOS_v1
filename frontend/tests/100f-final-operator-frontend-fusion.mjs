import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const read = (relative) => fs.readFileSync(path.join(root, relative), "utf8");
const routes = read("src/app/routes.ts");
const app = read("src/App.tsx");
const layout = read("src/components/Layout.tsx");
const main = read("src/main.tsx");
const fusion = read("src/components/fusion/FinalOperatorUnavailableSurface.tsx");
const readFusion = read("src/components/fusion/FinalOperatorReadSurface.tsx");
const readApi = read("src/api/finalOperatorReads.ts");
const fusionCss = read("src/styles/final-fusion.css");
const shellOverlay = read("src/styles/final-fusion-shell-overrides.css");
const canonicalOverlay = read("src/styles/final-fusion-canonical-overrides.css");
const processStage = read("src/stages/ProcessStage.tsx");
const contextNav = read("src/components/shell/ContextualNavigator.tsx");
const pkg = JSON.parse(read("package.json"));
const failures = [];
const check = (condition, message) => { if (!condition) failures.push(message); };
const includesAll = (text, fragments, message) => { for (const fragment of fragments) check(text.includes(fragment), `${message}: missing ${fragment}`); };

const canonicalRoutes = [
  "/design/process", "/design/bluecad", "/memory/project-basis", "/memory/models", "/memory/literature",
  "/development/roadmap/timeline", "/development/roadmap/calendar", "/development/brainstorm",
  "/coding/repository", "/coding/runtime", "/settings/appearance", "/settings/ai", "/settings/system"
];
for (const route of canonicalRoutes) check(routes.includes(`path: "${route}"`), `canonical route missing: ${route}`);

const primaryBlock = routes.match(/export const PRIMARY_NAV_ITEMS = \[([\s\S]*?)\] as const/)?.[1] ?? "";
const primaryLabels = [...primaryBlock.matchAll(/label: "([^"]+)"/g)].map((match) => match[1]);
check(JSON.stringify(primaryLabels) === JSON.stringify(["Design", "Memory", "Development", "Coding", "Settings"]), `primary IA drifted: ${primaryLabels.join(" | ")}`);
check(!primaryBlock.includes("Home") && !primaryBlock.includes("Runs") && !primaryBlock.includes("Engineering Data") && !primaryBlock.includes("Review"), "legacy peer leaked into primary rail");

includesAll(routes, [
  '"/": "/design/process"',
  '"/home": "/design/process"',
  '"/design/model": "/memory/models"',
  '"/design/results": "/memory/models"',
  '"/design/lineage": "/memory/models"',
  '"/design/flowsheet": "/memory/models"',
  '"/settings": "/settings/appearance"'
], "legacy redirect contract");

includesAll(routes, [
  'design: [', 'label: "Process"', 'label: "BLUECAD"',
  'memory: [', 'label: "Project Basis"', 'label: "Models"', 'label: "Literature"',
  'development: [', 'label: "Roadmap"', 'label: "Brainstorm"',
  'coding: [', 'label: "Repository"', 'label: "Runtime"',
  'settings: [', 'label: "Appearance"', 'label: "AI"', 'label: "System"',
  'label: "Timeline"', 'label: "Calendar"'
], "peer IA contract");
check(!routes.includes('label: "Board"'), "Board reintroduced as Roadmap peer");
check(contextNav.includes("ROADMAP_STAGE_ITEMS"), "Roadmap Timeline/Calendar secondary navigation missing");

check(app.includes('route.id === "design-process" || route.id === "design-bluecad"'), "Process/BLUECAD do not reuse the existing stage shell");
check(app.includes('sidecar: route.primaryNav === "settings" ? undefined : jarvisSidecar'), "Settings must not expose Jarvis sidecar");
includesAll(app, [
  'FinalOperatorReadSurface kind="project-basis"', 'FinalOperatorReadSurface kind="models"',
  'kind="literature"', 'kind="roadmap"', 'kind="calendar"', 'kind="brainstorm"',
  'kind="repository"', 'FinalOperatorReadSurface kind="runtime"'
], "missing final production surface composition");
check(app.includes("No server-owned roadmap item store") && app.includes("No server-owned time-allocation calendar"), "Development missing-authority states are not explicit");
check(app.includes("browser does not call GitHub"), "Repository frontend/GitHub truth boundary is not explicit");
check(!/iframe|srcDoc/.test(app), "static HTML embedding is forbidden");
check(!/localStorage|sessionStorage|fetch\(|axios|github\.com\/api/i.test(app), "final surface shell gained private truth/API authority");

includesAll(readFusion, [
  "Working revisions are unavailable",
  "Approve-all, working revision and deterministic revalidation require their future accepted owner.",
  "Exact model-version inventory is not exposed by the current read owner.",
  "Specification record; not an exact model version",
  "Not projected from workspace-level records because exact model/version binding cannot be proven.",
  "LOCAL · Unknown SHA",
  "REMOTE · Unknown",
  "does not prove an executed Git SHA",
  "The frontend does not call GitHub directly or infer alignment.",
  "Safe update and terminal EXECUTE authority are not present in 100f."
], "truthful READ/Unknown boundary missing");
check(!/cd951bae|86cdedde|working tree clean|remote current|PASS|Aligned/i.test(readFusion), "fixture repository/runtime success identity leaked into truthful read surface");
check(!/localStorage|sessionStorage|github\.com\/api|api\.github|child_process|powershell|cmd\.exe/i.test(readFusion), "read surface crossed frontend authority boundary");

includesAll(readApi, [
  'getJson<FinalWorkspace[]>("/workspaces")',
  "/model-specs",
  "/requirements",
  "/parameters",
  "/decisions",
  "getSystemInfo"
], "accepted existing backend READ binding missing");
check(!/github\.com|api\.github|localStorage|sessionStorage|child_process|powershell|cmd\.exe/i.test(readApi), "final read adapter crossed frontend authority boundary");

includesAll(layout, [
  "const finalOperatorRoute = route.primaryNav !== undefined",
  'application-shell--final',
  '!finalOperatorRoute && <TopBar',
  'setNavigatorOpen(route.id === "design-bluecad")'
], "canonical final routes must use rail-only shared shell and persistent BLUECAD navigator");
check(main.includes('final-fusion-shell-overrides.css'), "final shared-shell canonical overlay is not loaded");
includesAll(shellOverlay, [
  "grid-template-columns: 170px minmax(0, 1fr)",
  ".application-shell--final .shell-topbar",
  "display: none",
  'font-family: "Inter Display", "Inter"',
  "#fbfaf6",
  "#faf6ee",
  "height: 100vh",
  ".application-shell--final .shell-main > *"
], "canonical rail/shell geometry or visual language missing");

includesAll(processStage, [
  'label: "Select"', 'label: "Pan"', 'label: "Add equipment"', 'label: "Connect"', 'label: "Disconnect"',
  'label: "Multi-select"', 'label: "Duplicate"', 'label: "Delete"', 'label: "Fit view"', 'label: "Zoom"',
  'label: "Undo"', 'label: "Redo"', 'label: "Auto-layout"', 'label: "Validate"', 'label: "Solve"',
  'disabled', 'No process topology is loaded.'
], "canonical Process future affordances or fail-closed empty state missing");
check(!/useState|fetch\(|axios|localStorage|sessionStorage/i.test(processStage), "Process scaffold gained frontend topology/API authority");
includesAll(canonicalOverlay, [
  ".process-stage__toolbar", ".process-stage__palette", ".process-stage__canvas",
  "grid-template-columns: 190px minmax(0, 1fr)", "background-size: 40px 40px"
], "canonical Process workstation composition missing");

includesAll(fusion, [
  'title="Project search"', 'title="Project Basis"', 'title="Jarvis"',
  'title="Model versions"', 'title="Version dossier"', 'Results · Runs · Lineage remain contextual',
  'title="Literature"', 'Compact list · inline multi-expand', 'Bounded preview unavailable',
  'title="Timeline"', 'Execution status', '"Ready", "In progress", "Blocked"',
  '["Day", "Week", "Month", "Agenda"]', 'actual time allocation',
  '<strong>RAW</strong>', '<strong>RECONCILED</strong>', 'Opening an idea never adds it to context',
  'Repository Inspector', 'Preview · Architecture',
  'Local current · actually executed', 'GitHub latest · remote exact', 'Terminal · Logs'
], "canonical staged composition missing");
includesAll(fusion, [
  'navigate("/development/roadmap/calendar")',
  'navigate("/development/roadmap/timeline")',
  'aria-label="Roadmap views"'
], "Roadmap Timeline/Calendar NAVIGATE contract missing from visible production surface");
includesAll(fusion, ["Add workstream", "Add event", "Reconcile", "Promote", "Suggest modification", "Safe update", "Open terminal"], "future affordance preservation");
check(fusion.includes("disabled title={reason}"), "unsupported commit/execute affordances are not fail-closed");
check(!/fetch\(|axios|localStorage|sessionStorage/i.test(fusion), "truthless fusion component gained data/API authority");
check(!/healthy|working tree clean|remote current|PASS|Aligned|cd951bae|86cdedde/i.test(fusion), "canonical HTML fixture success/identity leaked into production staged surfaces");

includesAll(fusionCss, [
  "final-fusion__workbench--memory", "grid-template-columns: 255px minmax(0, 1fr) 315px",
  "final-fusion__workbench--models", "grid-template-columns: 230px minmax(0, 1fr) 310px",
  "final-fusion__workbench--development", "grid-template-columns: minmax(0, 1fr) 350px",
  "final-fusion__workbench--brainstorm", "grid-template-columns: minmax(0, 1fr) 360px",
  "final-fusion__preview-skeleton", "grid-template-columns: minmax(0,1fr) 218px",
  "final-fusion__execution-grid", "final-fusion__week-head", "final-fusion__repo-inspector-body", "final-fusion__compare"
], "canonical reference panel geometry missing");
check(!fusionCss.includes("border-radius: 16px") && !fusionCss.includes("border-radius: 20px"), "large-radius dashboard styling leaked into canonical fusion CSS");

const test100f = pkg.scripts?.["test:100f"] ?? "";
check(test100f.includes("node tests/100f-final-operator-frontend-fusion.mjs") && test100f.includes("node tests/100f-visual-conformance.mjs"), "test:100f is not wired");
check((pkg.scripts?.build ?? "").includes("npm run test:100f"), "build does not execute test:100f");

if (failures.length) {
  console.error("FINAL-OPERATOR-FRONTEND-FUSION-1 deterministic acceptance failed:");
  for (const failure of failures) console.error(`- ${failure}`);
  process.exit(1);
}
console.log("FINAL-OPERATOR-FRONTEND-FUSION-1 deterministic acceptance: PASS");
