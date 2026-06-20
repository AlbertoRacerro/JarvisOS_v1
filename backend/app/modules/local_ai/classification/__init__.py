"""Classification-only local AI utility.

Gemma output from this package is advisory. JarvisOS validation and fallback
policy remain authoritative.
"""

from app.modules.local_ai.classification.contracts import (
    CLASSIFICATION_INPUT_SCHEMA_VERSION,
    CLASSIFICATION_OUTPUT_SCHEMA_VERSION,
    CLASSIFICATION_DIAGNOSTIC_NUM_PREDICT_CANDIDATES,
    AllowedNextStep,
    ClassificationAttemptDiagnostics,
    ClassificationBudgetPolicy,
    ClassificationInput,
    ClassificationOutput,
    ClassificationServiceResult,
    ClassificationSource,
    ClassificationResultSource,
    ComplexityHint,
    ProjectArea,
    SensitivityHint,
    TaskType,
)
from app.modules.local_ai.classification.service import classify_text

__all__ = [
    "AllowedNextStep",
    "CLASSIFICATION_DIAGNOSTIC_NUM_PREDICT_CANDIDATES",
    "CLASSIFICATION_INPUT_SCHEMA_VERSION",
    "CLASSIFICATION_OUTPUT_SCHEMA_VERSION",
    "ClassificationAttemptDiagnostics",
    "ClassificationBudgetPolicy",
    "ClassificationInput",
    "ClassificationOutput",
    "ClassificationResultSource",
    "ClassificationServiceResult",
    "ClassificationSource",
    "ComplexityHint",
    "ProjectArea",
    "SensitivityHint",
    "TaskType",
    "classify_text",
]
