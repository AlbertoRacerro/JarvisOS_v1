from __future__ import annotations

import os
import subprocess
import time
import urllib.request
from pathlib import Path

import pytest

RUN_PROOF = os.environ.get("RUN_ANALYTICS_DOCK_BROWSER_PROOF") == "true"
TARGET_SHA = os.environ.get("TARGET_IMPLEMENTATION_SHA", "b56d6502389b0c5dcb7d16bed740f5e70cb45468")
TARGET_BRANCH = "spec/089-analytics-dock-1"


def _run(command: list[str], *, cwd: Path, env: dict[str, str], timeout: int = 300) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(command, cwd=cwd, env=env, text=True, capture_output=True, timeout=timeout, check=False)
    if result.returncode != 0:
        raise AssertionError(f"command failed: {command}\nstdout={result.stdout}\nstderr={result.stderr}")
    return result


def _wait(url: str, timeout: float = 20.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1) as response:
                if response.status < 500:
                    return
        except Exception:
            time.sleep(0.2)
    raise AssertionError(f"server did not become ready: {url}")


def _write_script(path: Path) -> None:
    path.write_text(r'''import { chromium } from "playwright";
const app="http://127.0.0.1:5173", api="http://127.0.0.1:8000";
const sleep=ms=>new Promise(r=>setTimeout(r,ms)); const assert=(v,m)=>{if(!v)throw new Error(m)};
const now="2026-08-15T12:00:00Z";
const workspaces=[{id:"workspace-a",name:"Workspace A",slug:"workspace-a",status:"active",created_at:now,updated_at:now},{id:"workspace-b",name:"Workspace B",slug:"workspace-b",status:"active",created_at:now,updated_at:now}];
const payload=(outputs,status="succeeded")=>JSON.stringify({schema_version:1,status,outputs,diagnostics:[]});
const run=(id,label,model,status,outputs)=>({id,workspace_id:"workspace-a",model_version_id:model,run_label:label,status,input_payload:null,parameter_payload:null,output_payload:outputs,started_at:null,completed_at:null,created_at:now,notes:null});
let runsA=[
 run("r1","Run One","model-v1","succeeded",payload({pressure:{value:100,unit:"Pa"},flow:{value:2,unit:"m3/s"}})),
 run("r2","Run Two","model-v1","succeeded",payload({pressure:{value:150,unit:"Pa"},flow:{value:3,unit:"m3/s"}})),
 run("r3","Run kPa","model-v1","succeeded",payload({pressure:{value:0.2,unit:"kPa"}})),
 run("r4","Run Mixed Model","model-v2","succeeded",payload({pressure:{value:130,unit:"Pa"}})),
 run("r5","Malformed","model-v1","succeeded","{bad"),
 run("r6","Nonnumeric","model-v1","succeeded",payload({pressure:{value:"100",unit:"Pa"}})),
 run("r7","Unitless","model-v1","succeeded",payload({pressure:{value:120,unit:""}})),
];
let delayFirstA=false, firstASeen=false, removed=false;
const runsB=[{...run("b1","Workspace B Run","model-v1","succeeded",payload({pressure:{value:999,unit:"Pa"}})),workspace_id:"workspace-b"}];
const browser=await chromium.launch({headless:true}); const context=await browser.newContext({viewport:{width:640,height:520}}); const page=await context.newPage(); const errors=[]; page.on("pageerror",e=>errors.push(e.message));
await page.route(`${api}/**`,async route=>{const p=decodeURIComponent(new URL(route.request().url()).pathname); if(p==="/workspaces")return route.fulfill({status:200,contentType:"application/json",body:JSON.stringify(workspaces)}); const m=p.match(/^\/workspaces\/([^/]+)\/simulation-runs$/); if(m){const ws=m[1]; if(ws==="workspace-a"&&delayFirstA&&!firstASeen){firstASeen=true; await sleep(900);} const rows=ws==="workspace-a"?(removed?runsA.filter(r=>r.id!=="r2"):runsA):runsB; return route.fulfill({status:200,contentType:"application/json",body:JSON.stringify(rows)});} return route.fulfill({status:404,body:"not mocked"});});
await page.goto(`${app}/runs`,{waitUntil:"domcontentloaded"}); await page.getByRole("heading",{name:"Runs",exact:true}).waitFor(); await page.getByRole("button",{name:"Show analysis",exact:true}).click(); const dock=page.locator("#shell-analysis-dock"); await dock.getByRole("heading",{name:"Analysis",exact:true}).waitFor(); assert(await dock.getByRole("heading",{name:"Analysis",exact:true}).evaluate(el=>document.activeElement===el),"analysis heading did not receive focus"); await dock.getByRole("heading",{name:"Run comparison",exact:true}).waitFor();
const box=label=>dock.getByLabel(label,{exact:true}); await box("Run One").check(); await box("Run Two").check(); await dock.getByText("Minimum",{exact:true}).waitFor(); assert((await dock.innerText()).includes("100 Pa")&&(await dock.innerText()).includes("150 Pa")&&(await dock.innerText()).includes("50 Pa"),"valid comparison summary missing");
await box("Run Two").uncheck(); await box("Run kPa").check(); await dock.getByText(/incompatible exact units/i).waitFor(); assert(!(await dock.innerText()).includes("200 Pa"),"unit conversion appeared");
await box("Run kPa").uncheck(); for(const label of ["Malformed","Nonnumeric","Unitless"]){await box(label).check(); await dock.getByText(/missing|unsupported|usable|invalid/i).first().waitFor(); await box(label).uncheck();}
await box("Run Mixed Model").check(); await dock.getByText(/one model version/i).waitFor(); await box("Run Mixed Model").uncheck();
await box("Run Two").check(); removed=true; await dock.getByRole("button",{name:"Refresh",exact:true}).click(); await dock.getByText("1/6",{exact:true}).waitFor(); assert(!(await dock.innerText()).includes("Run Two"),"disappeared selected run survived refresh"); removed=false;
await box("Run One").uncheck(); for(const label of ["Run Two","Run kPa","Run Mixed Model","Malformed","Nonnumeric","Unitless"]){await box(label).check();} await dock.getByText(/Six-run comparison limit reached/).waitFor(); assert(await box("Run One").isDisabled(),"six-run cap did not disable seventh run");
for(const label of ["Run Two","Run kPa","Run Mixed Model","Malformed","Nonnumeric","Unitless"]){await box(label).uncheck();}
delayFirstA=true; firstASeen=false; const refreshPromise=dock.getByRole("button",{name:"Refresh",exact:true}).click(); await page.getByLabel("Workspace").selectOption("workspace-b"); await page.getByLabel("Workspace").selectOption("workspace-a"); await refreshPromise; await sleep(1200); assert(!(await dock.innerText()).includes("Workspace B Run"),"late workspace response repainted analytics");
const overflow=await page.evaluate(()=>({scroll:document.documentElement.scrollWidth,client:document.documentElement.clientWidth})); assert(overflow.scroll<=overflow.client+1,`page overflow ${JSON.stringify(overflow)}`);
await page.keyboard.press("Escape"); await page.getByRole("button",{name:"Show analysis",exact:true}).waitFor(); assert(await page.getByRole("button",{name:"Show analysis",exact:true}).evaluate(el=>document.activeElement===el),"Escape did not restore dock-toggle focus");
await page.goto(`${app}/engineering-data`,{waitUntil:"domcontentloaded"}); await page.getByRole("heading",{name:"Engineering Data",exact:true}).waitFor(); await page.goto(`${app}/design/flowsheet`,{waitUntil:"domcontentloaded"}); await page.getByRole("heading",{name:/Flowsheet/i}).first().waitFor(); assert(errors.length===0,`uncaught browser errors: ${JSON.stringify(errors)}`); await browser.close(); console.log("ANALYTICS_DOCK_BROWSER_PROOF=PASS");
''',encoding="utf-8")


