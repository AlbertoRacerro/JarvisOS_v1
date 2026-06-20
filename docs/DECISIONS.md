# Architecture Decision Records

## ADR-001: Use FastAPI Backend

Status: Accepted

JarvisOS uses FastAPI for the backend because it is lightweight, typed, Python-native, and fits future engineering workflows that will rely on Python services and model execution.

## ADR-002: Use React + Vite + TypeScript Frontend

Status: Accepted

JarvisOS uses React, Vite, and TypeScript for the frontend. This keeps the local UI fast to develop while preserving type safety and a clean path to richer workflow screens later.

## ADR-003: Use SQLite Initially

Status: Accepted

JarvisOS starts with SQLite because the product is local-first and Windows-first. The database layer must remain small and avoid SQLite-only assumptions that would block a future PostgreSQL migration.

## ADR-004: Use Local Windows Data Root

Status: Accepted

Runtime data defaults to:

```text
C:\JarvisOS
```

The repository may live separately from the data root. Filesystem paths must be centralized through the backend paths layer.

## ADR-005: Route AI Access Through AI Gateway

Status: Accepted

All AI provider access must go through the AI Gateway. No feature module should call OpenAI, Gemini, local models, or future providers directly.

## ADR-006: Treat Old JarvisOS As Reference Only

Status: Accepted

JarvisOS v2/v3 is a clean new codebase. Prior implementations can inform decisions but should not be refactored as the foundation or copied as monolithic patterns.

## ADR-007: Keep V1 Architecture-Strong And Feature-Thin

Status: Accepted

JarvisOS V1 should establish strong architecture before broad features. Early tools must be placed inside the architecture spine and should remain migration-friendly.

## ADR-008: Introduce Minimal Persistent Domain Foundation Before Advanced Tools

Status: Accepted

JarvisOS needs persistent records for workspaces, model specs, assumptions, parameters, runs, decisions, files, links, and events before adding runners or AI workflows. This keeps future tools inside the architecture spine instead of creating isolated utilities.

## ADR-009: Use Migration-Friendly Metadata For Early Rough Records

Status: Accepted

Early engineering records may be incomplete or messy. Core tables include stable IDs, status, timestamps, schema version fields, notes, and raw payload fields where useful so later migrations and cleanup remain possible.

## ADR-010: Keep First APIs Simple And Workflow-Supporting

Status: Accepted

Milestone 0B exposes only the useful early APIs: workspaces, model specs, assumptions, parameters, simulation runs, and decisions. Lower-level entities, links, artifacts, and events remain internal until a concrete workflow needs direct API access.

## ADR-011: AI Calls Must Go Through The AI Gateway Provider Interface

Status: Accepted

All AI-assisted behavior must pass through `app/modules/ai/gateway.py`. Routes, modeling services, frontend helpers, and future utilities must not call paid providers directly.

## ADR-012: First AI Feature Is Structured Modeling Draft, Not Chat

Status: Accepted

The first AI Co-Engineering feature transforms an informal engineering idea into a structured draft for review. It is not a generic chatbot, streaming chat UI, autonomous agent loop, or Python execution workflow.

## ADR-013: Fake Provider Is Required For Tests And No-Cost Development

Status: Accepted

The fake provider is deterministic, requires no API key, spends no money, and is used by default. Backend tests must not require real provider calls.

## ADR-014: Default Monthly API Budget Is 0 USD

Status: Accepted

Paid AI is blocked by default. The user must explicitly change budget/settings before any future paid provider may be considered.

## ADR-015: Budget Guard Must Wrap All Real Provider Calls

Status: Accepted

Before any future real provider call, the gateway must check provider mode, API key availability, paid AI enablement, monthly budget, spend month-to-date, and provider-specific token caps where applicable. If cost is uncertain, the guard must be conservative.

## ADR-016: Scaleway EU Is The First Real Smoke-Test Provider

Status: Accepted

