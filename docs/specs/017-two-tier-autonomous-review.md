# 017 — Autonomous three-tier review: cheap → senior (GLM) → expert (Claude)

Status: implemented; automatic orchestration superseded by maintainer policy
Depends on: 004 (tiered PR review — this spec superseded its frontier wiring)

## Operational supersession — 2026-07-10

The automatic cheap → senior → expert chain and automatic Codex fix loop are no
longer active. The maintainer found that model reviews produced too many
spec-misaligned findings relative to their API cost and supervision burden.
Current live policy is defined in `AGENTS.md`:

- Cheap and Senior reviews are optional `workflow_dispatch` actions with an
  explicit PR number.
- Expert review runs only after the maintainer manually applies `expert-review`.
- No review workflow mentions Codex, applies readiness/tier labels, triggers
  another review, pushes code, or authorizes merge.
- CI and the human maintainer remain the authority.

The remainder of this document is retained as historical implementation context,
not as the current operating procedure.

## Goal

The review loop runs without the maintainer judging individual findings. The
maintainer's remaining duties are: strategic/architectural decisions (routed to
them explicitly), and the final merge click. Claude stops being the default
second tier — it becomes a rare expert escalation — so the loop keeps working
when Claude credits are exhausted and costs almost nothing when they are not.

## Tier chain

```
push → Cheap review (DeepSeek, every push)
         ├─ NEEDS_CHANGES → @codex fixes → push (loop, max 3 rounds)
         └─ NO_FURTHER_CHANGES → label `frontier-review`
                → Senior review (GLM 5.2, default gate)
                     ├─ NEEDS_CHANGES → @codex fixes → push (re-enters cheap tier)
                     ├─ NO_FURTHER_CHANGES → label `ready-for-merge` → human merge
                     └─ ESCALATE (rare) → label `expert-review`
                            → Expert review (Claude Opus)
                                 ├─ REQUEST_CHANGES → @codex fixes → push
                                 └─ APPROVE → `ready-for-merge` → human merge
```

Every push removes the stale `frontier-review`, `expert-review`, and
`ready-for-merge` labels (cheap tier does this at the start of each run), so a
verdict never survives a changed diff.
The maintainer can trigger the expert (Claude) review on any PR at any
time by manually applying the `expert-review` label; manual application is
exempt from GitHub's `GITHUB_TOKEN` anti-recursion rule.

## Key design points

- **One script, two tiers.** `scripts/cheap_review.py` serves both automated
  tiers via `REVIEW_TIER` (`cheap` | `senior`). The senior tier gets a stricter
  prompt (root cause, integration, cross-file) plus an escalation instruction:
  `ESCALATE: <reason>` directly after the verdict, expected on <1 in 10 PRs.
- **ARCH findings go to the maintainer.** All three tiers are instructed to
  prefix strategy/architecture/licensing/spec-defect findings with `ARCH:`,
  exclude them from the verdict, and never address them to @codex. This is the
  maintainer's decision channel; correctness findings are the agents' channel.
- **Label chain needs a PAT.** Labels added with the default `GITHUB_TOKEN` do
  not fire `labeled` events in other workflows (Actions anti-recursion guard).
  Both label-adding workflows read `LABEL_TOKEN` from the `REVIEW_BOT_TOKEN`
  secret; without it the script falls back to `GITHUB_TOKEN` and appends a
  visible note to the review comment saying the next tier will not auto-start.
- **Round limits bound the loop.** Cheap and senior each stop mentioning
  @codex after 3 rounds and hand the remaining findings to the maintainer, so
  the worst case is bounded regardless of model behavior.
- **Advisory throughout.** No tier approves or merges; `ready-for-merge` is
  informational. Merge authority stays CI + human (AGENTS.md).

## Files touched

- `scripts/cheap_review.py` — `REVIEW_TIER`, senior prompt, `parse_escalation`,
  stale-label cleanup, `LABEL_TOKEN` with fail-visible fallback, ARCH routing.
- `.github/workflows/senior-review.yml` — new (GLM 5.2 via z.ai, label-gated).
- `.github/workflows/cheap-review.yml` — tier/label env, `LABEL_TOKEN`.
- `.github/workflows/claude-review.yml` — retargeted to `expert-review`,
  prompt reframed as expert escalation (answers the ESCALATE question first).
- `.github/workflows/frontier-fallback-review.yml` — deleted; the senior tier
  replaces the manual GLM fallback.
- `AGENTS.md` — Review authority section updated to the three-tier chain.

## Maintainer setup (historical)

1. `REVIEW_BOT_TOKEN` previously drove cross-workflow labels. It is no longer
   consumed by the manual review workflows and may be removed from repository
   Actions secrets after this supersession merges.
2. `expert-review` remains the explicit manual trigger for Claude.
3. Provider API keys remain optional and are consumed only when the maintainer
   deliberately dispatches the corresponding review.
