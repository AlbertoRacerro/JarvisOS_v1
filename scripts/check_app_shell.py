#!/usr/bin/env python3
from __future__ import annotations

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

AUTHORIZED_ADDED = frozenset({
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
})
AUTHORIZED_MODIFIED = frozenset({
    "backend/app/main.py",
    "docs/specs/STATUS.md",
    "frontend/src/App.tsx",
    "frontend/src/components/Layout.tsx",
    "frontend/src/main.tsx",
    "frontend/src/styles/responsive.css",
    "scripts/check_ui_foundation.py",
})
PRODUCTION_PATHS = {
    "/home", "/design/model", "/design/results", "/design/flowsheet", "/runs",
    "/engineering-data", "/review", "/settings", "/legacy/domain-foundation",
    "/legacy/ai-draft", "/legacy/system-status",
}
PRIMARY_ITEMS = (
    ("Home", "/home"), ("Design", "/design/model"), ("Runs", "/runs"),
    ("Engineering Data", "/engineering-data"), ("Review", "/review"), ("Settings", "/settings"),
)
ROUTE_PATH = re.compile(r'path\s*:\s*"(/[^"]+)"')
TS_COMMENT = re.compile(r"//[^\n]*|/\*.*?\*/", re.DOTALL)
FENCE_START = re.compile(r"^ {0,3}(`{3,}|~{3,})")
RAW_HTML_START = re.compile(r"^ {0,3}<(?P<tag>pre|script|style|textarea)(?:\s|>|$)", re.IGNORECASE)
GENERIC_HTML_TAG = re.compile(r"^ {0,3}</?[A-Za-z][A-Za-z0-9-]*(?:\s|/?>|$)")
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


def without_comments(body: str) -> str:
    return TS_COMMENT.sub("", body)


def shell_files() -> list[Path]:
    files = [APP, LAYOUT]
    for directory in (FRONTEND / "app", FRONTEND / "components/shell", FRONTEND / "stages"):
        files.extend(sorted(directory.glob("*.ts")))
        files.extend(sorted(directory.glob("*.tsx")))
    return files


def strip_html_comments(text: str) -> str:
    result: list[str] = []
    cursor = 0
    while cursor < len(text):
        start = text.find("<!--", cursor)
        if start < 0:
            result.append(text[cursor:])
            break
        result.append(text[cursor:start])
        end = text.find("-->", start + 4)
        if end < 0:
            break
        comment = text[start:end + 3]
        result.append("\n" * comment.count("\n"))
        cursor = end + 3
    return "".join(result)


def markdown_indent(line: str) -> tuple[int, int]:
    columns = 0
    index = 0
    while index < len(line) and line[index] in (" ", "\t"):
        if line[index] == "\t":
            columns += 4 - (columns % 4)
        else:
            columns += 1
        index += 1
    return columns, index


def registry_lines(text: str) -> list[str]:
    cleaned = strip_html_comments(text)
    result: list[str] = []
    fence_char: str | None = None
    fence_len = 0
    html_block: str | None = None
    raw_block_end: str | None = None
    blank_terminated_html = False
    for line in cleaned.splitlines():
        indent, prefix_len = markdown_indent(line)
        candidate = line[prefix_len:]
        if html_block is not None:
            if re.search(rf"</{re.escape(html_block)}\s*>", candidate, re.IGNORECASE):
                html_block = None
            continue
        if raw_block_end is not None:
            if raw_block_end in candidate:
                raw_block_end = None
            continue
        if blank_terminated_html:
            if not candidate.strip():
                blank_terminated_html = False
            continue
        if fence_char is not None:
            if indent <= 3 and len(candidate) >= fence_len and candidate == fence_char * len(candidate):
                fence_char = None
                fence_len = 0
            continue
        marker = FENCE_START.match(line)
        if marker:
            token = marker.group(1)
            fence_char = token[0]
            fence_len = len(token)
            continue
        html_marker = RAW_HTML_START.match(line)
        if html_marker:
            tag = html_marker.group("tag").lower()
            if re.search(rf"</{re.escape(tag)}\s*>", candidate[html_marker.end():], re.IGNORECASE) is None:
                html_block = tag
            continue
        if indent <= 3 and candidate.startswith("<![CDATA["):
            if "]] >".replace(" ", "") not in candidate[len("<![CDATA["):]:
                raw_block_end = "]] >".replace(" ", "")
            continue
        if indent <= 3 and candidate.startswith("<?"):
            if "?>" not in candidate[2:]:
                raw_block_end = "?>"
            continue
        if indent <= 3 and re.match(r"<![A-Z]", candidate):
            if ">" not in candidate[2:]:
                raw_block_end = ">"
            continue
        if indent <= 3 and GENERIC_HTML_TAG.match(line):
            blank_terminated_html = bool(candidate.strip())
            continue
        if indent >= 4:
            continue
        result.append(line)
    return result


