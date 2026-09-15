# JarvisOS / BLUECAD / BlueRev idea intake and candidate-integration register

Status: canonical intake register; **not implementation authority**  
Created: 2026-08-19  
Last audit update: 2026-09-15  
Owner: repository maintainer

This is the compact canonical register for external projects, papers, products, repositories, architectural patterns, engineering ideas, hardware concepts and other material that may be useful to JarvisOS, BLUECAD or BlueRev.

`docs/specs/STATUS.md` remains the sole live authority for specification state, dependencies, queue order and implementation authorization. Nothing in this register authorizes implementation, deletion, dependency adoption, migration or queue changes.

The pre-reconciliation long-form register, including the detailed reusable-pattern prose for the earlier entries, is preserved byte-for-byte at:

- `docs/audits/IDEA_INTAKE_AND_CANDIDATE_INTEGRATIONS_ARCHIVE_2026-08-20.md`

Detailed code-first evidence for newer entries lives in the dated files under `docs/audits/`. This compact register should stay small enough to update safely; do not grow it back into a second architecture document.

## Mandatory intake rule

When a maintainer conversation proposes, links, uploads or discusses something that may materially improve JarvisOS, BLUECAD or BlueRev, the coordinating agent must:

1. read this register before claiming that an idea is new, covered or absent;
2. inspect source deeply enough to separate implementation evidence from README/marketing claims when source access permits;
3. update the closest existing entry rather than creating synonyms;
4. preserve source/provenance, the concrete reusable mechanism, major caveats, license posture and disposition in an audit document when detail is material;
5. keep rejected/superseded entries when they contain useful negative evidence;
6. re-check exact current upstream source, direct license, material transitive licenses and notices before code integration, vendoring or substantial reuse;
7. inspect fork/parent/source metadata before attributing an idea to a GitHub organization;
8. follow promising upstreams, siblings, dependencies, authors and papers when they expose a genuinely new architectural slot or materially stronger candidate;
9. stop open-ended enumeration when new sources only refill already well-covered slots.

## Software reuse policy

Preferred reuse modes:

- `DIRECT_DEPENDENCY`: maintained upstream package/binary/service/API when license and boundary fit.
- `VENDORED_COMPONENT`: permissively licensed component when vendoring materially improves offline operation, patch control or reproducibility; preserve provenance and update path.
- `EXTERNAL_ENGINE`: process/service/solver retained behind a typed adapter when license, deployment or operational isolation favors a process boundary.
- `REFERENCE_ONLY`: inspect concepts/interfaces without incorporating code when licensing, maintenance, security, dependency cost or fit is unsuitable.

Permissive licensing is a reason to compare direct reuse against recreation, not automatic adoption. Reciprocal/source-available/no-license code may still be an architecture reference but requires an explicit legal boundary before any reuse.

## Entry states

- `CAPTURED`: recorded but not deeply audited.
- `AUDITED`: source/docs inspected and useful mechanisms identified.
- `CANDIDATE`: materially worth competing in a later authorized subsystem bake-off.
- `PARKED`: useful but premature or lacking a trigger.
- `REJECTED`: not worth adopting in current form; retain why.
- `PROMOTED`: moved into a governing ADR/spec; that record owns implementation state.
- `SUPERSEDED`: a stronger reference replaced this entry's role.

Evidence labels: `CODE-FIRST`, `DOCS-FIRST`, `CONCEPT`.  
Value grades: `S`, `A`, `B`, `C`, `D`; grade is reference/integration value, not implementation priority.

---

# Current candidate register

