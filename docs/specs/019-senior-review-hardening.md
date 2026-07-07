# 019 — Senior review hardening

Status: implemented (pending review)
Depends on: 017 (Autonomous three-tier review)

## Goal

Harden the senior (GLM) tier of the automated PR review pipeline so it remains
cost-bounded, diagnosable, and reliable without changing workflow YAML, label
semantics, round limits, staleness guard, merge authority, or cheap-tier
DeepSeek request behavior.

## Root causes addressed

- **Billing runaway:** GLM 5.2 defaults to `reasoning_effort="max"`; without a
  combined reasoning/content `max_tokens` cap, it can consume tens of thousands
  of billed reasoning tokens and return empty content with
  `finish_reason="length"`.
- **Blind empty-content errors:** the SSE accumulator only read
  `choices[0].delta.content`, so it lost both `reasoning_content` evidence and
  the final `finish_reason` needed to diagnose token-budget exhaustion.
- **Verdict typo fail-closed:** senior output containing a typo such as
  `NO_FURTTER_CHANGES` was parsed as no verdict despite being clearly intended
  as a clean result.
- **Retry double-billing:** a read timeout after a long billed generation was
  retried as an `OSError`, potentially billing the same doomed call twice and
  exhausting the workflow wall clock.
- **Sticky comment pagination:** only the first 100 PR comments were inspected,
  so older sticky comments could be missed and the round counter reset.
- **Error-path loss:** provider-error reporting could fail while posting the
  fail-open GitHub comment, losing the generated error detail from workflow logs.

## Scope

- `scripts/cheap_review.py` only for implementation changes, using the Python
  standard library only.
- `docs/specs/017-two-tier-autonomous-review.md` for the manual expert-review
  label note.
- This spec file as the amendment record for spec 019.

## Non-goals

- No workflow YAML changes.
- No new dependencies.
- No change to cheap-tier DeepSeek request behavior beyond an empty default
  extra body.
- No change to label semantics, round limits, staleness guard, or merge
  authority.
- No streaming for the cheap tier.
- No expansion of tools, agents, background workers, or provider integrations.

## Acceptance criteria

1. `REVIEW_EXTRA_BODY` is accepted as a JSON object and merged into the model
   request body. Invalid JSON or a non-object value fails loudly. When unset,
   senior defaults are `{"reasoning_effort": "low", "max_tokens": 8000,
   "do_sample": false}` and cheap-tier defaults remain `{}`. Explicit keys in
   `REVIEW_EXTRA_BODY` override tier defaults.
2. Streaming SSE parsing accumulates content, detects whether any
   `reasoning_content` delta arrived, captures the final `finish_reason`, and
   supports multi-line `data:` fields. Empty streamed content raises a
   diagnostic that distinguishes token-budget exhaustion
   (`finish_reason=length` with reasoning content) from an empty stream.
3. Verdict parsing remains fail-closed for garbage, but verdict lines are
   normalized deterministically so exact tokens, `NO_FURTTER_CHANGES`,
   `NO FURTHER CHANGES`, and markdown-wrapped `needs_changes` parse as intended.
   The prompt explicitly tells reviewers to copy the verdict token
   character-for-character.
4. Model retries happen only for connection-phase `OSError`s before response
   reading begins. Read-phase failures are not retried.
5. Sticky comment lookup paginates PR comments up to a sane cap before creating
   a new sticky comment.
6. Provider-error handling prints diagnostic detail to stdout before attempting
   any GitHub write, wraps the fail-open comment write, and still exits non-zero
   with a clear message if GitHub is unavailable.
7. Spec 017 documents that maintainers may manually apply `expert-review` at any
   time to trigger Claude review, and that manual application is not blocked by
   GitHub's `GITHUB_TOKEN` anti-recursion rule.
8. `python scripts/cheap_review.py --self-test` passes offline with cases for
   extra-body defaults/override/invalid JSON, tolerant verdict matching,
   multi-line SSE data, finish-reason capture, and empty-content diagnostics.
9. Ruff is clean for the touched script.
