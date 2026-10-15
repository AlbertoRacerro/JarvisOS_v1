# 193 — Sidecar proposals for Engineering Studio drafts

State: **accepted and ready** under the 2026-10-15 maintainer directive, after recovery against `a6ce2259cd25c5d2b9d1a5755c54e3118bec7f72`.

Hard dependencies: 166, 187, 188, 189, 190 (all merged).

## Outcome

An engineer describes a calculation, build123d geometry, or steady custom process unit in ordinary language. Jarvis Sidecar returns a bounded proposal containing a readable variable/port contract, Python source diff, assumptions, and provenance. Explicit **Apply** creates a Studio draft or updates a selected open draft at its exact revision. The engineer can edit, Test, and Publish through the existing Studio owner. The Studio page presents code and AST-derived mathematics together, with source freshness and diagnostics visible.

The current Sidecar is deliberately absent from Studio (`frontend/src/App.tsx`), and 166 workspace actions accept only Process and BLUECAD (`backend/app/modules/workspace_actions/models.py`). Studio draft creation/update and isolated Test/Publish already exist (`backend/app/modules/studio/service.py`). These are the missing links, not a reason for a second AI execution system.

## Authority and scope

- Extend the existing Sidecar/Hermes/Relay proposal path and durable workspace-action provenance for a `studio` surface. Product AI generation continues through `run_ai_task`/`ai_jobs`; `route_class="auto"` never executes an external provider. The proposal is inert data and never executes source while parsing, previewing, or applying.
- Allow exactly the existing Studio executable categories: `calculation`, `geometry`, and `process_unit`. The worker may propose a new draft or a change to a selected open draft. The proposed contract is validated by the relevant Studio category models. A new proposal may include bounded source and assumptions; an update must carry the selected draft identity and exact source/contract revision. Revalidate all fields and revision at Apply in the Studio owner, atomically. A stale or foreign draft is refused without partial writes.
- The operator sees the contract in engineering terms: named inputs, outputs or ports, units, bounds, assumptions, source diff, and any limits. The code remains visible and editable. Apply is explicit for local Hermes and Relay. Dismissal leaves Studio unchanged. Applying a proposal creates or updates a **draft only** and clears prior test evidence when source or contract changes. Test and Publish remain separate explicit operator actions subject to 187–190 checks.
- Reuse the 166 origin and request digest lineage. Store enough proposal content to recover a review card without relying on a transient model transcript. Do not place secrets in the brief, card, logs, or AI context. A model cannot choose a runtime profile, capability, provider, or publication state.
- On Studio, show an owner-derived, bounded context chip and enable Sidecar. In the calculation editor, place code and read-only AST-derived equations/variables/diagnostics in a responsive split view. Narrative annotations and assumptions may be edited; equations remain derived from Python. Show when annotations or a displayed test report refer to an older source. Reuse existing editor and derived-document service. No notebook runtime.

## Acceptance and evidence

1. Real browser on exact head: ask Sidecar for a calculation, a parameterized helical baffle, and a nutrient-dosing steady unit; inspect readable contract, code diff, and assumptions; Apply each to a Studio draft; edit, Test, and Publish using Studio UI. Demonstrate at least one update proposal and stale-Apply refusal. Screenshots and `ai_jobs`/workspace-action provenance are from actual execution.
2. Deterministic tests prove malformed category/units/source, oversized source, foreign workspace, stale revision, repeated local turn, and Relay origin cannot create a draft or execute code. Only one draft mutation follows one Apply. Changed content invalidates test evidence. `auto` does not call an external provider. 187 sandbox hostile tests remain valid.
3. Browser proof shows code and derived equations side by side; editing source refreshes equations and marks stale annotations/test evidence without treating narrative as executable truth. Responsive layout remains usable at laptop width.
4. Relevant backend tests, full backend suite and Ruff, frontend build and focused UI tests pass. No claim of scientific validation follows from software success.

## Non-goals

No automatic Test, Publish, BLUECAD placement, Process solve, paid-provider enablement, notebook, new execution sandbox, or product Hermes skill installation. Scientific model qualification remains separate.
