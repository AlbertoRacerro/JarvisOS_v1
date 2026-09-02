#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import json
import sys
import tempfile
from collections import Counter
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

HTTP_MODULE_METHODS = {"get", "post", "put", "patch", "delete", "head", "options", "request", "stream"}
HTTP_CLIENT_METHODS = HTTP_MODULE_METHODS | {"send"}
REQUESTS_SESSION_METHODS = {"get", "post", "put", "patch", "delete", "head", "options", "request", "send"}
AIOHTTP_SESSION_METHODS = {"get", "post", "put", "patch", "delete", "head", "options", "request", "ws_connect"}
HTTP_CLIENT_LOW_LEVEL_METHODS = {"connect", "request", "send", "endheaders"}
URLLIB3_POOL_METHODS = {"request", "urlopen"}
SOCKET_INSTANCE_METHODS = {"connect", "connect_ex", "sendto"}
MODULE_SCOPE = (0, sys.maxsize, "<module>")


@dataclass(frozen=True, order=True)
class Finding:
    rule_id: str
    path: str
    symbol: str
    detail: str

    def render(self) -> str:
        return f"{self.rule_id} {self.path}::{self.symbol} - {self.detail}"


@dataclass(frozen=True)
class ImportFacts:
    aliases: dict[str, str]
    full_modules: frozenset[str]


def _load_config(path: Path) -> list[dict[str, str]]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid architecture config: {exc}") from exc
    if not isinstance(data, dict) or set(data) != {"exceptions"}:
        raise ValueError("config must be exactly {'exceptions': [...]}" )
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
        if path.suffix != ".py":
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=rel)
        except (OSError, SyntaxError) as exc:
            raise ValueError(f"cannot validate exception target {rel}: {exc}") from exc
        names = [
            node.name
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        ]
        count = Counter(names)[symbol]
        if count == 0:
            raise ValueError(f"stale exception symbol: {entry['exact_match']}")
        if count > 1:
            raise ValueError(f"ambiguous exception symbol: {entry['exact_match']}")


def _exception_set(config: list[dict[str, str]]) -> set[tuple[str, str]]:
    return {(e["rule_id"], e["exact_match"]) for e in config}


def _import_facts(tree: ast.AST) -> ImportFacts:
    aliases: dict[str, str] = {}
    full_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for item in node.names:
                full_modules.add(item.name)
                bound = item.asname or item.name.split(".")[0]
                aliases[bound] = item.name if item.asname else bound
        elif isinstance(node, ast.ImportFrom) and node.module:
            full_modules.add(node.module)
            for item in node.names:
                aliases[item.asname or item.name] = f"{node.module}.{item.name}"
    return ImportFacts(aliases=aliases, full_modules=frozenset(full_modules))


def _dotted(expr: ast.AST, aliases: dict[str, str]) -> str:
    if isinstance(expr, ast.Name):
        return aliases.get(expr.id, expr.id)
    if isinstance(expr, ast.Attribute):
        base = _dotted(expr.value, aliases)
        return f"{base}.{expr.attr}" if base else expr.attr
    return ""


def _root_name(expr: ast.AST) -> str | None:
    current = expr
    while isinstance(current, ast.Attribute):
        current = current.value
    return current.id if isinstance(current, ast.Name) else None


def _position(node: ast.AST) -> tuple[int, int]:
    return (getattr(node, "lineno", 0), getattr(node, "col_offset", 0))


def _call_name(node: ast.Call, aliases: dict[str, str]) -> str:
    return _dotted(node.func, aliases)


