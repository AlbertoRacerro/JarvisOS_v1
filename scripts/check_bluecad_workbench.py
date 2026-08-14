#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend/src"
MODEL_STAGE = FRONTEND / "stages/ModelStage.tsx"
WORKBENCH = FRONTEND / "components/bluecad/BluecadWorkbench.tsx"
STATE = FRONTEND / "components/bluecad/workbenchState.ts"
HARNESS = FRONTEND / "components/bluecad/workbenchStateHarness.ts"
VIEWER = FRONTEND / "components/BluecadGlbViewer.tsx"
STATUS = ROOT / "docs/specs/STATUS.md"
EXPECTED_PR = "[#239](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/239)"
REGISTRY_HEADER = "| Spec | Status | Implementation PR | Name | Depends on | Description |"
REGISTRY_SEPARATOR = "| --- | --- | --- | --- | --- | --- |"
FENCE_START = re.compile(r"^ {0,3}(`{3,}|~{3,})")

ALLOWED = {
    "frontend/src/App.tsx",
    "frontend/src/stages/registry.ts",
    "frontend/src/stages/ModelStage.tsx",
    "frontend/src/pages/BlueCAD.tsx",
    "frontend/src/components/Layout.tsx",
    "frontend/src/components/BluecadGlbViewer.tsx",
    "frontend/src/components/shell/ContextualNavigator.tsx",
    "frontend/src/components/shell/ContextualSidecar.tsx",
    "frontend/src/components/shell/AnalysisDock.tsx",
    "frontend/src/components/bluecad/BluecadWorkbench.tsx",
    "frontend/src/components/bluecad/BluecadNavigator.tsx",
    "frontend/src/components/bluecad/BluecadSidecar.tsx",
    "frontend/src/components/bluecad/BluecadAnalysisDock.tsx",
    "frontend/src/components/bluecad/workbenchState.ts",
    "frontend/src/components/bluecad/workbenchStateHarness.ts",
    "frontend/src/api/client.ts",
    "frontend/src/styles/global.css",
    "scripts/check_app_shell.py",
    "scripts/check_bluecad_read_model.py",
    "scripts/check_bluecad_workbench.py",
    "docs/specs/STATUS.md",
}
UI_AUTHORITY_PATHS = tuple(
    ROOT / path
    for path in sorted(ALLOWED)
    if path.startswith("frontend/src/")
    and path.endswith((".ts", ".tsx"))
    and path != "frontend/src/api/client.ts"
)

FAKE_TELEMETRY = re.compile(
    r"(?:AI\s+confidence|system\s+health|CPU\s*%|GPU\s*%|memory\s*%|stress\s*[:=]|186\.4\s*MPa|87%\s*validation)",
    re.IGNORECASE,
)
FORBIDDEN_AUTHORITY = re.compile(r"(?:stored_path|JARVISOS_DATA_ROOT|filesystem|api[_-]?key|run_ai_task)", re.IGNORECASE)


def fail(message: str) -> None:
    print(f"BLUECAD workbench check failed: {message}", file=sys.stderr)
    raise SystemExit(1)


def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        fail(f"missing required file: {path.relative_to(ROOT)}")


def changed_paths() -> set[str]:
    event_path = __import__("os").environ.get("GITHUB_EVENT_PATH")
    base: str | None = None
    if event_path:
        import json
        try:
            payload = json.loads(Path(event_path).read_text(encoding="utf-8"))
            candidate = payload.get("pull_request", {}).get("base", {}).get("sha")
            if isinstance(candidate, str) and re.fullmatch(r"[0-9a-f]{40}", candidate):
                base = candidate
        except (OSError, json.JSONDecodeError):
            pass
    if base is None:
        for ref in ("origin/master", "master"):
            try:
                base = subprocess.check_output(
                    ["git", "merge-base", "HEAD", ref], cwd=ROOT, text=True, stderr=subprocess.DEVNULL
                ).strip()
                break
            except (OSError, subprocess.CalledProcessError):
                continue
    if base is None:
        fail("cannot resolve PR/base merge point")
    try:
        output = subprocess.check_output(["git", "diff", "--name-only", f"{base}...HEAD"], cwd=ROOT, text=True)
    except (OSError, subprocess.CalledProcessError) as exc:
        fail(f"cannot inspect diff: {type(exc).__name__}")
    return {line.strip().replace("\\", "/") for line in output.splitlines() if line.strip()}