def registry_state(text: str) -> str:
    lines = registry_lines(text)
    registry_headers = [index for index, line in enumerate(lines) if line.strip() == "## Registry"]
    if len(registry_headers) != 1:
        fail("STATUS.md must contain exactly one canonical Registry section")
    start = registry_headers[0] + 1
    end = next((index for index in range(start, len(lines)) if lines[index].strip().startswith("## ")), len(lines))
    section = lines[start:end]
    table_headers = [index for index, line in enumerate(section) if line.strip() == REGISTRY_HEADER]
    if len(table_headers) != 1:
        fail("STATUS.md canonical Registry must contain exactly one exact table header")
    header = table_headers[0]
    if header + 1 >= len(section) or section[header + 1].strip() != REGISTRY_SEPARATOR:
        fail("STATUS.md canonical Registry separator is missing or malformed")
    rows: list[str] = []
    for line in section[header + 2:]:
        stripped = line.strip()
        if not stripped or not stripped.startswith("|"):
            break
        rows.append(stripped)
    matches = [row for row in rows if row.startswith("| 083 |")]
    if len(matches) != 1:
        fail(f"STATUS.md canonical Registry must contain exactly one spec 083 row; found {len(matches)}")
    cells = [cell.strip() for cell in matches[0].strip().strip("|").split("|")]
    if len(cells) != 6 or cells[2] != IMPLEMENTATION_PR_LINK or cells[1] not in {"in_review", "merged"}:
        fail("spec 083 registry row must be in_review/merged with exact implementation PR #231")
    return cells[1]


def parse_name_status(output: str) -> dict[str, str]:
    records: dict[str, str] = {}
    for line in output.splitlines():
        if not line.strip():
            continue
        fields = line.split("\t")
        status = fields[0][:1]
        paths = fields[1:] if status in {"R", "C"} else fields[1:2]
        for path in paths:
            if path in records:
                fail(f"duplicate diff path: {path}")
            records[path] = status
    return records


