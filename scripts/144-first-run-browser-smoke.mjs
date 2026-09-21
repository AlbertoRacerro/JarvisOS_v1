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
let browser; let page;
try {
  for (const url of ['http://127.0.0.1:8000/health','http://127.0.0.1:5173']) {
    let ready=false;for(let i=0;i<60;i++){try{if((await fetch(url)).ok){ready=true;break}}catch{}await new Promise(r=>setTimeout(r,250));}if(!ready)throw Error('Server not ready: '+url);
  }
  browser=await chromium.launch({executablePath:process.env.JARVIS_CHROMIUM_EXECUTABLE || undefined,args:['--no-sandbox','--disable-dev-shm-usage','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--no-zygote','--single-process']});
  page=await browser.newPage({viewport:{width:1280,height:800}});
  const errors=[]; page.on('pageerror',e=>errors.push(e.message));
  const api='http://127.0.0.1:8000';
  assert.deepEqual(await (await fetch(api+'/workspaces')).json(),[]);
  // Explicit transport fault injection; never confuse a failed list with empty data.
  const failList=route=>route.abort('failed');
  await page.route('**/workspaces',failList);
  await page.goto('http://127.0.0.1:5173/development/brainstorm');
  await page.getByText('Workspace service unavailable',{exact:true}).waitFor();
  assert.equal(await page.getByRole('button',{name:'Create workspace',exact:true}).count(),0);
  await page.unroute('**/workspaces',failList);
  await page.getByRole('button',{name:'Retry',exact:true}).click();
  await page.getByRole('heading',{name:'Create your first workspace',exact:true}).waitFor();
  await page.screenshot({path:evidence+'/first-workspace.png'});
  await page.getByLabel('Workspace name',{exact:true}).fill('BlueRev first project');
  await page.getByRole('button',{name:'Create workspace',exact:true}).click();
  await page.getByLabel('RAW idea',{exact:true}).waitFor();
  const first=(await (await fetch(api+'/workspaces')).json())[0];
  assert.equal(first.name,'BlueRev first project');
  assert.equal(new URL(page.url()).pathname,'/development/brainstorm');
  await page.getByLabel('RAW idea',{exact:true}).fill('First workspace note retained after setup.');
  await page.getByRole('button',{name:'Save raw note',exact:true}).click();
  await page.getByRole('status').filter({hasText:'Saved successfully.'}).waitFor();
  // Seed a second real workspace only to exercise existing selection; first creation is UI-only.
  const created=await fetch(api+'/workspaces',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:'Second project',slug:'second-project'})});
  assert.equal(created.status,201); const second=await created.json();
  await page.reload();
  await page.getByRole('combobox',{name:/^Workspace/}).selectOption(second.id);
  await page.getByLabel('RAW idea',{exact:true}).fill('This belongs only to the second project.');
  await page.getByRole('button',{name:'Save raw note',exact:true}).click();
  await page.getByRole('status').filter({hasText:'Saved successfully.'}).waitFor();
  await page.reload();
  await page.getByTestId('brainstorm-raw').filter({hasText:'This belongs only to the second project.'}).waitFor();
  assert.equal(await page.getByRole('combobox',{name:/^Workspace/}).inputValue(),second.id);
  assert.equal(await page.getByTestId('brainstorm-raw').filter({hasText:'First workspace note'}).count(),0);
  await page.goto('http://127.0.0.1:5173/memory/project-basis');
  await page.reload();
  await page.getByLabel('Project workspace',{exact:true}).getByRole('option',{name:'Second project',exact:true}).waitFor({state:'attached'});
  assert.equal(await page.getByLabel('Project workspace',{exact:true}).inputValue(),second.id);
  const exited=new Promise(resolve=>backend.once('exit',resolve));backend.kill();await exited;backend=startBackend();
  for(let i=0;i<60;i++){try{if((await fetch(api+'/health')).ok)break;}catch{}await new Promise(r=>setTimeout(r,250));}
  await page.goto('http://127.0.0.1:5173/development/brainstorm');
  await page.getByTestId('brainstorm-raw').filter({hasText:'This belongs only to the second project.'}).waitFor();
  // Invalid cached identity must be validated before any workspace-scoped request.
  await page.evaluate(()=>localStorage.setItem('jarvisos.active-workspace','missing-workspace'));
  const invalidRequests=[];page.on('request',r=>{if(r.url().includes('missing-workspace'))invalidRequests.push(r.url());});
  await page.reload();
  await page.getByLabel('RAW idea',{exact:true}).waitFor();
  assert.notEqual(await page.getByRole('combobox',{name:/^Workspace/}).inputValue(),'missing-workspace');
  assert.deepEqual(invalidRequests,[]);
  await page.route('**/workspaces',failList);
  await page.goto('http://127.0.0.1:5173/settings/appearance');
  await page.getByText('Workspace service unavailable',{exact:true}).waitFor({state:'hidden'});
  assert.equal(new URL(page.url()).pathname,'/settings/appearance');
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
  assert.deepEqual(errors,[]);
  console.log('PASS first workspace UI creation, failed-list retry, originating route, selected workspace reload/restart persistence, stale cache refusal, Settings access');
  console.log('Evidence:',evidence);
}catch(error){if(page){await page.screenshot({path:evidence+'/failure.png'});console.log(await page.locator('body').innerText());}throw error;}finally{await browser?.close();frontend.kill();backend.kill();}
