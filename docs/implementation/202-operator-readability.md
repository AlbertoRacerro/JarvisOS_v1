# Operator readability — evidence, 2026-10-20

PR: [#849](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/849).
Baseline: `0d6a68ae28b9c6d1fbb11e7d9046122b7b4ba420`.
Tested product source: tree `d3d227d5475341da267395710e2cc3d0701f75ed`
under commit `301201cfe5c789345c8e07d7e1af36baf87114f9`.
Subsequent evidence/registry changes do not alter that product source.

## Implemented

- Root font size respects the browser's default; body size stays on its own
  token. At a 16px browser default, captions/labels/body are 12/13/14px rather
  than 10.5/11.375/12.25px in explicitly rem-sized elements. Browser zoom and
  custom font defaults are not disabled. Tabular figures and 1.5 body leading.
- Shared workspace/navigation text uses semantic type and theme roles, wrapping
  peer tabs, preserved route names/current-page state, and explicit link focus.
- Removed redundant workspace and Settings introductions, calculation-wizard
  prose and repeated Studio empty-state instructions; concise field/action
  names. No handler or disabled predicate changed. Runtime availability,
  scientific qualification, unit conventions, stale/superseded state and the
  Draft/Test/Publish boundary remain visible.
- Rail/canvas backgrounds no longer force light colours under dark text tokens.
- Muted text light token changed from `#758078` to `#606b63`.

## Deterministic evidence

`npm ci --no-audit --no-fund`, `npm run test:202`, full `npm run build`
(including all existing frontend gates, test:202, TypeScript and Vite),
`python3 scripts/check_spec_status.py`, and `git diff --check`: PASS.
The bundle-size advisory remains; no unrelated bundling refactor was attempted.

The new test renders the actual React header with the actual AppLink, checks
route/current-page semantics, tests the intended root/body ownership, and checks
preservation of important Studio disclosures. It computes 30 contrast pairs
(primary/secondary/muted text on five semantic surfaces in both themes).
These pass 4.5:1; this is token evidence, not whole-application accessibility.

| Light muted text background | Before | After |
| --- | ---: | ---: |
| Surface `#fbfcf8` | 3.98:1 | 5.39:1 |
| Raised `#ffffff` | 4.11:1 | 5.55:1 |
| Subtle `#e9eee7` | 3.49:1 | 4.72:1 |

Two existing non-frozen frontend visual tests were changed solely to replace
literal warm-light colour requirements with semantic colour roles and to remove
the obsolete description grid row. No backend conformance test changed.

## Actual browser observations and missing proof

The available cloud browser cannot reach a Vite server at its own localhost.
An available workspace preview exposed the real frontend at
`http://terminal.local:4173/settings/appearance`. A separate pristine worktree
at the baseline head and the candidate were served successively, not as two
concurrent Vite instances. Viewport screenshots were 1363×936.

Observed both themes through the real Appearance radios. Baseline dark mode
showed an almost invisible heading and identity over a hardcoded light canvas.
Candidate dark mode displayed the heading, identity and navigation clearly on
dark surfaces. Candidate light mode retained the controls and removed the
redundant introduction. Active radio state, current Settings route, loading and
real `Failed to fetch` state remained observable. Screenshots were inspected
in the interactive session, not committed as durable image artifacts.

A real isolated backend was attempted, using a separate scratch data root and
safe defaults. Imports succeeded and uvicorn reported startup; optional PBR
warm-up reported absent CoolProp. The preview still could not reach that
separate runtime. No backend connectivity, solver, Studio lifecycle, dense data,
or scientific result claim is made. Browser zoom keys did not change the
observed viewport; they are not narrow-width proof. Keyboard-flow, narrow-layout,
populated engineering-screen and complete before/after parity remain unproven.

Therefore the PR remains draft and unmerged. Do not interpret deterministic
green checks or these Settings screenshots as complete visual acceptance.
No workstation deployment, runtime-data migration, credential change or paid
provider execution was performed. The mistakenly scheduled UI automation was
disabled at the maintainer's explicit request; no replacement was created.
