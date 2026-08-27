import fs from "node:fs";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const read = (relative) => fs.readFileSync(path.join(root, relative), "utf8");
const theme = read("src/theme.ts");
const tokens = read("src/styles/tokens.css");
const main = read("src/main.tsx");
const layout = read("src/components/Layout.tsx");
const shellCss = read("src/styles/shell.css");
const settings = read("src/pages/Settings.tsx");
const settingsCss = read("src/styles/settings.css");
const processStage = read("src/stages/ProcessStage.tsx");
const pkg = JSON.parse(read("package.json"));
const lock = JSON.parse(read("package-lock.json"));

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
check(theme.includes('root.style.setProperty("--accent-seed", seed)'), "accent seed is not applied through isolated CSS variable");
check(theme.includes('ACCENT_FOREGROUND_LIGHT = "#FFFFFF"') && theme.includes('ACCENT_FOREGROUND_DARK = "#000000"'), "bounded accent foreground candidates must span full readable contrast range");
check(theme.includes("relativeLuminance") && theme.includes("contrastRatio"), "custom accent foreground must be contrast-derived");
check(theme.includes('root.style.setProperty("--color-accent-on", accentForegroundHex(seed))'), "custom accent foreground is not applied from selected seed");
check(theme.includes('root.style.setProperty("--color-accent-foreground", accentTextForegroundHex(seed, appearance))'), "foreground accent text role is not derived from selected seed");
check(theme.includes('root.style.setProperty("--color-accent-foreground", accentTextForegroundHex(seed, resolved))'), "foreground accent text role is not refreshed when appearance changes");
check(main.includes("applyStoredVisualPreferences();"), "stored visual preferences are not initialized");

