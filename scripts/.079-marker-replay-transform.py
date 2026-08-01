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
    '''MARKER_RE = re.compile(
    r"<!-- jarvis-continuation:v2 spec=(?P<spec>\\d{3}[a-z]?) "
    r"pr=(?P<pr>\\d+) input=(?P<input>[0-9a-f]{40}) "
    r"output=(?P<output>[0-9a-f]{40}) result=(?P<result>changed|no_change) "
    r"run=(?P<run>\\d+) oidc=(?P<oidc>[A-Za-z0-9._-]+) -->",
    re.I,
)
''',
    '''MARKER_RE = re.compile(
    r"<!-- jarvis-continuation:v3 phase=(?P<phase>recover|bridge|final) "
    r"spec=(?P<spec>\\d{3}[a-z]?) pr=(?P<pr>\\d+) "
    r"input=(?P<input>[0-9a-f]{40}) output=(?P<output>[0-9a-f]{40}) "
    r"result=(?P<result>changed|no_change) run=(?P<run>\\d+) "
    r"oidc=(?P<oidc>[A-Za-z0-9._-]+) -->",
    re.I,
)
''',
)

replace_once(
    CONTROL,
    'PROTECTED_BRANCHES = {"master", "main"}\n',
    'PROTECTED_BRANCHES = {"master", "main"}\nMARKER_PHASE_RANK = {"recover": 0, "bridge": 1, "final": 2}\n',
)

replace_once(
    CONTROL,
    '''def marker_audience(
    spec: str, pr: int, input_head: str, output_head: str
) -> str:
    result = "changed" if input_head != output_head else "no_change"
    canonical = (
        f"v2|spec={spec.lower()}|pr={pr}|input={input_head}|"
        f"output={output_head}|result={result}"
    )
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return f"{MARKER_OIDC_AUDIENCE_PREFIX}-{digest}"
''',
    '''def marker_audience(
    spec: str,
    pr: int,
    input_head: str,
    output_head: str,
    phase: str = "final",
) -> str:
    if phase not in MARKER_PHASE_RANK:
        raise ContinuationError("marker phase is invalid")
    result = "changed" if input_head != output_head else "no_change"
    canonical = (
        f"v3|phase={phase}|spec={spec.lower()}|pr={pr}|input={input_head}|"
        f"output={output_head}|result={result}"
    )
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return f"{MARKER_OIDC_AUDIENCE_PREFIX}-{digest}"
''',
)

replace_once(
    CONTROL,
    '''def marker_text(
    spec: str,
    pr: int,
    input_head: str,
    output_head: str,
    run_id: str,
    oidc_token: str,
) -> str:
    result = "changed" if input_head != output_head else "no_change"
    return (
        f"<!-- jarvis-continuation:v2 spec={spec} pr={pr} input={input_head} "
        f"output={output_head} result={result} run={run_id} oidc={oidc_token} -->"
    )
''',
    '''def marker_text(
    spec: str,
    pr: int,
    input_head: str,
    output_head: str,
    run_id: str,
    oidc_token: str,
    phase: str = "final",
) -> str:
    if phase not in MARKER_PHASE_RANK:
        raise ContinuationError("marker phase is invalid")
    result = "changed" if input_head != output_head else "no_change"
    return (
        f"<!-- jarvis-continuation:v3 phase={phase} spec={spec} pr={pr} "
        f"input={input_head} output={output_head} result={result} "
        f"run={run_id} oidc={oidc_token} -->"
    )
''',
)

replace_once(
    CONTROL,
    '''            audience = marker_audience(
                match.group("spec"),
                int(match.group("pr")),
                match.group("input"),
                match.group("output"),
            )
''',
    '''            audience = marker_audience(
                match.group("spec"),
                int(match.group("pr")),
                match.group("input"),
                match.group("output"),
                match.group("phase"),
            )
''',
)

replace_once(
    CONTROL,
    '''    if not matches:
        return candidate.base_sha, False
    latest = matches[-1]
    input_head, output_head, result = (
        latest.group("input"),
        latest.group("output"),
        latest.group("result"),
    )
''',
    '''    if not matches:
        return candidate.base_sha, False
    ordered: dict[tuple[int, int], re.Match[str]] = {}
    payloads: dict[tuple[int, int], tuple[str, str, str]] = {}
    for match in matches:
        key = (int(match.group("run")), MARKER_PHASE_RANK[match.group("phase")])
        payload = (
            match.group("input"),
            match.group("output"),
            match.group("result"),
        )
        if key in payloads and payloads[key] != payload:
            raise ContinuationError(
                "conflicting authenticated markers share one run and phase"
            )
        payloads[key] = payload
        ordered[key] = match
    latest = ordered[max(ordered)]
    input_head, output_head, result = (
        latest.group("input"),
        latest.group("output"),
        latest.group("result"),
    )
''',
)

