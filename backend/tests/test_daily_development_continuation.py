from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "daily_development_continuation.py"
WORKFLOW = ROOT / ".github" / "workflows" / "daily-development-continuation.yml"
SPEC = importlib.util.spec_from_file_location("daily_development_continuation", SCRIPT)
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = module
SPEC.loader.exec_module(module)


class FakeReader:
    def __init__(self, pulls=None, registries=None, comments=None, status="ahead"):
        self._pulls = pulls or []
        self._registries = registries or {}
        self._comments = comments or {}
        self._status = status
        self.calls = []

    def open_pulls(self):
        self.calls.append("open_pulls")
        return self._pulls

    def file_text(self, path, ref):
        self.calls.append(("file_text", path, ref))
        return self._registries[ref]

    def comments(self, number):
        self.calls.append(("comments", number))
        return self._comments.get(number, [])

    def compare(self, base, head):
        self.calls.append(("compare", base, head))
        return self._status


def registry(status="in_review", pr=210, second_active=False):
    pr_cell = f"[#{pr}](https://github.com/owner/repo/pull/{pr})" if status == "in_review" else "—"
    rows = [
        "## Registry",
        "| Spec | Status | Implementation PR | Name | Depends on | Description |",
        "| --- | --- | --- | --- | --- | --- |",
        f"| 079 | {status} | {pr_cell} | Continuation | 022 | active |",
        "| 080 | planned | — | Review | 079 | later |",
    ]
    if second_active:
        rows.append("| 081 | in_review | [#211](https://github.com/owner/repo/pull/211) | Extra | 079 | bad |")
    return "\n".join(rows)


def pull(number=210, **updates):
    value = {
        "number": number,
        "state": "open",
        "draft": False,
        "title": "Implement spec 079",
        "body": "**Spec gate:** implementation 079",
        "base": {"ref": "master", "sha": "a" * 40},
        "head": {
            "ref": "spec/079-work",
            "sha": "b" * 40,
            "repo": {"full_name": "owner/repo"},
        },
    }
    value.update(updates)
    return value


def reader_for(pull_value=None, *, status="ahead", comments=None, registry_text=None):
    value = pull_value or pull()
    sha = value["head"]["sha"]
    return FakeReader(
        [value],
        {sha: registry_text or registry()},
        {value["number"]: comments or []},
        status,
    )


def build(mode="SHADOW", *, reader=None, token=False):
    return module.build_plan(
        mode=mode,
        repository="owner/repo",
        reader=reader or reader_for(),
        token_present=token,
    )


def test_off_never_reads_external_state():
    reader = FakeReader()
    result = build("OFF", reader=reader)
    assert result.action == "noop"
    assert result.reason == "mode_off"
    assert reader.calls == []


def test_shadow_discovers_registry_from_exact_pr_head_without_provider_token():
    reader = reader_for()
    result = build(reader=reader)
    assert result.action == "shadow"
    assert result.spec_id == "079"
    assert result.pr_number == 210
    assert result.head_ref == "spec/079-work"
    assert result.head_sha == "b" * 40
    assert result.checkpoint_sha == "a" * 40
    assert ("file_text", "docs/specs/STATUS.md", "b" * 40) in reader.calls


def test_execute_requires_nonempty_existing_secret():
    with pytest.raises(module.ContinuationError, match="not configured"):
        build("EXECUTE_NO_MERGE", token=False)
    assert build("EXECUTE_NO_MERGE", token=True).action == "execute"


def test_no_open_pull_is_a_noop():
    result = build(reader=FakeReader())
    assert result.action == "noop"
    assert result.reason == "no_active_front"


def test_open_pull_without_active_registry_row_is_ignored():
    value = pull()
    result = build(reader=reader_for(value, registry_text=registry("ready")))
    assert result.action == "noop"


@pytest.mark.parametrize(
    "value, message",
    [
        (pull(base={"ref": "develop", "sha": "a" * 40}), "base is not master"),
        (
            pull(head={"ref": "spec/079-work", "sha": "b" * 40, "repo": {"full_name": "other/repo"}}),
            "fork",
        ),
        (pull(head={"ref": "master", "sha": "b" * 40, "repo": {"full_name": "owner/repo"}}), "protected"),
        (pull(title="Other", body="", head={"ref": "feature", "sha": "b" * 40, "repo": {"full_name": "owner/repo"}}), "does not bind"),
    ],
)
def test_fail_closed_pull_cases(value, message):
    with pytest.raises(module.ContinuationError, match=message):
        build(reader=reader_for(value))


def test_draft_pull_is_not_an_active_candidate():
    result = build(reader=reader_for(pull(draft=True)))
    assert result.action == "noop"


def test_in_progress_registry_is_not_resumable():
    with pytest.raises(module.ContinuationError, match="not resumable"):
        build(reader=reader_for(registry_text=registry("in_progress")))


def test_registry_must_bind_the_same_pr_number():
    with pytest.raises(module.ContinuationError, match="bind itself"):
        build(reader=reader_for(registry_text=registry(pr=211)))


