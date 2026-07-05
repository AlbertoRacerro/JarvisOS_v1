# 009 — BLUECAD CalculiX FEM adapter (static v0) + ResultSummary + Tier 3

Status: implemented (pending review)
Depends on: 008

## Goal

After this slice, JarvisOS runs a static structural analysis end-to-end: the
008 mesh + an `AnalysisSpec` become a templated CalculiX `.inp`, the
registered `ccx` binary runs as a subprocess, `.frd`/`.dat` are parsed into a
`ResultSummary` (max displacement, max von Mises, reactions), and the
AnalysisSpec's `pass_criteria` are evaluated as Tier 3 checks appended to a
validation report.

## Why

Closes the analysis half of `BLUECAD_CORE_DESIGN.md` §5: review agents and
humans judge `ResultSummary`, never raw solver output; Tier 3 turns
engineering limits into data-driven checks. Static-only keeps the slice
small (modal/thermal are follow-ups).

## Scope

In scope:
- `.inp` assembly in `backend/app/modules/bluecad/fem_adapter.py`:
  - Template + data only (binding: **no free-form text passes from any LLM
    into the deck** — inputs are the schema-validated AnalysisSpec fields).
  - Sections: include mesh (`*INCLUDE` of 008's mesh.inp or concatenation —
    implementer's choice, note it), `*MATERIAL` (E, nu, rho from spec),
    `*BOUNDARY` fixing node sets `BC_<label>`, one static `*STEP` with
    loads on `LOAD_<label>` sets — v0 load types: `pressure` (DLOAD on
    faces) and `force_total` (CLOAD divided over set nodes; document the
    approximation in code docstring).
- Execution via `registry.run_tool("calculix", …)` (007), timeout from spec.
- Parsing: `.frd` displacements and stresses → derive max |u| (node id +
  value) and max von Mises (element/node + value); `.dat` reactions if
  requested. Malformed/truncated output → `PARSE_ERROR`; nonzero exit or
  "*ERROR" in log → `SOLVE_ERROR`; non-convergence pattern → `SOLVE_DIVERGED`.
- `schemas/bluecad_result_summary_v0_1.schema.json`: quantities above +
  solver exit status + artifact refs (`.inp`, `.frd`, `.dat`, log) + tool
  version from registry.
- Tier 3 evaluation: `pass_criteria` entries (e.g.
  `{"metric": "max_von_mises", "op": "<=", "value": 1.6e8}`) evaluated
  against ResultSummary → checks `T3_<METRIC>` appended to a validation
  report (005 report schema; additive check ids only). Unknown metric →
  structured error, not a skipped check.

Out of scope (binding non-goals):
- No modal/thermal/buckling (follow-up slices); no contact, no nonlinearity.
- No unit conversion: mm/N/MPa consistency is the spec author's contract
  (document the expected unit system in the AnalysisSpec schema
  descriptions — data stays mm/kg/s per core design, forces N, stress MPa).
- No AI interpretation (`bluecad.fem.interpret` is a later slice).
- No automatic mesh refinement loops beyond what 008 already does.

## Files likely touched

Verify against actual code before starting; report conflicts instead of guessing.

- `backend/app/modules/bluecad/fem_adapter.py` (new)
- `schemas/bluecad_result_summary_v0_1.schema.json` (new)
- `backend/tests/bluecad/test_fem_adapter.py`, fake-ccx fixture + golden
  `.frd`/`.dat` fixtures (new)

## Design constraints

- 007 `run_tool` only; never `import` anything CalculiX-related (GPL
  boundary C).
- Golden `.frd`/`.dat` test fixtures must be **synthetic, hand-written
  minimal files** following the public file-format spec — not copied from
  CalculiX distribution examples (clean-room rule).
- Deterministic: same mesh + spec + ccx version → identical ResultSummary
  numbers.
- ccx runs with `OMP_NUM_THREADS=1` in v0 (determinism over speed); env
  minimal per 007.

## Acceptance criteria

1. `.inp` generation from a fixture AnalysisSpec is byte-stable and
   contains material, boundary, and load sections referencing only
   `BC_*`/`LOAD_*` sets present in the mesh (offline).
2. Fake-ccx happy path → ResultSummary with max displacement, max von
   Mises, artifact refs; values match the golden `.frd` fixture's known
   maxima.
3. Tier 3: criteria pass/fail correctly against the golden summary
   (both directions tested); unknown metric → structured error.
4. `SOLVE_ERROR`, `SOLVE_DIVERGED`, `PARSE_ERROR`, `TIMEOUT` paths each
   produce their code with log artifact attached (fake-ccx variants).
5. **Live validation (marker `bluecad_ccx`, requires registered binary —
   assumption A4)**: cantilever tube fixture (005 geometry, one end fixed,
   tip force) — max tip displacement within 15% of the Euler-Bernoulli
   analytic value (coarse mesh tolerance; the point is order-of-magnitude
   correctness of the whole chain, not FEM accuracy tuning).
6. Zero LLM/`ai_jobs` involvement in this path (test-asserted as in 006b).

## Required tests

- Offline pytest with fake ccx via tmp registry + synthetic golden fixtures;
  live `bluecad_ccx` marker suite skipped when calculix is disabled in the
  registry.

## Definition of done

Test gate green (see `AGENTS.md`), acceptance criteria met, spec status
updated, summary written. A4 row in `BLUECAD_CORE_DESIGN.md` §11 updated by
the maintainer once a provenance-recorded binary passes the marker suite.
## Implementation notes

- Implemented `.inp` assembly using `*INCLUDE` to reference the 008 `mesh.inp` artifact directly rather than concatenating mesh text.
- Implemented v0 static `force_total` as uniformly divided `*CLOAD` entries over nodes found in the target `LOAD_<label>` mesh set.
- Offline tests use a synthetic fake `ccx` fixture and minimal hand-written `.frd`/`.dat` records; the live `bluecad_ccx` test remains marker-gated and skipped unless a maintainer registers a real binary.
- Deviations from spec: none.
