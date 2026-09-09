from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "cloud-delivery-comment-trigger.yml"


def test_cloud_delivery_comment_trigger_is_owner_only_and_dispatch_only() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert "issue_comment:" in workflow
    assert "types: [created]" in workflow
    assert "github.actor == github.repository_owner" in workflow
    assert "github.event.repository.default_branch == 'master'" in workflow
    assert "github.event.issue.pull_request != null" in workflow
    assert "actions: write" in workflow
    assert "contents: write" not in workflow
    assert "COMMENT_BODY: ${{ github.event.comment.body }}" in workflow
    assert "ISSUE_NUMBER: ${{ github.event.issue.number }}" in workflow
    assert "${{ github.event.comment.body }}" not in workflow.split("script: |", 1)[1]
    assert "jarvis-cloud-delivery:dispatch:v1" in workflow
    assert "pr !== issueNumber" in workflow
    assert "pull.data.state !== 'open'" in workflow
    assert "pull.data.head.repo?.full_name !== context.payload.repository.full_name" in workflow
    assert "actions.createWorkflowDispatch" in workflow
    assert "workflow_id: 'cloud-delivery-bridge.yml'" in workflow
    assert "ref: 'master'" in workflow
    assert "payload_comment_id: String(payloadCommentId)" in workflow