def test_registry_may_not_claim_two_active_fronts():
    with pytest.raises(module.ContinuationError, match="multiple active"):
        build(reader=reader_for(registry_text=registry(second_active=True)))


def test_two_candidate_prs_fail_closed():
    first = pull()
    second = pull(211)
    second["title"] = "Implement spec 081"
    second["body"] = "**Spec gate:** implementation 081"
    second["head"] = {"ref": "spec/081-work", "sha": "c" * 40, "repo": {"full_name": "owner/repo"}}
    second_registry = registry().replace("| 079 | in_review | [#210]", "| 079 | merged | —").replace(
        "| 080 | planned | — | Review | 079 | later |",
        "| 080 | planned | — | Review | 079 | later |\n| 081 | in_review | [#211](https://github.com/owner/repo/pull/211) | Extra | 079 | active |",
    )
    reader = FakeReader(
        [first, second],
        {"b" * 40: registry(), "c" * 40: second_registry},
        {},
        "ahead",
    )
    with pytest.raises(module.ContinuationError, match="multiple active implementation"):
        build(reader=reader)


def test_checkpoint_must_be_ancestor():
    with pytest.raises(module.ContinuationError, match="does not descend"):
        build(reader=reader_for(status="diverged"))


def test_marker_makes_same_no_change_head_idempotent():
    marker = module.marker_text("079", 210, "b" * 40, "b" * 40)
    result = build(reader=reader_for(status="identical", comments=[{"body": marker}]))
    assert result.action == "noop"
    assert result.reason == "head_already_processed"


def test_changed_marker_allows_new_output_head_next_day():
    value = pull()
    value["head"]["sha"] = "c" * 40
    marker = module.marker_text("079", 210, "b" * 40, "c" * 40)
    result = build(reader=reader_for(value, status="identical", comments=[{"body": marker}]))
    assert result.action == "shadow"
    assert result.checkpoint_sha == "c" * 40


def test_marker_claiming_unobserved_push_fails_closed():
    marker = module.marker_text("079", 210, "b" * 40, "c" * 40)
    with pytest.raises(module.ContinuationError, match="did not advance"):
        build(reader=reader_for(comments=[{"body": marker}]))


def test_conflicting_markers_fail_closed():
    one = module.marker_text("079", 210, "b" * 40, "b" * 40)
    two = module.marker_text("079", 210, "b" * 40, "c" * 40)
    with pytest.raises(module.ContinuationError, match="incompatible"):
        build(reader=reader_for(comments=[{"body": one}, {"body": two}]))


@pytest.mark.parametrize(
    "path",
    [
        ".github/workflows/ci.yml",
        "AGENTS.md",
        "CODEOWNERS",
        "scripts/daily_development_continuation.py",
        "backend/tests/test_daily_development_continuation.py",
        ".env",
        ".env.local",
        "config/token/value.txt",
        "docs/secrets/readme.md",
    ],
)
def test_forbidden_paths_are_rejected(path):
    with pytest.raises(module.ContinuationError):
        module.validate_changed_paths([path])


def test_normal_implementation_paths_are_allowed():
    module.validate_changed_paths(["backend/app/example.py", "backend/tests/test_example.py"])


def test_file_count_is_bounded():
    with pytest.raises(module.ContinuationError, match="too many"):
        module.validate_changed_paths([f"backend/app/f{i}.py" for i in range(21)])


def test_status_may_change_only_active_row():
    before = registry()
    after = before.replace("| 079 | in_review", "| 079 | merged")
    module.validate_status_change(before, after, "079")
    bad = after.replace("| 080 | planned", "| 080 | ready")
    with pytest.raises(module.ContinuationError, match="only the active"):
        module.validate_status_change(before, bad, "079")


def test_status_cannot_add_parallel_row():
    with pytest.raises(module.ContinuationError, match="add or remove"):
        module.validate_status_change(
            registry(), registry() + "\n| 081 | planned | — | Extra | — | no |", "079"
        )


def test_workflow_contract_is_daily_off_by_default_and_separates_authority():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert 'cron: "17 4 * * *"' in text
    assert "workflow_dispatch:" in text
    assert "group: jarvis-development-continuation" in text
    assert "vars.JARVISOS_CONTINUATION_MODE || 'OFF'" in text
    assert "anthropics/claude-code-action@v1" in text
    assert "claude_code_oauth_token: ${{ secrets.CLAUDE_CODE_OAUTH_TOKEN }}" in text
    assert "persist-credentials: false" in text
    assert "generate-patch:" in text and "validate-and-push:" in text
    assert "contents: read" in text and "contents: write" in text
    assert "git apply --index --whitespace=error-all" in text
    assert "python -m pytest -q" in text
    assert 'git push origin "HEAD:refs/heads/$HEAD_REF"' in text
    assert "Never modify .github/**, AGENTS.md, CODEOWNERS" in text
    assert "Do not commit, push, comment, merge" in text