| ID | Source / idea family | Area | Evidence | Grade | State | Main reusable value |
| --- | --- | --- | --- | --- | --- | --- |
| REF-000 | Current `AlbertoRacerro/JarvisOS_v1` | whole platform baseline | CODE-FIRST | — | CANDIDATE | incumbent implementation; receives **no sunk-cost privilege** and must compete subsystem-by-subsystem against upstreams |
| REF-001 | PHENOMVALENCE/JARVIS-OS | agent authority / desktop actions | CODE-FIRST | A | CANDIDATE | typed actions, permission/risk metadata, deterministic bypass, effect verification, recoverable deletion and audit patterns |
| REF-002 | Ouru77/ev-assistant | local desktop assistant | DOCS-FIRST | B | PARKED | offline-first voice/browser/screen routing, destructive confirmations, memory and desktop-assistant UX |
| REF-003 | moeru-ai/AIRI | computer use / task state | CODE-FIRST | S | CANDIDATE | perception-snapshot-bound computer use, session operation budgets, task memory separated from long-term memory |
| REF-004 | IRISX-AI/IRIS-Mini | realtime multimodal desktop UI | DOCS-FIRST | B | PARKED | realtime multimodal interaction, polished desktop UI, Socket.io/Windows setup patterns |
| REF-005 | SreejanPersonal/JARVIS-AGI | legacy Jarvis clone | DOCS-FIRST | C | PARKED | historical comparison only; stale relative to stronger references and licensing requires care |
| REF-006 | Wayfinder | routing / evaluation architecture | CODE-FIRST | A | CANDIDATE | deterministic preprocess -> features -> scoring -> recommendation -> explanation, validated config, dry-run JSON, benchmarks, ADRs |
| REF-007 | Cavemem/Caveman family | memory / retrieval | CONCEPT | A | PARKED | local-first write boundary, progressive retrieval, technical-token preservation, gated promotion |
| REF-008 | BlueRev Obsidian vault bridge | knowledge architecture | CONCEPT | A | CANDIDATE | Obsidian source-of-truth, read-only retrieval/index, bounded context packs, evidence/status classes, gated canonical promotion |
| REF-009 | Solnest coding agent | autonomous coding gates | CODE-FIRST | B | CANDIDATE | post-edit deterministic gates; implementation guardrails are weaker than the concept |
| REF-010 | reverse-skill | capability routing / experience | CODE-FIRST | B+ | CANDIDATE | machine-readable routing authority, local tool inventory, experience journal with controlled promotion |
| REF-011 | HyperClaw | authority / sandboxing | CODE-FIRST | A | CANDIDATE | monotonically restrictive authority, per-agent credentials, workspace/network/resource isolation |
| REF-012 | nexu-io/open-design | BLUECAD artifacts / agent runtimes | CODE-FIRST | S | CANDIDATE | refreshable Live Artifacts with provenance/snapshots and declarative agent-runtime adapters |
| REF-013 | isdvsv/bug-hunter | autonomous coding runtime | CODE-FIRST | A | CANDIDATE | canonical run state, single-writer lock, baseline, dry-run, resume, chunk/hash cache, payload validation, canary-first changes |
| REF-014 | avivl/claude-007-agents | multi-agent orchestration | CODE-FIRST | D | REJECTED | negative reference: advertised-real components included simulated MCP/tasks/mock/random analysis |
| REF-015 | mrveiss/AutoBot-AI | approvals / workflow orchestration | CODE-FIRST | A+ | CANDIDATE | persistent approval lifecycle, revision/resubmit, workflow dependency semantics, bounded remembered approvals |
| REF-016 | Jacobdrosol/NexusAI | distributed workers / authority | CODE-FIRST | A+ | CANDIDATE | worker readiness/attestation, typed least-privilege blueprints, credential refs, payload-bound one-shot approvals, scheduler |
| REF-017 | Solnest-AI/echo-agent | untrusted-content boundary | CODE-FIRST | A | CANDIDATE | deterministic lanes, sealed no-tool reasoning, strict structured output, ID whitelist, fail-soft fallback |
| REF-018 | grabbly/lanehub | multi-agent identity | CODE-FIRST | B+ | CANDIDATE | stable authenticated actor identities, per-agent credentials/endpoints, provenance-preserving merged feed |
| REF-019 | Lessan / linux-autonomos-agent | learning / tool effectiveness | CODE-FIRST | B- | PARKED | empirical tool effectiveness and prior-task retrieval; needs contextual metrics and no authority promotion |
| REF-020 | ZYRAXON browser family | browser/computer use | CODE-FIRST | C | SUPERSEDED | isolated observations only; AIRI/Hermes/Nexus references are stronger |
| REF-021 | zyraxon-code | coding editor | CODE-FIRST | D | REJECTED | insufficient unique value over studying actual upstream editor/agent projects |
| REF-022 | NousResearch/Hermes Agent | conversation/agent runtime, sessions, profiles, memory, delegation and tool orchestration | CODE-FIRST | S | PROMOTED | selected replaceable runtime direction under `docs/DECISIONS.md`: pin/direct-depend on upstream behind a Jarvis adapter/process boundary; reuse sessions, profiles, memory/search and bounded delegation while JarvisOS retains canonical state, credentials, egress/budget, engineering acceptance and promotion authority |
| REF-023 | Rizzo-AI-Academy/rizzo-pii current v2 family | privacy / egress preprocessing | CODE-FIRST | A+ | CANDIDATE | neural PII detection plus deterministic validators/checksums, reversible local pseudonymization, local restore; place privacy boundary before cloud egress |
| REF-024 | Seeker.Bot | evidence / capability dependencies | CODE-FIRST | A | CANDIDATE | claim-level evidence arbitration, verification depth, domain-sensitive confidence decay, capability dependency graph |
| REF-025 | ZYRAXON-AI | dynamic capability installation / memory | CODE-FIRST | B- | PARKED | typed capability-install concept and simple memory ranking; broad self-evolve authority is unsuitable |
| REF-026 | solnest-jarvis | latency lane / background jobs | CODE-FIRST | A- | CANDIDATE | fast native-tool lane, read-only background specialists, job epochs, concurrency cap, orphan reaping, stale-result suppression |
| REF-027 | MAYA-AIt | prompt-routed multi-agent graph | CODE-FIRST | C | REJECTED | mostly single-turn prompt specialists/placeholders; minor valid patterns are covered better elsewhere |
| REF-028 | IRIS-GO | advertised multi-agent system | CODE-FIRST | D | REJECTED | negative reference: advertised Browser/File/OS/Coder/Research agent files are empty and roadmap marks them unfinished |
| REF-029 | arpitrajjj/OnyxBridge + OnyxDashboard | edge-device / fleet telemetry | CODE-FIRST | A- | CANDIDATE | persistent identity, idempotent registration, heartbeat, offline queue/backoff, SSE dashboard + polling fallback |
| REF-030 | arpitrajjj/Mishri | utility behavior selection | CODE-FIRST | C+ | PARKED | utility-scored low-stakes behavior selection with anti-repeat/pacing |
| REF-031 | arpitrajjj/rich-editor-bot + rippercasted | messaging UX / C++ scaffold | CODE-FIRST | C | PARKED | rich messaging/mini-app UX and clean CMake scaffold; little unique core architecture value |
| REF-032 | NousResearch/hermes-toolperf-evals + hermes-compression-eval | runtime improvement / context survival | CODE-FIRST | S | CANDIDATE | mine real tool failures/waste; baseline-vs-fix evaluation; grade compression by ability to resume exact work |
| REF-033 | NousResearch/autoreason + hermes-agent-self-evolution | refinement / controlled self-improvement | CODE-FIRST | A | CANDIDATE | explicit incumbent, blinded challenger comparison, offline candidate evolution with deterministic promotion gates |
| REF-034 | NousResearch/Nomos + Atropos/tinker-atropos | adaptive reasoning / specialist training environments | CODE-FIRST | A- | PARKED | allocate compute to under-verified tasks; separate environment/reward truth from replaceable trainer/inference backend |
| REF-035 | NousResearch/neural-steering + smc-inference-server + DisTrO | model steering / inference-time search / distributed training | CODE-FIRST | B | PARKED | local-model steering/search/distributed-training research; never substitutes for authority policy |
| REF-036 | microsoft/agent-governance-toolkit | agent policy / governance / trust | CODE-FIRST | S | CANDIDATE | schema-versioned policy, fail-closed evaluation, additive-only inheritance, context-aware enforcement |
| REF-037 | NVIDIA/OpenShell + NVIDIA/NemoClaw | sandboxed autonomous execution | CODE-FIRST | S | CANDIDATE | real filesystem/network/process sandbox, seccomp/Landlock, provider routing and agent packaging |
| REF-038 | CoolProp + ChEDL thermo/chemicals/fluids/ht + ThermoSTEAM | thermodynamics / chemical properties | CODE-FIRST | S | CANDIDATE | mature property/flash/transport/hydraulics/heat-transfer stack behind typed backend adapters |
| REF-039 | BioSTEAM + Bioindustrial-Park + QSDsan | process simulation / TEA / bio-domain models | CODE-FIRST | S | CANDIDATE | sequential-modular process engine, TEA/UQ and dynamic bio/wastewater models |
| REF-040 | IDAES + Pyomo + WaterTAP | equation-oriented process modeling / optimization | CODE-FIRST | S | CANDIDATE | flowsheet/state/property-package contracts, dynamics and optimization; strong Aspen-like backend family |
| REF-041 | DWSIM + DTL + CAPE-OPEN | Aspen-like simulation / interoperability | CODE-FIRST | S | CANDIDATE | DWSIM as external engine, DTL as possible linked property backend, CAPE-OPEN as first-class interoperability target |
| REF-042 | FMI/FMPy + OpenModelica/OMSimulator + do-mpc + open62541 | digital twins / co-simulation / control / telemetry | CODE-FIRST | S | CANDIDATE | FMU execution, Modelica engines, MHE/MPC and OPC UA while keeping model/telemetry/controller objects separate |
| REF-043 | Cantera + TESPy + pycalphad + Reaktoro | specialized engineering solvers | CODE-FIRST | A+ | CANDIDATE | reaction/kinetics, thermal-network, materials-phase and reactive-chemistry backends |
| REF-044 | LEAP71 PicoGK + ShapeKernel + LatticeLibrary + HelixHeatX | computational geometry / CEM | CODE-FIRST | S | CANDIDATE | implicit/voxel geometry and semantic engineering shape libraries for generative/additive BLUECAD |
| REF-045 | CadQuery + OCCT | precise B-Rep CAD / assemblies | CODE-FIRST | S | CANDIDATE | parametric B-Rep, named assemblies, constraints, metadata and STEP; complement PicoGK |
| REF-046 | Gmsh + Netgen + OpenFOAM + SU2 + FEniCSx + CalculiX/Code_Aster + `isoAdvector/dictator` | mesh / CFD / FEM backends | CODE-FIRST | A+ | CANDIDATE | solver/mesher portfolio behind explicit external/linked boundaries; BLUECAD owns semantic IR and verified ingestion; `dictator` is a narrow deterministic OpenFOAM dictionary/config helper, not modeling authority |
| REF-047 | OpenMDAO + CasADi + SUNDIALS + PETSc | coupling / optimization / scalable numerics | CODE-FIRST | A+ | CANDIDATE | multidisciplinary coupling, optimal control/AD, ODE/DAE and scalable nonlinear infrastructure behind canonical IR |
| REF-048 | VTK + PyVista + ParaView + meshio | mesh/field results / scientific visualization | CODE-FIRST | S | CANDIDATE | scientific result/field representation, filters, interchange and independent inspection |
| REF-049 | Codex + Claude Agent SDK/Code + Kimi Code + AgentScope + Microsoft Agent Framework + Pydantic AI + Cline + Pi + OpenCode + Goose + Paperclip/team-agent references | generic AgentRuntime / development-worker comparison | CODE-FIRST | S | CANDIDATE | replaceable agent/session/tool/HITL runtime contract and worker patterns; vendor/team-agent managers remain reference-only when they would duplicate Jarvis development or task authority |
| REF-050 | MCP + ACP + A2A | interoperability protocols | CODE-FIRST | S | CANDIDATE | keep tool/context, client↔agent and agent↔agent protocol roles distinct instead of collapsing them into one bus |
| REF-051 | Serena/Oraios + LSP + Tree-sitter | code intelligence | CODE-FIRST | S | CANDIDATE | semantic/symbol-aware retrieval-editing, syntax intelligence, project/global memory integrity and minimal tool exposure by client context |
| REF-052 | WolframResearch Chatbook + WSTP/LibraryLink/Python/LSP + Wolfram Cloud/MCP family | provider capability / symbolic-compute/runtime bridges | CODE-FIRST | A+ | CANDIDATE | hierarchical model-capability resolution, persona/tool configuration, host↔kernel/language/process interoperability and possible bounded symbolic computation tool access; preserve auth/privacy/budget and Jarvis state authority |
| REF-053 | Letta + Graphiti + Mem0 + Cognee + LangGraph checkpoint family | derived memory / retrieval / checkpoints | CODE-FIRST | A+ | CANDIDATE | derived/temporal memory, replaceable memory backends and checkpoint conformance; canonical evidence must remain separate |
| REF-054 | VS Code extension host + Extism/Wasmtime/WASI + Tauri capability ACL | plugins / frontend IPC / isolation | CODE-FIRST | S | CANDIDATE | extension-process isolation, capability-scoped native IPC and sandboxable plugin execution |
| REF-055 | llama.cpp + vLLM + Ollama + Unsloth + ISTA-DASLab GSQ-RCO quantization + DwarfStar + LocalAI | local model runtime / control plane | CODE-FIRST | S | CANDIDATE | replaceable inference engines and hardware-aware qualification; benchmark Unsloth vs ISTA Qwen3.8-27B GGUF on Jarvis tool/reasoning workloads before choosing the local default |
| REF-056 | OpenTelemetry GenAI + Harbor/Verifiers + ToolSandbox + ADK/LangGraph conformance + DwarfStar qualification | observability / evaluation / conformance | CODE-FIRST | S | CANDIDATE | exact-run telemetry, stateful tool evaluation, conformance suites and backend/model/hardware qualification matrices |
| REF-057 | AllenAI SERA + Unsloth + Axolotl/TRL/PEFT/DataTrove + Agent Lightning + small-specialist-model product patterns | training / specialization | CODE-FIRST | A+ | PARKED | specialist-data/training pipelines with runtime/training disaggregation; recent small-model lessons reinforce evaluator-first specialization; promote only after task-specific evaluators exist |
| REF-058 | AIOS + ESAA/event-sourced agent architecture | authority/event architecture research | CONCEPT | S | CANDIDATE | small authoritative kernel, shared services/resources and deterministic event commit layer; model proposal is not canonical mutation |
| REF-059 | Progent + tracked capabilities/info-flow + AuthBench + instruction-hierarchy/tool-safety research | least privilege / information flow | CONCEPT | S | CANDIDATE | separate capability authority, egress authority and state-commit authority; do not let an LLM self-grant least privilege |
| REF-060 | NanoClaw | sandbox / credential / egress / worker lifecycle | CODE-FIRST | S | CANDIDATE | explicit mounts, non-root sessions, credential-less containers, optional forced proxy, fail-closed spawn and surviving-session adoption |
| REF-061 | antirez / Salvatore Sanfilippo editing and QA patterns | stale-write prevention / diff-aware QA | CODE-FIRST | A+ | CANDIDATE | compare-and-set/version identity for edits plus adversarial exact-diff review layered above deterministic tests |
| REF-062 | RizzoClaw | simple agent memory negative reference | CODE-FIRST | C | PARKED | useful negative evidence: Markdown project memory can leak sensitive context/provenance concerns; keep memory classes/sensitivity explicit |
| REF-063 | Bioo + Heirloom + AIR COMPANY + Linear + Raycast + Recursion + Vercel + Instrument typography + Phosphor Icons | visual identity / frontend design system | DOCS-FIRST | A+ | PROMOTED | maintainer-selected living-engineering visual direction; open Instrument/Plex typography candidates, Phosphor generic icons, bounded accent theming and reference-only external brand cues; promoted into the 100 design-authority pack |
| REF-064 | `AlbertoRacerro/jarvis-pr-attention` V1.11 PR #16 @ `c544e2885a69173c58feb2355bb53e8866e627eb` | PR evidence / review attention | CODE-FIRST | A | CANDIDATE | exact-head read-only evidence cycle with compact continuity/findings and fail-closed stale/tampered evidence; JarvisOS may consume it only as advisory/stateless evidence after 128, never as semantic acceptance, approval/comment, merge, queue, persistence or source-of-truth authority |
| REF-065 | `baidu/Unlimited-OCR` | document OCR / technical ingestion | DOCS-FIRST | A | CANDIDATE | long-document/PDF extraction candidate before Literature/Project Knowledge ingestion; preserve original page/file provenance and benchmark hardware fit/quality before promotion |
| REF-066 | `trybacked/anchor` | semantic model / provenance / MCP query | CODE-FIRST | A+ | CANDIDATE | entity/relation/definition modeling, provenance/confidence and human review patterns; use as derived/interchange/read projection rather than a second canonical Project Knowledge store |
| REF-067 | Meeting/brainstorm audio capture + PLAUD-like import adapters | speech / decision capture | CONCEPT | A | CANDIDATE | immutable raw audio/transcript provenance followed by proposed summaries/decisions/actions and explicit promotion into Brainstorm/Roadmap/Project Knowledge/Coding; vendor-independent core, no always-on recording by default |
| REF-068 | Clicky / `heyclicky.com` AI-buddy reference | desktop companion UX | DOCS-FIRST | B | PARKED | persistent assistant presence, lightweight summon/interruption, ambient status and conversational continuity; UX reference only, reusing Jarvis sidecar/Hermes sessions rather than new authority/state |
| REF-069 | TimesFM 3 family | time-series forecasting | DOCS-FIRST | A | CANDIDATE | specialist forecasting backend for telemetry/process/environmental series; verify official release/license/features and benchmark against simpler baselines; forecasts remain uncertainty-bearing derived evidence |
| REF-070 | GenCFD / diffusion-generative CFD research family | CFD surrogate / generative field prediction | CONCEPT | A | PARKED | future acceleration/surrogate research after deterministic CFD baselines and evaluators exist; verify code/data/license/hardware before any engineering-evidence role |
| REF-071 | WeatherNext 3 family | environmental/weather forecasting | DOCS-FIRST | A | PARKED | candidate external forecast source/backend for outdoor PBR/digital-twin scenarios; require official access/license validation plus typed provenance/uncertainty |
| REF-072 | Annota AI | OCR / knowledge / annotation / training workflow | DOCS-FIRST | B+ | CANDIDATE | commercial/product reference for OCR-to-knowledge, annotation-to-dataset and MCP workflows; compare against existing Literature/Project Knowledge pipeline and avoid duplicate canonical storage |
| REF-073 | CppJIT family | bounded native/JIT engineering acceleration | CONCEPT | B | PARKED | possible acceleration of engineering kernels; compare with existing extension approaches and require deterministic toolchain/cache identity, sandboxing and failure isolation; never expose unrestricted model-authored native execution |
| REF-074 | Design -> Coding promotion bridge | engineering-to-development workflow | CONCEPT | A+ | CANDIDATE | explicit `Send request to Coding` path carrying exact context/provenance, target subsystem and acceptance criteria into existing Coding/Development proposal authority; no direct source mutation/merge |
| REF-075 | Provider prompt caching + included/free compute pool | provider economics / routing | CONCEPT | A | CANDIDATE | exploit provider caching and legitimate subscription/free quotas behind Jarvis policy/accounting; classify local/included/free/paid routes and never silently cross into PAYG |
| REF-076 | Persistent Hermes VPS/container/serverless + sovereign/private provider options (DigitalOcean/Z.ai-type) | deployment / availability / sovereignty | CONCEPT | A | PARKED | make Jarvis availability independent of the maintainer laptop while preserving Jarvis authority, secrets/network isolation, backup/restore, pinned upgrades and cost caps; strategic provider programmes are optional topology choices, not product authority |
| REF-077 | IChemE PESD + curated engineering-source families | literature / research-source intake | DOCS-FIRST | B+ | CANDIDATE | high-quality process-engineering source families for Literature/research ingestion with provenance/access/licensing preserved and no automatic engineering acceptance |
| REF-078 | Frozen Jarvis core team + Hermes Profiles/BoardSession direction | multi-agent council / persona orchestration | CONCEPT | S | CANDIDATE | map the existing 11-persona roster onto persistent Hermes profiles plus bounded disposable delegation; persona remains model-independent, Jarvis chairs/authorizes, user can steer debates, and high-value decisions may add model diversity/frontier escalation |

