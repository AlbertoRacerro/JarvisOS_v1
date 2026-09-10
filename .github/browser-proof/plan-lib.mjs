import { readFile } from 'node:fs/promises';
import { basename, join, resolve, sep } from 'node:path';

export const PLAN_SCHEMA = 'jarvisos.browser-proof-plan.v1';
export const PLAN_ID_RE = /^[a-z0-9][a-z0-9-]{0,63}$/;
export const ALLOWED_FIXTURES = new Set(['none', 'model-version-selection']);
export const ALLOWED_ROLES = new Set(['button', 'heading', 'region', 'textbox', 'link']);
export const ALLOWED_ATTRIBUTES = new Set(['aria-pressed', 'data-provider-egress-state', 'value']);
const STEP_KEYS = {
  'navigate': ['op','name','route'],
  'reload': ['op','name'],
  'assert-visible': ['op','name','locator'],
  'assert-count': ['op','name','locator','equals'],
  'click': ['op','name','locator'],
  'open-technical-details': ['op','name','locator'],
  'assert-attribute': ['op','name','locator','attribute','equals'],
  'same-origin-get': ['op','name','path','capture'],
  'capture-text': ['op','name','locator','capture','stripPrefix'],
  'capture-attribute': ['op','name','locator','attribute','capture'],
  'capture-json-find': ['op','name','source','arrayPointer','field','equals','capture'],
  'assert-value-equals': ['op','name','left','right'],
  'map-value': ['op','name','source','capture','cases'],
  'assert-text-template': ['op','name','locator','template'],
  'assert-text-template-map': ['op','name','locator','source','cases'],
  'assert-json-deep-equals': ['op','name','locator','right'],
  'assert-body-absent': ['op','name','forbidden','caseInsensitive'],
  'assert-no-button-label': ['op','name','pattern'],
  'assert-all-attributes-in': ['op','name','locator','attribute','allowed','count'],
  'run-fixture': ['op','name','fixture','phase'],
  'screenshot': ['op','name','file'],
};
export const ALLOWED_OPS = new Set(Object.keys(STEP_KEYS));

const isObject = (value) => value !== null && typeof value === 'object' && !Array.isArray(value);
const fail = (message) => { throw new Error(`invalid proof plan: ${message}`); };
const boundedString = (value, name, max = 500) => {
  if (typeof value !== 'string' || value.length === 0 || value.length > max) fail(`${name} must be a non-empty string <= ${max}`);
};

export function validatePlanId(planId) {
  if (typeof planId !== 'string' || !PLAN_ID_RE.test(planId)) fail('unsafe plan id');
  return planId;
}

export function validateLocator(locator, depth = 0) {
  if (!isObject(locator)) fail('locator must be an object');
  if (depth > 4) fail('locator nesting too deep');
  const kind = locator.kind;
  if (kind === 'role') {
    if (!ALLOWED_ROLES.has(locator.role)) fail(`unsupported role ${locator.role}`);
    boundedString(locator.name, 'locator.name', 300);
    if ('exact' in locator && typeof locator.exact !== 'boolean') fail('locator.exact must be boolean');
    if ('regex' in locator && typeof locator.regex !== 'boolean') fail('locator.regex must be boolean');
    if (locator.exact && locator.regex) fail('locator cannot be exact and regex');
    for (const key of Object.keys(locator)) if (!['kind','role','name','exact','regex'].includes(key)) fail(`unknown role locator key ${key}`);
    return;
  }
  if (kind === 'text' || kind === 'label') {
    boundedString(locator.text, 'locator.text', 500);
    if ('exact' in locator && typeof locator.exact !== 'boolean') fail('locator.exact must be boolean');
    if ('regex' in locator && typeof locator.regex !== 'boolean') fail('locator.regex must be boolean');
    if (locator.exact && locator.regex) fail('locator cannot be exact and regex');
    for (const key of Object.keys(locator)) if (!['kind','text','exact','regex'].includes(key)) fail(`unknown ${kind} locator key ${key}`);
    return;
  }
  if (kind === 'testid') {
    if (typeof locator.testid !== 'string' || !/^[A-Za-z0-9:_-]{1,120}$/.test(locator.testid)) fail('unsafe testid');
    for (const key of Object.keys(locator)) if (!['kind','testid'].includes(key)) fail(`unknown testid locator key ${key}`);
    return;
  }
  if (kind === 'css') {
    boundedString(locator.selector, 'locator.selector', 300);
    if (!/^[A-Za-z0-9_\-#.:[\]=\"' >+~()*^$|,]+$/.test(locator.selector)) fail('unsafe css selector vocabulary');
    for (const key of Object.keys(locator)) if (!['kind','selector'].includes(key)) fail(`unknown css locator key ${key}`);
    return;
  }
  if (kind === 'within') {
    validateLocator(locator.parent, depth + 1);
    validateLocator(locator.child, depth + 1);
    if ('first' in locator && typeof locator.first !== 'boolean') fail('locator.first must be boolean');
    for (const key of Object.keys(locator)) if (!['kind','parent','child','first'].includes(key)) fail(`unknown within locator key ${key}`);
    return;
  }
  fail(`unsupported locator kind ${kind}`);
}

function validateValueRef(ref, name) {
  if (!isObject(ref)) fail(`${name} must be object`);
  const keys = Object.keys(ref);
  if (keys.length !== 1) fail(`${name} must have exactly one source`);
  if ('capture' in ref) boundedString(ref.capture, `${name}.capture`, 64);
  else if ('env' in ref) {
    boundedString(ref.env, `${name}.env`, 64);
    if (!['expectedHead','repository'].includes(ref.env)) fail(`unsupported env ref ${ref.env}`);
  } else if ('literal' in ref) {
    if (!['string','number','boolean'].includes(typeof ref.literal) && ref.literal !== null) fail(`${name}.literal unsupported type`);
  } else if ('json' in ref) {
    if (!isObject(ref.json)) fail(`${name}.json must be object`);
    boundedString(ref.json.source, `${name}.json.source`, 64);
    if (typeof ref.json.pointer !== 'string' || !ref.json.pointer.startsWith('/') || ref.json.pointer.length > 300) fail(`${name}.json.pointer invalid`);
    if ('length' in ref.json && typeof ref.json.length !== 'boolean') fail(`${name}.json.length must be boolean`);
    for (const key of Object.keys(ref.json)) if (!['source','pointer','length'].includes(key)) fail(`unknown json ref key ${key}`);
  } else fail(`${name} has unsupported source`);
}

function validateTemplate(template, name) {
  boundedString(template, name, 1000);
  const tokens = [...template.matchAll(/{{([^}]+)}}/g)].map((match) => match[1]);
  for (const token of tokens) {
    if (/^capture:[A-Za-z][A-Za-z0-9_-]{0,63}$/.test(token)) continue;
    if (/^env:(expectedHead|repository)(\|urlencode)?$/.test(token)) continue;
    if (/^json:[A-Za-z][A-Za-z0-9_-]{0,63}:\/[^|}]*(\|(length|urlencode))?$/.test(token)) continue;
    fail(`unsupported template token ${token}`);
  }
}

