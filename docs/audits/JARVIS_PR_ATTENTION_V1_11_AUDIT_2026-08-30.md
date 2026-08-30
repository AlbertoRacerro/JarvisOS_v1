# jarvis-pr-attention V1.11 — code-first candidate audit — 2026-08-30

Status: candidate-integration evidence only; **not implementation or merge authority**  
JarvisOS audit base: `2a9563fc3016e4c2babff3bca9fc42f54e45902d`  
Upstream repository: `AlbertoRacerro/jarvis-pr-attention`  
Upstream release PR: #16 — `Release 0.13.1 compact V1.11 cycle`  
Inspected upstream head: `c544e2885a69173c58feb2355bb53e8866e627eb`

## Disposition

Primary reuse mode for JarvisOS at this point: **REFERENCE_ONLY / advisory integration candidate**.

Do not vendor or give the tool authority before the 128 architecture-enforcement boundary is accepted. A later integration may consume the compact cycle as read-only evidence, but JarvisOS must retain exact-head ownership, semantic acceptance, review/approval decisions, queue/work-state, persistence and merge authority.

Candidate grade: **A** for the narrow PR-evidence role.

## Direct source inspected

The audit inspected the exact V1.11 PR head rather than relying only on README/release prose. Material inspected surfaces include:

- `src/pr_attention/cycle.py`;
- `cycle/action.yml`;
- the PR #16 changed-file inventory and release body;
- the direct repository `LICENSE` at the same exact head.

The direct license is MIT.

## Useful mechanism

The compact cycle provides a bounded read/evidence pipeline around a pull request:

1. collect current PR/check/review/branch evidence;
2. bind/rebind that evidence to an expected exact head;
3. produce bounded delta and continuity packets;
4. classify evidence/gates conservatively;
5. expose an advisory `merge_candidate` result only after the cycle's own exact-live checks are satisfied.

The composite action asks for a GitHub token with read access to pull requests/checks/statuses/branch rules/reviews/compare data. The inspected V1.11 action invokes the cycle CLI and publishes outputs; no repository write step is part of that inspected action surface.

This is useful to JarvisOS because exact-head evidence collection and stale-evidence invalidation are repetitive and error-prone, while the tool can remain independently removable.

## Authority boundary

Even when the cycle returns a favorable result, JarvisOS must interpret it only as **advisory evidence**.

The integration must never allow `jarvis-pr-attention` to become:

- semantic acceptance authority;
- code correctness authority beyond the evidence it actually observed;
- review approval/request-changes authority;
- comment or thread-resolution authority;
- merge authority;
- queue/scheduler/work-state authority;
- canonical persistence or a second source of truth;
- a substitute for `docs/specs/STATUS.md`;
- a substitute for fresh JarvisOS exact-head/CAS checks immediately before mutation.

A boolean named `merge_candidate` is particularly easy to misuse. JarvisOS must not wire that value directly to a merge actuator.

## Failure modes and caveats

### 1. Advisory result accidentally treated as permission

Failure: a caller interprets `merge_candidate=true` as sufficient merge authority.

Control: integration maps it to evidence/display only. ChatGPT/JarvisOS still performs fresh semantic acceptance, verifies the accepted spec/readiness, re-reads the current head and invokes merge only through the existing exact-head owner.

### 2. Caller-supplied accepted-head claim mistaken for independent authority

The cycle can receive accepted-head authority inputs. Those inputs are useful for continuity comparison but cannot establish JarvisOS semantic acceptance by themselves.

Control: JarvisOS owns the accepted head/digest provenance. The external tool never gets to declare that its own input is authoritative merely because it is syntactically valid.

### 3. Evidence becomes stale after mutation

Failure: evidence gathered on head A is reused after head B is pushed.

Control: exact-head identity remains part of every consumed packet; any relevant head mutation invalidates affected evidence and requires a new cycle.

### 4. Read token scope grows into write scope

Failure: a future integration grants broader GitHub credentials than the inspected V1.11 read action requires.

Control: least-privilege read credential only; 128 architecture checks should make accidental write/side-channel ownership harder before integration lands.

### 5. Shadow persistence / second work-state registry

Failure: continuity packets or previous findings become a second durable JarvisOS queue or approval record.

Control: any persisted JarvisOS work-state remains in its existing owners, especially `docs/specs/STATUS.md`. Passing prior cycle evidence to a subsequent cycle is evidence continuity, not canonical state.

### 6. Upstream drift

This audit is bound to exact upstream head `c544e2885a69173c58feb2355bb53e8866e627eb`. A later upstream version or changed action must be re-audited before JarvisOS updates the integration.

## Recommended JarvisOS integration boundary after 128

A later accepted integration should:

- pin an exact upstream release/commit or otherwise establish reproducible version identity;
- run with read-only permissions;
- consume live PR evidence for one explicit target PR/head;
- return structured evidence to the ChatGPT/JarvisOS review step;
- keep all merge/approval/comment/STATUS mutations outside the tool;
- fail closed on head mismatch, unavailable required evidence or malformed/tampered continuity input;
- remain removable without losing JarvisOS truth.

No runtime integration, dependency addition, workflow addition or credential mutation is authorized by this audit.