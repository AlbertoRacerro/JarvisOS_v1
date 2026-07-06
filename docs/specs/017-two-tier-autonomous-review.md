# 017 — Autonomous three-tier review: cheap → senior (GLM) → expert (Claude)

Status: implemented (pending live smoke)
Depends on: 004 (tiered PR review — this spec supersedes its frontier wiring)

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

## Maintainer setup (one-time, before first run)

1. **Create the `REVIEW_BOT_TOKEN` secret** — without it the chain stalls
   between tiers (visible note in the review comment, nothing breaks):
   GitHub → Settings (profile) → Developer settings → Fine-grained tokens →
   generate a token scoped to `JarvisOS_v1` with *Pull requests: Read and
   write* and *Issues: Read and write*; then repo → Settings → Secrets →
   Actions → new secret `REVIEW_BOT_TOKEN`.
2. Labels `expert-review` and `ready-for-merge` — already created (2026-07-06).
3. `GLM_API_KEY` — already present. `DEEPSEEK_API_KEY` — already present.
4. After merge, delete the now-unused `frontier-review-fallback` label.

## Acceptance criteria

1. A push to a non-draft PR runs the cheap review; on `NO_FURTHER_CHANGES` the
   `frontier-review` label is applied and (with `REVIEW_BOT_TOKEN` set) the
   senior review starts on its own.
2. Senior `NO_FURTHER_CHANGES` applies `ready-for-merge`; senior
   `NEEDS_CHANGES` mentions @codex; a senior `ESCALATE:` line applies
   `expert-review` and the Claude workflow starts.
3. The Claude workflow no longer triggers on `frontier-review`.
4. A new push removes all three verdict labels before anything else runs.
5. Without `REVIEW_BOT_TOKEN`, the review comment carries the explicit
   "next tier will NOT start on its own" note instead of failing silently.
6. `--self-test` passes offline; both workflows parse as YAML.

## Residual risks (accepted, watched at smoke)

- **Codex may ignore bot mentions.** The @codex fix loop assumes Codex reacts
  to mentions posted by github-actions. Verified for the Claude-posted
  mentions historically; the bot-posted path is confirmed at the first live
  smoke. If Codex ignores bots, the maintainer re-mentions manually and we
  move the mention into a PAT-authored comment.
- **GLM verdict quality is unmeasured.** The senior tier has never gated a
  real merge. First PRs: maintainer skims the senior comment before merging;
  confidence grows from the miss-rate observed when expert reviews run.
- **Escalation calibration unknown.** GLM may escalate too often (burns Claude
  budget) or never (expert tier goes unused). Watch the rate over the first
  ~10 PRs; tune the prompt threshold wording if needed.
- **`glm-5.2` model id / endpoint** confirmed from Z.ai docs 2026-07-06; if the
  API 404s, check `https://docs.z.ai` for the current id.
- **Data egress:** the pack (diff + spec + AGENTS excerpts) already goes to
  DeepSeek (China) per the 004 maintainer decision; GLM via z.ai is the same
  accepted posture. Redaction rules for workspace/project context still apply.
