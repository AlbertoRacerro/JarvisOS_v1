import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const [app, api, panel] = await Promise.all([
  readFile(new URL("../src/App.tsx", import.meta.url), "utf8"),
  readFile(new URL("../src/api/projectSearch.ts", import.meta.url), "utf8"),
  readFile(new URL("../src/components/fusion/ProjectSearchPanel.tsx", import.meta.url), "utf8")
]);

assert.match(app, /<ProjectSearchPanel\s+workspaceId=/);
assert.match(api, /\/project-search\?/);
assert.match(api, /\{ signal \}/);

assert.match(panel, /Enter at least two characters to search this workspace\./);
assert.match(panel, /Searching project records…/);
assert.match(panel, /No project records match this literal query\./);
assert.match(panel, /Project search unavailable/);
assert.match(panel, /Showing the first bounded results\./);

assert.match(panel, /function changeQuery\(nextQuery: string\)/);
assert.match(panel, /requestGeneration\.current \+= 1;\s*setQuery\(nextQuery\)/);
assert.match(panel, /if \(requestGeneration\.current !== generation\) return;/);
assert.match(panel, /\}, \[workspaceId\]\);/);

assert.match(panel, /navigate\(navigationTarget\(result\)\)/);
assert.match(panel, /Project Basis|Project knowledge/);
assert.match(panel, /Searching does not add Jarvis context\./);
assert.doesNotMatch(panel, /Add to Jarvis|postJson|putJson|deleteJson|execute|commit/i);

console.log("115 project search frontend contract: PASS");
