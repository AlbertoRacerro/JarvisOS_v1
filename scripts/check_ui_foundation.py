#!/usr/bin/env python3
from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOKENS = ROOT / "frontend/src/styles/tokens.css"
FOUNDATION = ROOT / "frontend/src/styles/foundation.css"
THEME = ROOT / "frontend/src/theme.ts"
MAIN = ROOT / "frontend/src/main.tsx"
LAYOUT = ROOT / "frontend/src/components/Layout.tsx"
STATUS = ROOT / "docs/specs/STATUS.md"
UI_DIR = ROOT / "frontend/src/components/ui"

PRIMITIVES = {"Button.tsx", "Surface.tsx", "StatusBadge.tsx", "Field.tsx", "InlineNotice.tsx"}
REQUIRED_COLORS = {
    "--color-bg-canvas", "--color-bg-shell", "--color-bg-surface", "--color-bg-surface-raised",
    "--color-bg-subtle", "--color-bg-technical-viewport", "--color-text-primary",
    "--color-text-secondary", "--color-text-muted", "--color-text-inverse",
    "--color-border-default", "--color-border-strong", "--color-accent-primary",
    "--color-accent-hover", "--color-focus-ring", "--color-status-info-bg",
    "--color-status-info-text", "--color-status-success-bg", "--color-status-success-text",
    "--color-status-warning-bg", "--color-status-warning-text", "--color-status-danger-bg",
    "--color-status-danger-text", "--color-status-neutral-bg", "--color-status-neutral-text",
    "--color-status-proposed-bg", "--color-status-proposed-text", "--color-status-stale-bg",
    "--color-status-stale-text", "--color-status-unavailable-bg", "--color-status-unavailable-text",
}
REQUIRED_NON_COLORS = {
    "--font-sans", "--font-mono", "--font-size-body", "--font-size-label", "--font-size-caption",
    "--font-size-section-title", "--font-size-page-title", "--line-height-body",
    "--control-height-compact", "--control-height-default", "--radius-sm", "--radius-md",
    "--radius-pill", "--border-width-default", "--shadow-raised", "--motion-fast",
    "--motion-standard", "--ease-standard", *{f"--space-{number}" for number in range(1, 9)},
}
APPROVED_KEY = "jarvisos:appearance:v1"
IMPLEMENTATION_PR_LINK = "[#225](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/225)"
REGISTRY_HEADER = "| Spec | Status | Implementation PR | Name | Depends on | Description |"
REGISTRY_SEPARATOR = "| --- | --- | --- | --- | --- | --- |"
HTML_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
RAW_COLOR = re.compile(
    r"(?<![\w-])(?:#[0-9a-fA-F]{3,8}\b|rgba?\(|hsla?\(|\b(?:black|white|red|blue|green|yellow|purple|orange|cyan|magenta)\b)",
    re.IGNORECASE,
)
INLINE_STYLE = re.compile(r"\bstyle\s*=\s*\{", re.IGNORECASE)
FORBIDDEN_IMPORT = re.compile(
    r"from\s+[\"'](?:\.\./)+(?:api|pages|services|router|modules|backend)(?:/|[\"'])",
    re.IGNORECASE,
)


def fail(message: str) -> None:
    print(f"ui-foundation check failed: {message}", file=sys.stderr)
    raise SystemExit(1)


def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        fail(f"missing required file: {path.relative_to(ROOT)}")


def block(css: str, selector: str) -> str:
    start = css.find(selector)
    if start < 0:
        fail(f"missing selector {selector!r}")
    brace = css.find("{", start)
    depth = 0
    for index in range(brace, len(css)):
        if css[index] == "{":
            depth += 1
        elif css[index] == "}":
            depth -= 1
            if depth == 0:
                return css[brace + 1:index]
    fail(f"unterminated selector {selector!r}")


def variables(css_block: str, prefix: str | None = None) -> set[str]:
    names = set(re.findall(r"(--[\w-]+)\s*:", css_block))
    return {name for name in names if prefix is None or name.startswith(prefix)}


