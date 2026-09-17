# Area B explicit file coverage increment — 2026-09-17 22:30 Europe/Rome

MAPPING_STATUS: IN_PROGRESS

This is B-only durable source evidence for later consolidation into the canonical `## EXPLICIT FILE COVERAGE LEDGER` in `B-frontend-operator-ux.md`. It does not assert global-union coverage. The canonical file still has a stale `MAPPING_STATUS: COMPLETE`; that marker is non-authoritative until exhaustive reconciliation proves literal zero unaccounted B-owned files.

Fresh branch baseline inspected before this increment: `db7e1ce806cef847f645e16bea7bba72ee7bbf0a` on `docs/capability-map-B-frontend-ux`.

## EXPLICIT FILE COVERAGE LEDGER — increment

| path | status | concise role / verification |
|---|---|---|
| `frontend/index.html` | READ | Directly inspected complete HTML entry document: declares UTF-8 + responsive viewport, title `JarvisOS`, single `#root` mount, and loads `/src/main.tsx` as the module entry. |
| `frontend/package-lock.json` | READ | Directly inspected lockfile header/root package and dependency records. npm lockfile v3 for `jarvisos-frontend` 0.1.0; pins React/ReactDOM/Three/Phosphor plus TypeScript/Vite/plugin/types dependency graph and package integrity metadata. |
| `frontend/public/fonts/README.md` | READ | Directly inspected bundled-font provenance manifest. Establishes local-only font policy and exact upstream commits/blob identities for Instrument Sans and IBM Plex Mono assets; explicitly rejects runtime-downloaded/remote-CDN fonts. |
| `frontend/public/fonts/OFL-InstrumentSans.txt` | READ | Directly inspected license header: Instrument Sans Project Authors, SIL Open Font License 1.1. License companion for bundled Instrument Sans assets. |
| `frontend/public/fonts/OFL-IBMPlexMono.txt` | READ | Directly inspected license header: IBM Corp., Reserved Font Name `Plex`, SIL Open Font License 1.1. License companion for bundled IBM Plex Mono asset. |
| `frontend/public/fonts/InstrumentSans-Regular.woff2` | GENERATED/ASSET | Binary asset identity/purpose verified from tracked tree plus provenance manifest: regular Instrument Sans webfont; tracked blob `1e0a9719d54a0b5bb46ad8dabae3cad1a6eee203` matches declared upstream blob. |
| `frontend/public/fonts/InstrumentSans-Medium.woff2` | GENERATED/ASSET | Binary asset identity/purpose verified from tracked tree plus provenance manifest: medium Instrument Sans webfont; tracked blob `1360f22eac6514275f824c522e5329e3336928ea` matches declared upstream blob. |
| `frontend/public/fonts/InstrumentSans-SemiBold.woff2` | GENERATED/ASSET | Binary asset identity/purpose verified from tracked tree plus provenance manifest: semibold Instrument Sans webfont; tracked blob `2285afc8e68c954a07bb438231acb1ca67afb3d2` matches declared upstream blob. |
| `frontend/public/fonts/IBMPlexMono-Variable.woff2` | GENERATED/ASSET | Binary asset identity/purpose verified from tracked tree plus provenance manifest: IBM Plex Mono variable Roman webfont; tracked blob `09a8c306fe9df33ffb8c2ff8edca7cb7025d79a2` matches declared upstream blob. |

## Reconciliation state

`UNACCOUNTED_FILES: UNKNOWN`

Do not mark Area B complete from this increment. Next work should continue literal tracked-file inspection and consolidate all B increments into the canonical ledger only after a fresh recursive B-scope tree comparison. No backend-A rows were added here.
