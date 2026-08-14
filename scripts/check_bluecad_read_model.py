#!/usr/bin/env python3
from __future__ import annotations

import ast
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
READ_MODEL = ROOT / "backend/app/modules/bluecad/read_model.py"
ROUTES = ROOT / "backend/app/modules/bluecad/routes.py"
CLIENT = ROOT / "frontend/src/api/client.ts"
STATUS = ROOT / "docs/specs/STATUS.md"

ALLOWED = {
    "backend/app/modules/bluecad/models.py",
    "backend/app/modules/bluecad/ledger.py",
    "backend/app/modules/bluecad/evidence.py",
    "backend/app/modules/bluecad/read_model.py",
    "backend/app/modules/bluecad/routes.py",
    "backend/app/modules/flowsheet/freshness.py",
    "backend/tests/bluecad/test_read_model.py",
    "frontend/src/api/client.ts",
    "scripts/check_bluecad_read_model.py",
    "docs/specs/STATUS.md",
}
FORBIDDEN_MANIFEST_PARTS = (
    "package.json",
    "package-lock.json",
    "requirements",
    "pyproject.toml",
    "schema.py",
    ".github/",
)
CLIENT_SYMBOL = "getBluecadCandidateAggregate"
IMPLEMENTATION_PR_LINK = "[#236](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/236)"
REGISTRY_HEADER = "| Spec | Status | Implementation PR | Name | Depends on | Description |"
REGISTRY_SEPARATOR = "| --- | --- | --- | --- | --- | --- |"
FENCE_START = re.compile(r"^ {0,3}(`{3,}|~{3,})")
RAW_HTML_START = re.compile(r"^ {0,3}<(?P<tag>pre|script|style|textarea)(?:\s|>|$)", re.IGNORECASE)
GENERIC_HTML_TAG = re.compile(r"^ {0,3}</?[A-Za-z][A-Za-z0-9-]*(?:\s|/?>|$)")


def fail(message: str) -> None:
    print(f"BLUECAD read-model check failed: {message}", file=sys.stderr)
    raise SystemExit(1)


def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        fail(f"missing required file: {path.relative_to(ROOT)}")


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
    matches = [row for row in rows if row.startswith("| 084 |")]
    if len(matches) != 1:
        fail(f"STATUS.md canonical Registry must contain exactly one spec 084 row; found {len(matches)}")
    cells = [cell.strip() for cell in matches[0].strip().strip("|").split("|")]
    if len(cells) != 6 or cells[2] != IMPLEMENTATION_PR_LINK or cells[1] not in {"in_review", "merged"}:
        fail("spec 084 registry row must be in_review/merged with exact implementation PR #236")
    return cells[1]


def _base_sha() -> str | None:
    event_path = os.getenv("GITHUB_EVENT_PATH")
    if event_path:
        try:
            payload = json.loads(Path(event_path).read_text(encoding="utf-8"))
            base = payload.get("pull_request", {}).get("base", {}).get("sha")
            if isinstance(base, str) and re.fullmatch(r"[0-9a-f]{40}", base):
                return base
        except (OSError, json.JSONDecodeError):
            pass
    for ref in ("origin/master", "master"):
        try:
            return subprocess.check_output(
                ["git", "merge-base", "HEAD", ref],
                cwd=ROOT,
                text=True,
                stderr=subprocess.DEVNULL,
            ).strip()
        except (OSError, subprocess.CalledProcessError):
            continue
    return None