def _function_ranges(tree: ast.AST) -> list[tuple[int, int, str]]:
    ranges: list[tuple[int, int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            ranges.append((node.lineno, getattr(node, "end_lineno", node.lineno), node.name))
    return ranges


def _enclosing_scope(function_ranges: Iterable[tuple[int, int, str]], target: ast.AST) -> tuple[int, int, str]:
    best = MODULE_SCOPE
    best_span: int | None = None
    line = getattr(target, "lineno", 0)
    for start, end, name in function_ranges:
        if start <= line <= end:
            span = end - start
            if best_span is None or span < best_span:
                best, best_span = (start, end, name), span
    return best


def _enclosing_symbol(function_ranges: Iterable[tuple[int, int, str]], target: ast.AST) -> str:
    return _enclosing_scope(function_ranges, target)[2]


def _binding_kind(constructor: str) -> str | None:
    mapping = {
        "httpx.Client": "httpx_client",
        "httpx.AsyncClient": "httpx_client",
        "requests.Session": "requests_session",
        "requests.session": "requests_session",
        "urllib3.PoolManager": "urllib3_pool",
        "urllib3.ProxyManager": "urllib3_pool",
        "aiohttp.ClientSession": "aiohttp_session",
        "http.client.HTTPConnection": "http_client_connection",
        "http.client.HTTPSConnection": "http_client_connection",
        "socket.socket": "socket",
        "urllib.request.build_opener": "urllib_opener",
    }
    return mapping.get(constructor)


def _local_history_event(
    history: dict[tuple[tuple[int, int, str], str], list[tuple[tuple[int, int], str | None]]],
    scope: tuple[int, int, str],
    name: str,
    position: tuple[int, int],
) -> tuple[bool, str | None]:
    events = history.get((scope, name), [])
    previous = [(event_position, kind) for event_position, kind in events if event_position < position]
    if not previous:
        return False, None
    return True, previous[-1][1]


def _constructor_kind(
    expr: ast.AST,
    aliases: dict[str, str],
    history: dict[tuple[tuple[int, int, str], str], list[tuple[tuple[int, int], str | None]]] | None = None,
    scope: tuple[int, int, str] = MODULE_SCOPE,
    position: tuple[int, int] = (0, 0),
) -> str | None:
    if not isinstance(expr, ast.Call):
        return None
    root = _root_name(expr.func)
    if history is not None and root and scope != MODULE_SCOPE:
        locally_bound, _ = _local_history_event(history, scope, root, position)
        if locally_bound:
            return None
    return _binding_kind(_call_name(expr, aliases))


def _record_binding(
    history: dict[tuple[tuple[int, int, str], str], list[tuple[tuple[int, int], str | None]]],
    *,
    target: ast.AST | None,
    value: ast.AST | None,
    aliases: dict[str, str],
    scope: tuple[int, int, str],
    position: tuple[int, int],
) -> None:
    if not isinstance(target, ast.Name) or value is None:
        return
    history.setdefault((scope, target.id), []).append(
        (position, _constructor_kind(value, aliases, history, scope, position))
    )


def _binding_history(
    tree: ast.AST,
    aliases: dict[str, str],
    function_ranges: list[tuple[int, int, str]],
) -> dict[tuple[tuple[int, int, str], str], list[tuple[tuple[int, int], str | None]]]:
    history: dict[
        tuple[tuple[int, int, str], str], list[tuple[tuple[int, int], str | None]]
    ] = {}
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        scope = (node.lineno, getattr(node, "end_lineno", node.lineno), node.name)
        parameters = [*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs]
        if node.args.vararg is not None:
            parameters.append(node.args.vararg)
        if node.args.kwarg is not None:
            parameters.append(node.args.kwarg)
        for parameter in parameters:
            history.setdefault((scope, parameter.arg), []).append(((node.lineno, -1), None))

    for node in sorted(ast.walk(tree), key=_position):
        scope = _enclosing_scope(function_ranges, node)
        position = _position(node)
        if isinstance(node, ast.Assign):
            for target in node.targets:
                _record_binding(
                    history,
                    target=target,
                    value=node.value,
                    aliases=aliases,
                    scope=scope,
                    position=position,
                )
        elif isinstance(node, ast.AnnAssign):
            _record_binding(
                history,
                target=node.target,
                value=node.value,
                aliases=aliases,
                scope=scope,
                position=position,
            )
        elif isinstance(node, ast.NamedExpr):
            _record_binding(
                history,
                target=node.target,
                value=node.value,
                aliases=aliases,
                scope=scope,
                position=position,
            )
        elif isinstance(node, (ast.With, ast.AsyncWith)):
            for item in node.items:
                _record_binding(
                    history,
                    target=item.optional_vars,
                    value=item.context_expr,
                    aliases=aliases,
                    scope=scope,
                    position=position,
                )
    for events in history.values():
        events.sort(key=lambda event: event[0])
    return history


def _history_kind(
    history: dict[tuple[tuple[int, int, str], str], list[tuple[tuple[int, int], str | None]]],
    scope: tuple[int, int, str],
    name: str,
    position: tuple[int, int],
) -> str | None:
    locally_bound, local_kind = _local_history_event(history, scope, name, position)
    if locally_bound:
        return local_kind
    if scope != MODULE_SCOPE:
        module_bound, module_kind = _local_history_event(history, MODULE_SCOPE, name, position)
        if module_bound:
            return module_kind
    return None


def _bound_kind(
    expr: ast.AST,
    aliases: dict[str, str],
    history: dict[tuple[tuple[int, int, str], str], list[tuple[tuple[int, int], str | None]]],
    scope: tuple[int, int, str],
    position: tuple[int, int],
) -> str | None:
    if isinstance(expr, ast.Name):
        return _history_kind(history, scope, expr.id, position)
    return _constructor_kind(expr, aliases, history, scope, position)


def _is_destination_bearing_sendmsg(node: ast.Call) -> bool:
    return len(node.args) >= 4 or any(keyword.arg == "address" for keyword in node.keywords)


def _network_dispatch(
    node: ast.Call,
    aliases: dict[str, str],
    history: dict[tuple[tuple[int, int, str], str], list[tuple[tuple[int, int], str | None]]],
    scope: tuple[int, int, str],
) -> str | None:
    call = _call_name(node, aliases)
    method = call.rsplit(".", 1)[-1]
    position = _position(node)
    root = _root_name(node.func)
    root_is_shadowed = False
    if root and scope != MODULE_SCOPE:
        root_is_shadowed, _ = _local_history_event(history, scope, root, position)

    if not root_is_shadowed:
        if call.startswith(("httpx.", "requests.")) and method in HTTP_MODULE_METHODS:
            return call
        if call == "urllib.request.urlopen":
            return call
        if call == "urllib3.request":
            return call
        if call == "socket.create_connection":
            return call
        if call == "websockets.connect":
            return call
        if call == "aiohttp.request":
            return call

    if not isinstance(node.func, ast.Attribute):
        return None
    kind = _bound_kind(node.func.value, aliases, history, scope, position)
    if kind == "httpx_client" and method in HTTP_CLIENT_METHODS:
        return call or f"httpx.Client.{method}"
    if kind == "requests_session" and method in REQUESTS_SESSION_METHODS:
        return call or f"requests.Session.{method}"
    if kind == "urllib3_pool" and method in URLLIB3_POOL_METHODS:
        return call or f"urllib3.PoolManager.{method}"
    if kind == "aiohttp_session" and method in AIOHTTP_SESSION_METHODS:
        return call or f"aiohttp.ClientSession.{method}"
    if kind == "http_client_connection" and method in HTTP_CLIENT_LOW_LEVEL_METHODS:
        return call or f"http.client.HTTPConnection.{method}"
    if kind == "urllib_opener" and method == "open":
        return call or "urllib.request.OpenerDirector.open"
    if kind == "socket":
        if method in SOCKET_INSTANCE_METHODS:
            return call or f"socket.socket.{method}"
        if method == "sendmsg" and _is_destination_bearing_sendmsg(node):
            return call or "socket.socket.sendmsg"
    return None


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
    import_facts = _import_facts(tree)
    aliases = import_facts.aliases
    function_ranges = _function_ranges(tree)
    binding_history = _binding_history(tree, aliases, function_ranges)
    provider_import = any(
        target.startswith("app.modules.ai.providers")
        or target.startswith("backend.app.modules.ai.providers")
        for target in import_facts.full_modules | frozenset(aliases.values())
    )
    findings: list[Finding] = []
    mutation_calls: list[tuple[str, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        scope = _enclosing_scope(function_ranges, node)
        symbol = scope[2]
        exact = f"{rel}::{symbol}"
        call = _call_name(node, aliases)
        method = call.rsplit(".", 1)[-1]
        if method in MUTATION_WORDS:
            mutation_calls.append((symbol, call))
        if call == "sqlite3.connect" and ("AE001", exact) not in exceptions:
            findings.append(Finding("AE001", rel, symbol, f"raw SQLite connection via {call}"))
        dispatch = _network_dispatch(node, aliases, binding_history, scope)
        external = dispatch is not None or (provider_import and call.endswith(".complete"))
        accepted_external_owner = rel.startswith("backend/app/modules/ai/providers/") or rel.startswith(
            "backend/app/modules/local_ai/"
        )
        if external and not accepted_external_owner and ("AE002", exact) not in exceptions:
            findings.append(Finding("AE002", rel, symbol, f"direct external dispatch via {dispatch or call}"))
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
    symbol_tree = ast.parse(
        "outside()\n"
        "def outer():\n"
        "    first()\n"
        "    def inner():\n"
        "        second()\n"
        "    third()\n"
    )
    function_ranges = _function_ranges(symbol_tree)
    actual_symbols = {
        node.func.id: _enclosing_symbol(function_ranges, node)
        for node in ast.walk(symbol_tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    expected_symbols = {
        "outside": "<module>",
        "first": "outer",
        "second": "inner",
        "third": "outer",
    }
    if actual_symbols != expected_symbols:
        print(
            f"self-test enclosing-symbol mismatch: expected {expected_symbols}, got {actual_symbols}",
            file=sys.stderr,
        )
        return 1

    binding_tree = ast.parse(
        "import httpx\n"
        "import requests\n"
        "import aiohttp\n"
        "def bindings():\n"
        "    first = second = httpx.Client()\n"
        "    first.get('https://example.invalid')\n"
        "    second.send(req)\n"
        "    with requests.Session() as session:\n"
        "        session.post('https://example.invalid')\n"
        "    if (walrus := httpx.Client()):\n"
        "        walrus.request('GET', 'https://example.invalid')\n"
        "async def async_bindings():\n"
        "    async with aiohttp.ClientSession() as client:\n"
        "        await client.ws_connect('https://example.invalid')\n"
    )
    binding_imports = _import_facts(binding_tree).aliases
    binding_ranges = _function_ranges(binding_tree)
    binding_history = _binding_history(binding_tree, binding_imports, binding_ranges)
    dispatches = {
        _network_dispatch(
            node,
            binding_imports,
            binding_history,
            _enclosing_scope(binding_ranges, node),
        )
        for node in ast.walk(binding_tree)
        if isinstance(node, ast.Call)
    }
    expected_binding_dispatches = {
        "first.get",
        "second.send",
        "session.post",
        "walrus.request",
        "client.ws_connect",
    }
    missing_binding_dispatches = expected_binding_dispatches - dispatches
    if missing_binding_dispatches:
        print(
            f"self-test binding provenance missed {sorted(missing_binding_dispatches)}",
            file=sys.stderr,
        )
        return 1

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