Scaleway EU was selected as the first real-provider smoke candidate because JarvisOS needed an EU-hosted diagnostic path before considering broader provider work. Milestone 0C-B implemented only the boundary and smoke-test controls; the Scaleway provider remained a no-network stub until a later milestone explicitly added real smoke calls. Later D6B/D6C decisions clarify that Scaleway is not the local privacy classifier, local gatekeeper, core router, or required future provider.

## ADR-017: Token Cap Must Stay Below Free-Tier Reference During Smoke Testing

Status: Accepted

Scaleway smoke tests default to a `500000` monthly token cap and an `800000` hard stop against a `1000000` token free-tier reference. This keeps smoke testing conservative and forces the gateway to prove cap behavior before any real provider usage is introduced.

## ADR-018: JarvisOS Enforces Routing Locally

Status: Accepted

Providers may recommend privacy or sensitivity classifications in future milestones, but they cannot authorize their own unrestricted access. JarvisOS uses local policy to decide whether content may be sent externally. In the current early-stage `FAST_DEV` mode, that policy protects structural secrets and provider credentials without broadly blocking normal public/internal technical prompts. Future `STRICT_IP` mode may block `sensitive_ip`, `confidential`, and `unknown` content more aggressively when real proprietary data enters the system.

## ADR-019: Smoke Tests Use Synthetic Data Only

Status: Accepted

AI smoke tests must use synthetic examples rather than real BlueRev secrets, proprietary geometry, or sensitive project data. The purpose is to validate gateway controls, token guards, policy decisions, and event logging without exposing actual engineering IP.

## ADR-020: Live Scaleway Calls Are Smoke-Test Only

Status: Accepted

The first real external AI call is limited to manually triggered Scaleway EU smoke tests. It must go through the AI Gateway, require paid AI, explicit Scaleway mode, explicit live smoke enablement, an environment API key, local privacy approval, and token-cap approval. Automated tests mock the provider and must never call Scaleway.

## ADR-021: AI Smoke Console Is A Guarded Smoke Surface, Not Chat

Status: Accepted

Milestone 0C-D adds a narrow manual AI Smoke Console for short harmless live Scaleway checks such as greetings. The console must use the existing AI Gateway, local privacy policy, token guard, and Scaleway provider boundary. It must not add conversation history, memory, RAG, agents, arbitrary system prompts, BlueRev modeling behavior, or Python execution. The console uses existing monthly Scaleway token counters and displays a fixed `500000` token smoke threshold for operator visibility.

## ADR-022: Python Runner V0 Is Explicit Local Execution For Reviewed Scripts

Status: Accepted

Milestone 0D-B introduces a minimal local Python Runner for reviewed deterministic scripts only. `model_versions` acts as the first ModelImplementation record, `simulation_runs` remains the canonical run record, and runner-specific metadata lives in small `runner_jobs`, `run_logs`, and `run_artifacts` tables. Execution is synchronous and explicit through a run endpoint; creating a job does not execute code. V0 uses no shell invocation, no inherited secret environment, controlled data-root paths, timeout and output limits, script hashing, and simple preflight checks, but it is not a hostile-code sandbox.

## ADR-023: Provider-neutral AI Contracts Before New Providers

Status: Accepted

Milestone 0E-D1 adds provider-neutral AI contracts before integrating additional providers. JarvisOS should expose one future Supervisor AI interface while provider/model selection remains internal, policy-driven, gated, and audited. The new contracts define provider, model, task, request, response, usage, routing, gate, authority, and registry shapes only. They do not add OpenAI, Anthropic, DeepSeek, Ollama, or any other provider, and they do not change the existing Scaleway smoke-test behavior.

## ADR-024: Scaleway Adapter Migrates First Without Expanding Provider Scope

Status: Accepted

Milestone 0E-D2 wraps the existing Scaleway live smoke-test implementation behind the provider-neutral `AIProviderAdapter` contract. The adapter maps `AIRequest` into the existing Scaleway smoke-call boundary and maps the sanitized provider result into `AIResponse` and `AIUsage`. Key resolution, local gates, smoke-only scope, monthly token counters, and no-network automated tests remain unchanged. This is not provider routing, dynamic model discovery, Supervisor AI, or the start of OpenAI, Anthropic, DeepSeek, Ollama, or other provider support.

