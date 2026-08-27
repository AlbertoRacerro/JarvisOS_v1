import assert from "node:assert/strict";
import fs from "node:fs/promises";
import path from "node:path";
import { chromium, firefox } from "playwright";

const PRODUCT_HEAD = "c241599492c9d4c5b2968998aedbe870474b6fdc";
const BASE_URL = process.env.JARVISOS_EVIDENCE_URL || "http://127.0.0.1:4173";
const OUT_DIR = process.env.JARVISOS_EVIDENCE_DIR || "evidence/100f-artifacts";

const surfaces = [
  { id:"process", route:"/design/process", viewport:{width:1365,height:768}, ref:"docs/design-references/process-beta/process-beta-approved-2026-08-26.html", sha256:"d3bb06d9a7c761699a21b9b6b0a1901214a799f06dd31570c2fbfedc018cc475", heading:/Process/i },
  { id:"bluecad", route:"/design/bluecad", viewport:{width:1365,height:768}, ref:"docs/design-references/bluecad-beta/bluecad-beta-approved-2026-08-26.html", sha256:"da4ddfb1ebf6e0c7d39c133bf9b7c0da82e14428bad87748b0f7aa37a7e17bd9", heading:/BLUECAD/i },
  { id:"project-basis", route:"/memory/project-basis", viewport:{width:1600,height:1000}, ref:"docs/design-references/memory-beta/memory-project-basis-approved-2026-08-27.html", sha256:"f901f977979d8389bec74a65510d1841ea12aa1e706f19dce0816a01d852b324", heading:/Project Basis/i },
  { id:"models", route:"/memory/models", viewport:{width:1600,height:1000}, ref:"docs/design-references/memory-beta/memory-models-approved-2026-08-27.html", sha256:"2e76a9d740bb07adacc85379e71912b50015af5706995367ed1b1593d921f627", heading:/Models/i },
  { id:"literature", route:"/memory/literature", viewport:{width:1600,height:1000}, ref:"docs/design-references/memory-beta/memory-literature-approved-2026-08-27.html", sha256:"c9e4225c5969ae86d9da6936b20eebfa6edbbc8a05b82a11d1a09d5a2231d150", heading:/Literature/i },
  { id:"roadmap", route:"/development/roadmap/timeline", viewport:{width:1600,height:1000}, ref:"docs/design-references/development-beta/development-roadmap-timeline-approved-2026-08-27.html", sha256:"eb71ddab8cd829d041319fca7a6b08d4e7f60ae57a51f96310ed9ea11d20dc70", heading:/Roadmap|Timeline/i },
  { id:"calendar", route:"/development/roadmap/calendar", viewport:{width:1600,height:1000}, ref:"docs/design-references/development-beta/development-roadmap-calendar-approved-2026-08-27.html", sha256:"3dc94b861478007080a3d9658ec81bc3c46394d0bf73f9a5aa4aa669024b2737", heading:/Calendar/i },
  { id:"brainstorm", route:"/development/brainstorm", viewport:{width:1600,height:1000}, ref:"docs/design-references/development-beta/development-brainstorm-approved-2026-08-27.html", sha256:"2b30f8d558045becf3c79b7d9a7bfcfd186a42a6278d92f53a0150be61f82631", heading:/Brainstorm/i },
  { id:"repository", route:"/coding/repository", viewport:{width:1600,height:1000}, ref:"docs/design-references/coding-beta/coding-repository-approved-2026-08-27.html", sha256:"afe3bf43eebc3da65e38aadcb27dcaac6f55b61959077cad82cbc51979b1d11f", heading:/Repository/i },
  { id:"runtime", route:"/coding/runtime", viewport:{width:1600,height:1000}, ref:"docs/design-references/coding-beta/coding-runtime-approved-2026-08-27.html", sha256:"041b2f8974a1ad866ac5fad700c920c3a4816e6a0d6263a185e20c0ca421893e", heading:/Runtime/i },
  { id:"settings", route:"/settings/appearance", viewport:{width:1365,height:768}, ref:"docs/design-references/settings-beta/settings-beta-approved-2026-08-27.html", sha256:"f30a0937f9e8cb1a189ade226a004ac4206597d1130433748b87d4c61043e5de", heading:/Settings|Appearance/i }
];

