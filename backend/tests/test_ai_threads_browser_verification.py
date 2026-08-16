from __future__ import annotations

import os
import subprocess
import time
import urllib.request
from pathlib import Path

import pytest

RUN_PROOF = os.environ.get("RUN_AI_THREADS_BROWSER_PROOF") == "true"
TARGET_SHA = os.environ.get("TARGET_IMPLEMENTATION_SHA", "23f6ed8a5fb879b421f2395ea42e113089e39dd3")
TARGET_BRANCH = "spec/090-ai-threads-0"


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
const now="2026-08-16T10:00:00Z";
const workspaces=[{id:"workspace-a",name:"Workspace A",slug:"workspace-a",status:"active",created_at:now,updated_at:now},{id:"workspace-b",name:"Workspace B",slug:"workspace-b",status:"active",created_at:now,updated_at:now}];
const summary=(id,workspace,title)=>({id,workspace_id:workspace,title,created_at:now,last_activity_at:now});
let listARevision=0, detailXRevision=0, submitCalls=[], externalCalls=[], delayedSubmitResolve=null;
const interaction=(id,user,assistant,flowState="complete",persistence="captured")=>({id,request_id:`req-${id}`,interaction_index:0,user_text:user,assistant_text:assistant,assistant_text_truncated:false,flow_id:`flow-${id}`,persistence_state:persistence,persistence_error:null,flow_state:flowState,terminal_reason:null,attempt_count:1,terminal_attempt_id:`job-${id}`,proposal_ids:[],proposal_count:0,proposals_truncated:false,created_at:now,updated_at:now});
const browser=await chromium.launch({headless:true}); const context=await browser.newContext({viewport:{width:640,height:560}}); const page=await context.newPage(); const pageErrors=[]; page.on("pageerror",e=>pageErrors.push(e.message));
await page.route("**/*",async route=>{const url=route.request().url(); if(!url.startsWith(api)){if(url.startsWith("http")&&!url.startsWith(app))externalCalls.push(url); return route.continue();} const u=new URL(url), p=decodeURIComponent(u.pathname), method=route.request().method();
if(p==="/workspaces") return route.fulfill({status:200,contentType:"application/json",body:JSON.stringify(workspaces)});
if(p.match(/^\/workspaces\/[^/]+\/simulation-runs$/)) return route.fulfill({status:200,contentType:"application/json",body:"[]"});
if(p==="/ai/threads"&&method==="GET"){const w=u.searchParams.get("workspace_id"); if(w==="workspace-a"){const rev=++listARevision; if(rev===1)await sleep(600); return route.fulfill({status:200,contentType:"application/json",body:JSON.stringify({threads:[summary("thread-x","workspace-a",rev===1?"STALE A":"Current A"),summary("thread-y","workspace-a","Thread Y")]})});} return route.fulfill({status:200,contentType:"application/json",body:JSON.stringify({threads:[summary("thread-b","workspace-b","Current B")]})});}
if(p==="/ai/threads"&&method==="POST") return route.fulfill({status:200,contentType:"application/json",body:JSON.stringify(summary("thread-new","workspace-a","Untitled thread"))});
const detail=p.match(/^\/ai\/threads\/([^/]+)$/); if(detail&&method==="GET"){const id=detail[1], w=u.searchParams.get("workspace_id"); if(id==="thread-x"){const rev=++detailXRevision; if(rev===1)await sleep(500); const mark=rev===1?"STALE-X":"CURRENT-X"; return route.fulfill({status:200,contentType:"application/json",body:JSON.stringify({...summary(id,w,"Current A"),interactions:[interaction(`x-${rev}`,"<script>unsafe()</script>",mark,"confirmation_required","dispatching")],has_older:false})});} const mark=id==="thread-y"?"CURRENT-Y":"CURRENT-B"; return route.fulfill({status:200,contentType:"application/json",body:JSON.stringify({...summary(id,w,mark),interactions:[interaction(id,"safe",mark)],has_older:false})});}
const submit=p.match(/^\/ai\/threads\/([^/]+)\/interactions$/); if(submit&&method==="POST"){const body=JSON.parse(route.request().postData()||"{}"); submitCalls.push({id:submit[1],request_id:body.request_id,prompt:body.prompt,workspace:u.searchParams.get("workspace_id")}); if(body.prompt==="retry-me"&&submitCalls.filter(x=>x.prompt==="retry-me").length===1)return route.fulfill({status:503,contentType:"application/json",body:'{"detail":"transient"}'}); if(body.prompt==="slow-submit"){await new Promise(r=>{delayedSubmitResolve=r});} return route.fulfill({status:200,contentType:"application/json",body:JSON.stringify({interaction:interaction("submit","slow-submit","done")})});}
return route.fulfill({status:404,contentType:"application/json",body:'{"detail":"not mocked"}'});});
const spa=async path=>{await page.evaluate(p=>{history.pushState({},"",p); window.dispatchEvent(new PopStateEvent("popstate"));},path);};
await page.goto(`${app}/runs`,{waitUntil:"domcontentloaded"}); await page.getByRole("heading",{name:"Runs",exact:true}).waitFor(); await page.getByLabel("Workspace").selectOption("workspace-a");
await spa("/ai-threads"); await page.getByRole("heading",{name:"AI Threads",exact:true}).waitFor(); await page.getByRole("button",{name:/Current A/i}).waitFor(); ok((await page.getByText("STALE A",{exact:true}).count())===0,"stale initial list painted");
await page.getByRole("button",{name:/Current A/i}).click(); await page.getByText("CURRENT-X",{exact:true}).waitFor(); ok((await page.locator("script").filter({hasText:"unsafe()"}).count())===0,"hostile text executed"); ok((await page.getByText("<script>unsafe()</script>",{exact:true}).count())===1,"hostile text not rendered inertly"); ok((await page.getByText("confirmation_required",{exact:true}).count())===1,"canonical state missing"); ok((await page.getByText("dispatching",{exact:true}).count())===1,"persistence state missing");
await page.getByRole("button",{name:/Thread Y/i}).click(); await page.getByRole("button",{name:/Current A/i}).click(); await page.getByText("CURRENT-X",{exact:true}).waitFor(); await sleep(700); ok((await page.getByText("STALE-X",{exact:true}).count())===0,"stale X detail repainted after X→Y→X");
const textarea=page.getByLabel("Prompt"); await textarea.fill("retry-me"); await textarea.press("Enter"); await page.getByText(/durable result could not be confirmed/i).waitFor(); const firstRetry=submitCalls.find(x=>x.prompt==="retry-me").request_id; await page.getByRole("button",{name:"Submit",exact:true}).click(); await sleep(200); const retryCalls=submitCalls.filter(x=>x.prompt==="retry-me"); ok(retryCalls.length===2&&retryCalls[1].request_id===firstRetry,"unchanged retry did not reuse request id");
await textarea.fill("slow-submit"); await page.getByRole("button",{name:"Submit",exact:true}).click(); await page.getByRole("button",{name:"Submitting…",exact:true}).evaluate(el=>el.click()); await sleep(100); ok(submitCalls.filter(x=>x.prompt==="slow-submit").length===1,"in-flight duplicate submit reached backend");
await page.getByRole("button",{name:/Thread Y/i}).click(); await page.getByText("CURRENT-Y",{exact:true}).waitFor(); ok(await textarea.isEnabled(),"thread Y composer stayed disabled after stale X submit ownership was invalidated"); ok((await textarea.inputValue())==="slow-submit","thread switch unexpectedly changed prompt before stale X completion"); delayedSubmitResolve(); await sleep(400); ok((await page.getByText("done",{exact:true}).count())===0,"stale X submit repainted thread Y"); ok(await textarea.isEnabled(),"stale X completion re-locked thread Y composer"); ok((await textarea.inputValue())==="slow-submit","stale X completion changed thread Y prompt"); ok((await page.getByText(/durable result could not be confirmed/i).count())===0,"stale X completion changed thread Y error state");
await textarea.fill("slow-submit"); await page.getByRole("button",{name:"Submit",exact:true}).click(); await sleep(100); await spa("/runs"); await page.getByRole("heading",{name:"Runs",exact:true}).waitFor(); await page.getByLabel("Workspace").selectOption("workspace-b"); await spa("/ai-threads"); await page.getByRole("button",{name:/Current B/i}).waitFor(); delayedSubmitResolve(); await sleep(400); ok((await page.getByText("done",{exact:true}).count())===0,"stale A submit repainted workspace B");
await spa("/runs"); await page.getByLabel("Workspace").selectOption("workspace-a"); await spa("/ai-threads"); await page.getByRole("button",{name:/Current A/i}).waitFor(); const width=await page.evaluate(()=>[document.documentElement.scrollWidth,document.documentElement.clientWidth]); ok(width[0]<=width[1]+1,`global overflow at effective-200%-width proxy ${width}`); await textarea.focus().catch(()=>{}); ok(pageErrors.length===0,`page errors ${JSON.stringify(pageErrors)}`); ok(externalCalls.length===0,`external provider/network calls observed ${JSON.stringify(externalCalls)}`); await browser.close(); console.log("AI_THREADS_BROWSER_PROOF=PASS");'''


@pytest.mark.skipif(not RUN_PROOF, reason="temporary exact-head AI-THREADS browser proof")
def test_exact_head_ai_threads_browser_proof(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[2]
    target = tmp_path / "target"
    env = os.environ.copy()
    run(["git", "fetch", "origin", TARGET_BRANCH, "--depth=200"], root, env, 120)
    assert run(["git", "rev-parse", "FETCH_HEAD"], root, env).strip() == TARGET_SHA
    run(["git", "worktree", "add", "--detach", str(target), TARGET_SHA], root, env, 60)
    server: subprocess.Popen[str] | None = None
    try:
        for cmd in (
            ["python", "scripts/check_spec_status.py", "--self-test"],
            ["python", "scripts/check_ui_foundation.py"],
            ["python", "scripts/check_app_shell.py"],
            ["python", "scripts/check_lineage_overview.py"],
            ["python", "scripts/check_runs_workbench.py"],
            ["python", "scripts/check_engineering_data.py"],
            ["python", "scripts/check_analytics_dock.py"],
            ["python", "scripts/check_proposal_review.py"],
            ["python", "scripts/check_ai_threads.py", "--self-test"],
            ["python", "scripts/check_ai_threads.py"],
        ):
            run(cmd, target, env)
        run(["python", "-m", "pytest", "-q", "backend/tests/test_ai_threads.py", "backend/tests/test_ai_egress_schema.py", "backend/tests/test_flow_grade_schema_registry.py"], target, env, 240)
        frontend = target / "frontend"
        run(["npm", "ci"], frontend, env, 180)
        out = tmp_path / "harness"
        run([str(frontend / "node_modules/.bin/tsc"), "src/components/threads/threadState.ts", "src/components/threads/threadStateHarness.ts", "--target", "ES2022", "--module", "commonjs", "--moduleResolution", "node", "--skipLibCheck", "--outDir", str(out)], frontend, env, 120)
        run(["node", str(out / "threadStateHarness.js")], frontend, env)
        run(["npm", "run", "build"], frontend, env, 180)
        run(["npm", "install", "--no-save", "--package-lock=false", "playwright@1.54.2"], frontend, env, 180)
        run([str(frontend / "node_modules/.bin/playwright"), "install", "--with-deps", "chromium"], frontend, env, 360)
        script = frontend / ".ai-threads-proof.mjs"
        script.write_text(SCRIPT, encoding="utf-8")
        server = subprocess.Popen(["npm", "run", "dev", "--", "--host", "127.0.0.1", "--port", "5173"], cwd=frontend, env=env, text=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        wait_url("http://127.0.0.1:5173/ai-threads")
        run(["node", str(script)], frontend, env, 180)
    finally:
        if server is not None:
            server.terminate()
            try:
                server.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server.kill()
