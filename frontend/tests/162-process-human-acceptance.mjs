import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const read = (path) => readFileSync(resolve(root, path), "utf8");
const editor = read("src/stages/ProcessDraftEditor.tsx");
const stage = read("src/stages/ProcessStage.tsx");
const api = read("src/api/processDraft.ts");
const menu = read("src/components/ui/ContextMenu.tsx");

assert.match(editor, /set_orientation/);
assert.match(editor, /onContextMenu=\{\(event\).*unitMenu\.targetProps\.onContextMenu/);
assert.match(editor, /unitMenu\.targetProps\.onKeyDown/);
assert.match(editor, /<MenuButton label=\{`Orientation for/);
assert.match(editor, /unit\.flip_x/);
assert.match(editor, /unit\.flip_y/);
assert.match(editor, /set_orientation.*id: contextUnit\.id/);
assert.match(editor, /data-testid="readiness-chip"/);
assert.match(editor, /blockers.*warning/);
assert.match(editor, /Readiness guidance/);
assert.match(editor, /run\.solve\.errors\.map/);
assert.match(editor, /error_detail\.dwsim_message/);
assert.match(editor, /molar_flow/);
assert.match(editor, /volumetric_flow/);
assert.match(editor, /Composition basis/);
assert.match(api, /molar_flow\?: StoredQuantity/);
assert.match(api, /vapor_fraction\?: StoredQuantity/);
assert.match(api, /solve_errors\?: string\[\]/);
assert.match(menu, /event\.key !== "ContextMenu"/);
assert.match(menu, /event\.key === "F10" && event\.shiftKey/);
assert.match(editor, /className="draft-run-button"/);
assert.match(editor, /<details className="draft-secondary">/);
assert.match(stage, /<details className="process-advanced">/);
assert.match(editor, /values below describe that revision/i);
assert.match(editor, /unitWidth = \(unit: DraftObject\) => Math\.max\(UNIT_W/);

console.log("162 process human acceptance source contract: PASS");
