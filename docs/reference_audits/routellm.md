# RouteLLM Reference Audit

## Pinned source

* repository: `C:\Users\thera\Documents\JarvisOS_external_refs\routing\RouteLLM`
* commit hash: `0b64fdafe049e596a3f5657c219329f24af24198`
* license: Apache-2.0
* inspected date: 2026-06-28

## Executive verdict

YELLOW as a JarvisOS reference.

RouteLLM is a strong reference for economic routing evaluation, strong/weak model framing, threshold calibration, benchmark curves, and OpenAI-compatible routing surfaces. It is not a direct JarvisOS routing design because its learned/static routers can become the routing authority, it assumes provider dispatch, and it does not encode sensitivity class, IP/privacy status, consent, or a JarvisOS economic envelope before model selection.

## Architecture map

* `README.md`
  * Product and research overview.
  * Documents strong/weak model routing, `router-[router]-[threshold]` model names, threshold calibration, server mode, supported routers, and evaluation workflow.
* `pyproject.toml`
  * Package metadata for `routellm`.
  * Core dependencies include `pyyaml`, `pydantic`, `numpy`, `pandas`, `torch`, `scikit-learn`, `openai`, `transformers`, `datasets`, and `litellm`.
  * Optional extras: `serve` for FastAPI/Uvicorn server, `eval` for benchmark plotting/evaluation, `dev` for formatting hooks.
* `config.example.yaml`
  * Router initialization config.
  * Points to Hugging Face datasets/checkpoints for `sw_ranking`, `causal_llm`, `bert`, and `mf`.
* `routellm/controller.py`
  * Main SDK-compatible controller.
  * Loads router classes from `ROUTER_CLS`.
  * Stores `ModelPair(strong, weak)`.
  * Parses `model="router-[router]-[threshold]"`.
  * Routes the last user turn through the selected router, then dispatches through LiteLLM `completion` / `acompletion`.
* `routellm/openai_server.py`
  * Optional OpenAI-compatible FastAPI server.
  * Exposes `/v1/chat/completions` and `/health`.
  * Initializes a global `Controller` at server lifespan startup.
  * Forwards routed requests to actual provider models through the controller.
* `routellm/routers/routers.py`
  * Defines abstract `Router`.
  * Router contract: `calculate_strong_win_rate(prompt) -> float`; route to strong model when score is greater than or equal to threshold.
  * Implements `RandomRouter`, `MatrixFactorizationRouter`, `SWRankingRouter`, `BERTRouter`, and `CausalLLMRouter`.
  * `mf`, `bert`, and `causal_llm` load model checkpoints; `sw_ranking` loads Arena datasets/embeddings and uses OpenAI embeddings.
* `routellm/calibrate_threshold.py`
  * Calibrates thresholds by quantile over precomputed router win rates.
  * Target is a desired percentage of strong-model calls.
  * Can generate and push threshold data, or read existing threshold data from Hugging Face.
* `routellm/evals/evaluate.py`
  * CLI evaluation entrypoint.
  * Sweeps router thresholds and records accuracy versus strong-model call percentage.
  * Computes benchmark plots and summary metrics: percent calls needed for 20/50/80 percent quality recovery, AUC, and APGR.
* `routellm/evals/benchmarks.py`
  * Benchmark abstraction plus `MMLU`, `MTBench`, and `GSM8K`.
  * Uses cached model outputs/judgements where possible.
  * Includes decontamination filters and optimal accuracy calculations.
* `benchmarks/README.md`
  * Documents comparison against commercial routers.
  * Frames results as MT-Bench score versus strong-model call fraction/cost assumptions.
* `examples/`
  * Python SDK and OpenAI-compatible server examples.
  * Includes local-model routing with Ollama as weak model.
* `routellm/tests/`
  * Contains executable smoke/demo scripts for client and server usage.
  * These are not a strong unit-test pattern for JarvisOS by themselves.
* `LICENSE`
  * Apache License 2.0 text.

## Routing model

RouteLLM routes between a strong model and a weak model.

* Strong/weak model framing:
  * The controller is initialized with `strong_model` and `weak_model`.
  * Each router estimates how likely the strong model is to be preferable for the prompt.
  * The selected provider model is one of the two concrete model names.
* Thresholds:
  * Request model names encode router and threshold as `router-[router name]-[threshold]`.
  * Router score greater than or equal to threshold routes to strong; otherwise weak.
  * Higher thresholds reduce strong-model calls and generally reduce cost with quality risk.
* Scoring/calibration:
  * `calibrate_threshold.py` selects a threshold by quantile so a target percentage of traffic routes to the strong model on calibration data.
  * Evaluation sweeps thresholds and plots quality versus strong-model call percentage.
* Learned/static components:
  * `random` is a baseline router.
  * `mf` uses a matrix-factorization model over model IDs and prompt text.
  * `bert` uses a sequence classifier checkpoint.
  * `causal_llm` uses an LLM classifier checkpoint.
  * `sw_ranking` uses similarity-weighted Arena battle data and embeddings.
