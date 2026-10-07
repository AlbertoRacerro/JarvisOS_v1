# 183 — Truthful, configurable recycle (tear) solver

State: **accepted and ready**. Written under the maintainer directive of 2026-10-07 ("Lane A/B — characterize and upgrade the mixed/recycle solver"). Reviewed against the current mixed engine at master `0b755d47`.

- **Hard dependencies:** 168 and 172 (merged).
- **Place in the roadmap:** BlueRev must be designed around physics, not around solver limits. This slice makes Jarvis-converged recycles truthful and operator-configurable first. Biological/hydraulic semantics and semi-batch campaigns are separate slices.

## Fresh evidence: the current controller (code at `0b755d47`)

`mixed.iterate` is the only controller for Jarvis-converged tears: a Recycle on a loop that contains a Jarvis unit.

- **Map.** It runs simultaneous damped successive substitution on every tear: `x ← x + ω (g(x) − x)` over T, P, mass flow, mass fractions and the six culture fields. pH is copied.
- **Damping.** ω starts at 1. When the max normalized residual exceeds 1.5× the best one, ω halves (floor 0.125) and the solve restarts from the best iterate. Four such growth events stop it with `damping_exhausted`.
- **Convergence.** `max_i |g(x)−x|_i / tol_i ≤ 1`, where tol is:
  - mass flow: 1e-5 relative (floor 1e-6 kg/s);
  - temperature: 0.01 K;
  - pressure: 1e-6 relative;
  - mass fraction: 1e-7;
  - culture: 1e-5 relative + 1e-12.

  It is a step-only test.
- **Limits.**
  - `MAX_ITERATIONS = 25` is a hard clamp; a caller can only lower it. The dynamic sampler uses 12.
  - Wall budget 90 s.
- **Seed.** Tear flow = 1e-6 × total feed flow (1e-3 before a HeatExchanger), with **every culture field 0**.
- **Stop reasons:** `converged`, `max_iterations`, `damping_exhausted`, `wall_budget`.
- **Operator control:** none. No API or UI exposes iterations, tolerance, seed or method.

A deterministic synthetic qualification matrix drives the controller directly on the real tear-state shape (`backend/tests/tear_qualification_support.py`):

- linear maps with q ∈ {0, 0.25, 0.5, 0.7, 0.9, 0.99, 0.999, 0.9999} from seeds exact / 1 % / 10 % / 100 % / near-zero;
- oscillating maps;
- 3-vectors;
- a saturating nonlinear contraction;
- a non-normal ill-conditioned coupled map;
- a bistable washout ↔ productive regime switch;
- a flat plateau (small step, far from x*);
- evaluation noise.

Findings (evidence `jarvis-control/work/evidence/183/lane-a/baseline.txt`):

1. **False convergence.**
   - q = 0.999 and 0.9999 from a 1 % or 10 % seed report `converged` after one evaluation, with a true error of 1–10 %.
   - With the cap removed, every q ≥ 0.99 case "converges" with a true error of about tol/(1−q); q = 0.9999 ends 9–11 % off after about 22 000 iterations.
2. **Budget.** Every q ≥ 0.9 case fails the 25-iteration cap from any wrong seed, and q = 0.7 fails from poor seeds.
3. **Spurious abort.** The growth guard aborts a convergent non-normal coupled map (spectral radius 0.95).
4. **Seed bias.** The zero culture seed lands on the washout branch of a bistable biology map and reports `converged` there.

## Decision

### 1. One engine-neutral solver, three methods

`tear_solver.solve` replaces the body of `mixed.iterate`; the signature stays compatible. It offers three methods:

- **`direct_substitution`** (the default, as before):
  - the legacy damped controller and its growth/damping rules;
  - plus the convergence truth below;
  - plus an explicit early stop.
- **`wegstein`**:
  - per-variable secant acceleration, bounded to `[-5, 0]` by default (operator range −1000 … 0.5);
  - for weakly coupled tears with q ≲ 0.9.
- **`broyden`**:
  - "good" inverse Broyden on the scaled tear vector, starting from `−ω I`;
  - updates are skipped when the denominator is degenerate;
  - a non-finite matrix is reset;
  - the step size is bounded at `max_step_ratio` × |residual|;
  - per-variable fraction-to-boundary keeps a variable from crossing its bound;
  - a damped direct step is taken where the local secant contraction is ≥ 1;
  - backtracking halves the step on residual growth;
  - after repeated failures it does a full reset, with explicit `acceleration_breakdown`.

**Anderson acceleration** (type II, depth ≤ 5, regularized) was implemented and qualified against the same matrix, and is **not adopted**:
- it was never better than Broyden on these small tear vectors;
- it lost on a noisy q = 0.9 case;
- before the secant cross-check existed, it certified a noise-dominated near-neutral map.

Exposing it would only add a name.

### 2. Convergence truth

A solve is `converged` only when **both** of these hold:
- the step residual is within tolerance;
- a **validated estimate of the fixed-point error** is within tolerance (or the residual is exactly zero).

The estimate is the estimated Newton step (I − g′)⁻¹ (g(x) − x), normalized at the current iterate's tolerances. It comes from:

- **direct substitution:** |g(x)−x| / (1 − q̂), where q̂ = 1 + (Δx·ΔF)/(Δx·Δx). It is valid only when two consecutive secant estimates agree within 50 % in (1 − q̂).
- **Wegstein:** per-variable |F_i| / (1 − s_i), with agreeing slopes.
- **Broyden:** −H F. It is valid only after one accepted secant update. The initial −ωI carries no information about the map.

