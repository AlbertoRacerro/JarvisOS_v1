# BlueRev Engineering Playbook retention and freshness policy

## Binding retention rule

The playbook stores reusable engineering capability rather than encyclopedic content.

A valid playbook is retained permanently when it captures one or more of:

- a workflow or algorithm;
- model or method selection logic;
- decision criteria and trade-offs;
- an architecture pattern;
- a diagnostic, verification or fallback method;
- a high-value didactic heuristic;
- a current, emerging or frontier research direction;
- a BlueRev-specific transfer path.

Retention is independent of immediate usability. Entries may be tagged `now`, `near_term`, `future` or `fleet`. Maturity controls warnings, ranking and evidence requirements; it does not determine whether the direction is remembered.

## Missing evidence is not deletion

When a direction is relevant but evidence is incomplete, the playbook stores:

- the engineering question;
- candidate model or method families;
- what is currently known;
- what remains unknown;
- the cheapest discriminating experiment or research task;
- the conditions that would permit promotion to stronger guidance.

The system must not invent species-specific parameters, standards compliance, field validation or industrial readiness. An unresolved research requirement remains retrievable as a research direction, not as a verified design claim.

## Excluded primary records

The following are not stored as standalone canonical playbooks:

- isolated standard formulas;
- textbook definitions;
- spreadsheet-cell values;
- case-specific exercise inputs or answers;
- unqualified parameter values;
- vendor claims without context;
- obsolete snapshots that can be retrieved reliably at use time.

They may appear as supporting context, temporary QA fixtures or live-looked-up evidence.

## Live lookup boundary

The following must be refreshed at the moment of consequential use:

1. current standard edition and applicable regulation;
2. vendor product, software and hardware specifications;
3. physical properties, coefficients, numerical parameters and correlations;
4. latest papers and benchmark results;
5. prices, energy tariffs, market values and financing conditions;
6. site-specific metocean, weather and environmental data.

## Freshness classes

Each playbook should state its freshness class:

- `stable_foundation` — enduring engineering reasoning or workflow;
- `slow_change` — mature industrial practice or standards-aligned architecture;
- `active_research` — methods or evidence developing on a multi-year horizon;
- `fast_change` — software, vendor capability, current regulation, pricing or rapidly evolving benchmarks.

Stable reasoning may remain canonical. Fast-changing implementation details must be checked live before consequential use.

## Retrieval behavior

- Mature and urgent entries should rank first for current design questions.
- Future and frontier entries must remain searchable and must never be deleted merely because BlueRev cannot yet implement them.
- The assistant must label frontier material as such and distinguish guidance from demonstrated BlueRev capability.
- High-consequence decisions require current sources, competent review and representative evidence.

## Consequential-use boundary

The playbook may guide learning, research planning, model comparison, design framing and experiment selection.

It is not by itself authority for:

- final equipment design;
- safety or control logic;
- legal or regulatory compliance;
- certification;
- autonomous field operation;
- unreviewed economic commitments.

Those uses require current source verification, domain review and BlueRev-specific validation.

## Supersession

A playbook entry is revised, not silently overwritten. Material changes must preserve:

- previous version identifier;
- reason for change;
- changed evidence;
- affected BlueRev decisions;
- required revalidation.