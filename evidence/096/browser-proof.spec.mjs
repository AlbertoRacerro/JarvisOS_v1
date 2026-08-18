import { test, expect } from '@playwright/test';

const APP = 'http://127.0.0.1:4173';
const API = 'http://127.0.0.1:8000';
const workspace = { id: 'ws-1', name: 'Evidence workspace', slug: 'evidence', description: null, status: 'active', created_at: '2026-08-18T00:00:00Z', updated_at: '2026-08-18T00:00:00Z' };
const hostile = '<img src=x onerror="window.__pwned=1">' + 'X'.repeat(1400);
const longLog = '<script>window.__pwned=2</script>\n' + 'log-line '.repeat(1400) + '\n' + 'Y'.repeat(1600);
const run = {
  id: 'run-' + 'a'.repeat(180), workspace_id: 'ws-1', model_version_id: 'model-' + 'b'.repeat(180),
  run_label: 'Hostile bounded run', status: 'succeeded',
  input_payload: JSON.stringify({ inlet_pressure_bar: 34, hostile, nested: { token: 'Z'.repeat(1800) } }),
  parameter_payload: JSON.stringify({ tube_length_m: 2, inner_diameter_m: 0.07, outer_diameter_m: 0.08 }),
  output_payload: JSON.stringify({ conversion: 0.82, note: hostile }),
  started_at: '2026-08-18T09:00:00Z', completed_at: '2026-08-18T09:00:04Z', created_at: '2026-08-18T09:00:00Z', notes: 'Browser evidence fixture'
};
const memoryRecord = {
  id: 'assumption-' + 'c'.repeat(180), record_kind: 'assumption', workspace_id: 'ws-1', status: 'proposed', origin: 'user',
  source_ai_job_id: 'job-' + 'd'.repeat(180), promoted_at: null, created_at: '2026-08-18T09:00:00.123456+00:00', updated_at: '2026-08-18T09:00:00.123456+00:00',
  title: null, statement: 'Pressure drop neglected ' + hostile, decision_text: null, name: null, source_ref: null, notes: 'No impact claim exists.',
  supersedes_parameter_id: null, scope: null, confidence: null, symbol: null, value: null, unit: null, value_status: null, value_min: null, value_max: null,
  rationale: null, linked_run_id: null
};

function interaction(i, assistant = 'Safe advisory ' + hostile) {
  return { id: `i-${i}`, request_id: `req-${i}`, interaction_index: i, user_text: `User message ${i} ${'u'.repeat(250)}`, assistant_text: assistant,
    assistant_text_truncated: false, flow_id: `flow-${i}`, persistence_state: 'persisted', persistence_error: null, flow_state: 'completed', terminal_reason: null,
    attempt_count: 1, terminal_attempt_id: null, proposal_ids: [], proposal_count: 0, proposals_truncated: false,
    created_at: '2026-08-18T09:00:00Z', updated_at: '2026-08-18T09:00:00Z' };
}
let threadInteractions = Array.from({length: 14}, (_, i) => interaction(i));

