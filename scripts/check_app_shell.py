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
IMPLEMENTATION_PR_LINK = "[#231](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/231)"
REGISTRY_HEADER = "| Spec | Status | Implementation PR | Name | Depends on | Description |"
REGISTRY_SEPARATOR = "| --- | --- | --- | --- | --- | --- |"

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
TS_COMMENT = re.compile(r"//[^\n]*|/\*.*?\*/", re.DOTALL)
HTML_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
RAW_COLOR = re.compile(
    r"(?<![\w-])(?:#[0-9a-fA-F]{3,8}\b|rgba?\(|hsla?\(|\b(?:black|white|red|blue|green|yellow|purple|orange|cyan|magenta)\b)",
    re.IGNORECASE,
)
INLINE_STYLE = re.compile(r"\bstyle\s*=\s*\{", re.IGNORECASE)
STORAGE = re.compile(r"\b(?:localStorage|sessionStorage|indexedDB|document\.cookie)\b")
EXTERNAL_ASSET = re.compile(r"https?://", re.IGNORECASE)
RAW_INTERNAL_ANCHOR = re.compile(r"<a\b[^>]*\bhref\s*=\s*[\"']/", re.IGNORECASE | re.DOTALL)


def fail(message: str) -> None:
    print(f"app-shell check failed: {message}", file=sys.stderr)
    raise SystemExit(1)


def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        fail(f"missing required file: {path.relative_to(ROOT)}")


def without_ts_comments(body: str) -> str:
    return TS_COMMENT.sub("", body)


def shell_files() -> list[Path]:
    files: list[Path] = [APP, LAYOUT]
    for directory in SHELL_DIRS:
        files.extend(sorted(directory.glob("*.ts")))
        files.extend(sorted(directory.glob("*.tsx")))
    return files


def registry_row_state(row: str) -> str | None:
    cells = tuple(cell.strip() for cell in row.strip().strip("|").split("|"))
    if (
        len(cells) == 6
        and cells[0] == "083"
        and cells[1] in REGISTRY_STATES
        and cells[2] == IMPLEMENTATION_PR_LINK
    ):
        return cells[1]
    return None


def registry_row_valid(row: str) -> bool:
    return registry_row_state(row) is not None


def canonical_registry_row(text: str) -> str:
    lines = HTML_COMMENT.sub("", text).splitlines()
    registry_headers = [index for index, line in enumerate(lines) if line.strip() == "## Registry"]
    if len(registry_headers) != 1:
        fail("STATUS.md must contain exactly one canonical Registry section")

    section_start = registry_headers[0] + 1
    section_end = next(
        (
            index
            for index in range(section_start, len(lines))
            if lines[index].strip().startswith("## ")
        ),
        len(lines),
    )
    section = lines[section_start:section_end]
    header_indexes = [index for index, line in enumerate(section) if line.strip() == REGISTRY_HEADER]
    if len(header_indexes) != 1:
        fail("STATUS.md canonical Registry must contain exactly one exact table header")

    header_index = header_indexes[0]
    if header_index + 1 >= len(section) or section[header_index + 1].strip() != REGISTRY_SEPARATOR:
        fail("STATUS.md canonical Registry separator is missing or malformed")

    rows: list[str] = []
    for line in section[header_index + 2 :]:
        stripped = line.strip()
        if not stripped or not stripped.startswith("|"):
            break
        rows.append(stripped)

    matches = [
        row
        for row in rows
        if tuple(cell.strip() for cell in row.strip("|").split("|"))[0] == "083"
    ]
    if len(matches) != 1:
        fail(f"STATUS.md canonical Registry must contain exactly one spec 083 row; found {len(matches)}")
    return matches[0]


def parse_name_status(output: str) -> dict[str, str]:
    records: dict[str, str] = {}
    for raw_line in output.splitlines():
        if not raw_line.strip():
            continue
        fields = raw_line.split("\t")
        status = fields[0][:1]
        if len(fields) == 2:
            paths = fields[1:]
        elif len(fields) == 3 and status in {"R", "C"}:
            paths = fields[1:]
        else:
            fail(f"malformed diff record: {raw_line!r}")
        for path in paths:
            if path in records:
                fail(f"duplicate diff path: {path!r}")
            records[path] = status
    return records


