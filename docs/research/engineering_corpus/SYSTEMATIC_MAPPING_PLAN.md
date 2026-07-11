# Systematic Mapping Plan

## Stage 1 — freeze v2 vocabulary

Run a second pilot of 50–75 records covering thermodynamics, separations, reaction engineering, equipment design, spreadsheets and FEM. Add fields only through logged gaps; do not mutate the schema ad hoc.

## Stage 2 — stratified corpus map

Build a document-level map first: course, chapter, role, language, page count, likely microtopic families, solution presence and artifact types. Use this to allocate extraction batches and prevent over-sampling one course.

## Stage 3 — candidate extraction

For each batch: segment source, propose microtopics, compile source claims, normalize equations and variables, then mark every record `structured`, never automatically `verified`.

## Stage 4 — verification ladder

Prioritize records with equations, solutions, code and design decisions. Run unit, conservation, numerical, limiting-case and runtime checks. Escalate unresolved claims to adversarial review.

## Stage 5 — benchmark factory

Generate candidates from verified records, then separate development-public and private-holdout partitions by semantic family before models see the holdout.

## Stage 6 — capability gap map

Aggregate recurring deterministic checks into candidate Jarvis tools: units, balances, empirical-correlation registry, ODE events, spreadsheet lineage, equation residuals, solver acceptance and source provenance.

## Initial batch policy

- batch size: 25–40 microtopics;
- at least 20% exercises/solutions;
- at least 10% known or suspected errors;
- at least 10% computational artifacts;
- every batch receives extraction, domain, adversarial and deterministic passes;
- schema changes require two or more recurring gaps or one critical loss of meaning.
