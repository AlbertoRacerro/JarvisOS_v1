# Hermes + GLM read-only worker experiment — 2026-08-28

Status: `EXPERIMENT / REFERENCE AUDIT` — not product/runtime implementation authority.

## Purpose

Evaluate whether a pinned Hermes Agent harness using Z.AI `glm-4.7-flash` can perform useful, low-cost repository preflight/review work for JarvisOS without consuming scarce Codex review capacity and without acquiring product, merge, GitHub-write, shell, provider-policy, or domain authority.

This experiment is deliberately independent from the 111→112 product front. It may run on an isolated same-repository PR while 111/112 remain serial because it does not mutate `master`, `docs/specs/STATUS.md`, backend, frontend, schemas, product provider policy, or runtime state.

The existing intake owner is `REF-022 | NousResearch/Hermes Agent` in `docs/IDEA_INTAKE_AND_CANDIDATE_INTEGRATIONS.md`. This experiment extends evidence for that existing candidate; it does not create a synonymous intake entry or promote Hermes into JarvisOS runtime.

## Upstream provenance

- Project: `NousResearch/hermes-agent`
- License: MIT, as declared by upstream README/`pyproject.toml` at the pinned source.
- Pinned upstream commit for this experiment: `306db2776c6b6f1acc85c31c4dabba3263f0e9fd`
- Upstream package version at that commit: `0.20.6`
- Provider: native Hermes `zai`
- Model: `glm-4.7-flash`
- Credential input: existing repository Actions secret `GLM_API_KEY`; the secret is never committed and is scoped only to the Hermes invocation/gate step.

The pinned upstream documentation at this commit explicitly supports:

- `GLM_API_KEY` / `ZAI_API_KEY` aliases for Z.AI, with default base URL `https://api.z.ai/api/paas/v4`;
- `hermes chat --oneshot` for non-interactive execution;
- `--provider zai` and `--model ...` per run;
- `--toolsets file` for the file toolset;
- `--ignore-user-config`, `--source tool`, and `--max-turns` for isolated third-party runs;
- `HERMES_WRITE_SAFE_ROOT`, which makes file writes outside configured safe roots fail closed.

## Minimum experiment boundary

The first smoke test is intentionally weaker than a coding worker. Hermes receives only the `file` toolset. That toolset contains read/search plus write/patch tools upstream, so the workflow also sets `HERMES_WRITE_SAFE_ROOT` to a scratch directory outside the JarvisOS checkout. A model attempt to use `write_file`/`patch` against the repository therefore fails closed.

Not enabled:

- terminal/process execution;
- code execution;
- web/browser;
- MCP;
- delegation/subagents;
- persistent memory;
- cron/gateway;
- `--yolo`;
- GitHub mutation credentials;
- merge/review authority.

The Actions job has repository permission `contents: read`; checkout uses `persist-credentials: false`. `GITHUB_TOKEN` is not passed to Hermes. The only external model credential exposed to the Hermes step is `GLM_API_KEY`.

## Exact smoke task

On the exact PR head, Hermes must inspect repository truth and return a bounded Markdown report containing:

1. expected exact checkout HEAD consistency;
2. current binding front and lifecycle state from `docs/specs/STATUS.md`;
3. at least three hard invariants from `AGENTS.md`;
4. one exact existing owner seam that spec 111 must reuse instead of duplicate;
5. one material fail-closed failure mode for a future 111 implementation;
6. `PASS`, `PARTIAL`, or `FAIL` on usefulness as a cheap read-only preflight worker.

Unknown or missing evidence must be reported as unknown/unavailable rather than guessed.

## Deterministic gates outside the model

The workflow, not Hermes, proves:

- checkout HEAD equals `github.event.pull_request.head.sha`;
- repository diff is empty before the model run;
- repository status is clean before the model run;
- Hermes is installed from the exact pinned upstream SHA above;
- requested provider is `zai` and requested model is `glm-4.7-flash`;
- Hermes emits a non-empty bounded report;
- Hermes usage evidence reports provider `zai` and model `glm-4.7-flash`;
- the literal `GLM_API_KEY` value is absent from captured model output/stderr;
- repository HEAD remains unchanged after the model run;
- repository diff/status remain clean after the model run.

A green workflow is necessary but not a semantic PASS. A later human/coordinator read must compare the report with repository truth and classify the experiment `PASS`, `PARTIAL`, or `FAIL`.

## Supply-chain and security caveats

This is an ephemeral CI experiment, not a hardened sandbox. Pinning Hermes prevents silent upstream source drift, but its Python dependencies are still installed into an ephemeral GitHub runner from package indexes according to the pinned upstream dependency metadata. The run therefore does not prove hostile-code isolation suitable for future arbitrary PTY or untrusted third-party agent execution.

`HERMES_WRITE_SAFE_ROOT` constrains Hermes file-tool writes, but upstream itself documents file read/write guards as defense in depth rather than a complete sandbox when terminal authority exists. This experiment deliberately withholds terminal authority, which is why the write-safe-root control is meaningful here.

The model is a cloud Z.AI model. Repository content selected by Hermes may leave GitHub infrastructure and be sent to Z.AI. Therefore this experiment is suitable only for repository material already permitted for that egress boundary. It must not be generalized into sensitive-project context dispatch without JarvisOS 059a/059b policy authority.

## Promotion criteria

Do not promote Hermes/GLM into a normal repository writer based on one smoke test. A later promotion decision should require repeated evidence across tasks such as:

- exact-head repository impact mapping;
- code/spec review against known findings;
- test-failure root-cause analysis;
- scope discipline and hallucination rate;
- failure recovery;
- token/API-call consumption and provider limits;
- comparison with coordinator/Claude findings;
- explicit branch-only write policy if write authority is ever considered.

Even after promotion as a cheap worker, merge authority, `STATUS.md`, shared integration files, security/egress policy, credentials, and high-risk runtime authority remain outside Hermes unless separately specified and proven.

## Workflow provenance

Experimental workflow: `.github/workflows/hermes-glm-worker-experiment.yml`

Pinned GitHub Actions:

- `actions/checkout@11d5960a326750d5838078e36cf38b85af677262` (`v4` ref observed 2026-08-28)
- `actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065` (`v5` ref observed 2026-08-28)
- `actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02` (`v4` ref observed 2026-08-28)

The experimental PR must remain draft while the harness is being corrected so the repository's Codex auto-review is not intentionally triggered. It is not merged during the 111/112 foundation work unless a later explicit promotion decision re-derives that boundary.
