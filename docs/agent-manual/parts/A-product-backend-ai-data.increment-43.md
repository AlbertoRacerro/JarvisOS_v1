# Area A file-coverage increment 43

MAPPING_STATUS: IN_PROGRESS
UNACCOUNTED_FILES: >0

This additive shard avoids rewriting the protected canonical Area-A ledger. Source content was independently reopened from fresh master `240d5e0b27d9837d40f47bddfa24871ae7a2a4bb` before credit.

## EXPLICIT FILE COVERAGE LEDGER

| Path | Status | Concise role / reason |
|---|---|---|
| `backend/app/modules/ai/egress_policy.py` | READ | Strict loader/parser for the canonical AI egress-policy JSON. It rejects noncanonical policy paths, missing/extra keys, unsupported schema versions/operations, invalid bounds and duplicate strings; materializes immutable `EgressPolicyConfig`; and computes a SHA-256 digest over canonicalized raw JSON. Default loading is process-cached (`lru_cache(maxsize=1)`), so on-disk policy changes are not observed by callers of `load_default_egress_policy()` until cache/process reset. |

### Runtime boundary notes

- `load_egress_policy()` permits only the resolved repository canonical path `configs/ai_egress_policy.json`; arbitrary alternate policy files are explicitly rejected.
- Parser validation is structural/bounded rather than cross-field semantic: for example, prompt/context limits and TTL values must be positive, but this module does not prove operational compatibility with downstream provider/runtime behavior.
- `sample_rate_bps` is constrained to 500..10000; `daily_soft_spend_usd` accepts zero and nonnegative numeric values while rejecting booleans.
- `supported_operations` must equal exactly `("external_provider_call",)`, including ordering/cardinality after list parsing.
- The config digest binds the entire accepted raw object after sorted compact JSON canonicalization; whitespace/key ordering in the source file therefore does not change the digest, while accepted value changes do.