Accelerated methods additionally **require** the vector-secant cross-check (two agreeing secants), and the larger estimate wins. This catches coupling that per-variable slopes miss, and noise or regime changes that make the secants disagree.

All estimates are labelled estimates. None is applied when its secant information is missing or inconsistent.

### 3. Diagnostics and stop reasons

Each history row adds:
- `method`;
- `q_hat` and `q_hat_stable`;
- `classification`: `fast` < 0.5 ≤ `moderate` < 0.9 ≤ `slow` < 0.99 ≤ `near_neutral`, plus `oscillatory` and `non_contractive`;
- `estimated_error_normalized` and `estimate_valid`;
- typed `events`: `damping_reduced`, `acceleration_reset`, `step_halved`, `step_clipped`, `step_limited_at_bounds`, `direct_step_locally_expansive`, `broyden_update_skipped`, `projected_to_bounds`, `coordinates_changed`, `non_finite_evaluation`.

The run's `mixed_solve` adds:
- `solver`: the effective settings;
- `diagnostics`: q̂, classification, estimate, iterations, growth events and resets;
- when unconverged, `direct_substitution_iterations_required` and a recommendation.

New stop reasons:
- `iteration_budget_insufficient`: direct substitution with a stable q̂ needs more than 2× the remaining budget. It stops early instead of burning DWSIM time.
- `acceleration_breakdown`.
- `non_finite_evaluation`.

None of these is a silent fallback. Every method change within a solve is an event on that iteration's row.

### 4. Operator settings

A new draft op, `set_solver {solver: {...} | null}`, stores `document.solver`. It is validated by `tear_solver.parse_settings`, which refuses unknown keys and out-of-range values:

| setting | range | default |
|---|---|---|
| `method` | direct_substitution / wegstein / broyden | direct_substitution |
| `max_iterations` | 1 … 5000 | 25 |
| `damping` | 0.05 … 1 | 1 |
| `tolerances` | mass_flow_rel, temperature_abs, pressure_rel, mass_fraction_abs, culture_rel (bounded) | legacy values |
| `wegstein_bounds` | −1000 ≤ low ≤ high ≤ 0.5 | [−5, 0] |
| `max_step_ratio` | 10 … 1e8 | 1e5 |
| `stop_when_budget_insufficient` | bool | true |
| `wall_s` | 10 … 600 | 90 |
| `seed_mode` | `legacy` (as before) / `feed` (total feed flow, feed culture at an assumed 1000 kg/m³) | legacy |
| `seeds` | per Recycle tag: mass flow, T, P, culture fields (mass-specific) | none |

- A seed that names a missing Recycle is a blocker (`SOLVER_SEED_UNKNOWN_RECYCLE`).
- The settings are part of the document's meaning, so they change the process fingerprint and stale results.
- A caller budget, such as the dynamic sampler's 12, can only lower `max_iterations`.
- Documents without `solver` keep the legacy method, limits and seed. Only the convergence truth changes, by design.

The **Process UI** adds a "Solver" section to the Setup drawer: method, max iterations, damping, wall budget, seed mode, and an advanced tolerances group. The run convergence panel shows method, q̂, classification, estimated error, stop reason and the recommendation.

## Acceptance

- `backend/tests/test_tear_solver_183.py` runs the matrix for every shipped method at budgets 25 and 200. It checks:
  - **zero false convergence** (converged > 10 tol from every true fixed point) and **zero false non-convergence**;
  - converged results are within 2 tol (noise-free families);
  - every legacy false convergence becomes `iteration_budget_insufficient`;
  - Broyden converges every linear case from every seed in ≤ 4 evaluations, and every ill-conditioned case;
  - the q̂ = 0.9994 diagnostics: near-neutral, estimate valid and matching the true error, about 19 000 direct iterations required, recommendation;
  - first-evaluation small steps are not certified;
  - non-finite evaluations stop explicitly;
  - physical bounds hold;
  - determinism;
  - settings validation and the op;
  - seed modes;
  - the fingerprint.
- The existing 168 mixed-engine suite and the process/PBR/dynamic suites stay green.
- A real-DWSIM regression: the 168/172/181 real-DWSIM tests, plus one culture recycle loop solved with each method, with the settings and diagnostics in the run record.
- The full backend suite in a clean environment; ruff, ratchet and architecture gates; the frontend build.

## Limitations (recorded, not hidden)

- **Singular Jacobian.** A flat-plateau map, with g′(x*) = 1, is not certifiable by any method within these budgets. It stays truthfully unconverged.
- **Evaluation noise.** With noise ε, the fixed point is only defined to about ε/(1−q), so near-neutral loops can be truthfully unconverged.
- **Multiple fixed points.** The solver cannot detect them. A seed selects the branch. `seed_mode: feed` avoids seeding the washout branch, and the biology-level classification of washout belongs to the PBR/culture slices.
- **Native DWSIM Recycles** inside a DWSIM-only segment keep DWSIM's own convergence (with the 158 tolerance fix). These settings govern Jarvis-converged tears.

## Non-goals

- Simultaneous (equation-oriented) flowsheet solving.
- Tear-set selection algorithms.
- A dynamic-formulation substitute for recycles (172/185).
- Changing DWSIM's native Recycle.
