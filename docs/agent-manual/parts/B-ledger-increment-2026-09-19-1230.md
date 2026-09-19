# Area B explicit file-coverage increment — 2026-09-19 12:30 Europe/Rome

MAPPING_STATUS: IN_PROGRESS

This is durable source evidence for consolidation into the canonical `## EXPLICIT FILE COVERAGE LEDGER` in `B-frontend-operator-ux.md`. It is B-only and MUST NOT be interpreted as global-union coverage. The canonical map's pre-existing `MAPPING_STATUS: COMPLETE` remains non-defensible until literal fresh-tree reconciliation proves every B-owned tracked file has exactly one canonical ledger row.

Fresh run-start evidence: PR #660 head `f2400820f26634253c97c2a7a52327e5a4463d1e`; base/master `240d5e0b27d9837d40f47bddfa24871ae7a2a4bb`; PR open on `docs/capability-map-B-frontend-ux`.

## EXPLICIT FILE COVERAGE LEDGER — inspected increment

| path | status | concise role/reason |
|---|---|---|
| `frontend/index.html` | READ | Vite HTML entry shell: viewport/title, `#root` mount target, and `/src/main.tsx` module bootstrap; no product/domain authority. |
| `frontend/package.json` | READ | Frontend package manifest. Pins React/Three/Vite/TypeScript dependencies and defines localhost dev/preview plus the production build gate chaining contract tests, `tsc`, and Vite build. |
| `frontend/package-lock.json` | GENERATED/ASSET | npm lockfile v3 for `jarvisos-frontend`; identity/purpose verified from root package record and resolved dependency entries. Locks the manifest dependency graph; not runtime capability evidence. |
| `frontend/tsconfig.json` | READ | Strict no-emit ES2020/DOM TypeScript configuration for `src`, using ESNext modules, Node resolution, isolated modules and React JSX transform. |
| `frontend/vite.config.ts` | READ | React Vite config; dev server binds `127.0.0.1:5173` and proxies `/api` to `http://127.0.0.1:8000` without changeOrigin/TLS. Development transport configuration only. |

## Failure-boundary notes

- `package.json` build success is a composite source/contract/type/bundle gate, not proof of arbitrary rendered browser behavior.
- `vite.config.ts` defines the development proxy only; it is not evidence for production deployment routing or remote-network exposure.
- The lockfile is dependency reproducibility evidence, not semantic evidence that any dependency-backed feature is wired or usable.

UNACCOUNTED_FILES: NOT_YET_RECONCILED
NEXT: continue literal tracked-file inspection under `frontend/public/`, `frontend/src/`, `frontend/tests/`, then canonical design-reference assets; consolidate all durable increments into the canonical ledger before asserting zero.
