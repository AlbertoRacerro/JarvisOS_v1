from __future__ import annotations

import base64
import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "daily_development_continuation.py"
SPEC = importlib.util.spec_from_file_location("daily_continuation", SCRIPT)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = mod
SPEC.loader.exec_module(mod)

REPOSITORY = "AlbertoRacerro/JarvisOS_v1"
BASE = "1" * 40
HEAD = "2" * 40
NEXT = "3" * 40
SIDE = "4" * 40
RUN = "12345"
TREE = "a" * 40


def registry(status: str = "in_review", pr: int = 210, extra: str = "") -> str:
    return (
        "# Status\n\n## Registry\n\n"
        "| Spec | Status | Implementation PR | Name | Depends on | Description |\n"
        "| --- | --- | --- | --- | --- | --- |\n"
        f"| 079 | {status} | https://github.com/{REPOSITORY}/pull/{pr} | CONTINUE | 004 | active |\n"
        "| 080 | planned | — | REVIEW | 079 | separate |\n"
        f"\n{extra}"
    )


def pull(*, number: int = 210, base: str = BASE, head: str = HEAD, **changes):
    value = {
        "number": number,
        "state": "open",
        "draft": False,
        "title": "Implement spec 079",
        "body": "Spec gate implementation 079",
        "base": {"ref": "master", "sha": base},
        "head": {
            "ref": "spec/079-work",
            "sha": head,
            "repo": {"full_name": REPOSITORY},
        },
    }
    for key, changed in changes.items():
        if key.startswith("head_"):
            value["head"][key[5:]] = changed
        elif key.startswith("base_"):
            value["base"][key[5:]] = changed
        else:
            value[key] = changed
    return value


class AcceptVerifier:
    def verify(
        self,
        token: str,
        *,
        run_id: str,
        audience: str,
        require_fresh: bool = False,
    ) -> bool:
        return (
            token == "valid.jwt.token"
            and run_id == RUN
            and audience.startswith(
                (
                    f"{mod.MARKER_OIDC_AUDIENCE_PREFIX}-",
                    f"{mod.COMMIT_OIDC_AUDIENCE_PREFIX}-",
                )
            )
        )


class RejectVerifier:
    def verify(
        self,
        token: str,
        *,
        run_id: str,
        audience: str,
        require_fresh: bool = False,
    ) -> bool:
        return False


class FakeReader:
    def __init__(self, pulls=None, statuses=None, comments=None, compares=None, commits=None):
        self.pulls = pulls if pulls is not None else [pull()]
        self.statuses = statuses if statuses is not None else {HEAD: registry()}
        self.comment_rows = comments if comments is not None else []
        self.compares = compares if compares is not None else {
            (BASE, HEAD): "ahead",
        }
        self.commits = commits if commits is not None else {
            HEAD: commit(HEAD, [BASE], "human")
        }
        self.open_pull_calls = 0
        self.commit_reads: list[str] = []

    def open_pulls(self):
        self.open_pull_calls += 1
        return self.pulls

    def file_text(self, path, ref):
        assert path == "docs/specs/STATUS.md"
        return self.statuses[ref]

    def comments(self, number):
        assert number == 210
        return self.comment_rows

    def compare(self, base, head):
        return self.compares.get((base, head), "behind")

    def commit_info(self, sha):
        self.commit_reads.append(sha)
        return self.commits[sha]


def commit(
    sha: str,
    parents: list[str],
    kind: str,
    input_head: str | None = None,
    *,
    token: str = "valid.jwt.token",
    tree_sha: str = TREE,
    declared_tree: str | None = None,
):
    message = "ordinary"
    author = {"login": "AlbertoRacerro"}
    committer = {"login": "AlbertoRacerro"}
    if kind == "continuation":
        input_head = input_head or parents[0]
        declared_tree = declared_tree or tree_sha
        message = (
            "Continue spec 079\n\nJarvis-Continuation: v2\nJarvis-Spec: 079\n"
            f"Jarvis-PR: 210\nJarvis-Input: {input_head}\n"
            f"Jarvis-Tree: {declared_tree}\nJarvis-Run: {RUN}\n"
            f"Jarvis-OIDC: {token}"
        )
        author = committer = {"login": "github-actions[bot]"}
    return {
        "sha": sha,
        "commit": {"message": message, "tree": {"sha": tree_sha}},
        "parents": [{"sha": parent} for parent in parents],
        "author": author,
        "committer": committer,
    }