export function validatePlan(plan) {
  if (!isObject(plan)) fail('root must be an object');
  for (const key of Object.keys(plan)) if (!['schema','id','fixture','steps'].includes(key)) fail(`unknown root key ${key}`);
  if (plan.schema !== PLAN_SCHEMA) fail('unknown schema');
  validatePlanId(plan.id);
  const fixture = plan.fixture ?? 'none';
  if (!ALLOWED_FIXTURES.has(fixture)) fail(`unknown fixture ${fixture}`);
  if (!Array.isArray(plan.steps) || plan.steps.length < 1 || plan.steps.length > 200) fail('steps must contain 1..200 entries');
  for (const [index, step] of plan.steps.entries()) {
    if (!isObject(step)) fail(`step ${index} must be object`);
    if (!ALLOWED_OPS.has(step.op)) fail(`unknown op ${step.op}`);
    for (const key of Object.keys(step)) if (!STEP_KEYS[step.op].includes(key)) fail(`step ${index} unknown key ${key}`);
    if ('name' in step) boundedString(step.name, `step ${index}.name`, 160);
    if ('locator' in step) validateLocator(step.locator);
    if (step.op === 'navigate') {
      if (typeof step.route !== 'string' || !/^\/[A-Za-z0-9_./?=&%:-]*$/.test(step.route) || step.route.length > 300) fail(`step ${index} unsafe route`);
    } else if (step.op === 'assert-count') {
      if (!step.locator || !Number.isInteger(step.equals) || step.equals < 0 || step.equals > 1000) fail(`step ${index} invalid count`);
    } else if (['assert-visible','click','open-technical-details'].includes(step.op)) {
      if (!step.locator) fail(`step ${index} locator required`);
    } else if (step.op === 'assert-attribute') {
      if (!step.locator || !ALLOWED_ATTRIBUTES.has(step.attribute) || typeof step.equals !== 'string') fail(`step ${index} invalid attribute assertion`);
    } else if (step.op === 'same-origin-get') {
      if (typeof step.path !== 'string' || !/^\/[A-Za-z0-9_./?=&%:{}|\-]*$/.test(step.path) || step.path.length > 500) fail(`step ${index} unsafe request path`);
      boundedString(step.capture, `step ${index}.capture`, 64); validateTemplate(step.path, `step ${index}.path`);
    } else if (step.op === 'capture-text') {
      if (!step.locator) fail(`step ${index} locator required`); boundedString(step.capture, `step ${index}.capture`, 64);
      if ('stripPrefix' in step) boundedString(step.stripPrefix, `step ${index}.stripPrefix`, 300);
    } else if (step.op === 'capture-attribute') {
      if (!step.locator || !ALLOWED_ATTRIBUTES.has(step.attribute)) fail(`step ${index} invalid capture attribute`); boundedString(step.capture, `step ${index}.capture`, 64);
    } else if (step.op === 'capture-json-find') {
      boundedString(step.source, `step ${index}.source`, 64); if (typeof step.arrayPointer !== 'string' || !step.arrayPointer.startsWith('/')) fail(`step ${index} arrayPointer invalid`);
      boundedString(step.field, `step ${index}.field`, 100); boundedString(step.equals, `step ${index}.equals`, 300); boundedString(step.capture, `step ${index}.capture`, 64);
    } else if (step.op === 'assert-value-equals') {
      validateValueRef(step.left, `step ${index}.left`); validateValueRef(step.right, `step ${index}.right`);
    } else if (step.op === 'map-value') {
      validateValueRef(step.source, `step ${index}.source`); boundedString(step.capture, `step ${index}.capture`, 64);
      if (!isObject(step.cases) || Object.keys(step.cases).length < 1 || Object.keys(step.cases).length > 30) fail(`step ${index} cases invalid`);
      for (const [key, value] of Object.entries(step.cases)) { boundedString(key, `step ${index} case key`, 100); boundedString(value, `step ${index} case value`, 500); }
    } else if (step.op === 'assert-text-template') {
      if (!step.locator) fail(`step ${index} locator required`); validateTemplate(step.template, `step ${index}.template`);
    } else if (step.op === 'assert-text-template-map') {
      if (!step.locator) fail(`step ${index} locator required`); validateValueRef(step.source, `step ${index}.source`);
      if (!isObject(step.cases) || Object.keys(step.cases).length < 1 || Object.keys(step.cases).length > 30) fail(`step ${index} cases invalid`);
      for (const [key, value] of Object.entries(step.cases)) { boundedString(key, `step ${index} case key`, 100); validateTemplate(value, `step ${index} case value`); }
    } else if (step.op === 'assert-json-deep-equals') {
      if (!step.locator) fail(`step ${index} locator required`); validateValueRef(step.right, `step ${index}.right`);
    } else if (step.op === 'assert-body-absent') {
      if (!Array.isArray(step.forbidden) || step.forbidden.length < 1 || step.forbidden.length > 40) fail(`step ${index} forbidden invalid`);
      for (const item of step.forbidden) boundedString(item, `step ${index}.forbidden`, 120);
      if ('caseInsensitive' in step && typeof step.caseInsensitive !== 'boolean') fail(`step ${index} caseInsensitive invalid`);
    } else if (step.op === 'assert-no-button-label') {
      boundedString(step.pattern, `step ${index}.pattern`, 300);
    } else if (step.op === 'assert-all-attributes-in') {
      if (!step.locator || !ALLOWED_ATTRIBUTES.has(step.attribute) || !Array.isArray(step.allowed) || step.allowed.length < 1 || step.allowed.length > 20) fail(`step ${index} attribute set invalid`);
      for (const item of step.allowed) boundedString(item, `step ${index}.allowed`, 120);
      if (!Number.isInteger(step.count) || step.count < 0 || step.count > 1000) fail(`step ${index} count invalid`);
    } else if (step.op === 'run-fixture') {
      if (!ALLOWED_FIXTURES.has(step.fixture) || step.fixture === 'none') fail(`step ${index} fixture invalid`);
      if (!['versions'].includes(step.phase)) fail(`step ${index} fixture phase invalid`);
    } else if (step.op === 'screenshot') {
      if (typeof step.file !== 'string' || !/^[A-Za-z0-9_-]{1,80}$/.test(step.file)) fail(`step ${index} screenshot name invalid`);
    }
  }
  return plan;
}