replace_once(
    CONTROL,
    '''    marker.add_argument("--run-id", default=os.getenv("GITHUB_RUN_ID", ""))
    marker.add_argument("--spec", required=True)
''',
    '''    marker.add_argument("--run-id", default=os.getenv("GITHUB_RUN_ID", ""))
    marker.add_argument("--phase", choices=tuple(MARKER_PHASE_RANK), required=True)
    marker.add_argument("--spec", required=True)
''',
)

replace_once(
    CONTROL,
    '''        audience = marker_audience(
            args.spec, args.pr, args.input_head, args.output_head
        )
''',
    '''        audience = marker_audience(
            args.spec, args.pr, args.input_head, args.output_head, args.phase
        )
''',
)

replace_once(
    CONTROL,
    '''                args.spec.lower(), args.pr, args.input_head, args.output_head,
                args.run_id, args.oidc_token,
''',
    '''                args.spec.lower(), args.pr, args.input_head, args.output_head,
                args.run_id, args.oidc_token, args.phase,
''',
)

replace_once(
    TESTS,
    '''            token == "valid.jwt.token"
            and run_id == RUN
            and audience.startswith(
''',
    '''            token == "valid.jwt.token"
            and run_id.isdigit()
            and audience.startswith(
''',
)

replace_once(
    TESTS,
    '''def marker(input_head=BASE, output_head=HEAD, token="valid.jwt.token", run=RUN, actor="github-actions[bot]"):
    return {
        "body": mod.marker_text("079", 210, input_head, output_head, run, token),
        "user": {"login": actor},
    }
''',
    '''def marker(
    input_head=BASE,
    output_head=HEAD,
    token="valid.jwt.token",
    run=RUN,
    actor="github-actions[bot]",
    phase="final",
):
    return {
        "body": mod.marker_text(
            "079", 210, input_head, output_head, run, token, phase
        ),
        "user": {"login": actor},
    }
''',
)

replace_once(
    TESTS,
    '''def test_bridge_then_no_change_is_terminal():
    comments = [marker(BASE, HEAD), marker(HEAD, HEAD)]
''',
    '''def test_bridge_then_no_change_is_terminal():
    comments = [
        marker(BASE, HEAD, phase="bridge"),
        marker(HEAD, HEAD, phase="final"),
    ]
''',
)

replace_once(
    TESTS,
    '''def test_latest_authenticated_marker_supersedes_older_edges():
    comments = [marker(BASE, HEAD), marker(BASE, NEXT)]
''',
    '''def test_latest_authenticated_marker_supersedes_older_edges():
    comments = [marker(BASE, HEAD, run="12344"), marker(BASE, NEXT)]
''',
)

replace_once(
    TESTS,
    '''def test_duplicate_marker_is_idempotent():
''',
    '''def test_replayed_older_run_posted_last_cannot_roll_back_checkpoint():
    comments = [
        marker(BASE, NEXT, run="12346"),
        marker(BASE, HEAD, run="12344"),
    ]
    checkpoint, terminal = mod.checkpoint_for(
        candidate(NEXT), comments, verifier=AcceptVerifier(),
    )
    assert checkpoint == NEXT
    assert terminal is False


def test_replayed_bridge_after_same_run_final_cannot_roll_back_checkpoint():
    comments = [
        marker(HEAD, NEXT, run="12346", phase="final"),
        marker(BASE, HEAD, run="12346", phase="bridge"),
    ]
    checkpoint, terminal = mod.checkpoint_for(
        candidate(NEXT), comments, verifier=AcceptVerifier(),
    )
    assert checkpoint == NEXT
    assert terminal is False


def test_conflicting_same_run_and_phase_markers_fail_closed():
    comments = [
        marker(BASE, HEAD),
        marker(BASE, NEXT),
    ]
    with pytest.raises(mod.ContinuationError, match="run and phase"):
        mod.checkpoint_for(
            candidate(NEXT), comments, verifier=AcceptVerifier(),
        )


def test_duplicate_marker_is_idempotent():
''',
)

replace_once(
    TESTS,
    '''def test_oidc_audience_binds_marker_payload(monkeypatch):
''',
    '''def test_marker_audience_binds_phase():
    assert mod.marker_audience("079", 210, BASE, HEAD, "bridge") != mod.marker_audience(
        "079", 210, BASE, HEAD, "final"
    )


def test_oidc_audience_binds_marker_payload(monkeypatch):
''',
)

