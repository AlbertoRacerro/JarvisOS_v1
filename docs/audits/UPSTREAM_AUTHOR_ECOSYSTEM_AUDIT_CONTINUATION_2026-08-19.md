# Upstream Author Ecosystem Audit — Continuation — 2026-08-19

Status: audit/reference document only. No implementation authorization is implied.

This continuation records code-first findings produced after `UPSTREAM_AUTHOR_ECOSYSTEM_AUDIT_2026-08-19.md`. The standing reuse policy is:

- permissive and commercially compatible upstream (MIT, Apache-2.0, BSD, ISC, zlib, etc.): prefer direct dependency or vendored component when technically appropriate;
- no-license, unclear mixed-license, or incompatible/copyleft code: reference-only unless a compatible boundary is demonstrated;
- permissive licensing does not make a component a security boundary: authority, sandboxing, provenance, attribution, NOTICE/SBOM and dependency review remain separate concerns.

## 1. `vercel-labs/agent-browser` — S browser worker, Apache-2.0

### What is directly useful

- credential vault and out-of-process credential plugins;
- domain egress allowlists and browser-level request controls;
- daemon-side action policy and confirmations;
- bounded output;
- browser/Electron automation suitable for a Jarvis browser worker.

### Code-first safety findings

`ActionPolicy` evaluates deny before confirm before allow/default. However an absent/empty allow-list without `default: deny` permits actions. Jarvis must therefore provide explicit fail-closed policy or maintain a stronger authority layer above the worker.

The element reference mechanism is robust but not strongly snapshot-bound. A ref stores backend node id plus role/name/nth. If the backend node id becomes stale, the resolver can intentionally re-find a fresh node with equivalent role/name. That is useful UX, but a stale reference can therefore resolve to a different live node instead of necessarily failing.

### Jarvis decision

Use as a browser worker, not as the final authority boundary. Add a Jarvis-owned `snapshot_id/page_epoch` and reject mutating actions whose observation epoch no longer matches. Keep AIRI-style perception preflight for sensitive computer-use actions.

## 2. Evaluation stack split

### `EleutherAI/lm-evaluation-harness` — A, MIT

Use for general/static base-model evaluation and compatibility with established language-model benchmarks.

### `huggingface/lighteval` — A, MIT

Use as a modern/composable model-evaluation option, especially around Hugging Face workflows, grammar generation, sampling metrics and Inspect AI interoperability.

### Decision

Do not make either the primary Jarvis engineering-agent benchmark. Split responsibilities:

- `lm-evaluation-harness` / `Lighteval`: base model qualification;
- Harbor / Terminal-Bench-Science: environment, artifact and deterministic engineering verification;
- MCP-Universe / MCPEval: MCP/tool-use benchmarking and task synthesis/prevalidation;
- WindowsAgentArena: Windows desktop-agent regression testing.

## 3. Quantization and edge

### `huggingface/optimum-quanto` — PARKED

Permissive but currently in maintenance mode; upstream recommends torchAO for new integrations.

### `pytorch/ao` / torchAO — A+/S, BSD-3-Clause

Strong direct integration candidate for PyTorch quantization/training:

- int4/int8/FP8 paths;
- QAT / quantized training;
- integrations with Transformers, vLLM and ExecuTorch.

### `pytorch/executorch` — A future edge, BSD

Useful for future on-device/edge Jarvis clients and appliances, including modern LLM families such as Qwen. It does not currently displace llama.cpp for the main Windows consumer-GPU laptop path; desktop CUDA support remains less mature than the target local runtime stack.

## 4. Microsoft ecosystem

### `microsoft/autogen` — PARKED for new Jarvis work

Current upstream is maintenance-mode relative to the new Microsoft Agent Framework. Do not choose AutoGen as a new Jarvis dependency unless a specific compatibility requirement appears.

### `microsoft/agent-framework` — A+/S comparison candidate, MIT

Useful features include middleware, graph workflows, checkpoint/resume, HITL, time travel, OpenTelemetry, multi-provider support and typed tool approval.

