import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, "..");
const read = (relative) => fs.readFileSync(path.join(root, relative), "utf8");
const assert = (condition, message) => {
  if (!condition) throw new Error(`100g conformance failure: ${message}`);
};

const shellCss = read("src/styles/final-fusion-shell-overrides.css");
const workspaceCss = read("src/styles/final-workspace-header.css");
const repairCss = read("src/styles/100g-ui-repair.css");
const main = read("src/main.tsx");
const routes = read("src/app/routes.ts");
const processStage = read("src/stages/ProcessStage.tsx");
const bluecadStage = read("src/stages/ModelStage.tsx");
const settingsSurface = read("src/components/fusion/FinalSettingsSurface.tsx");
const pkg = JSON.parse(read("package.json"));

// Finding A: final route fragments must stack workspace header above the real workbench surface.
assert(shellCss.includes("flex-direction: column;"), "final shell main must stack header and work surface vertically");
assert(!workspaceCss.includes("min-height: 104px"), "workspace header must not reserve the legacy 104px dead band");
assert(!workspaceCss.includes("calc(100% - 104px)"), "work surface must not use the legacy fixed-height subtraction");
assert(workspaceCss.includes("grid-template-columns: minmax(0, 1fr) auto;"), "desktop workspace header must place metadata and peer tabs in one horizontal band");
assert(workspaceCss.includes('"eyebrow tabs"') && workspaceCss.includes('"title tabs"') && workspaceCss.includes('"description tabs"'), "workspace header must bind peer tabs beside title metadata");
assert(workspaceCss.includes(".final-fusion__workspace-head + .final-fusion__workbench"), "workspace repair must bind the actual production workbench sibling");
assert(!workspaceCss.includes(".final-fusion__workspace-head + .final-fusion {"), "workspace repair must not target the obsolete wrapper shape");
assert(workspaceCss.includes("flex: 1 1 auto;") && workspaceCss.includes("height: auto;"), "work surface must consume the space immediately below the compact header");

// Finding B: all peer navigation uses neutral inactive and soft-accent active states.
for (const token of ["#ddd5c8", "#fffefc", "#76a964", "#edf7e7", "#28581a"]) {
  assert(workspaceCss.includes(token), `Memory/Development/Coding peer tabs must include shared token ${token}`);
  assert(repairCss.includes(token), `Design/Settings peer tabs must include shared token ${token}`);
}
assert(repairCss.includes(".application-shell--final .design-stage__tabs button"), "Design peer tabs must receive final-route navigation overrides");
assert(repairCss.includes('.design-stage__tabs button[aria-current="page"]'), "Design active peer tab must use route state, not primary-action styling");
assert(repairCss.includes(".application-shell--final .final-settings__tab.is-active"), "Settings active peer tab must share the soft-accent language");
assert(main.includes('import "./styles/100g-ui-repair.css";'), "100g repair stylesheet must be loaded by production entrypoint");

// Preserve exact canonical routes and intentional Design workbench structure.
for (const route of [
  "/memory/project-basis",
  "/memory/models",
  "/memory/literature",
  "/development/roadmap/timeline",
  "/development/roadmap/calendar",
  "/development/brainstorm",
  "/coding/repository",
  "/coding/runtime",
  "/design/process",
  "/design/bluecad",
  "/settings/appearance",
  "/settings/ai",
  "/settings/system",
]) {
  assert(routes.includes(`path: "${route}"`), `canonical route must remain present: ${route}`);
}
assert(processStage.includes("process-stage__palette"), "Process operational palette must remain structurally distinct from the workspace header repair");
assert(processStage.includes("design-stage__tabs") && bluecadStage.includes("design-stage__tabs"), "Process and BLUECAD must preserve their shared peer selector");
assert(settingsSurface.includes("final-settings__tabs"), "Settings must preserve its peer selector semantics");

// Regression gate must be part of the normal build.
assert(pkg.scripts?.["test:100g"] === "node tests/100g-final-operator-ui-repair.mjs", "package must expose test:100g");
assert(pkg.scripts?.build?.includes("npm run test:100g"), "npm run build must execute test:100g");

console.log("100g final operator UI repair conformance: PASS");
