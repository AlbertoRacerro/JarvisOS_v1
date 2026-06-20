from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.modules.local_ai_eval.models import ContextPackage, EvalSensitivity


MICRO_CONTRACT_SCHEMA_VERSION = "local_gemma_micro_contract_v1"


class MicroContractBase(BaseModel):
    """Base for staged local Gemma contract outputs."""

    model_config = ConfigDict(extra="forbid")

    confidence: float = Field(ge=0, le=1)
    schema_version: str

    @field_validator("schema_version")
    @classmethod
    def schema_version_must_match(cls, value: str) -> str:
        if value != MICRO_CONTRACT_SCHEMA_VERSION:
            raise ValueError(f"schema_version must be {MICRO_CONTRACT_SCHEMA_VERSION}")
        return value


class TaskType(StrEnum):
    local_question = "local_question"
    project_planning = "project_planning"
    code_change = "code_change"
    bug_report = "bug_report"
    documentation = "documentation"
    extraction = "extraction"
    prompt_drafting = "prompt_drafting"
    modeling = "modeling"
    unknown = "unknown"


class ProjectArea(StrEnum):
    jarvisos = "jarvisos"
    bluerev = "bluerev"
    local_ai = "local_ai"
    python_runner = "python_runner"
    documentation = "documentation"
    unknown = "unknown"


class RiskLevel(StrEnum):
    low = "low"
    medium = "medium"
    high = "high"
    blocked = "blocked"


class ExternalCapability(StrEnum):
    general_reasoning = "general_reasoning"
    code_reasoning = "code_reasoning"
    scientific_reasoning = "scientific_reasoning"
    summarization = "summarization"
    prompt_review = "prompt_review"


class DecisionStatus(StrEnum):
    proposed = "proposed"
    accepted = "accepted"
    superseded = "superseded"
    rejected = "rejected"
    unknown = "unknown"


class EvidenceRef(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ref_id: str = Field(min_length=1)
    reason: str = Field(min_length=1)


class TaskClassificationOutput(MicroContractBase):
    task_type: TaskType
    project_area: ProjectArea
    requires_context: bool
    requires_tool: bool
    requires_external_reasoning: bool
    reasons: list[str] = Field(default_factory=list)


class ContextRequestOutput(MicroContractBase):
    requested_context_packages: list[ContextPackage] = Field(default_factory=list)
    context_request_reason: str = Field(min_length=1)
    minimum_needed_context: list[str] = Field(default_factory=list)
    forbidden_context: list[str] = Field(default_factory=list)


class SensitivityCheckOutput(MicroContractBase):
    sensitivity: EvalSensitivity
    externalization_allowed: bool
    redaction_required: bool
    user_confirmation_required: bool
    reasons: list[str] = Field(default_factory=list)


class ToolCallProposalOutput(MicroContractBase):
    tool_name: str = Field(min_length=1)
    arguments: dict[str, str | int | float | bool | None]
    purpose: str = Field(min_length=1)
    risk_level: RiskLevel
    requires_user_confirmation: bool
    allowed_by_model: bool


class ExternalPromptDraftOutput(MicroContractBase):
    target_capability: ExternalCapability
    redacted_prompt: str = Field(min_length=1)
    included_context_refs: list[str] = Field(default_factory=list)
    excluded_sensitive_refs: list[str] = Field(default_factory=list)
    reason_for_escalation: str = Field(min_length=1)
    expected_output_contract: str = Field(min_length=1)


class TodoItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str = Field(min_length=1)
    source_refs: list[str] = Field(default_factory=list)


class TodoExtractionOutput(MicroContractBase):
    todos: list[TodoItem] = Field(default_factory=list)
    owner_guess: str | None = None
    priority_guess: str | None = None
    source_refs: list[str] = Field(default_factory=list)


class DecisionItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str = Field(min_length=1)
    status: DecisionStatus
    source_refs: list[str] = Field(default_factory=list)
    supersedes: list[str] = Field(default_factory=list)


class DecisionExtractionOutput(MicroContractBase):
    decisions: list[DecisionItem] = Field(default_factory=list)
    decision_status: DecisionStatus
    source_refs: list[str] = Field(default_factory=list)
    supersedes: list[str] = Field(default_factory=list)


class EvidenceSelectionOutput(MicroContractBase):
    selected_evidence_refs: list[EvidenceRef] = Field(default_factory=list)
    rejected_evidence_refs: list[EvidenceRef] = Field(default_factory=list)
    reasoning_summary: str = Field(min_length=1)
    missing_evidence: list[str] = Field(default_factory=list)
