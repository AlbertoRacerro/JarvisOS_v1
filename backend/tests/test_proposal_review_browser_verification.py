from __future__ import annotations

import os
import subprocess
import time
import urllib.request
from pathlib import Path

import pytest

RUN_PROOF = os.environ.get("RUN_PROPOSAL_REVIEW_BROWSER_PROOF") == "true"
TARGET_SHA = os.environ.get("TARGET_IMPLEMENTATION_SHA", "2ae935f561ed89cd0ea73f06e0a888638ed9953f")
TARGET_BRANCH = "spec/054-proposal-review-1"


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
const app="http://127.0.0.1:5173", api="http://127.0.0.1:8000", sleep=ms=>new Promise(r=>setTimeout(r,ms)), ok=(v,m)=>{if(!v)throw new Error(m)};
const now="2026-08-15T20:00:00Z", workspaces=[{id:"workspace-a",name:"Workspace A",slug:"workspace-a",status:"active",created_at:now,updated_at:now},{id:"workspace-b",name:"Workspace B",slug:"workspace-b",status:"active",created_at:now,updated_at:now}];
const base={workspace_id:"workspace-a",status:"proposed",origin:"ai_proposed",source_ai_job_id:"job-1",promoted_at:null,created_at:now,updated_at:now,title:null,statement:null,decision_text:null,name:null,source_ref:null,notes:null,supersedes_parameter_id:null,scope:null,confidence:null,symbol:null,value:null,unit:null,value_status:null,value_min:null,value_max:null,rationale:null,linked_run_id:null};
const assumption={...base,id:"a1",record_kind:"assumption",statement:"<script>unsafe()</script> seawater density",scope:"hydraulics",confidence:"medium",source_ref:"paper:1"};
const replacement={...base,id:"p1",record_kind:"parameter",name:"Tube diameter",symbol:"D",value:"0.25",unit:"m",value_status:"literature",value_min:.2,value_max:.3,confidence:.8,source_ref:"paper:2",supersedes_parameter_id:"old-p"};
const decision={...base,id:"d1",record_kind:"decision",title:"Select tube",decision_text:"Use candidate A",rationale:"Lowest verified pressure drop"};
let proposals=[assumption,replacement,decision], accepted=[], rejected=[], replacementCalls=0, genericReplacementCalls=0, delayProposed=false, delayed=false;
const browser=await chromium.launch({headless:true}), context=await browser.newContext({viewport:{width:640,height:560}}), page=await context.newPage(), errors=[]; page.on("pageerror",e=>errors.push(e.message));
await page.route(`${api}/**`,async route=>{const u=new URL(route.request().url()), p=decodeURIComponent(u.pathname), method=route.request().method(); if(p==="/workspaces")return route.fulfill({status:200,contentType:"application/json",body:JSON.stringify(workspaces)}); if(p.match(/^\/workspaces\/[^/]+\/simulation-runs$/))return route.fulfill({status:200,contentType:"application/json",body:"[]"}); if(p==="/memory/proposals"&&method==="GET"){const status=u.searchParams.get("status"); if(status==="proposed"&&delayProposed&&!delayed){delayed=true;await sleep(800)} const rows=status==="accepted"?accepted:status==="rejected"?rejected:status==="superseded"?[]:status===null?[...proposals,...accepted,...rejected]:proposals; return route.fulfill({status:200,contentType:"application/json",body:JSON.stringify(rows)});} const repl=p.match(/^\/memory\/parameter\/([^/]+)\/promote-replacement$/); if(repl&&method==="POST"){replacementCalls++; const rec=proposals.find(r=>r.id===repl[1]); proposals=proposals.filter(r=>r.id!==repl[1]); accepted=[{...rec,status:"accepted",promoted_at:now},...accepted]; return route.fulfill({status:200,contentType:"application/json",body:JSON.stringify({accepted_parameter:{...rec,status:"accepted",promoted_at:now},superseded_parameter:{...rec,id:"old-p",status:"superseded",supersedes_parameter_id:null},invalidation:{id:"inv-1",source_ref:"parameter:old-p",replacement_ref:`parameter:${repl[1]}`,affected_count:2,graph_digest:"abc",created_at:now}})});} const tr=p.match(/^\/memory\/(assumption|parameter|decision)\/([^/]+)\/(promote|reject)$/); if(tr&&method==="POST"){const [,kind,id,action]=tr; if(kind==="parameter"&&id==="p1"&&action==="promote")genericReplacementCalls++; const rec=proposals.find(r=>r.id===id); if(!rec)return route.fulfill({status:404,contentType:"application/json",body:JSON.stringify({detail:"not found"})}); proposals=proposals.filter(r=>r.id!==id); const next={...rec,status:action==="promote"?"accepted":"rejected",promoted_at:action==="promote"?now:null}; (action==="promote"?accepted:rejected).unshift(next); return route.fulfill({status:200,contentType:"application/json",body:JSON.stringify(next)});} return route.fulfill({status:404,contentType:"application/json",body:JSON.stringify({detail:"not mocked"})});});
await page.goto(`${app}/design/review`,{waitUntil:"domcontentloaded"}); await page.getByRole("heading",{name:"Review",exact:true}).waitFor(); await page.getByText(/Choose a workspace elsewhere/).waitFor();
await page.goto(`${app}/runs`,{waitUntil:"domcontentloaded"}); await page.getByRole("heading",{name:"Runs",exact:true}).waitFor(); await page.getByLabel("Workspace").selectOption("workspace-a"); await page.goto(`${app}/design/review`,{waitUntil:"domcontentloaded"}); await page.getByRole("heading",{name:"Review",exact:true}).waitFor();
const nav=page.getByLabel("Proposal review navigator"); await nav.getByRole("button",{name:/assumption.*seawater density/i}).waitFor(); await nav.getByRole("button",{name:/assumption.*seawater density/i}).click(); await page.getByText("hydraulics",{exact:true}).waitFor(); ok(await page.locator("script").count()===0,"untrusted statement became script"); ok((await page.getByText(/<script>unsafe\(\)<\/script>/).count())===1,"untrusted text not rendered inertly");
await nav.getByRole("button",{name:/parameter.*Tube diameter/i}).click(); await page.getByText("0.25",{exact:true}).waitFor(); await page.getByRole("button",{name:"Accept",exact:true}).click(); await nav.getByRole("button",{name:/decision.*Select tube/i}).waitFor(); ok(replacementCalls===1&&genericReplacementCalls===0,"configured replacement did not use dedicated endpoint"); await page.getByText(/freshness invalidation affected 2/).waitFor();
const decisionButton=nav.getByRole("button",{name:/decision.*Select tube/i}); await decisionButton.click(); await page.getByRole("button",{name:"Reject",exact:true}).click(); await nav.getByRole("button",{name:/assumption.*seawater density/i}).waitFor(); ok(rejected.some(r=>r.id==="d1"),"decision reject not persisted by canonical mock");
const filter=nav.getByLabel("Status"); delayProposed=true; delayed=false; await filter.selectOption("accepted"); await nav.getByText(/record/).first().waitFor(); const late=filter.selectOption("proposed"); await filter.selectOption("accepted"); await filter.selectOption("proposed"); await late; await sleep(900); ok((await nav.innerText()).includes("seawater density"),"filter A-B-A stale response replaced current state");
const width=await page.evaluate(()=>[document.documentElement.scrollWidth,document.documentElement.clientWidth]); ok(width[0]<=width[1]+1,`page overflow ${width}`); ok(errors.length===0,`browser errors ${JSON.stringify(errors)}`); await browser.close(); console.log("PROPOSAL_REVIEW_BROWSER_PROOF=PASS");'''


@pytest.mark.skipif(not RUN_PROOF, reason="temporary exact-head PROPOSAL-REVIEW browser proof")
def test_exact_head_proposal_review_browser_proof(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[2]
    target = tmp_path / "target"
    env = os.environ.copy()
    run(["git", "fetch", "origin", TARGET_BRANCH, "--depth=200"], root, env, 120)
    assert run(["git", "rev-parse", "FETCH_HEAD"], root, env).strip() == TARGET_SHA
    run(["git", "worktree", "add", "--detach", str(target), TARGET_SHA], root, env, 60)
    server: subprocess.Popen[str] | None = None
    try:
        for cmd in (["python","scripts/check_spec_status.py","--self-test"],["python","scripts/check_ui_foundation.py"],["python","scripts/check_app_shell.py"],["python","scripts/check_lineage_overview.py"],["python","scripts/check_engineering_data.py"],["python","scripts/check_proposal_review.py","--self-test"],["python","scripts/check_proposal_review.py"]):
            run(cmd, target, env)
        run(["python","-m","pytest","-q","backend/tests/test_memory_store.py"], target, env, 180)
        frontend = target / "frontend"
        run(["npm","ci"], frontend, env)
        out = tmp_path / "harness"
        run([str(frontend/"node_modules/.bin/tsc"),"src/components/review/reviewState.ts","src/components/review/reviewStateHarness.ts","--target","ES2022","--module","commonjs","--moduleResolution","node","--skipLibCheck","--outDir",str(out)], frontend, env, 120)
        run(["node", str(out/"reviewStateHarness.js")], frontend, env)
        run(["npm","run","build"], frontend, env, 180)
        run(["npm","install","--no-save","--package-lock=false","playwright@1.54.2"], frontend, env)
        run([str(frontend/"node_modules/.bin/playwright"),"install","--with-deps","chromium"], frontend, env, 360)
        script = frontend / ".proposal-review-proof.mjs"
        script.write_text(SCRIPT, encoding="utf-8")
        server = subprocess.Popen(["npm","run","dev","--","--host","127.0.0.1","--port","5173"], cwd=frontend, env=env, text=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        wait_url("http://127.0.0.1:5173/design/review")
        run(["node", str(script)], frontend, env, 180)
    finally:
        if server is not None:
            server.terminate()
            try:
                server.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server.kill()
