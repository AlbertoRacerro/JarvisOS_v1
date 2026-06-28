# DeepSparkInference Reference Audit

## Pinned source

* repository: `C:\Users\thera\Documents\JarvisOS_external_refs\inference\DeepSparkInference`
* commit hash: `76f100b2acaa09c7a0253c086629b6ecc5e96303`
* license: Apache-2.0
* inspected date: 2026-06-28

## Executive verdict

YELLOW as a JarvisOS reference.

DeepSparkInference is useful as a concrete reference for local inference runtime organization, model/backend metadata, hardware-specific setup boundaries, and benchmark reporting. It is not a JarvisOS policy-router reference: it assumes direct runtime execution, vendor GPU stacks, model-specific scripts, benchmark servers, and environment mutation. JarvisOS should adapt the documentation, metadata, validation, and benchmark-reporting patterns without copying runtime scripts or coupling policy decisions to inference backends.

## Architecture map

* `README_en.md`: English overview of DeepSparkInference as a ModelZoo. Describes supported model domains, backend engines, model tables, IXUCA SDK compatibility, and the supported engine mix across CV, NLP, LLM, speech, multimodal, and other workloads.
* `README.md`: Chinese root overview. Terminal rendering was not reliable in this Windows PowerShell session, so `README_en.md` was used as the readable root reference.
* `LICENSE`: Apache License 2.0 for the root project.
* `RELEASE.md`: release notes and version history.
* `CONTRIBUTING.md`: contribution process.
* `docs/README_TEMPLATE.md`: reusable model-card template. Separates supported environments, model preparation, resource preparation, dependency installation, conversion, inference, results, and references.
* `models/`: primary model zoo. Organized by domain: `audio/`, `benchmark/`, `cv/`, `multimodal/`, `nlp/`, `others/`, and `speech/`.
* `models/<domain>/<task>/<model>/<backend>/`: recurring model package shape. Typical contents include model-specific README files, requirements, `ci/prepare.sh`, inference scripts, performance scripts, accuracy scripts, and backend-specific assets.
* `models/benchmark/`: benchmark harnesses for serving, multimodal serving, and LongBench-style evaluation. Includes `benchmark_serving.py`, `benchmark_serving_multimodal.py`, `benchmark_longbench.py`, shell wrappers, environment setup, requirements, and per-model benchmark records.
* `models/benchmark/benchmark_serving.py`: OpenAI-compatible serving benchmark client. Measures request throughput, output token throughput, total token throughput, time-to-first-token, time-per-output-token, inter-token latency, and end-to-end latency percentiles.
* `models/benchmark/benchmark_longbench.py`: long-context benchmark runner using vLLM and LongBench-style task metrics such as QA F1, Rouge, retrieval scores, classification, counting, and code similarity.
* `models/benchmark/test_performance_server.sh`: runtime benchmark wrapper that starts a vLLM OpenAI-compatible API server, waits for local readiness, runs the benchmark client, and cleans up server processes.
* `models/benchmark/test_performance_server_multimodal.sh`: multimodal equivalent of the serving benchmark wrapper.
* `models/benchmark/test_vllm_longbench.sh`: environment setup plus LongBench evaluation wrapper.
* `models/benchmark/set_environment.sh`: installs benchmark dependencies with `pip3` and an external package mirror. This is an invasive setup script and should not be copied into JarvisOS core.
* `tests/README.md`: states that the test scripts are for CI runner usage.
* `tests/model_info.json`: large model metadata catalog. Captures display name, model name, framework, release versions, SDK/GPGPU requirements, category, toolbox, dimensions, datasets, license, model path, README path, download URL, third-party dependency flag, precisions, type, demo metadata, and descriptions.
* `tests/run_vllm.py`: CI runner for vLLM/PyTorch-style models. Reads model metadata, checks SDK assumptions, builds model-specific shell scripts, sets hardware/runtime environment variables, and invokes offline inference or benchmarks.
* `tests/run_igie.py`: CI runner entrypoint for IGIE-backed examples.
* `tests/run_ixrt.py`: CI runner entrypoint for ixRT-backed examples.
* `tests/run_trtllm.py`: CI runner entrypoint for TensorRT-LLM-backed examples.
* `tests/utils.py`: CI utilities including environment flags and automatic `numactl` installation attempts through system package managers.
* `toolbox/ByteMLPerf/`: nested benchmark toolbox with its own `LICENSE` and `NOTICE`. It must be treated as a separate third-party component for any future reuse analysis.
* `.gitee/`, `data/`: repository support and data-related directories.

