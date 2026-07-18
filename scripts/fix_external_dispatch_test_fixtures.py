from __future__ import annotations

from pathlib import Path

EXECUTION_TEST = Path("backend/tests/test_ai_execution_spine.py")
ALPHA_TEST = Path("backend/tests/test_alpha_gate_enforcement.py")


def replace_exact(path: Path, old: str, new: str, expected: int = 1) -> None:
    source = path.read_text(encoding="utf-8")
    count = source.count(old)
    if count != expected:
        raise RuntimeError(f"{path}: expected {expected} matches, found {count}: {old[:80]!r}")
    path.write_text(source.replace(old, new), encoding="utf-8")


def main() -> None:
    replace_exact(
        EXECUTION_TEST,
        """from app.modules.ai.contracts import (
    AIRequest,
""",
        """from app.modules.ai.contracts import (
    AIExternalDispatchState,
    AIRequest,
""",
    )
    replace_exact(
        EXECUTION_TEST,
        """                safety_status="allowed",
            )
""",
        """                safety_status="allowed",
                external_dispatch_state=AIExternalDispatchState.started,
            )
""",
        expected=1,
    )
    replace_exact(
        EXECUTION_TEST,
        """            blocked_reason="provider_failed",
            error=AIProviderError(code=self.code, message="provider failed", retryable=self.retryable),
        )
""",
        """            blocked_reason="provider_failed",
            error=AIProviderError(code=self.code, message="provider failed", retryable=self.retryable),
            external_dispatch_state=AIExternalDispatchState.started,
        )
""",
        expected=1,
    )
    replace_exact(
        EXECUTION_TEST,
        """            safety_status="allowed",
        )

    def stream(self, request: AIRequest):  # pragma: no cover - not used
""",
        """            safety_status="allowed",
            external_dispatch_state=AIExternalDispatchState.started,
        )

    def stream(self, request: AIRequest):  # pragma: no cover - not used
""",
        expected=1,
    )

    replace_exact(
        ALPHA_TEST,
        """from app.modules.ai.contracts import (
    AIProviderError,
""",
        """from app.modules.ai.contracts import (
    AIExternalDispatchState,
    AIProviderError,
""",
    )
    replace_exact(
        ALPHA_TEST,
        """            safety_status="allowed",
        )

    def stream(self, request: AIRequest):  # pragma: no cover - not used
""",
        """            safety_status="allowed",
            external_dispatch_state=AIExternalDispatchState.started,
        )

    def stream(self, request: AIRequest):  # pragma: no cover - not used
""",
        expected=1,
    )
    replace_exact(
        ALPHA_TEST,
        """            error=AIProviderError(
                code=AIProviderErrorCode.provider_timeout,
                message="retryable timeout",
                retryable=True,
            ),
        )
""",
        """            error=AIProviderError(
                code=AIProviderErrorCode.provider_timeout,
                message="retryable timeout",
                retryable=True,
            ),
            external_dispatch_state=AIExternalDispatchState.started,
        )
""",
        expected=1,
    )
    replace_exact(
        ALPHA_TEST,
        """    adapter = _SuccessAdapter("test_provider")
    binding = ProviderBinding(
        "external:test",
        "test_provider",
        "test-model",
        True,
        128,
    )
""",
        """    adapter = _SuccessAdapter("deepseek")
    binding = ProviderBinding(
        "external:test",
        "deepseek",
        "deepseek-v4-pro",
        True,
        128,
        execution_class="external_provider",
        context_window_tokens=8192,
    )
""",
        expected=1,
    )
    replace_exact(
        ALPHA_TEST,
        """        adapters={"test_provider": adapter},
        bindings={"external:test": binding},
""",
        """        adapters={"deepseek": adapter},
        bindings={"external:test": binding},
""",
        expected=1,
    )
    replace_exact(
        ALPHA_TEST,
        """    assert calls == [("test_provider", budget.ALPHA_EXTERNAL_PROVIDER_CALL)]
""",
        """    assert calls == [("deepseek", budget.ALPHA_EXTERNAL_PROVIDER_CALL)]
""",
        expected=1,
    )


if __name__ == "__main__":
    main()
