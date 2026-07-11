# BlueRev bioprocess modeling research backlog

This backlog converts the biological-modeling gap audit into an ordered research programme. It is not a parameter database and does not assume that the most detailed model is the best model.

## Priority rule

Prioritize research by expected value of information for BlueRev decisions:

1. can the mechanism change reactor, sensor, control or experiment decisions;
2. can it be identified with feasible measurements;
3. is current uncertainty large enough to affect conclusions;
4. can a simpler model already support the decision;
5. what is the cost of being wrong.

## P0 — before trusting the first dynamic model

1. Fix the exact *Nannochloropsis gaditana* strain and cultivation basis.
2. Define the minimum biological state vector.
3. Compare external-substrate, internal-quota and photoacclimation model families.
4. Establish light-response, photoinhibition and day-night respiration requirements.
5. Define carbonate chemistry and carbon-uptake representation.
6. Determine whether nitrogen alone or N/P co-limitation must be modeled.
7. Establish temperature, salinity and pH response functions with validity limits.
8. Separate gas-transfer parameters from biological source/sink terms.
9. Define measurement models, sampling rates and uncertainty.
10. Perform structural/practical identifiability screening before fitting.

## P1 — before scale-up to a recirculating tubular loop

1. Characterize residence-time distribution and axial/compartment structure.
2. Quantify Lagrangian light history and flashing-light effects.
3. Test pump recirculation, shear and bubble damage.
4. Couple oxygen production, supersaturation and degassing.
5. Characterize attached growth, optical loss and cleaning recovery.
6. Test model transfer from controlled laboratory conditions to outdoor weather cycles.
7. Establish stress/recovery and inoculum-history effects.
8. Validate soft sensors against direct biomass and physiological measurements.

## P2 — before protected-water pilot operation

1. Add contamination and community-risk models.
2. Introduce probabilistic weather and parameter uncertainty.
3. Build validity-envelope and out-of-distribution detection.
4. Compare advisory control, MPC and economic optimization needs.
5. Add maintenance/fouling state estimation.
6. Evaluate whether product-composition states affect harvesting decisions.

## P3 — future and fleet directions

1. Hierarchical learning across modules and campaigns.
2. Dynamic metabolic or genome-scale models where decision-relevant.
3. Population-balance models for size, aggregation or separation.
4. Evolutionary adaptation and phenotypic drift.
5. Community/microbiome models.
6. Federated digital twins combining biology, transport, structure and economics.

## Promotion criteria

A research result becomes stronger playbook guidance only when:

- species/strain and operating context are explicit;
- assumptions and transferability limits are stated;
- competing models were considered;
- parameters are identifiable with reported uncertainty;
- validation uses conditions not employed for fitting;
- decision consequences are demonstrated;
- failure modes and fallback behavior are documented.

Research directions remain retained even when these criteria are not yet met.