## Runtime model

DeepSparkInference targets local and server-side inference on vendor-specific GPU infrastructure, especially Iluvatar CoreX GPGPU stacks. The root documentation highlights IXUCA SDK compatibility and model examples for Iluvatar GPU Inference Engine (IGIE), ixRT, vLLM, TensorRT-LLM, TGI, FastDeploy, LMDeploy, Transformers, PyTorch, IxFormer, xDiT, Diffusers, ComfyUI, and related model-serving or inference frameworks.

Hardware and backend assumptions include:

* Iluvatar CoreX GPGPU and Zhikai 100 references in documentation and evaluation notes.
* IXUCA SDK version compatibility tracked per model.
* Backend-specific engines such as IGIE and ixRT.
* GPU runtime variables such as `CUDA_VISIBLE_DEVICES`.
* Hardware monitoring and cleanup assumptions such as `ixsmi`.
* Tensor parallel and backend-specific launch flags.
* Local filesystem conventions such as `/mnt/deepspark/...` in CI runner scripts.

Inference is launched through a mix of model-specific scripts and benchmark runners:

* Model packages commonly use `ci/prepare.sh` for setup or preparation.
* Model packages commonly use `scripts/infer_*` scripts for accuracy, performance, or offline inference.
* Benchmark wrappers can start a local vLLM OpenAI-compatible API server with `python3 -m vllm.entrypoints.openai.api_server`.
* Benchmark clients then send local HTTP requests to the server.
* Test runners dynamically generate and execute shell commands from `tests/model_info.json`.

Models and configs are organized as a model zoo rather than as a policy registry:

* Domain-level directories separate CV, NLP, multimodal, speech, audio, benchmark, and miscellaneous models.
* Model-level directories encode backend and script choices.
* `tests/model_info.json` acts as a central metadata catalog for CI/runtime assumptions.
* Model READMEs and the shared README template define environment, preparation, inference, and result expectations.

Benchmarks and performance scripts live in several layers:

* `models/benchmark/` provides shared serving and LongBench benchmark harnesses.
* Model-specific directories provide local `scripts/infer_*_performance.sh` or equivalent wrappers.
* `toolbox/ByteMLPerf/` provides a nested microbenchmark/performance toolbox.
* Benchmark reporting includes latency percentiles, throughput metrics, token counts, successful request counts, and long-context task metrics.

Unsafe assumptions for JarvisOS core:

* Installing dependencies or system packages during tests or runtime.
* Starting local inference servers from policy code.
* Killing server or GPU processes from generic scripts.
* Assuming vendor-specific GPU tooling inside core.
* Assuming model artifacts or external downloads are available.
* Allowing `--trust-remote-code` or model-specific dynamic code paths inside core.
* Treating benchmark execution as a router decision.
* Treating backend availability as policy authorization.

## Transferable patterns

* Environment validation: JarvisOS should define a read-only hardware and runtime capability report before enabling any local backend milestone.
* Runtime/backend separation: backend launch, health, and benchmark logic should remain below the policy router and should not decide sensitivity, consent, or economic policy.
* Benchmark reporting: adopt structured performance fields such as throughput, latency percentiles, token counts, success counts, and benchmark duration.
* Hardware capability checks: represent GPU, memory, SDK, driver, quantization, context length, and backend support as reported capabilities, not as implicit assumptions.
* Install/run separation: documentation should separate environment preparation, dependency installation, model preparation, inference launch, benchmark run, and result interpretation.
* Model-card structure: adapt the `docs/README_TEMPLATE.md` concept into JarvisOS local-backend documentation with supported environment, model preparation, run mode, dry-run behavior, benchmark result, and limitations sections.
* Metadata catalog shape: adapt the idea of `tests/model_info.json` into a JarvisOS-owned capability manifest for local backend candidates, without importing model paths, download URLs, or vendor assumptions.
* Benchmark harness shape: keep benchmark clients independent from routing policy, with explicit input fixture selection, deterministic seeds where applicable, and machine-readable output.
* Serving boundary: if JarvisOS later supports local OpenAI-compatible servers, treat them as backend endpoints behind an authorization layer, not as router authorities.
* No-policy-in-runtime boundary: inference runtime packages should expose capabilities and execution results only. Sensitivity, consent, economic envelope, and dry-run confirmation remain outside the backend.

