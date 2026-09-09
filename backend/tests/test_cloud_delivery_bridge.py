from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from cloud_delivery_bridge import (  # noqa: E402
    MARKER,
    PATCH_CLOSE,
    PATCH_OPEN,
    BridgeError,
    Payload,
    _diff_paths,
    apply_and_verify,
    parse_payload,
)


def _body(*, patch: str, paths: list[str] | None = None, **overrides: object) -> str:
    metadata: dict[str, object] = {
        "version": 1,
        "pr": 589,
        "base_sha": "a" * 40,
        "target_ref": "impl/143-operator-semantic-ux",
        "patch_sha256": hashlib.sha256(patch.encode()).hexdigest(),
        "changed_paths": paths or ["frontend/src/pages/Settings.tsx"],
        "validation_profile": "frontend-143",
    }
    metadata.update(overrides)
    return (
        f"{MARKER}\n```json\n{json.dumps(metadata)}\n```\n"
        f"{PATCH_OPEN}{patch}{PATCH_CLOSE}"
    )


def test_payload_requires_exact_digest_and_normalized_safe_paths() -> None:
    patch = "diff --git a/frontend/src/pages/Settings.tsx b/frontend/src/pages/Settings.tsx\n"
    payload = parse_payload(_body(patch=patch))
    assert payload.pr == 589
    assert payload.base_sha == "a" * 40
    assert payload.changed_paths == ("frontend/src/pages/Settings.tsx",)

    with pytest.raises(BridgeError, match="digest"):
        parse_payload(_body(patch=patch, patch_sha256="b" * 64))
    with pytest.raises(Exception, match="sensitive"):
        parse_payload(_body(patch=patch, paths=[".github/workflows/ci.yml"]))
    with pytest.raises(BridgeError, match="ambiguous"):
        parse_payload(_body(patch=patch, paths=["frontend/../frontend/src/pages/Settings.tsx"]))
    with pytest.raises(BridgeError, match="ambiguous"):
        parse_payload(_body(patch=patch, paths=["frontend\\src\\pages\\Settings.tsx"]))
    with pytest.raises(BridgeError, match="patch headers"):
        parse_payload(_body(patch=patch, paths=["frontend/src/pages/Other.tsx"]))


def test_payload_refuses_default_ref_control_paths_and_unknown_profiles() -> None:
    patch = "diff --git a/README.md b/README.md\n"
    with pytest.raises(BridgeError, match="target_ref"):
        parse_payload(_body(patch=patch, target_ref="master"))
    for path in [
        "scripts/cloud_delivery_bridge.py",
        ".gitmodules",
        ".gitattributes",
    ]:
        with pytest.raises(BridgeError, match="control"):
            parse_payload(_body(patch=patch, paths=[path]))
    with pytest.raises(BridgeError, match="validation_profile"):
        parse_payload(_body(patch=patch, validation_profile="arbitrary-shell"))


def test_payload_refuses_unknown_path_class_instead_of_docs_fallback() -> None:
    path = "configs/ai_egress_policy.json"
    patch = f"diff --git a/{path} b/{path}\n"
    with pytest.raises(BridgeError, match="unsupported changed-path class"):
        parse_payload(_body(patch=patch, paths=[path], validation_profile="docs"))


def _git(cwd: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=cwd, text=True, capture_output=True, check=True
    )
    return result.stdout


def _init_repo(repo: Path) -> str:
    repo.mkdir()
    _git(repo, "init")
    _git(repo, "config", "user.email", "test@example.invalid")
    _git(repo, "config", "user.name", "Bridge Test")
    seed = repo / "README.md"
    seed.write_text("base\n", encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "base")
    return _git(repo, "rev-parse", "HEAD").strip()