def validate_scope(paths: set[str]) -> None:
    unexpected = sorted(paths - ALLOWED)
    if unexpected:
        fail(f"files outside 085 readiness boundary changed: {', '.join(unexpected)}")
    forbidden = sorted(
        path for path in paths
        if path.startswith("backend/")
        or path.startswith(".github/")
        or path.endswith("package.json")
        or path.endswith("package-lock.json")
        or "migration" in path.lower()
    )
    if forbidden:
        fail(f"forbidden backend/dependency/workflow/schema surface changed: {', '.join(forbidden)}")


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


def registry_lines(text: str) -> list[str]:
    cleaned = strip_html_comments(text)
    result: list[str] = []
    fence_char: str | None = None
    fence_len = 0
    for line in cleaned.splitlines():
        indent = len(line) - len(line.lstrip(" "))
        candidate = line[indent:]
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
        result.append(line)
    return result


def registry_row(text: str) -> str:
    lines = registry_lines(text)
    registry_headers = [index for index, line in enumerate(lines) if line.strip() == "## Registry"]
    if len(registry_headers) != 1:
        fail("STATUS.md must contain exactly one canonical Registry section")
    start = registry_headers[0] + 1
    end = next((index for index in range(start, len(lines)) if lines[index].strip().startswith("## ")), len(lines))
    section = lines[start:end]
    table_headers = [index for index, line in enumerate(section) if line.strip() == REGISTRY_HEADER]
    if len(table_headers) != 1:
        fail("canonical Registry must contain exactly one exact table header")
    header = table_headers[0]
    if header + 1 >= len(section) or section[header + 1].strip() != REGISTRY_SEPARATOR:
        fail("canonical Registry separator is missing or malformed")
    rows: list[str] = []
    for line in section[header + 2:]:
        stripped = line.strip()
        if not stripped or not stripped.startswith("|"):
            break
        rows.append(stripped)
    matches = [row for row in rows if row.startswith("| 085 |")]
    if len(matches) != 1:
        fail(f"canonical Registry must contain exactly one spec 085 row; found {len(matches)}")
    return matches[0]


def check_registry_text(status: str) -> None:
    row = registry_row(status)
    cells = [cell.strip() for cell in row.strip("|").split("|")]
    if len(cells) != 6 or cells[1] != "in_review" or cells[2] != EXPECTED_PR:
        fail("spec 085 must be in_review with implementation PR #239")


def check_registry() -> None:
    check_registry_text(read(STATUS))


def check_primary_composition() -> None:
    model = read(MODEL_STAGE)
    if 'from "../pages/BlueCAD"' in model or "<BlueCAD" in model:
        fail("ModelStage still compatibility-mounts the legacy stacked BlueCAD page")
    if 'from "../components/bluecad/BluecadWorkbench"' not in model or "<BluecadWorkbench" not in model:
        fail("ModelStage does not mount the native BLUECAD workbench")


def check_state_authority() -> None:
    workbench = read(WORKBENCH)
    state = read(STATE)
    harness = read(HARNESS)
    if "getBluecadCandidateAggregate" not in workbench:
        fail("visible workbench does not consume the 084 aggregate")
    if 'resource: "bluecad-candidate"' not in workbench:
        fail("candidate selection does not publish the typed BLUECAD RecordRef")
    if ">Refresh<" not in workbench and '"Refresh"' not in workbench:
        fail("explicit manual Refresh action is missing")
    required_exports = ("acceptsRequest", "acceptsMutation", "revalidateSelection", "mutationConflicts", "duplicateBrief")
    for symbol in required_exports:
        if f"export function {symbol}" not in state:
            fail(f"production state helper is missing {symbol}")
        if symbol not in harness:
            fail(f"state harness does not exercise/import {symbol}")
        if symbol not in workbench:
            fail(f"workbench does not delegate {symbol} decisions to production state helper")
    if './workbenchState' not in harness:
        fail("state harness does not import the production helper")