## Non-transferable patterns

* Hardware-specific assumptions in core: do not encode Iluvatar, IXUCA, IGIE, ixRT, `ixsmi`, CUDA flags, tensor parallel defaults, or filesystem paths in JarvisOS core policy code.
* Invasive install scripts: do not copy scripts that call package managers, install Python packages, or mutate the host environment as part of validation.
* Runtime dispatch before provider registry: do not launch vLLM, IGIE, ixRT, TensorRT-LLM, TGI, FastDeploy, LMDeploy, or any other backend before a future JarvisOS provider/backend registry milestone explicitly defines the boundary.
* Model artifacts inside JarvisOS: do not vendor model weights, model configs, benchmark datasets, external download URLs, or model-specific generated scripts into core.
* Secrets/config leakage: do not add API keys, provider credentials, external endpoint configuration, or implicit auth behavior. The inspected serving benchmark used placeholder authorization for local testing, but JarvisOS should still require an explicit no-secret contract.
* Coupling inference runtime to policy decisions: backend availability must not override sensitivity class, IP gate, consent boundary, dry-run mode, or economic envelope.
* Benchmark server wrappers in core: do not copy wrappers that start servers, poll ports, run HTTP benchmarks, and kill processes. JarvisOS can define a spec for such behavior later, outside core routing.
* Auto-download and trust-remote-code behavior: do not adapt direct external model download or `--trust-remote-code` patterns into any default JarvisOS path.
* CI runner shell generation: do not directly port model-specific shell generation. If needed later, JarvisOS should use explicit, reviewed backend fixtures.

## JarvisOS adaptation proposal

Map DeepSparkInference ideas into future JarvisOS components as follows:

* `local_inference_backend` abstraction: a future interface that reports capabilities and can execute only after policy authorization. It should not classify sensitivity, select providers, or approve cost.
* Hardware capability report: a read-only report that records available accelerator type, driver/runtime versions, memory, supported precision, max context limits, installed backend packages, and known limitations.
* Offline benchmark harness: a deterministic benchmark runner that can consume fixed prompts and expected metric schemas without contacting external providers or changing policy decisions.
* Provider candidate local backend metadata: a JarvisOS-owned manifest for local candidates such as model id, backend class, context limits, precision, hardware requirement, expected latency envelope, benchmark provenance, and support status.
* Separation from sensitivity/economic policy router: the router may consume backend metadata and benchmark summaries, but policy decisions must be made first by sensitivity, consent, confirmation, and economic envelope rules.
* Dry-run capability inspection: before any runtime execution milestone, JarvisOS should support a dry-run command that prints what local backend would be eligible, why, and what constraints prevent execution.
* Benchmark-result schema: define machine-readable fields for latency, throughput, cost proxy, success rate, failure class, hardware profile, model hash or version, and dataset fixture id.

## Adoption boundary

DeepSparkInference is a runtime/inference reference only.

No vendoring, no runtime integration, no provider execution, no install scripts copied, no model artifacts copied, no provider registry added, and no API keys or external endpoints configured.

Any future code reuse must be explicit, license-compliant, attributed, marked as modified, and covered by JarvisOS-specific tests. Any future backend execution must be introduced through a dedicated milestone after the policy router, provider/backend registry, consent boundary, and dry-run confirmation model are defined.

## License/attribution notes

The root project is licensed under Apache-2.0. If JarvisOS later copies any code, documentation structure, scripts, or substantial implementation details, the future change must:

* preserve applicable copyright and license notices;
* include Apache-2.0 license text or a compliant reference;
* mark modified files where applicable;
* avoid implying upstream endorsement;
* document what was copied versus independently reimplemented;
* add JarvisOS-specific tests around the adapted behavior.

The nested `toolbox/ByteMLPerf/` directory contains its own `LICENSE` and `NOTICE`. It must be reviewed independently before any future reuse. This audit does not approve copying ByteMLPerf code or assets.

This audit copied no DeepSparkInference code into JarvisOS.

## Recommended next slice

After routing matrix work, add a docs/test/spec-only local inference capability slice:

* `docs/routing/LOCAL_INFERENCE_BACKEND_CAPABILITY_CONTRACT.md`
* a JSON fixture describing local backend capability reports;
* a schema/spec test that validates required fields and confirms the fixture cannot dispatch providers;
* no backend runtime, no model execution, no install script, no provider registry, and no policy-router integration.