def marker(input_head=BASE, output_head=HEAD, token="valid.jwt.token", run=RUN, actor="github-actions[bot]"):
    return {
        "body": mod.marker_text("079", 210, input_head, output_head, run, token),
        "user": {"login": actor},
    }


def fake_jwt(claims: dict[str, object], kid: str = "k1") -> str:
    def enc(value):
        raw = json.dumps(value, separators=(",", ":")).encode()
        return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()

    signature = base64.urlsafe_b64encode(b"x" * 256).rstrip(b"=").decode()
    return f"{enc({'alg': 'RS256', 'kid': kid})}.{enc(claims)}.{signature}"


def valid_claims():
    return {
        "iss": mod.OIDC_ISSUER,
        "aud": mod.marker_audience("079", 210, BASE, HEAD),
        "repository": REPOSITORY,
        "workflow_ref": f"{REPOSITORY}/{mod.WORKFLOW_PATH}@refs/heads/master",
        "ref": "refs/heads/master",
        "run_id": RUN,
        "event_name": "schedule",
        "iat": 1000,
        "nbf": 1000,
        "exp": 1600,
    }


def candidate(head=HEAD):
    return mod.Candidate("079", 210, "spec/079-work", head, BASE)


def test_off_returns_before_repository_discovery():
    reader = FakeReader()
    plan = mod.build_plan(
        mode="OFF", repository=REPOSITORY, reader=reader,
        token_present=False, verifier=RejectVerifier(),
    )
    assert plan.action == "noop"
    assert reader.open_pull_calls == 0


def test_invalid_mode_fails_closed():
    with pytest.raises(mod.ContinuationError, match="must be OFF"):
        mod.build_plan(
            mode="GO", repository=REPOSITORY, reader=FakeReader(),
            token_present=True, verifier=AcceptVerifier(),
        )


def test_shadow_is_provider_free_and_does_not_require_secret():
    plan = mod.build_plan(
        mode="SHADOW", repository=REPOSITORY, reader=FakeReader(),
        token_present=False, verifier=AcceptVerifier(),
    )
    assert plan.action == "shadow"
    assert plan.head_sha == HEAD


def test_execute_requires_secret():
    with pytest.raises(mod.ContinuationError, match="CLAUDE_CODE_OAUTH_TOKEN"):
        mod.build_plan(
            mode="EXECUTE_NO_MERGE", repository=REPOSITORY, reader=FakeReader(),
            token_present=False, verifier=AcceptVerifier(),
        )


def test_execute_discovers_exact_candidate():
    plan = mod.build_plan(
        mode="EXECUTE_NO_MERGE", repository=REPOSITORY, reader=FakeReader(),
        token_present=True, verifier=AcceptVerifier(),
    )
    assert plan.action == "execute"
    assert plan.pr_number == 210
    assert plan.checkpoint_sha == BASE


@pytest.mark.parametrize(
    "changed, message",
    [
        ({"draft": True}, "no_active_front"),
        ({"state": "closed"}, "no_active_front"),
    ],
)
def test_closed_or_draft_pr_is_ignored(changed, message):
    reader = FakeReader(pulls=[pull(**changed)])
    plan = mod.build_plan(
        mode="SHADOW", repository=REPOSITORY, reader=reader,
        token_present=False, verifier=AcceptVerifier(),
    )
    assert plan.reason == message


def test_fork_fails_closed():
    reader = FakeReader(pulls=[pull(head_repo={"full_name": "other/repo"})])
    with pytest.raises(mod.ContinuationError, match="fork"):
        mod.discover_candidate(REPOSITORY, reader)


def test_wrong_base_fails_closed():
    reader = FakeReader(pulls=[pull(base_ref="develop")])
    with pytest.raises(mod.ContinuationError, match="base is not master"):
        mod.discover_candidate(REPOSITORY, reader)


def test_protected_head_fails_closed():
    reader = FakeReader(pulls=[pull(head_ref="master")])
    with pytest.raises(mod.ContinuationError, match="protected"):
        mod.discover_candidate(REPOSITORY, reader)


