#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import json
import sys
import tempfile
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover - CI installs backend requirements first
    yaml = None

RULE_IDS = {"AE001", "AE002", "AE003", "AE004"}
PROTECTED_TABLES = {"model_specs", "assumptions", "parameters", "requirements", "simulation_runs"}
V2_MARKERS = {"JARVIS_COORD_V2", "WORKPACK", "CANDIDATE_PATCH"}
MUTATION_WORDS = {
    "create_file", "update_file", "delete_file", "create_branch", "update_ref",
    "merge_pull_request", "update_pull_request", "STATUS.md", "apply_patch",
}
SQL_EXECUTION_METHODS = {"execute", "executemany", "executescript"}
EXACT_CANONICAL_MUTATION_OWNER_FILES = {
    "backend/app/modules/modeling/project_knowledge_owner.py",
    "backend/app/modules/modeling/parameter_lifecycle.py",
}


@dataclass(frozen=True, order=True)
class Finding:
    rule_id: str
    path: str
    symbol: str
    detail: str

    def render(self) -> str:
        return f"{self.rule_id} {self.path}::{self.symbol} - {self.detail}"


def _load_config(path: Path) -> list[dict[str, str]]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid architecture config: {exc}") from exc
    if not isinstance(data, dict) or set(data) != {"exceptions"}:
        raise ValueError("config must be exactly {'exceptions': [...]}")
    entries = data["exceptions"]
    if not isinstance(entries, list):
        raise ValueError("exceptions must be a list")
    required = {"rule_id", "exact_match", "classification", "owner_or_removal_spec", "rationale"}
    seen: set[tuple[str, str]] = set()
    result: list[dict[str, str]] = []
    for raw in entries:
        if not isinstance(raw, dict) or set(raw) != required:
            raise ValueError("every exception must contain the exact required keys")
        if any(not isinstance(raw[k], str) or not raw[k].strip() for k in required):
            raise ValueError("exception values must be non-empty strings")
        if raw["rule_id"] not in RULE_IDS:
            raise ValueError(f"unknown rule id: {raw['rule_id']}")
        if any(ch in raw["exact_match"] for ch in "*?[]"):
            raise ValueError(f"wildcards are forbidden: {raw['exact_match']}")
        if "::" not in raw["exact_match"]:
            raise ValueError("exact_match must be path::symbol")
        key = (raw["rule_id"], raw["exact_match"])
        if key in seen:
            raise ValueError(f"duplicate exception: {key}")
        seen.add(key)
        result.append({k: raw[k].strip() for k in required})
    return result


def _validate_exception_targets(root: Path, config: list[dict[str, str]]) -> None:
    for entry in config:
        rel, symbol = entry["exact_match"].split("::", 1)
        path = root / rel
        if not path.is_file():
            raise ValueError(f"stale exception path: {entry['exact_match']}")
        if path.suffix == ".py":
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"), filename=rel)
            except (OSError, SyntaxError) as exc:
                raise ValueError(f"cannot validate exception target {rel}: {exc}") from exc
            names = {
                node.name
                for node in ast.walk(tree)
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
            }
            if symbol not in names:
                raise ValueError(f"stale exception symbol: {entry['exact_match']}")


def _exception_set(config: list[dict[str, str]]) -> set[tuple[str, str]]:
    return {(e["rule_id"], e["exact_match"]) for e in config}


def _aliases(tree: ast.AST) -> dict[str, str]:
    aliases: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for item in node.names:
                aliases[item.asname or item.name.split(".")[0]] = item.name
        elif isinstance(node, ast.ImportFrom) and node.module:
            for item in node.names:
                aliases[item.asname or item.name] = f"{node.module}.{item.name}"
    return aliases


def _call_name(node: ast.Call, aliases: dict[str, str]) -> str:
    def dotted(expr: ast.AST) -> str:
        if isinstance(expr, ast.Name):
            return aliases.get(expr.id, expr.id)
        if isinstance(expr, ast.Attribute):
            base = dotted(expr.value)
            return f"{base}.{expr.attr}" if base else expr.attr
        return ""

    return dotted(node.func)


def _enclosing_symbol(tree: ast.AST, target: ast.AST) -> str:
    best = "<module>"
    best_span = None
    line = getattr(target, "lineno", 0)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            end = getattr(node, "end_lineno", node.lineno)
            if node.lineno <= line <= end:
                span = end - node.lineno
                if best_span is None or span < best_span:
                    best, best_span = node.name, span
    return best


def _literal_sql(call: ast.Call) -> str | None:
    if not call.args:
        return None
    arg = call.args[0]
    if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
        return arg.value
    return None


def _mutates_protected_table(sql: str) -> bool:
    words = " ".join(sql.upper().split())
    if not any(token in words for token in ("INSERT ", "UPDATE ", "DELETE ", "REPLACE ")):
        return False
    return any(table.upper() in words for table in PROTECTED_TABLES)


