import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const stage = readFileSync(resolve(root, "src/stages/ProcessStage.tsx"), "utf8");
const generated = readFileSync(resolve(root, "src/api/generated/dwsimEditor.ts"), "utf8");
const fail = (message) => { throw new Error(`149 dynamics controls acceptance failed: ${message}`); };
const has = (text, value, message) => { if (!text.includes(value)) fail(message); };

for (const kind of ["controller_set", "event_add", "event_remove", "dynamics_run", "state_save", "state_restore"]) {
  has(generated, `kind: "${kind}"`, `generated command contract missing ${kind}`);
  has(stage, `kind: "${kind}"`, `operator control missing ${kind}`);
  has(stage, `can("${kind}")`, `${kind} must honor projected server availability`);
}
for (const field of ["expected_revision: projection.revision", "setProjection(result.projection)", "dynamicsProjection.controllers", "dynamicsProjection.event_sets", "dynamicsProjection.saved_states", "dynamicsProjection.last_dynamic_run", "dynamicsUnavailableReason"])
  has(stage, field, `dynamics UI must preserve server authority/readback: ${field}`);
if (/fetch\s*\(/.test(stage)) fail("dynamics controls must use the existing API command path");
console.log("149 dynamics controls deterministic acceptance: PASS");
