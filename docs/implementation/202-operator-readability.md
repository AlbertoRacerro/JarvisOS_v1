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

## Real Chromium acceptance on the recovered candidate

Recovered candidate source: merge commit `9a3dcfd3e167caba7ab63b544247a1011b866609`
(the spec 202 product tree of `301201cf` merged with master `42ce1a84`).
Baseline source: `0d6a68ae28b9c6d1fbb11e7d9046122b7b4ba420`.
The registry conflict was resolved by retaining merged 201/203 facts and placing
202 in review; `python3 scripts/check_spec_status.py` passed at the recovered
candidate. No product file conflicted.

On 2026-10-21, local Playwright 1.55.0 used its cached real Chromium 1187
against two isolated FastAPI/SQLite backends. Each backend served its own
built `frontend/dist` at the same origin as its API, on a fresh data root
bootstrapped with `app.core.bootstrap`. Builds set `VITE_API_BASE_URL=` so
browser requests used that origin. Provider defaults stayed fake, paid AI off,
and budget zero. No provider or Studio code execution was enabled.

Before/after screenshots covered Settings Appearance and the Engineering Studio
at 1365×900 and 390×844 in both light and dark themes: 16 real-browser captures.
All 16 had no JavaScript page errors or horizontal overflow. Selected captures
are in [evidence-202](evidence-202/). Visual inspection confirms the baseline
light canvas / near-invisible dark heading defect, the recovered dark surfaces,
readable shared navigation and responsive wrap, and the intentional removal of
repeated introductory copy. The Settings AI tab loaded real fake-mode policy,
provider and budget projections at narrow width; its screenshot is included.
The Studio `+ New model` action opened the dense calculation form in both
versions; paired narrow/dark screenshots show retained fields and controls with
the candidate's shorter copy. The runtime-disabled and scientific qualification
notices stayed visible.

Interaction checks on the candidate: selecting Dark changed the root theme;
Settings AI displayed its permission/budget section; opening the Studio form
preserved the runtime warning; Tab reached the Process control with a visible
solid focus outline. No horizontal overflow occurred in that flow. The full
frontend build, including rendered-header and contrast tests, passed again at
the recovered source. The exact diff changes no backend, API, routing, data,
scientific, permission or execution code.

This is visual acceptance for the bounded spec 202 readability/copy pass. It
does not claim scientific-run, provider, user-code or workstation acceptance.
