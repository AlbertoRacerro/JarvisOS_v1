import assert from 'node:assert/strict';
import { validatePlan, validatePlanId } from './plan-lib.mjs';
import { readFile } from 'node:fs/promises';
for (const id of ['113-memory-models','124-settings-ai','140-coding']) {
  validatePlanId(id);
  validatePlan(JSON.parse(await readFile(new URL(`./plans/${id}.json`, import.meta.url), 'utf8')));
}
for (const bad of ['../x','A','x/y','', 'x'.repeat(65)]) assert.throws(() => validatePlanId(bad));
const base = JSON.parse(await readFile(new URL('./plans/113-memory-models.json', import.meta.url), 'utf8'));
assert.throws(() => validatePlan({...base, schema:'evil'}));
assert.throws(() => validatePlan({...base, steps:[{op:'shell', command:'rm -rf /'}]}));
assert.throws(() => validatePlan({...base, fixture:'../../evil'}));
assert.throws(() => validatePlan({...base, steps:[{op:'navigate', route:'/ok', eval:'alert(1)'}]}));
assert.throws(() => validatePlan({...base, steps:[{op:'assert-visible', locator:{kind:'css', selector:'body; rm -rf /'}}]}));
console.log('browser-proof plan validation PASS');
