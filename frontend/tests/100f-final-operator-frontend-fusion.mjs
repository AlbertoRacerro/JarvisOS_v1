import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const read = (relative) => fs.readFileSync(path.join(root, relative), "utf8");
const routes = read("src/app/routes.ts");
const app = read("src/App.tsx");
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
check(app.includes("No server-owned roadmap item store") && app.includes("No server-owned time-allocation calendar"), "Development missing-authority states are not explicit");
check(app.includes("browser does not call GitHub") && app.includes("Runtime health, SHA, update and terminal state therefore remain Unknown or unavailable"), "Coding truth boundaries are not explicit");
check(!/iframe|srcDoc/.test(app), "static HTML embedding is forbidden");
check(!/localStorage|sessionStorage|fetch\(|axios|github\.com\/api/i.test(app), "final surface shell gained private truth/API authority");
check(pkg.scripts?.["test:100f"] === "node tests/100f-final-operator-frontend-fusion.mjs", "test:100f is not wired");
check((pkg.scripts?.build ?? "").includes("npm run test:100f"), "build does not execute test:100f");

if (failures.length) {
  console.error("FINAL-OPERATOR-FRONTEND-FUSION-1 deterministic acceptance failed:");
  for (const failure of failures) console.error(`- ${failure}`);
  process.exit(1);
}
console.log("FINAL-OPERATOR-FRONTEND-FUSION-1 deterministic acceptance: PASS");
