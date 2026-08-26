import fs from "node:fs";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const read = (relative) => fs.readFileSync(path.join(root, relative), "utf8");
const theme = read("src/theme.ts");
const tokens = read("src/styles/tokens.css");
const main = read("src/main.tsx");
const settings = read("src/pages/Settings.tsx");
const settingsCss = read("src/styles/settings.css");
const processStage = read("src/stages/ProcessStage.tsx");
const pkg = JSON.parse(read("package.json"));

const failures = [];
const check = (condition, message) => { if (!condition) failures.push(message); };

check(/APPEARANCE_OPTIONS[^\n]*\["system", "light", "dark"\]/.test(theme), "appearance choices drifted");
check(/ACCENT_OPTIONS[\s\S]*"microalgae"[\s\S]*"leaf-chlorophyll"[\s\S]*"lagoon"[\s\S]*"custom"/.test(theme), "accent choices drifted");
check(theme.includes('DEFAULT_ACCENT_HEX = "#528B68"'), "Microalgae default missing");
check(theme.includes('"leaf-chlorophyll": "#5F8F52"'), "Leaf Chlorophyll seed missing");
check(theme.includes('lagoon: "#4F938A"'), "Lagoon seed missing");
check(theme.includes('/^#[0-9A-F]{6}$/'), "six-digit HEX validation missing");
check((theme.match(/preset: "microalgae"/g) ?? []).length >= 4, "invalid accent paths must fail to Microalgae");
check(theme.includes("jarvisos:accent:v1"), "versioned accent storage key missing");
check(theme.includes("root.style.setProperty(\"--accent-seed\""), "accent seed is not applied through isolated CSS variable");
check(main.includes("applyStoredVisualPreferences();"), "stored visual preferences are not initialized");

const semanticTokens = [
  "--color-status-success-bg", "--color-status-warning-bg", "--color-status-danger-bg",
  "--color-status-proposed-bg", "--color-status-stale-bg", "--color-status-unavailable-bg"
];
for (const token of semanticTokens) {
  const matches = tokens.match(new RegExp(`${token}:`, "g")) ?? [];
  check(matches.length >= 2, `${token} missing light/dark definitions`);
}
check(tokens.includes("--accent-seed: #528B68"), "accent seed token missing");
check(tokens.includes("--color-accent-primary: var(--accent-seed)"), "accent primary must derive from accent seed");
const derivedAccentTokens = [
  "--color-accent-subtle", "--color-accent-surface", "--color-accent-border",
  "--color-accent-border-strong", "--color-accent-hover", "--color-accent-active", "--color-focus-ring"
];
for (const token of derivedAccentTokens) {
  const escaped = token.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  check(new RegExp(`${escaped}:\\s*color-mix\\(in oklch, var\\(--accent-seed\\)`).test(tokens), `${token} must derive from the selected accent seed`);
  check((tokens.match(new RegExp(`${escaped}:`, "g")) ?? []).length >= 2, `${token} requires a deterministic fallback before perceptual derivation`);
}
check(!/--color-status-[^:]+:\s*var\(--accent/.test(tokens), "semantic status token depends on user accent");
check(tokens.includes("--font-size-caption: 0.75rem"), "12px metadata scale missing");
check(tokens.includes("--font-size-label: 0.8125rem"), "13px label scale missing");
check(tokens.includes("--font-size-body: 0.875rem"), "14px body scale missing");
check(tokens.includes("--font-size-section-title: 1rem"), "16px section scale missing");
check(tokens.includes("--control-height-compact: 1.875rem"), "30px compact control missing");
check(tokens.includes("--control-height-default: 2.1875rem"), "35px default control missing");
check(tokens.includes("@media (prefers-reduced-motion: reduce)"), "reduced-motion rule missing");
check(tokens.includes("--motion-fast: 0ms") && tokens.includes("--motion-standard: 0ms"), "reduced-motion must collapse non-essential motion");
check(!tokens.includes("backdrop-filter"), "structural glass is not authorized in first pass");

check(settings.includes('type="color"'), "Settings Custom accent must use the native color input");
check(settings.includes("Reset to Microalgae"), "Settings accent Reset is missing");
check(settings.includes("APPEARANCE_OPTIONS.map"), "Settings appearance choices are missing");
check(settings.includes("ACCENT_OPTIONS.map"), "Settings accent choices are missing");
check(settings.includes("normalizeAccentHex(customAccentDraft)"), "malformed Custom HEX is not guarded before application");
check(settingsCss.includes("var(--color-status-danger-text)"), "invalid custom HEX lacks non-accent error semantics");
check(!/saveAISetting\([^\n]*(accent|appearance)/i.test(settings), "visual preferences must not use canonical settings API");

check(!/pump|compressor|reactor|heat exchanger|stream node/i.test(processStage), "Process scaffold gained fake process semantics");
check(!/fetch\(|axios|provider|runner/i.test(theme), "visual preference owner gained runtime execution/API authority");
check(pkg.scripts?.["test:058d"] === "node tests/058d-process-workspace.mjs", "058d deterministic gate changed");
check(pkg.scripts?.["test:100"] === "node tests/100-visual-identity.mjs", "100 deterministic gate not wired");

if (failures.length) {
  console.error("VISUAL-IDENTITY-1 deterministic acceptance failed:");
  for (const failure of failures) console.error(`- ${failure}`);
  process.exit(1);
}
console.log("VISUAL-IDENTITY-1 deterministic acceptance: PASS");
