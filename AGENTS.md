# AGENTS.md — Instructions for AI coding agents working on JarvisOS

This file governs AI coding and review agents acting on the JarvisOS repository and delivery process. It does not govern JarvisOS or Hermes runtime actors directly. Runtime state, policy, sensitivity, routing, egress, budgets, tools, and promotion remain owned by JarvisOS.

JarvisOS is a single-user AI engineering workspace. Backend authority is FastAPI + SQLite; the React/Vite frontend is an operator interface. Models propose; deterministic code validates, gates, records, and audits.

## Hard invariants — never violate

1. `route_class="auto"` never executes an external provider.
2. Product AI calls go through `run_ai_task` and create an `ai_jobs` row.
3. The frontend never calls providers, Ollama, filesystems, or execution tools directly.
4. Safe defaults remain safe: paid AI disabled, budget zero, provider mode `fake`, tests fake or mock all providers.
5. The local classifier is advisory and owns no permission, provider, memory, or sensitivity decision.
6. No secrets in logs, events, docs, fixtures, commits, or frontend responses.
7. Data-root paths (`C:\JarvisOS`) go through `backend/app/core/paths.py`; runtime data never enters the repository.
8. Model output is a proposal until explicit user or deterministic-policy promotion.
9. Never fabricate outputs, validators, artifacts, metrics, or expected values to satisfy a gate.
10. Prefer the smallest sufficient change. Do not add infrastructure likely to be removed or replaced.

If a specification requires violating an invariant, stop and report the conflict.

## Repository operating regime — effective 2026-08-01

This section supersedes earlier cadence, per-step authorization, and human-merge rules.

### Permanent authorization and queue

- The assigned agent owns the technical merge decision.
- When deterministic gates are green and no current blocking review finding remains open, merge with an exact-head guard and continue to the next queued item.
- Do not wait for maintainer confirmation between definition, readiness, implementation, evidence, or registry-reconciliation PRs.
- Work queue order is binding. Finish, verify, and merge the first item before opening the next implementation front.
- Report only when the queue is exhausted, once per week for a queue longer than one week, or when one of the four interruption reasons below applies.
- Never enable GitHub auto-merge. The agent performs and verifies each merge explicitly.

### Only four interruption reasons

Contact the maintainer outside the final report only when:

1. real spending is required or a budget limit is at risk;
2. a credential, account, repository, or organization does not already exist;
3. there is a security issue or a secret may be exposed;
4. an obstacle has no two practicable routes forward.

Otherwise choose the least-cost safe route, proceed, and record the decision in the final report.

### Test del minimo necessario

Before work that adds infrastructure, credentials, external accounts, a new durable state store, or broader specification scope, put this block in the PR body:

```text
### Test del minimo necessario
Criterio di accettazione della spec:
Questo lavoro serve a soddisfarlo?           sì / no
Il criterio è raggiungibile senza di esso?   sì / no — con quale prova
Se sì: perché lo aggiungo comunque
```

If the acceptance criterion is reachable without the proposed work, do not build it. Record it as a future extension.

A specification declared separate remains separate. Never merge specifications merely because implementation would be convenient.

## Spec 079 scheduled-continuation exception

Spec 079 is a narrow repository-development exception to hard invariant 2. It permits the readiness-approved daily workflow to invoke the repository's existing `anthropics/claude-code-action@v1` integration for one exact-head continuation of one existing same-repository implementation PR.

The exception is bounded as follows:

- mode is `OFF`, `SHADOW`, or `EXECUTE_NO_MERGE`; absent mode means `OFF`;
- `OFF` and `SHADOW` invoke no provider and mutate nothing;
- active authority is reconstructed from the exact PR-head `STATUS.md`, the PR, branch, commit ancestry, and checkpoint comments;
- the existing `CLAUDE_CODE_OAUTH_TOKEN` is reused; no new provider credential or account is added;
- the Claude job has read-only repository authority and persisted checkout credentials disabled;
- Claude may only produce an untrusted local patch artifact;
- a separate job, without the Claude secret, rejects protected/sensitive paths, runs deterministic gates, rereads the remote exact head, and alone may make a normal non-forced same-branch push;
- the workflow cannot merge, auto-merge, review, classify findings, change labels, select a new specification, change settings/secrets, or dispatch another provider;
- `.github/**`, `AGENTS.md`, `CODEOWNERS`, and the 079 control script/test are immutable to scheduled continuation;
- `STATUS.md` may change only in the row of the active specification;
- tests make no live provider call and incur no spend.

