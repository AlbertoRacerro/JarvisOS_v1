# Engineering Knowledge Retention Policy

## Binding rule

The retrievable engineering memory stores only corrected canonical knowledge.

It does not retain:

- rejected numerical values;
- misleading conceptual explanations;
- duplicated wrong alternatives;
- narratives about who made an error;
- evaluator-only solutions or gold.

## Ingestion sequence

1. Extract candidate content into a temporary QA workspace.
2. Check equations, dimensions, balances, limiting cases, numerical reproducibility and runtime behavior where applicable.
3. Correct conceptual or numerical problems.
4. Write only the accepted formulation into the microtopic `knowledge` block.
5. Retain source file SHA-256 and exact locator as provenance.
6. Keep rejected fragments only as temporary QA evidence outside retrieval, training and benchmark-reference stores.

## Export gate

A record may enter retrieval only when:

- `governance.retention_policy == canonical_verified_knowledge_only`;
- `verification.knowledge_exportable == true`;
- verification status satisfies the configured project threshold.

A source label such as “official” is evidence of provenance, not proof of correctness.