const semanticTokens = [
  "--color-status-info-bg", "--color-status-info-text",
  "--color-status-success-bg", "--color-status-success-text",
  "--color-status-warning-bg", "--color-status-warning-text",
  "--color-status-danger-bg", "--color-status-danger-text",
  "--color-status-proposed-bg", "--color-status-proposed-text",
  "--color-status-stale-bg", "--color-status-stale-text",
  "--color-status-unavailable-bg", "--color-status-unavailable-text"
];
for (const token of semanticTokens) {
  const matches = tokens.match(new RegExp(`${token}:`, "g")) ?? [];
  check(matches.length >= 2, `${token} missing light/dark definitions`);
}
check(tokens.includes("--accent-seed: #528B68"), "accent seed token missing");
check(tokens.includes("--color-accent-primary: var(--accent-seed)"), "accent primary must derive from accent seed");
check(tokens.includes("--color-accent-foreground:"), "contrast-safe accent foreground role missing");
check((tokens.match(/--color-accent-hover:\s*var\(--accent-seed\)/g) ?? []).length >= 2, "hover fills must preserve the raw-seed foreground contrast decision");
check((tokens.match(/--color-accent-active:\s*var\(--accent-seed\)/g) ?? []).length >= 2, "active fills must preserve the raw-seed foreground contrast decision");
check((tokens.match(/--color-focus-ring:\s*var\(--color-accent-foreground\)/g) ?? []).length >= 2, "focus ring must use the contrast-safe accent foreground role");
const derivedAccentTokens = [
  "--color-accent-subtle", "--color-accent-surface", "--color-accent-border", "--color-accent-border-strong"
];
for (const token of derivedAccentTokens) {
  const escaped = token.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  check(new RegExp(`${escaped}:\\s*color-mix\\(in oklch, var\\(--accent-seed\\)`).test(tokens), `${token} must derive from the selected accent seed`);
  check((tokens.match(new RegExp(`${escaped}:`, "g")) ?? []).length >= 2, `${token} requires a deterministic fallback before perceptual derivation`);
}
const perceptualSupportIndex = tokens.indexOf("@supports (color: color-mix(in oklch, red, blue))");
check(perceptualSupportIndex >= 0, "perceptual accent overrides require an @supports feature boundary");
check(perceptualSupportIndex < 0 || !tokens.slice(0, perceptualSupportIndex).includes("color-mix(in oklch"), "unsupported color-mix expressions must not override literal fallbacks outside @supports");
const supportedAccentBlock = perceptualSupportIndex >= 0 ? tokens.slice(perceptualSupportIndex) : "";
check(!/--color-(?:accent-hover|accent-active|focus-ring):\s*color-mix/.test(supportedAccentBlock), "interaction fills/focus must not be remixed away from their validated contrast roles");
check(!/--color-status-[^:]+:\s*var\(--accent/.test(tokens), "semantic status token depends on user accent");
const darkTokens = tokens.split('[data-theme="dark"] {')[1]?.split("@supports (color: color-mix")[0] ?? "";
check(darkTokens.includes("--color-text-inverse: #eef2ee"), "dark technical surfaces require a light inverse-text token");
check(darkTokens.includes("--color-text-on-accent: var(--color-accent-on)"), "dark accent fills must use the contrast-derived foreground token");
check(!darkTokens.includes("--color-accent-on:"), "dark appearance must not override contrast-derived accent foreground");
check(tokens.includes("--font-size-caption: 0.75rem"), "12px metadata scale missing");
check(tokens.includes("--font-size-label: 0.8125rem"), "13px label scale missing");
check(tokens.includes("--font-size-body: 0.875rem"), "14px body scale missing");
check(tokens.includes("--font-size-section-title: 1rem"), "16px section scale missing");
check(tokens.includes("--control-height-compact: 1.875rem"), "30px compact control missing");
check(tokens.includes("--control-height-default: 2.1875rem"), "35px default control missing");
check(tokens.includes("@media (prefers-reduced-motion: reduce)"), "reduced-motion rule missing");
check(tokens.includes("--motion-fast: 0ms") && tokens.includes("--motion-standard: 0ms"), "reduced-motion must collapse non-essential motion");
check(!tokens.includes("backdrop-filter"), "structural glass is not authorized in first pass");

const applyAccentBlock = theme.match(/export function applyAccentPreference\([\s\S]*?\n}\n\nexport function applyStoredAccent/)?.[0] ?? "";
const dynamicAccentWrites = [...applyAccentBlock.matchAll(/setProperty\("([^"]+)"/g)].map((match) => match[1]);
const allowedDynamicAccentWrites = new Set(["--accent-seed", "--color-accent-on", "--color-accent-foreground"]);
check(dynamicAccentWrites.length === 3, "accent application must have exactly three isolated dynamic CSS writes");
check(dynamicAccentWrites.every((token) => allowedDynamicAccentWrites.has(token)), "accent application mutates semantic/scientific CSS state");
const declarationValues = (token) => {
  const escaped = token.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  return [...tokens.matchAll(new RegExp(`${escaped}:\\s*([^;]+);`, "g"))].map((match) => match[1].trim());
};
const discoveredScientificTokens = [...new Set(
  [...tokens.matchAll(/(--(?:color-)?(?:scientific|field|plot|chart|series|categorical)[a-z0-9-]*):/gi)].map((match) => match[1])
)];
const invariantProjectionTokens = [...semanticTokens, ...discoveredScientificTokens];
const invariantProjection = Object.fromEntries(invariantProjectionTokens.map((token) => [token, declarationValues(token)]));
const projectAccent = (seed) => ({
  seed,
  dynamicWrites: dynamicAccentWrites.map((token) => [token, token === "--accent-seed" ? seed : "derived-accent-only"]),
  invariants: invariantProjection
});
const warmProjection = projectAccent("#C46B2B");
const coolProjection = projectAccent("#5B6FD8");
check(warmProjection.seed !== coolProjection.seed, "adversarial accent seeds must be materially different");
check(JSON.stringify(warmProjection.invariants) === JSON.stringify(coolProjection.invariants), "warm/cool accent projections changed semantic/scientific channels");
check(!warmProjection.dynamicWrites.some(([token]) => invariantProjectionTokens.includes(token)), "warm accent projection writes an invariant semantic/scientific token");
check(!coolProjection.dynamicWrites.some(([token]) => invariantProjectionTokens.includes(token)), "cool accent projection writes an invariant semantic/scientific token");

const localFonts = [
  ["public/fonts/InstrumentSans-Regular.woff2", '/fonts/InstrumentSans-Regular.woff2'],
  ["public/fonts/InstrumentSans-Medium.woff2", '/fonts/InstrumentSans-Medium.woff2'],
  ["public/fonts/InstrumentSans-SemiBold.woff2", '/fonts/InstrumentSans-SemiBold.woff2'],
  ["public/fonts/IBMPlexMono-Variable.woff2", '/fonts/IBMPlexMono-Variable.woff2']
];
for (const [relative, cssPath] of localFonts) {
  const absolute = path.join(root, relative);
  check(fs.existsSync(absolute) && fs.statSync(absolute).size > 0, `${relative} missing or empty`);
  check(tokens.includes(`url("${cssPath}") format("woff2")`), `${relative} is not referenced as a local woff2 source`);
}
check(!/@font-face[\s\S]*url\(["']?https?:\/\//i.test(tokens), "normal font rendering must not depend on a remote URL");

check(pkg.dependencies?.["@phosphor-icons/react"] === "2.1.10", "Phosphor dependency must be pinned to 2.1.10");
check(lock.packages?.[""]?.dependencies?.["@phosphor-icons/react"] === "2.1.10", "lockfile root must pin Phosphor 2.1.10");
check(lock.packages?.["node_modules/@phosphor-icons/react"]?.version === "2.1.10", "resolved Phosphor package must be 2.1.10");
for (const forbidden of ["lucide-react", "@tabler/icons-react", "phosphor-react"]) {
  check(!(forbidden in (pkg.dependencies ?? {})) && !(forbidden in (pkg.devDependencies ?? {})), `${forbidden} generic icon dependency is forbidden`);
}
check(layout.includes('from "@phosphor-icons/react"'), "allowed shell controls must consume the pinned Phosphor family");
check(layout.includes('aria-hidden="true"'), "decorative shell icons must not duplicate accessible control names");
check(shellCss.includes(".shell-skip-link") && shellCss.includes(".shell-text-link"), "accent foreground link surfaces missing");
const unsafeForegroundLinks = /\.shell-(?:skip-link|text-link)\s*\{[\s\S]*?color:\s*var\(--color-accent-primary\)/g.test(shellCss);
check(!unsafeForegroundLinks, "foreground links must not use the raw Custom accent seed");
check((shellCss.match(/color:\s*var\(--color-accent-foreground\)/g) ?? []).length >= 2, "foreground links must use the contrast-safe accent role");

check(settings.includes('type="color"'), "Settings Custom accent must use the native color input");
check(settings.includes("Reset to Microalgae"), "Settings accent Reset is missing");
check(settings.includes("APPEARANCE_OPTIONS.map"), "Settings appearance choices are missing");
check(settings.includes("ACCENT_OPTIONS.map"), "Settings accent choices are missing");
check(settings.includes("normalizeAccentHex(customAccentDraft)"), "malformed Custom HEX is not guarded before application");
check(settings.includes("const customAccentSwatch = normalizeAccentHex(customAccentDraft)"), "Custom swatch must normalize draft input before CSS application");
check(settings.includes('option === "custom" ? customAccentSwatch'), "Custom swatch is still receiving raw malformed draft input");
check(settingsCss.includes("var(--color-status-danger-text)"), "invalid custom HEX lacks non-accent error semantics");
check(!/saveAISetting\([^\n]*(accent|appearance)/i.test(settings), "visual preferences must not use canonical settings API");

// 100f supersedes the old blanket ban on equipment names: the canonical Process target
// requires a visible future palette, but every authoring affordance must remain inert.
for (const label of ["Heat exchanger", "Pump", "Compressor", "Reactor"]) {
  check(processStage.includes(`"${label}"`), `final Process future palette is missing ${label}`);
}
check((processStage.match(/\bdisabled\b/g) ?? []).length >= 2, "final Process future palette/toolbar is not deterministically disabled");
check(!/\bonClick\s*=|\buseState\b|\buseEffect\b|\bfetch\s*\(/.test(processStage), "Process future affordances gained frontend mutation/runtime authority");
check(!/fetch\(|axios|provider|runner/i.test(theme), "visual preference owner gained runtime execution/API authority");
check(pkg.scripts?.["test:058d"] === "node tests/058d-process-workspace.mjs", "058d deterministic gate changed");
check(pkg.scripts?.["test:100"] === "node tests/100-visual-identity.mjs", "100 deterministic gate not wired");

if (failures.length) {
  console.error("VISUAL-IDENTITY-1 deterministic acceptance failed:");
  for (const failure of failures) console.error(`- ${failure}`);
  process.exit(1);
}
console.log("VISUAL-IDENTITY-1 deterministic acceptance: PASS");