Code-first approval finding: rules can bind approval to exact canonical arguments, tool identity and server label, and persist in session state. Upstream explicitly warns that name-only approval can collide with an unrelated same-named tool. This is a useful pattern for Jarvis capability identity.

Decision: run an integration bake-off against Pydantic AI/Harness and Hermes rather than adopting a second large orchestrator by default.

### `microsoft/agent-lightning` — A+/S future training layer, MIT

Promising for engineering-agent specialization/RL:

- trajectory/model-request/reward telemetry;
- explicit rollout lifecycle;
- idempotent rollout ids;
- can train existing agent harnesses through gateway/proxy integration.

Candidate future pipeline:

`Harbor/TB-Science deterministic verifier -> reward -> Agent Lightning rollout/training`.

### `microsoft/UFO` — S Windows worker/integration layer, MIT

Strong match for JarvisOS because it is Windows-first and combines native Windows automation with visual grounding. The tree separates automator, application APIs, UI inspection, screenshots/UI tree and grounding. Its OmniParser adapter maps normalized visual bounding boxes back into the actual UIA application rectangle and returns actionable target information.

Candidate role: Windows application worker beneath Jarvis authority.

### `microsoft/OmniParser` — license-blocked standalone integration

The current root repository has a license inconsistency: README/badges and newer-weight notes refer to MIT components, while the root `LICENSE` is CC BY 4.0. Older Ultralytics detector weights also retain AGPL-related constraints, while the newer YOLOv9-E `icon_detect_v3` and caption path are described as MIT.

Decision:

- do not vendor the full standalone OmniParser repository until licensing is unambiguous;
- UFO's own MIT adapter remains usable;
- treat model weights/components with independent provenance and license records;
- avoid older AGPL detector path for the proprietary Jarvis core.

### `microsoft/WindowsAgentArena` — S Windows benchmark harness, MIT

Provides reproducible Windows VM tasks and application-specific deterministic evaluators. Important design lesson: evaluate actual application/file state (for example spreadsheet contents/rendered values), not only screenshots or LLM-judged text.

Candidate use: benchmark UFO/Jarvis desktop actions and build analogous HYSYS/Excel/CAD evaluators.

### `microsoft/TypeAgent` — A component mine, MIT

Do not adopt as another complete agent framework. High-value subcomponent: schema-hashed action cache / grammar generation. It can invalidate cached translations when the action schema changes and distill successfully translated requests into grammar/NFA paths.

Candidate Jarvis pattern:

`LLM translation once -> schema-validated action construction -> deterministic grammar/cache path for repeat requests`.

This extends the earlier E.V. deterministic-router idea.

### `microsoft/agent-host-protocol` — A+/S session synchronization protocol, MIT

Promising for multi-client Jarvis sessions: immutable state, pure reducers, write-ahead reconciliation, client/server sequence numbers, rejection reasons and multi-language clients.

Candidate role: synchronize Jarvis desktop/mobile/CLI/remote-worker session state. It is not the authority policy itself.

## 5. NVIDIA ecosystem

### `NVIDIA/SkillSpector` — S admission/security scanner, Apache-2.0

Direct integration candidate for untrusted Agent Skills/MCP/plugin intake.

Code-first findings:

- structured scan verdict;
- `safe_to_install` requires risk below threshold, successful execution and zero entirely-uninspected files;
- distinguishes requested/available/actually-used LLM semantic scan, preventing static-only results from masquerading as full scans;
- HTTP MCP transport rejects caller-selected local filesystem targets by default;
- static + optional semantic analysis; SARIF/JSON outputs; ingest limits and broader security scanners.

Candidate lifecycle:

`UNTRUSTED -> SkillSpector scan -> license/quality evaluation -> ELIGIBLE -> explicit Jarvis approval/install`.

### `NVIDIA/SkillEvaluator` — A+/S artifact/skill quality pipeline, Apache-2.0

Three-tier evaluation:

1. deterministic validation/security/license/PII/quality;
2. similarity/dedup/context optimization;
3. live agent evaluation.

Notably reuses SkillSpector for security and Harbor for sandboxed live evaluation. This is preferable to inventing a parallel Jarvis skill-quality framework.

### `NVIDIA/NeMo-Relay` — S lifecycle/trajectory/guardrail plane, Apache-2.0

