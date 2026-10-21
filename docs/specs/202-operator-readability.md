# OPERATOR-READABILITY-1

Accepted outcome and readiness: maintainer request of 2026-10-20, followed by
the explicit instruction to perform the work now, not through an automation.
Live state is recorded only in STATUS.md.

## Scope and direction

A bounded readability and copy pass on the existing green/mineral identity,
not the alternative art-direction selection or full redesign of spec 198.
Use the repository-owned React and browser-proof skills and the relevant audited
readability techniques from the visual-design draft. No new dependency.

- Restore the intended 12/13/14px metadata/label/body scale at default browser
  settings, while respecting the user's browser font-size preference.
- Remove redundant workspace/settings introductions and obvious Studio usage
  instructions. Retain errors, empty states, runtime availability, scientific
  qualification, units, provenance and all permission/action boundaries.
- Make shared workspace headings and peer navigation readable and theme-aware;
  preserve names, routes, active state, focus and responsive wrapping.
- Improve muted text contrast on the existing semantic surfaces.

Brief: primary green and accents remain user-configurable; existing surface
roles, font families, radii and spacing scale are reused; compact navigation,
comfortable text, no new ornament or motion. The content is the focal point.

## Acceptance and boundaries

Run the full frontend build and focused regression checks, including actual
rendered markup for removed copy/preserved controls and contrast calculations
for changed text tokens. Inspect the exact diff for unchanged behavior.
Real-browser before/after checks at wide and narrow widths and in both themes
are required before declaring visual acceptance or merging. If that environment
is unavailable, retain a tested draft PR and state the missing evidence.

No backend, API, provider, routing, storage, numeric-format, scientific-contract,
unit, permission or execution changes. Do not modify frozen backend conformance
tests. Existing non-frozen visual tests may be updated only where this accepted
change intentionally replaces literal hardcoded colours with semantic tokens.
