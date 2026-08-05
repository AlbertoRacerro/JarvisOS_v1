#!/usr/bin/env python3
from __future__ import annotations

import ast
import json
import re
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

SHELL_DIRS = (
    FRONTEND / "app",
    FRONTEND / "components/shell",
    FRONTEND / "stages",
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
PRIMARY_LABELS = ("Home", "Design", "Runs", "Engineering Data", "Review", "Settings")
STAGE_KINDS = ("model", "results", "review", "flowsheet")
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


def check_self_cases() -> None:
    samples = {
        "raw hex": (RAW_COLOR, "color: #fff"),
        "raw rgb": (RAW_COLOR, "background: rgb(0 0 0)"),
        "inline style": (INLINE_STYLE, "<div\n style = {value} />"),
        "storage": (STORAGE, "window.localStorage.setItem('x', 'y')"),
        "external asset": (EXTERNAL_ASSET, "https://example.invalid/a.svg"),
    }
    for label, (pattern, sample) in samples.items():
        if pattern.search(sample) is None:
            fail(f"self-case detector failed for {label}")


def check_routes() -> None:
    body = read(ROUTES)
    found = set(re.findall(r'path:\s*"(/[^"]+)"', body))
    if found != PRODUCTION_PATHS | {DEV_PATH}:
        fail(f"route paths differ: missing={sorted((PRODUCTION_PATHS | {DEV_PATH}) - found)}, extra={sorted(found - (PRODUCTION_PATHS | {DEV_PATH}))}")
    if 'normalized === "/"' not in body or 'canonicalPath: "/home"' not in body or "shouldReplace: true" not in body:
        fail("root canonicalization does not replace / with /home")
    if "replace(/^\\/+|\\/+$/g" not in body:
        fail("trailing-slash normalization is missing")
    if "import.meta.env.DEV" not in body or "devOnly: true" not in body:
        fail("development route is not gated")

    for label in PRIMARY_LABELS:
        if body.count(f'label: "{label}"') != 1:
            fail(f"primary navigation label must appear exactly once: {label}")
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
    combined = "\n".join(read(path) for path in (APP, LAYOUT, FRONTEND / "components/shell/Rail.tsx", FRONTEND / "components/shell/TopBar.tsx"))
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
    if "| ready |" not in row and "| in_progress |" not in row and "| in_review |" not in row:
        fail("spec 083 registry state is not implementation-compatible")


def main() -> None:
    check_self_cases()
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
