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
11. Deterministic repository/runtime evidence and accepted authority prevail over model claims.
12. A green workflow alone is not semantic PASS.

If a specification requires violating an invariant, stop and report the conflict.

## Repository operating regime — effective 2026-08-01

This section supersedes earlier cadence, per-step authorization, and human-merge rules.

### Permanent authorization and queue

- The assigned agent owns the technical merge decision.
- When deterministic gates are green and no current blocking review finding remains open, merge with an exact-head guard and continue to the next queued item.
- Do not wait for maintainer confirmation between definition, readiness, implementation, evidence, or registry-reconciliation PRs.
- Work queue order is binding. Finish, verify, and merge the first item before opening the next implementation front, except for the explicitly gated post-112 controlled-parallel profile below.
- Report only when the queue is exhausted, once per week for a queue longer than one week, or when one of the four interruption reasons below applies.
- Never enable GitHub auto-merge. The agent performs and verifies each merge explicitly.

### Post-112 controlled-parallel delivery exception — dormant until 112 merges

`docs/POST_112_PARALLEL_DELIVERY_PROFILE.md` is the canonical execution profile for controlled parallel repository delivery after the activation gate below. It changes development mechanics only; `docs/specs/STATUS.md` remains the sole live authority for state, dependencies, queue order, and implementation-PR association.

- Until fresh exact `master` shows `112 PROJECT-KNOWLEDGE-CORE-1` as `merged`, the ordinary one-active-front rule remains absolute through 112. The parallel profile grants no implementation authority before that point.
- After 112 is merged, the coordinating agent activates the profile automatically only for candidate lanes whose file, store, schema, migration, and authority boundaries are demonstrated to be sufficiently disjoint. No maintainer checkpoint is required merely to activate a proved-safe lane.
- Scheduler identities are generic ChatGPT compute slots; logical Integration/Knowledge/Development/Coding responsibilities are dynamic locks, not permanent automation identities.
- Only one ChatGPT coordinator/writer may own GitHub/shared-authority mutation at a time. The coordinator alone owns shared integration boundaries, merge sequencing, and registry reconciliation.
- GLM candidate workers may run in parallel only on demonstrably disjoint exact-head tasks/lanes and own no GitHub, merge, queue, or shared-authority role.
- Parallelism never makes a `planned` row implementable, skips a hard dependency, weakens exact-head evidence, or broadens runtime/model/provider authority.
- A conflict returns only the affected slices to serial execution. Independent lanes may continue if their own dependencies, readiness, and ownership evidence remain valid.
- The profile does not automatically parallelize guarded self-update/PTY or other separately gated work.

Detailed lane, mutex, work-stealing, shared-file, planning-compression, CI, browser-proof, read-only-prework, Hermes, and conflict mechanics live only in `docs/POST_112_PARALLEL_DELIVERY_PROFILE.md`; do not create a second parallel-delivery policy elsewhere.

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

## Repository-development model roles

The current normative delivery split is:

1. **ChatGPT — Tech Lead / Architect / Maintainer.** Resolve fresh repo/context, choose architecture and ownership, author definition/full spec/readiness, issue precise implementation packets, define scope/non-goals/acceptance criteria, review candidate diffs semantically, integrate, own `STATUS.md` and shared authority, and perform exact-head merge/reconciliation.
2. **GLM-5.3-Flash — default bounded coding implementer and repair implementer for non-trivial READY code slices.** Give it exact target/base SHA, allowed paths, preloaded authority/context, required behavior, non-goals, and acceptance tests/checks. It writes candidate patches only in an ephemeral checkout. It owns no GitHub, merge, queue, architecture, policy, or shared-authority decision. Broad/general/adversarial review is not its default role.
3. **ChatGPT acceptance and repair loop.** After GLM output, ChatGPT checks diff, scope, semantics, and tests. When materially fixable, prefer a narrow GLM `REPAIR ONLY` packet over discarding or reimplementing the patch. ChatGPT codes directly only for trivial/mechanical fixes, minimal delivery plumbing, or proven GLM failure where another delegation is not worthwhile.
4. **Claude — normal independent terminal reviewer** when independent review is required or materially useful. Claude is a reviewer, not the default implementer.
5. **Codex — scarce specialist/high-risk reserve** only where a concrete material advantage or unresolved high-risk need justifies it. Do not use Codex routinely for docs/planning/reconciliation, small PRs, ordinary UI polish, or duplicate review.

