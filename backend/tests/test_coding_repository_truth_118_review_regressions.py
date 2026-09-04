from __future__ import annotations

import base64
import json

import pytest

from app.modules.coding.repository_truth import (
    MAX_COLLECTION_ITEMS,
    MAX_FILE_PREVIEW_BYTES,
    HttpResponse,
    RepositoryTruthError,
    RepositoryTruthService,
)

REPOSITORY = "AlbertoRacerro/JarvisOS_v1"
HEAD_SHA = "a" * 40
BASE_SHA = "b" * 40
BIG_SHA = "c" * 40
SMALL_SHA = "d" * 40


def response(payload: object, status: int = 200) -> HttpResponse:
    return HttpResponse(status=status, headers={}, body=json.dumps(payload).encode("utf-8"))


class FakeTransport:
    def __init__(self, routes: dict[str, HttpResponse]) -> None:
        self.routes = routes
        self.calls: list[str] = []

    def __call__(self, path: str) -> HttpResponse:
        self.calls.append(path)
        value = self.routes.get(path)
        if value is None:
            raise AssertionError(f"unexpected transport path: {path}")
        return value


def service(routes: dict[str, HttpResponse]) -> tuple[RepositoryTruthService, FakeTransport]:
    transport = FakeTransport(routes)
    return RepositoryTruthService([REPOSITORY], transport=transport), transport


def commit_route(payload: object | None = None) -> dict[str, HttpResponse]:
    return {f"/repos/{REPOSITORY}/commits/master": response(payload or {"sha": HEAD_SHA})}


def pr_payload(*, head_sha: object = HEAD_SHA) -> dict[str, object]:
    return {
        "state": "open",
        "head": {"ref": "feature", "sha": head_sha},
        "base": {"ref": "master", "sha": BASE_SHA},
    }


def test_literal_search_oversized_declared_candidate_marks_partial() -> None:
    encoded = base64.b64encode(b"alpha").decode("ascii")
    routes = {
        **commit_route(),
        f"/repos/{REPOSITORY}/git/trees/{HEAD_SHA}?recursive=1": response(
            {
                "truncated": False,
                "tree": [
                    {
                        "type": "blob",
                        "path": "large.txt",
                        "sha": BIG_SHA,
                        "size": MAX_FILE_PREVIEW_BYTES + 1,
                    },
                    {"type": "blob", "path": "small.txt", "sha": SMALL_SHA, "size": 5},
                ],
            }
        ),
        f"/repos/{REPOSITORY}/git/blobs/{SMALL_SHA}": response(
            {"encoding": "base64", "content": encoded}
        ),
    }
    subject, transport = service(routes)
    result = subject.literal_search(REPOSITORY, "master", "needle")
    assert result.partial is True
    assert result.payload["matches"] == []
    assert f"/repos/{REPOSITORY}/git/blobs/{BIG_SHA}" not in transport.calls


def test_literal_search_non_base64_candidate_marks_partial() -> None:
    routes = {
        **commit_route(),
        f"/repos/{REPOSITORY}/git/trees/{HEAD_SHA}?recursive=1": response(
            {
                "truncated": False,
                "tree": [{"type": "blob", "path": "large.txt", "sha": BIG_SHA}],
            }
        ),
        f"/repos/{REPOSITORY}/git/blobs/{BIG_SHA}": response(
            {"encoding": "none", "content": ""}
        ),
    }
    subject, _ = service(routes)
    result = subject.literal_search(REPOSITORY, "master", "needle")
    assert result.partial is True
    assert result.payload["matches"] == []


def test_literal_search_malformed_base64_is_typed() -> None:
    routes = {
        **commit_route(),
        f"/repos/{REPOSITORY}/git/trees/{HEAD_SHA}?recursive=1": response(
            {
                "truncated": False,
                "tree": [{"type": "blob", "path": "bad.txt", "sha": BIG_SHA, "size": 3}],
            }
        ),
        f"/repos/{REPOSITORY}/git/blobs/{BIG_SHA}": response(
            {"encoding": "base64", "content": "%%%"}
        ),
    }
    subject, _ = service(routes)
    with pytest.raises(RepositoryTruthError) as exc:
        subject.literal_search(REPOSITORY, "master", "needle")
    assert exc.value.code == "malformed_provider_response"


@pytest.mark.parametrize("sha", [None, 123, True])
def test_repository_ref_truth_malformed_sha_shape_is_typed(sha: object) -> None:
    subject, _ = service(commit_route({"sha": sha}))
    with pytest.raises(RepositoryTruthError) as exc:
        subject.repository_ref_truth(REPOSITORY, "master")
    assert exc.value.code == "malformed_provider_response"


def test_pull_request_null_head_sha_is_typed() -> None:
    subject, _ = service({f"/repos/{REPOSITORY}/pulls/7": response(pr_payload(head_sha=None))})
    with pytest.raises(RepositoryTruthError) as exc:
        subject.pull_request_truth(REPOSITORY, 7)
    assert exc.value.code == "malformed_provider_response"


def test_check_truth_invalid_total_count_is_typed() -> None:
    routes = {
        f"/repos/{REPOSITORY}/pulls/7": response(pr_payload()),
        f"/repos/{REPOSITORY}/commits/{HEAD_SHA}/check-runs?per_page={MAX_COLLECTION_ITEMS}": response(
            {"total_count": "many", "check_runs": []}
        ),
    }
    subject, _ = service(routes)
    with pytest.raises(RepositoryTruthError) as exc:
        subject.check_truth(REPOSITORY, 7, expected_head_sha=HEAD_SHA)
    assert exc.value.code == "malformed_provider_response"


def test_check_truth_null_run_head_sha_is_typed() -> None:
    routes = {
        f"/repos/{REPOSITORY}/pulls/7": response(pr_payload()),
        f"/repos/{REPOSITORY}/commits/{HEAD_SHA}/check-runs?per_page={MAX_COLLECTION_ITEMS}": response(
            {
                "total_count": 1,
                "check_runs": [
                    {
                        "id": 1,
                        "name": "CI",
                        "status": "completed",
                        "conclusion": "success",
                        "head_sha": None,
                    }
                ],
            }
        ),
    }
    subject, _ = service(routes)
    with pytest.raises(RepositoryTruthError) as exc:
        subject.check_truth(REPOSITORY, 7, expected_head_sha=HEAD_SHA)
    assert exc.value.code == "malformed_provider_response"
