#!/usr/bin/env python3
from __future__ import annotations

import ast
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend/src"
ROUTES = FRONTEND / "app/routes.ts"
ROUTER = FRONTEND / "app/useAppRouter.ts"
APP = FRONTEND / "App.tsx"
LAYOUT = FRONTEND / "components/Layout.tsx"
MAIN = FRONTEND / "main.tsx"
SHELL_CSS = FRONTEND / "styles/shell.css"
PACKAGE = ROOT / "frontend/package.json"
STATUS = ROOT / "docs/specs/STATUS.md"
IMPLEMENTATION_BASE = "994b40009f5bf898aac7f9ba978c4925c610e505"

SHELL_DIRS = (
    FRONTEND / "app",
    FRONTEND / "components/shell",
    FRONTEND / "stages",
)
AUTHORIZED_ADDED = frozenset(
    {
        "backend/app/core/spa_static.py",
        "backend/tests/test_spa_static.py",
        "frontend/src/app/AppLink.tsx",
        "frontend/src/app/routes.ts",
        "frontend/src/app/selection.ts",
        "frontend/src/app/useAppRouter.ts",
        "frontend/src/components/shell/AnalysisDock.tsx",
        "frontend/src/components/shell/ContextualNavigator.tsx",
        "frontend/src/components/shell/ContextualSidecar.tsx",
        "frontend/src/components/shell/LegacyDiagnosticSurface.tsx",
        "frontend/src/components/shell/MigrationPendingSurface.tsx",
        "frontend/src/components/shell/Rail.tsx",
        "frontend/src/components/shell/TopBar.tsx",
        "frontend/src/stages/FlowsheetStage.tsx",
        "frontend/src/stages/ModelStage.tsx",
        "frontend/src/stages/ResultsStage.tsx",
        "frontend/src/stages/ReviewStage.tsx",
        "frontend/src/stages/registry.ts",
        "frontend/src/styles/shell.css",
        "scripts/check_app_shell.py",
    }
)
AUTHORIZED_MODIFIED = frozenset(
    {
        "backend/app/main.py",
        "docs/specs/STATUS.md",
        "frontend/src/App.tsx",
        "frontend/src/components/Layout.tsx",
        "frontend/src/main.tsx",
        "frontend/src/styles/responsive.css",
        "scripts/check_ui_foundation.py",
    }
)
PRODUCTION_PATHS = {
    "/home",
    "/design/model",
    "/design/results",
    "/design/flowsheet",
    "/runs",
    "/engineering-data",
    "/review",
    "/settings",
    "/legacy/domain-foundation",
    "/legacy/ai-draft",
    "/legacy/system-status",
}
DEV_PATH = "/legacy/dev-local-chat"
PRIMARY_ITEMS = (
    ("Home", "/home"),
    ("Design", "/design/model"),
    ("Runs", "/runs"),
    ("Engineering Data", "/engineering-data"),
    ("Review", "/review"),
    ("Settings", "/settings"),
)
STAGE_KINDS = ("model", "results", "review", "flowsheet")
REGISTRY_STATES = ("in_review", "merged")
ROUTE_PATH = re.compile(r'path\s*:\s*"(/[^"]+)"')
RAW_COLOR = re.compile(
    r"(?<![\w-])(?:#[0-9a-fA-F]{3,8}\b|rgba?\(|hsla?\(|\b(?:black|white|red|blue|green|yellow|purple|orange|cyan|magenta)\b)",
    re.IGNORECASE,
)
INLINE_STYLE = re.compile(r"\bstyle\s*=\s*\{", re.IGNORECASE)
STORAGE = re.compile(r"\b(?:localStorage|sessionStorage|indexedDB|document\.cookie)\b")
EXTERNAL_ASSET = re.compile(r"https?://", re.IGNORECASE)


def fail(message: str) -> None:
    print(f"app-shell check failed: {message}", file=sys.stderr)
    raise SystemExit(1)


def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        fail(f"missing required file: {path.relative_to(ROOT)}")


def shell_files() -> list[Path]:
    files: list[Path] = [APP, LAYOUT]
    for directory in SHELL_DIRS:
        files.extend(sorted(directory.glob("*.ts")))
        files.extend(sorted(directory.glob("*.tsx")))
    return files


def registry_row_valid(row: str) -> bool:
    has_terminal_state = any(f"| {state} |" in row for state in REGISTRY_STATES)
    return row.startswith("| 083 |") and has_terminal_state and "pull/231" in row


def parse_name_status(output: str) -> tuple[frozenset[str], frozenset[str]]:
    added: set[str] = set()
    modified: set[str] = set()
    for raw_line in output.splitlines():
        if not raw_line.strip():
            continue
        fields = raw_line.split("\t")
        status = fields[0]
        if status == "A" and len(fields) == 2:
            added.add(fields[1])
        elif status == "M" and len(fields) == 2:
            modified.add(fields[1])
        else:
            fail(f"unauthorized diff status or malformed record: {raw_line!r}")
    return frozenset(added), frozenset(modified)


