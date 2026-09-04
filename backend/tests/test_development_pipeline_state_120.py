from __future__ import annotations

import base64
import json
from collections.abc import Callable

import pytest

from app.modules.coding.pipeline_state import (
    DevelopmentPipelineStateService,
    PipelineStateInputError,
)
from app.modules.coding.repository_truth import (
    HttpResponse,
    RepositoryTruthError,
    RepositoryTruthResult,
    RepositoryTruthService,
)

REPOSITORY = "AlbertoRacerro/JarvisOS_v1"
HEAD = "a" * 40
BASE = "b" * 40
MASTER = "c" * 40
NEW_HEAD = "d" * 40
NEW_MASTER = "e" * 40
PR = 541


def truth(
    operation: str,
    payload: dict[str, object],
    *,
    sha: str | None = HEAD,
    partial: bool = False,
) -> RepositoryTruthResult:
    return RepositoryTruthResult(
        provider="github",
        repository=REPOSITORY,
        operation=operation,
        requested_ref=None,
        resolved_sha=sha,
        partial=partial,
        payload=payload,
        observed_at="2026-09-04T00:00:00+00:00",
    )


def status_text(status: str, implementation_pr: int | None = PR) -> str:
    pr_cell = "—" if implementation_pr is None else f"[#${implementation_pr}]".replace("$", "")
    return (
        "| Spec | Status | Implementation PR | Name | Depends on | Description |\n"
        "| --- | --- | --- | --- | --- | --- |\n"
        f"| 120 | {status} | {pr_cell} | DEVELOPMENT-PIPELINE-STATE-1 | 118 | x |\n"
    )


def stage_map(result: dict[str, object]) -> dict[str, dict[str, object]]:
    stages = result["stages"]
    assert isinstance(stages, list)
    return {
        str(stage["name"]): stage
        for stage in stages
        if isinstance(stage, dict) and "name" in stage
    }


def check_result(
    *,
    backend_status: str = "completed",
    backend_conclusion: str | None = "success",
    evidence_status: str = "completed",
    evidence_conclusion: str | None = "success",
    partial: bool = False,
) -> RepositoryTruthResult:
    return truth(
        "check_truth",
        {
            "check_runs": [
                {
                    "id": 1,
                    "name": "backend",
                    "status": backend_status,
                    "conclusion": backend_conclusion,
                    "head_sha": HEAD,
                    "stale": False,
                },
                {
                    "id": 2,
                    "name": "evidence",
                    "status": evidence_status,
                    "conclusion": evidence_conclusion,
                    "head_sha": HEAD,
                    "stale": False,
                },
            ]
        },
        partial=partial,
    )


def review_comment(
    *, verdict: str = "APPROVE", disposition: str = "PARK", head: str = HEAD, base: str = BASE
) -> dict[str, object]:
    marker = {
        "schema": "jarvis.claude-review.v3.2",
        "head_sha": head,
        "base_sha": base,
        "verdict": verdict,
        "findings": [{"severity": "P2", "disposition": disposition}],
    }
    return {"id": 9, "author": "claude", "body": "JARVIS_CLAUDE_REVIEW_V3_2_JSON:" + json.dumps(marker)}


class FakeTruth:
    def __init__(
        self,
        *,
        head_status: str = "in_review",
        master_status: str = "in_review",
        implementation_pr: int | None = PR,
        checks: RepositoryTruthResult | None = None,
        comments: RepositoryTruthResult | None = None,
        merged: bool = False,
        state: str = "open",
        head_moves: bool = False,
        base_moves: bool = False,
        master_moves: bool = False,
        malformed_status: str | None = None,
    ) -> None:
        self.head_status = head_status
        self.master_status = master_status
        self.implementation_pr = implementation_pr
        self.checks = checks or check_result()
        self.comments = comments or truth(
            "pull_request_comments_truth", {"comments": [review_comment()]}
        )
        self.merged = merged
        self.state = state
        self.head_moves = head_moves
        self.base_moves = base_moves
        self.master_moves = master_moves
        self.malformed_status = malformed_status
        self.pr_reads = 0
        self.master_reads = 0

    def pull_request_truth(self, repository: str, pr_number: int) -> RepositoryTruthResult:
        assert repository == REPOSITORY and pr_number == PR
        self.pr_reads += 1
        head = NEW_HEAD if self.head_moves and self.pr_reads > 1 else HEAD
        base = NEW_HEAD if self.base_moves and self.pr_reads > 1 else BASE
        return truth(
            "pull_request_truth",
            {
                "number": PR,
                "state": self.state,
                "draft": False,
                "merged": self.merged,
                "head_ref": "impl/120-development-pipeline-state",
                "head_sha": head,
                "base_ref": "master",
                "base_sha": base,
            },
            sha=head,
        )

    def file_preview(self, repository: str, ref: str, path: str) -> RepositoryTruthResult:
        assert repository == REPOSITORY
        assert path == "docs/specs/STATUS.md"
        if self.malformed_status is not None:
            text = self.malformed_status
        elif ref == HEAD:
            text = status_text(self.head_status, self.implementation_pr)
        else:
            text = status_text(self.master_status, self.implementation_pr)
        return truth("file_preview", {"text": text}, sha=ref)

    def check_truth(
        self, repository: str, pr_number: int, *, expected_head_sha: str
    ) -> RepositoryTruthResult:
        assert repository == REPOSITORY and pr_number == PR and expected_head_sha == HEAD
        return self.checks

    def pull_request_comments_truth(
        self, repository: str, pr_number: int, *, expected_head_sha: str
    ) -> RepositoryTruthResult:
        assert repository == REPOSITORY and pr_number == PR and expected_head_sha == HEAD
        return self.comments

    def repository_ref_truth(self, repository: str, ref: str) -> RepositoryTruthResult:
        assert repository == REPOSITORY and ref == "master"
        self.master_reads += 1
        sha = NEW_MASTER if self.master_moves and self.master_reads > 1 else MASTER
        return truth("repository_ref_truth", {"sha": sha}, sha=sha)