def test_wrong_registry_pr_binding_fails_closed():
    reader = FakeReader(statuses={HEAD: registry(pr=211)})
    with pytest.raises(mod.ContinuationError, match="bind itself"):
        mod.discover_candidate(REPOSITORY, reader)


def test_missing_spec_binding_fails_closed():
    p = pull(title="unrelated", body="unrelated", head_ref="feature/work")
    reader = FakeReader(pulls=[p])
    with pytest.raises(mod.ContinuationError, match="does not bind spec"):
        mod.discover_candidate(REPOSITORY, reader)


def test_multiple_active_fronts_fail_closed():
    second = pull(number=211, head=NEXT, head_ref="spec/079-other")
    statuses = {HEAD: registry(), NEXT: registry(pr=211)}
    reader = FakeReader(pulls=[pull(), second], statuses=statuses)
    with pytest.raises(mod.ContinuationError, match="multiple active"):
        mod.discover_candidate(REPOSITORY, reader)


def test_in_progress_pre_pr_state_is_not_resumable():
    reader = FakeReader(statuses={HEAD: registry(status="in_progress")})
    with pytest.raises(mod.ContinuationError, match="not resumable"):
        mod.discover_candidate(REPOSITORY, reader)


def test_unverified_marker_from_shared_actions_actor_is_ignored():
    checkpoint, terminal = mod.checkpoint_for(
        candidate(), [marker(token="forged.jwt.token")],
        verifier=RejectVerifier(),
    )
    assert checkpoint == BASE
    assert terminal is False


def test_marker_from_human_is_ignored_even_with_valid_token():
    checkpoint, _ = mod.checkpoint_for(
        candidate(), [marker(actor="AlbertoRacerro")],
        verifier=AcceptVerifier(),
    )
    assert checkpoint == BASE


def test_verified_changed_marker_advances_checkpoint():
    checkpoint, terminal = mod.checkpoint_for(
        candidate(), [marker()], verifier=AcceptVerifier(),
    )
    assert checkpoint == HEAD
    assert terminal is False


def test_floating_no_change_marker_fails_closed():
    with pytest.raises(mod.ContinuationError, match="not contiguous"):
        mod.checkpoint_for(
            candidate(), [marker(input_head=HEAD, output_head=HEAD)],
            verifier=AcceptVerifier(),
        )


def test_bridge_then_no_change_is_terminal():
    comments = [marker(BASE, HEAD), marker(HEAD, HEAD)]
    checkpoint, terminal = mod.checkpoint_for(
        candidate(), comments, verifier=AcceptVerifier(),
    )
    assert checkpoint == HEAD
    assert terminal is True


def test_conflicting_markers_fail_closed():
    comments = [marker(BASE, HEAD), marker(BASE, NEXT)]
    with pytest.raises(mod.ContinuationError, match="incompatible"):
        mod.checkpoint_for(
            candidate(), comments, verifier=AcceptVerifier(),
        )


def test_disconnected_verified_marker_fails_closed():
    with pytest.raises(mod.ContinuationError, match="not contiguous"):
        mod.checkpoint_for(
            candidate(), [marker(HEAD, NEXT)],
            verifier=AcceptVerifier(),
        )


def test_duplicate_marker_is_idempotent():
    checkpoint, _ = mod.checkpoint_for(
        candidate(), [marker(), marker()], verifier=AcceptVerifier(),
    )
    assert checkpoint == HEAD


def test_divergent_checkpoint_fails_closed():
    reader = FakeReader(
        comments=[marker()],
        compares={(BASE, HEAD): "ahead", (HEAD, HEAD): "identical"},
    )
    plan = mod.build_plan(
        mode="SHADOW", repository=REPOSITORY, reader=reader,
        token_present=False, verifier=AcceptVerifier(),
    )
    assert plan.action == "shadow"


def test_recovery_finds_single_unrecorded_continuation_commit():
    reader = FakeReader(
        statuses={NEXT: registry()},
        pulls=[pull(head=NEXT)],
        compares={(BASE, NEXT): "ahead"},
        commits={NEXT: commit(NEXT, [BASE], "continuation", BASE)},
    )
    plan = mod.build_plan(
        mode="EXECUTE_NO_MERGE", repository=REPOSITORY, reader=reader,
        token_present=True, verifier=AcceptVerifier(),
    )
    assert plan.action == "recover"
    assert plan.recovery_output_sha == NEXT


