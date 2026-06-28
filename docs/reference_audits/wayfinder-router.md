# Wayfinder Router Reference Audit

## Pinned source

* repository: https://github.com/itsthelore/wayfinder-router
* commit hash: `c872b2a3b19bf514c93d4e9788f2a8d502d69fa7`
* license: Apache-2.0
* inspected date: 2026-06-28

## Executive verdict

YELLOW as a JarvisOS reference.

Reason: Wayfinder is a strong reference for deterministic, offline, explainable routing architecture, but its decision axis is prompt complexity, not JarvisOS policy. It does not encode sensitivity class, consent/IP handling, or an economic envelope in the scored path, so it is useful as a structural pattern source rather than a direct routing template.

## Architecture map

* `pyproject.toml`
  * Exposes `wayfinder-router` as the CLI entrypoint.
  * Splits optional surfaces by extra: `gateway`, `ui`, `tui`, `all`.
  * Keeps the deterministic core on stdlib only; impure dependencies are isolated behind extras.
* `wayfinder_router/complexity.py`
  * Core scorer and routing policy.
  * Defines `Lexicon`, `Tier`, `ClassifierModel`, `RoutingConfig`, `ComplexityScore`.
  * Implements `strip_frontmatter`, `extract_features`, `normalized_features`, `scalar_score`, `recommend_tier`, `score_complexity`, `explain_score`.
  * Feature extraction is deterministic and offline: headings, lists, code fences, tables, links, lexical cues, question marks.
* `wayfinder_router/config.py`
  * Walk-up discovery for `wayfinder-router.toml`.
  * Pure TOML parsing and validation via `tomllib`.
  * Environment override for binary threshold through `WAYFINDER_ROUTER_THRESHOLD`.
  * Round-trip dump helpers for routing config.
* `wayfinder_router/cli.py`
  * Main CLI entrypoint and subcommands.
  * `route` emits human text or JSON.
  * `calibrate` fits threshold / tiers / classifier configs from JSONL labels.
  * `serve`, `webchat`, `ui`, `chat`, `onboard`, `recalibrate`, `init`, `doctor`, `keys`.
  * Handles user-facing exit codes and file-not-found/config errors.
* `wayfinder_router/gateway.py`
  * Optional FastAPI gateway behind the `gateway` extra.
  * OpenAI-compatible proxy surface: `/v1/chat/completions`, `/chat/completions`, `/v1/models`, `/models`.
  * Dry-run path returns routing decision without upstream calls.
  * Response metadata: `x-wayfinder-router-model`, `x-wayfinder-router-score`, `x-wayfinder-router-mode`, `x-wayfinder-router-request-id`.
  * Diagnostic surfaces: `/healthz`, `/metrics`, `/router`, `/router/recent`, `/router/models`, `/router/profiles`, `/demo`, `/savings`, `/v1/feedback`.
  * Secret handling is env-based: `api_key_env` names the env var; `api_key_cmd` can populate it in memory at startup; the secret itself is never written to config.
  * Hot reload, retries, circuit breaker, cache, rate limit, virtual key support, and cost/savings accounting are all isolated from the scorer.
* `wayfinder_router/pricing.py`
  * Token estimation, cost table, turn-cost accounting, and savings ledger.
* `wayfinder_router/reliability.py`
  * Retryability, backoff, circuit breaker, and failover candidate planning.
* `wayfinder_router/cache.py`
  * Exact-match response cache.
* `wayfinder_router/ratelimit.py`
  * RPM/TPM rate limiting.
* `wayfinder_router/vkeys.py`
  * Virtual API key minting and bearer-token matching.
* `wayfinder_router/bootstrap.py`
  * Key resolution helpers and onboarding/doctor support.
* `wayfinder_router/anthropic_adapter.py`
  * Claude Code / Anthropic-compatible translation layer.
* `benchmarks/`
  * Offline harness and adapters for benchmark datasets.
  * `run.py` prints the markdown report.
  * `harness.py` defines the metric model and knee selection.
  * `routers.py` holds offline router baselines and the Wayfinder adapter.
  * `routerbench_adapter.py` and `routerarena_adapter.py` convert public benchmark sources into the local harness format.
* `tests/`
  * Broad unit coverage for scorer, config, CLI, gateway, pricing, reliability, benchmarks, adapters, UI, and TUI.
  * Gateway tests stub all upstream transport so no real network or key is needed.