Review, finding, correction, and re-review behavior belongs only to separate spec 080. No 080 behavior may be smuggled into 079.

## Model economy

Once existing egress policies permit it:

- cheap external models are the normal compute workhorse;
- frontier models are reserved for review, strategic documents, and hard tasks;
- local models are the fallback when safe redaction is impossible or ambiguous.

This never weakens the product execution spine or safe defaults.

## Spec-driven work

- Read `docs/specs/STATUS.md`, then `docs/specs/README.md`, then the selected specification.
- Implement exactly one specification per implementation branch.
- Scope, acceptance criteria, and non-goals are binding.
- If the specification conflicts with current code, report the conflict; do not guess.
- `STATUS.md` is the sole live status and priority authority.
- Do not infer state from legacy `Status:` prose, strategy documents, or chat handoffs.

## Cross-chat idea intake and external-reference register

`docs/IDEA_INTAKE_AND_CANDIDATE_INTEGRATIONS.md` is the canonical cross-chat intake register for external projects, papers, products, engineering methods, hardware concepts, and other ideas that may be useful to JarvisOS, BLUECAD, or BlueRev. It is a reference/candidate register only and never overrides `docs/specs/STATUS.md`, an accepted specification, or an ADR.

Whenever the maintainer proposes, links, uploads, or discusses something that could materially improve JarvisOS, BLUECAD, or BlueRev, the coordinating agent must:

1. read `docs/IDEA_INTAKE_AND_CANDIDATE_INTEGRATIONS.md` before claiming novelty, overlap, or implementation value;
2. audit the exact source deeply enough to distinguish verified implementation from README/marketing claims when source access permits;
3. update that register in the repository during the same work session, either by adding a new entry or extending the closest existing entry;
4. record provenance, concrete reusable mechanisms, caveats/negative evidence, and disposition rather than leaving the useful result only in chat context;
5. preserve rejected/superseded findings when they prevent repeated weak audits;
6. re-check current version and licensing before copying code or substantial implementation detail;
7. promote a candidate into implementation only through the normal backlog/spec/readiness/ADR process. The register itself grants no implementation authority.

This trigger-specific register read/update is mandatory even when the proposed item is not part of the currently active product queue. Do not copy the register into `STATUS.md` or use it as a parallel roadmap.

## Conduct when encountering an obstacle

A technical obstacle opens work; it does not close it.

1. Report every obstacle with at least two routes forward, their cost, and first concrete step.
2. Do not set a registry row to `blocked` for technical difficulty until two workaround attempts are documented and neither is viable.
3. An exploratory test must state a viable route, cost, and first step, not only yes/no.
4. When desired properties conflict, separate cases and declare the trade-off rather than forcing an invalid implementation.

### Obstacle report format

```text
### <short title>
What I tried:
What happened, with evidence (command, error, file, line):
Why it blocks:
Route A — <description> · cost: <low/medium/high> · first step:
Route B — <description> · cost: <low/medium/high> · first step:
Recommendation:
```

## Final queue report

At queue exhaustion report, in this order:

1. usable capabilities added;
2. integrated specifications/PRs and deterministic-gate results;
3. technical choices made for the maintainer and why;
4. minimum-necessary proposals rejected;
5. open obstacles in the required format;
6. anything required from the maintainer, limited to the four interruption reasons.

Do not end with a hypothetical next step.

## Repository map