Cross-runtime boundary for scopes, managed LLM/tool lifecycle, middleware, plugins, subscribers and normalized trajectories. It can wrap Codex/Claude Code and is already integrated into Hermes.

Code-first tests confirm:

- tool start/end lifecycle and parent scopes;
- required structured `ToolExecutionResult`;
- error end-events;
- request/response sanitizers;
- conditional blocking guardrails;
- async guardrail support;
- malformed/cyclic result handling.

Candidate role: common lifecycle/observability/trajectory/guardrail plane across workers. It does not replace OpenShell as the hard OS sandbox.

### `NVIDIA/NeMo-Agent-Toolkit` — A / PARKED as whole framework, Apache-2.0

Rich but broad: profiling, observability, eval, optimization, RL, MCP/A2A and multiple agent-framework integrations. Prefer the narrower NVIDIA components above unless a specific Toolkit-only primitive wins a later comparison.

## 6. Cline ecosystem

### `cline/cline-bench` — useful benchmark reference, currently REFERENCE_ONLY

Technically valuable because tasks come from real-world Cline sessions and already use Harbor layout:

- instruction;
- broken containerized environment;
- oracle solution;
- pytest verifier;
- binary pass/fail reward.

No root LICENSE was found during this audit. Do not import its task corpus into Jarvis as though it were Apache/MIT until licensing is clarified.

### `cline/skills` — A reusable skills source, Apache-2.0

Official Agent Skills collection that works across Cline, Claude Code, Cursor, OpenCode, Codex and Pi. Particularly relevant reusable skills include SDK guidance, review-team, data tooling, source search and skill creation/evaluation.

Candidate use: selected direct skills may be installed through the future Jarvis skill intake gate rather than copied/re-authored. Every imported skill should still pass SkillSpector + license/provenance checks.

### `cline/plugins` — A reusable plugin component library, Apache-2.0

Interesting implementations include:

- `branch-protector`;
- `env-blocker`;
- gitignored-path guard;
- background terminal;
- custom compaction;
- TypeScript LSP;
- subagent squad;
- browser/search/integration plugins.

Code-first caveats:

#### `branch-protector`

Real `beforeTool` enforcement hook but includes an explicit textual `--force-allow` bypass. Useful convenience/defense-in-depth, not Jarvis non-bypassable repository governance.

#### `env-blocker`

Intercepts direct file reads and command text mentioning `.env`. It cannot logically guarantee every indirect way arbitrary executable code might read a secret file. Treat it as defense-in-depth; enforce filesystem/secret boundaries below the agent with Jarvis/OpenShell.

#### `background-terminal`

Useful ready-made lifecycle implementation: UUID jobs, detached processes, persistent stdout/stderr, polling metadata and completion steer back into the session. It intentionally accepts arbitrary command/cwd/shell and inherits process environment, so it must run inside OpenShell/Jarvis authority and should not receive ambient secrets.

#### `typescript-lsp`

Strong narrow coding capability: resolves the target project's own TypeScript version and uses the TypeScript Language Service for symbol definitions across imports/re-exports/type aliases. Good candidate for direct reuse in a Cline coding worker.

### Cline security conclusion

Reuse its SDK/plugins/skills as implementations where valuable, but do not promote plugin hooks into the root Jarvis security model. Preferred layering remains:

`Jarvis authority -> OpenShell -> Cline worker + selected Cline plugins`.

## 7. `models.dev` provenance and model catalog

`cline/models.dev` is a fork. Original upstream: `anomalyco/models.dev`, MIT.

The upstream provides provider-agnostic and provider-specific model metadata including:

- model family/release/knowledge date;
- context/input/output limits;
- modality support;
- reasoning/tool-call/structured-output support;
- open-weights and license metadata;
- weights links and benchmark metadata;
- provider endpoint/auth metadata and prices.

### Jarvis decision

Do not manually maintain the public model/provider catalog. Use `models.dev` as a direct dependency/data source or periodically pinned local snapshot, then overlay Jarvis-specific measurements:

