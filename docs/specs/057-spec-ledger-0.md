# 057 — SPEC-LEDGER-0: spec progress ledger + fast handoff context

Status: ready
Depends on: none (can run in parallel with BLUECAD implementation specs; must not modify runtime behavior)

## Goal

Create a small, deterministic project handoff mechanism so a new chat/agent can answer “what happened, what is active, what is next?” without reconstructing context from memory, issue comments, or stale summaries.

After this slice, JarvisOS has:

- one short canonical handoff file for humans/agents to read first;
- a deterministic script/check that derives the spec ledger from `docs/specs/*.md` plus a tiny explicit active-work section;
- a review rule that every spec PR updates or regenerates the handoff context when it changes spec state;
- no runtime/backend/frontend behavior changes.

## Why

The current workflow loses time when switching chats because the assistant must be re-fed recent state: merged specs, active Codex branch/issue, blocked specs, next recommended slice, and known stale docs. The repo already has specs and PR history, but the information is scattered across spec files, issue comments, PR reviews, and chat memory. This creates repeated handoff cost and increases the chance of starting the wrong next spec.

This slice makes handoff a repository artifact rather than a chat-memory artifact.

## Scope

In scope:

- Add or formalize a canonical handoff file, proposed path:
  - `docs/JARVISOS_CURRENT_CONTEXT.md`
- Add a small standard-library script, proposed path:
  - `scripts/spec_ledger.py`
- The script scans `docs/specs/*.md` and extracts at minimum:
  - spec id and title;
  - `Status:` line;
  - `Depends on:` line when present;
  - first implementation-notes block when present;
  - next ready specs sorted by id;
  - implemented/pending-review specs;
  - blocked specs;
  - stale-index warning if `docs/specs/README.md` disagrees with individual spec files.
- Add a `--write` mode that updates the canonical handoff file.
- Add a `--check` mode that fails if the generated handoff file is stale.
- Add focused tests for the parser/generator using temporary fixture spec files.
- Update `docs/specs/README.md` execution workflow to say: before dispatching a new spec, read `docs/JARVISOS_CURRENT_CONTEXT.md`; after changing spec state, run the ledger update/check.

Out of scope:

- No backend API changes.
- No frontend/UI changes.
- No database schema changes.
- No GitHub API dependency in v0.
- No workflow/Actions changes unless strictly needed for an existing test command.
- No attempt to infer live Codex usage limits or active cloud tasks automatically.
- No automatic merge/dispatch behavior.

## Handoff file contract

`docs/JARVISOS_CURRENT_CONTEXT.md` should remain short enough to paste or read at the start of a chat. It should contain these sections, in this order:

1. `Current active work`
   - active issue/PR/branch;
   - latest known state;
   - human action needed, if any.
2. `Recently merged`
   - last few merged specs/PRs with commit hashes when known.
3. `Next recommended specs`
   - 3-5 candidates with dependency notes.
4. `Known stale/conflicting docs`
   - docs that are not authoritative until updated.
5. `Standing rules`
   - merge requires explicit confirmation;
   - runtime/code/tests beat docs;
   - specs are done only after merge;
   - Codex/model reviews are advisory, deterministic tests are authority.

## Design constraints

- Deterministic output: no current timestamp in generated sections.
- Standard library only.
- Generated sections must be visibly marked, for example:
  - `<!-- spec-ledger:start -->`
  - `<!-- spec-ledger:end -->`
- Manual active-work notes may exist outside generated markers.
- The script must not need network access.
- If the script cannot parse a spec, it must report the file and continue/fail deterministically rather than silently dropping it.
- The output must be concise. This is a handoff file, not a full project report.

## Acceptance criteria

- `scripts/spec_ledger.py --check` passes on a clean checkout.
- `scripts/spec_ledger.py --write` is idempotent.
- Tests cover parsing at least:
  - numeric specs (`038-...`);
  - suffixed specs (`005b-...`);
  - ready / implemented pending review / done / blocked statuses;
  - missing `Depends on:`;
  - stale README index detection.
- `docs/JARVISOS_CURRENT_CONTEXT.md` exists and contains the generated ledger block.
- `docs/specs/README.md` points new agents to the handoff file before selecting the next spec.
- No runtime, provider, AI, frontend, or workflow behavior changes.

## Implementation notes guidance

When this spec is implemented, append an `## Implementation notes` section that states:

- exact command to refresh the ledger;
- exact command to check it;
- whether README index disagreement is warning-only or check-failing;
- how a maintainer should record active in-flight work such as “Codex is working on issue #63”.
