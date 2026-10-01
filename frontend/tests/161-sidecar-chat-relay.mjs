// Spec 161 source-level and pure-function checks; browser behaviour is proven separately.
import assert from "node:assert/strict";
import fs from "node:fs";
import { modelDisplayName } from "../src/components/ai/modelDisplayName.ts";

const read = (path) => fs.readFileSync(new URL(`../${path}`, import.meta.url), "utf8");
const sidecar = read("src/components/ai/useJarvisSidecar.tsx");
const shellSidecar = read("src/components/shell/ContextualSidecar.tsx");
const layout = read("src/components/Layout.tsx");
const api = read("src/api/threads.ts");
const shellCss = read("src/styles/final-fusion-shell-overrides.css");
const contextMenu = read("src/components/ui/ContextMenu.tsx");

// Human model names: concise, derived from the recorded id, never invented.
for (const [id, name] of [
  ["gemma-4-12b-it-qat-q4_0", "Gemma 4 12B"],
  ["/models/gemma-4-12b-it-qat-q4_0.gguf", "Gemma 4 12B"],
  ["Qwen3.5-4B-Q6_K.gguf", "Qwen 3.5 4B"],
  ["claude-opus-5-5", "Claude Opus 5.5"],
  ["claude-sonnet-5-5", "Claude Sonnet 5.5"],
  ["gpt-6-luna", "GPT-6 Luna"],
  ["gpt-6.1-sol", "GPT-6.1 Sol"],
  ["deepseek-v4-flash-0731", "DeepSeek V4 Flash"]
]) assert.equal(modelDisplayName(id), name, id);
assert.equal(modelDisplayName(null, "codex"), "Codex");
assert.equal(modelDisplayName(null), "Unknown model");

// Chat-first hierarchy: no duplicate headings or legacy form labels.
assert.doesNotMatch(shellSidecar, /Jarvis &amp; Properties|role="tablist"/);
for (const legacy of ["Jarvis agent (Hermes)\" : responderLabel", "Send to Jarvis\"", "<span>Conversation</span>", "<span>Responder</span>", "<span>Send to</span>", "Ask Jarvis about this workspace."]) {
  assert.ok(!sidecar.includes(legacy), `legacy Sidecar chrome still present: ${legacy}`);
}
assert.match(sidecar, /jarvis-turn--user/);
assert.match(sidecar, /jarvis-sidecar__history/);
assert.ok(sidecar.indexOf("jarvis-sidecar__composer") < sidecar.indexOf("jarvis-sidecar__history"), "history must sit below the composer");
assert.match(sidecar, /SidecarChromeActions/);
assert.match(sidecar, /reason_code === "LLAMACPP_AUTH_REQUIRED"/, "a protected llama-server is not presented as a usable responder");
assert.match(sidecar, /function ResponderMenu[\s\S]*useContext\(SidecarChrome\)[\s\S]*id: "show-properties", label: "Show properties"/);
assert.doesNotMatch(sidecar, /aria-pressed=\{chrome\.propertiesOpen\}/, "Properties stays in the compact secondary controls, outside the required header row");
assert.match(shellSidecar, /closest\('\[role="menu"\]'\)/, "Escape in a menu must not close the whole Sidecar");
assert.match(contextMenu, /if \(!position\) return;[\s\S]*querySelector<HTMLButtonElement>\("button:not\(:disabled\)"\)[\s\S]*\}, \[position\]\)/, "menus move keyboard focus after their final position is measured");
assert.match(shellSidecar, /Back to Jarvis/);

// Relay is the default escalation; the API path stays an explicit choice; no silent fallback.
assert.match(sidecar, /onClick=\{onRelay\}/);
assert.match(sidecar, /"Escalate with Relay"/);
assert.match(sidecar, /"Escalate with API key…"/);
assert.match(sidecar, /Nothing was sent to a paid API\./);
assert.match(sidecar, /subscription, no API charge/);
assert.match(api, /relay-escalation-draft/);
assert.match(api, /relay-escalate/);

// Closing a shell region leaves an on-screen reopen affordance.
assert.match(layout, /shell-reopen--sidecar/);
assert.match(layout, /shell-reopen--navigator/);
assert.match(shellCss, /--jarvis-width: clamp\(300px, 24vw, 420px\)/);
console.log("161 Sidecar chat and Relay escalation checks passed");
