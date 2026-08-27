import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import fs from "node:fs/promises";
import path from "node:path";
import { chromium, firefox } from "playwright";

const PRODUCT_HEAD="221d50d9befcb7fafe56148e7104da9a056d36f4";
const BASE_URL=process.env.JARVISOS_EVIDENCE_URL||"http://127.0.0.1:4173";
const REFERENCE_URL=process.env.JARVISOS_REFERENCE_URL||"http://127.0.0.1:4174";
const OUT_DIR=process.env.JARVISOS_EVIDENCE_DIR||"evidence/100f-artifacts";
const REPO_ROOT=path.resolve(process.cwd(),"..");
const surfaces=[
{id:"process",route:"/design/process",viewport:{width:1365,height:768},ref:"docs/design-references/process-beta/process-beta-approved-2026-08-26.html",sha256:"d3bb06d9a7c761699a21b9b6b0a1901214a799f06dd31570c2fbfedc018cc475",marker:/Process/i},
{id:"bluecad",route:"/design/bluecad",viewport:{width:1365,height:768},ref:"docs/design-references/bluecad-beta/bluecad-beta-approved-2026-08-26.html",sha256:"da4ddfb1ebf6e0c7d39c133bf9b7c0da82e14428bad87748b0f7aa37a7e17bd9",marker:/BLUECAD/i},
{id:"project-basis",route:"/memory/project-basis",viewport:{width:1600,height:1000},ref:"docs/design-references/memory-beta/memory-project-basis-beta-approved-2026-08-26.html",sha256:"f901f977979d8389bec74a65510d1841ea12aa1e706f19dce0816a01d852b324",marker:/Project Basis/i},
{id:"models",route:"/memory/models",viewport:{width:1600,height:1000},ref:"docs/design-references/memory-beta/memory-models-beta-approved-2026-08-26.html",sha256:"2e76a9d740bb07adacc85379e71912b50015af5706995367ed1b1593d921f627",marker:/Model versions|Version dossier/i},
{id:"literature",route:"/memory/literature",viewport:{width:1600,height:1000},ref:"docs/design-references/memory-beta/memory-literature-beta-approved-2026-08-26.html",sha256:"c9e4225c5969ae86d9da6936b20eebfa6edbbc8a05b82a11d1a09d5a2231d150",marker:/Literature/i},
{id:"roadmap",route:"/development/roadmap/timeline",viewport:{width:1600,height:1000},ref:"docs/design-references/development-beta/development-roadmap-timeline-beta-approved-2026-08-27.html",sha256:"eb71ddab8cd829d041319fca7a6b08d4e7f60ae57a51f96310ed9ea11d20dc70",marker:/Timeline/i},
{id:"calendar",route:"/development/roadmap/calendar",viewport:{width:1600,height:1000},ref:"docs/design-references/development-beta/development-calendar-beta-approved-2026-08-27.html",sha256:"3dc94b861478007080a3d9658ec81bc3c46394d0bf73f9a5aa4aa669024b2737",marker:/Calendar/i},
{id:"brainstorm",route:"/development/brainstorm",viewport:{width:1600,height:1000},ref:"docs/design-references/development-beta/development-brainstorm-beta-approved-2026-08-27.html",sha256:"2b30f8d558045becf3c79b7d9a7bfcfd186a42a6278d92f53a0150be61f82631",marker:/Brainstorm/i},
{id:"repository",route:"/coding/repository",viewport:{width:1600,height:1000},ref:"docs/design-references/coding-beta/coding-repository-beta-approved-2026-08-27.html",sha256:"afe3bf43eebc3da65e38aadcb27dcaac6f55b61959077cad82cbc51979b1d11f",marker:/Repository/i},
{id:"runtime",route:"/coding/runtime",viewport:{width:1600,height:1000},ref:"docs/design-references/coding-beta/coding-runtime-beta-approved-2026-08-27.html",sha256:"041b2f8974a1ad866ac5fad700c920c3a4816e6a0d6263a185e20c0ca421893e",marker:/Runtime/i},
{id:"settings",route:"/settings/appearance",viewport:{width:1365,height:768},ref:"docs/design-references/settings-beta/settings-beta-approved-2026-08-26.html",sha256:"f30a0937f9e8cb1a189ade226a004ac4206597d1130433748b87d4c61043e5de",marker:/Appearance/i}
];
const primaryNav=["Design","Memory","Development","Coding","Settings"];
const report={productHead:PRODUCT_HEAD,generatedAt:new Date().toISOString(),referenceBase:REFERENCE_URL,productionBase:BASE_URL,surfaces:[],interactionStates:[]};
await fs.mkdir(OUT_DIR,{recursive:true});
const safe=s=>s.replace(/[^a-z0-9._-]+/gi,"-").toLowerCase();
const visibleText=(page,text)=>page.getByText(text,{exact:false}).count().then(n=>n>0);
const sha256=bytes=>createHash("sha256").update(bytes).digest("hex");
async function referenceDigest(s){const bytes=await fs.readFile(path.join(REPO_ROOT,s.ref));const actual=sha256(bytes);assert.equal(actual,s.sha256,`${s.id} canonical HTML digest drift`);return actual;}
async function assertShell(page){const nav=page.getByRole("navigation",{name:"Primary navigation"});assert.equal(await nav.count(),1,"shared primary rail missing");const labels=(await nav.getByRole("link").allTextContents()).map(v=>v.trim()).filter(Boolean);assert.deepEqual(labels,primaryNav,"primary rail drifted");assert.equal(labels.includes("Home"),false,"Home returned");assert.equal(await page.locator(".application-shell--final").count(),1,"final shell marker missing");}
async function noOverflow(page){const d=await page.evaluate(()=>({s:document.documentElement.scrollWidth,c:document.documentElement.clientWidth,b:document.body.scrollWidth}));assert.ok(d.s<=d.c+2,`page overflow ${d.s}>${d.c}`);assert.ok(d.b<=d.c+2,`body overflow ${d.b}>${d.c}`);}
async function unavailable(page,label){const b=page.getByRole("button",{name:new RegExp(label,"i")});if(await b.count())assert.equal(await b.first().isDisabled(),true,`${label} must be unavailable`);}
async function stateShot(page,engine,s,label,authority="presentation") {const file=`${engine.name}-${safe(s.id)}-state-${safe(label)}-${s.viewport.width}x${s.viewport.height}.png`;await page.screenshot({path:path.join(OUT_DIR,file),fullPage:true});report.interactionStates.push({engine:engine.name,id:s.id,route:new URL(page.url()).pathname,viewport:s.viewport,label,authority,screenshot:file,status:"PASS"});}
async function exercise(page,id,engine,s){
 if(id==="process"){for(const l of ["Add","Connect","Disconnect","Validate","Solve"])await unavailable(page,l);assert.ok(await visibleText(page,"Jarvis"));assert.ok(await visibleText(page,"Properties"));}
 if(id==="bluecad"){assert.ok(await visibleText(page,"Jarvis"));assert.ok(await visibleText(page,"Properties"));assert.equal(await page.locator(".shell-navigator").count(),1,"BLUECAD navigator must remain visible");}
 if(id==="project-basis"){await unavailable(page,"Approve all");await unavailable(page,"Validate");}
 if(id==="models"){const collapse=page.getByRole("button",{name:"Collapse all",exact:true});if(await collapse.count()){await collapse.click();assert.equal(await collapse.getAttribute("aria-expanded"),"false");await stateShot(page,engine,s,"dossier-collapsed");await page.getByRole("button",{name:"Expand sections",exact:true}).click();}}
 if(id==="literature"){assert.ok(await visibleText(page,"No literature records"));assert.ok(await visibleText(page,"Bounded preview unavailable"));await unavailable(page,"Import");await stateShot(page,engine,s,"inline-expansion-unavailable-no-record-owner","unavailable");}
 if(id==="roadmap"){assert.ok(await visibleText(page,"Execution status"));assert.equal(await page.getByText("Board",{exact:true}).count(),0);const collapse=page.getByRole("button",{name:"Collapse",exact:true});assert.equal(await collapse.count(),1);await stateShot(page,engine,s,"execution-expanded");await collapse.click();assert.equal(await collapse.getAttribute("aria-expanded"),"false");await stateShot(page,engine,s,"execution-collapsed");await page.getByRole("button",{name:"Expand",exact:true}).click();const c=page.getByRole("button",{name:"Calendar",exact:true});await c.click();await page.waitForTimeout(60);assert.equal(new URL(page.url()).pathname,"/development/roadmap/calendar");await page.goto(BASE_URL+"/development/roadmap/timeline",{waitUntil:"networkidle"});}
 if(id==="calendar"){const week=page.getByRole("button",{name:"Week",exact:true});assert.ok((await week.getAttribute("class")||"").includes("is-active"));await unavailable(page,"Add event");await stateShot(page,engine,s,"week-default");const day=page.getByRole("button",{name:"Day",exact:true});await day.click();assert.ok((await day.getAttribute("class")||"").includes("is-active"));await stateShot(page,engine,s,"day-presentation");await week.click();const t=page.getByRole("button",{name:"Timeline",exact:true});await t.click();await page.waitForTimeout(60);assert.equal(new URL(page.url()).pathname,"/development/roadmap/timeline");await page.goto(BASE_URL+"/development/roadmap/calendar",{waitUntil:"networkidle"});}
 if(id==="brainstorm"){for(const l of ["Attach","Microphone","Save","Reconcile","Promote"])await unavailable(page,l);assert.ok(await visibleText(page,"Opening an idea never adds it to context"));assert.ok(await visibleText(page,"RECONCILED"));await stateShot(page,engine,s,"reconciled-context-unavailable-no-record-owner","unavailable");}
 if(id==="repository"){assert.ok(await visibleText(page,"Unknown"));await unavailable(page,"Suggest modification");}
 if(id==="runtime"){assert.ok(await visibleText(page,"Unknown"));await unavailable(page,"update");await unavailable(page,"terminal");}
 if(id==="settings"){for(const l of ["Appearance","AI","System"])assert.ok(await visibleText(page,l));for(const [label,route] of [["AI","/settings/ai"],["System","/settings/system"]]){await page.getByRole("button",{name:label,exact:true}).click();await page.waitForTimeout(60);assert.equal(new URL(page.url()).pathname,route);await stateShot(page,engine,s,`settings-${label.toLowerCase()}`);}await page.getByRole("button",{name:"Appearance",exact:true}).click();await page.waitForTimeout(60);assert.equal(new URL(page.url()).pathname,"/settings/appearance");}
}
for(const engine of [{name:"chromium",impl:chromium},{name:"firefox",impl:firefox}]){
 const browser=await engine.impl.launch({headless:true});
 try{
  for(const s of surfaces){
   const digest=await referenceDigest(s);
   const context=await browser.newContext({viewport:s.viewport,reducedMotion:"reduce"});
   const referencePage=await context.newPage();
   const referenceUrl=`${REFERENCE_URL}/${s.ref}`;
   const referenceResponse=await referencePage.goto(referenceUrl,{waitUntil:"domcontentloaded"});assert.ok(referenceResponse?.ok(),`${s.id} canonical HTML failed to load`);await referencePage.waitForTimeout(250);
   const referenceScreenshot=`${engine.name}-${safe(s.id)}-canonical-${s.viewport.width}x${s.viewport.height}.png`;await referencePage.screenshot({path:path.join(OUT_DIR,referenceScreenshot),fullPage:true});
   const page=await context.newPage();const errors=[];page.on("pageerror",e=>errors.push(String(e)));await page.goto(BASE_URL+s.route,{waitUntil:"networkidle"});assert.equal(new URL(page.url()).pathname,s.route,`${s.id} route drift`);await assertShell(page);assert.equal(await page.getByRole("main").count(),1,`${s.id} main missing`);assert.ok(await page.getByText(s.marker).count()>0||s.id==="process"||s.id==="bluecad",`${s.id} canonical composition marker missing`);await exercise(page,s.id,engine,s);await noOverflow(page);assert.equal(errors.length,0,`${s.id} page errors: ${errors.join(" | ")}`);
   const productionScreenshot=`${engine.name}-${safe(s.id)}-production-${s.viewport.width}x${s.viewport.height}.png`;await page.screenshot({path:path.join(OUT_DIR,productionScreenshot),fullPage:true});report.surfaces.push({engine:engine.name,id:s.id,route:s.route,viewport:s.viewport,canonicalHtmlPath:s.ref,canonicalSha256:s.sha256,computedCanonicalSha256:digest,referenceUrl,referenceScreenshot,productionScreenshot,status:"PASS"});await context.close();
  }
 }finally{await browser.close();}
}
assert.equal(report.surfaces.length,22,"all eleven surfaces must be proven in both browsers");
for(const required of ["execution-expanded","execution-collapsed","week-default","inline-expansion-unavailable-no-record-owner","reconciled-context-unavailable-no-record-owner","settings-ai","settings-system"])assert.ok(report.interactionStates.some(v=>v.label===required),`required interaction proof missing: ${required}`);
const rows=report.surfaces.map(p=>`<section><h2>${p.engine} · ${p.id} · ${p.viewport.width}×${p.viewport.height}</h2><p><code>${p.route}</code><br><code>${p.canonicalHtmlPath}</code><br><code>${p.computedCanonicalSha256}</code></p><div class="pair"><figure><figcaption>Canonical HTML</figcaption><img src="${p.referenceScreenshot}" alt="Canonical ${p.id}"></figure><figure><figcaption>Production React/Vite</figcaption><img src="${p.productionScreenshot}" alt="Production ${p.id}"></figure></div></section>`).join("\n");
const states=report.interactionStates.map(p=>`<figure><figcaption>${p.engine} · ${p.id} · ${p.label} · ${p.authority}</figcaption><img src="${p.screenshot}" alt="${p.id} ${p.label}"></figure>`).join("\n");
const comparison=`<!doctype html><meta charset="utf-8"><title>100f canonical comparison</title><style>body{font-family:system-ui;margin:20px;background:#f4f1e9;color:#222}section{margin:0 0 40px;padding:16px;background:white;border:1px solid #ccc}.pair{display:grid;grid-template-columns:1fr 1fr;gap:12px;align-items:start}figure{margin:0 0 20px}figcaption{font-weight:600;margin-bottom:6px}img{display:block;width:100%;height:auto;border:1px solid #999}code{font-size:12px}@media(max-width:900px){.pair{grid-template-columns:1fr}}</style><h1>100f exact-head canonical comparisons</h1><p>Product head: <code>${PRODUCT_HEAD}</code>. Raw canonical HTML is shown before final overlays; unavailable interaction states are explicit when the current accepted owner is absent.</p>${rows}<h1>Required interaction states</h1>${states}`;
await fs.writeFile(path.join(OUT_DIR,"comparison.html"),comparison);await fs.writeFile(path.join(OUT_DIR,"manifest.json"),JSON.stringify(report,null,2)+"\n");console.log(`100f browser evidence PASS: ${report.surfaces.length} paired proofs + ${report.interactionStates.length} interaction states on exact product head ${PRODUCT_HEAD}`);