replace_once(
    TESTS,
    '''    comments = [
        marker(BASE, HEAD),
        marker(HEAD, HEAD),
        marker(HEAD, NEXT),
    ]
''',
    '''    comments = [
        marker(BASE, HEAD, run="12344"),
        marker(HEAD, HEAD, run="12345"),
        marker(HEAD, NEXT, run="12346", phase="bridge"),
    ]
''',
)

replace_once(
    TESTS,
    '''    assert "CONTINUATION_OIDC_TOKEN" in text
    marker_region = text.split("  record-marker:\\n", 1)[1]
''',
    '''    assert "CONTINUATION_OIDC_TOKEN" in text
    assert "v3|phase=recover|" in text
    assert "v3|phase=bridge|" in text
    assert "v3|phase=final|" in text
    assert '--phase "recover"' in text
    assert '--phase "bridge"' in text
    assert '--phase "final"' in text
    marker_region = text.split("  record-marker:\\n", 1)[1]
''',
)

replace_once(
    WORKFLOW,
    'payload="v2|spec=${{ needs.plan.outputs.spec_id }}|pr=${{ needs.plan.outputs.pr_number }}|input=${{ needs.plan.outputs.checkpoint_sha }}|output=${{ needs.plan.outputs.recovery_output_sha }}|result=changed"',
    'payload="v3|phase=recover|spec=${{ needs.plan.outputs.spec_id }}|pr=${{ needs.plan.outputs.pr_number }}|input=${{ needs.plan.outputs.checkpoint_sha }}|output=${{ needs.plan.outputs.recovery_output_sha }}|result=changed"',
)

replace_once(
    WORKFLOW,
    '''            --spec "${{ needs.plan.outputs.spec_id }}" \\
            --pr "${{ needs.plan.outputs.pr_number }}" \\
            --input-head "${{ needs.plan.outputs.checkpoint_sha }}" \\
            --output-head "${{ needs.plan.outputs.recovery_output_sha }}"
''',
    '''            --phase "recover" \\
            --spec "${{ needs.plan.outputs.spec_id }}" \\
            --pr "${{ needs.plan.outputs.pr_number }}" \\
            --input-head "${{ needs.plan.outputs.checkpoint_sha }}" \\
            --output-head "${{ needs.plan.outputs.recovery_output_sha }}"
''',
)

replace_once(
    WORKFLOW,
    'payload="v2|spec=${{ needs.plan.outputs.spec_id }}|pr=${{ needs.plan.outputs.pr_number }}|input=${{ needs.plan.outputs.checkpoint_sha }}|output=${{ needs.plan.outputs.head_sha }}|result=changed"',
    'payload="v3|phase=bridge|spec=${{ needs.plan.outputs.spec_id }}|pr=${{ needs.plan.outputs.pr_number }}|input=${{ needs.plan.outputs.checkpoint_sha }}|output=${{ needs.plan.outputs.head_sha }}|result=changed"',
)

replace_once(
    WORKFLOW,
    '''            --spec "${{ needs.plan.outputs.spec_id }}" \\
            --pr "${{ needs.plan.outputs.pr_number }}" \\
            --input-head "${{ needs.plan.outputs.checkpoint_sha }}" \\
            --output-head "${{ needs.plan.outputs.head_sha }}"
''',
    '''            --phase "bridge" \\
            --spec "${{ needs.plan.outputs.spec_id }}" \\
            --pr "${{ needs.plan.outputs.pr_number }}" \\
            --input-head "${{ needs.plan.outputs.checkpoint_sha }}" \\
            --output-head "${{ needs.plan.outputs.head_sha }}"
''',
)

replace_once(
    WORKFLOW,
    'payload="v2|spec=${{ needs.plan.outputs.spec_id }}|pr=${{ needs.plan.outputs.pr_number }}|input=${{ needs.plan.outputs.head_sha }}|output=${{ needs.push.outputs.output_head }}|result=$result"',
    'payload="v3|phase=final|spec=${{ needs.plan.outputs.spec_id }}|pr=${{ needs.plan.outputs.pr_number }}|input=${{ needs.plan.outputs.head_sha }}|output=${{ needs.push.outputs.output_head }}|result=$result"',
)

replace_once(
    WORKFLOW,
    '''            --spec "${{ needs.plan.outputs.spec_id }}" \\
            --pr "${{ needs.plan.outputs.pr_number }}" \\
            --input-head "${{ needs.plan.outputs.head_sha }}" \\
            --output-head "${{ needs.push.outputs.output_head }}"
''',
    '''            --phase "final" \\
            --spec "${{ needs.plan.outputs.spec_id }}" \\
            --pr "${{ needs.plan.outputs.pr_number }}" \\
            --input-head "${{ needs.plan.outputs.head_sha }}" \\
            --output-head "${{ needs.push.outputs.output_head }}"
''',
)
