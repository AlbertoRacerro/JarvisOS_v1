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


def run(cmd: list[str], cwd: Path, env: dict[str, str], timeout: int = 300) -> str:
    result = subprocess.run(cmd, cwd=cwd, env=env, text=True, capture_output=True, timeout=timeout, check=False)
    if result.returncode:
        raise AssertionError(f"command failed: {cmd}\nstdout={result.stdout}\nstderr={result.stderr}")
    return result.stdout


def wait_url(url: str) -> None:
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1) as response:
                if response.status < 500:
                    return
        except Exception:
            time.sleep(0.2)
    raise AssertionError(f"server did not become ready: {url}")


SCRIPT = r'''import { chromium } from "playwright";
const app="http://127.0.0.1:5173", api="http://127.0.0.1:8000", sleep=ms=>new Promise(r=>setTimeout(r,ms));
const ok=(v,m)=>{if(!v)throw new Error(m)}, now="2026-08-15T12:00:00Z";
const workspaces=["a","b"].map(x=>({id:`workspace-${x}`,name:`Workspace ${x.toUpperCase()}`,slug:`workspace-${x}`,status:"active",created_at:now,updated_at:now}));
const payload=(outputs)=>JSON.stringify({schema_version:1,status:"succeeded",outputs,diagnostics:[]});
const mk=(id,label,model,output)=>({id,workspace_id:"workspace-a",model_version_id:model,run_label:label,status:"succeeded",input_payload:null,parameter_payload:null,output_payload:output,started_at:null,completed_at:null,created_at:now,notes:null});
const all=[mk("r1","Run One","m1",payload({pressure:{value:100,unit:"Pa"},flow:{value:2,unit:"m3/s"}})),mk("r2","Run Two","m1",payload({pressure:{value:150,unit:"Pa"},flow:{value:3,unit:"m3/s"}})),mk("r3","Run kPa","m1",payload({pressure:{value:.2,unit:"kPa"}})),mk("r4","Run Mixed Model","m2",payload({pressure:{value:130,unit:"Pa"}})),mk("r5","Malformed","m1","{bad"),mk("r6","Nonnumeric","m1",payload({pressure:{value:"100",unit:"Pa"}})),mk("r7","Unitless","m1",payload({pressure:{value:120,unit:""}}))];
const b=[{...mk("b1","Workspace B Run","m1",payload({pressure:{value:999,unit:"Pa"}})),workspace_id:"workspace-b"}];
let removed=false, delayA=false, delayed=false;
const browser=await chromium.launch({headless:true}), context=await browser.newContext({viewport:{width:640,height:520}}), page=await context.newPage(), errors=[]; page.on("pageerror",e=>errors.push(e.message));
await page.route(`${api}/**`,async route=>{const p=decodeURIComponent(new URL(route.request().url()).pathname); if(p==="/workspaces")return route.fulfill({status:200,contentType:"application/json",body:JSON.stringify(workspaces)}); const m=p.match(/^\/workspaces\/([^/]+)\/simulation-runs$/); if(m){if(m[1]==="workspace-a"&&delayA&&!delayed){delayed=true;await sleep(900)} const rows=m[1]==="workspace-a"?(removed?all.filter(r=>r.id!=="r2"):all):b; return route.fulfill({status:200,contentType:"application/json",body:JSON.stringify(rows)});} return route.fulfill({status:404,body:"not mocked"});});
await page.goto(`${app}/runs`,{waitUntil:"domcontentloaded"}); await page.getByRole("heading",{name:"Runs",exact:true}).waitFor(); const toggle=page.getByRole("button",{name:"Show analysis",exact:true}); await toggle.click(); const dock=page.locator("#shell-analysis-dock"), heading=dock.getByRole("heading",{name:"Analysis dock",exact:true}); await heading.waitFor(); ok(await heading.evaluate(e=>document.activeElement===e),"dock open focus"); await dock.getByRole("heading",{name:"Run comparison",exact:true}).waitFor();
const box=label=>dock.locator("label.analytics-run-row").filter({hasText:label}).locator('input[type="checkbox"]'); const text=()=>dock.innerText();
await box("Run One").check(); await box("Run Two").check(); await dock.getByRole("row",{name:/Minimum 100 Pa/}).waitFor(); let t=await text(); ok(t.includes("100 Pa")&&t.includes("150 Pa")&&t.includes("50 Pa"),"same-unit min/max/range");
await box("Run Two").uncheck(); await box("Run kPa").check(); await dock.getByText(/exact units are incompatible/i).waitFor(); ok(!(await text()).includes("200 Pa"),"unit conversion must not occur"); await box("Run kPa").uncheck();
const rejected=[["Malformed",/malformed JSON/i],["Nonnumeric",/not a finite numeric value/i],["Unitless",/unit is missing/i]]; for(const [label,reason] of rejected){await box(label).check(); await dock.getByText(reason).first().waitFor(); await box(label).uncheck();}
await box("Run Mixed Model").check(); await dock.getByText(/one exact model version/i).waitFor(); await box("Run Mixed Model").uncheck();
await box("Run Two").check(); removed=true; await dock.getByRole("button",{name:"Refresh",exact:true}).click(); await dock.getByText("1/6",{exact:true}).waitFor(); ok(!(await text()).includes("Run Two"),"disappeared selection retained"); removed=false; await dock.getByRole("button",{name:"Refresh",exact:true}).click(); await box("Run Two").waitFor();
await box("Run One").uncheck(); for(const label of ["Run Two","Run kPa","Run Mixed Model","Malformed","Nonnumeric","Unitless"]) await box(label).check(); await dock.getByText(/Six-run comparison limit reached/).waitFor(); ok(await box("Run One").isDisabled(),"six-run cap"); for(const label of ["Run Two","Run kPa","Run Mixed Model","Malformed","Nonnumeric","Unitless"]) await box(label).uncheck();
delayA=true; delayed=false; const late=dock.getByRole("button",{name:"Refresh",exact:true}).click(); await page.getByLabel("Workspace").selectOption("workspace-b"); await page.getByLabel("Workspace").selectOption("workspace-a"); await late; await sleep(1100); ok(!(await text()).includes("Workspace B Run"),"A-B-A stale response");
const width=await page.evaluate(()=>[document.documentElement.scrollWidth,document.documentElement.clientWidth]); ok(width[0]<=width[1]+1,`page overflow ${width}`); await page.keyboard.press("Escape"); await toggle.waitFor(); ok(await toggle.evaluate(e=>document.activeElement===e),"Escape focus restoration");
await page.goto(`${app}/engineering-data`,{waitUntil:"domcontentloaded"}); await page.getByRole("heading",{name:"Engineering Data",exact:true}).waitFor(); await page.goto(`${app}/design/flowsheet`,{waitUntil:"domcontentloaded"}); await page.getByRole("heading",{name:/Flowsheet/i}).first().waitFor(); ok(errors.length===0,`browser errors ${JSON.stringify(errors)}`); await browser.close(); console.log("ANALYTICS_DOCK_BROWSER_PROOF=PASS");'''