* `docs/`, `examples/`, `decisions/`, `designs/`, `roadmaps/`
  * Document the architecture, integration recipes, and the design/ADR history around deterministic routing, gateway behavior, calibration, cost, metrics, and licensing.

## Transferable patterns

* Split the system into a pure deterministic core and a separate impure gateway/invocation layer.
* Keep the scorer a pure function over text plus immutable config.
* Make feature extraction explicit, stable, and inspectable.
* Preserve a versioned JSON output contract for the route decision.
* Sort and validate tier thresholds deterministically.
* Support config round-trip dumps so calibration output can be persisted verbatim.
* Emit explainability fields that show feature contribution, not just the final decision.
* Provide a dry-run mode that exercises routing without upstream dependencies.
* Use a benchmark harness with always-local, always-cloud, random, and oracle baselines.
* Sweep thresholds and choose a cost-aware knee rather than a single arbitrary cut.
* Keep test fixtures offline, monkeypatched, and deterministic.
* Separate core, gateway, UI, and benchmark code at the module level.
* Keep secrets out of config payloads; store only env-var names or command references.

## Non-transferable patterns

* Binary local/cloud routing as the primary model. JarvisOS needs policy-aware provider selection, not a two-tier complexity switch.
* Routing driven only by prompt complexity or lexical cues.
* The `prefer-local` / `prefer-hosted` / OpenAI-model-field routing directives as a direct JarvisOS abstraction.
* Gateway-first architecture that presumes OpenAI-compatible client proxying as the main product surface.
* Any assumption that the score can stand in for sensitivity, consent, IP risk, or operational permission.
* Any provider-facing semantics that ignore JarvisOS `provider_candidate` vs `provider_class`.
* Any cost framing that is only about per-call spend, rather than an economic envelope tied to success criteria.
* Direct reuse of Wayfinder's lexical heuristics without revalidation against JarvisOS policy classes.

## JarvisOS adaptation proposal

Minimal future components to derive from this reference, adapted for policy routing:

* `deterministic_task_complexity_score`
  * Pure scoring function for task shape only.
  * Must never be the sole authority for routing.
* `sensitivity_intelligence_matrix`
  * Primary policy matrix combining sensitivity class and task intelligence level.
  * Should own the route eligibility boundary.
* `provider_candidate/provider_class mapping`
  * Separate candidate providers from abstract provider classes.
  * Keep concrete endpoints out of the policy layer.
* `route_decision_audit_fields`
  * Record sensitivity class, task level, provider candidate/class, economic envelope, dry-run/confirmation boundary, and cost-per-success benchmark.
* `dry_run router CLI`
  * Deterministic preview of the routing decision without dispatching work.
* `benchmark fixtures`
  * Offline fixtures that evaluate decision quality against cost-per-success and policy correctness, not prompt complexity alone.

## Test patterns to copy conceptually

* Deterministic scorer stability across repeated runs.
* Frontmatter / non-semantic wrapper stripping tests.
* Fence-aware feature extraction tests.
* Threshold boundary and tier ordering tests.
* Config parse, validation, and round-trip tests.
* JSON output contract tests with schema versioning.
* Dry-run tests that assert no upstream call occurs.
* Secret handling tests that verify env vars are read late and never serialized.
* Gateway error-shaping tests for upstream failure, misconfiguration, and auth failure.
* Benchmark tests for oracle, baselines, sweep, and knee selection.
* Adapter tests that prove external benchmark formats are normalized correctly.
* CLI exit-code tests for usage/config/file errors.

## License/attribution notes

* License is Apache 2.0.
* Code and substantial text can be copied only if Apache 2.0 terms are preserved.
* If any code or adapted text is copied later, keep the copyright notice, retain the Apache license text, and preserve or update `NOTICE` as required.
* Attribution should remain in the derivative artifact metadata and any redistribution bundle.
* The license is permissive, but it does not waive the need to retain notices and mark modifications.

## Recommended next slice

After A7-PRE, the smallest JarvisOS slice is a pure policy-spec package for routing decisions: define the audit schema and a deterministic dry-run evaluator around `sensitivity_intelligence_matrix` and `cost_per_success`, with no provider registry, no runtime routing, and no upstream calls.
