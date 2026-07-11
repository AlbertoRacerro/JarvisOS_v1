# Migration from v1/v2.0 to v2.1

## Binding change

V2.0 fields `source_claims` and `normalized_knowledge` are superseded by:

- `source_evidence`: provenance only;
- `knowledge`: corrected canonical engineering content only;
- `verification.knowledge_exportable`: explicit retrieval/export gate;
- `governance.retention_policy=canonical_verified_knowledge_only`.

## Migration rules

| Earlier field | v2.1 field | Rule |
|---|---|---|
| identity fields | `identity` | retain stable ID; split compound records when needed |
| provenance/source claims | `source_evidence` | retain file, SHA-256, locator, authority and supported canonical fields; remove rejected claim text |
| normalized content | `knowledge` | correct conceptual/numerical issues before writing |
| record/claim verification | `verification` | retain only methods, checks, confidence, limitations and export verdict |
| benchmark candidate | `assessment` | retain task/readiness metadata without solution or gold |
| Jarvis candidate | `jarvis` | separate deterministic core, AI role and required tools |
| lifecycle metadata | `governance` | add canonical-only retention policy |

## Non-mechanical cases

When earlier records contain contradictory source claims, do not migrate both alternatives. Re-run verification in a temporary QA workspace and migrate only the accepted canonical formulation. Keep provenance sufficient to repeat the decision.