export async function loadTrustedPlan(planId, planDir) {
  validatePlanId(planId);
  const root = resolve(planDir);
  const path = resolve(join(root, `${planId}.json`));
  if (!path.startsWith(`${root}${sep}`) || basename(path) !== `${planId}.json`) fail('plan path escaped trusted directory');
  let raw;
  try { raw = await readFile(path, 'utf8'); } catch (error) { throw new Error(`trusted proof plan not found: ${planId}`, { cause: error }); }
  let plan;
  try { plan = JSON.parse(raw); } catch (error) { throw new Error(`trusted proof plan is not valid JSON: ${planId}`, { cause: error }); }
  validatePlan(plan);
  if (plan.id !== planId) fail('plan id does not match trusted filename');
  return plan;
}

export function jsonPointer(root, pointer) {
  if (pointer === '') return root;
  if (typeof pointer !== 'string' || !pointer.startsWith('/')) throw new Error('invalid JSON pointer');
  return pointer.slice(1).split('/').reduce((value, token) => {
    const key = token.replace(/~1/g, '/').replace(/~0/g, '~');
    if (value === null || value === undefined || !Object.prototype.hasOwnProperty.call(value, key)) throw new Error(`JSON pointer missing ${pointer}`);
    return value[key];
  }, root);
}
