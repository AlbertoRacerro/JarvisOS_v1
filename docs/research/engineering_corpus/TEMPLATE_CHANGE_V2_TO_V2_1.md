# Template change: v2.0 to v2.1

V2.0 represented source statements as claims, including statements later rejected during verification. That is useful for forensic auditing but is not the intended content of JarvisOS engineering memory.

V2.1 replaces `source_claims` with `source_evidence`:

- evidence contains only source identity, SHA-256, exact location, authority and supported canonical fields;
- `knowledge` contains only the corrected canonical formulation;
- rejected values and explanations may exist temporarily in an ingestion QA workspace, never in retrievable knowledge;
- `verification.knowledge_exportable` is the mechanical gate between reviewed candidates and memory;
- `governance.retention_policy` is fixed to `canonical_verified_knowledge_only`.

This change preserves reproducibility without teaching the model incorrect alternatives or irrelevant error histories.