async function installMocks(page, counters) {
  await page.route(`${API}/**`, async route => {
    const req = route.request();
    const url = new URL(req.url());
    const p = url.pathname;
    counters.all.push(`${req.method()} ${p}`);
    const json = body => route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(body) });
    if (p === '/workspaces') return json([workspace]);
    if (p === '/ai/threads' && req.method() === 'GET') return json({ threads: [{ id:'thread-1', workspace_id:'ws-1', title:'Evidence thread', created_at:'2026-08-18T09:00:00Z', last_activity_at:'2026-08-18T09:00:00Z' }] });
    if (p === '/ai/threads/thread-1' && req.method() === 'GET') return json({ id:'thread-1', workspace_id:'ws-1', title:'Evidence thread', created_at:'2026-08-18T09:00:00Z', last_activity_at:'2026-08-18T09:00:00Z', interactions: threadInteractions, has_older:false });
    if (p === '/ai/context/packs/preview') return json({ context_digest:'digest-096', context_sources_manifest:[], char_count:120, estimated_token_count:30, included_count:1, dropped_count:0, budget_chars:8000 });
    if (p === '/ai/threads/thread-1/interactions' && req.method() === 'POST') {
      counters.interactions += 1;
      await new Promise(r => setTimeout(r, 700));
      const body = req.postDataJSON();
      const next = interaction(99, 'Durable evidence response');
      next.user_text = body.prompt;
      threadInteractions = [...threadInteractions, next];
      return json({ interaction: next });
    }
    if (p === '/workspaces/ws-1/simulation-runs' && req.method() === 'GET') return json([run]);
    if (p === `/workspaces/ws-1/simulation-runs/${encodeURIComponent(run.id)}`) return json(run);
    if (p.endsWith('/logs')) return json([{ id:'log-1', workspace_id:'ws-1', simulation_run_id:run.id, stream:'stdout', content:longLog, truncated:false, created_at:'2026-08-18T09:00:05Z' }]);
    if (p.endsWith('/artifacts')) return json([{ artifact_id:'artifact-1', workspace_id:'ws-1', simulation_run_id:run.id, role:'output', artifact_type:'text', filename:'artifact-'+'f'.repeat(500)+'.txt', size_bytes:1234, created_at:'2026-08-18T09:00:05Z', source_ref:'source-'+'s'.repeat(600), source_module:'evidence', mime_type:'text/plain', sha256:'a'.repeat(64), status:'registered', under_data_root:true }]);
    if (p === '/memory/proposals') return json([memoryRecord]);
    if (p.includes('/analytics') || p.includes('/comparison')) return json({});
    return json([]);
  });
}

async function openRuns(page) {
  await page.goto(`${APP}/runs`);
  await expect(page.getByRole('heading', {name:'Runs', level:1})).toBeVisible();
  await expect(page.getByText('Hostile bounded run').first()).toBeVisible();
}

function viewportOverflow(page) {
  return page.evaluate(() => ({ scrollWidth: document.documentElement.scrollWidth, clientWidth: document.documentElement.clientWidth, scrollHeight: document.documentElement.scrollHeight, innerHeight: window.innerHeight }));
}

