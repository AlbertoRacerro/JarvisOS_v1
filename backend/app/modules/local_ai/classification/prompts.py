import json

from app.modules.local_ai.classification.contracts import (
    CLASSIFICATION_OUTPUT_SCHEMA_VERSION,
    ClassificationInput,
    TaskType,
    ProjectArea,
    ComplexityHint,
    SensitivityHint,
    AllowedNextStep,
)


MAX_CLASSIFICATION_PROMPT_CHARS = 2000


class ClassificationPromptError(ValueError):
    """Raised when a local classification prompt would exceed its budget."""


def build_classification_prompt(request: ClassificationInput) -> str:
    """Build a bounded JSON-only prompt for advisory classification."""

    metadata = json.dumps(request.metadata, ensure_ascii=True, separators=(",", ":"), sort_keys=True)
    prompt = (
        "JSON only; no prose/extra. Advisory: no tools/retrieval/memory/routing/external/state. "
        f"schema_version={CLASSIFICATION_OUTPUT_SCHEMA_VERSION};"
        f"task_type={'|'.join(item.value for item in TaskType)};"
        f"project_area={'|'.join(item.value for item in ProjectArea)};"
        f"complexity_hint={'|'.join(item.value for item in ComplexityHint)};"
        f"sensitivity_hint={'|'.join(item.value for item in SensitivityHint)};"
        f"allowed_next_step={'|'.join(item.value for item in AllowedNextStep)};"
        "needs_context bool;confidence 0..1;refusal_or_uncertainty_reason string|null;"
        f"source={request.source.value};meta={metadata};text={request.text}"
    )
    if len(prompt) > MAX_CLASSIFICATION_PROMPT_CHARS:
        raise ClassificationPromptError("classification prompt exceeds 2000 characters")
    return prompt