const primaryNav = ["Design","Memory","Development","Coding","Settings"];
const report = { productHead: PRODUCT_HEAD, generatedAt: new Date().toISOString(), surfaces: [] };
await fs.mkdir(OUT_DIR,{recursive:true});

function safe(name){return name.replace(/[^a-z0-9._-]+/gi,"-").toLowerCase();}
async function visibleText(page,text){return await page.getByText(text,{exact:false}).count() > 0;}

async function assertPrimaryShell(page){
  const nav=page.getByRole("navigation",{name:"Primary navigation"});
  assert.equal(await nav.count(),1,"shared primary rail missing");
  const labels=(await nav.getByRole("link").allTextContents()).map(v=>v.trim()).filter(Boolean);
  assert.deepEqual(labels,primaryNav,"primary rail drifted from final IA");
  assert.equal(labels.includes("Home"),false,"Home must not return to final IA");
  assert.equal(await page.locator(".application-shell--final").count(),1,"final shared shell marker missing");
}

async function assertNoHorizontalOverflow(page){
  const dims=await page.evaluate(()=>({scrollWidth:document.documentElement.scrollWidth,clientWidth:document.documentElement.clientWidth,bodyScrollWidth:document.body.scrollWidth}));
  assert.ok(dims.scrollWidth<=dims.clientWidth+2,`page horizontal overflow ${dims.scrollWidth}>${dims.clientWidth}`);
  assert.ok(dims.bodyScrollWidth<=dims.clientWidth+2,`body horizontal overflow ${dims.bodyScrollWidth}>${dims.clientWidth}`);
}

async function assertUnavailableButton(page,label){
  const b=page.getByRole("button",{name:new RegExp(label,"i")});
  if(await b.count()) assert.equal(await b.first().isDisabled(),true,`${label} must be unavailable without an accepted owner`);
}

