import pytest
from pydantic import ValidationError

from app.modules.local_ai.contracts import (
    MICRO_CONTRACT_SCHEMA_VERSION,
    ContextPackage,
    ContextRequestOutput,
    DecisionExtractionOutput,
    DecisionItem,
    DecisionStatus,
    EvalSensitivity,
    EvidenceRef,
    EvidenceSelectionOutput,
    ExternalCapability,
    ExternalPromptDraftOutput,
    ProjectArea,
    RiskLevel,
    SensitivityCheckOutput,
    TaskClassificationOutput,
    TaskType,
    TodoExtractionOutput,
    TodoItem,
    ToolCallProposalOutput,
)


def test_task_classification_contract_accepts_minimal_valid_output() -> None:
    output = TaskClassificationOutput(
        task_type=TaskType.project_planning,
        project_area=ProjectArea.jarvisos,
        requires_context=True,
        requires_tool=False,
        requires_external_reasoning=False,
        confidence=0.82,
        reasons=["Needs roadmap context."],
        schema_version=MICRO_CONTRACT_SCHEMA_VERSION,
    )

    assert output.schema_version == MICRO_CONTRACT_SCHEMA_VERSION


def test_context_request_contract_uses_controlled_context_packages() -> None:
    output = ContextRequestOutput(
        requested_context_packages=[ContextPackage.CURRENT_MILESTONE, ContextPackage.RECENT_DECISIONS],
        context_request_reason="Need bounded project context before planning.",
        minimum_needed_context=["current milestone", "recent accepted decisions"],
        forbidden_context=["raw filesystem scan"],
        confidence=0.7,
        schema_version=MICRO_CONTRACT_SCHEMA_VERSION,
    )

    assert output.requested_context_packages == [ContextPackage.CURRENT_MILESTONE, ContextPackage.RECENT_DECISIONS]


def test_sensitivity_contract_is_advisory_and_schema_validated() -> None:
    output = SensitivityCheckOutput(
        sensitivity=EvalSensitivity.confidential,
        externalization_allowed=False,
        redaction_required=True,
        user_confirmation_required=True,
        reasons=["Contains non-public project strategy."],
        confidence=0.91,
        schema_version=MICRO_CONTRACT_SCHEMA_VERSION,
    )

    assert output.externalization_allowed is False


def test_tool_call_proposal_contract_cannot_execute_anything() -> None:
    output = ToolCallProposalOutput(
        tool_name="read_context_package",
        arguments={"package": "RECENT_DECISIONS"},
        purpose="Inspect bounded context package selected by JarvisOS.",
        risk_level=RiskLevel.low,
        requires_user_confirmation=False,
        allowed_by_model=True,
        confidence=0.76,
        schema_version=MICRO_CONTRACT_SCHEMA_VERSION,
    )

    assert output.tool_name == "read_context_package"
    assert output.allowed_by_model is True


def test_external_prompt_draft_contract_separates_draft_from_call() -> None:
    output = ExternalPromptDraftOutput(
        target_capability=ExternalCapability.scientific_reasoning,
        redacted_prompt="Review this public, redacted modeling assumption.",
        included_context_refs=["ctx_public_001"],
        excluded_sensitive_refs=["ctx_secret_001"],
        reason_for_escalation="Needs stronger external reasoning after local validation.",
        expected_output_contract="short technical critique",
        confidence=0.63,
        schema_version=MICRO_CONTRACT_SCHEMA_VERSION,
    )

    assert "secret" not in output.redacted_prompt.lower()


def test_todo_decision_and_evidence_contracts_validate() -> None:
    todos = TodoExtractionOutput(
        todos=[TodoItem(text="Create D10B probe harness.", source_refs=["doc_d10a"])],
        owner_guess="Codex",
        priority_guess="medium",
        source_refs=["doc_d10a"],
        confidence=0.8,
        schema_version=MICRO_CONTRACT_SCHEMA_VERSION,
    )
    decisions = DecisionExtractionOutput(
        decisions=[
            DecisionItem(
                text="Use staged Gemma micro-contracts before full D7 output.",
                status=DecisionStatus.accepted,
                source_refs=["adr_036"],
            )
        ],
        decision_status=DecisionStatus.accepted,
        source_refs=["adr_036"],
        confidence=0.86,
        schema_version=MICRO_CONTRACT_SCHEMA_VERSION,
    )
    evidence = EvidenceSelectionOutput(
        selected_evidence_refs=[EvidenceRef(ref_id="d9r_compact_schema", reason="Shows 31B can pass compact schema.")],
        rejected_evidence_refs=[],
        reasoning_summary="Compact schema evidence is relevant; full D7 timeout is a separate limit.",
        missing_evidence=["category-diverse D10B probes"],
        confidence=0.78,
        schema_version=MICRO_CONTRACT_SCHEMA_VERSION,
    )

    assert todos.todos[0].text
    assert decisions.decisions[0].status == DecisionStatus.accepted
    assert evidence.selected_evidence_refs[0].ref_id == "d9r_compact_schema"


def test_micro_contracts_forbid_extra_fields() -> None:
    with pytest.raises(ValidationError):
        TaskClassificationOutput(
            task_type=TaskType.local_question,
            project_area=ProjectArea.local_ai,
            requires_context=False,
            requires_tool=False,
            requires_external_reasoning=False,
            confidence=0.5,
            schema_version=MICRO_CONTRACT_SCHEMA_VERSION,
            unauthorized_field="not allowed",
        )


def test_micro_contracts_reject_wrong_schema_version() -> None:
    with pytest.raises(ValidationError, match="schema_version"):
        TaskClassificationOutput(
            task_type=TaskType.local_question,
            project_area=ProjectArea.local_ai,
            requires_context=False,
            requires_tool=False,
            requires_external_reasoning=False,
            confidence=0.5,
            schema_version="wrong",
        )


def test_micro_contract_json_schema_is_small_and_structured_output_friendly() -> None:
    schema = ToolCallProposalOutput.model_json_schema()

    assert schema["additionalProperties"] is False
    assert "properties" in schema
    assert set(schema["required"]) >= {
        "tool_name",
        "arguments",
        "purpose",
        "risk_level",
        "requires_user_confirmation",
        "allowed_by_model",
        "confidence",
        "schema_version",
    }
