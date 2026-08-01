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
    '''def checkpoint_for(
    candidate: Candidate,
    comments: list[dict[str, object]],
    *,
    verifier: MarkerVerifier,
) -> tuple[str, bool]:
    matches = _verified_markers(
        comments,
        spec=candidate.spec_id,
        pr=candidate.pr_number,
        verifier=verifier,
    )
    if not matches:
        return candidate.base_sha, False
    changed_edges: dict[str, str] = {}
    no_change_inputs: set[str] = set()
    all_inputs: set[str] = set()
    for match in matches:
        input_head, output_head, result = (
            match.group("input"),
            match.group("output"),
            match.group("result"),
        )
        all_inputs.add(input_head)
        if result == "no_change":
            if output_head != input_head:
                raise ContinuationError("no-change marker changed the checkpoint")
            no_change_inputs.add(input_head)
            continue
        if output_head == input_head:
            raise ContinuationError("changed marker did not advance the checkpoint")
        if input_head in changed_edges and changed_edges[input_head] != output_head:
            raise ContinuationError(
                "incompatible continuation markers share one input head"
            )
        changed_edges[input_head] = output_head
    checkpoint = candidate.base_sha
    seen: set[str] = set()
    while checkpoint in changed_edges:
        if checkpoint in seen:
            raise ContinuationError("continuation marker chain contains a cycle")
        seen.add(checkpoint)
        checkpoint = changed_edges[checkpoint]
    reachable_inputs = seen | {checkpoint}
    if all_inputs - reachable_inputs:
        raise ContinuationError("continuation marker chain is not contiguous")
    terminal = checkpoint in no_change_inputs and checkpoint not in changed_edges
    return checkpoint, terminal and checkpoint == candidate.head_sha
''',
    '''def checkpoint_for(
    candidate: Candidate,
    comments: list[dict[str, object]],
    *,
    verifier: MarkerVerifier,
) -> tuple[str, bool]:
    matches = _verified_markers(
        comments,
        spec=candidate.spec_id,
        pr=candidate.pr_number,
        verifier=verifier,
    )
    if not matches:
        return candidate.base_sha, False
    latest = matches[-1]
    input_head, output_head, result = (
        latest.group("input"),
        latest.group("output"),
        latest.group("result"),
    )
    if result == "no_change":
        if output_head != input_head:
            raise ContinuationError("no-change marker changed the checkpoint")
    elif output_head == input_head:
        raise ContinuationError("changed marker did not advance the checkpoint")
    terminal = result == "no_change" and output_head == candidate.head_sha
    return output_head, terminal
''',
)

replace_once(
    CONTROL,
    '''def validate_changed_paths(paths: list[str], active_spec: str) -> None:
''',
    '''def read_nul_paths(path: Path) -> list[str]:
    raw = path.read_bytes()
    if not raw:
        return []
    if not raw.endswith(b"\\0"):
        raise ContinuationError("changed-files stream is not NUL-terminated")
    records = raw[:-1].split(b"\\0")
    if any(not record for record in records):
        raise ContinuationError("changed-files stream contains an empty path")
    try:
        return [record.decode("utf-8") for record in records]
    except UnicodeDecodeError as exc:
        raise ContinuationError("changed-files stream contains a non-UTF-8 path") from exc


def validate_changed_paths(paths: list[str], active_spec: str) -> None:
''',
)

replace_once(
    CONTROL,
    '''            paths = [line for line in args.changed_files.read_text(encoding="utf-8").splitlines() if line]
            validate_changed_paths(paths, args.active_spec.lower())
''',
    '''            paths = read_nul_paths(args.changed_files)
            validate_changed_paths(paths, args.active_spec.lower())
''',
)

replace_once(
    TESTS,
    '''class RejectVerifier:
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
''',
    '''class RejectVerifier:
    def verify(
        self,
        token: str,
        *,
        run_id: str,
        audience: str,
        require_fresh: bool = False,
    ) -> bool:
        return False


class CurrentKeyVerifier:
    def verify(
        self,
        token: str,
        *,
        run_id: str,
        audience: str,
        require_fresh: bool = False,
    ) -> bool:
        return token == "current.jwt.token" and run_id == RUN


class FakeReader:
''',
)

