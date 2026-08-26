import { chromium, firefox } from "playwright";
import fs from "node:fs/promises";
import path from "node:path";
import assert from "node:assert/strict";

const PRODUCT_HEAD = "db2591239a4ba22906157898b5ba83eb1e03e9a0";
const ORIGIN = "http://127.0.0.1:4173";
const API = "http://127.0.0.1:8000";
const now = "2026-08-26T00:00:00Z";
const SHA = "a".repeat(64);
const KEY_A = `bluecad-part-sha256-${"1".repeat(64)}`;
const tri = new Float32Array([-1,0,0,0,1,0,1,0,0]);
const triBytes = Buffer.from(tri.buffer);
const gltf = JSON.stringify({asset:{version:"2.0"},buffers:[{uri:`data:application/octet-stream;base64,${triBytes.toString("base64")}`,byteLength:triBytes.length}],bufferViews:[{buffer:0,byteOffset:0,byteLength:36}],accessors:[{bufferView:0,componentType:5126,count:3,type:"VEC3",min:[-1,0,0],max:[1,1,0]}],meshes:[{name:"Evidence tube",primitives:[{attributes:{POSITION:0}}]}],nodes:[{name:KEY_A,children:[1]},{name:"Evidence tube",mesh:0}],scenes:[{nodes:[0]}],scene:0});
const workspace = {id:"ws-1",name:"Visual evidence workspace",slug:"visual-evidence",description:null,status:"active",created_at:now,updated_at:now};
const candidate = {id:"bound",workspace_id:"ws-1",brief_text:"Candidate bound",brief_digest:"d".repeat(64),status:"valid",parked_reason:null,spec_artifact_id:null,glb_artifact_id:"bound-glb",report_artifact_id:null,promoted_decision_id:null,origin:"evidence",parent_candidate_id:null,loop_config_json:"{}",created_at:now,updated_at:now,notes:null,attempts:[{id:"bound-attempt",candidate_id:"bound",attempt_no:1,route_class:"local",proposal_outcome:"success",build_outcome:"success",validation_verdict:"pass",manifest_artifact_id:"bound-manifest",started_at:now,finished_at:now}]};
const manifest = {spec_id:"spec-bound",parts:{"PART-A":{kind:"tube"}},artifacts:{"model.glb":{sha256:SHA}},scene_binding:{version:"bluecad_scene_binding_v0_1",artifact:"model.glb",spec_id:"spec-bound",objects:{[KEY_A]:{part_id:"PART-A"}}}};
const aggregate = {candidate,artifacts:[{id:"bound-glb",roles:["candidate.glb_artifact_id"],filename:"model.glb",mime_type:"model/gltf-binary",sha256:SHA,status:"ready",source_ref:null,created_at:now,content_url:"/workspaces/ws-1/bluecad/artifacts/bound-glb/content"},{id:"bound-manifest",roles:["attempt.manifest_artifact_id"],filename:"manifest.json",mime_type:"application/json",sha256:"b".repeat(64),status:"ready",source_ref:null,created_at:now,content_url:"/workspaces/ws-1/bluecad/artifacts/bound-manifest/content"}],evidence:[],runs:[],freshness:"fresh",diagnostics:[]};
const parameters = [
{id:"p-flow",workspace_id:"ws-1",name:"Nominal recirculation flow rate with long engineering label",symbol:"Q_rec",value:"18.450",unit:"m3/h",value_status:"validated",value_min:17.2,value_max:19.8,source_ref:"pilot-loop-2026",confidence:0.92,status:"accepted",notes:"Measured operating envelope",supersedes_parameter_id:null,created_at:now,updated_at:now,lifecycle_state:"active"},
{id:"p-temp",workspace_id:"ws-1",name:"Reactor outlet temperature",symbol:"T_out",value:"318.15",unit:"K",value_status:"candidate",value_min:null,value_max:null,source_ref:"design-study",confidence:0.65,status:"proposed",notes:null,supersedes_parameter_id:null,created_at:now,updated_at:now,lifecycle_state:"inactive"}
];
const modelSpecs=[{id:"m1",workspace_id:"ws-1",title:"Photobioreactor hydraulic model",engineering_question:"Maintain residence time under bounded pumping demand",scope:"Hydraulics and operating envelope",status:"active",maturity_status:"reviewed",schema_version:3,created_at:now,updated_at:now}];
const assumptions=[{id:"a1",workspace_id:"ws-1",statement:"Seawater density remains within the validated operating interval.",confidence:0.8,status:"active"}];
const decisions=[{id:"d1",workspace_id:"ws-1",title:"Pump operating point",decision_text:"Retain the validated operating point pending higher-fidelity evidence.",status:"accepted"}];
const aiSettings={policy_mode:"operator",monthly_api_budget_usd:10,api_spend_month_to_date_usd:0,paid_ai_enabled:false,default_ai_provider:"fake",default_ai_model:"fake",provider_mode:"fake",use_fake_provider_when_budget_zero:true,scaleway_enabled:false,scaleway_smoke_test_enabled:false,scaleway_live_smoke_test_enabled:false,scaleway_monthly_token_cap:0,scaleway_hard_stop_token_cap:0,scaleway_free_tier_reference_tokens:0,scaleway_input_tokens_month_to_date:0,scaleway_output_tokens_month_to_date:0,usage_total_tokens:0,smoke_test_mode_enabled:false,max_direct_continuations:0,max_direct_continuations_min:0,max_direct_continuations_max:16,direct_continuation_policy_version:"v1",updated_at:now};
const aiStatus={policy_mode:"operator",ai_enabled:false,active_provider_mode:"fake",provider_mode:"fake",provider_id:"fake",adapter_enabled:false,fake_provider_enabled:true,scaleway_enabled:false,scaleway_api_key_configured:false,scaleway_provider_implementation:"disabled",paid_ai_enabled:false,monthly_api_budget_usd:10,spend_month_to_date_usd:0,scaleway_smoke_test_enabled:false,scaleway_live_smoke_test_enabled:false,scaleway_monthly_token_cap:0,scaleway_hard_stop_token_cap:0,scaleway_free_tier_reference_tokens:0,scaleway_input_tokens_month_to_date:0,scaleway_output_tokens_month_to_date:0,usage_total_tokens:0,external_calls_allowed:false,blocking_reason:"disabled"};
const systemInfo={status:"ok",app_name:"JarvisOS",version:"evidence",environment:"test",data_root:"/tmp",data_root_exists:true,paths:{},database:{engine:"sqlite",database_file:"evidence.db",configured:true,ready:true,initialized:true},ai:{provider:"fake",gateway_configured:true,provider_configured:false,provider_calls_enabled:false,provider_mode:"fake",monthly_budget_usd:10,spend_month_to_date_usd:0,scaleway_enabled:false,scaleway_api_key_configured:false,scaleway_provider_implementation:"disabled",scaleway_smoke_test_enabled:false,scaleway_live_smoke_test_enabled:false,scaleway_monthly_token_cap:0,scaleway_hard_stop_token_cap:0,scaleway_free_tier_reference_tokens:0,scaleway_input_tokens_month_to_date:0,scaleway_output_tokens_month_to_date:0,blocking_reason:"disabled"}};

