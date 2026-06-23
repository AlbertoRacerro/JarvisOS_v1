"""Local AI utility contracts.

Evaluation harness adapters live in explicitly named eval modules and are not
approved runtime orchestration, chat, retrieval, memory, or gatekeeper code.
"""

from app.modules.local_ai.config import LocalGemmaConfig, validate_local_endpoint_url
from app.modules.local_ai.eval_adapter import LocalGemmaEvalAdapter, LocalGemmaEvalAdapterResult

__all__ = [
    "LocalGemmaEvalAdapter",
    "LocalGemmaEvalAdapterResult",
    "LocalGemmaConfig",
    "validate_local_endpoint_url",
]