- measured VRAM/RAM/disk footprint by quantization;
- local throughput/TTFT;
- tool-call reliability;
- engineering-benchmark score;
- privacy/egress tier;
- supported Jarvis runtime backend (`llama.cpp`, Ollama, vLLM, etc.).

This keeps public factual metadata upstream while Jarvis owns device-specific operational truth.

## 8. Newly discovered original author ecosystem: `anomalyco`

A relevance-scoped repository inventory has been completed. High-priority siblings to audit code-first next:

1. `anomalyco/opencode` — MIT coding agent/runtime; compare component boundaries with Cline/Hermes before adopting anything large.
2. `anomalyco/browser-control` — inspect whether it adds anything over `agent-browser`.
3. `anomalyco/terminal-control` — inspect process/session semantics versus Cline background-terminal/OpenShell.
4. `anomalyco/agents-benchmark` and `opencode-bench` — determine license and verifier methodology.
5. `anomalyco/opentui` — potential reusable TUI if a Jarvis CLI becomes important.
6. `anomalyco/openauth` — only audit if Jarvis needs a self-hosted auth component.
7. OpenCode SDKs — potentially easier integration surface than embedding the whole coding agent.

Generic SST/cloud infrastructure repositories are low priority for the current JarvisOS/local-agent architecture.

## 9. Current architecture candidate after this tranche

This is a direction map, not implementation authorization:

- **Authority / capability policy:** Jarvis backend + typed CapabilityRegistry; evaluate Microsoft Agent Governance Toolkit.
- **Hard execution isolation:** NVIDIA OpenShell.
- **General agent runtime bake-off:** Pydantic AI/Harness vs Hermes vs Microsoft Agent Framework.
- **Coding worker:** Cline SDK + selected Apache-2.0 Cline plugins; OpenCode remains comparison candidate.
- **Windows worker:** Microsoft UFO.
- **Browser worker:** Vercel agent-browser with Jarvis-owned snapshot/page epoch.
- **Computer-use preflight:** AIRI-style observation binding.
- **Model/provider catalog:** anomalyco/models.dev + Jarvis local measurements.
- **Local serving:** llama.cpp / Ollama / vLLM selected per host; vLLM Agentic API where Responses/Claude-compatible stateful gateway is useful.
- **Provider gateway:** LiteLLM MIT core, with Jarvis explicit no-implicit-cloud-fallback policy.
- **Session/client synchronization:** Microsoft Agent Host Protocol candidate.
- **Cross-runtime lifecycle/trajectory:** NeMo Relay.
- **Skill/plugin admission:** SkillSpector + SkillEvaluator + provenance/license registry.
- **Model benchmark:** lm-evaluation-harness / Lighteval.
- **Tool/agent benchmarks:** MCP-Universe/MCPEval, Harbor/TB-Science, WindowsAgentArena.
- **Future RL specialization:** deterministic engineering verifier -> Agent Lightning reward/rollout.
- **Repeated-command acceleration:** TypeAgent schema-hashed action cache/grammar.
- **Quantization/training:** torchAO; ExecuTorch for future edge deployments.

## 10. Exact next audit checkpoint

Resume in this order:

1. `anomalyco/opencode` code-first: permissions, tool/session architecture, SDK boundary, provider/model layer and whether any narrow component beats Cline/Hermes.
2. `anomalyco/browser-control` and `terminal-control`.
3. `anomalyco/agents-benchmark` / `opencode-bench`.
4. Hugging Face sibling wave: `smolagents`, `trl`, `peft`, `accelerate`, current TGI status, DataTrove/Nanotron only where they add a unique Jarvis primitive.
5. DeepSeek sibling wave: DeepSpec first, then performance/training kernels only where relevant to local/server inference.
6. EleutherAI sibling wave beyond lm-evaluation-harness.
7. n0/Iroh networking family for optional peer-to-peer Jarvis worker connectivity.
8. Persist promotions into the canonical `docs/IDEA_INTAKE_AND_CANDIDATE_INTEGRATIONS.md` with explicit `DIRECT_DEPENDENCY`, `VENDORED_COMPONENT`, or `REFERENCE_ONLY` disposition.

No merge should occur until the final PR head is known and all required repository gates are checked against that exact head.
