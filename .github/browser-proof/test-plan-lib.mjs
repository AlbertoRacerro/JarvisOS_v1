import assert from 'node:assert/strict';
import { validatePlan, validatePlanId } from './plan-lib.mjs';
import { readFile } from 'node:fs/promises';

const runSource = await readFile(new URL('./run.mjs', import.meta.url), 'utf8');
const plans = new Map();
for (const id of ['113-memory-models','124-settings-ai','140-coding']) {
  validatePlanId(id);
  const plan = JSON.parse(await readFile(new URL(`./plans/${id}.json`, import.meta.url), 'utf8'));
  validatePlan(plan);
  plans.set(id, plan);
}
const names = (id) => new Set(plans.get(id).steps.map((step) => step.name));
const requireNames = (id, required) => {
  const actual = names(id);
  for (const name of required) assert(actual.has(name), `${id} missing compatibility assertion ${name}`);
};
assert.equal(plans.get('113-memory-models').fixture, 'model-version-selection');
requireNames('113-memory-models', ['113:empty-state','113:trusted-version-seed','113:select-a','113:a-exact-identity','113:select-b','113:a-deselected','113:b-exact-identity','113:no-mutation-affordance']);
requireNames('124-settings-ai', ['124:provider-settings','124:provider:scaleway','124:effective-source-server-match','124:persisted-state-server-match','124:credential-canonical-combination','124:credential-human-summary','124:credential-input-empty','124:no-secret-reference-leak','124:no-provider-execution-affordance','124:provider-egress-state']);
requireNames('140-coding', ['140:repository-truth','140:repository-disclosure','140:repository-no-direct-mutation-buttons','140:runtime-truth','140:remote-ahead-summary','140:remote-behind-summary','140:changed-files-summary','140:alignment-rendering','140:local-commit-exact-head','140:local-commit-server-match','140:remote-commit-server-match','140:raw-semantic-delta-server-match','140:development-pipeline','140:runtime-no-direct-mutation-buttons']);
for (const id of plans.keys()) assert(plans.get(id).steps.some((s) => s.op === 'open-technical-details'), `${id} must retain real Technical details interaction`);
assert(!/prove113|prove124|prove140|PROOF_SCENARIO/.test(runSource), 'generic executor must not retain per-spec control branches');

for (const bad of ['../x','A','x/y','', 'x'.repeat(65), '140-coding.json']) assert.throws(() => validatePlanId(bad));
const base = plans.get('113-memory-models');
assert.throws(() => validatePlan({...base, schema:'evil'}));
assert.throws(() => validatePlan({...base, steps:[{op:'shell', command:'rm -rf /'}]}));
assert.throws(() => validatePlan({...base, fixture:'../../evil'}));
assert.throws(() => validatePlan({...base, steps:[{op:'navigate', route:'/ok', eval:'alert(1)'}]}));
assert.throws(() => validatePlan({...base, steps:[{op:'assert-visible', locator:{kind:'css', selector:'body; rm -rf /'}}]}));
assert.throws(() => validatePlan({...base, steps:[{op:'same-origin-get', name:'evil', path:'/ok', capture:'x', command:'curl attacker'}]}));
assert.throws(() => validatePlan({...base, steps:[{op:'run-fixture', name:'evil', fixture:'model-version-selection', phase:'../../shell'}]}));
assert.throws(() => validatePlan({...base, fixture:'none', steps:[{op:'run-fixture', name:'mismatch', fixture:'model-version-selection', phase:'versions'}]}));
console.log('browser-proof plan validation and compatibility PASS');