def test_recovery_rejects_forged_shared_actions_commit():
    reader = FakeReader(
        statuses={NEXT: registry()},
        pulls=[pull(head=NEXT)],
        compares={(BASE, NEXT): "ahead"},
        commits={
            NEXT: commit(
                NEXT, [BASE], "continuation", BASE, token="forged.jwt.token"
            )
        },
    )
    plan = mod.build_plan(
        mode="EXECUTE_NO_MERGE", repository=REPOSITORY, reader=reader,
        token_present=True, verifier=AcceptVerifier(),
    )
    assert plan.action == "execute"
    assert plan.recovery_output_sha == ""


def test_recovery_rejects_authenticated_tree_mismatch():
    reader = FakeReader(
        commits={
            NEXT: commit(
                NEXT, [BASE], "continuation", BASE, declared_tree="b" * 40
            )
        },
        compares={(BASE, NEXT): "ahead"},
    )
    with pytest.raises(mod.ContinuationError, match="tree does not match"):
        mod.find_unrecorded_continuation(
            candidate(NEXT), BASE, reader, AcceptVerifier()
        )


def test_recovery_ignores_unrelated_merge_side_history():
    merge = "5" * 40
    reader = FakeReader(
        commits={
            merge: commit(merge, [NEXT, SIDE], "human"),
            NEXT: commit(NEXT, [BASE], "continuation", BASE),
            SIDE: commit(SIDE, ["6" * 40], "human"),
        },
        compares={
            (BASE, NEXT): "ahead",
            (BASE, SIDE): "behind",
            (BASE, merge): "ahead",
        },
    )
    found = mod.find_unrecorded_continuation(
        candidate(merge), BASE, reader, AcceptVerifier()
    )
    assert found == NEXT
    assert SIDE not in reader.commit_reads


def test_recovery_fails_on_multiple_continuation_commits():
    fourth = "7" * 40
    reader = FakeReader(
        commits={
            fourth: commit(fourth, [NEXT], "continuation", NEXT),
            NEXT: commit(NEXT, [BASE], "continuation", BASE),
        },
        compares={(BASE, NEXT): "ahead"},
    )
    with pytest.raises(mod.ContinuationError, match="multiple"):
        mod.find_unrecorded_continuation(
            candidate(fourth), BASE, reader, AcceptVerifier()
        )


@pytest.mark.parametrize(
    "path",
    [
        ".github/workflows/x.yml",
        "AGENTS.md",
        "CODEOWNERS",
        "scripts/daily_development_continuation.py",
        "backend/tests/test_daily_development_continuation.py",
        ".git/hooks/pre-commit",
        "config/.env",
        "docs/api-token.txt",
    ],
)
def test_protected_and_sensitive_paths_are_rejected(path):
    with pytest.raises(mod.ContinuationError):
        mod.validate_changed_paths([path], "079")


@pytest.mark.parametrize(
    "path",
    [
        "backend/tests/test_bluecad_conformance.py",
        "backend/tests/bluecad/test_geometry_conformance.py",
    ],
)
def test_maintainer_owned_conformance_tests_are_rejected(path):
    with pytest.raises(mod.ContinuationError, match="maintainer-owned conformance test"):
        mod.validate_changed_paths([path], "079")


def test_allowed_paths_pass():
    mod.validate_changed_paths(
        [
            "backend/app/service.py",
            "backend/tests/test_service.py",
            "docs/specs/STATUS.md",
            "docs/specs/079-autonomous-development-loop-0.md",
        ],
        "079",
    )


@pytest.mark.parametrize(
    "path",
    [
        "docs/specs/080-autonomous-review-repair-0.md",
        "docs/specs/078-bluecad-complex-system-reference-architecture.md",
        "docs/specs/archive/079-old.md",
    ],
)
def test_non_active_specification_paths_are_rejected(path):
    with pytest.raises(mod.ContinuationError, match="non-active specification"):
        mod.validate_changed_paths([path], "079")


def test_too_many_paths_fail():
    with pytest.raises(mod.ContinuationError, match="too many"):
        mod.validate_changed_paths([f"docs/{i}.md" for i in range(21)], "079")


