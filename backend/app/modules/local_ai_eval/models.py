from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

GEMMA_EVAL_SCHEMA_VERSION = "local_gemma_eval_v1"


class GoldenCategory(StrEnum):
    conversation_continuity = "conversation_continuity"
    codex_log_summary = "codex_log_summary"
    codex_prompt_drafting = "codex_prompt_drafting"
    project_decision_extraction = "project_decision_extraction"
    todo_extraction = "todo_extraction"
    sensitivity_classification = "sensitivity_classification"
    complexity_classification = "complexity_classification"
    local_only_private_note = "local_only_private_note"
    public_technical_question = "public_technical_question"
    retrieval_interpretation = "retrieval_interpretation"
    tool_result_grounding = "tool_result_grounding"
    hallucination_resistance = "hallucination_resistance"
    schema_compliance = "schema_compliance"
    context_request_planning = "context_request_planning"
    partial_context_handling = "partial_context_handling"
    canonical_vs_stale_distinction = "canonical_vs_stale_distinction"
    tool_package_selection = "tool_package_selection"
    missing_context_refusal = "missing_context_refusal"
    external_escalation_preparation = "external_escalation_preparation"


class EvalTaskType(StrEnum):
    continue_conversation = "continue_conversation"
    summarize_codex_log = "summarize_codex_log"
    draft_codex_prompt = "draft_codex_prompt"
    extract_project_decisions = "extract_project_decisions"
    extract_todos = "extract_todos"
    classify_sensitivity = "classify_sensitivity"
    classify_complexity = "classify_complexity"
    handle_local_note = "handle_local_note"
    answer_public_technical = "answer_public_technical"
    interpret_retrieval = "interpret_retrieval"
    grounded_tool_summary = "grounded_tool_summary"
    detect_hallucination = "detect_hallucination"
    validate_schema = "validate_schema"
    plan_context_request = "plan_context_request"
    handle_partial_context = "handle_partial_context"
    resolve_canonical_context = "resolve_canonical_context"
    select_tool_packages = "select_tool_packages"
    refuse_missing_context = "refuse_missing_context"
    prepare_external_escalation = "prepare_external_escalation"


class EvalState(StrEnum):
    INTAKE = "INTAKE"
    CONTEXT_PLAN = "CONTEXT_PLAN"
    CONTEXT_REQUEST = "CONTEXT_REQUEST"
    CONTEXT_RECEIVED = "CONTEXT_RECEIVED"
    ANALYSIS = "ANALYSIS"
    NEED_MORE_CONTEXT = "NEED_MORE_CONTEXT"
    ASK_USER_CLARIFICATION = "ASK_USER_CLARIFICATION"
    READY_LOCAL_RESPONSE = "READY_LOCAL_RESPONSE"
    READY_EXTERNAL_PROMPT = "READY_EXTERNAL_PROMPT"
    USER_CONFIRM_REQUIRED = "USER_CONFIRM_REQUIRED"
    BLOCKED = "BLOCKED"


class ContextSufficiency(StrEnum):
    insufficient = "insufficient"
    partial = "partial"
    sufficient = "sufficient"
    not_applicable = "not_applicable"


class ContextPackage(StrEnum):
    CURRENT_TASK = "CURRENT_TASK"
    CURRENT_MILESTONE = "CURRENT_MILESTONE"
    RECENT_CONVERSATION_SUMMARY = "RECENT_CONVERSATION_SUMMARY"
    ACTIVE_PROJECT_STATE = "ACTIVE_PROJECT_STATE"
    RECENT_DECISIONS = "RECENT_DECISIONS"
    OPEN_DECISIONS = "OPEN_DECISIONS"
    CANONICAL_ROADMAP = "CANONICAL_ROADMAP"
    CODEX_LAST_LOG = "CODEX_LAST_LOG"
    FILES_CHANGED_SUMMARY = "FILES_CHANGED_SUMMARY"
    TEST_RESULTS_SUMMARY = "TEST_RESULTS_SUMMARY"
    RELEVANT_DOCS = "RELEVANT_DOCS"
    RELEVANT_EVENTS = "RELEVANT_EVENTS"
    RELEVANT_ARTIFACTS = "RELEVANT_ARTIFACTS"
    ENTITY_GRAPH_SNIPPET = "ENTITY_GRAPH_SNIPPET"
    MEMORY_SNIPPETS = "MEMORY_SNIPPETS"
    SENSITIVITY_RULES = "SENSITIVITY_RULES"
    PROVIDER_TIER_MAP = "PROVIDER_TIER_MAP"
    LOCAL_TOOL_CATALOG = "LOCAL_TOOL_CATALOG"


