from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    target = Path(path)
    text = target.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected one match, found {count}")
    target.write_text(text.replace(old, new, 1), encoding="utf-8")


CONTROL = "scripts/daily_development_continuation.py"
TESTS = "backend/tests/test_daily_development_continuation.py"
WORKFLOW = ".github/workflows/daily-development-continuation.yml"

replace_once(
    CONTROL,
    '''        if row.prs != (number,):
            raise ContinuationError(f"PR #{number} registry does not bind itself exactly")
        binding_text = " ".join(str(pull.get(key) or "") for key in ("title", "body"))
''',
    '''        if row.prs != (number,):
            raise ContinuationError(f"PR #{number} registry does not bind itself exactly")
        dependencies = list(
            dict.fromkeys(
                value.lower() for value in SPEC_BINDING_RE.findall(row.depends_on)
            )
        )
        unmet = []
        for dependency in dependencies:
            dependency_row = registry.get(dependency)
            if dependency_row is None:
                unmet.append(f"{dependency}=absent")
            elif dependency_row.status != "merged":
                unmet.append(f"{dependency}={dependency_row.status}")
        if unmet:
            raise ContinuationError(
                f"PR #{number} active spec has unmerged dependencies: "
                + ", ".join(unmet)
            )
        binding_text = " ".join(str(pull.get(key) or "") for key in ("title", "body"))
''',
)

replace_once(
    TESTS,
    '''        "| --- | --- | --- | --- | --- | --- |\\n"
        f"| 079 | {status} | https://github.com/{REPOSITORY}/pull/{pr} | CONTINUE | 004 | active |\\n"
''',
    '''        "| --- | --- | --- | --- | --- | --- |\\n"
        "| 004 | merged | — | BASE | — | dependency |\\n"
        f"| 079 | {status} | https://github.com/{REPOSITORY}/pull/{pr} | CONTINUE | 004 | active |\\n"
''',
)

replace_once(
    TESTS,
    '''def test_missing_spec_binding_fails_closed():
''',
    '''def test_unmerged_dependency_fails_before_provider_execution():
    status = registry().replace("| CONTINUE | 004 | active |", "| CONTINUE | 080 | active |")
    reader = FakeReader(statuses={HEAD: status})
    with pytest.raises(mod.ContinuationError, match="080=planned"):
        mod.discover_candidate(REPOSITORY, reader)


def test_missing_dependency_fails_before_provider_execution():
    status = registry().replace("| CONTINUE | 004 | active |", "| CONTINUE | 099 | active |")
    reader = FakeReader(statuses={HEAD: status})
    with pytest.raises(mod.ContinuationError, match="099=absent"):
        mod.discover_candidate(REPOSITORY, reader)


def test_missing_spec_binding_fails_closed():
''',
)

replace_once(
    TESTS,
    '''    assert "python scripts/daily_development_continuation.py validate" not in push_block


def test_workflow_uses_raw_nul_delimited_paths_in_both_workspaces():
''',
    '''    assert "python scripts/daily_development_continuation.py validate" not in push_block
    assert "audience=$(python -I -S -c" in push_block
    assert "| python -I -S -c 'import json,sys;" in push_block
    assert 'test "$(git write-tree)" = "$tree_sha"' in push_block


def test_workflow_uses_raw_nul_delimited_paths_in_both_workspaces():
''',
)

replace_once(
    WORKFLOW,
    '''          audience=$(python -c 'import hashlib,sys; print("jarvisos-continuation-commit-v1-" + hashlib.sha256(sys.argv[1].encode()).hexdigest())' "$payload")
          url="${ACTIONS_ID_TOKEN_REQUEST_URL}&audience=$audience"
          commit_oidc_token=$(curl --fail --silent --show-error \\
            -H "Authorization: bearer ${ACTIONS_ID_TOKEN_REQUEST_TOKEN}" "$url" \\
            | python -c 'import json,sys; print(json.load(sys.stdin)["value"])')
          echo "::add-mask::$commit_oidc_token"
          git commit --no-verify \\
''',
    '''          audience=$(python -I -S -c 'import hashlib,sys; print("jarvisos-continuation-commit-v1-" + hashlib.sha256(sys.argv[1].encode()).hexdigest())' "$payload")
          url="${ACTIONS_ID_TOKEN_REQUEST_URL}&audience=$audience"
          commit_oidc_token=$(curl --fail --silent --show-error \\
            -H "Authorization: bearer ${ACTIONS_ID_TOKEN_REQUEST_TOKEN}" "$url" \\
            | python -I -S -c 'import json,sys; print(json.load(sys.stdin)["value"])')
          echo "::add-mask::$commit_oidc_token"
          test "$(git write-tree)" = "$tree_sha"
          git commit --no-verify \\
''',
)
