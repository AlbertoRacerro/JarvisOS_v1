# Spec 108 runtime evidence

`run_pbr_study.py` runs three seeded Latin hypercube points through the real 107 PBR evaluator using `scripts/qualification/107/synthetic-parameters.json`. The committed JSON is execution evidence for those synthetic inputs only; it does not qualify the model.

The 108 controller currently returns typed `StudyRun` and `StudyPoint` records with a canonical content digest. It does not persist them. Existing `simulation_runs` services are specific to modeling and runner jobs, and there is no clean generic study persistence service to reuse. A future bridge should attach these records through Jarvis's canonical artifact/evidence owners; 108 adds no table or migration.
