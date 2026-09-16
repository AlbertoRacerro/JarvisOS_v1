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

  await page.goto('http://127.0.0.1:5173/development/roadmap/timeline');
  await page.getByRole('button',{name:'+ Add work item',exact:true}).click();
  await page.getByLabel('New work item',{exact:true}).fill('Design pump circuit');
  await page.getByRole('button',{name:'+ Add work item',exact:true}).click();
  await page.getByLabel('Window start',{exact:true}).fill('2026-09-15');
  await page.getByLabel('Window end',{exact:true}).fill('2026-10-02');
  await page.getByLabel('Done when',{exact:true}).fill('Pressure drop calculation reviewed');
  await page.getByRole('button',{name:'Save work item',exact:true}).click();
  await page.getByTestId('roadmap-timeline-window').waitFor();
  await page.getByRole('button',{name:'Mark Done',exact:true}).click();
  await page.getByRole('alert').waitFor();
  console.log('PASS unsatisfied done_when refusal:',await page.getByRole('alert').innerText());
  await page.getByRole('link',{name:'Schedule in Calendar',exact:true}).click();
  await page.getByRole('button',{name:'+ Add event',exact:true}).click();
  await page.getByLabel('Title',{exact:true}).fill('Calculate pressure drop');
  await page.getByLabel('Start',{exact:true}).fill('2026-09-16T09:00');
  await page.getByLabel('End',{exact:true}).fill('2026-09-16T11:30');
  await page.getByLabel('Time zone',{exact:true}).fill('Europe/Rome');
  await page.getByRole('button',{name:'+ Add event',exact:true}).click();
  await page.getByRole('button',{name:'Edit event',exact:true}).waitFor();
  await page.getByRole('button',{name:'Edit event',exact:true}).click();
  await page.getByLabel('Edit event title',{exact:true}).fill('Review pressure drop and pipe sizing');
  await page.getByRole('button',{name:'Save event',exact:true}).click();
  await page.getByRole('button',{name:'Edit event',exact:true}).waitFor();
  for(const view of ['Week','Month','Day','Agenda']) {
    await page.getByRole('button',{name:view,exact:true}).click();
    if(view==='Day') await page.getByLabel('View date',{exact:true}).fill('2026-09-16');
    await page.getByRole('button',{name:/Review pressure drop and pipe sizing/}).first().waitFor();
    await page.screenshot({path:evidence+'/calendar-'+view.toLowerCase()+'.png'});
  }
  await page.getByRole('button',{name:'Week',exact:true}).click();
  for(const route of ['development/roadmap/timeline','development/roadmap/calendar']) {
    await page.goto('http://127.0.0.1:5173/'+route);
    await page.waitForTimeout(500);
    await page.screenshot({path:evidence+'/'+route.replaceAll('/','-')+'.png'});
    await page.setViewportSize({width:1280,height:800});
    await page.screenshot({path:evidence+'/'+route.replaceAll('/','-')+'-compact.png'});
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>window.innerWidth),false);
    await page.setViewportSize({width:1600,height:1000});
  }
  const exited=new Promise(resolve=>backend.once('exit',resolve));backend.kill();await exited;backend=startBackend();
  for(let i=0;i<60;i++){try{if((await fetch('http://127.0.0.1:8000/health')).ok)break;}catch{}await new Promise(r=>setTimeout(r,250));}
  await page.goto('http://127.0.0.1:5173/development/roadmap/timeline');
  await page.getByTestId('roadmap-timeline-window').filter({hasText:'Design pump circuit'}).waitFor();
  await page.goto('http://127.0.0.1:5173/development/roadmap/calendar');
  await page.getByRole('button',{name:/Review pressure drop and pipe sizing/}).waitFor();
  assert.deepEqual(pageErrors,[]);
  console.log('PASS create/edit roadmap window, done_when refusal, linked event create/edit, day/week/month/agenda, compact widths, backend restart persistence. Evidence:',evidence);
}finally{await browser?.close();frontend.kill();backend.kill();}

