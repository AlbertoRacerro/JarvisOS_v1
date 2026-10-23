# STUDIO-DEMONSTRATOR-1 — AI-prepared Engineering Studio example workspace

Accepted outcome and readiness: binding roadmap directive
`L20261022122708-233d` (P1 "Engineering Studio demonstrator": "An accessible,
AI-prepared example workspace with verified artifacts: a pipe hydraulic
calculation, a parametric geometry, a custom process unit and a procedure.
These must be real Studio artifacts, visible and editable through the normal
UI, not screenshots or hardcoded mockups. The maintainer will inspect them
before deciding whether notebook/spreadsheet integration advances."). It
builds on the merged Studio categories of specs 188 (calculation), 189
(geometry), 190 (process unit) and 191 (procedure). Live state is recorded
only in STATUS.md.

## Outcome

The operator can open, from the Studio surface, a dedicated example
workspace whose Studio library holds four published, verified artifacts
prepared by the AI coordinator:

1. **Pipe hydraulic calculation** — a single-phase pressure-drop calculation
   for a straight circular pipe (velocity, Reynolds number, Darcy friction
   factor across laminar and turbulent flow, pressure drop and head loss)
   from flow, diameter, length, roughness and fluid properties, in declared
   units.
2. **Parametric geometry** — a build123d part with dimensional inputs
   relevant to the photobioreactor domain (for example a flanged tube spool),
   producing the normal Studio geometry artifacts.
3. **Custom process unit** — a steady-state Studio process unit with declared
   ports and parameters that conserves mass, compounds and culture species
   under the host balance checks, placeable from the Process palette.
4. **Procedure** — a declarative culture procedure (for example a
   draw/separate/refill/dose harvest cycle) tested against a small culture
   loop Process draft created in the same workspace for that purpose.

"Verified" means each artifact is published only through the normal Studio
test-then-publish path with a passing report, and its test cases carry
expected values computed independently of the artifact source (closed-form
or hand arithmetic recorded in the repository tests), not values read back
from the artifact itself. Every artifact states in its assumptions that it
was AI-prepared, its validity range, and that it remains scientifically
unqualified, as all Studio publications are.

"Accessible and editable through the normal UI" means the artifacts are
ordinary Studio drafts and published versions: they appear in the Studio
library, open in the existing editor tabs, can be revised into a new draft,
edited, re-tested and re-published, and the calculation and geometry can be
selected for the existing calculation/generation run flows.

## Scope

- Repository-owned demonstrator content (contracts, sources, test cases,
  assumptions) and a backend owner that creates the example workspace and
  drives the existing Studio, process-draft and workspace services to create,
  test and publish the four artifacts.
- One explicit, idempotent typed action to create or open the example
  workspace, guarded like the existing Studio runtime actions, with a typed
  refusal when the Studio runtime is unavailable or disabled; a repeated
  request returns the existing example workspace without duplicating or
  overwriting it, including after the operator has edited it.
- A compact Studio control that triggers that action and switches to the
  example workspace, with busy, success and refusal states.

## Non-goals and boundaries

- No change to Studio category contracts, the runtime sandbox, publication
  semantics or any existing persistence schema beyond what the demonstrator
  needs to find its own workspace again; no new runtime dependency or network
  egress.
- No automatic seeding at startup and no change to the default workspace.
- No notebook or spreadsheet integration (the maintainer decides that after
  inspecting this result), no scientific qualification claim and no new
  solver capability.
- The demonstrator never commands equipment; the procedure keeps the existing
  simulation-only notice.

## Acceptance

- Backend tests on the exact head create the example workspace through the
  typed action and check: four published artifacts of the four categories
  with passing reports bound to their current source and contract; the
  calculation outputs agree with an independent closed-form computation in
  the test across laminar and turbulent cases; the geometry volume agrees
  with its analytic volume; the process unit closes its balances; the
  procedure test passes against the example Process draft; a repeated action
  is idempotent; an edited (revised) artifact is not overwritten; the
  runtime-unavailable refusal creates nothing.
- Frontend build, type check and test suite pass.
- Real-Chromium evidence, recorded in an implementation note: the Studio
  control opens the example workspace; each artifact opens in the normal
  editor; the calculation runs through the existing run flow and the geometry
  shows its generated preview; one artifact is revised, edited, re-tested and
  re-published; no page or console errors.