def check_self_cases() -> None:
    samples = {
        "raw hex": (RAW_COLOR, "/* color: #fff */"),
        "raw rgb template": (RAW_COLOR, "const value = `rgb(${r} ${g} ${b})`;"),
        "inline style": (INLINE_STYLE, "<div\n style = {value} />"),
        "storage": (STORAGE, "window.localStorage.setItem('x', 'y')"),
        "external asset": (EXTERNAL_ASSET, "https://example.invalid/a.svg"),
    }
    for label, (pattern, sample) in samples.items():
        if pattern.search(sample) is None:
            fail(f"self-case detector failed for {label}")
    if ROUTE_PATH.findall('const route = { path : "/home" };') != ["/home"]:
        fail("route detector does not cover whitespace evasions")
    if not registry_row_valid("| 083 | in_review | [#231](https://github.com/x/y/pull/231) |"):
        fail("registry detector rejects the valid review state")
    if not registry_row_valid("| 083 | merged | [#231](https://github.com/x/y/pull/231) |"):
        fail("registry detector rejects the valid merged state")
    if registry_row_valid("| 083 | ready | [#231](https://github.com/x/y/pull/231) |"):
        fail("registry detector accepts a stale ready state")
    if registry_row_valid("| 083 | in_review | [#999](https://github.com/x/y/pull/999) |"):
        fail("registry detector accepts the wrong implementation PR")
    if registry_row_valid("| 083 | merged | [#999](https://github.com/x/y/pull/999) |"):
        fail("registry detector accepts a merged row with the wrong implementation PR")
    parsed_added, parsed_modified = parse_name_status("A\tnew.ts\nM\texisting.ts\n")
    if parsed_added != {"new.ts"} or parsed_modified != {"existing.ts"}:
        fail("name-status detector does not preserve add/modify classes")