class EvalSensitivity(StrEnum):
    public = "public"
    internal = "internal"
    confidential = "confidential"
    sensitive_ip = "sensitive_ip"
    secret = "secret"
    unknown = "unknown"


class EvalComplexity(StrEnum):
    trivial = "trivial"
    low = "low"
    medium = "medium"
    high = "high"
    unknown = "unknown"


class EvalLocalAction(StrEnum):
    LOCAL_ONLY = "LOCAL_ONLY"
    LOCAL_GEMMA = "LOCAL_GEMMA"
    USER_CONFIRM_REQUIRED = "USER_CONFIRM_REQUIRED"
    CHEAP_GATE = "CHEAP_GATE"
    CHEAP_PLUS_GATE = "CHEAP_PLUS_GATE"
    SCIENTIFIC_MEDIUM_GATE = "SCIENTIFIC_MEDIUM_GATE"
    FRONTIER_GATE = "FRONTIER_GATE"
    ASK_FOR_CONTEXT = "ASK_FOR_CONTEXT"
    BLOCKED = "BLOCKED"
    ANSWER_LOCALLY = "ANSWER_LOCALLY"
    SUMMARIZE_CONTEXT = "SUMMARIZE_CONTEXT"
    DRAFT_CODEX_PROMPT = "DRAFT_CODEX_PROMPT"
    EXTRACT_DECISIONS = "EXTRACT_DECISIONS"
    EXTRACT_TODOS = "EXTRACT_TODOS"
    CLASSIFY_SENSITIVITY = "CLASSIFY_SENSITIVITY"
    CLASSIFY_COMPLEXITY = "CLASSIFY_COMPLEXITY"
    INTERPRET_RETRIEVAL = "INTERPRET_RETRIEVAL"
    INTERPRET_TOOL_RESULTS = "INTERPRET_TOOL_RESULTS"
    VALIDATE_SCHEMA = "VALIDATE_SCHEMA"


class Severity(StrEnum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class ProvidedContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    current_task: str = ""
    conversation_summary: str = ""
    project_state: str = ""
    relevant_decisions: list[str] = Field(default_factory=list)
    tool_results: list[dict[str, Any]] = Field(default_factory=list)
    known_constraints: list[str] = Field(default_factory=list)
    forbidden_actions: list[str] = Field(default_factory=list)


class ExpectedEvaluation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task_type: EvalTaskType
    sensitivity: EvalSensitivity
    complexity: EvalComplexity
    selected_local_action: EvalLocalAction
    must_include: list[str] = Field(default_factory=list)
    must_not_include: list[str] = Field(default_factory=list)
    expected_decisions: list[str] = Field(default_factory=list)
    expected_todos: list[str] = Field(default_factory=list)
    expected_missing_context_flags: list[str] = Field(default_factory=list)
    expected_state: EvalState = EvalState.READY_LOCAL_RESPONSE
    expected_requested_context_packages: list[ContextPackage] = Field(default_factory=list)
    forbidden_context_packages: list[ContextPackage] = Field(default_factory=list)
    context_sufficiency: ContextSufficiency = ContextSufficiency.not_applicable
    expected_allowed_tool_requests: list[str] = Field(default_factory=list)
    forbidden_tool_requests: list[str] = Field(default_factory=list)
    external_call_requested: bool = False
    external_call_allowed_by_model: bool = False


class GoldenTestCase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    category: GoldenCategory
    input: str = Field(min_length=1)
    provided_context: ProvidedContext
    expected: ExpectedEvaluation
    severity: Severity
    notes: str = Field(min_length=1)


class GemmaEvalOutput(BaseModel):
    """Future local Gemma response shape; validated now without calling a model."""

    model_config = ConfigDict(extra="forbid")

    task_type: EvalTaskType
    state: EvalState
    sensitivity: EvalSensitivity
    complexity: EvalComplexity
    selected_local_action: EvalLocalAction
    requested_context_packages: list[ContextPackage]
    context_sufficiency: ContextSufficiency
    context_request_reason: str | None
    allowed_tool_requests: list[str]
    forbidden_tool_requests: list[str]
    external_prompt: str | None
    external_call_requested: bool
    external_call_allowed_by_model: bool
    confidence: float = Field(ge=0, le=1)
    reasons: list[str]
    extracted_todos: list[str]
    extracted_decisions: list[str]
    missing_context: list[str]
    tool_result_references_used: list[str]
    hallucination_flags: list[str]
    suggested_next_action: str
    local_only_warning: bool
    schema_version: str

    @field_validator("schema_version")
    @classmethod
    def schema_version_must_match(cls, value: str) -> str:
        if value != GEMMA_EVAL_SCHEMA_VERSION:
            raise ValueError(f"schema_version must be {GEMMA_EVAL_SCHEMA_VERSION}")
        return value
