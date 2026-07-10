# PR checklist

**Spec:** docs/specs/NNN — <title>, or N/A

**Spec gate:** implementation NNN | definition NNN | N/A

- `implementation NNN`: `docs/specs/STATUS.md` must show `in_review`, this PR
  number, and only `merged` hard dependencies.
- `definition NNN`: the registry row must exist as `planned`, `blocked`, or
  `ready`; the implementation PR column stays `—`.
- `N/A`: use only when the PR does not implement or define a numbered spec.

## What changed

- <summary of the change, per file group>

## Files outside spec scope

<"None", or list each out-of-scope file with a one-line justification>

## Deviations from spec

<"None", or list EVERY simplification, placeholder, partial implementation, or
unmet acceptance criterion — undisclosed deviations violate AGENTS.md invariant 9>

## Test evidence

- [ ] `python -m pytest -q` green (paste tail of output below)
- [ ] `python -m ruff check app tests` clean
- [ ] Frontend build green (only if frontend touched)

```text
<paste test output tail here>
```

## Invariants (AGENTS.md)

- [ ] No Auto-external execution paths added or weakened
- [ ] All AI calls still go through the spine + `ai_jobs` ledger
- [ ] Safe defaults unchanged (fake provider, paid AI off, budget zero)
- [ ] No secrets in code, tests, fixtures, or logs
- [ ] Data-root paths via `app/core/paths.py`; no hardcoded absolute paths

## Residual risk / notes

<anything the reviewer should look at closely; deviations from spec; discoveries>
