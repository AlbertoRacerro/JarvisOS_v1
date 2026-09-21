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
const testEnv={...process.env,JARVISOS_DATA_ROOT:data,JARVISOS_CORS_ORIGINS:'http://127.0.0.1:5191'};
const init=spawnSync(python,['-c','from app.core.database import initialize_database; initialize_database()'],{cwd:root+'/backend',env:testEnv,encoding:'utf8'});
assert.equal(init.status,0,init.stderr);
const evidence=process.env.JARVIS_BROWSER_EVIDENCE || path.join(data,'evidence');
await mkdir(evidence,{recursive:true});
function startBackend() { return spawn(python,['-m','uvicorn','app.main:app','--port','8021'],{cwd:root+'/backend',env:testEnv,stdio:['ignore','ignore','pipe']}); }
let backend=startBackend();
const frontend=spawn('node',['node_modules/vite/bin/vite.js','--host','127.0.0.1','--port','5191'],{cwd:root+'/frontend',env:{...process.env,VITE_API_BASE_URL:'http://127.0.0.1:8021'},stdio:['ignore','ignore','pipe']});
let browser;
try {
  for (const url of ['http://127.0.0.1:8021/health','http://127.0.0.1:5191']) {
    let ready=false;for(let i=0;i<60;i++){try{if((await fetch(url)).ok){ready=true;break}}catch{}await new Promise(r=>setTimeout(r,250));}if(!ready)throw Error('Server not ready: '+url);
  }
  let workspaces=await(await fetch('http://127.0.0.1:8021/workspaces')).json();
  if(!workspaces.length){const r=await fetch('http://127.0.0.1:8021/workspaces',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:'Operator acceptance',slug:'operator-144'})});assert.equal(r.status,201,await r.text());}
  browser=await chromium.launch({executablePath:process.env.JARVIS_CHROMIUM_EXECUTABLE || undefined,args:['--no-sandbox','--disable-dev-shm-usage','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--no-zygote','--single-process']});
  const page=await browser.newPage({viewport:{width:1600,height:1000}});
  const pageErrors=[];
  page.on('pageerror',e=>{pageErrors.push(e.message);console.error('PAGE ERROR',e.message)});
  page.on('console',m=>{if(m.type()==='error') console.error('CONSOLE',m.text())});
  await page.goto('http://127.0.0.1:5191/memory/literature');
  await page.getByRole('button',{name:'+ Register source',exact:true}).click();
  await page.getByLabel('Source title',{exact:true}).fill('Pressure drop handbook');
  await page.getByLabel('Citation, DOI or URL (optional)',{exact:true}).fill('Operator acceptance source, 2026');
  await page.getByRole('button',{name:'Save source',exact:true}).click();
  await page.getByText('Source saved as raw.',{exact:false}).waitFor();
  await page.getByLabel('Find in loaded sources',{exact:false}).fill('handbook pressure');
  await page.getByText('Pressure drop handbook',{exact:true}).first().waitFor();
  await page.getByLabel('Find in loaded sources',{exact:false}).fill('');
  await page.getByText('Add a finding',{exact:true}).click();
  await page.getByLabel('Claim statement',{exact:true}).fill('The friction factor depends on Reynolds number.');
  await page.getByRole('button',{name:'Save raw finding',exact:true}).click();
  await page.getByText('Saved as raw. This finding has not been accepted as engineering evidence.',{exact:true}).waitFor();
  await page.getByText('The friction factor depends on Reynolds number.',{exact:true}).click();
  await page.getByRole('button',{name:'Select finding for Jarvis',exact:true}).click();
  await page.getByTestId('knowledge-actions').getByText('The friction factor depends on Reynolds number.',{exact:true}).waitFor();
  const previewResponse = page.waitForResponse(response => response.url().endsWith('/memory/jarvis/context-preview') && response.request().method()==='POST');
  await page.getByRole('button',{name:'Add selected to Jarvis context',exact:true}).click();
  const exactPreview = await (await previewResponse).json();
  await page.getByTestId('knowledge-context-preview').waitFor();
  assert.match(await page.getByTestId('knowledge-context-basket').innerText(),/The friction factor depends on Reynolds number/);
  await page.getByTestId('knowledge-context-preview').scrollIntoViewIfNeeded();
  await page.screenshot({path:evidence+'/literature-context-preview.png'});
  await writeFile(evidence+'/context-preview.txt',await page.getByTestId('knowledge-actions').innerText());
  await page.locator('.jarvis-conversation-settings summary').click();
  await page.getByLabel('Jarvis responder').selectOption('local:fake');
  await page.locator('.jarvis-conversation-settings summary').click();
  await page.getByLabel('Message',{exact:true}).fill('Explain the selected friction-factor claim.');
  const exactSubmitResponse = page.waitForResponse(response => response.url().includes('/interactions?') && response.request().method()==='POST');
  await page.getByRole('button',{name:'Send with selected context',exact:true}).click();
  const exactSubmit = await exactSubmitResponse;
  assert.equal(exactSubmit.status(),200,await exactSubmit.text());
  const sent = exactSubmit.request().postDataJSON();
  assert.equal(sent.expected_jarvis_context_digest,exactPreview.context_digest);
  assert.deepEqual(sent.jarvis_context.added_context_refs,exactPreview.exact_refs);
  assert.equal((await exactSubmit.json()).interaction.execution_class,'synthetic');
  await page.getByLabel('Jarvis thread transcript').getByText('Explain the selected friction-factor claim.',{exact:false}).first().waitFor();
  console.log('PASS exact Literature refs/digest accepted by real thread backend (synthetic responder, not inference proof)');
  await page.getByRole('button',{name:'Remove',exact:true}).click();
  await page.getByTestId('knowledge-context-basket').waitFor({state:'detached'});
  await page.getByRole('button',{name:'Send without project context',exact:true}).waitFor();
  await writeFile(evidence+'/after-remove.txt',await page.locator('body').innerText());
  await page.screenshot({path:evidence+'/after-remove.png'});
  if (!(await page.getByLabel('Finding type').isVisible())) {
    await page.getByText('Pressure drop handbook',{exact:true}).first().click();
    await page.getByText('Add a finding',{exact:true}).click();
  }
  await page.getByLabel('Finding type').selectOption('datum');
  await page.getByLabel('Reported value',{exact:true}).fill('1.25');
  await page.getByLabel('Unit (optional)',{exact:true}).fill('bar');
  await page.getByRole('button',{name:'Save raw finding',exact:true}).click();
  await page.getByText('1.25 bar',{exact:true}).waitFor();
  await page.locator('.literature-add-finding > summary').click();
  await page.locator('.literature-library').evaluate(el=>el.scrollTop=0);
  await page.screenshot({path:evidence+'/literature-source.png'});
  await page.reload();
  await page.getByText('Pressure drop handbook',{exact:true}).first().click();
  await page.getByText('The friction factor depends on Reynolds number.',{exact:true}).waitFor();
  const ws=(await(await fetch('http://127.0.0.1:8021/workspaces')).json())[0].id;
  const saved=await(await fetch(`http://127.0.0.1:8021/workspaces/${ws}/literature/sources`)).json();
  assert.equal(saved.items[0].entries.length,2);
  assert.ok(saved.items[0].entries.every(entry=>entry.status==='raw'));
  assert.equal(saved.items[0].entries.find(entry=>entry.entry_kind==='datum').value_text,'1.25');
  await page.goto('http://127.0.0.1:5191/memory/models');
  await page.getByRole('button',{name:'+ New model',exact:true}).click();
  await page.getByLabel('Model title',{exact:true}).fill('Pipe pressure drop');
  await page.getByLabel('Engineering question',{exact:true}).fill('How much pressure is lost?');
  await page.getByLabel('Scope (optional)',{exact:true}).fill('Single-phase incompressible flow');
  let rejectModelPost = true;
  let failModelRefresh = false;
  await page.route('**/workspaces/*/model-specs', async (route) => {
    if (route.request().method() === 'POST' && rejectModelPost) {
      rejectModelPost = false;
      await route.fulfill({status: 422, contentType: 'application/json', body: JSON.stringify({detail: 'Draft title rejected for browser failure proof'})});
      return;
    }
    await route.continue();
  });
  await page.getByRole('button',{name:'Save draft definition',exact:true}).click();
  await page.getByRole('alert').filter({hasText:'could not be saved'}).waitFor();
  assert.ok(await page.getByRole('button',{name:'Save draft definition',exact:true}).isVisible());
  failModelRefresh = true;
  await page.route('**/workspaces/*/model-dossiers', async (route) => {
    if (route.request().method() === 'GET' && failModelRefresh) {
      failModelRefresh = false;
      await route.fulfill({status: 503, contentType: 'application/json', body: JSON.stringify({detail: 'Refresh intentionally unavailable for browser failure proof'})});
      return;
    }
    await route.continue();
  });
  await page.getByRole('button',{name:'Save draft definition',exact:true}).click();
  await page.getByRole('status').filter({hasText:'Saved draft definition'}).waitFor();
  await page.getByRole('alert').filter({hasText:'could not be refreshed'}).waitFor();
  assert.equal(await page.getByRole('button',{name:'Save draft definition',exact:true}).count(), 0);
  await page.unroute('**/workspaces/*/model-specs');
  await page.unroute('**/workspaces/*/model-dossiers');
  await page.reload();
  await page.getByRole('button',{name:'Pipe pressure drop Definition · no version yet',exact:true}).click();
  await page.getByText('How much pressure is lost?',{exact:true}).waitFor();
  await page.getByLabel('Find a model or version',{exact:false}).fill('drop pipe');
  await page.getByRole('button',{name:'Pipe pressure drop Definition · no version yet',exact:true}).waitFor();
  await page.getByLabel('Find a model or version',{exact:false}).fill('');
  await page.screenshot({path:evidence+'/model-definition.png'});
  for(const route of ['memory/models','memory/literature']) {
    await page.goto('http://127.0.0.1:5191/'+route);
    if(route==='memory/models') await page.getByText('How much pressure is lost?',{exact:true}).waitFor();
    if(route==='memory/literature') await page.getByText('Pressure drop handbook',{exact:true}).first().click();
    await page.setViewportSize({width:1280,height:800});
    await page.screenshot({path:evidence+'/'+route.replaceAll('/','-')+'-compact.png'});
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>window.innerWidth),false);
    await writeFile(evidence+'/'+route.replaceAll('/','-')+'-metrics.json',JSON.stringify(await page.locator('.final-fusion__workbench').evaluate(el=>Array.from(el.querySelectorAll('h2,strong,p,input,button')).filter(n=>n.getBoundingClientRect().width&&n.getBoundingClientRect().height).map(n=>({tag:n.tagName,text:n.textContent?.slice(0,65),font:getComputedStyle(n).fontSize,width:n.getBoundingClientRect().width}))),null,2));
  }
  const exited=new Promise(resolve=>backend.once('exit',resolve)); backend.kill(); await exited;
  backend=startBackend();
  for(let i=0;i<60;i++){try{if((await fetch('http://127.0.0.1:8021/health')).ok)break;}catch{}await new Promise(r=>setTimeout(r,250));}
  await page.goto('http://127.0.0.1:5191/memory/literature');
  await page.getByText('Pressure drop handbook',{exact:true}).first().click();
  await page.getByText('The friction factor depends on Reynolds number.',{exact:true}).waitFor();
  assert.deepEqual(pageErrors,[]);
  await page.getByLabel('Jarvis thread transcript').getByText('Explain the selected friction-factor claim.',{exact:false}).first().waitFor();
  await page.goto('http://127.0.0.1:5191/memory/models');
  await page.getByRole('button',{name:'Pipe pressure drop Definition · no version yet',exact:true}).click();
  await page.getByText('How much pressure is lost?',{exact:true}).waitFor();
  const persistedModels = await (await fetch(`http://127.0.0.1:8021/workspaces/${ws}/model-specs`)).json();
  assert.equal(persistedModels.filter(model => model.title === 'Pipe pressure drop').length, 1);
  assert.deepEqual(pageErrors,[]);
  console.log('PASS real citation + claim/datum and model draft creation; explicit 422/503 fault recovery without duplicate model; token search, context preview/removal, reload and backend restart persistence; compact overflow checks');
  console.log('Evidence:',evidence);
}finally{await browser?.close();frontend.kill();backend.kill();}