| Path | Contents |
| --- | --- |
| `backend/app/core/` | config, paths, database, schema, logging, errors |
| `backend/app/modules/ai/` | execution spine, gateway, providers, routing, context builder |
| `backend/app/modules/ai/routing/` | RouterPolicy producer, Auto bridge, capability matrix |
| `backend/app/modules/local_ai/` | local classifier and local runtime support |
| `backend/app/modules/local_ai_eval/` | local model evaluation harness |
| `backend/app/modules/modeling/` | model specs, versions, simulation runs |
| `backend/app/modules/runner/` | bounded local Python runner |
| `backend/app/modules/engineering/`, `workspaces/`, `events/`, `files/` | domain foundation |
| `backend/app/modules/tools/`, `agents/` | registry skeletons only; do not expand without a specification |
| `backend/tests/` | Pytest suite |
| `frontend/` | React/Vite operator UI |
| `docs/` | canonical docs; `ARCHITECTURE.md` and `DECISIONS.md` win conflicts |
| `docs/specs/` | work-item specifications and canonical `STATUS.md` |
| `reports/` | generated evaluation/smoke reports |

## Environments

| | Local maintainer | Cloud container / CI |
| --- | --- | --- |
| OS | Windows 11, PowerShell | Linux |
| Python | `backend/.venv` | Python 3.11+, install backend requirements |
| Data root | `C:\JarvisOS` | none; tests isolate it |

Cross-platform rules:

- tests use `JARVISOS_DATA_ROOT` and `tmp_path`, never drive-letter assumptions;
- use `pathlib`;
- do not modify Windows launchers from Linux unless the specification supplies a verifiable test path.

## Deterministic gates

From `backend/`:

```bash
python -m pytest -q
python -m ruff check app tests
```

If frontend files changed:

```bash
cd frontend
npm run build
```

Repository CI, spec-status checks, and specification-specific conformance tests must pass on the exact head. Do not silence, skip, or relabel failures.

Tests run offline. Never require a live provider, network, or running Ollama.

## Review and merge authority

Automated and model reviews are advisory evidence. For each finding, reproduce or trace the concrete failure against the current specification and exact head. Fix genuine defects on the same branch. Rebut false findings with tests, authoritative sources, or precise code paths.

Merge requirements:

1. exact current PR head verified;
2. required deterministic gates green on that head;
3. no unresolved current P0/P1 or other blocking review finding;
4. no scope, dependency, secret, spending, or security conflict;
5. PR body includes the minimum-necessary test when required.

When all five hold, merge immediately with the expected-head SHA and verify `master`. The merge owner then reconciles `STATUS.md` and continues the queue.

External review workflows remain bounded by their own specifications. Spec 079 may continue implementation only. Spec 080, if later promoted, owns review/fix/re-review automation.

## Agent autonomy

Within the queued slice, proceed through inspection, definition, evidence, implementation, tests, CI diagnosis, review handling, merge, and status reconciliation without waiting between reversible steps.

This autonomy stops only for the four interruption reasons, destructive actions outside the specification, or a hard safety invariant.

Maintainer-owned conformance tests matching `backend/tests/**/test_*_conformance.py` may not be changed unless the queued work explicitly assigns that exact modification.

## Definition of done

1. Acceptance criteria met.
2. Required and full tests green.
3. Ruff clean on touched Python.
4. No unapproved dependency.
5. Docs changed only within scope.
6. PR records changes, tests, and deferred findings.
7. Implementation PR has the correct `STATUS.md` state and number before merge.
8. Merge is verified on `master`; registry is immediately reconciled.

## Conventions

- Use existing Python style, type hints, and small pure functions.
- English for code, comments, docs, and commit messages.
- Follow existing service/routes/models layout.
- SQLite migrations are additive in `backend/app/core/schema.py`; no Alembic.
- Short imperative commit subjects; one logical change per commit.

## What NOT to do

- no broad refactors, renames, or file moves unless required by the specification;
- no new frameworks, ORMs, agent libraries, or vector databases without accepted authority;
- no touching `backend/.venv`, `frontend/node_modules`, report history, or the data root;
- no expansion of tool/agent skeletons, MCP servers, background workers, or streaming unless a specification requires it;
- no speculative work while touching adjacent code;
- no combining independently removable specifications.