def check_viewer_cleanup() -> None:
    viewer = read(VIEWER)
    markers = (
        "disposeOwnedScene",
        "object.geometry?.dispose()",
        "material.dispose()",
        "value instanceof THREE.Texture",
        "if (disposed)",
        "disposeOwnedScene(gltf.scene)",
        "controls.dispose()",
        "renderer.dispose()",
    )
    for marker in markers:
        if marker not in viewer:
            fail(f"GLB owned-resource cleanup marker missing: {marker}")
    if 'aria-label", "Interactive 3D preview' not in viewer:
        fail("GLB canvas accessible label is missing")
    error_callback = re.search(r"\(error: unknown\)\s*=>\s*\{(?P<body>.*?)\n\s*\}", viewer, re.DOTALL)
    if not error_callback or "if (disposed) return;" not in error_callback.group("body"):
        fail("GLB error callback is not guarded against stale/unmounted completion")


def between(source: str, start: str, end: str) -> str:
    if start not in source or end not in source:
        fail(f"cannot isolate lifecycle block: {start}")
    return source.split(start, 1)[1].split(end, 1)[0]


def check_async_addendum_contracts() -> None:
    workbench = read(WORKBENCH)
    harness = read(HARNESS)
    required_workbench = {
        "validation acceptance through production request guard": "acceptsRequest(currentValidation.current, request)",
        "parked candidate diagnostic": "parked_reason",
        "structured validation formatter": "formatValidationDetail",
        "structured validation actual/declared labels": '"actual" in value && "declared" in value',
        "replacement candidate focus": "candidateRefs.current[selectedId]?.focus()",
        "empty candidate focus fallback": "emptyCandidatesRef.current?.focus()",
        "workspace empty state": "No workspaces are available.",
        "workspace discovery failure state": "Workspace discovery failed.",
        "candidate loading state": "Loading candidates…",
        "candidate failure state": "Candidate discovery failed.",
        "candidate empty state": "No BLUECAD candidates exist in this workspace.",
        "attempt trail": "Attempt history",
        "malformed attempt detail preservation": "formatAttemptDetail",
    }
    for label, marker in required_workbench.items():
        if marker not in workbench:
            fail(f"async addendum contract missing: {label}")

    handle_brief_ref_body = between(workbench, "const handleBriefRef =", "const visibleCandidates =")
    duplicate_body = between(workbench, "const duplicateSelectedBrief =", "const navigator =")
    navigator_body = between(workbench, "const navigator =", "const sidecar =")
    duplicate_focus_requirements = {
        "duplicate brief arms deferred focus": (duplicate_body, "focusBriefOnMount.current = true"),
        "duplicate brief reveals navigator": (duplicate_body, 'requestShellRegionOpen("navigator")'),
        "brief ref consumes deferred focus intent": (handle_brief_ref_body, "focusBriefOnMount.current"),
        "brief ref clears deferred focus intent": (handle_brief_ref_body, "focusBriefOnMount.current = false"),
        "brief ref transfers focus after mount": (handle_brief_ref_body, "node.focus()"),
        "navigator textarea uses semantic callback ref": (navigator_body, "ref={handleBriefRef}"),
    }
    for label, (body, marker) in duplicate_focus_requirements.items():
        if marker not in body:
            fail(f"duplicate-brief focus control flow regressed: {label}")

    refresh_body = between(workbench, "const refresh =", "const onCreate =")
    create_body = between(workbench, "const onCreate =", "const onArchive =")
    archive_body = between(workbench, "const onArchive =", "const onPromote =")
    promote_body = between(workbench, "const onPromote =", "const duplicateSelectedBrief =")
    lifecycle_requirements = {
        "refresh": (refresh_body, ("loadCandidates(", "loadAggregate(")),
        "create": (create_body, ("createBluecadCandidate(", "loadCandidates(", "loadAggregate(")),
        "archive": (archive_body, ("archiveBluecadCandidate(", "loadCandidates(", "loadAggregate(")),
        "promote": (promote_body, ("promoteBluecadCandidate(", "await refresh()")),
    }
    for label, (body, markers) in lifecycle_requirements.items():
        missing = [marker for marker in markers if marker not in body]
        if missing:
            fail(f"{label} lifecycle is not tied to canonical reload path: {', '.join(missing)}")

    required_harness = (
        "stale same-context generation accepted",
        "stale validation response accepted",
        "stale validation response mutated visible state",
        "current create completion rejected",
        "current archive completion rejected",
        "duplicate brief became backend mutation",
    )
    for marker in required_harness:
        if marker not in harness:
            fail(f"state harness addendum case missing: {marker}")


