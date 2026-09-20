import { spawn, spawnSync } from 'node:child_process';
import { mkdir, writeFile, mkdtemp } from 'node:fs/promises';
import path from 'node:path';
import { tmpdir } from 'node:os';
import { fileURLToPath } from 'node:url';
import assert from 'node:assert/strict';
const { chromium } = await import(process.env.JARVIS_PLAYWRIGHT_MODULE || 'playwright');
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const python=process.env.JARVIS_TEST_PYTHON || 'python';
const data=await mkdtemp(path.join(tmpdir(), 'jarvis-144-'));
const testEnv={...process.env,JARVISOS_DATA_ROOT:data};
const init=spawnSync(python,['-c','from app.core.database import initialize_database; initialize_database()'],{cwd:root+'/backend',env:testEnv,encoding:'utf8'});
assert.equal(init.status,0,init.stderr);
const evidence=process.env.JARVIS_BROWSER_EVIDENCE || path.join(data,'evidence');
await mkdir(evidence,{recursive:true});
function startBackend() { return spawn(python,['-m','uvicorn','app.main:app','--port','8000'],{cwd:root+'/backend',env:testEnv,stdio:['ignore','ignore','pipe']}); }
let backend=startBackend();
const frontend=spawn('node',['node_modules/vite/bin/vite.js','--host','127.0.0.1'],{cwd:root+'/frontend',stdio:['ignore','ignore','pipe']});
let browser;
try {
  for (const url of ['http://127.0.0.1:8000/health','http://127.0.0.1:5173']) {
    let ready=false;for(let i=0;i<60;i++){try{if((await fetch(url)).ok){ready=true;break}}catch{}await new Promise(r=>setTimeout(r,250));}if(!ready)throw Error('Server not ready: '+url);
  }
  let workspaces=await(await fetch('http://127.0.0.1:8000/workspaces')).json();
  if(!workspaces.length){const r=await fetch('http://127.0.0.1:8000/workspaces',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:'Operator acceptance',slug:'operator-144'})});assert.equal(r.status,201,await r.text());}
  browser=await chromium.launch({executablePath:process.env.JARVIS_CHROMIUM_EXECUTABLE || undefined,args:['--no-sandbox','--disable-dev-shm-usage','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--no-zygote','--single-process']});
  const page=await browser.newPage({viewport:{width:1600,height:1000}});
  const pageErrors=[];
  page.on('pageerror',e=>pageErrors.push(e.message));
  await page.goto('http://127.0.0.1:5173/development/brainstorm');
  await page.getByLabel('RAW idea',{exact:true}).fill('Perdite di carico nel circuito: verificare diametro e consumo della pompa.\nIdea libera, ancora da discutere.');
  await page.getByRole('button',{name:'Save raw note',exact:true}).click();
  await page.getByRole('status').filter({hasText:'Saved successfully.'}).waitFor();
  await page.reload();
  await page.getByTestId('brainstorm-raw').filter({hasText:'Perdite di carico nel circuito'}).first().waitFor();
  console.log('PASS raw capture persists across reload');
  await page.getByRole('button',{name:'Organize this note',exact:true}).click();
  await page.getByRole('button',{name:'Record discussion',exact:true}).click();
  await page.getByText('RAW discussion provenance',{exact:true}).waitFor();
  await page.getByLabel('Title',{exact:true}).fill('Check pump pressure drop');
  await page.getByLabel('Takeaway',{exact:true}).fill('Measure the circuit before sizing the pump.');
  await page.getByLabel('Synthesis',{exact:true}).fill('Compare the measured pressure drop against the proposed one-bar limit.');
  await page.getByRole('button',{name:'Create reconciled idea',exact:true}).click();
  await page.getByTestId('brainstorm-idea').filter({hasText:'Check pump pressure drop'}).waitFor();
  await page.getByRole('button',{name:'Inspect synthesis and provenance',exact:true}).click();
  await page.getByTestId('brainstorm-detail').getByText('Compare the measured pressure drop against the proposed one-bar limit.',{exact:true}).waitFor();
  await page.getByLabel('Search reconciled ideas',{exact:true}).fill('no matching idea');
  await page.getByRole('status').filter({hasText:'No reconciled ideas match'}).waitFor();
  await page.getByLabel('Search reconciled ideas',{exact:true}).fill('pump');
  await page.getByTestId('brainstorm-idea').filter({hasText:'Check pump pressure drop'}).locator('summary').filter({hasText:'Idea actions'}).click();
  await page.getByRole('button',{name:'Add to Roadmap proposal',exact:true}).click();
  await page.getByTestId('brainstorm-promotion').filter({hasText:'roadmap'}).waitFor();
  await page.reload();
  await page.getByTestId('brainstorm-idea').filter({hasText:'Check pump pressure drop'}).waitFor();
  await page.getByTestId('brainstorm-promotion').filter({hasText:'roadmap'}).waitFor();
  console.log('PASS real manual discussion, synthesis disclosure and proposal-only promotion survive reload');
  await page.goto('http://127.0.0.1:5173/memory/project-basis');
  await page.locator('.jarvis-conversation-settings summary').click();
  await page.getByLabel('Jarvis responder').selectOption('local:fake');
  await page.locator('.jarvis-conversation-settings summary').click();
  await page.getByLabel('Message',{exact:true}).fill('Quali dati servono per iniziare?');
  await page.getByRole('button',{name:'Send without project context',exact:true}).click();
  await page.getByLabel('Jarvis thread transcript').getByText('Quali dati servono per iniziare?',{exact:false}).first().waitFor();
  console.log('PASS first conversation creates and stores a real interaction (synthetic responder, not AI evidence)');
  // Delay the real initial list response: do not synthesize any app response.
  let releaseThreadList;
  const threadListGate = new Promise(resolve => { releaseThreadList = resolve; });
  let threadWrites = 0;
  const countThreadWrites = request => {
    if (request.method() === 'POST' && new URL(request.url()).pathname.startsWith('/ai/threads')) threadWrites++;
  };
  page.on('request', countThreadWrites);
  const delayThreadList = async route => { await threadListGate; await route.continue(); };
  await page.route('**/ai/threads?*', delayThreadList);
  await page.reload();
  await page.getByLabel('Message',{exact:true}).fill('Preserve this draft while conversations load.');
  assert.equal(await page.getByRole('button',{name:'Loading conversations…',exact:true}).isDisabled(),true);
  await page.getByLabel('Message',{exact:true}).press('Enter');
  assert.equal(threadWrites,0,'No thread creation or dispatch before conversation ownership is known');
  releaseThreadList();
  await page.getByRole('button',{name:'Send without project context',exact:true}).waitFor();
  await page.getByLabel('Jarvis thread transcript').getByText('Quali dati servono per iniziare?',{exact:false}).first().waitFor();
  assert.equal(await page.getByLabel('Message',{exact:true}).inputValue(),'Preserve this draft while conversations load.');
  await page.getByLabel('Message',{exact:true}).fill('');
  await page.unroute('**/ai/threads?*', delayThreadList);
  page.off('request', countThreadWrites);
  console.log('PASS delayed real conversation list blocks Enter/send and preserves draft and thread ownership');
  await page.getByLabel('Requirement statement').fill('Le perdite di carico devono essere inferiori a 1 bar.');
  await page.getByRole('button',{name:'Preview impact',exact:true}).click();
  await page.getByRole('button',{name:'Approve all',exact:true}).waitFor();
  await page.getByRole('button',{name:'Approve all',exact:true}).click();
  await page.getByRole('button',{name:'Final reconcile',exact:true}).waitFor();
  await page.getByRole('button',{name:'Final reconcile',exact:true}).click();
  await page.getByRole('button',{name:/Le perdite di carico devono/}).waitFor();
  await page.getByLabel('Search project records',{exact:true}).fill('perdite carico');
  await page.getByRole('button',{name:'Search',exact:true}).click();
  await page.getByRole('button',{name:'Open in Project Basis',exact:true}).first().waitFor();
  await page.getByRole('button',{name:/Le perdite di carico devono/}).first().click();
  await page.locator('.basis-record-detail').first().waitFor();
  await page.getByRole('button',{name:'Add selected to Jarvis context',exact:true}).click();
  await page.getByTestId('knowledge-context-preview').waitFor();
  await page.getByLabel('Message',{exact:true}).fill('Riassumi il requisito selezionato.');
  assert.equal(await page.getByRole('button',{name:'Send with selected context',exact:true}).isDisabled(),true);
  await page.getByText('Project Basis discussion is unavailable under the current sensitivity controls.',{exact:false}).waitFor();
  await page.getByRole('button',{name:'Clear context',exact:true}).click();
  await page.getByTestId('knowledge-context-basket').waitFor({state:'detached'});
  console.log('PASS requirement reconciliation, human search, disclosure, exact-context sensitivity refusal and removal');
  await page.locator('.jarvis-conversation-settings summary').click();
  await page.getByLabel('Jarvis responder').selectOption('local:general');
  await page.locator('.jarvis-conversation-settings summary').click();
  await page.getByLabel('Message',{exact:true}).fill('Explain pressure drop in one sentence.');
  const localResponse=page.waitForResponse(response=>response.url().includes('/interactions?')&&response.request().method()==='POST',{timeout:90000});
  await page.getByRole('button',{name:'Send without project context',exact:true}).click();
  const local=await localResponse;
  assert.equal(local.status(),200,await local.text());
  const localResult=(await local.json()).interaction;
  assert.notEqual(localResult.execution_class,'synthetic');
  console.log('Local model actual outcome:',localResult.flow_state,localResult.terminal_reason);

  for(const route of ['memory/project-basis','development/brainstorm','coding/repository','development/roadmap/timeline','development/roadmap/calendar','memory/models','memory/literature','design/process','design/bluecad','settings/appearance','settings/ai','settings/system']) {
    await page.goto('http://127.0.0.1:5173/'+route);await page.waitForTimeout(1200);
    await page.screenshot({path:evidence+'/'+route.replaceAll('/','-')+'.png'});
    await writeFile(evidence+'/'+route.replaceAll('/','-')+'.txt',await page.locator('body').innerText());
    await page.setViewportSize({width:1280,height:800});
    await page.screenshot({path:evidence+'/'+route.replaceAll('/','-')+'-compact.png'});
    const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>window.innerWidth);
    console.log(route, 'horizontal document overflow:',overflow);
    await page.setViewportSize({width:1600,height:1000});
  }
  const references={
    'memory-reference':'memory-beta/memory-project-basis-beta-approved-2026-08-26.html',
    'brainstorm-reference':'development-beta/development-brainstorm-beta-approved-2026-08-27.html',
    'coding-reference':'coding-beta/coding-repository-beta-approved-2026-08-27.html',
    'timeline-reference':'development-beta/development-roadmap-timeline-beta-approved-2026-08-27.html',
    'calendar-reference':'development-beta/development-calendar-beta-approved-2026-08-27.html'
  };
  for(const [name,reference] of Object.entries(references)) {
    await page.goto('file://'+root+'/docs/design-references/'+reference);
    await page.screenshot({path:evidence+'/'+name+'.png'});
  }
  const exited=new Promise(resolve=>backend.once('exit',resolve)); backend.kill(); await exited;
  backend=startBackend();
  for(let i=0;i<60;i++){try{if((await fetch('http://127.0.0.1:8000/health')).ok)break;}catch{}await new Promise(r=>setTimeout(r,250));}
  await page.goto('http://127.0.0.1:5173/development/brainstorm');
  await page.getByTestId('brainstorm-raw').filter({hasText:'Perdite di carico nel circuito'}).waitFor();
  await page.getByTestId('brainstorm-idea').filter({hasText:'Check pump pressure drop'}).waitFor();
  await page.getByTestId('brainstorm-promotion').filter({hasText:'roadmap'}).waitFor();
  await page.goto('http://127.0.0.1:5173/memory/project-basis');
  await page.getByRole('button',{name:/Le perdite di carico devono/}).waitFor();
  await page.getByLabel('Jarvis thread transcript').getByText('Quali dati servono per iniziare?',{exact:false}).first().waitFor();
  assert.deepEqual(pageErrors,[]);
  console.log('PASS backend restart retains RAW, reconciled requirement and conversation');
  console.log('Evidence:',evidence);
}finally{await browser?.close();frontend.kill();backend.kill();}