def inspect(subject: FakeTruth) -> dict[str, object]:
    return DevelopmentPipelineStateService(subject).inspect(  # type: ignore[arg-type]
        repository=REPOSITORY, pr_number=PR, spec_id="120"
    )


def test_exact_registry_and_green_evidence_complete_current_stages() -> None:
    stages = stage_map(inspect(FakeTruth()))
    assert stages["proposal"]["state"] == "complete"
    assert stages["plan"]["state"] == "complete"
    assert stages["implementation"]["state"] == "complete"
    assert stages["tests"]["state"] == "complete"
    assert stages["independent_review"]["state"] == "complete"
    assert stages["merge"]["state"] == "pending"
    assert stages["reconciliation"]["state"] == "not_applicable"


@pytest.mark.parametrize(
    ("status", "expected"),
    [("planned", "pending"), ("blocked", "blocked")],
)
def test_plan_comes_only_from_canonical_status(status: str, expected: str) -> None:
    stages = stage_map(inspect(FakeTruth(master_status=status, implementation_pr=None)))
    assert stages["plan"]["state"] == expected


@pytest.mark.parametrize(
    "text",
    [
        "no table here",
        "| 120 | in_review | [#541] | only-four |",
        status_text("in_review") + status_text("in_review"),
    ],
)
def test_missing_duplicate_or_malformed_status_is_unknown(text: str) -> None:
    stages = stage_map(inspect(FakeTruth(malformed_status=text)))
    assert stages["proposal"]["state"] == "unknown"
    assert stages["implementation"]["state"] == "unknown"


def test_wrong_registry_pr_never_completes_implementation() -> None:
    stages = stage_map(inspect(FakeTruth(implementation_pr=999)))
    assert stages["implementation"]["state"] == "unknown"


@pytest.mark.parametrize(
    ("subject", "stage", "expected"),
    [
        (FakeTruth(head_moves=True), "implementation", "stale"),
        (FakeTruth(head_moves=True), "tests", "stale"),
        (FakeTruth(base_moves=True), "independent_review", "stale"),
        (FakeTruth(master_moves=True), "reconciliation", "not_applicable"),
    ],
)
def test_identity_moves_fail_closed(subject: FakeTruth, stage: str, expected: str) -> None:
    assert stage_map(inspect(subject))[stage]["state"] == expected


@pytest.mark.parametrize(
    ("checks", "expected"),
    [
        (check_result(backend_status="in_progress", backend_conclusion=None), "pending"),
        (check_result(evidence_conclusion="failure"), "blocked"),
        (check_result(partial=True), "unknown"),
    ],
)
def test_test_gate_classification_is_conservative(
    checks: RepositoryTruthResult, expected: str
) -> None:
    assert stage_map(inspect(FakeTruth(checks=checks)))["tests"]["state"] == expected


def test_old_head_checks_cannot_complete_tests() -> None:
    checks = check_result()
    runs = checks.payload["check_runs"]
    assert isinstance(runs, list)
    for run in runs:
        assert isinstance(run, dict)
        run["head_sha"] = NEW_HEAD
        run["stale"] = True
    assert stage_map(inspect(FakeTruth(checks=checks)))["tests"]["state"] == "stale"