def check_exact_file_set() -> None:
    try:
        result = subprocess.run(
            ["git", "diff", "--name-status", "--no-renames", IMPLEMENTATION_BASE, "HEAD", "--"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        fail(f"cannot verify exact implementation diff from {IMPLEMENTATION_BASE}: {exc}")
    added, modified = parse_name_status(result.stdout)
    if added != AUTHORIZED_ADDED or modified != AUTHORIZED_MODIFIED:
        fail(
            "implementation file/status set differs: "
            f"missing_added={sorted(AUTHORIZED_ADDED - added)}, extra_added={sorted(added - AUTHORIZED_ADDED)}, "
            f"missing_modified={sorted(AUTHORIZED_MODIFIED - modified)}, "
            f"extra_modified={sorted(modified - AUTHORIZED_MODIFIED)}"
        )


def check_routes() -> None:
    body = read(ROUTES)
    found = set(ROUTE_PATH.findall(body))
    expected_paths = PRODUCTION_PATHS | {DEV_PATH}
    if found != expected_paths:
        fail(f"route paths differ: missing={sorted(expected_paths - found)}, extra={sorted(found - expected_paths)}")
    if 'normalized === "/"' not in body or 'canonicalPath: "/home"' not in body or "shouldReplace: true" not in body:
        fail("root canonicalization does not replace / with /home")
    if "replace(/^\\/+|\\/+$/g" not in body:
        fail("trailing-slash normalization is missing")
    if "import.meta.env.DEV" not in body or "devOnly: true" not in body:
        fail("development route is not gated")

    start = body.find("export const PRIMARY_NAV_ITEMS")
    end = body.find("] as const", start)
    if start < 0 or end < 0:
        fail("primary navigation registry is missing")
    primary_block = body[start:end]
    pairs = tuple(re.findall(r'label\s*:\s*"([^"]+)"\s*,\s*href\s*:\s*"([^"]+)"', primary_block))
    if pairs != PRIMARY_ITEMS:
        fail(f"primary navigation differs: expected={PRIMARY_ITEMS}, found={pairs}")
    if "/legacy/" in primary_block:
        fail("legacy routes appear in primary navigation")

    for legacy in ("/legacy/domain-foundation", "/legacy/ai-draft", "/legacy/system-status"):
        if legacy not in body:
            fail(f"required legacy route missing: {legacy}")


def check_router() -> None:
    body = read(ROUTER)
    if body.count('addEventListener("popstate"') != 1 or body.count('removeEventListener("popstate"') != 1:
        fail("router must contain one popstate subscription and cleanup")
    if "window.history.pushState" not in body or "window.history.replaceState" not in body:
        fail("History API push/replace behavior is incomplete")
    if "URLSearchParams" in body or STORAGE.search(body):
        fail("router persists or interprets forbidden shell state")


def check_stage_registry() -> None:
    routes = read(ROUTES)
    expected_union = 'type StageKind = "model" | "results" | "review" | "flowsheet"'
    if expected_union not in routes:
        fail("StageKind union is not exactly model/results/review/flowsheet")

    registry = read(FRONTEND / "stages/registry.ts")
    for kind in STAGE_KINDS:
        if len(re.findall(rf"^\s*{kind}:\s*\{{", registry, re.MULTILINE)) != 1:
            fail(f"stage registry entry missing or duplicated: {kind}")
    if "Record<StageKind, StageDefinition>" not in registry:
        fail("stage registry is not exhaustively typed")

    bluecad_importers = []
    for path in shell_files():
        if re.search(r'import\s+BlueCAD\s+from\s+["\']', read(path)):
            bluecad_importers.append(path.relative_to(ROOT).as_posix())
    if bluecad_importers != ["frontend/src/stages/ModelStage.tsx"]:
        fail(f"BlueCAD must be imported only by ModelStage; found {bluecad_importers}")


def check_navigation_and_accessibility() -> None:
    combined = "\n".join(
        read(path)
        for path in (APP, LAYOUT, FRONTEND / "components/shell/Rail.tsx", FRONTEND / "components/shell/TopBar.tsx")
    )
    required = (
        "Skip to main content",
        'aria-current=',
        'aria-expanded=',
        'aria-controls=',
        'id="app-main"',
        "document.title",
        "tabIndex={-1}",
    )
    for marker in required:
        if marker not in combined:
            fail(f"accessibility marker missing: {marker}")

    legacy = read(FRONTEND / "components/shell/LegacyDiagnosticSurface.tsx")
    if "Legacy diagnostic surface" not in legacy:
        fail("legacy routes lack the exact transition label")
    for panel in ("ContextualNavigator.tsx", "ContextualSidecar.tsx", "AnalysisDock.tsx"):
        body = read(FRONTEND / "components/shell" / panel)
        if 'event.key !== "Escape"' not in body or "onKeyDown={onPanelKeyDown}" not in body:
            fail(f"focused-panel Escape behavior missing: {panel}")


def check_styles_and_modules() -> None:
    css = read(SHELL_CSS)
    if RAW_COLOR.search(css):
        fail("shell.css contains a raw color literal")
    if "minmax(0, 1fr)" not in css:
        fail("shell stage layout is not shrink-safe")
    if "var(--color-" not in css or "@media" in css:
        fail("shell.css must use 070 semantic colors and leave responsive rules in responsive.css")

    for path in shell_files():
        body = read(path)
        relative = path.relative_to(ROOT)
        if RAW_COLOR.search(body):
            fail(f"raw color found in shell module: {relative}")
        if INLINE_STYLE.search(body):
            fail(f"inline style found: {relative}")
        if "dangerouslySetInnerHTML" in body or "<svg" in body.lower():
            fail(f"unsafe HTML/SVG found: {relative}")
        if EXTERNAL_ASSET.search(body):
            fail(f"external asset URL found: {relative}")
        if STORAGE.search(body):
            fail(f"forbidden browser persistence found: {relative}")
        if re.search(r"\b(?:ollama|run_ai_task|filesystem|api[_-]?key)\b", body, re.IGNORECASE):
            fail(f"provider/tool authority string introduced: {relative}")


def check_dependencies_and_import_order() -> None:
    package = json.loads(read(PACKAGE))
    allowed_dependencies = {"react", "react-dom", "three"}
    if set(package.get("dependencies", {})) != allowed_dependencies:
        fail("frontend runtime dependency set changed")
    forbidden_names = re.compile(r"router|redux|zustand|mobx|xstate|icon|material|chakra|tailwind", re.IGNORECASE)
    all_names = set(package.get("dependencies", {})) | set(package.get("devDependencies", {}))
    unexpected = sorted(name for name in all_names if forbidden_names.search(name))
    if unexpected:
        fail(f"forbidden routing/state/icon/UI dependency found: {unexpected}")

    main = read(MAIN)
    expected = (
        "./styles/tokens.css",
        "./styles/global.css",
        "./styles/foundation.css",
        "./styles/shell.css",
        "./styles/responsive.css",
    )
    positions = [main.find(item) for item in expected]
    if any(position < 0 for position in positions) or positions != sorted(positions):
        fail("stylesheet import order is not tokens/global/foundation/shell/responsive")


def check_registry_state() -> None:
    row = next((line for line in read(STATUS).splitlines() if line.startswith("| 083 |")), "")
    if not row:
        fail("spec 083 registry row is missing")
    if not registry_row_valid(row):
        fail("spec 083 registry row must be in_review or merged and linked to implementation PR #231")


def main() -> None:
    check_self_cases()
    check_exact_file_set()
    check_routes()
    check_router()
    check_stage_registry()
    check_navigation_and_accessibility()
    check_styles_and_modules()
    check_dependencies_and_import_order()
    check_registry_state()
    ast.parse(read(Path(__file__)))
    print("APP-SHELL-1 checks passed")


if __name__ == "__main__":
    main()
