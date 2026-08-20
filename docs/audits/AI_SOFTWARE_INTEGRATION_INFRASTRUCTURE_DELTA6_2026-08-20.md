# AI SOFTWARE INTEGRATION INFRASTRUCTURE DELTA6 — 2026-08-20
MODE=DISCOVERY;FORMAT=AI_FIRST_TOKEN_DENSE;AUTHORITY=AUDIT_ONLY;IMPLEMENTATION_AUTHORIZED=NO;BRANCH=audit/hermes-agent-2026-08-20

## DIRECTIVE
PIVOT=P0_AI_SOFTWARE_INTEGRATION;DEFER={corrosion,materials,broad_mechanics};GOAL=fast/correct integration of heterogeneous engineering repos into one Jarvis/BLUECAD UX. RULES={SUNK_COST_ZERO,PIPPO_OS_TEST,REPLACE_NOT_LAYER,CODE_FIRST,STANDARD_BOUNDARIES,AUTHORITY_SEPARATION,NO_MEGA_VENV}.

## TARGET LAYERING
UI <-> AG_UI_candidate <-> JARVIS_AUTHORITY <-> ONE_PRIMARY_AGENT_RUNTIME <-> MCP <-> ISOLATED_ENGINEERING_ADAPTERS <-> SOLVERS.
REMOTE_AGENT=Jarvis<->A2A<->independent specialist/vendor agent.
SIM_COMPONENT=FMI/FMU where applicable.
TOOL_UI=MCP Apps ui:// where applicable.
PORTABLE_PROCEDURE=Agent Skills SKILL.md;SECURITY_AUTHORITY=separate deterministic Jarvis capability policy.
TRACE=OpenTelemetry-compatible canonical trace spine.

## WOLFRAM
repo=WolframResearch/AgentTools;license=MIT;STATUS=DIRECT_TOOLKIT;ENGINE_LICENSE=COMMERCIAL_BOUNDARY.
CODE_EVIDENCE: repo contains AgentSkills,Dockerfile,Kernel,FrontEnd,Documentation,Tests,.claude-plugin; Tests include CreateMCPServer,InstallMCPServer,EvaluatorSessions,CodeInspectorTool,MCPApps etc; not README-only.
CAPS={MCP server creation/install,skills,Wolfram computation,WolframAlpha,notebook IO,code inspection,test reports,MCP Apps,Docker,project roots}.
PIPPO=ADOPT_BOUNDARY_PATTERN;do_not_use_as_primary_orchestrator.
WOLFRAM_ENGINE caveat=not OSS; free engine non-production; production/commercial licensing required. AgentTools MIT != Engine rights.
TARGET_ROLE={symbolic math,exact algebra,unit/math oracle,ODE/PDE manipulation,formula verification,computable knowledge,notebook/report tool};all through MCP/isolated boundary; graceful fallback mandatory.
Agent One API=vendor computational-agent service; OpenAI-compatible chat endpoint; audit later as optional oracle, not canonical runtime.
SOURCES={github:WolframResearch/AgentTools/LICENSE,Tests; wolfram AgentTools docs; Wolfram Engine licensing docs}.

## MCP
STATUS=S_CANONICAL_TOOL_BOUNDARY_CANDIDATE.
Official SDK tier1={Python,TypeScript,CSharp,Go};tier2={Java};multi-language makes heterogeneous adapters feasible.
Adapter server SHOULD expose={tools,resources,prompts,health,version,license,capabilities,structured outputs,optional ui};Jarvis owns approval/policy.
SECURITY: MCP server=UNTRUSTED. Must gate={filesystem,network,secrets,side effects,sampling/server-initiated model calls};schema validate; sandbox; provenance/version/hash/license record; default deny server sampling unless explicit bounded approval.
WHY=avoid importing every repo dependency into Jarvis backend; adapters can run distinct Python/native/MATLAB/Wolfram stacks.

