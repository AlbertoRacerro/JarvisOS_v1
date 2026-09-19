# Area B explicit file coverage increment — 2026-09-17T0232Z

MAPPING_STATUS: IN_PROGRESS

Area B only. These rows are direct-read evidence for the required canonical `## EXPLICIT FILE COVERAGE LEDGER` in `B-frontend-operator-ux.md`. They do not alter Area A/C/D ownership. Canonical consolidation remains blocked by the connector's bounded read + whole-file replacement write shape; this increment preserves verified evidence without risking destructive truncation.

| path | status | one-line role/reason |
|---|---|---|
| `frontend/src/components/ai/JarvisKnowledgeActions.tsx` | READ | Operator knowledge-action UI builds an exact-ref context basket, re-previews on add/remove, rejects changed inspected refs, binds advisory proposals to server-previewed context, and states explicitly that proposal generation performs no domain mutation. |
| `frontend/src/components/ai/JarvisSidecar.css` | READ | Jarvis sidecar layout stylesheet: constrains scrolling/composer regions, hides local/stage context by default unless explicitly visible, wraps evidence safely, and collapses header/transcript metadata grids at 48rem. |
| `frontend/src/components/ai/useJarvisSidecar.tsx` | READ | Jarvis advisory sidecar controller: isolates stale async responses with ownership generations, uses inspected context digests, preserves request IDs/digests for uncertain idempotent retry, forces refresh on 409 context drift, and exposes canonical flow/persistence/attempt/proposal evidence in the transcript. |

## Capability facts

- Local route/selection descriptors are deliberately not provider context: the UI says they stay local, while provider context is the separately inspected project pack.
- Context-enabled thread dispatch is blocked unless an inspected digest exists. A 409 invalidates the pending submit and requires the operator to inspect the refreshed digest before sending again.
- For non-409 uncertain submission failures, unchanged text retains the same request ID and inspected digest, making the UI retry path explicitly idempotent rather than silently creating a new interaction.
- Workspace, route, selection, thread-detail, preview and submit changes increment ownership generations so late async responses cannot overwrite the currently selected operator context.
- Knowledge-action basket mutations compare exact workspace/owner/kind/id/version/revision/immutable-ref/content-digest identity; changed evidence is surfaced as stale rather than accepted by stable display ref alone.
- Knowledge proposals remain advisory: the UI surfaces target domain, proposed items and authoritative next action while explicitly stating that no domain mutation occurred.

## Remaining coverage

Literal Area-B completion is not yet proven. Remaining scope includes `frontend/package-lock.json`, `frontend/public/`, unledgered API/components/pages/stages/styles/helpers/tests, and canonical behavior/appearance assets under `docs/design-references/`, plus safe consolidation of all verified rows into the canonical ledger.

UNACCOUNTED_FILES: NOT_YET_ZERO
