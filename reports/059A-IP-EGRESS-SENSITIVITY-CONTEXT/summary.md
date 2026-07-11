# 059a — Sensitivity and context foundation

Status: implementation in progress.

Base commit: `736bedd98f9bdbb5fc8a7ea0b644e1828a522fd4`.

## Scope boundary

This slice will add only digest-bound sensitivity labels, operator-reviewed
sanitized derivatives, deterministic sensitivity floors, stale-source handling,
and sensitivity-aware context selection/preview. It will not alter provider
adapter invocation, confirmation tickets, fallback execution, or the external
execution spine; those remain owned by 059b.

## Merge gate

The PR must pass focused and full deterministic tests and receive a completed
Codex review on its final head. Review findings must be resolved or explicitly
dispositioned before human merge.
