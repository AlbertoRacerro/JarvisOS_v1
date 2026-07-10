# Engineering Corpus Boundary v1

## Scope

This slice adds an offline, fail-closed boundary only. It does not add an API route,
normal-chat caller, provider call, network call, corpus binary, or private benchmark gold.

Implemented:

- SHA-256-bound, path-confined, SQLite `mode=ro&immutable=1` corpus snapshots;
- bounded read-only retrieval with exact provenance;
- forced private-role exclusion and stronger evaluation-mode solution exclusion;
- deterministic unit, elemental-conservation and numeric tolerance checkers;
- evaluator-only structured benchmark grading that does not return hidden expected values.

## Authority

AI output remains advisory. Unit compatibility, elemental residuals, numeric tolerances,
snapshot identity and benchmark checks are deterministic.

## Deployment requirement

`private_gold` must be mounted only in a separate evaluator process. Python object
encapsulation is not a security boundary. Normal retrieval and agent workspaces must not
share that mount.

## Explicit non-goals

- no automatic equation extraction;
- no Python/MATLAB/Abaqus execution;
- no model-based grader;
- no DuckDB runtime dependency;
- no ingestion of copyrighted course binaries into Git.
