from __future__ import annotations

from pathlib import Path

EXECUTION_TEST = Path("backend/tests/test_ai_execution_spine.py")
ALPHA_TEST = Path("backend/tests/test_alpha_gate_enforcement.py")


def _insert_import(source: str, following: str) -> str:
    if "    AIExternalDispatchState,\n" in source:
        return source
    marker = f"from app.modules.ai.contracts import (\n    {following},\n"
    if source.count(marker) != 1:
        raise RuntimeError(f"contract import marker for {following} is missing or ambiguous")
    return source.replace(
        marker,
        f"from app.modules.ai.contracts import (\n    AIExternalDispatchState,\n    {following},\n",
    )


def _bounded(source: str, start: str, end: str) -> tuple[str, str, str]:
    start_index = source.find(start)
    if start_index < 0:
        raise RuntimeError(f"missing block start: {start}")
    end_index = source.find(end, start_index + len(start))
    if end_index < 0:
        raise RuntimeError(f"missing block end after {start}: {end}")
    return source[:start_index], source[start_index:end_index], source[end_index:]


def _mark_started(
    source: str,
    *,
    start: str,
    end: str,
    closing_indent: str,
    field_indent: str,
) -> str:
    prefix, block, suffix = _bounded(source, start, end)
    if "external_dispatch_state=AIExternalDispatchState.started" in block:
        return source
    closing = f"\n{closing_indent})"
    index = block.rfind(closing)
    if index < 0:
        raise RuntimeError(f"AIResponse closing marker missing in {start}")
    block = (
        block[:index]
        + f"\n{field_indent}external_dispatch_state=AIExternalDispatchState.started,"
        + block[index:]
    )
    return prefix + block + suffix


def _replace_once(source: str, old: str, new: str, label: str) -> str:
    if new in source:
        return source
    if source.count(old) != 1:
        raise RuntimeError(f"{label} target is missing or ambiguous")
    return source.replace(old, new)


def _patch_execution_test() -> None:
    source = EXECUTION_TEST.read_text(encoding="utf-8")
    source = _insert_import(source, "AIRequest")
    source = _mark_started(
        source,
        start="def _stub_scaleway_adapter(",
        end="def _clear_local_route_env(",
        closing_indent="            ",
        field_indent="                ",
    )
    source = _mark_started(
        source,
        start="class _ErrorAdapter:",
        end="class _SuccessAdapter:",
        closing_indent="        ",
        field_indent="            ",
    )
    source = _mark_started(
        source,
        start="class _SuccessAdapter:",
        end="def test_provider_token_cap_blocks_before_adapter_call(",
        closing_indent="        ",
        field_indent="            ",
    )
    EXECUTION_TEST.write_text(source, encoding="utf-8")


def _patch_alpha_test() -> None:
    source = ALPHA_TEST.read_text(encoding="utf-8")
    source = _insert_import(source, "AIProviderError")
    source = _mark_started(
        source,
        start="class _SuccessAdapter:",
        end="class _RetryableAdapter(",
        closing_indent="        ",
        field_indent="            ",
    )
    source = _mark_started(
        source,
        start="class _RetryableAdapter(",
        end="def test_alpha_gate_fails_closed_on_missing_server_context(",
        closing_indent="        ",
        field_indent="            ",
    )
    source = _replace_once(
        source,
        '''    adapter = _SuccessAdapter("test_provider")
    binding = ProviderBinding(
        "external:test",
        "test_provider",
        "test-model",
        True,
        128,
    )
''',
        '''    adapter = _SuccessAdapter("deepseek")
    binding = ProviderBinding(
        "external:test",
        "deepseek",
        "deepseek-v4-pro",
        True,
        128,
        execution_class="external_provider",
        context_window_tokens=8192,
    )
''',
        "registered alpha-gate binding",
    )
    source = _replace_once(
        source,
        '        adapters={"test_provider": adapter},\n',
        '        adapters={"deepseek": adapter},\n',
        "registered alpha-gate adapter",
    )
    source = _replace_once(
        source,
        '    assert calls == [("test_provider", budget.ALPHA_EXTERNAL_PROVIDER_CALL)]\n',
        '    assert calls == [("deepseek", budget.ALPHA_EXTERNAL_PROVIDER_CALL)]\n',
        "alpha-gate provider assertion",
    )
    ALPHA_TEST.write_text(source, encoding="utf-8")


def main() -> None:
    _patch_execution_test()
    _patch_alpha_test()


if __name__ == "__main__":
    main()
