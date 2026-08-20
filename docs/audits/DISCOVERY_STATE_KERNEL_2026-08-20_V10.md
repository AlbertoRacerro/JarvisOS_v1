# DISCOVERY STATE KERNEL V10 — 2026-08-20
PURPOSE=AI_REHYDRATION;FORMAT=TOKEN_DENSE;AUTHORITY=AUDIT_ONLY;IMPLEMENTATION_AUTHORIZED=NO;SUPERSEDES_FOR_REHYDRATION=V9;BRANCH=audit/hermes-agent-2026-08-20
RULES=SUNK_COST_ZERO|PIPPO_OS_TEST|REPLACE_NOT_LAYER|CODE_FIRST|AUTHORITY_SEPARATION|BACKEND_OVER_REWRITE|STANDARD_BOUNDARIES|DISCOVERY_WIDE_IMPLEMENTATION_NARROW|SERENDIPITY|NO_MEGA_VENV|AUDIT_BRANCH_ONLY.
LICENSE={DIRECT permissive;BOUNDARY adapter/LGPL/commercial/nonmodified;EXTERNAL GPL/AGPL/process;CLEAN_ROOM equations/idea/no-code;RESEARCH_ONLY NC;GAP none}.

P0_PIVOT=AI_SOFTWARE_INTEGRATION_INFRASTRUCTURE;DEFER={corrosion,materials,broad_mechanics}. GOAL=integrate heterogeneous engineering repos correctly/quickly into coherent BLUECAD/Jarvis UX.

TARGET=BLUECAD_UI<->AG_UI_candidate<->JARVIS_AUTHORITY<->ONE_PRIMARY_AGENT_RUNTIME<->MCP<->ISOLATED_ADAPTERS<->SOLVERS.
EXTERNAL_AGENT=A2A;SIM_COMPONENT=FMI/FMU;TOOL_UI=MCP_Apps;PROCEDURE=AgentSkills/SKILL.md;TRACE=OpenTelemetry.
JARVIS_AUTHORITY_OWNS={capability,sensitivity,egress,network,secrets,budget,confirmation,canonical_engineering_state,proposal/promotion,provenance,license,risk};runtime replaceable.

RUNTIME_DECISION=OPEN.
Hermes=S incumbent; strongest prior coding/terminal,tool discovery/ToolSearch,skills,subagents,procedural memory; authority weaker.
MicrosoftAgentFramework=S ADOPT_CANDIDATE; MIT; successor SK+AutoGen; progressive MCP disclosure; allow/approval; default-deny server sampling+limits; OTel; skills;A2A;AG-UI;shell/Docker;workflow/HITL/background. Serious Hermes competitor.
PydanticAI=S typed-service candidate; MIT Production/Stable; provider-neutral,toolsets,MCP,HITL,durable={DBOS,Temporal,Prefect},realtime/UI; strong typed-engineering fit; coding depth TBD.
OpenAIAgents=A+/S;MIT;minimal core;MCP,handoffs,sessions,guardrails,tracing;optional sandboxes={Docker,E2B,Modal,Runloop,etc},Temporal; neutrality/coding depth TBD.
LangGraph=reference/mature graph likely redundant;GoogleADK=reference Google-heavy;SemanticKernel+AutoGen not primary (MAF successor).
RULE=choose ONE primary runtime unless hard evidence forces split.

MCP=S canonical agent-to-tool/resource boundary candidate; official multi-language SDKs. Adapter exposes={tools,resources,prompts,health,version,license,capabilities,structured_output,optional_UI}. MCP_SERVER=UNTRUSTED;Jarvis gates fs/network/secrets/side_effects/sampling.
MCP_APPS=S UX-cost reducer; ui:// sandboxed widgets; solver-specific UI without bespoke frontend; widget state never canonical before Jarvis validation/promotion.
AG_UI=S candidate frontend event protocol={stream,state,tool_lifecycle,HITL,generative_UI}; source/license/security next.
A2A=A+ external independent-agent federation only; not default internal delegation.
AGENT_SKILLS=adopt open SKILL.md; risk/capability/secret/egress/license/validation stays deterministic registry/sidecar.
FMI/FMPy=scientific model component boundary where applicable.

WOLFRAM:WolframResearch/AgentTools=MIT DIRECT+substantial tests; MCP servers,skills,notebook/code inspection,test reports,MCP Apps,Docker. Use computational boundary/toolset,not orchestrator. WolframEngine/WA/AgentOne=COMMERCIAL/SERVICE BOUNDARY; optional exact/symbolic/knowledge oracle+fallback; AgentTools MIT != Engine production rights.

ADAPTER_BUILD_SPEC={source_ref,license,env,lock,build,test,health,entrypoint,protocol,capabilities,security,version_hash,optional_MCPApp}.
ENV:uv=A+/S Python;Pixi=A+/S mixed/native science;DevContainer=A+ reproducibility;Dagger=A+/S build/test/package candidate P0;E2B sandbox candidate;Daytona NOT foundation due 2026 OSS/private transition/vendor dependence.
NO solver dependency in Jarvis core unless lightweight/stable/unique.

DURABLE:DBOS=A+/S low-ops Python/Postgres;Temporal=S distributed long jobs;Restate pending. Runtime must not monopolize durable state.
TRACE:OpenTelemetry canonical request->agent->tool->adapter->solver->artifact->proposal/promotion; framework tracers/exporters optional.

BLUECAD_NUMERICAL=SemanticModelIR->{nativeM0|PyBaMM/CasADi|Modelica/PyMoCa|FMU/FMPy|specialist|external};adapter_protocols={MCP,FMI,native,external_process,typed_HTTP,A2A};Jarvis owns meaning/provenance/validation.

SCIENTIFIC_STATE=PBR+mechanics findings retained in V9/deltas;PC-Gym MIT adopt-candidate;pyHAMS/Kratos/CoSimIO/Chrono/HydroChrono/PyElastica/pyLife/FLife etc parked. CORROSION explicitly DEFERRED by user.

NEXT=P0 deep code-first Hermes vs MAF vs PydanticAI vs OpenAI Agents matrix;P0 MCP Apps+AG-UI source/license/security;P0 Dagger+uv+Pixi+DevContainer AdapterBuildSpec;P1 coding-agent competitors={OpenHands,SWE-agent,CodexCLI,GeminiCLI,Goose,ACP,OpenCode};P1 deeper Wolfram AgentTools/AgentOne;P2 scientific discovery resume after integration architecture stabilizes.

DETAIL=AI_SOFTWARE_INTEGRATION_INFRASTRUCTURE_DELTA6_2026-08-20.md;HERMES_AGENT_CODE_FIRST_AUDIT_2026-08-20.md;DISCOVERY_STATE_KERNEL_2026-08-20_V9.md;MODEL_IR_AND_INTERCHANGE_AUDIT_2026-08-20.md;BLUEREV_CONTROL_AI_DISCOVERY_DELTA5_2026-08-20.md;MECHANICAL_*;PBR_*;SEAWATER_*;../IDEA_INTAKE_AND_CANDIDATE_INTEGRATIONS.md.
REHYDRATION=read V10 first;details only as needed;newer evidence wins;merged governance authority unchanged.