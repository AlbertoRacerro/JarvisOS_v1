#!/usr/bin/env python3
"""Temporary 100a exact-ref metrics collector. Standard library only."""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import subprocess
from collections import Counter, defaultdict
from pathlib import PurePosixPath

SCOPE_PREFIXES = (
    "backend/app/", "backend/tests/", "frontend/src/", "frontend/tests/",
    "scripts/", ".github/workflows/",
)
ROOT_EXEC = {
    "Start-JarvisOS.cmd", "Start-JarvisOS-Backend.cmd", "Start-JarvisOS-Frontend.cmd",
    "backend/pyproject.toml", "backend/requirements.txt", "backend/requirements-dev.txt",
    "backend/pytest.ini", "frontend/package.json", "frontend/tsconfig.json",
    "frontend/vite.config.ts", "frontend/index.html",
}
SOURCE_EXT = {".py", ".ts", ".tsx", ".js", ".mjs", ".yml", ".yaml", ".cmd", ".ps1", ".vbs", ".toml", ".json", ".html", ".css"}
ROUTE_RE = re.compile(r"@(?:router|app)\.(get|post|put|delete|patch)\(\s*[\"']([^\"']+)")
EXPORT_RE = re.compile(r"\bexport\s+(?:async\s+)?(?:function|const|class)\s+([A-Za-z_$][\w$]*)")
IMPORT_RE = re.compile(r"(?:from\s+[\"'](\.[^\"']+)[\"']|import\s+[\"'](\.[^\"']+)[\"'])")

def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], text=True, encoding="utf-8", errors="replace")

def content(ref: str, path: str) -> str:
    return git("show", f"{ref}:{path}")

def area(path: str) -> str:
    for prefix, label in [
        ("backend/app/", "backend_app"), ("backend/tests/", "backend_tests"),
        ("frontend/src/", "frontend_src"), ("frontend/tests/", "frontend_tests"),
        ("scripts/", "scripts"), (".github/workflows/", "workflows")]:
        if path.startswith(prefix): return label
    return "launchers_config"

def py_module(path: str) -> str | None:
    if not path.startswith("backend/") or not path.endswith(".py"): return None
    p = path[len("backend/"):-3].replace("/", ".")
    return p[:-9] if p.endswith(".__init__") else p

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref", required=True)
    ap.add_argument("--output")
    ns = ap.parse_args()
    ref = git("rev-parse", ns.ref).strip()
    paths = git("ls-tree", "-r", "--name-only", ref).splitlines()
    scoped = [p for p in paths if p in ROOT_EXEC or any(p.startswith(x) for x in SCOPE_PREFIXES)]
    metrics: dict = {"audited_sha": ref, "definition": "physical lines and nonblank physical lines of tracked UTF-8-decodable first-party files", "areas": {}, "languages": {}, "backend_routes": [], "frontend_api_exports": [], "hotspots": {}, "exact_duplicate_groups": []}
    by_area = defaultdict(lambda: Counter(files=0, lines=0, nonblank=0, bytes=0))
    by_ext = defaultdict(lambda: Counter(files=0, lines=0, nonblank=0, bytes=0))
    texts = {}
    hashes = defaultdict(list)
    for p in scoped:
        ext = PurePosixPath(p).suffix.lower()
        if ext not in SOURCE_EXT and p not in ROOT_EXEC: continue
        try: txt = content(ref, p)
        except subprocess.CalledProcessError: continue
        texts[p] = txt
        raw = txt.encode("utf-8")
        lines = txt.splitlines()
        nb = sum(bool(x.strip()) for x in lines)
        for bucket in (by_area[area(p)], by_ext[ext or "<none>"]):
            bucket["files"] += 1; bucket["lines"] += len(lines); bucket["nonblank"] += nb; bucket["bytes"] += len(raw)
        if len(raw): hashes[hashlib.sha256(raw).hexdigest()].append(p)
        if p.startswith("backend/app/") and ext == ".py":
            for m in ROUTE_RE.finditer(txt): metrics["backend_routes"].append({"method": m.group(1).upper(), "path": m.group(2), "owner": p})
        if p.startswith("frontend/src/") and ext in {".ts", ".tsx"} and ("/api/" in p or p.endswith("api.ts") or p.endswith("client.ts")):
            for name in EXPORT_RE.findall(txt): metrics["frontend_api_exports"].append({"name": name, "owner": p})
    metrics["areas"] = {k: dict(v) for k,v in sorted(by_area.items())}
    metrics["languages"] = {k: dict(v) for k,v in sorted(by_ext.items())}
    metrics["totals"] = dict(sum((v for v in by_area.values()), Counter()))
    metrics["workflow_count"] = sum(p.startswith(".github/workflows/") and p.endswith((".yml", ".yaml")) for p in scoped)
    metrics["script_file_count"] = sum(p.startswith("scripts/") for p in scoped)
    metrics["backend_route_count"] = len(metrics["backend_routes"])
    metrics["frontend_api_export_count"] = len(metrics["frontend_api_exports"])
    metrics["exact_duplicate_groups"] = [v for v in hashes.values() if len(v) > 1]

    py_in = Counter(); py_out = Counter()
    known = {m for p in texts if (m := py_module(p))}
    for p, txt in texts.items():
        mod = py_module(p)
        if not mod: continue
        try: tree = ast.parse(txt)
        except SyntaxError: continue
        deps=set()
        for n in ast.walk(tree):
            if isinstance(n, ast.Import): deps.update(a.name for a in n.names if a.name.startswith("app"))
            elif isinstance(n, ast.ImportFrom) and n.module and n.module.startswith("app"): deps.add(n.module)
        deps={d for d in deps if d in known or any(k.startswith(d+".") for k in known)}
        py_out[mod]=len(deps)
        for d in deps: py_in[d]+=1
    metrics["hotspots"]["python_fan_in"] = py_in.most_common(20)
    metrics["hotspots"]["python_fan_out"] = py_out.most_common(20)

    ts_in=Counter(); ts_out=Counter()
    ts_paths={p for p in texts if p.startswith("frontend/src/") and PurePosixPath(p).suffix in {".ts", ".tsx"}}
    for p in ts_paths:
        deps=set(IMPORT_RE.findall(texts[p]))
        dep_count=sum(bool(a or b) for a,b in deps)
        ts_out[p]=dep_count
    metrics["hotspots"]["frontend_relative_import_fan_out"] = ts_out.most_common(20)

    payload=json.dumps(metrics, indent=2, sort_keys=True)
    print(payload)
    if ns.output:
        with open(ns.output, "w", encoding="utf-8") as fh: fh.write(payload+"\n")
if __name__ == "__main__": main()
