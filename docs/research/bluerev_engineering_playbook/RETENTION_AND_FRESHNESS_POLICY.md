# Retention and Freshness Policy

## Binding retention rule

This playbook stores **capabilities**, not encyclopedic facts.

Every entry is retained permanently when it contains at least one of:

- a reusable workflow;
- decision criteria or trade-offs;
- an architecture pattern;
- a diagnostic or failure-recovery method;
- a current or future engineering direction;
- tacit teaching advice that changes how work is performed;
- a BlueRev-specific transfer path.

Entries are retained regardless of whether their horizon is `now`, `near_term`, `future` or `fleet`.

## What is deliberately not stored as a primary entry

- isolated standard formulas;
- textbook definitions that can be retrieved reliably on demand;
- one exercise's inputs, intermediate values or final answer;
- a spreadsheet cell result;
- a copied standard, article or vendor manual;
- current prices, weather, regulation or vendor specifications.

A standard formula may be mentioned inside a workflow only when needed to explain a selection or verification procedure.

## Live lookup boundary

The following must be refreshed at the moment of consequential use:

1. current standard edition and applicable regulation;
2. vendor product, software and hardware specifications;
3. physical properties, coefficients, numerical parameters and correlations;
4. latest papers and benchmark results;
5. prices, energy tariffs, market values and financing conditions;
6. site-specific metocean, weather and environmental data.

## Retrieval behavior

- Mature and urgent entries should rank first for current design questions.
- Future and frontier entries must remain searchable and must never be deleted merely because BlueRev cannot yet implement them.
- The assistant must label frontier material as such and distinguish guidance from demonstrated BlueRev capability.
- High-consequence decisions require current sources, competent review and representative evidence.

## Supersession

A playbook entry is revised, not silently overwritten. Material changes must preserve:

- previous version identifier;
- reason for change;
- changed evidence;
- affected BlueRev decisions;
- required revalidation.