---

# Current architectural slots for later comparison

The broad audit is considered saturated enough for synthesis. A later strategy must compare `REF-000` against candidates **by slot**, not by repository popularity:

1. Authority/Event Kernel
2. AgentRuntime
3. Tool/Capability Gateway
4. Execution/Sandbox
5. Model Runtime/Provider
6. Code Intelligence
7. Canonical Memory/Evidence
8. Derived Memory/Index
9. Egress/Privacy
10. Observability/Evaluation
11. Training/Specialization
12. Desktop/Frontend IPC
13. Document/Media Ingestion
14. External Data/Forecasting
15. Engineering Solver/Interoperability

The recurring invariant is:

`agent/model proposal != canonical state mutation`

and the three authorities must remain independently enforceable:

`capability authority != information-flow/egress authority != state-commit authority`.

## Required implementation sequence

This register does **not** alter the active queue. The current maintainer direction is preserved here so later audits do not regress to the stale pre-117 sequence; normal spec/readiness promotion remains mandatory.

1. close `122 JARVIS-DEVELOPMENT-ACTIONS-1` and the bounded GitHub Education/Copilot Student + Google AI Pro/Jules development-pipeline expansion;
2. qualify the local Qwen3.8-27B candidates (Unsloth vs ISTA-DASLab GSQ-RCO) on Jarvis-relevant tool/reasoning/hardware evidence;
3. integrate the pinned Hermes product sidecar with persistent sessions, native memory/session retrieval, profiles and user-steerable named-agent council mechanics while Jarvis remains authority;
4. make llama.cpp/local inference first-class and add the Jarvis agent-inference/provider boundary required for real Hermes tool loops;
5. add cloud/frontier escalation only behind secure credentials, Jarvis egress/budget/accounting, Rizzo-style PII handling plus project-IP sanitization and no silent PAYG fallback;
6. begin engineering capability-slot bake-offs across the existing S/A candidate families, with PBR/BlueRev as the first serious vertical target;
7. integrate later ingestion/UX/deployment/specialist candidates when a concrete product or engineering capability needs them;
8. keep self-update, generic PTY, broad computer-use and uncontrolled self-improvement deferred unless a concrete blocker changes the minimum-necessary test.