@pytest.mark.parametrize(
    ("comments", "expected"),
    [
        (
            truth(
                "pull_request_comments_truth",
                {"comments": [review_comment(verdict="REQUEST_CHANGES", disposition="BLOCK")]},
            ),
            "blocked",
        ),
        (
            truth(
                "pull_request_comments_truth",
                {"comments": [review_comment(head=NEW_HEAD)]},
            ),
            "stale",
        ),
        (
            truth("pull_request_comments_truth", {"comments": [{"id": 1, "body": "APPROVE"}]}),
            "unknown",
        ),
        (
            truth(
                "pull_request_comments_truth", {"comments": [review_comment()]}, partial=True
            ),
            "unknown",
        ),
    ],
)
def test_review_marker_requires_exact_structured_nonpartial_evidence(
    comments: RepositoryTruthResult, expected: str
) -> None:
    stage = stage_map(inspect(FakeTruth(comments=comments)))["independent_review"]
    assert stage["state"] == expected


@pytest.mark.parametrize(
    ("merged", "state", "master_status", "implementation_pr", "merge_state", "reconcile"),
    [
        (False, "open", "in_review", PR, "pending", "not_applicable"),
        (False, "closed", "in_review", PR, "blocked", "not_applicable"),
        (True, "closed", "in_review", PR, "complete", "pending"),
        (True, "closed", "merged", PR, "complete", "complete"),
        (True, "closed", "merged", 999, "complete", "unknown"),
    ],
)
def test_merge_and_reconciliation_are_exact_and_separate(
    merged: bool,
    state: str,
    master_status: str,
    implementation_pr: int,
    merge_state: str,
    reconcile: str,
) -> None:
    stages = stage_map(
        inspect(
            FakeTruth(
                merged=merged,
                state=state,
                master_status=master_status,
                implementation_pr=implementation_pr,
            )
        )
    )
    assert stages["merge"]["state"] == merge_state
    assert stages["reconciliation"]["state"] == reconcile


@pytest.mark.parametrize("pr_number", [0, -1])
def test_invalid_pr_number_is_rejected_before_truth_reads(pr_number: int) -> None:
    with pytest.raises(PipelineStateInputError):
        DevelopmentPipelineStateService(FakeTruth()).inspect(  # type: ignore[arg-type]
            repository=REPOSITORY, pr_number=pr_number, spec_id="120"
        )


@pytest.mark.parametrize("spec_id", ["", "12", "000", "120-x", "../../120"])
def test_invalid_spec_id_is_rejected_before_truth_reads(spec_id: str) -> None:
    with pytest.raises(PipelineStateInputError):
        DevelopmentPipelineStateService(FakeTruth()).inspect(  # type: ignore[arg-type]
            repository=REPOSITORY, pr_number=PR, spec_id=spec_id
        )


def http_response(payload: object, *, link: str | None = None) -> HttpResponse:
    headers = {} if link is None else {"link": link}
    return HttpResponse(status=200, headers=headers, body=json.dumps(payload).encode())


def test_repository_comment_truth_checks_head_and_projects_bounded_fields() -> None:
    long_body = "x" * 9000
    calls: list[str] = []

    def transport(path: str) -> HttpResponse:
        calls.append(path)
        if path == f"/repos/{REPOSITORY}/pulls/7":
            return http_response(
                {
                    "state": "open",
                    "draft": False,
                    "merged": False,
                    "head": {"ref": "feature", "sha": HEAD},
                    "base": {"ref": "master", "sha": BASE},
                }
            )
        if path == f"/repos/{REPOSITORY}/issues/7/comments?per_page=100":
            return http_response(
                [{"id": 3, "user": {"login": "reviewer"}, "body": long_body}],
                link='<next>; rel="next"',
            )
        raise AssertionError(path)

    service = RepositoryTruthService([REPOSITORY], transport=transport)
    result = service.pull_request_comments_truth(REPOSITORY, 7, expected_head_sha=HEAD)
    assert result.partial is True
    comments = result.payload["comments"]
    assert isinstance(comments, list)
    assert comments == [{"id": 3, "author": "reviewer", "body": "x" * 8192}]
    assert calls[-1].endswith("/issues/7/comments?per_page=100")


def test_repository_comment_truth_rejects_stale_head_before_comments_read() -> None:
    calls: list[str] = []

    def transport(path: str) -> HttpResponse:
        calls.append(path)
        return http_response(
            {
                "state": "open",
                "draft": False,
                "merged": False,
                "head": {"ref": "feature", "sha": NEW_HEAD},
                "base": {"ref": "master", "sha": BASE},
            }
        )

    service = RepositoryTruthService([REPOSITORY], transport=transport)
    with pytest.raises(RepositoryTruthError) as exc:
        service.pull_request_comments_truth(REPOSITORY, 7, expected_head_sha=HEAD)
    assert exc.value.code == "stale_ref"
    assert calls == [f"/repos/{REPOSITORY}/pulls/7"]
