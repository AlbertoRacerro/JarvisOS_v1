import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const [app, api, page] = await Promise.all([
  readFile(new URL("../src/App.tsx", import.meta.url), "utf8"),
  readFile(new URL("../src/api/modelDossier.ts", import.meta.url), "utf8"),
  readFile(new URL("../src/pages/ModelDossier.tsx", import.meta.url), "utf8")
]);

assert.match(app, /case "memory-models"/);
assert.match(app, /<ModelDossier workspaceId=/);
assert.match(api, /\/model-dossiers/);
assert.match(api, /encodeURIComponent\(modelVersionId\)/);
assert.match(page, /model_version_id/);
assert.match(page, /Browsing is context-neutral/);
assert.match(page, /does not add records to Jarvis context/);
assert.doesNotMatch(page, /createModel|updateModel|postJson|putJson|deleteJson/);

console.log("113 model dossier frontend contract: PASS");
