# WP5 — Hermes integration kernels and roadmap re-scope

Date: 2026-07-13

## Scope

Docs and registry planning only. This work adds kernels for:

- `066 HERMES-PASSTHROUGH-0`;
- `067 JARVIS-MCP-0`;
- `068 HERMES-CONFIG-0`;
- `069 MEMORY-CONSOLIDATE-0`.

It re-scopes spec 060 as the Hermes integration umbrella and marks specs 030,
031, 034, and 036 superseded in part while preserving their thin JarvisOS-side
contracts.

No runtime, schema, provider, dependency, workflow, frontend, test, or merged
059a implementation file is changed.

## Reconstruction

The branch is reconstructed directly from post-#97 master commit
`7358bd0c2f2d19585a76e0eaf97fa778f015a8b2` through a six-entry tree containing
only the four kernels, canonical registry, and this report.

Its final diff is exactly:

- `docs/specs/066-hermes-passthrough-0.md`;
- `docs/specs/067-jarvis-mcp-0.md`;
- `docs/specs/068-hermes-config-0.md`;
- `docs/specs/069-memory-consolidate-0.md`;
- `docs/specs/STATUS.md`;
- this report.

The merged egress foundation, rows 061–064, and the WP3 roadmap order are inherited
from `master`, not duplicated in this PR. All four Hermes rows remain `planned`.

## Runtime facts that changed the kernel wording

1. The current `run_ai_task` path assembles a text prompt and the current
   provider-neutral contracts do not preserve the full OpenAI tool-calling
   exchange Hermes requires. Therefore 066 requires an explicit compatibility
   matrix for messages, tool definitions, `tool_calls`, tool-result IDs,
   `finish_reason`, usage, refusal, and error behavior rather than a text-only
   wrapper.
2. Selecting a custom provider for the main model does not prove that every
   auxiliary, delegated, fallback, compression, or MCP-sampling model call uses
   the same boundary. Spec 068 therefore requires effective-config closure and
   fail-closed preflight.
3. Hermes terminal deny rules are not a filesystem sandbox. Spec 068 requires a
   concrete Windows-first host-isolation boundary and direct provider-egress
   denial.
4. Hermes may classify policy HTTP errors as fallback-worthy. Spec 066 requires
   tested denial, retry, idempotency, and confirmation behavior with no
   ungoverned provider fallback.
5. Hermes exposes MCP text and structured content to the model. Specs 066/067
   therefore require server-owned provenance capsules reloaded by JarvisOS before
   egress; model-visible metadata cannot self-declare sensitivity.
6. MCP sampling and parallel mutation are disabled for the first profile.

## Preserved authority boundaries

- provider credentials remain only in JarvisOS;
- every AI provider attempt traverses `run_ai_task`, policy, budget, egress, and
  `ai_jobs` accounting;
- MCP uses existing service boundaries and never accesses SQLite, the repository,
  or the data root directly;
- Hermes memory/skills are disposable;
- canonical truth enters through MemoryStore proposals and human promotion;
- Hermes cannot own sensitivity, route permission, budget, promotion, or accepted
  engineering state;
- external passthrough execution remains blocked until 059b is merged and active;
- merged PR #90 / 059a remains untouched.

## P1 lifecycle disposition

Spec 060 is a normative, definition-only umbrella. It records the durable Hermes
integration direction but owns no implementation lifecycle and therefore is not a
hard dependency of slices 066–068. Specs 066, 067, and 068 own the normal
kernel → full spec → implementation ladder; their hard dependencies contain only
mergeable implementation prerequisites. The descriptive relationship to umbrella
060 remains intact.

## Roadmap integration

- 059b remains the first runtime-policy blocker.
- 062/061 provide graded evidence and token/economic bounds required by 066.
- 066 and 067 establish the standards-only model/tool boundaries.
- 068 follows only after those contracts and a concrete isolation design are stable.
- 047–049 productive engineering work is interleaved and must not be displaced by
  platform orchestration.
- 069 is the first Hermes dogfood only after 066–068 merge and a local route is
  qualified; it remains proposal-only.

## Verification checklist

- four new kernel files only under `docs/specs/`;
- one canonical registry update;
- one report;
- no implementation PR number assigned to planned rows;
- no status advanced to `ready`;
- no duplicate row IDs;
- specs 030/031/034/036 retain residual JarvisOS contracts;
- spec 060 owns no runtime and points normatively to slices 066–068;
- 060 is not a hard lifecycle dependency of 066–068;
- spec 069 is proposal-only first dogfood.

## Merge gate

Keep draft until:

1. the branch is a bounded delta directly on current `master`;
2. the diff contains exactly the six declared files;
3. GitHub Actions execute and pass on the exact head;
4. a current-head review completes;
5. all findings are resolved or explicitly dispositioned;
6. the maintainer authorizes merge.
