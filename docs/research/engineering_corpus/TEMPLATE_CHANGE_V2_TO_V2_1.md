# Template Evolution: v2.0 to v2.2

## v2.1 — canonical-only memory

V2.1 replaced retrievable source claims with provenance-only `source_evidence` and a corrected canonical `knowledge` block. Rejected values and explanations may exist temporarily in ingestion QA, never in retrievable knowledge.

## v2.2 — typed engineering contracts

V2.2 keeps the canonical-only decision and adds:

- closed `knowledge_strength` vocabulary;
- structured PDF and spreadsheet locators;
- typed equation and variable registries;
- explicit variable unit and coefficient basis;
- `correlation_contract`;
- `graphical_method_contract`;
- `spreadsheet_lineage`;
- `fem_verification_target`;
- typed verification checks with severity and evidence;
- strict export conditions and explicit unresolved issues.

## Rehearsal outcome

V2.2 was applied to 150 candidates. Schema validation passed for all records, but meaningful engineering gates did not: five content checks and one semantic contract failed, 113 records were withheld, and independent reviewer passes were not available. Full-corpus mapping remains on hold.