@pytest.mark.skipif(not RUN_PROOF, reason="temporary exact-head ANALYTICS-DOCK browser proof")
def test_exact_head_analytics_dock_browser_proof(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[2]
    target = tmp_path / "target"
    env = os.environ.copy()
    run(["git", "fetch", "origin", TARGET_BRANCH, "--depth=200"], root, env, 120)
    assert run(["git", "rev-parse", "FETCH_HEAD"], root, env).strip() == TARGET_SHA
    run(["git", "worktree", "add", "--detach", str(target), TARGET_SHA], root, env, 60)
    server: subprocess.Popen[str] | None = None
    try:
        for cmd in (["python","scripts/check_spec_status.py","--self-test"],["python","scripts/check_ui_foundation.py"],["python","scripts/check_app_shell.py"],["python","scripts/check_lineage_overview.py"],["python","scripts/check_runs_workbench.py"],["python","scripts/check_engineering_data.py"],["python","scripts/check_analytics_dock.py","--self-test"],["python","scripts/check_analytics_dock.py"]):
            run(cmd, target, env)
        frontend = target / "frontend"
        run(["npm","ci"], frontend, env)
        out = tmp_path / "harness"
        run([str(frontend/"node_modules/.bin/tsc"),"src/components/analytics/analyticsState.ts","src/components/analytics/analyticsStateHarness.ts","--target","ES2022","--module","commonjs","--moduleResolution","node","--skipLibCheck","--outDir",str(out)], frontend, env, 120)
        run(["node", str(out/"analyticsStateHarness.js")], frontend, env)
        run(["npm","run","build"], frontend, env, 180)
        run(["npm","install","--no-save","--package-lock=false","playwright@1.54.2"], frontend, env)
        run([str(frontend/"node_modules/.bin/playwright"),"install","--with-deps","chromium"], frontend, env, 360)
        script = frontend / ".analytics-proof.mjs"
        script.write_text(SCRIPT, encoding="utf-8")
        server = subprocess.Popen(["npm","run","dev","--","--host","127.0.0.1","--port","5173"], cwd=frontend, env=env, text=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        wait_url("http://127.0.0.1:5173/runs")
        run(["node", str(script)], frontend, env, 180)
    finally:
        if server is not None:
            server.terminate()
            try:
                server.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server.kill()
