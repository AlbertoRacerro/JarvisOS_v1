# Area B explicit file coverage ledger increment — 2026-09-17T19:33Z

MAPPING_STATUS: IN_PROGRESS

This is a B-only durable increment for consolidation into the canonical `## EXPLICIT FILE COVERAGE LEDGER` in `B-frontend-operator-ux.md`. It does not establish global-union completion and contains no Area-A ownership rows.

| path | status | concise role/reason |
|---|---|---|
| `frontend/package.json` | READ | Directly inspected. Private ESM frontend package; pins React 18.3.1, Three 0.171.0, Vite 6.0.5 and TypeScript 5.7.2. Defines the authoritative frontend dev/build command chain: build executes the named 058d/100/100f/100g/112/113/114/115/116/117/124/140/143 contracts plus eyebrow contrast, then `tsc` and `vite build`. |
| `frontend/vite.config.ts` | READ | Directly inspected. Vite React configuration binds the development server to loopback `127.0.0.1:5173` and proxies `/api` to loopback backend `127.0.0.1:8000`; no external dev-server bind or alternate API target is defined here. |
| `frontend/tsconfig.json` | READ | Directly inspected. Strict no-emit React/ES2020 TypeScript boundary for `src`, with DOM libs, isolated modules and JSON-module resolution; this file defines compile-time frontend constraints rather than runtime behavior. |

## Run reconciliation

Fresh PR head at run start: `aa63b191cf42e3302b05fa5b5b0be3f97ad49f8c` on `docs/capability-map-B-frontend-ux` / PR #660. A recursive tracked-tree read was taken from that exact head before these inspections. Literal exhaustive reconciliation of all B-owned tracked files is still pending, so `UNACCOUNTED_FILES: 0` is not asserted and any stale canonical `MAPPING_STATUS: COMPLETE` remains non-authoritative until consolidation plus a fresh exact tree comparison proves zero unaccounted files.
