# 164 — Coding control room

State: **ready**. Combined definition, contract and readiness under the maintainer directive of 2026-10-01. Dependencies 118, 140 and 160 are merged. This spec owns the `/coding/runtime` surface in `CodingWorkbench` and one read-only backend projection.

## Fresh evidence (master `fc34a316`)

- `GET /api/coding/runtime-truth` already gives:
  - the startup and live local SHA, branch and dirty state;
  - the GitHub-resolved remote SHA;
  - alignment, ahead/behind and the changed files.
- The Runtime page shows these as sparse cards. It also has a manual PR/spec pipeline form.
- No endpoint lists spec rows. Only a single-row parser exists (`pipeline_state.py`).
- Chronological completed work can be derived without `gh`. Every first-parent merge on `origin/master` reads `Merge pull request #N from <owner>/<kind>/<spec>-<slug>`.
- `STATUS.md` currently has 0 `ready`, 0 `in_progress` and 0 `in_review` rows. An honest "upcoming" view must therefore cope with an empty authorized queue and with planned rows that are deferred or trigger-gated.

## Decision

Keep Repository (code browser) and Runtime as separate pages. They answer different questions: "what is the code?" versus "what is running, what landed, what is next?". Runtime becomes the compact maintainer control room.

## Accepted capability

1. **Runtime truth.** Local running code identity and remote target identity sit side by side, with:
   - alignment or mismatch;
   - dirty state;
   - change since startup;
   - backend build or runtime identity, from available process facts such as the startup SHA and start time.
   Technical fields go behind disclosure.
2. **Recent work.** Recently completed work is listed in chronological order from first-parent merge commits on the target ref. Each entry shows:
   - the spec id, or "maintenance" when none is derivable;
   - a short human name joined from the registry row;
   - the lifecycle kind (plan, implementation, reconcile);
   - the current registry state;
   - PR, SHA and time behind disclosure.
3. **Upcoming work.** Registry rows not yet `merged` or `cancelled`, ordered by authority, then by dependency readiness:
   - first `in_review`, `in_progress` and `ready`;
   - then `planned` rows whose dependencies are all merged;
   - then `blocked`.
   Each row shows its id, short name, status and dependency readiness. An empty authorized queue is stated truthfully. The view never invents ordering from numeric ids.
4. The manual pipeline inspector stays available behind secondary disclosure.

## Boundaries / non-goals

- The projection is derived and read-only from canonical sources: git at the target ref and `docs/specs/STATUS.md` at that ref, plus the existing runtime-truth service.
- No hand-maintained queue.
- No new store.
- No GitHub mutation.
- No `gh` dependency in the backend.
- Repository browser (160) behaviour is unchanged.

## Required evidence

- **Backend tests** for registry parsing, merge-subject parsing (including multi-spec and non-spec branches), ordering, and fail-closed warnings.
- **Real Chromium** on the canonical host at 1280 and 1440 px, with no horizontal overflow and the live data inspected for correctness against `git log` and STATUS.
- Exact-head CI green.