def canonical_registry_row(text: str, spec_id: str) -> str:
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
        if tuple(cell.strip() for cell in row.strip("|").split("|"))[0] == spec_id
    ]
    if len(matches) != 1:
        fail(f"STATUS.md canonical Registry must contain exactly one spec {spec_id} row; found {len(matches)}")
    return matches[0]


def check_tokens() -> None:
    css = read(TOKENS)
    required = REQUIRED_COLORS | REQUIRED_NON_COLORS
    missing = sorted(required - variables(css))
    if missing:
        fail(f"missing required tokens: {', '.join(missing)}")
    for forbidden in ("bluecad", "dashboard", "settings", "ai-draft"):
        if re.search(rf"--[\w-]*{forbidden}[\w-]*\s*:", css, re.IGNORECASE):
            fail(f"page-specific token name contains {forbidden!r}")

    light = variables(block(css, ':root,\n[data-theme="light"]'), "--color-")
    dark = variables(block(css, '[data-theme="dark"]'), "--color-")
    if light != dark:
        fail(f"light/dark semantic token sets differ: light-only={sorted(light-dark)}, dark-only={sorted(dark-light)}")
    if not REQUIRED_COLORS.issubset(light):
        fail("required semantic colors are not defined in both resolved themes")


def check_theme() -> None:
    body = read(THEME)
    if 'type AppearancePreference = "system" | "light" | "dark"' not in body:
        fail("appearance enum is not exactly system/light/dark")
    if 'type ResolvedAppearance = "light" | "dark"' not in body:
        fail("resolved appearance is not limited to light/dark")
    if APPROVED_KEY not in body:
        fail("approved versioned appearance key is missing")
    string_keys = set(re.findall(r"[\"'](jarvisos:[^\"']+)[\"']", body))
    if string_keys != {APPROVED_KEY}:
        fail(f"unexpected JarvisOS storage keys: {sorted(string_keys)}")
    if "JSON.stringify" in body or "JSON.parse" in body:
        fail("appearance storage must persist only the enum, not serialized objects")
    if body.count("localStorage") != 1:
        fail("localStorage access must be centralized through one guarded acquisition")
    if "dataset.theme = resolved" not in body:
        fail("resolved data-theme assignment is missing")
    if "addEventListener(\"change\"" not in body or "removeEventListener(\"change\"" not in body:
        fail("system appearance listener cleanup is missing")


def check_primitives() -> None:
    actual = {path.name for path in UI_DIR.glob("*.tsx")}
    if actual != PRIMITIVES:
        fail(f"primitive set must be exactly {sorted(PRIMITIVES)}; found {sorted(actual)}")
    for path in sorted(UI_DIR.glob("*.tsx")):
        body = read(path)
        if FORBIDDEN_IMPORT.search(body):
            fail(f"primitive imports application authority: {path.relative_to(ROOT)}")
        if INLINE_STYLE.search(body):
            fail(f"primitive uses inline/template style: {path.relative_to(ROOT)}")
        if RAW_COLOR.search(body):
            fail(f"primitive contains a raw color literal: {path.relative_to(ROOT)}")
        if "<svg" in body.lower() or re.search(r"from\s+[\"'][^\"']+\.svg[\"']", body, re.IGNORECASE):
            fail(f"primitive contains or imports SVG markup: {path.relative_to(ROOT)}")

    consumers = "\n".join(
        read(path)
        for path in (
            LAYOUT,
            ROOT / "frontend/src/components/PageErrorBoundary.tsx",
            ROOT / "frontend/src/pages/SystemStatus.tsx",
        )
    )
    for primitive in ("Button", "Surface", "StatusBadge", "Field", "InlineNotice"):
        if not re.search(rf'import\s+{primitive}\b', consumers):
            fail(f"required primitive is defined but not consumed: {primitive}")