Deterministic repository/runtime evidence and accepted authority always outrank model claims. Workflow green alone is not semantic PASS. For GLM, prefer a sufficiently budgeted completed bounded task over a cheap failed attempt while keeping path, exploration, tool, and authority scope narrow.

Detailed packet, review, repair, exact-head, and post-112 mechanics are canonical only in `docs/AGENT_EXECUTION_AND_AUTOMATION_PROTOCOL.md` and, after its activation gate, `docs/POST_112_PARALLEL_DELIVERY_PROFILE.md`.

This role split never weakens the product execution spine, provider policy, or safe defaults.

## Spec-driven work

- Read `docs/specs/STATUS.md`, then `docs/specs/README.md`, then the selected specification.
- Implement exactly one specification per implementation branch, except only where the post-112 profile explicitly authorizes disjoint parallel lanes.
- Scope, acceptance criteria, and non-goals are binding.
- If the specification conflicts with current code, report the conflict; do not guess.
- `STATUS.md` is the sole live status and priority authority.
- Do not infer state from legacy `Status:` prose, strategy documents, or chat handoffs.

## Lean codebase policy

JarvisOS is expected to be maintained and reviewed primarily by AI coding agents. Optimize for **minimum semantic surface**, not beginner-oriented ceremony and not code golf.

- Prefer the smallest number of real concepts, code paths, schemas and ownership boundaries that preserve behavior and invariants.
- Prefer direct functions/modules over class → factory → facade → manager chains when the extra layer does not enforce authority, security, transactions, provenance, a scientific contract, a replacement seam, or meaningful independent reuse.
- Do not split cohesive code merely to make files shorter. A direct larger module can be better than many tiny modules connected by indirection.
- Do not compress code into cryptic expressions, clever metaprogramming, or remove useful types/invariants merely to reduce LOC.
- Existing code has zero sunk-cost privilege. If a qualified upstream or a simpler existing boundary solves the same generic problem better, prefer wrap/replace/delete over parallel maintenance.
- **No current consumer is not proof of dead code.** Before deleting an apparently unreachable backend/API/tool capability, establish current product intent. Desired-but-unwired functionality is `WIRE`/`DEFER`, not deletion material.
- Do not preserve compatibility wrappers for hypothetical consumers. Preserve them only when a real supported consumer, migration requirement, public contract, authority boundary or accepted specification requires them.
- Tests are evidence, not automatic product intent. A test-only path may be obsolete, or it may encode an important scientific/security/behavior contract; trace the owner before removal.
- Runtime optimization requires profiling. Fewer Python/TypeScript lines do not by themselves prove lower wall time; distinguish first-party CPU cost from database/filesystem, native CAD kernels, external solvers, network/model latency and other waits.
- Broad cleanup must be spec-authorized. When code is adjacent to the current task, do not refactor it opportunistically unless the active specification requires the simplification.

For codebase-wide cleanup, specs 100a/100b define the evidence and deletion gates. Outside those slices, the same principle still applies: absence of reachability alone never authorizes deletion of a desired capability.

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
| `docs/` | canonical documentation; use the authority-by-question precedence in `docs/AGENT_EXECUTION_AND_AUTOMATION_PROTOCOL.md` |
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

When all five hold, merge immediately with the expected-head SHA and verify `master`. The merge owner then reconciles `STATUS.md` and continues according to the live registry and applicable delivery profile.

External review workflows remain bounded by their own specifications. Spec 079 may continue implementation only. Spec 080, if later promoted, owns its narrower repository-internal review/fix/re-review automation and is not broadened by the external delivery pipeline.

## Agent autonomy

Within the queued slice, proceed through inspection, definition, evidence, implementation, tests, CI diagnosis, review handling, merge, and status reconciliation without waiting between reversible steps.

After the post-112 profile activates, this autonomy applies inside each authorized lane while the single ChatGPT coordinator/writer retains shared-boundary and merge responsibilities defined by that profile.

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
- Follow existing service/routes/models layout only where that layout still adds a real ownership boundary; do not preserve ceremony for its own sake.
- SQLite migrations are additive in `backend/app/core/schema.py`; no Alembic.
- Short imperative commit subjects; one logical change per commit.

## What NOT to do

- no broad refactors, renames, or file moves unless required by the specification;
- no new frameworks, ORMs, agent libraries, or vector databases without accepted authority;
- no touching `backend/.venv`, `frontend/node_modules`, report history, or the data root;
- no expansion of tool/agent skeletons, MCP servers, background workers, or streaming unless a specification requires it;
- no speculative work while touching adjacent code;
- no combining independently removable specifications.