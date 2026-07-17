from __future__ import annotations

from pathlib import Path


EXECUTION = Path("backend/app/modules/ai/execution.py")
TEST = Path("backend/tests/test_token_flow_execution_wiring.py")

OLD_EXECUTION_IMPORTS = '''from app.modules.ai.execution_types import ProviderBinding
from app.modules.ai.token_flow_evidence import AttemptEvidence
from app.modules.ai.token_flow_runtime import (
    local_exception_evidence,
    local_response_evidence,
    no_execution_evidence,
    normalize_outcome_reason,
)
from app.modules.ai.token_flow_service import create_flow, transition_flow_state
from app.modules.ai.token_flow_transaction import record_attempt_evidence_in_transaction
from app.modules.ai.providers.fake_adapter import FAKE_PROVIDER_ID, FakeProviderAdapter
from app.modules.ai.providers.local_ollama_adapter import (
    LOCAL_OLLAMA_PROVIDER_ID,
    LocalOllamaAdapter,
)
from app.modules.ai.providers.openai_compat_adapter import OpenAICompatAdapter
from app.modules.ai.providers.scaleway_adapter import SCALEWAY_PROVIDER_ID, ScalewayProviderAdapter
'''
NEW_EXECUTION_IMPORTS = '''from app.modules.ai.execution_types import ProviderBinding
from app.modules.ai.providers.fake_adapter import FAKE_PROVIDER_ID, FakeProviderAdapter
from app.modules.ai.providers.local_ollama_adapter import (
    LOCAL_OLLAMA_PROVIDER_ID,
    LocalOllamaAdapter,
)
from app.modules.ai.providers.openai_compat_adapter import OpenAICompatAdapter
from app.modules.ai.providers.scaleway_adapter import SCALEWAY_PROVIDER_ID, ScalewayProviderAdapter
from app.modules.ai.token_flow_evidence import AttemptEvidence
from app.modules.ai.token_flow_runtime import (
    local_exception_evidence,
    local_response_evidence,
    no_execution_evidence,
    normalize_outcome_reason,
)
from app.modules.ai.token_flow_service import create_flow, transition_flow_state
from app.modules.ai.token_flow_transaction import record_attempt_evidence_in_transaction
'''

PAIR_OLD = '''    from app.modules.ai.execution import run_ai_task
    from app.modules.ai.token_flow_service import get_flow
'''
PAIR_NEW = '''    from app.modules.ai.token_flow_service import get_flow

    from app.modules.ai.execution import run_ai_task
'''
TRIPLE_OLD = '''    from app.modules.ai.execution import run_ai_task
    from app.modules.ai.execution_types import ProviderBinding
    from app.modules.ai.token_flow_service import get_flow
'''
TRIPLE_NEW = '''    from app.modules.ai.execution_types import ProviderBinding
    from app.modules.ai.token_flow_service import get_flow

    from app.modules.ai.execution import run_ai_task
'''


def replace_exact(path: Path, old: str, new: str, expected_count: int) -> None:
    source = path.read_text(encoding="utf-8")
    count = source.count(old)
    if count != expected_count:
        raise RuntimeError(f"{path}: expected {expected_count} replacement points, found {count}")
    path.write_text(source.replace(old, new), encoding="utf-8")


def main() -> None:
    replace_exact(EXECUTION, OLD_EXECUTION_IMPORTS, NEW_EXECUTION_IMPORTS, 1)
    replace_exact(TEST, TRIPLE_OLD, TRIPLE_NEW, 1)
    replace_exact(TEST, PAIR_OLD, PAIR_NEW, 2)


if __name__ == "__main__":
    main()