## ADR-025: Default AI Policy Mode Is FAST_DEV

Status: Accepted

JarvisOS currently contains mostly public physics, generic code, toy models, architecture notes, and non-proprietary design exploration. The default AI policy mode is therefore `FAST_DEV`: it allows ordinary public/internal technical prompts through approved AI paths while preserving budget, token, provider, credential, event-redaction, and no-plaintext-secret boundaries. Broad keyword blocking for terms such as `patent`, `geometry`, `BlueRev`, `Smart Joint`, or `confidential` is intentionally not used in `FAST_DEV`. `STRICT_IP` remains a future mode for stricter classification and deterministic AuthorityPolicy behavior once real proprietary IP is present.

## ADR-026: Add DeepSeek As One Strong Smoke-only Provider

Status: Accepted

Milestone 0E-D4 adds exactly one strong provider adapter: DeepSeek through an OpenAI-compatible chat-completions request shape. The adapter is env-var-only through `DEEPSEEK_API_KEY`, supports only the narrow provider-smoke path, and does not add provider routing, Supervisor AI, BlueRev modeling, or a provider-specific bot UI. This validates the provider-neutral adapter boundary without expanding product scope. Automated tests mock the provider and must not call the network.

## ADR-027: First Supervisor AI Endpoint Is Public/Internal And Narrow

Status: Accepted

Milestone 0E-D5 adds `POST /ai/supervisor/public-test` as the first Supervisor AI vertical slice. It is backend-only, runs only in `FAST_DEV`, accepts bounded public/internal technical prompts, does not accept provider/model selection, and records redacted provider-neutral events. Temporary provider selection prefers the configured DeepSeek adapter and falls back to Scaleway only when explicitly configured for live smoke. This is not chat, routing, BlueRev modeling, file ingestion, runner execution, or an agent framework.

## ADR-028: Supervisor AI Uses Logical Provider Tiers, Not Provider Bots

Status: Accepted, refined by ADR-029

JarvisOS should evolve toward one stable user-facing Supervisor AI backed by logical provider tiers: `cheap`, `medium`, and `frontier`, with optional future local/offline handling. Users should not choose provider-specific bots such as DeepSeek, Grok, GPT, Gemini, Claude, or Scaleway in normal workflows. Provider/model details, tier assignments, fallback chains, credentials, and diagnostic smoke targets remain internal or admin/config-only. The current `provider_mode` field remains a compatibility control for existing smoke paths, but future Supervisor routing should use tier assignments and auditable route plans. ADR-029 corrects the ordering: local gate contracts must come before external tier contracts.

## ADR-029: Local Gatekeeper Comes Before External Provider Tiers

Status: Accepted, refined by ADR-030

The component deciding whether raw user input is safe to send externally must run locally. JarvisOS must not use Scaleway, DeepSeek, Grok, Gemini, GPT, Claude, or any other cloud provider as the first sensitivity classifier. Future Supervisor flow starts with a Local Gatekeeper that applies deterministic hard rules and, later, may use a local Gemma classifier. The gatekeeper emits a logical gate decision such as `LOCAL_ONLY`, `LOCAL_GEMMA`, `USER_CONFIRM_REQUIRED`, `CHEAP_GATE`, `CHEAP_PLUS_GATE`, `SCIENTIFIC_MEDIUM_GATE`, `FRONTIER_GATE`, or `BLOCKED`. Only after that decision may an allowed request reach an external provider adapter. Scaleway remains a smoke/simulation provider and adapter example, not the privacy classifier or core router. ADR-030 supersedes the original contract-first next step; the next milestone is `0E-D7 - Local Gemma Evaluation Harness and Golden Set`.

## ADR-030: Evaluate Local Gemma Foundation Before Gatekeeper Contracts

Status: Accepted