def changed_paths() -> set[str]:
    base = _base_sha()
    if base is None:
        fail("cannot resolve a merge base for the exact file-boundary check")
    try:
        output = subprocess.check_output(
            ["git", "diff", "--name-only", f"{base}...HEAD"],
            cwd=ROOT,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        fail(f"cannot inspect implementation diff: {type(exc).__name__}")
    return {line.strip().replace("\\", "/") for line in output.splitlines() if line.strip()}


def validate_changed_paths(paths: set[str]) -> None:
    unexpected = sorted(paths - ALLOWED)
    if unexpected:
        fail(f"files outside the 084 readiness boundary changed: {', '.join(unexpected)}")
    forbidden = sorted(path for path in paths if any(part in path for part in FORBIDDEN_MANIFEST_PARTS))
    if forbidden:
        fail(f"forbidden schema/package/workflow path changed: {', '.join(forbidden)}")


def check_contract() -> None:
    read_model = read(READ_MODEL)
    routes = read(ROUTES)
    client = read(CLIENT)

    tree = ast.parse(read_model)
    class_names = {node.name for node in tree.body if isinstance(node, ast.ClassDef)}
    required_classes = {
        "BluecadArtifactRefRead",
        "BluecadEvidenceRefRead",
        "BluecadRunRefRead",
        "BluecadReadDiagnostic",
        "BluecadCandidateAggregateRead",
    }
    missing = sorted(required_classes - class_names)
    if missing:
        fail(f"missing response models: {', '.join(missing)}")

    if re.search(r"^\s*stored_path\s*:", read_model, flags=re.MULTILINE):
        fail("stored_path appears in the aggregate response model")
    if "PRAGMA query_only = ON" not in read_model or 'execute("BEGIN")' not in read_model:
        fail("aggregate does not establish a query-only read transaction")
    if '"/candidates/{candidate_id}/aggregate"' not in routes:
        fail("aggregate route is missing")
    if "response_model=BluecadCandidateAggregateRead" not in routes:
        fail("aggregate route is not bound to the strict response model")
    if f"export function {CLIENT_SYMBOL}" not in client:
        fail("typed frontend aggregate client is missing")
    if "encodeURIComponent(workspaceId)" not in client or "encodeURIComponent(candidateId)" not in client:
        fail("aggregate client does not URL-encode both path segments")


def frontend_consumers(root: Path = ROOT) -> list[str]:
    consumers: list[str] = []
    src = root / "frontend/src"
    for path in src.rglob("*"):
        if not path.is_file() or path == root / "frontend/src/api/client.ts":
            continue
        if path.suffix not in {".ts", ".tsx"}:
            continue
        try:
            body = path.read_text(encoding="utf-8")
        except OSError:
            continue
        if CLIENT_SYMBOL in body:
            consumers.append(path.relative_to(root).as_posix())
    return sorted(consumers)


def check_no_ui_consumption() -> None:
    consumers = frontend_consumers()
    if consumers:
        fail(f"084 aggregate client is consumed by UI code: {', '.join(consumers)}")


def status_fixture(row: str, *, decoy: str = "") -> str:
    return "\n".join((decoy, "## Registry", "", REGISTRY_HEADER, REGISTRY_SEPARATOR, row, "", "## Next"))


def self_test() -> None:
    validate_changed_paths(set())
    validate_changed_paths({"backend/app/modules/bluecad/read_model.py", "frontend/src/api/client.ts"})
    try:
        validate_changed_paths({"frontend/src/pages/Bluecad.tsx"})
    except SystemExit:
        pass
    else:
        fail("negative self-test accepted an out-of-scope UI page change")

    merged = f"| 084 | merged | {IMPLEMENTATION_PR_LINK} | BLUECAD-READ-MODEL-1 | deps | done |"
    active = f"| 084 | in_review | {IMPLEMENTATION_PR_LINK} | BLUECAD-READ-MODEL-1 | deps | active |"
    if registry_state(status_fixture(merged)) != "merged" or registry_state(status_fixture(active)) != "in_review":
        fail("registry lifecycle detector self-test failed")
    try:
        registry_state(status_fixture("| 084 | merged | — | BLUECAD-READ-MODEL-1 | deps | wrong |"))
    except SystemExit:
        pass
    else:
        fail("registry lifecycle detector accepted wrong implementation PR")
    decoy = f"<!--\n{merged}\n-->"
    if registry_state(status_fixture(active, decoy=decoy)) != "in_review":
        fail("registry lifecycle detector accepted an HTML-comment decoy over canonical evidence")
    try:
        registry_state(status_fixture("| 083 | merged | — | OTHER | deps | no 084 |", decoy=decoy))
    except SystemExit:
        pass
    else:
        fail("registry lifecycle detector accepted a decoy when canonical 084 evidence was absent")
    fenced_decoy = "\n".join(("```markdown", "## Registry", REGISTRY_HEADER, REGISTRY_SEPARATOR, merged, "```"))
    if registry_state(status_fixture(active, decoy=fenced_decoy)) != "in_review":
        fail("registry lifecycle detector accepted a fenced decoy over canonical evidence")
    hidden_only = (
        fenced_decoy,
        "\n".join(("```markdown", "```not-a-close", "## Registry", REGISTRY_HEADER, REGISTRY_SEPARATOR, merged, "```")),
        "\n".join(("```markdown", "    ```", "## Registry", REGISTRY_HEADER, REGISTRY_SEPARATOR, merged, "```")),
        "\n".join(("<pre>", "## Registry", REGISTRY_HEADER, REGISTRY_SEPARATOR, merged, "</pre>")),
        "\n".join(("    ## Registry", "    " + REGISTRY_HEADER, "    " + REGISTRY_SEPARATOR, "    " + merged)),
        "\n".join(("<!--", "## Registry", REGISTRY_HEADER, REGISTRY_SEPARATOR, merged)),
    )
    for hidden in hidden_only:
        try:
            registry_state(hidden)
        except SystemExit:
            pass
        else:
            fail("registry lifecycle detector accepted hidden Markdown lifecycle evidence")

    import tempfile
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        (root / "frontend/src/api").mkdir(parents=True)
        (root / "frontend/src/pages").mkdir(parents=True)
        (root / "frontend/src/api/client.ts").write_text(
            f"export function {CLIENT_SYMBOL}() {{ return null; }}\n", encoding="utf-8"
        )
        (root / "frontend/src/pages/Workbench.tsx").write_text(
            f"const symbol = '{CLIENT_SYMBOL}';\n", encoding="utf-8"
        )
        if frontend_consumers(root) != ["frontend/src/pages/Workbench.tsx"]:
            fail("negative UI-consumption self-test did not detect the client symbol")


def main() -> None:
    self_test()
    state = registry_state(read(STATUS))
    if state == "in_review":
        validate_changed_paths(changed_paths())
    check_contract()
    if state == "in_review":
        check_no_ui_consumption()
    ast.parse(read(Path(__file__)))
    print("BLUECAD read-model checks passed")


if __name__ == "__main__":
    main()
