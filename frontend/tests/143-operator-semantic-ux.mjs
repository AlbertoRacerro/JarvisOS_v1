import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const coding = readFileSync(new URL("../src/pages/CodingWorkbench.tsx", import.meta.url), "utf8");
const models = readFileSync(new URL("../src/pages/ModelDossier.tsx", import.meta.url), "utf8");
const settings = readFileSync(new URL("../src/pages/Settings.tsx", import.meta.url), "utf8");
const status = readFileSync(new URL("../../docs/specs/STATUS.md", import.meta.url), "utf8");

assert.match(status, /\| 143 \| in_review \| \[#589\]/);
assert.match(coding, /runtime\?\.semantic_delta/);
assert.match(coding, /server-owned 119 semantic delta/);
assert.match(coding, /function RawJson/);
assert.match(coding, /<details><summary>Technical details<\/summary>/);
assert.doesNotMatch(coding, /<pre className="final-fusion__searchbox">\{JSON\.stringify\(prEvidence/);
assert.doesNotMatch(coding, /<pre className="final-fusion__searchbox">\{JSON\.stringify\(pipeline/);
assert.doesNotMatch(coding, /<span>›<\/span>/);
assert.doesNotMatch(models, /<span>›<\/span>/);
assert.match(models, /<button type="button" className="final-fusion__disclosure-row"/);
assert.match(settings, /providerName\(provider\.provider_id\)/);
assert.match(settings, /Provider code · \{provider\.provider_id\}/);
assert.match(settings, /<details><summary>Technical details<\/summary>/);
assert.doesNotMatch(settings, /<strong>\{provider\.provider_id\}<\/strong>/);

console.log("spec 143 operator semantic UX contract passed");
