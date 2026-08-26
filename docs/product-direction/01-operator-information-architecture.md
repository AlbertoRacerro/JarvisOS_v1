# PD-01 — Operator information architecture

Status: future product direction; not implementation authority.

## Purpose

Define the stable top-level user mental model for JarvisOS. The product must expose work concepts, not backend table names or historical implementation slices.

## Primary navigation

Normal primary navigation is exactly:

- `Design`
- `Memory`
- `Development`
- `Coding`
- `Settings`

Do not add `Home`, `Runs`, `Engineering Data`, `Review`, `Evidence`, `Files`, `History`, or `Lineage` as peer primary destinations unless the maintainer explicitly revises this contract.

## No normal Home dashboard

JarvisOS should reopen the last useful workspace. If no previous route exists, the default may be `Design > Process`.

Backend/database/provider health does not justify a Home dashboard. Global health is represented compactly beside the `JARVIS OS` brand, for example `JARVIS OS ●`.

The global health indicator:

- green: normal operation;
- amber: degraded but usable;
- red: runtime/backend failure requiring attention.

Clicking it may open a compact status popover. Detailed diagnostics belong in `Settings > System`.

## Cross-workspace shell invariants

- Keep the primary rail narrow and persistent.
- Use the approved light-first warm-white/limestone visual identity and chlorophyll green as an accent, not as a large ambient background.
- Use official Phosphor icons for generic application/tooling iconography.
- Prefer nearly square controls and surfaces with small radii rather than pill-heavy UI.
- Avoid dashboard-like oversized cards when simple rows, dividers, tabs, status text or compact panels communicate the information more directly.
- A right-side Jarvis panel is present where conversation materially assists work. It is not required in Settings.

## Context instead of duplicate destinations

Information that is useful while working but not itself a primary workspace should appear as compact contextual anchors, drawers, panels or search results.

Examples:

- current model version;
- latest run/result state;
- stale dependencies;
- lineage/provenance;
- review/proposal count;
- runtime/Git state;
- system health.

These anchors may deep-link to their canonical owning context; they must not create parallel copies of the underlying record.

## Ownership map

`Design` owns current engineering editing.  
`Memory` owns authoritative project knowledge.  
`Development` owns future work and non-authoritative ideas.  
`Coding` owns JarvisOS software development, repository/runtime state, and JarvisOS-internal software knowledge.  
`Settings` owns operator configuration, AI/provider controls and system diagnostics.

## Critical separation: project memory vs JarvisOS self-knowledge

The normal `Memory` workspace is **project memory only**. JarvisOS architecture decisions, code knowledge, implementation contracts, repository history and self-development knowledge do not appear as a second scope inside project Memory.

JarvisOS software knowledge is exposed only inside `Coding`, primarily through Coding search and context panels.

## User-facing naming rule

Do not derive navigation labels mechanically from database tables or module names. A backend may retain artifacts, events, runs, proposals, evidence records, files or memory records internally while the UI presents them under the work concept that owns them.
