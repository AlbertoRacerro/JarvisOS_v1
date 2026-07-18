from __future__ import annotations

from pathlib import Path

PATH = Path("docs/specs/STATUS.md")


def replace_once(source: str, old: str, new: str) -> str:
    count = source.count(old)
    if count != 1:
        raise RuntimeError(f"expected one STATUS match, found {count}: {old[:100]!r}")
    return source.replace(old, new)


source = PATH.read_text(encoding="utf-8")
source = replace_once(
    source,
    """3. Promote `061` TOKEN-FLOW-0 before `062` GRADE-0: 061 owns finalized flow,
   execution-class, adapter/external-dispatch, external-provider-spend, and explicit
   local-unpriced/synthetic evidence; 062 consumes that evidence for human outcome
   grading without treating local compute as free.
4. Draft and promote `066` HERMES-PASSTHROUGH-0 and `067` JARVIS-MCP-0 only after
   their contracts are reconciled with 059b, 061, and existing service boundaries.
""",
    """3. Merge `061a` TOKEN-FLOW-CORE-0 before starting `061b` continuation work.
   `061a` owns canonical flow/attempt evidence and accounting; `061b` owns automatic
   continuation, protected resume, and assembled-output completion. `062` consumes both.
4. Draft and promote `066` HERMES-PASSTHROUGH-0 and `067` JARVIS-MCP-0 only after
   their contracts are reconciled with 059b, 061a/061b, and existing service boundaries.
""",
)
source = replace_once(
    source,
    "| 029 | planned | — | Settings and secrets operator page | 015, 018, 061 |",
    "| 029 | planned | — | Settings and secrets operator page | 015, 018, 061a |",
)
source = replace_once(
    source,
    "| 058 | planned | — | Unified workspace home layout | 006, 029, 037, 061 |",
    "| 058 | planned | — | Unified workspace home layout | 006, 029, 037, 061a |",
)
source = replace_once(
    source,
    """| 061 | in_review | [#134](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/134) | TOKEN-FLOW-0 | 021, 059b | Correlate complete flows across no-execution, synthetic, local-compute, and external-provider attempts; separate adapter invocation from external egress, preserve restart-safe confirmation and bounded continuation, account only external provider spend in USD, and expose local compute as explicitly unpriced rather than free. |
| 062 | planned | — | GRADE-0 | 021, 059b, 061 | Record optional human flow grades (`useful`, `partly`, `rework`, `failed`) over finalized 061 outcomes while keeping attempt execution/accounting evidence, external provider spend, local-unpriced coverage, synthetic exclusions, deterministic failures, and ungraded flows visible; grades never actuate routing. |
""",
    """| 061 | planned | — | TOKEN-FLOW-0 umbrella definition | 021, 059b | Definition-only umbrella for complete flow economics and bounded completion; implementation is owned by 061a core and 061b continuation slices. |
| 061a | in_review | [#134](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/134) | TOKEN-FLOW-CORE-0 | 021, 059b | Correlate no-execution, synthetic, local-compute, and external-provider attempts in one canonical flow; separate adapter invocation from external dispatch, preserve 059b accounting authority, aggregate only external provider spend in USD, and expose local compute as unpriced. Continuation execution remains deferred to 061b. |
| 061b | blocked | — | TOKEN-FLOW-CONTINUATION-0 | 061a | Add exact-length continuation, protected accumulated segments, restart-safe 059b confirmation resume, assembled-output digests, single final record capture, and safe continuation status after 061a is merged. |
| 062 | planned | — | GRADE-0 | 021, 059b, 061a, 061b | Record optional human flow grades (`useful`, `partly`, `rework`, `failed`) over finalized flow outcomes while keeping attempt execution/accounting evidence, external provider spend, local-unpriced coverage, synthetic exclusions, deterministic failures, and ungraded flows visible; grades never actuate routing. |
""",
)
source = replace_once(
    source,
    "| 066 | planned | — | HERMES-PASSTHROUGH-0 | 015, 018, 021, 059b, 061, 062 |",
    "| 066 | planned | — | HERMES-PASSTHROUGH-0 | 015, 018, 021, 059b, 061a, 061b, 062 |",
)
source = replace_once(
    source,
    "| 069 | planned | — | MEMORY-CONSOLIDATE-0 | 040, 042, 061, 062, 066, 067, 068 |",
    "| 069 | planned | — | MEMORY-CONSOLIDATE-0 | 040, 042, 061a, 061b, 062, 066, 067, 068 |",
)
PATH.write_text(source, encoding="utf-8")