@pytest.mark.skipif(not RUN_PROOF, reason="temporary exact-head ANALYTICS-DOCK browser proof")
def test_exact_head_analytics_dock_browser_proof(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[2]
    target = tmp_path / "target"
    env = os.environ.copy()
    _run(["git", "fetch", "origin", TARGET_BRANCH, "--depth=200"], cwd=repo_root, env=env, timeout=120)
    initial = _run(["git", "rev-parse", "FETCH_HEAD"], cwd=repo_root, env=env).stdout.strip()
    assert initial == TARGET_SHA, (initial, TARGET_SHA)
    _run(["git", "worktree", "add", "--detach", str(target), TARGET_SHA], cwd=repo_root, env=env, timeout=60)
    server: subprocess.Popen[str] | None = None
    try:
        for command in (["python","scripts/check_spec_status.py","--self-test"],["python","scripts/check_ui_foundation.py"],["python","scripts/check_app_shell.py"],["python","scripts/check_lineage_overview.py"],["python","scripts/check_runs_workbench.py"],["python","scripts/check_engineering_data.py"],["python","scripts/check_analytics_dock.py","--self-test"],["python","scripts/check_analytics_dock.py"]):
            _run(command,cwd=target,env=env)
        frontend=target/"frontend"; _run(["npm","ci"],cwd=frontend,env=env,timeout=300)
        out=tmp_path/"harness"; _run([str(frontend/"node_modules/.bin/tsc"),"src/components/analytics/analyticsState.ts","src/components/analytics/analyticsStateHarness.ts","--target","ES2022","--module","commonjs","--moduleResolution","node","--skipLibCheck","--outDir",str(out)],cwd=frontend,env=env,timeout=120); _run(["node",str(out/"analyticsStateHarness.js")],cwd=frontend,env=env); _run(["npm","run","build"],cwd=frontend,env=env,timeout=180)
        _run(["npm","install","--no-save","--package-lock=false","playwright@1.54.2"],cwd=frontend,env=env,timeout=300); _run([str(frontend/"node_modules/.bin/playwright"),"install","--with-deps","chromium"],cwd=frontend,env=env,timeout=360)
        script=frontend/".analytics-proof.mjs"; _write_script(script); server=subprocess.Popen(["npm","run","dev","--","--host","127.0.0.1","--port","5173"],cwd=frontend,env=env,text=True,stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT); _wait("http://127.0.0.1:5173/runs"); _run(["node",str(script)],cwd=frontend,env=env,timeout=180)
    finally:
        if server is not None:
            server.terminate()
            try: server.wait(timeout=5)
            except subprocess.TimeoutExpired: server.kill()
