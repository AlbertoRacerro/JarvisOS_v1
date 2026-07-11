# Pilot Record Index

| # | Microtopic | Type | Source | Verification | Benchmark |
|---:|---|---|---|---|---|
| 1 | `pic.diffusion_reaction.planar_first_order.balance` | model | Risultati PIC Ex4.pdf page 1-2 | cross_source_verified | yes |
| 2 | `pic.diffusion_reaction.planar_first_order.boundary_conditions` | concept | Risultati PIC Ex4.pdf page 1 | cross_source_verified | yes |
| 3 | `pic.diffusion_reaction.planar_first_order.modulus` | equation | Risultati PIC Ex4.pdf page 2 | dimensionally_checked | yes |
| 4 | `pic.diffusion_reaction.planar_first_order.profile` | equation | Risultati PIC Ex4.pdf page 2 | numerically_reproduced | yes |
| 5 | `pic.diffusion_reaction.planar_first_order.bottom_concentration` | solution | Risultati PIC Ex4.pdf page 2 | numerically_reproduced | yes |
| 6 | `pic.diffusion_reaction.planar_first_order.average_rate` | equation | Risultati PIC Ex4.pdf page 2 | numerically_reproduced | yes |
| 7 | `pic.diffusion_reaction.planar_first_order.official_solution_error` | failure_mode | Risultati PIC Ex4.pdf page 2 | incorrect | yes |
| 8 | `pic.diffusion_reaction.sphere_zero_order.profile` | model | Risultati PIC Ex4.pdf page 3-4 | numerically_reproduced | yes |
| 9 | `pic.diffusion_reaction.sphere_zero_order.viability_radius` | solution | PIC Ex4 - Diffusione stazionaria con reazione.pdf page 1 | numerically_reproduced | yes |
| 10 | `pic.diffusion_reaction.sphere_zero_order.necrotic_core` | model | PIC Ex4 - Diffusione stazionaria con reazione.pdf page 1 | source_transcribed | yes |
| 11 | `atp.finite_difference.second_derivative.uniform_grid` | equation | Notes_02_ATP_NumericalMethods.pdf page 8 | cross_source_verified | yes |
| 12 | `atp.finite_difference.variable_diffusivity.conservative_form` | procedure | Notes_02_ATP_NumericalMethods.pdf page 9 | cross_source_verified | yes |
| 13 | `atp.boundary_conditions.dirichlet` | concept | Notes_02_ATP_NumericalMethods.pdf page 10 | cross_source_verified | yes |
| 14 | `atp.boundary_conditions.neumann_one_sided_second_order` | equation | Notes_02_ATP_NumericalMethods.pdf page 10 | cross_source_verified | yes |
| 15 | `atp.boundary_conditions.robin` | concept | Notes_02_ATP_NumericalMethods.pdf page 10 | cross_source_verified | yes |
| 16 | `atp.discretization.sparse_algebraic_system` | concept | Notes_02_ATP_NumericalMethods.pdf page 11-12 | cross_source_verified | yes |
| 17 | `atp.finite_volume.integral_conservation_form` | model | Notes_02_ATP_NumericalMethods.pdf page 12-13 | cross_source_verified | yes |
| 18 | `atp.stability.fourier_error_mode` | concept | Slides_07_ATP_StabilityAnalysis.pdf page 14-15 | cross_source_verified | yes |
| 19 | `atp.stability.ftcs_advection_diffusion.amplification_factor` | equation | Slides_07_ATP_StabilityAnalysis.pdf page 16-18 | cross_source_verified | yes |
| 20 | `atp.stability.von_neumann.condition` | concept | Slides_07_ATP_StabilityAnalysis.pdf page 19 | cross_source_verified | yes |
| 21 | `atp.stability.ftcs_diffusion.limit` | equation | Slides_07_ATP_StabilityAnalysis.pdf page 20 | cross_source_verified | yes |
| 22 | `atp.stability.ftcs_centered_advection.unconditional_instability` | failure_mode | Slides_07_ATP_StabilityAnalysis.pdf page 21-22 | cross_source_verified | yes |
| 23 | `bio.aeration.kla.definition` | concept | MBI 2025 - 2.3. Aeration.pdf page 22-23 | dimensionally_checked | yes |
| 24 | `bio.aeration.otr_equation` | equation | MBI 2025 - 2.3. Aeration.pdf page 24-25 | dimensionally_checked | yes |
| 25 | `bio.aeration.otr_our_constraint` | model | MBI 2025 - 2.3. Aeration.pdf page 25-27 | numerically_reproduced | yes |
| 26 | `bio.aeration.critical_kla` | equation | MBI 2025 - 2.3. Aeration.pdf page 27 | numerically_reproduced | yes |
| 27 | `plant.adsorption.python.runtime_import_failure` | failure_mode | Soluzione Python Esercizio 3.py line 25 | incorrect | yes |
| 28 | `plant.adsorption.antoine_convention_mismatch` | failure_mode | Soluzione Python Esercizio 3.py lines 34-42 | disputed | yes |
| 29 | `plant.adsorption.placeholder_isotherm` | failure_mode | Soluzione Python Esercizio 3.py lines 49-66 and 91-99 | incorrect | yes |
| 30 | `plant.psa.breakthrough_event` | procedure | Soluzione Matlab esercizio 3.m lines 1-119 | numerically_reproduced | yes |