def check_historical_active_scope() -> None:
    try:
        output = subprocess.check_output(
            ["git", "diff", "--name-status", "--no-renames", IMPLEMENTATION_BASE, "HEAD", "--"],
            cwd=ROOT, text=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        fail(f"cannot verify historical 083 implementation scope: {type(exc).__name__}")
    records = parse_name_status(output)
    added = frozenset(path for path, status in records.items() if status == "A")
    modified = frozenset(path for path, status in records.items() if status == "M")
    invalid = {path: status for path, status in records.items() if status not in {"A", "M"}}
    if invalid or added != AUTHORIZED_ADDED or modified != AUTHORIZED_MODIFIED:
        fail("active 083 implementation footprint differs from the frozen historical allow-list")


def check_routes() -> None:
    raw = read(ROUTES)
    body = without_comments(raw)
    found = set(ROUTE_PATH.findall(body))
    expected = PRODUCTION_PATHS | {"/legacy/dev-local-chat"}
    if found != expected:
        fail(f"route paths differ: missing={sorted(expected-found)}, extra={sorted(found-expected)}")
    if 'normalized === "/"' not in body or 'canonicalPath: "/home"' not in body or "shouldReplace: true" not in body:
        fail("root canonicalization contract regressed")
    if 'pathOnly.startsWith("//")' not in raw or "replace(/\\/+$/g" not in body or "replace(/^\\/+|\\/+$/g" in body:
        fail("route normalizer contract regressed")
    if "import.meta.env.DEV" not in body or "devOnly: true" not in body:
        fail("development-only local-chat route gating regressed")
    start = body.find("export const PRIMARY_NAV_ITEMS")
    end = body.find("] as const", start)
    if start < 0 or end < 0:
        fail("primary navigation registry is missing")
    pairs = tuple(re.findall(r'label\s*:\s*"([^"]+)"\s*,\s*href\s*:\s*"([^"]+)"', body[start:end]))
    if pairs != PRIMARY_ITEMS:
        fail("primary navigation contract regressed")
    if "/legacy/" in body[start:end]:
        fail("legacy routes leaked into primary navigation")


def check_router() -> None:
    body = without_comments(read(ROUTER))
    if body.count('addEventListener("popstate"') != 1 or body.count('removeEventListener("popstate"') != 1:
        fail("router popstate subscription/cleanup regressed")
    if "window.history.pushState" not in body or "window.history.replaceState" not in body:
        fail("History API push/replace contract regressed")
    if "URLSearchParams" in body or STORAGE.search(body):
        fail("router introduced forbidden persisted/interpreted shell state")


def check_stage_registry(state: str) -> None:
    routes = without_comments(read(ROUTES))
    if 'type StageKind = "model" | "results" | "review" | "flowsheet"' not in routes:
        fail("StageKind contract regressed")
    registry = without_comments(read(FRONTEND / "stages/registry.ts"))
    for kind in ("model", "results", "review", "flowsheet"):
        if len(re.findall(rf"^\s*{kind}:\s*\{{", registry, re.MULTILINE)) != 1:
            fail(f"stage registry entry missing or duplicated: {kind}")
    if "Record<StageKind, StageDefinition>" not in registry:
        fail("stage registry is not exhaustively typed")

    model = without_comments(read(FRONTEND / "stages/ModelStage.tsx"))
    if state == "in_review":
        if 'from "../pages/BlueCAD"' not in model or "<BlueCAD" not in model:
            fail("active historical 083 context lost the compatibility-mounted BLUECAD contract")
    elif "ModelStage" not in model:
        fail("merged 083 ModelStage contract is missing")


def check_accessibility() -> None:
    combined = "\n".join(without_comments(read(path)) for path in (
        APP, LAYOUT, FRONTEND / "components/shell/Rail.tsx", FRONTEND / "components/shell/TopBar.tsx"
    ))
    for marker in ("Skip to main content", "aria-current=", "aria-expanded=", "aria-controls=", 'id="app-main"', "document.title", "tabIndex={-1}"):
        if marker not in combined:
            fail(f"accessibility contract marker missing: {marker}")
    legacy = without_comments(read(FRONTEND / "components/shell/LegacyDiagnosticSurface.tsx"))
    if "Legacy diagnostic surface" not in legacy:
        fail("legacy diagnostic transition label regressed")
    for panel in ("ContextualNavigator.tsx", "ContextualSidecar.tsx", "AnalysisDock.tsx"):
        body = without_comments(read(FRONTEND / "components/shell" / panel))
        escape_guard = 'event.key !== "Escape"' in body or 'event.key === "Escape"' in body
        if not escape_guard or "onKeyDown={onPanelKeyDown}" not in body:
            fail(f"focused-panel Escape behavior regressed: {panel}")


def check_shell_modules() -> None:
    css = read(SHELL_CSS)
    if RAW_COLOR.search(css):
        fail("shell.css contains raw color literals")
    if "minmax(0, 1fr)" not in css or "var(--color-" not in css or "@media" in css:
        fail("shell shrink-safe/token/responsive separation contract regressed")
    for path in shell_files():
        body = read(path)
        relative = path.relative_to(ROOT)
        if RAW_COLOR.search(body):
            fail(f"raw color found in shell module: {relative}")
        if INLINE_STYLE.search(body):
            fail(f"inline style found in shell module: {relative}")
        if "dangerouslySetInnerHTML" in body or "<svg" in body.lower():
            fail(f"unsafe HTML/SVG found in shell module: {relative}")
        if EXTERNAL_ASSET.search(body):
            fail(f"external asset URL found in shell module: {relative}")
        if STORAGE.search(body):
            fail(f"forbidden browser persistence found in shell module: {relative}")
        if RAW_INTERNAL_ANCHOR.search(body):
            fail(f"raw internal anchor bypasses AppLink: {relative}")
        if re.search(r"\b(?:ollama|run_ai_task|filesystem|api[_-]?key)\b", body, re.IGNORECASE):
            fail(f"provider/tool authority string introduced: {relative}")


def check_dependencies() -> None:
    package = json.loads(read(PACKAGE))
    if set(package.get("dependencies", {})) != {"react", "react-dom", "three"}:
        fail("frontend runtime dependency set changed")
    forbidden = re.compile(r"router|redux|zustand|mobx|xstate|icon|material|chakra|tailwind", re.IGNORECASE)
    names = set(package.get("dependencies", {})) | set(package.get("devDependencies", {}))
    unexpected = sorted(name for name in names if forbidden.search(name))
    if unexpected:
        fail(f"forbidden routing/state/icon/UI dependency found: {unexpected}")
    main = read(MAIN)
    expected = ("./styles/tokens.css", "./styles/global.css", "./styles/foundation.css", "./styles/shell.css", "./styles/responsive.css")
    positions = [main.find(item) for item in expected]
    if any(position < 0 for position in positions) or positions != sorted(positions):
        fail("stylesheet import order regressed")


def status_fixture(row: str, *, decoy: str = "") -> str:
    return "\n".join((decoy, "## Registry", "", REGISTRY_HEADER, REGISTRY_SEPARATOR, row, "", "## Next"))


def self_test() -> None:
    valid_merged = f"| 083 | merged | {IMPLEMENTATION_PR_LINK} | APP-SHELL-1 | 006, 070 | done |"
    valid_active = f"| 083 | in_review | {IMPLEMENTATION_PR_LINK} | APP-SHELL-1 | 006, 070 | active |"
    if registry_state(status_fixture(valid_merged)) != "merged" or registry_state(status_fixture(valid_active)) != "in_review":
        fail("registry lifecycle self-test failed")
    for invalid in (
        "| 083 | merged | — | APP-SHELL-1 | 006, 070 | wrong |",
        f"| 083 | ready | {IMPLEMENTATION_PR_LINK} | APP-SHELL-1 | 006, 070 | wrong |",
    ):
        try:
            registry_state(status_fixture(invalid))
        except SystemExit:
            pass
        else:
            fail("registry parser accepted invalid lifecycle evidence")
    decoy = f"<!--\n{valid_merged}\n-->"
    if registry_state(status_fixture(valid_active, decoy=decoy)) != "in_review":
        fail("registry parser accepted an HTML-comment decoy over canonical evidence")
    fenced_decoy = "```markdown\n" + status_fixture(valid_merged) + "\n```"
    if registry_state(status_fixture(valid_active, decoy=fenced_decoy)) != "in_review":
        fail("registry parser accepted a fenced Registry decoy over canonical evidence")
    hidden_only = (
        fenced_decoy,
        "```markdown\n    ```\n" + status_fixture(valid_merged) + "\n```",
        "\n".join(("<pre>", "## Registry", REGISTRY_HEADER, REGISTRY_SEPARATOR, valid_merged, "</pre>")),
        "\n".join(("    ## Registry", "    " + REGISTRY_HEADER, "    " + REGISTRY_SEPARATOR, "    " + valid_merged)),
        "\n".join(("<!--", "## Registry", REGISTRY_HEADER, REGISTRY_SEPARATOR, valid_merged)),
    )
    for hidden in hidden_only:
        try:
            registry_state(hidden)
        except SystemExit:
            pass
        else:
            fail("registry parser accepted hidden Markdown lifecycle evidence")
    try:
        registry_state(status_fixture("| 084 | merged | — | OTHER | — | no 083 |", decoy=decoy))
    except SystemExit:
        pass
    else:
        fail("registry parser accepted a decoy when canonical 083 evidence was absent")
    parsed = parse_name_status("A\tnew.ts\nM\texisting.ts\n")
    if parsed != {"new.ts": "A", "existing.ts": "M"}:
        fail("name-status parser self-test failed")
    for pattern, sample in (
        (RAW_COLOR, "#fff"), (INLINE_STYLE, "style = {value}"), (STORAGE, "localStorage"),
        (EXTERNAL_ASSET, "https://example.invalid/a.svg"), (RAW_INTERNAL_ANCHOR, '<a href="/runs">'),
    ):
        if pattern.search(sample) is None:
            fail("shell invariant detector self-test failed")


def main() -> None:
    self_test()
    state = registry_state(read(STATUS))
    if state == "in_review":
        check_historical_active_scope()
    check_routes()
    check_router()
    check_stage_registry(state)
    check_accessibility()
    check_shell_modules()
    check_dependencies()
    print("APP-SHELL-1 checks passed")


if __name__ == "__main__":
    main()
