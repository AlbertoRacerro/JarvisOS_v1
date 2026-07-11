# Engineering Knowledge Retention Policy

## Binding rule

Retrievable engineering memory stores only corrected canonical knowledge.

Allowed:

- normalized definitions, equations, assumptions, validity conditions and procedures;
- explicit units, coefficient bases and model conventions;
- source file SHA-256 and exact PDF or spreadsheet locator;
- passing verification evidence that supports the canonical formulation;
- general failure modes that remain useful across problems.

Excluded from retrieval, training reference and benchmark reference:

- rejected numerical values;
- rejected formulas or explanations;
- narratives about who made a source error;
- failing source-audit evidence;
- unresolved candidates marked non-exportable;
- evaluator-only gold.

Rejected fragments may exist temporarily in bounded QA evidence so a reviewer can reproduce the correction. They must not be copied into `knowledge` or `canonical_export`.

## Mechanical export conditions

A record enters model-visible reference memory only when:

- `governance.retention_policy == canonical_verified_knowledge_only`;
- `verification.knowledge_exportable == true`;
- all major and critical embedded checks pass;
- no unresolved issue remains;
- units and bases are explicit;
- the required typed contract has been verified;
- governance visibility is `model_visible_reference`.

The v2.2 production rehearsal exported 37/150 records. The remaining 113 records stay QA-only rather than being promoted with weaker evidence.