Detailed rationale and the disposition of the 2026-09-15 candidate wave live in `docs/audits/FUTURE_INTEGRATIONS_SYNTHESIS_2026-09-15.md`.

## Strategic disposition vocabulary

For every future subsystem comparison use exactly one primary disposition:

- `KEEP_JARVIS`
- `REPLACE_WITH_UPSTREAM`
- `WRAP_UPSTREAM`
- `HYBRID`
- `DELETE`
- `PARK`

Each disposition must cite current Jarvis code, candidate evidence, exact contract/ownership boundary, migration path, deterministic acceptance tests, licensing/provenance, rollback and dependencies.

---

# Detailed audit index

Core software/runtime:

- `docs/audits/CORE_SOFTWARE_ECOSYSTEM_AUDIT_2026-08-20.md`
- `docs/audits/CORE_SOFTWARE_ECOSYSTEM_AUDIT_CONTINUATION_2026-08-20.md`
- `docs/audits/CORE_SOFTWARE_ECOSYSTEM_AUDIT_CONTINUATION_2_2026-08-20.md`
- `docs/audits/CORE_SOFTWARE_ECOSYSTEM_AUDIT_CONTINUATION_3_2026-08-20.md`
- `docs/audits/CORE_SOFTWARE_ECOSYSTEM_AUDIT_CONTINUATION_4_2026-08-20.md`
- `docs/audits/CORE_SOFTWARE_ECOSYSTEM_AUDIT_CONTINUATION_5_2026-08-20.md`
- `docs/audits/CORE_SOFTWARE_ECOSYSTEM_AUDIT_CONTINUATION_6_2026-08-20.md`
- `docs/audits/CORE_SOFTWARE_ECOSYSTEM_AUDIT_CONTINUATION_7_2026-08-20.md`
- `docs/audits/JARVIS_PR_ATTENTION_V1_11_AUDIT_2026-08-30.md`
- `docs/audits/FUTURE_INTEGRATIONS_SYNTHESIS_2026-09-15.md`