Before Gemma can support local gatekeeping, JarvisOS must prove that local Gemma can use context, memory, deterministic tool outputs, and structured output schemas correctly. A weak previous Jarvis/Gemma experience should not be attributed to the model alone until context packing, retrieval, tool contracts, memory design, orchestration, and evaluation are tested. The next milestone should be `0E-D7 - Local Gemma Evaluation Harness and Golden Set`, with no Gemma runtime, no routing, no external APIs, no chat UI, and no memory runtime. Local gate and external tier contracts should follow only after the evaluation foundation defines quality bars and failure categories.

## ADR-031: Local Gemma Evaluation Harness Comes Before Runtime Adapter

Status: Accepted

Milestone 0E-D7 adds a backend-local golden set and deterministic scoring harness for future Gemma evaluation. The harness currently validates 95 synthetic cases across conversation continuity, Codex log summarization, prompt drafting, decision/TODO extraction, sensitivity/complexity classification, local-only note handling, public technical Q&A, retrieval interpretation, tool grounding, hallucination resistance, and schema compliance. It defines a strict `GemmaEvalOutput` schema and critical safety failure rules, but it does not call Gemma, Ollama, llama.cpp, LiteLLM, external providers, or any model server. The next milestone may be `0E-D8 - Local Gemma Runtime Adapter Dry Run`, using this harness as the boundary.

## ADR-032: Local Operating Brain Must Request Bounded Context

Status: Accepted

Milestone 0E-D7B extends the D7 harness so future local Gemma is evaluated as a local operating brain, not only a model answering from already supplied context. Gemma should be able to identify missing context, request bounded context packages from a controlled vocabulary, interpret partial context, ask for more context when needed, and avoid hallucinating file/tool/database results. The schema adds state, context sufficiency, requested context packages, allowed/forbidden tool requests, external prompt, and external-call intent fields. External calls remain non-executable in this harness; `external_call_requested` must remain false unless a later explicit runtime/policy milestone permits execution.

## ADR-033: Harden Local Gemma Evaluation Before Runtime

Status: Accepted

Milestone 0E-D7C reviews and hardens the D7/D7B evaluation harness before any real Gemma runtime is connected. The harness must reject duplicate or invalid golden cases, require missing-context rationale for context-request states, require expected forbidden tool requests to be explicitly marked as forbidden, reject invalid prose or JSON-like output as schema-invalid, and treat premature external prompts/calls as critical failures. D8 may run a local Gemma adapter only as a dry-run producer of schema outputs for this scorer; it must not add chat, tool execution, memory runtime, retrieval runtime, local gate enforcement, routing, or external provider calls.

## ADR-034: D8 Local Gemma Runtime Is Evaluation-Only

Status: Accepted

Milestone 0E-D8 adds a local Gemma runtime adapter dry run that can call only explicitly configured localhost OpenAI-compatible endpoints. It requires no API key and rejects non-local URLs, HTTPS URLs, credentials in URLs, private LAN IPs, and external domains. The adapter may produce only schema outputs for the D7/D7B/D7C deterministic scorer and local report. D8 does not add chat, memory runtime, file/database retrieval, context broker runtime, local gatekeeper enforcement, provider routing, external APIs, frontend UI, autonomous tools, or BlueRev modeling.

## ADR-035: D9 Gemma Evaluation Does Not Approve Operating-Brain Use

Status: Accepted

Milestone 0E-D9 ran the first local Gemma evaluation through the D8 adapter and D7 scorer. `gemma4:12b-it-qat` completed only the Stage 1 smoke subset and produced zero schema-valid outputs. `gemma4:31b-it-qat` did not complete the Stage 1 subset and timed out on a single-case probe under the current local setup. These results do not approve Gemma for local chat, memory runtime, context broker runtime, local gatekeeping, provider routing, autonomous tools, or BlueRev modeling. Any follow-up must remain evaluation-only and focus on local runtime latency, prompt/protocol simplification, schema simplification, and JSON compliance before Gemma can be reconsidered as a local operating-brain candidate.

## ADR-036: D9R Requires Staged Local Gemma Schemas Before Full D7 Output

Status: Accepted

