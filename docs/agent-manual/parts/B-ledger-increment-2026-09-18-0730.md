# Area B explicit file coverage ledger increment — 2026-09-18 07:30 Europe/Rome

MAPPING_STATUS: IN_PROGRESS

This increment is durable Area-B-only source evidence for later consolidation into the canonical `## EXPLICIT FILE COVERAGE LEDGER` in `B-frontend-operator-ux.md`. It does not claim global-union ownership and does not alter Area A/C/D ownership.

| path | status | concise role/reason |
|---|---|---|
| `frontend/src/theme.ts` | READ | Directly inspected. Defines operator appearance/accent preference types, localStorage keys and safe persistence, system dark-mode resolution/subscription, custom accent normalization, WCAG-style 4.5 text-contrast fallback logic, CSS-variable application, and visual-preference change events. Persistence is deliberately best-effort/visual-only and carries no application authority; unavailable/invalid storage or media-query APIs fall back safely. |

## Operator/failure-mode notes

- Custom accents are accepted only as normalized six-digit hex values; invalid custom values fall back to the `microalgae` preset.
- Appearance and accent persistence tolerate unavailable/throwing `localStorage`; this prevents visual preferences from becoming an application-availability dependency.
- Accent text foreground checks a 4.5 minimum contrast ratio against the resolved surface and falls back to black/white when the seed is insufficient.
- `system` appearance tracks `prefers-color-scheme` when available, with legacy `MediaQueryList.addListener` compatibility.
- Visual preference writes dispatch a local event even if persistence fails, so same-page consumers can converge on the requested visual state without implying durable storage succeeded.

UNACCOUNTED_FILES: NOT_YET_PROVEN_ZERO