def check_self_cases() -> None:
    samples = {
        "raw hex": (RAW_COLOR, "/* color: #fff */"),
        "raw rgb template": (RAW_COLOR, "const value = `rgb(${r} ${g} ${b})`;"),
        "inline style": (INLINE_STYLE, "<div\n style = {value} />"),
        "storage": (STORAGE, "window.localStorage.setItem('x', 'y')"),
        "external asset": (EXTERNAL_ASSET, "https://example.invalid/a.svg"),
        "raw internal anchor": (RAW_INTERNAL_ANCHOR, '<a className="x" href="/runs">Runs</a>'),
    }
    for label, (pattern, sample) in samples.items():
        if pattern.search(sample) is None:
            fail(f"self-case detector failed for {label}")
    if ROUTE_PATH.findall('const route = { path : "/home" };') != ["/home"]:
        fail("route detector does not cover whitespace evasions")
    comment_only_routes = '// path: "/home"\n/* path: "/design/model" */'
    if ROUTE_PATH.findall(without_ts_comments(comment_only_routes)):
        fail("route detector accepts commented-out route evidence")
    valid_review = f"| 083 | in_review | {IMPLEMENTATION_PR_LINK} | APP-SHELL-1 | 006, 070 | active |"
    valid_merged = f"| 083 | merged | {IMPLEMENTATION_PR_LINK} | APP-SHELL-1 | 006, 070 | done |"
    if registry_row_state(valid_review) != "in_review":
        fail("registry detector rejects the valid review state")
    if registry_row_state(valid_merged) != "merged":
        fail("registry detector rejects the valid merged state")
    if registry_row_valid(f"| 083 | ready | {IMPLEMENTATION_PR_LINK} | APP-SHELL-1 | 006, 070 | stale |"):
        fail("registry detector accepts a stale ready state")
    wrong_pr = "[#999](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/999)"
    if registry_row_valid(f"| 083 | in_review | {wrong_pr} | APP-SHELL-1 | 006, 070 | wrong |"):
        fail("registry detector accepts the wrong implementation PR")
    prefix_collision = "[#2310](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/2310)"
    if registry_row_valid(f"| 083 | merged | {prefix_collision} | APP-SHELL-1 | 006, 070 | wrong |"):
        fail("registry detector accepts an implementation PR prefix collision")
    if registry_row_valid(f"| 083 | in_review | — | APP-SHELL-1 | 006, 070 | mentions {IMPLEMENTATION_PR_LINK} only here |"):
        fail("registry detector accepts the PR link outside the implementation-PR column")
    decoy_status = "\n".join(
        [
            "<!--",
            valid_merged,
            "-->",
            "```text",
            valid_merged,
            "```",
            "## Registry",
            REGISTRY_HEADER,
            REGISTRY_SEPARATOR,
            valid_review,
            "",
            valid_merged,
        ]
    )
    if canonical_registry_row(decoy_status) != valid_review:
        fail("canonical registry parser accepts a pre-registry or post-table decoy row")
    parsed = parse_name_status("A\tnew.ts\nM\texisting.ts\nD\tlater.ts\n")
    if parsed != {"new.ts": "A", "existing.ts": "M", "later.ts": "D"}:
        fail("name-status detector does not preserve change classes")


