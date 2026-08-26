import { chromium, firefox } from "playwright";
import fs from "node:fs/promises";
import path from "node:path";
import assert from "node:assert/strict";

const PRODUCT_HEAD = "f086e91fedb5cf8896fbb0ed0702b44bc5999321";
const distAssets = path.resolve("dist/assets");
const files = await fs.readdir(distAssets);
const cssFiles = files.filter((name) => name.endsWith(".css"));
assert.ok(cssFiles.length > 0, "production build emitted no CSS assets");
const css = (await Promise.all(cssFiles.map((name) => fs.readFile(path.join(distAssets, name), "utf8")))).join("\n");
assert.ok(css.includes(".eyebrow"), "compiled production CSS contains no generic eyebrow rule");

function parseRgb(value) {
  const match = value.match(/rgba?\(\s*(\d+)\D+(\d+)\D+(\d+)/i);
  return match ? [Number(match[1]), Number(match[2]), Number(match[3])] : null;
}

function luminance(rgb) {
  const channels = rgb.map((value) => value / 255).map((value) => value <= 0.04045 ? value / 12.92 : ((value + 0.055) / 1.055) ** 2.4);
  return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2];
}

function ratio(first, second) {
  const [high, low] = [luminance(first), luminance(second)].sort((a, b) => b - a);
  return (high + 0.05) / (low + 0.05);
}

const cases = [
  { appearance: "light", seed: "#FFFFFF", foreground: "#000000" },
  { appearance: "dark", seed: "#000000", foreground: "#FFFFFF" }
];

const summary = [];
for (const [browserName, engine] of [["chromium", chromium], ["firefox", firefox]]) {
  const browser = await engine.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 960, height: 540 } });
  for (const testCase of cases) {
    await page.setContent(`<!doctype html><html data-theme="${testCase.appearance}" style="--accent-seed:${testCase.seed};--color-accent-foreground:${testCase.foreground}"><head><style>${css}</style></head><body><section id="proof-surface" style="background:var(--color-bg-surface-raised);padding:24px"><div id="proof-eyebrow" class="eyebrow">VISUAL IDENTITY PROOF</div></section></body></html>`);
    const rendered = await page.evaluate(() => {
      const eyebrow = document.querySelector("#proof-eyebrow");
      const surface = document.querySelector("#proof-surface");
      const eyebrowStyle = getComputedStyle(eyebrow);
      const surfaceStyle = getComputedStyle(surface);
      return {
        color: eyebrowStyle.color,
        background: surfaceStyle.backgroundColor,
        fontSize: eyebrowStyle.fontSize
      };
    });
    const foregroundRgb = parseRgb(rendered.color);
    const backgroundRgb = parseRgb(rendered.background);
    assert.ok(foregroundRgb && backgroundRgb, `${browserName} ${testCase.appearance}: unable to parse rendered colors`);
    const contrast = ratio(foregroundRgb, backgroundRgb);
    assert.ok(contrast >= 4.5, `${browserName} ${testCase.appearance}: eyebrow contrast ${contrast.toFixed(2)} < 4.5`);
    const rawSeedRgb = testCase.seed === "#FFFFFF" ? [255, 255, 255] : [0, 0, 0];
    assert.notDeepEqual(foregroundRgb, rawSeedRgb, `${browserName} ${testCase.appearance}: eyebrow still renders with raw Custom seed`);
    summary.push({ browser: browserName, productHead: PRODUCT_HEAD, ...testCase, rendered, contrast });
  }
  await browser.close();
}

await fs.mkdir("reports/100-eyebrow", { recursive: true });
await fs.writeFile("reports/100-eyebrow/summary.json", `${JSON.stringify(summary, null, 2)}\n`, "utf8");
console.log(`VISUAL-IDENTITY-1 targeted eyebrow browser proof: PASS on ${PRODUCT_HEAD}`);
