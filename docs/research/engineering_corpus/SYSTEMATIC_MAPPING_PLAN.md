# Systematic Engineering-Corpus Mapping Plan

## Current state

Template v2.2 has been exercised on 150 candidate microtopics. The representation is usable, but only 37 records met the strict canonical-export gate. Full unattended extraction remains blocked.

## Stage 1 — verification-focused recovery batch

Select 50–75 of the 113 withheld rehearsal records, balanced across domains. Do not add new records merely to increase throughput.

For every selected record:

1. re-check the exact source region;
2. normalize notation, units and coefficient basis;
3. reproduce numerical results or governing-equation residuals independently;
4. test limiting cases and physical plausibility;
5. verify the typed correlation, graphical, spreadsheet or FEM contract;
6. obtain a genuinely independent domain/model review when available;
7. promote only if every strict gate passes.

Target: at least 70% export yield without changing tolerances or weakening gates.

## Stage 2 — document-level corpus map

Map every source by course, chapter, role, language, page count, artifact type, likely microtopic families and presence of worked solutions. Use this map to allocate balanced batches and prevent one course from dominating the corpus.

## Stage 3 — candidate extraction outside memory

For each bounded batch:

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
6. retain file hash and exact location as provenance;
7. set `knowledge_exportable=true` only after the strict gate passes.

Rejected values, rejected formulas and source-error narratives remain outside retrievable knowledge.

## Stage 5 — benchmark factory

Generate benchmark candidates only from strictly exported canonical records. Separate development and private-holdout semantic families before model exposure. Solutions and gold remain outside reference retrieval.

## Stage 6 — Jarvis capability map

Aggregate recurring deterministic checks into tool candidates: unit conversion, material and elemental balances, correlation contracts, phase-equilibrium solvers, ODE events, spreadsheet lineage, equation residuals, FEM acceptance and source provenance.

## Normal batch policy after readiness is proven

- 25–40 microtopics per batch;
- stratified coverage across theory, equations, exercises, tables, diagrams and computational artifacts;
- extraction, domain, adversarial and deterministic passes;
- failed checks remain failed until the underlying knowledge is corrected and independently verified;
- quality is measured by reproducibility and semantic completeness, not by number of records produced.