test('096 readiness browser matrix', async ({ page }) => {
  const counters = { interactions: 0, all: [] };
  await installMocks(page, counters);
  await page.setViewportSize({ width: 1440, height: 900 });
  await openRuns(page);

  // 1-2: bounded desktop sidecar, 42/58 split, independent scroll, reachable Jarvis controls.
  await page.getByRole('button', {name:'Show context'}).click();
  const sidecar = page.locator('#shell-sidecar');
  await expect(sidecar).toBeVisible();
  const workbench = sidecar.locator('.shell-sidecar__workbench');
  const jarvisPane = sidecar.locator('.shell-sidecar__pane--jarvis');
  const propertiesPane = sidecar.locator('.shell-sidecar__pane--properties');
  const boxes = await Promise.all([workbench.boundingBox(), jarvisPane.boundingBox(), propertiesPane.boundingBox()]);
  expect(boxes.every(Boolean)).toBeTruthy();
  const ratio = boxes[1].height / boxes[0].height;
  expect(ratio).toBeGreaterThan(0.35); expect(ratio).toBeLessThan(0.5);
  const paneStyles = await Promise.all([jarvisPane, propertiesPane].map(p => p.evaluate(el => ({ overflowY:getComputedStyle(el).overflowY, clientHeight:el.clientHeight, scrollHeight:el.scrollHeight }))));
  expect(paneStyles[0].overflowY).toMatch(/auto|scroll/); expect(paneStyles[1].overflowY).toMatch(/auto|scroll/);
  await expect(sidecar.getByText('Evidence thread')).toBeVisible();
  await expect(sidecar.locator('#jarvis-prompt')).toBeVisible();

  // 3: truthful no-selection properties + locally bounded technical disclosure.
  await expect(propertiesPane.getByText('No object selected.')).toBeVisible();
  expect((await viewportOverflow(page)).scrollWidth).toBeLessThanOrEqual((await viewportOverflow(page)).clientWidth + 1);

  // 4-6: compact tabset keyboard behavior; held submit survives tab switch and close/reopen without duplicate dispatch.
  await page.setViewportSize({ width: 720, height: 620 });
  const tabs = sidecar.getByRole('tablist', {name:'Sidecar views'});
  await expect(tabs).toBeVisible();
  const jarvisTab = sidecar.getByRole('tab', {name:'Jarvis'});
  await jarvisTab.focus(); await page.keyboard.press('ArrowRight');
  await expect(sidecar.getByRole('tab', {name:'Properties'})).toBeFocused();
  await sidecar.getByRole('tab', {name:'Jarvis'}).click();
  await sidecar.locator('#jarvis-prompt').fill('held submit evidence');
  await sidecar.locator('#jarvis-prompt').press('Enter');
  await sidecar.getByRole('tab', {name:'Properties'}).click();
  await page.getByRole('button', {name:'Hide context'}).click();
  await page.getByRole('button', {name:'Show context'}).click();
  await page.waitForTimeout(1000);
  expect(counters.interactions).toBe(1);
  await expect(page.locator('#shell-sidecar')).toContainText('Durable evidence response');

  // 7,9,10: hostile Runs payloads/logs stay bounded, inert and no global horizontal overflow.
  await page.setViewportSize({ width: 1440, height: 900 });
  const rawSummaries = page.getByText(/View raw/);
  expect(await rawSummaries.count()).toBeGreaterThan(0);
  const beforeExpand = await viewportOverflow(page);
  await rawSummaries.first().click();
  await page.getByText('View raw log').click();
  const afterExpand = await viewportOverflow(page);
  expect(afterExpand.scrollHeight - beforeExpand.scrollHeight).toBeLessThan(900);
  expect(afterExpand.scrollWidth).toBeLessThanOrEqual(afterExpand.clientWidth + 1);
  expect(await page.evaluate(() => window.__pwned ?? 0)).toBe(0);
  await page.getByRole('button', {name:'Show analysis'}).click();
  await expect(page.locator('#shell-analysis-dock')).toBeVisible();

  // 8: Review is decision-first; machine ids secondary; unsupported impact/current claims omitted.
  await page.getByText('Review', {exact:true}).first().click();
  await expect(page.getByRole('heading', {name:'Review', level:1})).toBeVisible();
  await expect(page.getByRole('button', {name:'Accept'})).toBeVisible();
  await expect(page.getByRole('button', {name:'Reject'})).toBeVisible();
  const technical = page.getByText('Technical details').last();
  await expect(technical).toBeVisible();
  await expect(page.getByText(/Impact/i)).toHaveCount(0);
  expect(await page.evaluate(() => window.__pwned ?? 0)).toBe(0);

  // 11: keyboard and Escape/focus return.
  await page.getByRole('button', {name:'Show context'}).click();
  await page.locator('#shell-sidecar').press('Escape');
  await expect(page.getByRole('button', {name:'Show context'})).toBeFocused();

  // 12: appearance modes and reduced motion remain usable.
  await page.emulateMedia({ reducedMotion:'reduce' });
  const appearance = page.getByLabel('Appearance preference');
  for (const mode of ['light','dark','system']) { await appearance.selectOption(mode); await expect(page.locator('body')).toBeVisible(); }

  // 13: presentation interactions emitted no provider/task/product mutation calls except the one explicit thread interaction.
  const unexpected = counters.all.filter(x => /\/ai\/tasks|provider|\/promote|\/reject/.test(x));
  expect(unexpected).toEqual([]);

  await page.screenshot({ path:'evidence/096/096-final.png', fullPage:true });
});
