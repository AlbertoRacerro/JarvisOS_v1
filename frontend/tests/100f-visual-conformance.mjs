import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const read = (relative) => fs.readFileSync(path.join(root, relative), "utf8");
const app = read("src/App.tsx");
const settings = read("src/components/fusion/FinalSettingsSurface.tsx");
const settingsCss = read("src/styles/final-settings.css");
const designCss = read("src/styles/final-fusion-canonical-overrides.css");
const failures = [];
const check = (condition, message) => { if (!condition) failures.push(message); };
const includesAll = (text, fragments, message) => { for (const fragment of fragments) check(text.includes(fragment), `${message}: missing ${fragment}`); };

includesAll(app, [
  '<FinalSettingsSurface section="appearance"',
  '<FinalSettingsSurface section="ai"',
  '<FinalSettingsSurface section="system"'
], "Settings canonical routes are not section-specific");
includesAll(settings, [
  'label: "Appearance"', 'href: "/settings/appearance"',
  'label: "AI"', 'href: "/settings/ai"',
  'label: "System"', 'href: "/settings/system"',
  'aria-label="Settings sections"', 'aria-current={tab.id === section ? "page" : undefined}'
], "Settings visible peer IA drifted");
includesAll(settingsCss, [
  ".final-settings__tabs", ".final-settings__tab.is-active",
  ".final-settings--appearance .settings-grid > .settings-card--visual",
  ".final-settings--ai .settings-grid > .settings-card:nth-child(2)",
  ".final-settings--ai .settings-grid > .settings-card:nth-child(3)",
  ".final-settings--ai .settings-grid > .settings-card:nth-child(4)",
  ".final-settings--system .settings-grid > .settings-card:nth-child(5)",
  ".application-shell--final .bluecad-workbench__viewport",
  ".application-shell--final .bluecad-workbench__empty-viewer"
], "Settings section filtering or BLUECAD empty viewport composition missing");
includesAll(designCss, [
  ".process-stage__palette-grid",
  "grid-template-columns: repeat(2, minmax(0, 1fr))",
  ".application-shell--final .shell-navigator",
  ".application-shell--final .shell-sidecar",
  "width: 240px",
  "width: 300px",
  ".bluecad-final-stage__toolbar button",
  "background: transparent !important"
], "Canonical Process/BLUECAD workstation composition missing");
check(!settings.includes("fetch(") && !settings.includes("localStorage") && !settings.includes("sessionStorage"), "Settings wrapper gained data/authority state");

if (failures.length) {
  console.error("100f visual conformance acceptance failed:");
  for (const failure of failures) console.error(`- ${failure}`);
  process.exit(1);
}
console.log("100f visual conformance acceptance: PASS");