## MCP_APPS
STATUS=S_UX_COST_REDUCTION_CANDIDATE;extension=io.modelcontextprotocol/ui;stable 2026.
Pattern=tool returns ui:// interactive resource; sandboxed iframe + bidirectional JSON-RPC + capability negotiation.
PIPPO=ADOPT_HOST_SUPPORT_IF_SECURITY_TESTS_PASS.
Potential widgets={CoolProp property explorer,Kratos loads/results,PBR parameter/plot panel,Wolfram derivation,pyLife fatigue panel,FMU parameter/simulation panel}.
Invariant=widget state != canonical engineering state until Jarvis validation/promotion; no secret inheritance; strict origin/CSP/capability scope.

## AG_UI
STATUS=S_CANDIDATE_AGENT_FRONTEND_PROTOCOL;open event protocol for streaming,state sync,tool lifecycle,generative UI,HITL,bidirectional interaction.
Target role=Jarvis runtime<->BLUECAD frontend; reduces custom streaming/state plumbing.
PIPPO=SPIKE;verify exact LICENSE/SDK maturity/security/client compatibility before adoption.
Do not make framework-specific tracing/session protocol canonical if AG-UI can decouple frontend.

## A2A
STATUS=A_PLUS_EXTERNAL_AGENT_BOUNDARY;Apache2/Linux Foundation ecosystem;multi-language SDK/TCK/Agent Cards/streaming/push.
USE=independent remote specialist agents/vendors/org services.
DO_NOT_USE=every internal Jarvis subagent; internal delegation should stay cheaper/in-process unless isolation/federation needed.
DISTINCTION=MCP agent-to-tool;A2A independent agent-to-agent.

## AGENT_SKILLS
Anthropic-origin open portable standard; OpenAI/Wolfram support; SKILL.md + optional scripts/references/assets.
PIPPO=ADOPT_FORMAT;Jarvis-specific risk/capability/secret/egress/license/validation metadata remains deterministic sidecar/registry, not prose-only SKILL.md.
Separation={Skill=procedural knowledge;CapabilityPolicy=authority;Tool=MCP/function/adapter}.

## PRIMARY_RUNTIME_CANDIDATES
### Hermes
existing audit verdict=best coding/terminal-agent muscle found earlier: tool registry/discovery,ToolSearch,skills,subagents,procedural memory,terminal/browser patterns. Weakness vs Jarvis=authority/governance; safety/approval coverage issues previously found. STATUS=S incumbent_candidate,NOT winner by sunk cost.

### Microsoft Agent Framework (MAF)
repo=microsoft/agent-framework;license=MIT;direct successor to AutoGen+SemanticKernel;STATUS=S_ADOPT_CANDIDATE.
Code evidence `_mcp.py` contains: MCPSpecificApproval(always/never), progressive `list_mcp_tools/load_tool/unload_tool`, framework denylist preventing runtime-object leakage to MCP, metadata validation, OTel propagation, default-deny server sampling without approval callback, sampling max_tokens=4096,max_requests=25/session,long-running MCP task polling/reconnect; test_mcp exists.
2026 changelog/features={progressive MCP disclosure,skills,A2A,AG-UI,local+Docker shell tools,OTel,background/long-running agents,workflow/HITL}.
PIPPO=serious Hermes competitor; must test provider neutrality,dependency graph,coding depth,memory,durable runtime,churn.

### PydanticAI
repo=pydantic/pydantic-ai;license=MIT;classifier=Production/Stable;STATUS=S_TYPED_SERVICE_RUNTIME_CANDIDATE.
pyproject shows provider extras OpenAI/Anthropic/Google/MCP/evals/web/Logfire + DBOS/Prefect/Temporal + mcp-tasks/realtime/UI; tests toolsets/tools.
Strength={typed schemas,provider neutrality,toolset composition,MCP,HITL,durable integrations,fit with Pydantic-heavy Jarvis engineering contracts}.
Risk=may be less deep as autonomous coding/terminal agent than Hermes/MAF; avoid layering duplicate framework if one primary can cover both.

### OpenAI Agents SDK
repo=openai/openai-agents-python;license=MIT;v0.22.0 at audit;STATUS=A_PLUS/S_CANDIDATE.
Core deps small-ish={openai,pydantic,mcp,requests,websockets}; optional sandbox/providers={Docker,E2B,Daytona,Modal,Runloop,Cloudflare,Blaxel}; sessions,tracing,handoffs,guardrails,realtime,Temporal optional.
Strength=minimal primitives,OpenAI-native,sandbox-agent integrations; risk=provider/runtime dependence vs neutral core. Compare, do not assume winner.