def check_exact_file_set(registry_state: str) -> None:
    try:
        result = subprocess.run(
            ["git", "diff", "--name-status", "--no-renames", IMPLEMENTATION_BASE, "HEAD", "--"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        fail(f"cannot verify implementation diff from {IMPLEMENTATION_BASE}: {exc}")
    records = parse_name_status(result.stdout)
    expected = {path: "A" for path in AUTHORIZED_ADDED} | {path: "M" for path in AUTHORIZED_MODIFIED}

    if registry_state == "in_review":
        unexpected_status = {path: status for path, status in records.items() if status not in {"A", "M"}}
        added = frozenset(path for path, status in records.items() if status == "A")
        modified = frozenset(path for path, status in records.items() if status == "M")
        if unexpected_status or added != AUTHORIZED_ADDED or modified != AUTHORIZED_MODIFIED:
            fail(
                "active implementation file/status set differs: "
                f"unexpected_status={unexpected_status}, "
                f"missing_added={sorted(AUTHORIZED_ADDED - added)}, extra_added={sorted(added - AUTHORIZED_ADDED)}, "
                f"missing_modified={sorted(AUTHORIZED_MODIFIED - modified)}, "
                f"extra_modified={sorted(modified - AUTHORIZED_MODIFIED)}"
            )
        return

    mismatched = {
        path: {"expected": status, "actual": records.get(path)}
        for path, status in expected.items()
        if records.get(path) != status
    }
    if mismatched:
        fail(f"merged implementation footprint drifted: {mismatched}")


def check_routes() -> None:
    body = without_ts_comments(read(ROUTES))
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
    body = without_ts_comments(read(ROUTER))
    if body.count('addEventListener("popstate"') != 1 or body.count('removeEventListener("popstate"') != 1:
        fail("router must contain one popstate subscription and cleanup")
    if "window.history.pushState" not in body or "window.history.replaceState" not in body:
        fail("History API push/replace behavior is incomplete")
    if "URLSearchParams" in body or STORAGE.search(body):
        fail("router persists or interprets forbidden shell state")


def check_stage_registry() -> None:
    routes = without_ts_comments(read(ROUTES))
    expected_union = 'type StageKind = "model" | "results" | "review" | "flowsheet"'
    if expected_union not in routes:
        fail("StageKind union is not exactly model/results/review/flowsheet")

    registry = without_ts_comments(read(FRONTEND / "stages/registry.ts"))
    for kind in STAGE_KINDS:
        if len(re.findall(rf"^\s*{kind}:\s*\{{", registry, re.MULTILINE)) != 1:
            fail(f"stage registry entry missing or duplicated: {kind}")
    if "Record<StageKind, StageDefinition>" not in registry:
        fail("stage registry is not exhaustively typed")

    bluecad_importers = []
    for path in shell_files():
        if re.search(r'import\s+BlueCAD\s+from\s+["\']', without_ts_comments(read(path))):
            bluecad_importers.append(path.relative_to(ROOT).as_posix())
    if bluecad_importers != ["frontend/src/stages/ModelStage.tsx"]:
        fail(f"BlueCAD must be imported only by ModelStage; found {bluecad_importers}")


def check_navigation_and_accessibility() -> None:
    combined = "\n".join(
        without_ts_comments(read(path))
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

    legacy = without_ts_comments(read(FRONTEND / "components/shell/LegacyDiagnosticSurface.tsx"))
    if "Legacy diagnostic surface" not in legacy:
        fail("legacy routes lack the exact transition label")
    for panel in ("ContextualNavigator.tsx", "ContextualSidecar.tsx", "AnalysisDock.tsx"):
        body = without_ts_comments(read(FRONTEND / "components/shell" / panel))
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
        if RAW_INTERNAL_ANCHOR.search(body):
            fail(f"raw internal anchor bypasses AppLink: {relative}")
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

    main = without_ts_comments(read(MAIN))
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


def check_registry_state() -> str:
    row = canonical_registry_row(read(STATUS))
    registry_state = registry_row_state(row)
    if registry_state is None:
        fail("spec 083 canonical registry row must be in_review or merged with exact implementation PR #231")
    return registry_state


def main() -> None:
    check_self_cases()
    registry_state = check_registry_state()
    check_exact_file_set(registry_state)
    check_routes()
    check_router()
    check_stage_registry()
    check_navigation_and_accessibility()
    check_styles_and_modules()
    check_dependencies_and_import_order()
    ast.parse(read(Path(__file__)))
    print("APP-SHELL-1 checks passed")


if __name__ == "__main__":
    main()
