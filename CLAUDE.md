# CLAUDE.md

Read and follow `AGENTS.md` in this directory — it is the single source of agent
instructions for this repo (invariants, test gate, spec workflow, conventions).

Claude-specific notes:

- Strategic/review material lives in `docs/strategy/`; work-item specs in `docs/specs/`.
- Claude is primarily used here for review and analysis (code review of diffs,
  architecture judgment), while implementation slices are usually executed by other
  agents. When reviewing, verify the diff against the spec's acceptance criteria and
  the hard invariants in `AGENTS.md`.
