# JarvisOS agent capability manual — coverage audit

GLOBAL_FILE_COVERAGE: COMPLETE

Baseline: master@240d5e0b27d9837d40f47bddfa24871ae7a2a4bb
Fresh tree enumeration: every root/top-level subtree fetched with truncated:false.
Canonical manifest: docs/agent-manual/FILE_COVERAGE_MANIFEST.tsv

## Counters

| metric | value |
|---|---:|
| TOTAL_TRACKED_FILES | 2036 |
| READ | 1350 |
| GENERATED/ASSET | 686 |
| COVERED_FILES | 2036 |
| UNACCOUNTED_FILES_COUNT | 0 |
| DUPLICATE_PATH_COUNT | 0 |
| AMBIGUOUS_OWNERSHIP_COUNT | 0 |

Accounting: 2036 = 1350 READ + 686 GENERATED/ASSET.

## Owner totals

| owner | total | READ | GENERATED/ASSET |
|---|---:|---:|---:|
| A — product backend / AI / data / context | 1109 | 455 | 654 |
| B — frontend / operator UX / design references | 160 | 144 | 16 |
| C — engineering / BLUECAD / process / scientific | 233 | 223 | 10 |
| D — delivery / security / operations / governance | 534 | 528 | 6 |

## Evidence rules

READ is credited only for direct fresh-master content inspection or a prior lane row that records actual source-content inspection and is attributable to the path's final owner. Historical Area-B backend hints were not used as B ownership; duplicated rows were collapsed by normalized repository path.

GENERATED/ASSET is used for generated reports, binary CAD/mesh/font assets, SVG assets, and approved HTML reference artifacts after identity/provenance verification. These files are accounted for but are not treated as executable capability evidence.

## Validation

Run:

    python3 scripts/validate_agent_manual_coverage.py --base-ref master

Expected result: PASS; manifest rows exactly equal the fresh master tree, with no duplicate path, invalid status, missing path, extra path, or multi-owner row.