replace_once(
    TESTS,
    '''def test_floating_no_change_marker_fails_closed():
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
''',
    '''def test_latest_no_change_marker_at_head_is_terminal():
    checkpoint, terminal = mod.checkpoint_for(
        candidate(), [marker(input_head=HEAD, output_head=HEAD)],
        verifier=AcceptVerifier(),
    )
    assert checkpoint == HEAD
    assert terminal is True


def test_bridge_then_no_change_is_terminal():
    comments = [marker(BASE, HEAD), marker(HEAD, HEAD)]
    checkpoint, terminal = mod.checkpoint_for(
        candidate(), comments, verifier=AcceptVerifier(),
    )
    assert checkpoint == HEAD
    assert terminal is True


def test_latest_authenticated_marker_supersedes_older_edges():
    comments = [marker(BASE, HEAD), marker(BASE, NEXT)]
    checkpoint, terminal = mod.checkpoint_for(
        candidate(NEXT), comments, verifier=AcceptVerifier(),
    )
    assert checkpoint == NEXT
    assert terminal is False


def test_latest_valid_marker_reanchors_after_retired_oidc_key():
    comments = [
        marker(BASE, HEAD, token="retired.jwt.token"),
        marker(HEAD, NEXT, token="current.jwt.token"),
    ]
    checkpoint, terminal = mod.checkpoint_for(
        candidate(NEXT), comments, verifier=CurrentKeyVerifier(),
    )
    assert checkpoint == NEXT
    assert terminal is False


def test_build_plan_rejects_disconnected_latest_anchor():
    reader = FakeReader(
        comments=[marker(SIDE, NEXT)],
        compares={(BASE, HEAD): "ahead", (NEXT, HEAD): "behind"},
    )
    with pytest.raises(mod.ContinuationError, match="does not descend from the checkpoint"):
        mod.build_plan(
            mode="SHADOW", repository=REPOSITORY, reader=reader,
            token_present=False, verifier=AcceptVerifier(),
        )


def test_duplicate_marker_is_idempotent():
''',
)

replace_once(
    TESTS,
    '''def test_too_many_paths_fail():
    with pytest.raises(mod.ContinuationError, match="too many"):
        mod.validate_changed_paths([f"docs/{i}.md" for i in range(21)], "079")


def test_status_only_active_row_may_change_when_binding_is_preserved():
''',
    '''def test_too_many_paths_fail():
    with pytest.raises(mod.ContinuationError, match="too many"):
        mod.validate_changed_paths([f"docs/{i}.md" for i in range(21)], "079")


@pytest.mark.parametrize("separator", ["\\n", "\\t"])
def test_nul_path_stream_preserves_control_characters_and_rejects_protected_path(
    tmp_path, separator
):
    changed = tmp_path / "changed-files.z"
    changed.write_bytes(f".github/workflows/evil{separator}.yml".encode() + b"\\0")
    paths = mod.read_nul_paths(changed)
    assert paths == [f".github/workflows/evil{separator}.yml"]
    with pytest.raises(mod.ContinuationError, match="protected path"):
        mod.validate_changed_paths(paths, "079")


def test_nul_path_stream_must_be_terminated(tmp_path):
    changed = tmp_path / "changed-files.z"
    changed.write_bytes(b"backend/app/service.py")
    with pytest.raises(mod.ContinuationError, match="NUL-terminated"):
        mod.read_nul_paths(changed)


def test_status_only_active_row_may_change_when_binding_is_preserved():
''',
)

replace_once(
    TESTS,
    '''def test_workflow_runs_timed_bluecad_canary_before_push():
''',
    '''def test_workflow_uses_raw_nul_delimited_paths_in_both_workspaces():
    text = (ROOT / ".github/workflows/daily-development-continuation.yml").read_text()
    validate_block = text.split("  validate:\\n", 1)[1].split("\\n  push:\\n", 1)[0]
    push_block = text.split("\\n  push:\\n", 1)[1].split("\\n  record-marker:\\n", 1)[0]
    assert validate_block.count("--name-only -z") == 1
    assert push_block.count("--name-only -z") == 1
    assert "changed-files.z" in validate_block
    assert "changed-files.z" in push_block
    assert "changed-files.txt" not in validate_block
    assert "changed-files.txt" not in push_block


def test_workflow_runs_timed_bluecad_canary_before_push():
''',
)