def test_status_only_active_row_may_change_when_binding_is_preserved():
    before = registry(extra="queue unchanged\n")
    after = before.replace("| CONTINUE | 004 | active |", "| CONTINUE | 004 | active detail |")
    mod.validate_status_change(before, after, "079", 210)


def test_status_may_not_leave_in_review():
    before = registry()
    after = before.replace("| 079 | in_review", "| 079 | merged")
    with pytest.raises(mod.ContinuationError, match="remain in_review"):
        mod.validate_status_change(before, after, "079", 210)


def test_status_may_not_rebind_the_active_pr():
    before = registry()
    after = before.replace("/pull/210", "/pull/211")
    with pytest.raises(mod.ContinuationError, match="active PR"):
        mod.validate_status_change(before, after, "079", 210)


def test_status_dependencies_may_not_change():
    before = registry()
    after = before.replace("| CONTINUE | 004 | active |", "| CONTINUE | 080 | active |")
    with pytest.raises(mod.ContinuationError, match="dependencies may not change"):
        mod.validate_status_change(before, after, "079", 210)


def test_status_prose_change_fails():
    before = registry(extra="queue unchanged\n")
    after = before.replace("queue unchanged", "queue changed")
    with pytest.raises(mod.ContinuationError, match="exact active"):
        mod.validate_status_change(before, after, "079", 210)


def test_status_other_row_change_fails():
    before = registry()
    after = before.replace("| 080 | planned", "| 080 | ready")
    with pytest.raises(mod.ContinuationError, match="exact active"):
        mod.validate_status_change(before, after, "079", 210)


def test_oidc_verifier_binds_exact_workflow_and_run(monkeypatch):
    monkeypatch.setattr(mod, "_rsa_rs256_valid", lambda *args: True)
    verifier = mod.GitHubOIDCVerifier(
        REPOSITORY,
        jwks_loader=lambda: {"keys": [{"kid": "k1", "kty": "RSA", "use": "sig"}]},
        now=lambda: 1200,
    )
    assert verifier.verify(
        fake_jwt(valid_claims()),
        run_id=RUN,
        audience=mod.marker_audience("079", 210, BASE, HEAD),
        require_fresh=True,
    )


@pytest.mark.parametrize(
    "field,value",
    [
        ("workflow_ref", f"{REPOSITORY}/.github/workflows/cheap-review.yml@refs/heads/master"),
        ("run_id", "999"),
        ("repository", "other/repo"),
        ("ref", "refs/heads/feature"),
        ("event_name", "pull_request"),
        ("aud", "other-audience"),
    ],
)
def test_oidc_verifier_rejects_other_workflow_or_context(monkeypatch, field, value):
    monkeypatch.setattr(mod, "_rsa_rs256_valid", lambda *args: True)
    claims = valid_claims()
    claims[field] = value
    verifier = mod.GitHubOIDCVerifier(
        REPOSITORY,
        jwks_loader=lambda: {"keys": [{"kid": "k1", "kty": "RSA", "use": "sig"}]},
        now=lambda: 1200,
    )
    assert not verifier.verify(
        fake_jwt(claims),
        run_id=RUN,
        audience=mod.marker_audience("079", 210, BASE, HEAD),
        require_fresh=True,
    )


def test_historical_oidc_proof_does_not_require_unexpired_token(monkeypatch):
    monkeypatch.setattr(mod, "_rsa_rs256_valid", lambda *args: True)
    verifier = mod.GitHubOIDCVerifier(
        REPOSITORY,
        jwks_loader=lambda: {"keys": [{"kid": "k1", "kty": "RSA", "use": "sig"}]},
        now=lambda: 999999,
    )
    token = fake_jwt(valid_claims())
    audience = mod.marker_audience("079", 210, BASE, HEAD)
    assert verifier.verify(
        token, run_id=RUN, audience=audience, require_fresh=False
    )
    assert not verifier.verify(
        token, run_id=RUN, audience=audience, require_fresh=True
    )


