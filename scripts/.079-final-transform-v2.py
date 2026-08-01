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
    "def validate_changed_paths(paths: list[str]) -> None:\n",
    "def validate_changed_paths(paths: list[str], active_spec: str) -> None:\n",
)

replace_once(
    CONTROL,
    '        if path.startswith("backend/tests/") and Path(path).name.startswith("test_") and Path(path).name.endswith("_conformance.py"):\n',
    (
        '        if path.startswith("docs/specs/") and path != "docs/specs/STATUS.md":\n'
        '            filename = path.removeprefix("docs/specs/")\n'
        '            if "/" in filename or not filename.startswith(f"{active_spec.lower()}-"):\n'
        '                raise ContinuationError(\n'
        '                    f"continuation patch changes a non-active specification: {raw_path}"\n'
        '                )\n'
        '        if path.startswith("backend/tests/") and Path(path).name.startswith("test_") and Path(path).name.endswith("_conformance.py"):\n'
    ),
)

replace_once(
    CONTROL,
    (
        '    if active_after.status != "in_review" or active_after.prs != (active_pr,):\n'
        '        raise ContinuationError(\n'
        '            "active STATUS.md row must remain in_review and bound to the active PR"\n'
        '        )\n'
        '    prefix = f"| {active_spec} |"\n'
    ),
    (
        '    if active_after.status != "in_review" or active_after.prs != (active_pr,):\n'
        '        raise ContinuationError(\n'
        '            "active STATUS.md row must remain in_review and bound to the active PR"\n'
        '        )\n'
        '    if active_after.depends_on != before_rows[active_spec].depends_on:\n'
        '        raise ContinuationError(\n'
        '            "active STATUS.md dependencies may not change during continuation"\n'
        '        )\n'
        '    prefix = f"| {active_spec} |"\n'
    ),
)

replace_once(
    CONTROL,
    "            validate_changed_paths(paths)\n",
    "            validate_changed_paths(paths, args.active_spec.lower())\n",
)

replace_once(
    TESTS,
    (
        'def test_protected_and_sensitive_paths_are_rejected(path):\n'
        '    with pytest.raises(mod.ContinuationError):\n'
        '        mod.validate_changed_paths([path])\n'
    ),
    (
        'def test_protected_and_sensitive_paths_are_rejected(path):\n'
        '    with pytest.raises(mod.ContinuationError):\n'
        '        mod.validate_changed_paths([path], "079")\n'
    ),
)

replace_once(
    TESTS,
    (
        'def test_maintainer_owned_conformance_tests_are_rejected(path):\n'
        '    with pytest.raises(mod.ContinuationError, match="maintainer-owned conformance test"):\n'
        '        mod.validate_changed_paths([path])\n'
    ),
    (
        'def test_maintainer_owned_conformance_tests_are_rejected(path):\n'
        '    with pytest.raises(mod.ContinuationError, match="maintainer-owned conformance test"):\n'
        '        mod.validate_changed_paths([path], "079")\n'
    ),
)

replace_once(
    TESTS,
    (
        'def test_allowed_paths_pass():\n'
        '    mod.validate_changed_paths(\n'
        '        [\n'
        '            "backend/app/service.py",\n'
        '            "backend/tests/test_service.py",\n'
        '            "docs/specs/STATUS.md",\n'
        '        ]\n'
        '    )\n'
        '\n'
        '\n'
        'def test_too_many_paths_fail():\n'
    ),
    (
        'def test_allowed_paths_pass():\n'
        '    mod.validate_changed_paths(\n'
        '        [\n'
        '            "backend/app/service.py",\n'
        '            "backend/tests/test_service.py",\n'
        '            "docs/specs/STATUS.md",\n'
        '            "docs/specs/079-autonomous-development-loop-0.md",\n'
        '        ],\n'
        '        "079",\n'
        '    )\n'
        '\n'
        '\n'
        '@pytest.mark.parametrize(\n'
        '    "path",\n'
        '    [\n'
        '        "docs/specs/080-autonomous-review-repair-0.md",\n'
        '        "docs/specs/078-bluecad-complex-system-reference-architecture.md",\n'
        '        "docs/specs/archive/079-old.md",\n'
        '    ],\n'
        ')\n'
        'def test_non_active_specification_paths_are_rejected(path):\n'
        '    with pytest.raises(mod.ContinuationError, match="non-active specification"):\n'
        '        mod.validate_changed_paths([path], "079")\n'
        '\n'
        '\n'
        'def test_too_many_paths_fail():\n'
    ),
)

replace_once(
    TESTS,
    '        mod.validate_changed_paths([f"docs/{i}.md" for i in range(21)])\n',
    '        mod.validate_changed_paths([f"docs/{i}.md" for i in range(21)], "079")\n',
)

replace_once(
    TESTS,
    "def test_status_prose_change_fails():\n",
    (
        'def test_status_dependencies_may_not_change():\n'
        '    before = registry()\n'
        '    after = before.replace("| CONTINUE | 004 | active |", "| CONTINUE | 080 | active |")\n'
        '    with pytest.raises(mod.ContinuationError, match="dependencies may not change"):\n'
        '        mod.validate_status_change(before, after, "079", 210)\n'
        '\n'
        '\n'
        'def test_status_prose_change_fails():\n'
    ),
)

replace_once(
    TESTS,
    "def test_workflow_oidc_authority_is_confined_to_trusted_jobs():\n",
    (
        'def test_workflow_runs_timed_bluecad_canary_before_push():\n'
        '    text = (ROOT / ".github/workflows/daily-development-continuation.yml").read_text()\n'
        '    validate_block = text.split("  validate:\\n", 1)[1].split("\\n  push:\\n", 1)[0]\n'
        '    assert "Run timed BLUECAD continuation canary" in validate_block\n'
        '    assert "timeout 240s python -m pytest -q" in validate_block\n'
        '    assert "tests/bluecad/test_manifest_determinism_canary.py" in validate_block\n'
        '    assert "tests/bluecad/test_geometry_property_invariants.py" in validate_block\n'
        '    assert "tests/bluecad/test_capped_manifold.py" in validate_block\n'
        '    assert \'test "$status" = "0"\' in validate_block\n'
        '    assert \'test "$elapsed" -le 240\' in validate_block\n'
        '\n'
        '\n'
        'def test_workflow_oidc_authority_is_confined_to_trusted_jobs():\n'
    ),
)

replace_once(
    WORKFLOW,
    "      - name: Run deterministic gates\n",
    (
        '      - name: Run timed BLUECAD continuation canary\n'
        "        if: ${{ steps.inspect.outputs.has_changes == 'true' }}\n"
        '        working-directory: backend\n'
        '        shell: bash\n'
        '        run: |\n'
        '          set -o pipefail\n'
        '          set +e\n'
        '          SECONDS=0\n'
        '          timeout 240s python -m pytest -q \\\n'
        '            tests/bluecad/test_manifest_determinism_canary.py \\\n'
        '            tests/bluecad/test_geometry_property_invariants.py \\\n'
        '            tests/bluecad/test_capped_manifold.py \\\n'
        '            2>&1 | tee "$RUNNER_TEMP/bluecad-continuation-canary.log"\n'
        '          status=${PIPESTATUS[0]}\n'
        '          elapsed=$SECONDS\n'
        '          set -e\n'
        '          test "$status" = "0"\n'
        '          test "$elapsed" -le 240\n'
        '\n'
        '      - name: Run deterministic gates\n'
    ),
)