await fs.mkdir("reports/100-browser",{recursive:true});
const engines=[['chromium',chromium],['firefox',firefox]];
const summary=[];
for (const [engineName,engine] of engines) {
  const browser=await engine.launch({headless:true});
  const context=await browser.newContext({viewport:{width:1440,height:1000},colorScheme:"light",reducedMotion:"reduce"});
  const page=await context.newPage();
  const mutations=[]; const pageErrors=[]; const consoleErrors=[];
  page.on('pageerror',e=>pageErrors.push(String(e)));
  page.on('console',m=>{if(m.type()==='error') consoleErrors.push(m.text());});
  page.on('request',r=>{if(['POST','PUT','PATCH','DELETE'].includes(r.method())&&!r.url().includes('/ai/context/packs/preview')) mutations.push(`${r.method()} ${r.url()}`);});
  await page.route(`${API}/**`,async route=>{
    const req=route.request(); const u=new URL(req.url()); const p=u.pathname;
    const json=(v,status=200)=>route.fulfill({status,contentType:'application/json',headers:{'Access-Control-Allow-Origin':'*'},body:JSON.stringify(v)});
    if(req.method()==='OPTIONS') return route.fulfill({status:204,headers:{'Access-Control-Allow-Origin':'*','Access-Control-Allow-Headers':'Content-Type'}});
    if(req.method()==='POST'&&p==='/ai/context/packs/preview') return json({context_digest:null,context_sources_manifest:[],char_count:0,estimated_token_count:0,included_count:0,dropped_count:0,budget_chars:0});
    if(req.method()!=='GET') return json({error:'mutation forbidden in evidence'},409);
    if(p==='/workspaces') return json([workspace]);
    if(p==='/workspaces/ws-1/bluecad/candidates') return json([candidate]);
    if(p==='/workspaces/ws-1/bluecad/candidates/bound/aggregate') return json(aggregate);
    if(p==='/workspaces/ws-1/bluecad/artifacts/bound-glb/content') return route.fulfill({status:200,contentType:'model/gltf+json',headers:{'Access-Control-Allow-Origin':'*'},body:gltf});
    if(p==='/workspaces/ws-1/bluecad/artifacts/bound-manifest/content') return json(manifest);
    if(p==='/workspaces/ws-1/model-specs') return json(modelSpecs);
    if(p==='/workspaces/ws-1/assumptions') return json(assumptions);
    if(p==='/workspaces/ws-1/parameters') return json(parameters);
    if(p==='/workspaces/ws-1/decisions') return json(decisions);
    if(p==='/workspaces/ws-1/model-implementations') return json([]);
    if(p==='/ai/threads') return json({threads:[]});
    if(p==='/ai/settings') return json(aiSettings);
    if(p==='/ai/status') return json(aiStatus);
    if(p==='/secrets/scaleway/status') return json({key_present:false,source:'none',effective_source:'none',persisted_state:'absent',storage_mode:'none',reason_code:null});
    if(p==='/system/info') return json(systemInfo);
    return json([]);
  });
  const shot=async(name)=>page.screenshot({path:`reports/100-browser/${engineName}-${name}.png`,fullPage:true});
  const setAppearance=async(value)=>{await page.evaluate(v=>localStorage.setItem('jarvisos:appearance:v1',v),value); await page.reload();};
  const overflow=async()=>page.evaluate(()=>document.documentElement.scrollWidth-document.documentElement.clientWidth);

  // A: real BLUECAD artifact fixture -> semantic selected object -> Properties/Jarvis/dock.
  await page.goto(`${ORIGIN}/design/model`); await page.getByRole('heading',{name:'Model workbench'}).waitFor();
  await page.getByRole('button',{name:/Candidate bound/}).click();
  await page.getByText('Orbit, pan, zoom, or click a mesh to inspect visible geometry.').waitFor({timeout:10000});
  const contextToggle=page.getByRole('button',{name:/Show context|Hide context/}); if((await contextToggle.first().textContent())?.includes('Show')) await contextToggle.first().click();
  const props=page.getByRole('tab',{name:'Properties'}); if(await props.count()) await props.click();
  await page.getByLabel('Inspectable mesh').selectOption('mesh-1');
  await page.locator('#shell-sidecar-pane-properties').filter({hasText:'PART-A'}).waitFor({timeout:10000});
  const jarvis=page.getByRole('tab',{name:'Jarvis'}); assert.ok(await jarvis.count(),'Jarvis tab missing on selected BLUECAD object');
  const dockToggle=page.getByRole('button',{name:/Show analysis|Hide analysis/}); if((await dockToggle.first().textContent())?.includes('Show')) await dockToggle.first().click();
  await page.getByRole('heading',{name:'Analysis dock'}).waitFor(); await shot('A-model-light');

  // B: Process remains inert and visually primary.
  await page.goto(`${ORIGIN}/design/process`); await page.getByRole('heading',{name:'Process workspace'}).waitFor();
  assert.equal(await page.getByRole('button',{name:/Add equipment|Connect/}).count(),2); assert.equal(await page.getByText('No process topology is loaded.',{exact:true}).count(),1);
  assert.equal((await page.locator('body').innerText()).match(/pump|compressor|reactor stream/gi)?.length??0,0,'fake process semantics appeared'); await shot('B-process-light');

  // C: dense real-shaped Engineering Data records and numeric hierarchy.
  await page.goto(`${ORIGIN}/engineering-data`); await page.getByRole('heading',{name:'Engineering Data'}).waitFor();
  await page.getByText('Nominal recirculation flow rate with long engineering label',{exact:true}).waitFor({timeout:10000});
  await page.getByText('18.450',{exact:true}).first().waitFor(); await shot('C-engineering-data-light');

  // D: appearance/accent controls + semantic isolation + local-only writes.
  await page.goto(`${ORIGIN}/settings`); await page.getByRole('heading',{name:'Appearance & accent'}).waitFor();
  const semanticBefore=await page.evaluate(()=>getComputedStyle(document.documentElement).getPropertyValue('--color-status-danger-bg'));
  for (const label of ['Microalgae','Leaf Chlorophyll','Lagoon']) { await page.getByLabel(label,{exact:true}).check(); }
  await page.getByLabel('Custom',{exact:true}).check();
  const hex=page.getByLabel('HEX',{exact:true}); await hex.fill('#C46B2B'); await page.waitForTimeout(80);
  assert.equal(await page.evaluate(()=>getComputedStyle(document.documentElement).getPropertyValue('--accent-seed').trim()),'#C46B2B');
  const semanticAfter=await page.evaluate(()=>getComputedStyle(document.documentElement).getPropertyValue('--color-status-danger-bg')); assert.equal(semanticAfter,semanticBefore,'warm custom accent changed danger semantics');
  await hex.fill('#5B6FD8'); await page.waitForTimeout(80); assert.equal(await page.evaluate(()=>getComputedStyle(document.documentElement).getPropertyValue('--accent-seed').trim()),'#5B6FD8');
  await page.getByRole('button',{name:'Reset to Microalgae'}).click(); assert.equal(await page.evaluate(()=>getComputedStyle(document.documentElement).getPropertyValue('--accent-seed').trim()),'#528B68'); await shot('D-settings-light');
  assert.deepEqual(mutations,[],'visual proof dispatched a backend mutation');

  // Dark parity, reduced motion, keyboard focus, compact/effective-200% containment.
  await setAppearance('dark'); await page.goto(`${ORIGIN}/engineering-data`); await page.getByRole('heading',{name:'Engineering Data'}).waitFor(); await shot('C-engineering-data-dark');
  await page.goto(`${ORIGIN}/settings`); await page.getByRole('heading',{name:'Appearance & accent'}).waitFor(); await shot('D-settings-dark');
  const motion=await page.evaluate(()=>getComputedStyle(document.documentElement).getPropertyValue('--motion-standard').trim()); assert.ok(motion==='0ms'||motion==='0s',`reduced motion not collapsed: ${motion}`);
  await page.keyboard.press('Tab'); assert.ok(await page.evaluate(()=>document.activeElement!==document.body),'keyboard focus did not move');
  await page.setViewportSize({width:640,height:900}); await page.goto(`${ORIGIN}/design/process`); await page.getByRole('heading',{name:'Process workspace'}).waitFor(); assert.ok((await overflow())<=1,`compact/effective-200% page overflow ${(await overflow())}px`);
  await page.goto(`${ORIGIN}/engineering-data`); await page.getByRole('heading',{name:'Engineering Data'}).waitFor(); assert.ok((await overflow())<=1,`Engineering Data compact overflow ${(await overflow())}px`);

  assert.deepEqual(pageErrors,[],`page errors: ${pageErrors.join(' | ')}`);
  assert.deepEqual(consoleErrors,[],`console errors: ${consoleErrors.join(' | ')}`);
  summary.push({engine:engineName,productHead:PRODUCT_HEAD,proofs:'A-D',reducedMotion:true,compactWidth:640,mutations:mutations.length});
  await browser.close();
}
await fs.writeFile(path.join('reports','100-browser','summary.json'),JSON.stringify(summary,null,2)+'\n');
console.log('VISUAL_IDENTITY_100_BROWSER_PASS',summary);