* Runtime dispatch boundaries:
  * `Controller.route()` returns the selected model name without dispatch.
  * `Controller.completion()` and `Controller.acompletion()` route and then call LiteLLM.
  * `openai_server.py` exposes this as an OpenAI-compatible runtime service.

## Economic routing patterns

Transferable economic patterns:

* Cost-quality tradeoff:
  * Express router performance as quality retained versus fraction of strong/frontier calls.
  * Treat a threshold as an operating point, not a policy decision by itself.
* Benchmark baselines:
  * Always-weak baseline.
  * Always-strong baseline.
  * Random routing baseline.
  * Optimal/oracle routing curve for upper-bound comparison.
* Cost_per_success:
  * JarvisOS should adapt the strong-call fraction into `cost_per_success`, using success labels and actual/estimated costs.
  * RouteLLM's APGR and AUC patterns are useful, but JarvisOS needs a cost-normalized success metric with policy violations counted as failures.
* Threshold sweeps:
  * Sweep thresholds to produce a curve instead of selecting one opaque default.
  * Store the chosen threshold with the dataset, model pair, costs, and benchmark version.
* Always-cheap / always-frontier / oracle comparisons:
  * Keep all three in JarvisOS reports so economic claims do not float without a baseline.
* Evaluation metrics:
  * Strong-model call percentage, accuracy/performance, AUC, APGR, and quality-recovery points are useful reference metrics.
  * JarvisOS should add policy-pass rate, sensitivity-gate violations, external-egress violations, and cost-per-success.

## Transferable patterns

* Separate router scoring from provider dispatch.
* Treat threshold calibration as data-bound and traffic-specific.
* Use a versioned benchmark report that records model pair, threshold, dataset, and metric definitions.
* Evaluate routing as a curve, not a single point.
* Keep always-cheap, always-frontier, random, and oracle baselines.
* Record route counts by provider class and compare them to quality outcomes.
* Preserve a dry-run path that returns route decisions without calling a provider.
* Make the router interface narrow enough that multiple router strategies can be evaluated under the same harness.
* Include decontamination/history-contamination checks in benchmark preparation.

## Non-transferable patterns

* A model-based router must not become the authority in JarvisOS.
* Strong/weak routing must not run before sensitivity, IP/privacy, consent, and allowed-egress gates.
* Provider dispatch through LiteLLM/OpenAI-compatible surfaces must not appear before a JarvisOS provider registry milestone.
* `router-[router]-[threshold]` in the OpenAI `model` field should not be copied as a JarvisOS contract.
* Calibration against public preference data is not enough for internal/private JarvisOS workloads.
* Routers that require embeddings, checkpoints, Hugging Face downloads, OpenAI embeddings, or model calls are not acceptable inside JarvisOS dry-run/spec layers.
* RouteLLM tests are not sufficient as a JarvisOS testing model because they are mostly executable examples rather than assertive policy tests.

## JarvisOS adaptation proposal

* `cost_per_success benchmark spec`
  * Define offline benchmark rows with task, sensitivity class, expected policy route, cost estimate, success label, and policy-pass label.
  * Report cost per successful and policy-compliant result.
* `frontier_primary vs pre_frontier vs cheap_cloud`
  * Map strong/weak concepts into JarvisOS provider classes.
  * Keep `frontier_primary`, `pre_frontier`, and `cheap_cloud` as classes, not provider endpoints.
* `provider_candidate/provider_class separation`
  * A benchmark row may name candidate providers, but the routing contract should first select allowed provider class.
  * Concrete provider candidates remain advisory until a future registry milestone.
* `no-upstream-call dry-run evaluator`
  * Build a deterministic evaluator that reads fixtures and emits route decisions, costs, and policy fields without network/model calls.
* `sensitivity gate before economic routing`
  * Economic routing runs only after sensitivity/IP/consent gates have determined that external egress and model use are allowed.
  * For S2/S3/S4 material, economic preference must never override policy.

## Adoption boundary

RouteLLM is a reference only.

No vendoring, no runtime integration, no provider execution, no API keys, and no dependency addition are approved by this audit. Any future code reuse must be explicit, license-compliant, attributed, marked as modified, and covered by JarvisOS-specific tests.

## License/attribution notes

* RouteLLM is licensed under Apache-2.0.
* Future copying of code or substantial text would require preserving the Apache-2.0 license text and copyright/license notices.
* Modified copied code must be clearly marked as changed.
* If a future upstream distribution includes a `NOTICE` file, JarvisOS must preserve required NOTICE contents; no `NOTICE` file was present in this inspected checkout.
* This audit does not copy RouteLLM code and does not create a derivative implementation.

## Recommended next slice

After A7-PRE, add a docs/test/spec-only JarvisOS economic-routing benchmark contract: offline fixtures plus a markdown spec for `cost_per_success`, provider-class baselines, threshold sweeps, and policy-gate failure accounting. Do not add provider dispatch, registry integration, API keys, or model calls in that slice.
