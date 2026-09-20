# JarvisOS agent manual coverage audit

Issue #656 canonical coverage summary for the final capability manual.

- Baseline: `master@240d5e0b27d9837d40f47bddfa24871ae7a2a4bb`
- Manifest: `docs/agent-manual/FILE_COVERAGE_MANIFEST.tsv`
- Master tracked paths: **2036**
- Manifest rows: **2036**
- READ: **1459**
- GENERATED/ASSET: **577**
- Covered: **2036**
- Missing: **0**
- Extra: **0**
- Duplicate paths: **0**
- Ambiguous ownership: **0**
- Invalid terminal statuses: **0**
- Report Markdown reclassification: **109** summaries changed from GENERATED/ASSET to READ after semantic inspection; report JSON/text/binary evidence remains GENERATED/ASSET where it has no standalone capability semantics.

Ownership totals remain A=1109, B=160, C=233, D=534. Every tracked master path appears exactly once and every terminal status is READ or GENERATED/ASSET.

Validation command:

```text
python3 scripts/validate_agent_manual_coverage.py --base-ref master
```

Expected result at the audited base: PASS with 2036 tracked paths, 2036 manifest rows, 0 missing, 0 extra, 0 duplicates and 0 ambiguous owners.