Architecture/safety research:

- `docs/audits/AGENT_ARCHITECTURE_RESEARCH_AUDIT_2026-08-20.md`
- `docs/audits/AGENT_ARCHITECTURE_RESEARCH_AUDIT_CONTINUATION_2026-08-20.md`

Engineering ecosystem:

- `docs/audits/ENGINEERING_SOFTWARE_ECOSYSTEM_AUDIT_2026-08-19.md`
- `docs/audits/ENGINEERING_SOFTWARE_ECOSYSTEM_AUDIT_CONTINUATION_2026-08-19.md`
- `docs/audits/ENGINEERING_SOFTWARE_ECOSYSTEM_AUDIT_CONTINUATION_2_2026-08-19.md`

Nous/upstream provenance:

- `docs/audits/NOUS_FORK_UPSTREAM_EXPANSION_2026-08-19.md`
- `docs/audits/NOUS_RESEARCH_REPO_AUDIT_2026-08-19.md`
- `docs/audits/UPSTREAM_AUTHOR_ECOSYSTEM_AUDIT_2026-08-19.md`
- `docs/audits/UPSTREAM_AUTHOR_ECOSYSTEM_AUDIT_CONTINUATION_2026-08-19.md`
- `docs/audits/UPSTREAM_AUTHOR_ECOSYSTEM_AUDIT_CONTINUATION_2_2026-08-19.md`
- `docs/audits/UPSTREAM_AUTHOR_ECOSYSTEM_AUDIT_CONTINUATION_3_2026-08-19.md`