Milestone 0E-D9R diagnosed the D9 failure with local-only probes. Both `gemma4:12b-it-qat` and `gemma4:31b-it-qat` can emit tiny direct JSON objects. `gemma4:12b-it-qat` still failed a compact operating-brain schema in both OpenAI-compatible and native Ollama modes. `gemma4:31b-it-qat` passed the compact schema only through native Ollama structured output, but timed out on a full D7 one-case probe even with native schema output and a simplified prompt. JarvisOS should not proceed to full local operating-brain behavior. The next local-AI milestone, if pursued, must remain evaluation-only and use staged schemas and protocol simplification before reconsidering the full `GemmaEvalOutput` contract.

## ADR-037: Local Gemma Uses Micro-Contracts Before Runtime Orchestration

Status: Accepted

Milestone 0E-D10A replaces the first-runtime-contract strategy for local Gemma. Instead of asking Gemma for one large `GemmaEvalOutput`, JarvisOS should evaluate small, independent micro-contracts such as task classification, context request, sensitivity check, tool-call proposal, external prompt draft, TODO extraction, decision extraction, and evidence selection. Gemma may propose structured objects only; JarvisOS remains responsible for validation, policy, execution, persistence, audit, retrieval, memory, and external API calls. D10A adds isolated schema models and documentation only. It does not add chat, memory runtime, retrieval runtime, local gatekeeping, provider routing, frontend UI, autonomous tools, or BlueRev modeling.

## ADR-038: D10B Micro-Contract Probes Do Not Approve Gemma Runtime Orchestration

Status: Accepted

Milestone 0E-D10B tested `gemma4:31b-it-qat` against the D10A micro-contracts using local Ollama native structured output and the real Pydantic JSON schemas exported by each contract. All 16 probe cases returned empty content and failed as invalid JSON. This does not approve Gemma for staged local orchestration, local chat, memory runtime, retrieval runtime, local gatekeeping, provider routing, autonomous tools, or BlueRev modeling. Because D9R showed that a hand-written compact schema can work, the likely next local-AI diagnostic would be schema-compatibility testing for Pydantic `$defs`/`$ref` versus flattened schemas. Product work should not wait on that if BlueRev Model Foundry progress is more important.

## ADR-039: D10B-R Separates Schema/Budget Issues From Gemma Model Judgement

Status: Accepted

Milestone 0E-D10B-R showed that empty Ollama `message.content` can occur while `message.thinking` is non-empty and `done_reason=length`, so D10B's empty-content failures were not sufficient evidence that Gemma cannot perform micro-contract tasks. With higher `num_predict` and flat/direct schemas, `gemma4:12b-it-qat` passed several lightweight contract probes and `gemma4:31b-it-qat` passed a limited comparison, but 31B remained too slow for routine orchestration. Future local-Gemma evaluation should prefer flat schemas, explicit thinking/output-budget diagnostics, and 12B as the lightweight candidate; 31B should be reserved for occasional heavy local expert probes. This still does not authorize chat, memory runtime, retrieval runtime, context broker runtime, local gatekeeping, provider routing, autonomous tools, frontend UI, or BlueRev modeling.

## ADR-040: D10C Limits Local Gemma To Classification-Style Utility Candidates

Status: Accepted

Milestone 0E-D10C replaced the misleading D10B probe path with flat schemas, thinking-aware diagnostics, 12B-first probing, repeatability checks, and a limited 31B comparison. `gemma4:12b-it-qat` passed and repeated only task classification and sensitivity classification; it failed context request, TODO extraction, decision extraction, and evidence selection due to thinking budget exhaustion. `gemma4:31b-it-qat` passed the limited comparison on task classification, context request, and sensitivity check but remained too slow for routine orchestration. JarvisOS should not proceed to local Gemma orchestration, local gatekeeping, memory runtime, retrieval runtime, context broker runtime, chat, provider routing, autonomous tools, frontend UI, or BlueRev modeling. If local Gemma work continues, it should be limited to classification-style utility design with JarvisOS policy remaining authoritative.