def check_migration() -> None:
    foundation = read(FOUNDATION)
    if RAW_COLOR.search(foundation):
        fail("foundation.css contains raw color literals")
    if "prefers-reduced-motion: reduce" not in foundation or "transition-duration: 0ms" not in foundation:
        fail("reduced-motion must disable actual transitions")

    for token in sorted(REQUIRED_COLORS | REQUIRED_NON_COLORS):
        if f"var({token})" not in foundation:
            fail(f"required token is defined but not consumed: {token}")

    for tone, marker in (("proposed", "dashed"), ("stale", "double"), ("unavailable", "dotted")):
        section = block(foundation, f".ui-status-badge--{tone}")
        if f"border-style: {marker}" not in section:
            fail(f"{tone} status lacks non-color distinction")
    synthetic = block(foundation, '.ui-status-badge--synthetic')
    if "border-radius: var(--radius-sm)" not in synthetic:
        fail("synthetic status is not geometrically distinct from unavailable")

    migrated = (
        MAIN,
        LAYOUT,
        ROOT / "frontend/src/components/PageErrorBoundary.tsx",
        ROOT / "frontend/src/pages/SystemStatus.tsx",
    )
    for path in migrated:
        body = read(path)
        if INLINE_STYLE.search(body):
            fail(f"inline/template style found in migrated file: {path.relative_to(ROOT)}")
        if RAW_COLOR.search(body):
            fail(f"raw color found in migrated file: {path.relative_to(ROOT)}")
        if "<svg" in body.lower() or re.search(r"from\s+[\"'][^\"']+\.svg[\"']", body, re.IGNORECASE):
            fail(f"SVG literal/import found in migrated file: {path.relative_to(ROOT)}")

    main = read(MAIN)
    expected_order = ["./styles/tokens.css", "./styles/global.css", "./styles/foundation.css"]
    positions = [main.find(item) for item in expected_order]
    if any(position < 0 for position in positions) or positions != sorted(positions):
        fail("token, legacy, and foundation stylesheets are not imported in the required order")
    if "applyStoredAppearance();" not in main:
        fail("stored appearance is not applied before React mount")

    if ".bluecad-viewer" not in foundation or "var(--color-bg-technical-viewport)" not in block(foundation, ".bluecad-viewer"):
        fail("BLUECAD CSS container does not consume the technical viewport token")

    evasion_samples = (
        "<div style={{ color: token }} />",
        "<div style = {{ color: token }} />",
        "<div\n  style\n  =\n  {computedStyle}\n/>",
    )
    if any(INLINE_STYLE.search(sample) is None for sample in evasion_samples):
        fail("inline-style detector does not cover whitespace/newline evasions")


def check_registry() -> None:
    row = canonical_registry_row(read(STATUS), "070")
    cells = tuple(cell.strip() for cell in row.strip().strip("|").split("|"))
    if len(cells) != 6 or cells[1] != "merged" or cells[2] != IMPLEMENTATION_PR_LINK:
        fail("spec 070 canonical registry row must be merged and contain the exact implementation PR #225 link")

    valid = f"| 070 | merged | {IMPLEMENTATION_PR_LINK} | UI-FOUNDATION-1 | 006, 082, 094 | done |"
    wrong_prefix = "[#2250](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/2250)"
    synthetic = "\n".join(
        [
            "<!--",
            f"| 070 | merged | {wrong_prefix} | decoy | — | decoy |",
            "-->",
            "## Registry",
            REGISTRY_HEADER,
            REGISTRY_SEPARATOR,
            valid,
            "",
            f"| 070 | merged | {wrong_prefix} | post-table | — | decoy |",
        ]
    )
    if canonical_registry_row(synthetic, "070") != valid:
        fail("spec 070 canonical registry parser accepts a decoy or PR-prefix collision")


def main() -> None:
    check_tokens()
    check_theme()
    check_primitives()
    check_migration()
    check_registry()
    ast.parse(read(Path(__file__)))
    print("UI foundation checks passed")


if __name__ == "__main__":
    main()
