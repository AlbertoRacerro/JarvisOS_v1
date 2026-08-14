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


def fail(message: str) -> None:
    print(f"BLUECAD read-model check failed: {message}", file=sys.stderr)
    raise SystemExit(1)


def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        fail(f"missing required file: {path.relative_to(ROOT)}")


def registry_state(text: str) -> str:
    rows = [line for line in text.splitlines() if line.startswith("| 084 |")]
    if len(rows) != 1:
        fail(f"STATUS.md must contain exactly one canonical spec 084 row; found {len(rows)}")
    cells = [cell.strip() for cell in rows[0].strip().strip("|").split("|")]
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
    if registry_state(merged) != "merged" or registry_state(active) != "in_review":
        fail("registry lifecycle detector self-test failed")
    try:
        registry_state("| 084 | merged | — | BLUECAD-READ-MODEL-1 | deps | wrong |")
    except SystemExit:
        pass
    else:
        fail("registry lifecycle detector accepted wrong implementation PR")

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
