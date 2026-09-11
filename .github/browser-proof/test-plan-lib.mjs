import assert from 'node:assert/strict';
import { checkJsonContract, inputEmptyResult, noButtonLabelMatches, validatePlan, validatePlanId } from './plan-lib.mjs';
import { fixturePhaseAllowed, resolveTrustedFixture } from './fixture-registry.mjs';
import { readFile } from 'node:fs/promises';

const runSource = await readFile(new URL('./run.mjs', import.meta.url), 'utf8');
const workflowSource = await readFile(new URL('../workflows/exact-head-browser-proof.yml', import.meta.url), 'utf8');
const plans = new Map();
for (const id of ['113-memory-models','114-literature','124-settings-ai','140-coding']) {
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
assert.equal(plans.get('114-literature').fixture, 'literature-knowledge');
assert.equal(plans.get('114-literature').forbidMutatingRequests, true, 'Literature proof must assert browser-side mutation neutrality');
requireNames('113-memory-models', ['113:trusted-workspace-seed','113:empty-state','113:trusted-version-seed','113:select-a','113:a-exact-identity','113:select-b','113:a-deselected','113:b-exact-identity','113:no-mutation-affordance']);
requireNames('114-literature', ['114:seed-workspace','114:empty-state','114:seed-sources','114:expand-a','114:expand-b','114:a-remains-expanded','114:b-remains-expanded','114:a-preview','114:b-preview','114:open-source-links','114:context-neutral-disclosure','114:no-promotion-affordance']);
requireNames('124-settings-ai', ['124:provider-settings','124:provider:scaleway','124:effective-source-server-match','124:persisted-state-server-match','124:credential-canonical-combination','124:credential-human-summary','124:credential-input-empty','124:no-secret-reference-leak','124:no-provider-execution-affordance','124:provider-egress-state']);
requireNames('140-coding', ['140:repository-truth','140:repository-disclosure','140:repository-no-direct-mutation-buttons','140:runtime-truth','140:runtime-trusted-semantic-delta-schema','140:remote-ahead-summary','140:remote-behind-summary','140:changed-files-summary','140:alignment-rendering','140:local-commit-exact-head','140:local-commit-server-match','140:remote-commit-server-match','140:raw-semantic-delta-server-match','140:development-pipeline','140:runtime-no-direct-mutation-buttons']);
for (const id of ['113-memory-models','124-settings-ai','140-coding']) assert(plans.get(id).steps.some((s) => s.op === 'open-technical-details'), `${id} must retain real Technical details interaction`);
assert(!/prove113|prove124|prove140|PROOF_SCENARIO/.test(runSource), 'generic executor must not retain per-spec control branches');
assert(!runSource.includes('fixture !== "model-version-selection"'), 'generic executor must not retain per-fixture control branches');
assert(!workflowSource.includes('model_version_selection.py'), 'workflow must not execute a fixture-specific script');
assert(!workflowSource.includes('none|model-version-selection'), 'workflow must not hard-code fixture identity choices');
assert(runSource.includes('const mutatingBrowserRequests = []'), 'generic executor must record browser mutation evidence');
assert(runSource.includes('if (plan.forbidMutatingRequests)'), 'generic executor must enforce trusted mutation-free plan policy');
assert(!runSource.includes('planId === "114-literature"'), 'mutation evidence must remain generic rather than spec-specific');

assert.equal(fixturePhaseAllowed('model-version-selection', 'workspace'), true);
assert.equal(fixturePhaseAllowed('model-version-selection', 'versions'), true);
assert.equal(fixturePhaseAllowed('literature-knowledge', 'workspace'), true);
assert.equal(fixturePhaseAllowed('literature-knowledge', 'sources'), true);
assert.equal(fixturePhaseAllowed('literature-knowledge', '../../shell'), false);
assert.equal(fixturePhaseAllowed('../../evil', 'workspace'), false);
assert(resolveTrustedFixture('literature-knowledge', 'sources', new URL('./fixtures', import.meta.url).pathname).endsWith('/literature_knowledge.py'));
assert.throws(() => resolveTrustedFixture('../../evil', 'workspace', new URL('./fixtures', import.meta.url).pathname));
assert.throws(() => resolveTrustedFixture('literature-knowledge', '../../shell', new URL('./fixtures', import.meta.url).pathname));

const p124 = plans.get('124-settings-ai');
assert.equal(p124.artifactMode, 'metadata-only', 'credential proof must disable browser capture artifacts');
assert(!p124.steps.some((s) => s.op === 'screenshot'), 'metadata-only credential proof cannot take screenshots');
assert(p124.steps.some((s) => s.op === 'assert-input-empty' && s.name === '124:credential-input-empty'));
assert(!p124.steps.some((s) => s.op === 'capture-attribute' && s.attribute === 'value'), 'generic proof plan must not capture input values');
assert(p124.steps.find((s) => s.name === '124:no-provider-execution-affordance').caseInsensitive);
for (const name of ['140:repository-no-direct-mutation-buttons','140:runtime-no-direct-mutation-buttons']) {
  assert(plans.get('140-coding').steps.find((s) => s.name === name).caseInsensitive);
}

assert(noButtonLabelMatches(['Save', 'Cancel'], '^(commit|merge|test provider)', true));
assert(!noButtonLabelMatches(['Commit'], '^(commit|merge|test provider)', true));
assert(!noButtonLabelMatches(['MERGE now'], '^(commit|merge|test provider)', true));
assert(!noButtonLabelMatches(['Test provider'], '^(commit|merge|test provider)', true));

const sentinel = 'sk_live_SENTINEL_DO_NOT_PERSIST';
const secretResult = inputEmptyResult(sentinel);
assert.equal(secretResult.pass, false);
assert(!JSON.stringify(secretResult).includes(sentinel), 'secret-safe input assertion detail must not persist observed value');
assert(runSource.includes('const traceEnabled = artifactMode === "full"'));
assert(runSource.includes('if (traceEnabled) await context.tracing.start'));
assert(!runSource.includes('step.attribute === "value"'), 'executor must not retain generic input-value capture');

const p140 = plans.get('140-coding');
const contractStep = p140.steps.find((s) => s.name === '140:runtime-trusted-semantic-delta-schema');
assert(contractStep && contractStep.op === 'assert-json-contract');
const contract = contractStep.contract;
assert.equal(contract.fields.files.fields.filename.minLength, 1);
assert.equal(contract.fields.files.fields.status.minLength, 1);
const good = {
  status:'available', relation:'ahead', ahead_by:2, behind_by:0, partial:false,
  files:[{filename:'x.py',status:'modified',additions:2,deletions:1,patch:null}],
};
assert.equal(checkJsonContract(good, contract).pass, true);
for (const bad of [
  {...good, status:'unknown'},
  {...good, relation:'sideways'},
  {...good, ahead_by:-1},
  {...good, ahead_by:0},
  {...good, behind_by:1},
  {...good, partial:'false'},
  {...good, files:[{filename:'',status:'modified',additions:1,deletions:0,patch:null}]},
  {...good, files:[{filename:'x.py',status:'',additions:1,deletions:0,patch:null}]},
  {...good, files:[{filename:'x.py',status:'modified',additions:-1,deletions:0,patch:null}]},
  {...good, files:[{filename:'x.py',status:'modified',additions:1,deletions:0,patch:7}]},
  {...good, relation:'behind', ahead_by:0, behind_by:0},
  {...good, relation:'diverged', ahead_by:1, behind_by:0},
  {...good, relation:'identical', ahead_by:1, behind_by:0},
]) assert.equal(checkJsonContract(bad, contract).pass, false, `malformed semantic delta must fail: ${JSON.stringify(bad)}`);

for (const bad of ['../x','A','x/y','', 'x'.repeat(65), '140-coding.json']) assert.throws(() => validatePlanId(bad));
const base = plans.get('113-memory-models');
assert.throws(() => validatePlan({...base, schema:'evil'}));
assert.throws(() => validatePlan({...base, artifactMode:'arbitrary'}));
assert.throws(() => validatePlan({...base, forbidMutatingRequests:'yes'}));
assert.throws(() => validatePlan({...base, artifactMode:'metadata-only', steps:[...base.steps, {op:'screenshot', name:'unsafe', file:'unsafe'}]}));
assert.throws(() => validatePlan({...base, steps:[{op:'shell', command:'rm -rf /'}]}));
assert.throws(() => validatePlan({...base, fixture:'../../evil'}));
assert.throws(() => validatePlan({...base, steps:[{op:'navigate', route:'/ok', eval:'alert(1)'}]}));
assert.throws(() => validatePlan({...base, steps:[{op:'assert-visible', locator:{kind:'css', selector:'body; rm -rf /'}}]}));
assert.throws(() => validatePlan({...base, steps:[{op:'same-origin-get', name:'evil', path:'/ok', capture:'x', command:'curl attacker'}]}));
assert.throws(() => validatePlan({...base, steps:[{op:'run-fixture', name:'evil', fixture:'model-version-selection', phase:'../../shell'}]}));
assert.throws(() => validatePlan({...base, fixture:'none', steps:[{op:'run-fixture', name:'mismatch', fixture:'model-version-selection', phase:'versions'}]}));
assert.throws(() => validatePlan({...base, steps:[{op:'run-fixture', name:'wrong-fixture', fixture:'literature-knowledge', phase:'workspace'}]}));
assert.throws(() => validatePlan({...base, steps:[{op:'capture-attribute', name:'secret', locator:{kind:'label',text:'Key'}, attribute:'value', capture:'x'}]}));
assert.throws(() => validatePlan({...base, steps:[{op:'assert-no-button-label', name:'bad', pattern:'x', caseInsensitive:'yes'}]}));
assert.throws(() => validatePlan({...base, steps:[{op:'assert-json-contract', name:'bad', source:'x', pointer:'/x', contract:{fields:{x:{type:'function'}}}}]}));
assert.throws(() => validatePlan({...base, steps:[{op:'assert-json-contract', name:'bad', source:'x', pointer:'/x', contract:{fields:{x:{type:'integer',minLength:1}}}}]}));
assert.throws(() => validatePlan({...base, steps:[{op:'assert-json-contract', name:'bad', source:'x', pointer:'/x', contract:{fields:{x:{type:'string',minLength:-1}}}}]}));
assert.throws(() => validatePlan({...base, steps:[{op:'assert-json-contract', name:'bad', source:'x', pointer:'/x', contract:{fields:{x:{type:'string',minLength:10001}}}}]}));
assert.throws(() => validatePlan({...base, steps:[{op:'assert-json-contract', name:'bad', source:'x', pointer:'/x', contract:{fields:{x:{type:'integer'}},conditions:[{when:{field:'x',equals:1},then:[{field:'x',op:'eval',value:1}]}]}}]}));
console.log('browser-proof plan validation, fixture registry, secret safety and compatibility PASS');
