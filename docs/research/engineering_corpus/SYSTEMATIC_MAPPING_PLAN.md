# Systematic Engineering-Corpus Mapping Plan

## Stage 1 — stabilize v2.1 typed blocks

The 75-record second pilot validated the canonical-only record shape. Before full-scale extraction, add typed contracts for empirical correlations, graphical methods, spreadsheet lineage and FEM verification targets. Schema changes require a recurring logged gap or one critical loss of meaning.

## Stage 2 — document-level corpus map

Map every source by course, chapter, role, language, page count, artifact type, likely microtopic families and presence of worked solutions. Use this to create balanced extraction batches.

## Stage 3 — candidate extraction outside memory

For each batch:

1. segment source pages, tables, diagrams, sheets or code;
2. propose atomic microtopics;
3. extract candidate equations, assumptions and procedures into a temporary QA workspace;
4. never export a raw candidate directly to retrieval.

## Stage 4 — canonicalization and verification

For each candidate:

1. normalize notation and units;
2. correct conceptual and numerical errors;
3. reproduce calculations when possible;
4. run dimensional, conservation, residual, limiting-case and runtime checks;
5. write only the corrected canonical result into the microtopic record;
6. retain file hash and location as provenance;
7. set `knowledge_exportable=true` only after the configured gate passes.

Rejected candidate values and source-error narratives remain outside retrievable knowledge.

## Stage 5 — benchmark factory

Generate benchmark candidates only from verified canonical records. Separate development and private-holdout families before model exposure. Solutions and gold remain outside reference retrieval.

## Stage 6 — Jarvis capability map

Aggregate recurring checks into tool candidates: unit conversion, material and elemental balances, correlation contracts, phase-equilibrium solvers, ODE events, spreadsheet lineage, equation residuals, FEM acceptance and source provenance.

## Batch policy

- 25–40 microtopics per normal batch;
- stratified coverage across theory, equations, exercises, tables, diagrams and computational artifacts;
- every batch receives extraction, domain, adversarial and deterministic passes;
- quality is measured by reproducibility and semantic completeness, not by number of records produced.