def test_apply_verifies_exact_base_and_changed_path_set(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    base = _init_repo(repo)
    target = repo / "frontend" / "src" / "pages" / "Settings.tsx"
    target.parent.mkdir(parents=True)
    target.write_text("before\n", encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "tracked target")
    base = _git(repo, "rev-parse", "HEAD").strip()
    target.write_text("after\n", encoding="utf-8")
    patch = _git(repo, "diff", "--binary", "--full-index")
    _git(repo, "checkout", "--", ".")
    patch_file = tmp_path / "delivery.patch"
    patch_file.write_text(patch, encoding="utf-8")
    payload = Payload(
        pr=589,
        base_sha=base,
        target_ref="impl/143-operator-semantic-ux",
        patch_sha256=hashlib.sha256(patch.encode()).hexdigest(),
        changed_paths=("frontend/src/pages/Settings.tsx",),
        validation_profile="frontend-143",
        patch=patch,
    )
    apply_and_verify(repo, payload, patch_file)
    assert target.read_text(encoding="utf-8") == "after\n"

    _git(repo, "checkout", "--", ".")
    wrong = Payload(
        **{**payload.__dict__, "changed_paths": ("frontend/src/pages/Other.tsx",)}
    )
    with pytest.raises(BridgeError, match="patch headers"):
        apply_and_verify(repo, wrong, patch_file)


def test_apply_accounts_for_new_untracked_file_before_validation(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    base = _init_repo(repo)
    rel = "frontend/tests/143-operator-semantic-ux.mjs"
    target = repo / rel
    target.parent.mkdir(parents=True)
    target.write_text("export const bridgeProof = true;\n", encoding="utf-8")
    _git(repo, "add", "--intent-to-add", "--", rel)
    patch = _git(repo, "diff", "--binary", "--full-index", "--", rel)
    _git(repo, "reset", "--", rel)
    target.unlink()

    patch_file = tmp_path / "addition.patch"
    patch_file.write_text(patch, encoding="utf-8")
    payload = Payload(
        pr=589,
        base_sha=base,
        target_ref="impl/143-operator-semantic-ux",
        patch_sha256=hashlib.sha256(patch.encode()).hexdigest(),
        changed_paths=(rel,),
        validation_profile="frontend-143",
        patch=patch,
    )
    apply_and_verify(repo, payload, patch_file)
    assert target.read_text(encoding="utf-8") == "export const bridgeProof = true;\n"


def test_post_apply_inventory_includes_ignored_untracked_files(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    base = _init_repo(repo)
    ignore = repo / ".gitignore"
    ignore.write_text("backend/.hidden/\n", encoding="utf-8")
    _git(repo, "add", ".gitignore")
    _git(repo, "commit", "-m", "ignore hidden backend payloads")
    base = _git(repo, "rev-parse", "HEAD").strip()

    hidden = repo / "backend" / ".hidden" / "payload.py"
    hidden.parent.mkdir(parents=True)
    hidden.write_text("raise RuntimeError('must never execute')\n", encoding="utf-8")

    assert _diff_paths(repo, base) == ("backend/.hidden/payload.py",)


def test_workflow_freezes_payload_before_untrusted_validation_and_separates_writer() -> None:
    workflow = (ROOT / ".github" / "workflows" / "cloud-delivery-bridge.yml").read_text(
        encoding="utf-8"
    )
    admit = workflow.split("  admit:\n", 1)[1].split("\n  validate:\n", 1)[0]
    validate = workflow.split("  validate:\n", 1)[1].split("\n  materialize:\n", 1)[0]
    write = workflow.split("\n  materialize:\n", 1)[1]
    assert "actions/upload-artifact@v4" in admit
    assert "npm run" not in admit
    assert "Bind validation strength to admitted paths" in admit
    assert "unsupported changed-path class" in admit
    assert "INPUT_PR: ${{ inputs.pr }}" in admit
    assert '--pr "$INPUT_PR"' in admit
    assert "--pr '${{ inputs.pr }}'" not in admit
    assert "contents: read" in validate
    assert "contents: write" not in validate
    assert "persist-credentials: false" in validate
    assert "npm run test:143" in validate
    assert "actions/upload-artifact@v4" not in validate
    assert "contents: write" in write
    assert "npm run" not in write
    assert "pytest" not in write
    assert "ref: ${{ github.sha }}" in write
    assert "cloud_delivery_bridge.py materialize" in write