def _scan_python(path: Path, root: Path, exceptions: set[tuple[str, str]]) -> list[Finding]:
    rel = path.relative_to(root).as_posix()
    try:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=rel)
    except (OSError, SyntaxError) as exc:
        return [Finding("AE001", rel, "<parse>", f"covered Python source did not parse: {exc}")]
    aliases = _aliases(tree)
    provider_import = any(
        target.startswith("app.modules.ai.providers")
        or target.startswith("backend.app.modules.ai.providers")
        for target in aliases.values()
    )
    findings: list[Finding] = []
    mutation_calls: list[tuple[str, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        symbol = _enclosing_symbol(tree, node)
        exact = f"{rel}::{symbol}"
        call = _call_name(node, aliases)
        method = call.rsplit(".", 1)[-1]
        if method in MUTATION_WORDS:
            mutation_calls.append((symbol, call))
        if call == "sqlite3.connect" and ("AE001", exact) not in exceptions:
            findings.append(Finding("AE001", rel, symbol, f"raw SQLite connection via {call}"))
        external = (
            call.startswith(("httpx.", "requests."))
            and method in {"get", "post", "put", "patch", "delete", "request", "stream"}
        ) or (provider_import and call.endswith(".complete"))
        accepted_external_owner = rel.startswith("backend/app/modules/ai/providers/") or rel.startswith(
            "backend/app/modules/local_ai/"
        )
        if external and not accepted_external_owner and ("AE002", exact) not in exceptions:
            findings.append(Finding("AE002", rel, symbol, f"direct external dispatch via {call}"))
        sql = _literal_sql(node) if method in SQL_EXECUTION_METHODS else None
        accepted_mutation_owner = rel in EXACT_CANONICAL_MUTATION_OWNER_FILES
        if (
            sql
            and _mutates_protected_table(sql)
            and not accepted_mutation_owner
            and ("AE003", exact) not in exceptions
        ):
            findings.append(Finding("AE003", rel, symbol, "direct protected canonical SQL mutation"))
    if any(marker in source for marker in V2_MARKERS) and mutation_calls:
        symbol, call = mutation_calls[0]
        findings.append(
            Finding("AE004", rel, symbol, f"V2 coordination content reaches repository mutation call {call}")
        )
    return findings


def _scan_workflow(path: Path, root: Path) -> list[Finding]:
    rel = path.relative_to(root).as_posix()
    if yaml is None:
        return [Finding("AE004", rel, "<yaml>", "PyYAML unavailable; workflow inspection fails closed")]
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return [Finding("AE004", rel, "<yaml>", f"workflow parse failed: {exc}")]
    if not isinstance(data, dict):
        return [Finding("AE004", rel, "<yaml>", "workflow root is not a mapping")]
    trigger = data.get("on", data.get(True))
    issue_comment = (
        trigger == "issue_comment"
        or (isinstance(trigger, list) and "issue_comment" in trigger)
        or (isinstance(trigger, dict) and "issue_comment" in trigger)
    )
    if issue_comment:
        return [Finding("AE004", rel, "on.issue_comment", "automatic issue_comment workflow is forbidden by 128")]
    text = path.read_text(encoding="utf-8")
    if any(marker in text for marker in V2_MARKERS) and any(word in text for word in MUTATION_WORDS):
        return [Finding("AE004", rel, "<yaml>", "workflow parses V2 coordination into mutation authority")]
    return []


def _iter_sources(root: Path) -> Iterable[Path]:
    for base in (root / "backend" / "app", root / "scripts"):
        if base.exists():
            yield from sorted(p for p in base.rglob("*.py") if p.is_file())
    workflows = root / ".github" / "workflows"
    if workflows.exists():
        yield from sorted(
            p for p in workflows.iterdir() if p.is_file() and p.suffix in {".yml", ".yaml"}
        )


def scan(root: Path, config_path: Path) -> list[Finding]:
    config = _load_config(config_path)
    _validate_exception_targets(root, config)
    exceptions = _exception_set(config)
    findings: list[Finding] = []
    for path in _iter_sources(root):
        findings.extend(
            _scan_python(path, root, exceptions) if path.suffix == ".py" else _scan_workflow(path, root)
        )
    return sorted(set(findings))


def _self_test() -> int:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "backend/app/x").mkdir(parents=True)
        (root / "scripts").mkdir()
        (root / ".github/workflows").mkdir(parents=True)
        (root / "configs").mkdir()
        (root / "configs/architecture_enforcement.json").write_text(
            '{"exceptions":[]}', encoding="utf-8"
        )
        (root / "backend/app/x/bad.py").write_text(
            "import sqlite3 as s\nimport httpx as h\ndef f(c):\n"
            "    s.connect('x')\n    h.post('https://example.invalid')\n"
            "    c.execute('UPDATE requirements SET statement = ?')\n",
            encoding="utf-8",
        )
        (root / "scripts/v2_apply.py").write_text(
            "MARKER='JARVIS_COORD_V2 CANDIDATE_PATCH'\ndef apply():\n    update_file()\n",
            encoding="utf-8",
        )
        (root / ".github/workflows/bad.yml").write_text(
            "name: bad\non:\n  issue_comment:\njobs: {}\n", encoding="utf-8"
        )
        ids = {f.rule_id for f in scan(root, root / "configs/architecture_enforcement.json")}
        if ids != RULE_IDS:
            print(f"self-test expected {sorted(RULE_IDS)}, got {sorted(ids)}", file=sys.stderr)
            return 1
    print("architecture enforcement self-test: PASS")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--config", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return _self_test()
    root = args.root.resolve()
    config = (args.config or root / "configs/architecture_enforcement.json").resolve()
    try:
        findings = scan(root, config)
    except ValueError as exc:
        print(f"ARCH_CONFIG_ERROR: {exc}", file=sys.stderr)
        return 2
    if findings:
        for finding in findings:
            print(finding.render())
        return 1
    print("architecture enforcement: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
