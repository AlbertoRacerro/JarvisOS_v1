# Migration v1 to v2

| v1 | v2 | Rule |
|---|---|---|
| `microtopic_id`, title, type | `identity` | type becomes `primary_record_type` plus `record_types[]` |
| single `provenance` | `source_claims[]` | create at least one claim per independently verifiable assertion |
| definition/meaning/model fields | `normalized_knowledge` | retain normalized content; add typed model context and relations |
| record-wide verification | `verification.claim_checks[]` | each source claim gets accept/reject/disputed/pending |
| verification methods | deterministic and sanity checks | preserve inputs, tolerance, result and evidence |
| benchmark candidate | `assessment` | add readiness, contamination class and gold policy |
| Jarvis candidate | `jarvis` | separate deterministic authority, AI role and required tools |
| no lifecycle | `governance` | use explicit extraction/review/verification/promotion states |

Migration is not purely mechanical when one v1 record contains multiple source claims. Such records must be split or assigned multiple claim checks during human/agent review.