def check_no_fake_authority() -> None:
    bodies = [
        path.read_text(encoding="utf-8")
        for path in UI_AUTHORITY_PATHS
        if path.exists()
    ]
    combined = "\n".join(bodies)
    if FAKE_TELEMETRY.search(combined):
        fail("mock workstation telemetry/confidence/engineering result introduced")
    if FORBIDDEN_AUTHORITY.search(combined):
        fail("forbidden filesystem/provider/private-path authority appears in 085 UI")


def status_fixture(row: str, *, decoy: str = "") -> str:
    return "\n".join((decoy, "## Registry", "", REGISTRY_HEADER, REGISTRY_SEPARATOR, row, "", "## Next"))


def self_test() -> None:
    validate_scope(set())
    validate_scope({"frontend/src/components/bluecad/BluecadWorkbench.tsx", "scripts/check_bluecad_workbench.py"})
    try:
        validate_scope({"backend/app/main.py"})
    except SystemExit:
        pass
    else:
        fail("negative scope self-test accepted backend change")
    if FAKE_TELEMETRY.search("AI confidence 92%") is None:
        fail("fake telemetry detector self-test failed")
    if FORBIDDEN_AUTHORITY.search("stored_path") is None:
        fail("forbidden authority detector self-test failed")
    required_scanned_ui = {
        FRONTEND / "components/bluecad/BluecadNavigator.tsx",
        FRONTEND / "components/bluecad/BluecadSidecar.tsx",
        FRONTEND / "components/bluecad/BluecadAnalysisDock.tsx",
        FRONTEND / "components/shell/ContextualNavigator.tsx",
        FRONTEND / "components/shell/ContextualSidecar.tsx",
        FRONTEND / "components/shell/AnalysisDock.tsx",
    }
    if not required_scanned_ui.issubset(set(UI_AUTHORITY_PATHS)):
        fail("authority scanner coverage self-test failed")

    valid = f"| 085 | in_review | {EXPECTED_PR} | BLUECAD-WORKBENCH-2 | 006, 006c, 083, 084 | active |"
    check_registry_text(status_fixture(valid))
    decoy = f"<!--\n{valid}\n-->"
    check_registry_text(status_fixture(valid, decoy=decoy))
    fenced_decoy = "```markdown\n## Registry\n\n" + REGISTRY_HEADER + "\n" + REGISTRY_SEPARATOR + "\n" + valid + "\n```"
    check_registry_text(status_fixture(valid, decoy=fenced_decoy))
    malformed_close_decoy = (
        "```markdown\n```not-a-close\n## Registry\n\n"
        + REGISTRY_HEADER + "\n" + REGISTRY_SEPARATOR + "\n" + valid + "\n```"
    )
    check_registry_text(status_fixture(valid, decoy=malformed_close_decoy))
    overindented_close_decoy = (
        "```markdown\n    ```\n## Registry\n\n"
        + REGISTRY_HEADER + "\n" + REGISTRY_SEPARATOR + "\n" + valid + "\n```"
    )
    check_registry_text(status_fixture(valid, decoy=overindented_close_decoy))
    unterminated_comment_decoy = "<!--\n## Registry\n\n" + REGISTRY_HEADER + "\n" + REGISTRY_SEPARATOR + "\n" + valid
    for invalid in (
        "| 085 | ready | — | BLUECAD-WORKBENCH-2 | deps | wrong |",
        "| 084 | merged | — | OTHER | deps | no 085 |",
    ):
        try:
            check_registry_text(status_fixture(invalid, decoy=decoy))
        except SystemExit:
            pass
        else:
            fail("registry self-test accepted non-canonical or invalid 085 lifecycle evidence")
    for hidden_only in (fenced_decoy, malformed_close_decoy, overindented_close_decoy, unterminated_comment_decoy):
        try:
            check_registry_text(hidden_only)
        except SystemExit:
            pass
        else:
            fail("registry self-test accepted hidden lifecycle evidence as canonical")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    self_test()
    if args.self_test:
        print("BLUECAD workbench checker self-test passed")
        return
    validate_scope(changed_paths())
    check_registry()
    check_primary_composition()
    check_state_authority()
    check_viewer_cleanup()
    check_async_addendum_contracts()
    check_no_fake_authority()
    print("BLUECAD workbench checks passed")


if __name__ == "__main__":
    main()