### LangGraph
MIT;Production/Stable;stateful graph+checkpoint/durable HITL; mature SQLite/Postgres/Redis test surface. STATUS=REFERENCE/CANDIDATE only; likely redundant if chosen runtime + DBOS/Temporal cover state/durability; LangChain dependency cost.

### Google ADK
Apache;typed but core/all dependency graph is Google/cloud-heavy and can include LangGraph/MCP/A2A/sandbox/data stacks. STATUS=REFERENCE; not preferred neutral core unless Google stack becomes dominant.

### SemanticKernel/AutoGen
LEGACY_PRIMARY_CANDIDATES=NO; Microsoft Agent Framework is direct successor. Keep only migration/pattern references.

## DURABILITY
Temporal=MIT service+SDK; strong distributed durable workflows,deterministic replay,sandbox; S future production/high-duration engineering jobs; operationally heavier.
DBOS=MIT/Postgres-backed Python durable decorators/queues/sleep/recovery; A+/S initial candidate due low ops cost; PydanticAI support.
Restate=candidate; exact server license/ops audit pending.
RULE=agent framework must not be sole owner of canonical long-running workflow state if durable execution layer can make it replaceable.

## OBSERVABILITY
OpenTelemetry=canonical interoperability target. GenAI semantic conventions developing; use stable generic spans + namespaced attrs where needed.
Trace lineage=request->agent_run->tool_call->adapter->solver_run->artifact/result->proposal/promotion.
Framework-specific observability={OpenAI tracing,Logfire,LangSmith,Azure} may be exporters/sinks, not canonical truth.

## ENVIRONMENT/BUILD
NO_MEGA_VENV.
uv=A+/S default Python adapter env/package candidate; fast,lockfile,Python management,workspaces,cross-platform.
Pixi=A+/S native/mixed scientific env candidate; Conda ecosystem,multi-language,C/C++/Fortran/R/Python,lockfile.
DevContainer=A+ reproducible adapter/build contract candidate.
E2B=Apache cloud/self-host sandbox candidate for builder/code execution.
Daytona=open-core status degraded 2026/public core private+AGPL history => hosted adapter only if compelling; NOT foundation.
Dagger=Apache candidate for reproducible cached typed build/test/package pipelines; deeper audit P0.
Proposed AdapterBuildSpec={manifest,source_ref,license,environment:{uv|pixi|container},lockfile,build,test,health,entrypoint,protocol:{MCP|FMI|HTTP|process},capabilities,security,version/hash,optional MCPApp}.

## UX/INTEGRATION TARGET
Adding a solver should approximate:
1 source audit+license;2 create isolated reproducible env;3 generate adapter manifest/schema;4 expose MCP tools/resources;5 health+validation regression;6 optional MCP App;7 register capabilities;8 Jarvis authority;9 OTel trace;10 user sees one coherent tool/UI.
Success metric=integration cost grows ~adapter complexity,not global dependency graph.

## PRIMARY NEXT AUDIT
P0 deep code-first matrix Hermes vs MAF vs PydanticAI vs OpenAI Agents: {tool registry,progressive disclosure,MCP,sandbox,coding/terminal,skills,subagents,memory/session,durable workflows,approvals,provider neutrality,OTel,typing,tests,deps,churn,embed-under-Jarvis,replaceability}.
P0 MCP Apps + AG-UI source/license/security/maturity.
P0 Dagger + uv/Pixi/DevContainer as AdapterBuildSpec/build engine.
P1 coding-agent competitors={OpenHands,SWE-agent,Codex CLI,Gemini CLI,Goose,ACP/OpenCode} for patterns better than Hermes.
P1 Wolfram AgentTools deeper server/tool contract + Agent One optional oracle.

## DECISION_INVARIANTS
ONE primary agent runtime unless hard evidence for split; Jarvis deterministic authority remains outside runtime unless competitor demonstrably replaces it and passes Pippo test; protocol standards preferred over framework-specific coupling; no solver dependency in core unless lightweight/stable/unique; adapter sandbox+license+validation mandatory; UI plugin cannot write canonical engineering state directly.