replace_once(
    WORKFLOW,
    '''          if [ ! -s "$patch" ]; then
            : > "$RUNNER_TEMP/changed-files.txt"
            echo "has_changes=false" >> "$GITHUB_OUTPUT"
            echo "frontend_changed=false" >> "$GITHUB_OUTPUT"
            exit 0
          fi
          git apply --index --whitespace=error-all "$patch"
          git diff --cached --no-renames --name-only > "$RUNNER_TEMP/changed-files.txt"
          count=$(grep -c . "$RUNNER_TEMP/changed-files.txt" || true)
          test "$count" -le 20
          if [ "$count" -eq 0 ]; then
            echo "has_changes=false" >> "$GITHUB_OUTPUT"
            echo "frontend_changed=false" >> "$GITHUB_OUTPUT"
            exit 0
          fi
          echo "has_changes=true" >> "$GITHUB_OUTPUT"
          if grep -q '^frontend/' "$RUNNER_TEMP/changed-files.txt"; then
            echo "frontend_changed=true" >> "$GITHUB_OUTPUT"
          else
            echo "frontend_changed=false" >> "$GITHUB_OUTPUT"
          fi
          cp docs/specs/STATUS.md "$RUNNER_TEMP/status-after.md"
          python scripts/daily_development_continuation.py validate \\
            --changed-files "$RUNNER_TEMP/changed-files.txt" \\
''',
    '''          if [ ! -s "$patch" ]; then
            : > "$RUNNER_TEMP/changed-files.z"
            echo "has_changes=false" >> "$GITHUB_OUTPUT"
            echo "frontend_changed=false" >> "$GITHUB_OUTPUT"
            exit 0
          fi
          git apply --index --whitespace=error-all "$patch"
          git diff --cached --no-renames --name-only -z > "$RUNNER_TEMP/changed-files.z"
          count=$(python - "$RUNNER_TEMP/changed-files.z" <<'PY'
          from pathlib import Path
          import sys
          raw = Path(sys.argv[1]).read_bytes()
          records = [record for record in raw.split(b"\\0") if record]
          print(len(records))
          PY
          )
          test "$count" -le 20
          if [ "$count" -eq 0 ]; then
            echo "has_changes=false" >> "$GITHUB_OUTPUT"
            echo "frontend_changed=false" >> "$GITHUB_OUTPUT"
            exit 0
          fi
          echo "has_changes=true" >> "$GITHUB_OUTPUT"
          if python - "$RUNNER_TEMP/changed-files.z" <<'PY'
          from pathlib import Path
          import sys
          records = [record for record in Path(sys.argv[1]).read_bytes().split(b"\\0") if record]
          raise SystemExit(0 if any(record.startswith(b"frontend/") for record in records) else 1)
          PY
          then
            echo "frontend_changed=true" >> "$GITHUB_OUTPUT"
          else
            echo "frontend_changed=false" >> "$GITHUB_OUTPUT"
          fi
          cp docs/specs/STATUS.md "$RUNNER_TEMP/status-after.md"
          python scripts/daily_development_continuation.py validate \\
            --changed-files "$RUNNER_TEMP/changed-files.z" \\
''',
)

replace_once(
    WORKFLOW,
    '''          git apply --index --whitespace=error-all "$RUNNER_TEMP/continuation/continuation.patch"
          git diff --cached --no-renames --name-only > "$RUNNER_TEMP/changed-files.txt"
          cp docs/specs/STATUS.md "$RUNNER_TEMP/status-after.md"
          index_tree=$(git write-tree)
          python -I -S "$RUNNER_TEMP/trusted-continuation-validator.py" validate \\
            --changed-files "$RUNNER_TEMP/changed-files.txt" \\
''',
    '''          git apply --index --whitespace=error-all "$RUNNER_TEMP/continuation/continuation.patch"
          git diff --cached --no-renames --name-only -z > "$RUNNER_TEMP/changed-files.z"
          cp docs/specs/STATUS.md "$RUNNER_TEMP/status-after.md"
          index_tree=$(git write-tree)
          python -I -S "$RUNNER_TEMP/trusted-continuation-validator.py" validate \\
            --changed-files "$RUNNER_TEMP/changed-files.z" \\
''',
)