Visual identity / frontend design:

- `docs/audits/VISUAL_IDENTITY_REFERENCE_AUDIT_2026-08-25.md`
- `docs/design/visual-identity-100/README.md`

Legacy detailed register prose:

- `docs/audits/IDEA_INTAKE_AND_CANDIDATE_INTEGRATIONS_ARCHIVE_2026-08-20.md`

---

# Promotion rule

When a candidate becomes relevant to current product work:

1. revalidate exact upstream version/commit and current Jarvis implementation;
2. classify reuse mode and verify direct/transitive license compatibility plus required notices;
3. state the exact problem and why upstream reuse, wrapping, hybridization or deletion wins against the incumbent;
4. run the minimum security/performance/platform prototype needed to resolve uncertainty;
5. define canonical owner, input/output contracts, failure semantics and rollback;
6. define deterministic acceptance/conformance tests before migration;
7. create/update the governing ADR/spec through the normal repository process;
8. change the register entry to `PROMOTED` and link that authority;
9. keep live implementation status exclusively in `docs/specs/STATUS.md`.

# Maintenance rule

Keep this file as a compact index. Put detailed findings in dated audit documents and link them here. Preserve negative findings and provenance. Do not create a new REF when an existing family can be updated safely. Open-ended ecosystem enumeration is complete unless a later exact comparison exposes a genuinely missing slot or a materially stronger candidate.