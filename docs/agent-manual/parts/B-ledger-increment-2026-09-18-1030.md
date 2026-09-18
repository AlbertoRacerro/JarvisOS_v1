# Area B explicit file coverage increment — 2026-09-18 10:30 Europe/Rome

MAPPING_STATUS: IN_PROGRESS

This is durable Area-B source evidence for consolidation into the canonical `## EXPLICIT FILE COVERAGE LEDGER` in `B-frontend-operator-ux.md`. It does not assert global-union ownership and does not make the stale canonical `MAPPING_STATUS: COMPLETE` marker authoritative.

Fresh run-start PR head before this commit: `b0f251fb773092e1e20aae8fa0d2fb0764522321` on `docs/capability-map-B-frontend-ux`; fresh master/base: `240d5e0b27d9837d40f47bddfa24871ae7a2a4bb`.

## EXPLICIT FILE COVERAGE LEDGER — verified this run

| path | status | concise role/reason |
|---|---|---|
| `frontend/package.json` | READ | Directly inspected. Frontend package/build contract: Vite dev/preview bind loopback; build serially runs the 058d/100/100f/100g/112/113/114/115/116/117/124/140/143 source contracts plus eyebrow contrast, then `tsc` and Vite build. Pins React 18.3.1, Vite 6.0.5, TypeScript 5.7.2 and Three 0.171.0. No generic frontend codegen script is declared. |
| `frontend/tsconfig.json` | READ | Directly inspected. Strict no-emit browser TypeScript contract over `src`, ES2020/DOM libs, ESNext modules, React JSX, isolated modules and JSON module resolution. It is compile-time verification only and confers no runtime/operator authority. |
| `frontend/vite.config.ts` | READ | Directly inspected. React Vite configuration; dev server binds `127.0.0.1:5173` and proxies `/api` to `http://127.0.0.1:8000` without origin rewriting. This is local development transport wiring, not production/backend capability evidence. |

## Failure-mode notes

- `npm run build` is a strong source/compile/bundle gate but must not be promoted to rendered-browser proof: most named contracts are Node/source checks.
- The dev proxy is explicitly loopback-bound. Documentation must not imply remote/LAN reachability from this configuration.
- `tsconfig.json` uses `skipLibCheck: true`; successful TypeScript compilation therefore does not prove third-party declaration internals were type-checked.

## Remaining coverage state

Literal reconciliation of the complete tracked `frontend/` tree plus canonical operator design-reference files/assets is still pending. `UNACCOUNTED_FILES: 0` is NOT asserted. The next consolidation pass must derive the exact tracked B-owned path set from a fresh recursive tree and compare it path-by-path against explicit READ/GENERATED/ASSET/OUT_OF_SCOPE rows; subsystem-level prose is insufficient.