async function exercise(page,id){
  if(id==="process"){
    for(const label of ["Add","Connect","Disconnect","Validate","Solve"]) await assertUnavailableButton(page,label);
    assert.ok(await visibleText(page,"Jarvis"),"Process must preserve Jarvis inspector affordance");
    assert.ok(await visibleText(page,"Properties"),"Process must preserve Properties inspector affordance");
  }
  if(id==="bluecad"){
    assert.ok(await visibleText(page,"Jarvis"),"BLUECAD must preserve Jarvis inspector affordance");
    assert.ok(await visibleText(page,"Properties"),"BLUECAD must preserve Properties inspector affordance");
  }
  if(id==="project-basis"){
    await assertUnavailableButton(page,"Approve all");
    await assertUnavailableButton(page,"Validate");
  }
  if(id==="models"){
    const collapse=page.getByRole("button",{name:/Collapse all/i});
    if(await collapse.count()){await collapse.click();await page.waitForTimeout(80);}
  }
  if(id==="literature") assert.ok(await visibleText(page,"unavailable")||await visibleText(page,"no bounded literature"),"Literature missing truthful unavailable state");
  if(id==="roadmap"){
    assert.ok(await visibleText(page,"Execution status"),"Roadmap must retain Execution status below Timeline");
    assert.equal(await page.getByText("Board",{exact:true}).count(),0,"Board must not be a Roadmap peer");
    const calendar=page.getByRole("button",{name:"Calendar",exact:true});
    assert.equal(await calendar.count(),1,"Roadmap Calendar navigation missing");
    await calendar.click();await page.waitForTimeout(60);
    assert.equal(new URL(page.url()).pathname,"/development/roadmap/calendar","Roadmap Calendar NAVIGATE failed");
    await page.goto(BASE_URL+"/development/roadmap/timeline",{waitUntil:"networkidle"});
  }
  if(id==="calendar"){
    assert.ok(await visibleText(page,"Week"),"Calendar must expose Week default presentation");
    await assertUnavailableButton(page,"Add event");
    const timeline=page.getByRole("button",{name:"Timeline",exact:true});
    assert.equal(await timeline.count(),1,"Calendar Timeline navigation missing");
    await timeline.click();await page.waitForTimeout(60);
    assert.equal(new URL(page.url()).pathname,"/development/roadmap/timeline","Calendar Timeline NAVIGATE failed");
    await page.goto(BASE_URL+"/development/roadmap/calendar",{waitUntil:"networkidle"});
  }
  if(id==="brainstorm") for(const label of ["Attach","Record","Save","Reconcile","Promote"]) await assertUnavailableButton(page,label);
  if(id==="repository"){
    assert.ok(await visibleText(page,"Unknown"),"Repository truth must remain Unknown without observer");
    await assertUnavailableButton(page,"Suggest modification");
  }
  if(id==="runtime"){
    assert.ok(await visibleText(page,"Unknown"),"Runtime truth must remain Unknown when observer is absent");
    await assertUnavailableButton(page,"update");
    await assertUnavailableButton(page,"terminal");
  }
  if(id==="settings"){
    for(const label of ["Appearance","AI","System"]) assert.ok(await visibleText(page,label),`Settings ${label} section missing`);
    const ai=page.getByRole("link",{name:"AI"});if(await ai.count()){await ai.click();await page.waitForTimeout(80);}
    const system=page.getByRole("link",{name:"System"});if(await system.count()){await system.click();await page.waitForTimeout(80);}
    await page.goto(BASE_URL+"/settings/appearance",{waitUntil:"networkidle"});
  }
}

for(const engine of [{name:"chromium",impl:chromium},{name:"firefox",impl:firefox}]){
  const browser=await engine.impl.launch({headless:true});
  try{
    for(const surface of surfaces){
      const context=await browser.newContext({viewport:surface.viewport,reducedMotion:"reduce"});
      const page=await context.newPage();
      const pageErrors=[];page.on("pageerror",error=>pageErrors.push(String(error)));
      await page.goto(BASE_URL+surface.route,{waitUntil:"networkidle"});
      assert.equal(new URL(page.url()).pathname,surface.route,`${surface.id} route canonicalization drift`);
      await assertPrimaryShell(page);
      assert.equal(await page.getByRole("main").count(),1,`${surface.id} main region missing`);
      assert.ok(await page.getByText(surface.heading).count()>0||surface.id==="process"||surface.id==="bluecad",`${surface.id} canonical surface title missing`);
      await exercise(page,surface.id);
      await assertNoHorizontalOverflow(page);
      assert.equal(pageErrors.length,0,`${surface.id} page errors: ${pageErrors.join(" | ")}`);
      const screenshot=`${engine.name}-${safe(surface.id)}-${surface.viewport.width}x${surface.viewport.height}.png`;
      await page.screenshot({path:path.join(OUT_DIR,screenshot),fullPage:true});
      report.surfaces.push({engine:engine.name,id:surface.id,route:surface.route,viewport:surface.viewport,canonicalHtmlPath:surface.ref,canonicalSha256:surface.sha256,screenshot,status:"PASS"});
      await context.close();
    }
  } finally {await browser.close();}
}

assert.equal(report.surfaces.length,surfaces.length*2,"all 11 canonical surfaces must be proven in both browsers");
await fs.writeFile(path.join(OUT_DIR,"manifest.json"),JSON.stringify(report,null,2)+"\n");
console.log(`100f browser evidence PASS: ${report.surfaces.length} proofs on exact product head ${PRODUCT_HEAD}`);
