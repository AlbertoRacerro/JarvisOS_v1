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
const testEnv={...process.env,JARVISOS_DATA_ROOT:data,JARVISOS_CORS_ORIGINS:"http://127.0.0.1:5193"};
const init=spawnSync(python,['-c','from app.core.database import initialize_database; initialize_database()'],{cwd:root+'/backend',env:testEnv,encoding:'utf8'});
assert.equal(init.status,0,init.stderr);
const evidence=process.env.JARVIS_BROWSER_EVIDENCE || path.join(data,'evidence');
await mkdir(evidence,{recursive:true});
function startBackend() { return spawn(python,['-m','uvicorn','app.main:app','--port','8023'],{cwd:root+'/backend',env:testEnv,stdio:['ignore','ignore','pipe']}); }
let backend=startBackend();
const frontend=spawn('node',['node_modules/vite/bin/vite.js','--host','127.0.0.1','--port','5193'],{cwd:root+'/frontend',env:{...process.env,VITE_API_BASE_URL:'http://127.0.0.1:8023'},stdio:['ignore','ignore','pipe']});
let browser;
try {
  for (const url of ['http://127.0.0.1:8023/health','http://127.0.0.1:5193']) {
    let ready=false;for(let i=0;i<60;i++){try{if((await fetch(url)).ok){ready=true;break}}catch{}await new Promise(r=>setTimeout(r,250));}if(!ready)throw Error('Server not ready: '+url);
  }
  let workspaces=await(await fetch('http://127.0.0.1:8023/workspaces')).json();
  if(!workspaces.length){const r=await fetch('http://127.0.0.1:8023/workspaces',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:'Operator acceptance',slug:'operator-144'})});assert.equal(r.status,201,await r.text());}
  browser=await chromium.launch({executablePath:process.env.JARVIS_CHROMIUM_EXECUTABLE || undefined,args:['--no-sandbox','--disable-dev-shm-usage','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--no-zygote','--single-process']});
  const page=await browser.newPage({viewport:{width:1600,height:1000}});
  const pageErrors=[];
  page.on('pageerror',e=>pageErrors.push(e.message));

  await page.goto('http://127.0.0.1:5193/design/bluecad');
  await page.getByLabel('New candidate brief',{exact:true}).fill('Browser parked candidate safety check');
  await page.getByRole('button',{name:'New candidate',exact:true}).click();
  await page.getByRole('status').filter({hasText:'Candidate saved · parked — budget_blocked.'}).waitFor();
  await page.getByRole('button',{name:'Inspect candidate',exact:true}).click();
  await page.getByRole('heading',{name:'Candidate inspector',exact:true}).waitFor();
  assert.equal(await page.locator('.bluecad-workbench__chrome details').getAttribute('open'),null);
  await page.locator('.bluecad-workbench__chrome summary').filter({hasText:'Candidate details'}).click();
  await page.locator('.bluecad-workbench__chrome').getByText('Candidate ID',{exact:true}).waitFor();
  await page.locator('.bluecad-workbench__chrome summary').filter({hasText:'Candidate details'}).click();
  await page.reload();
  await page.getByRole('button',{name:/parkedBrowser parked candidate safety check/}).count();
  await page.getByRole('button',{name:'Archive',exact:true}).waitFor();
  await page.getByRole('button',{name:'Archive',exact:true}).click();
  await page.getByRole('status').filter({hasText:'Candidate archived.'}).waitFor();
  await page.waitForTimeout(400);
  await page.getByLabel('Show archived',{exact:true}).focus();
  await page.getByLabel('Show archived',{exact:true}).press('Space');
  await page.waitForFunction(()=>document.querySelector('.bluecad-workbench__navigator input[type=checkbox]')?.checked);
  await page.locator('.bluecad-candidate').filter({hasText:'Browser parked candidate safety check'}).click();
  await page.getByRole('button',{name:'Inspect candidate',exact:true}).waitFor();
  for(const width of [1600,1280]) {
    await page.setViewportSize({width,height:800});
    await page.screenshot({path:evidence+'/bluecad-'+width+'.png'});
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>window.innerWidth),false);
  }
  const exited=new Promise(resolve=>backend.once('exit',resolve));backend.kill();await exited;backend=startBackend();
  for(let i=0;i<60;i++){try{if((await fetch('http://127.0.0.1:8023/health')).ok)break;}catch{}await new Promise(r=>setTimeout(r,250));}
  await page.reload();
  await page.waitForTimeout(400);
  await page.getByLabel('Show archived',{exact:true}).focus();
  await page.getByLabel('Show archived',{exact:true}).press('Space');
  await page.waitForFunction(()=>document.querySelector('.bluecad-workbench__navigator input[type=checkbox]')?.checked);
  await page.locator('.bluecad-candidate').filter({hasText:'Browser parked candidate safety check'}).waitFor();
  assert.ok((await page.locator('.bluecad-candidate').filter({hasText:'Browser parked candidate safety check'}).innerText()).toLowerCase().includes('archived'));
  console.log('PASS real backend parked candidate create/read/archive/reload/restart');
  await page.goto('http://127.0.0.1:5193/settings/ai');
  await page.getByText('Enabled in configuration · runtime availability not verified',{exact:false}).first().waitFor();
  await page.screenshot({path:evidence+'/settings.png'});
  // Error recovery test uses an explicit failed read, never a replacement success fixture.
  await page.route('**/ai/settings',route=>route.abort());
  await page.reload();
  await page.getByRole('button',{name:'Reload settings',exact:true}).waitFor();
  assert.ok((await page.locator('.settings-facts').first().innerText()).includes('Unavailable'));
  await page.unroute('**/ai/settings');
  await page.getByRole('button',{name:'Reload settings',exact:true}).click();
  await page.getByText('Canonical state reloaded.',{exact:false}).waitFor();
  assert.deepEqual(pageErrors,[]);
  console.log('PASS settings runtime wording; explicit browser request-abort fault injection shows unavailable usage and Reload recovery (not an observed server outage)');
  console.log('Evidence:',evidence);
}finally{await browser?.close();frontend.kill();backend.kill();}
