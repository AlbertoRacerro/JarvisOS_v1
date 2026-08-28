import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import fs from "node:fs/promises";
import path from "node:path";
import { chromium } from "playwright";

const PRODUCT_HEAD="5ec45f13d44a950a7a0c84617759df5c90ffcede";
const BASE_URL=process.env.JARVISOS_EVIDENCE_URL||"http://127.0.0.1:4173";
const REFERENCE_URL=process.env.JARVISOS_REFERENCE_URL||"http://127.0.0.1:4174";
const OUT_DIR=process.env.JARVISOS_EVIDENCE_DIR||"evidence/100g-artifacts";
const REPO_ROOT=path.resolve(process.cwd(),"..");
const surfaces=[
{id:"process",route:"/design/process",viewport:{width:1365,height:768},ref:"docs/design-references/process-beta/process-beta-approved-2026-08-26.html",sha256:"d3bb06d9a7c761699a21b9b6b0a1901214a799f06dd31570c2fbfedc018cc475"},
{id:"bluecad",route:"/design/bluecad",viewport:{width:1365,height:768},ref:"docs/design-references/bluecad-beta/bluecad-beta-approved-2026-08-26.html",sha256:"da4ddfb1ebf6e0c7d39c133bf9b7c0da82e14428bad87748b0f7aa37a7e17bd9"},
{id:"project-basis",route:"/memory/project-basis",viewport:{width:1600,height:1000},ref:"docs/design-references/memory-beta/memory-project-basis-beta-approved-2026-08-26.html",sha256:"f901f977979d8389bec74a65510d1841ea12aa1e706f19dce0816a01d852b324"},
{id:"models",route:"/memory/models",viewport:{width:1600,height:1000},ref:"docs/design-references/memory-beta/memory-models-beta-approved-2026-08-26.html",sha256:"2e76a9d740bb07adacc85379e71912b50015af5706995367ed1b1593d921f627"},
{id:"literature",route:"/memory/literature",viewport:{width:1600,height:1000},ref:"docs/design-references/memory-beta/memory-literature-beta-approved-2026-08-26.html",sha256:"c9e4225c5969ae86d9da6936b20eebfa6edbbc8a05b82a11d1a09d5a2231d150"},
{id:"roadmap",route:"/development/roadmap/timeline",viewport:{width:1600,height:1000},ref:"docs/design-references/development-beta/development-roadmap-timeline-beta-approved-2026-08-27.html",sha256:"eb71ddab8cd829d041319fca7a6b08d4e7f60ae57a51f96310ed9ea11d20dc70"},
{id:"calendar",route:"/development/roadmap/calendar",viewport:{width:1600,height:1000},ref:"docs/design-references/development-beta/development-calendar-beta-approved-2026-08-27.html",sha256:"3dc94b861478007080a3d9658ec81bc3c46394d0bf73f9a5aa4aa669024b2737"},
{id:"brainstorm",route:"/development/brainstorm",viewport:{width:1600,height:1000},ref:"docs/design-references/development-beta/development-brainstorm-beta-approved-2026-08-27.html",sha256:"2b30f8d558045becf3c79b7d9a7bfcfd186a42a6278d92f53a0150be61f82631"},
{id:"repository",route:"/coding/repository",viewport:{width:1600,height:1000},ref:"docs/design-references/coding-beta/coding-repository-beta-approved-2026-08-27.html",sha256:"afe3bf43eebc3da65e38aadcb27dcaac6f55b61959077cad82cbc51979b1d11f"},
{id:"runtime",route:"/coding/runtime",viewport:{width:1600,height:1000},ref:"docs/design-references/coding-beta/coding-runtime-beta-approved-2026-08-27.html",sha256:"041b2f8974a1ad866ac5fad700c920c3a4816e6a0d6263a185e20c0ca421893e"},
{id:"settings",route:"/settings/appearance",viewport:{width:1365,height:768},ref:"docs/design-references/settings-beta/settings-beta-approved-2026-08-26.html",sha256:"f30a0937f9e8cb1a189ade226a004ac4206597d1130433748b87d4c61043e5de"}
];
const workspaceIds=new Set(["project-basis","models","literature","roadmap","calendar","brainstorm","repository","runtime"]);
const sha256=bytes=>createHash("sha256").update(bytes).digest("hex");
const safe=s=>s.replace(/[^a-z0-9._-]+/gi,"-").toLowerCase();
const report={productHead:PRODUCT_HEAD,generatedAt:new Date().toISOString(),surfaces:[]};
await fs.mkdir(OUT_DIR,{recursive:true});
async function digestReference(s){const bytes=await fs.readFile(path.join(REPO_ROOT,s.ref));const actual=sha256(bytes);assert.equal(actual,s.sha256,`${s.id} canonical digest drift`);return actual;}
async function box(locator){return await locator.boundingBox();}
async function assertWorkspaceComposition(page,id){
 const header=page.locator(".final-fusion__workspace-head");
 assert.equal(await header.count(),1,`${id}: workspace header missing`);
 const work=page.locator(".final-fusion__workspace-head + .final-fusion, .final-fusion__workspace-head + .final-fusion__workbench").first();
 assert.equal(await work.count(),1,`${id}: work area missing after header`);
 const hb=await box(header);const wb=await box(work);assert.ok(hb&&wb,`${id}: layout boxes unavailable`);
 assert.ok(hb.height<150,`${id}: header remains oversized (${hb.height}px)`);
 assert.ok(wb.y>=hb.y+hb.height-2,`${id}: work area is not below header`);
 assert.ok(wb.y-(hb.y+hb.height)<=24,`${id}: dead-space gap remains (${wb.y-(hb.y+hb.height)}px)`);
 assert.ok(wb.width>=hb.width*0.9,`${id}: work area does not recover workspace width`);
 const active=header.locator(".final-fusion__peer-tabs [aria-current='page']");
 assert.equal(await active.count(),1,`${id}: active peer tab missing`);
 const inactive=header.locator(".final-fusion__peer-tabs a:not([aria-current='page'])").first();
 const a=await active.evaluate(el=>{const s=getComputedStyle(el);return {bg:s.backgroundColor,border:s.borderColor,weight:s.fontWeight}});
 assert.notEqual(a.bg,"rgb(76, 175, 80)",`${id}: active peer tab uses strong action green`);
 assert.notEqual(a.bg,"rgb(46, 125, 50)",`${id}: active peer tab uses strong action green`);
 if(await inactive.count()){const i=await inactive.evaluate(el=>{const s=getComputedStyle(el);return {bg:s.backgroundColor,border:s.borderColor}});assert.notEqual(i.bg,a.bg,`${id}: active/inactive peer tabs are visually indistinct`);}
}
async function assertSecondaryNav(page,id,root){
 const active=page.locator(`${root} [aria-current='page'], ${root} .is-active`).first();
 assert.ok(await active.count()>=1,`${id}: active secondary navigation missing`);
 const style=await active.evaluate(el=>{const s=getComputedStyle(el);return {bg:s.backgroundColor,border:s.borderColor,weight:s.fontWeight}});
 assert.notEqual(style.bg,"rgb(76, 175, 80)",`${id}: active navigation uses strong action green`);
 assert.notEqual(style.bg,"rgb(46, 125, 50)",`${id}: active navigation uses strong action green`);
}
const browser=await chromium.launch({headless:true});
try{
 for(const s of surfaces){
  const digest=await digestReference(s);
  const context=await browser.newContext({viewport:s.viewport,reducedMotion:"reduce"});
  const refPage=await context.newPage();
  const referenceUrl=`${REFERENCE_URL}/${s.ref}`;
  const rr=await refPage.goto(referenceUrl,{waitUntil:"domcontentloaded"});assert.ok(rr?.ok(),`${s.id}: canonical HTML failed to load`);
  await refPage.waitForTimeout(150);
  const referenceScreenshot=`chromium-${safe(s.id)}-canonical-${s.viewport.width}x${s.viewport.height}.png`;
  await refPage.screenshot({path:path.join(OUT_DIR,referenceScreenshot),fullPage:true});
  const page=await context.newPage();const errors=[];page.on("pageerror",e=>errors.push(String(e)));
  await page.goto(BASE_URL+s.route,{waitUntil:"networkidle"});assert.equal(new URL(page.url()).pathname,s.route,`${s.id}: route drift`);
  assert.equal(await page.locator(".application-shell--final").count(),1,`${s.id}: final shell missing`);
  if(workspaceIds.has(s.id))await assertWorkspaceComposition(page,s.id);
  if(s.id==="process"||s.id==="bluecad")await assertSecondaryNav(page,s.id,".design-stage__tabs");
  if(s.id==="settings")await assertSecondaryNav(page,s.id,".final-settings__tabs");
  if(s.id==="bluecad")assert.equal(await page.locator(".shell-navigator").count(),1,"BLUECAD navigator regression");
  if(s.id==="process"){for(const label of ["Add","Connect","Disconnect","Validate","Solve"]){const b=page.getByRole("button",{name:new RegExp(`^${label}$`,"i")});if(await b.count())assert.equal(await b.first().isDisabled(),true,`Process ${label} must remain unavailable`);}}
  const dims=await page.evaluate(()=>({scroll:document.documentElement.scrollWidth,client:document.documentElement.clientWidth}));assert.ok(dims.scroll<=dims.client+2,`${s.id}: horizontal overflow`);
  assert.equal(errors.length,0,`${s.id}: page errors ${errors.join(" | ")}`);
  const productionScreenshot=`chromium-${safe(s.id)}-production-${s.viewport.width}x${s.viewport.height}.png`;
  await page.screenshot({path:path.join(OUT_DIR,productionScreenshot),fullPage:true});
  report.surfaces.push({id:s.id,route:s.route,viewport:s.viewport,canonicalHtmlPath:s.ref,canonicalSha256:digest,referenceScreenshot,productionScreenshot,status:"PASS"});
  await context.close();
 }
}finally{await browser.close();}
assert.equal(report.surfaces.length,11,"all 11 surfaces must be proven");
await fs.writeFile(path.join(OUT_DIR,"manifest.json"),JSON.stringify(report,null,2)+"\n");
console.log(`100g browser evidence PASS: 11 surfaces on exact product head ${PRODUCT_HEAD}`);
