# Process workspace — beta approved visual reference

**Maintainer decision:** 2026-08-26  
**Target route:** `/design/process`  
**Golden image:** [`process-beta-approved-2026-08-26.jpg`](./process-beta-approved-2026-08-26.jpg)  
**Canonical viewport:** 1365 × 768  
**Reference image SHA-256:** `e48503c97f4914ee70dab2b0051d6b08129e1aa548ca36be89beb7c065a5dd66` for the original approved render before repository JPEG compression.

## Status and authority

This is the maintainer-approved **beta visual target** for the Process workspace. The golden image is the primary visual reference for a later authorized implementation. This file does **not** itself authorize runtime work, release the post-100 visual-inspection hold, alter `docs/specs/STATUS.md`, or grant any process-engine/backend authority.

A later builder must use this artifact instead of reconstructing the target from chat history.

## Hard visual requirements

- No global white top utility bar containing `Show navigator`, `Show context`, or `Show analysis`.
- Narrow persistent primary rail on the left with `Home`, `Design`, `Runs`, `Engineering Data`, `Review`, `Settings`.
- `Model`, `Process`, `Results`, `Lineage` remain visibly discoverable within Design; `Process` is active here.
- `Appearance / Light` lives in the upper-right of the Process workspace header; redundant `Workspace · Design` / `Mode · Process` chips are absent.
- Compact icon-first process toolbar spans the workspace below the stage tabs.
- Main workbench is three-column: process-equipment toolbox, dominant central grid canvas, right inspector.
- Right inspector is split into **Jarvis** above and **Properties** below.
- Properties `Value` cells are visibly editable input-style fields; Property and Unit remain read-only presentation.
- Central canvas is near-white with faint warm-gray grid lines.
- Background/surfaces are warm temple-stone/ivory, not green-tinted.
- Green is a strong chlorophyll accent for active states, icons, Jarvis status and emphasis.
- Geometry is predominantly squared with small corner radii; avoid pill-heavy or strongly rounded cards.
- Typography is a modern slightly futuristic sans-serif with polished landing-page character but engineering-workstation readability.

## Toolbar/toolbox intent

The reference shows likely future affordances such as Select, Pan, Add equipment, Connect, Disconnect, Multi-select, Duplicate, Delete, Fit view, Zoom, Undo, Redo, Auto-layout, Validate and Solve, plus representative process equipment.

These are product/visual intent only until a separate implementation spec binds each action to real server-owned process-engine contracts. Do not fabricate backend semantics merely to match the picture.

## Builder acceptance

When implementation is separately authorized, render `/design/process` at the canonical desktop viewport and compare it directly with the golden image. Treat the following as hard acceptance targets unless an authoritative runtime/accessibility contract requires deviation:

- overall spatial organization and panel proportions;
- absence/presence of the shell regions described above;
- central-canvas dominance;
- warm light-stone palette plus chlorophyll accent role;
- near-square geometry;
- editable Properties values;
- Jarvis/Properties split;
- icon-first toolbar density and toolbox organization.

Small copy differences and backend-driven state differences are acceptable only where required by the actual authoritative contract.