def test_oidc_audience_binds_marker_payload(monkeypatch):
    monkeypatch.setattr(mod, "_rsa_rs256_valid", lambda *args: True)
    claims = valid_claims()
    verifier = mod.GitHubOIDCVerifier(
        REPOSITORY,
        jwks_loader=lambda: {
            "keys": [{"kid": "k1", "kty": "RSA", "use": "sig"}]
        },
        now=lambda: 1200,
    )
    token = fake_jwt(claims)
    forged_audience = mod.marker_audience("079", 210, BASE, NEXT)
    assert not verifier.verify(
        token, run_id=RUN, audience=forged_audience, require_fresh=True
    )


def test_commit_audience_is_bound_to_input_and_tree():
    expected = mod.commit_audience("079", 210, BASE, TREE)
    assert expected.startswith(f"{mod.COMMIT_OIDC_AUDIENCE_PREFIX}-")
    assert expected != mod.commit_audience("079", 210, HEAD, TREE)
    assert expected != mod.commit_audience("079", 210, BASE, "b" * 40)


def test_human_commit_after_no_change_can_be_bridged():
    comments = [
        marker(BASE, HEAD),
        marker(HEAD, HEAD),
        marker(HEAD, NEXT),
    ]
    checkpoint, terminal = mod.checkpoint_for(
        candidate(NEXT), comments, verifier=AcceptVerifier()
    )
    assert checkpoint == NEXT
    assert terminal is False


def test_workflow_contract_separates_validation_and_trusted_push():
    text = (ROOT / ".github/workflows/daily-development-continuation.yml").read_text()
    assert "JARVISOS_CONTINUATION_MODE" in text
    assert "vars.JARVISOS_CONTINUATION_MODE || 'OFF'" in text
    assert "validate:\n" in text and "push:\n" in text
    validate_block = text.split("  validate:\n", 1)[1].split("\n  push:\n", 1)[0]
    push_block = text.split("\n  push:\n", 1)[1].split("\n  record-marker:\n", 1)[0]
    assert "contents: read" in validate_block
    assert "contents: write" not in validate_block
    assert "contents: write" in push_block
    assert "pip install" not in push_block
    assert "pytest" not in push_block
    assert "git commit --no-verify" in push_block
    assert "persist-credentials: false" in push_block
    assert "trusted-continuation-validator.py" in push_block
    assert "python -I -S" in push_block
    assert "index_tree=$(git write-tree)" in push_block
    assert "--active-pr" in push_block
    assert "python scripts/daily_development_continuation.py validate" not in push_block


def test_workflow_runs_timed_bluecad_canary_before_push():
    text = (ROOT / ".github/workflows/daily-development-continuation.yml").read_text()
    validate_block = text.split("  validate:\n", 1)[1].split("\n  push:\n", 1)[0]
    assert "Run timed BLUECAD continuation canary" in validate_block
    assert "timeout 240s python -m pytest -q" in validate_block
    assert "tests/bluecad/test_manifest_determinism_canary.py" in validate_block
    assert "tests/bluecad/test_geometry_property_invariants.py" in validate_block
    assert "tests/bluecad/test_capped_manifold.py" in validate_block
    assert 'test "$status" = "0"' in validate_block
    assert 'test "$elapsed" -le 240' in validate_block


def test_workflow_oidc_authority_is_confined_to_trusted_jobs():
    text = (ROOT / ".github/workflows/daily-development-continuation.yml").read_text()
    generate_block = text.split("  generate-patch:\n", 1)[1].split("\n  validate:\n", 1)[0]
    push_block = text.split("  push:\n", 1)[1].split("\n  record-marker:\n", 1)[0]
    assert text.count("id-token: write") == 4
    assert "id-token: write" not in generate_block
    assert "id-token: write" in push_block
    assert "jarvisos-continuation-commit-v1-" in push_block
    assert "Jarvis-Continuation: v2" in push_block
    assert "Jarvis-OIDC:" in push_block
    assert "CONTINUATION_OIDC_TOKEN" in text
    marker_region = text.split("  record-marker:\n", 1)[1]
    assert "CLAUDE_CODE_OAUTH_TOKEN" not in marker_region


def test_workflow_shadow_cannot_reach_mutating_jobs():
    text = (ROOT / ".github/workflows/daily-development-continuation.yml").read_text()
    assert text.count("needs.plan.outputs.action == 'execute'") >= 5
    assert "needs.plan.outputs.action == 'recover'" in text
    assert "steps.plan.outputs.action == 'noop' || steps.plan.outputs.action == 'shadow'" in text
