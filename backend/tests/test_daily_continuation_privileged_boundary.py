from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "daily-development-continuation.yml"


def test_privileged_push_uses_prepatch_isolated_repository_delivery_copy() -> None:
    source = WORKFLOW.read_text(encoding="utf-8")
    reapply = source.split(
        "- name: Reapply and revalidate in the trusted workspace", 1
    )[1].split("- name: Commit and push only from the unchanged exact head", 1)[0]
    copy = (
        'cp scripts/repository_delivery.py '
        '"$RUNNER_TEMP/trusted-repository-delivery.py"'
    )
    apply_patch = (
        'git apply --index --whitespace=error-all '
        '"$RUNNER_TEMP/continuation/continuation.patch"'
    )
    assert copy in reapply
    assert apply_patch in reapply
    assert reapply.index(copy) < reapply.index(apply_patch)

    push = source.split(
        "- name: Commit and push only from the unchanged exact head", 1
    )[1].split("record-marker:", 1)[0]
    isolated = (
        'python -I -S "$RUNNER_TEMP/trusted-repository-delivery.py" '
        "ci-guarded-push"
    )
    assert isolated in push
    assert "python scripts/repository_delivery.py ci-guarded-push" not in push
