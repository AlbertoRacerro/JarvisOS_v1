# AI AGENT RUNTIME / PROTOCOL / POLICY DELTA7 — 2026-08-20
MODE=DISCOVERY;FORMAT=AI_FIRST_TOKEN_DENSE;AUTHORITY=AUDIT_ONLY;IMPLEMENTATION_AUTHORIZED=NO;BRANCH=audit/hermes-agent-2026-08-20

## DECISION CHANGES
D1=ACP becomes S canonical CANDIDATE for Jarvis Builder<->coding-worker boundary. This reduces need to embed a single coding-agent harness in Jarvis.
D2=Hermes no longer presumed embedded runtime winner; general runtime and coding worker may be separated.
D3=Cedar becomes S candidate to REPLACE substantial handwritten RouterPolicy authorization logic. Jarvis remains authority SERVICE; implementation language/engine not sacred.
D4=Goose becomes S/A+ coding-runtime/worker candidate but NOT authority engine.
D5=AWS Strands becomes S/A+ runtime/reference and exposed Cedar authorization design; IBM BeeAI downgraded due declared maintenance cessation; Cloudflare Agents optional deployment substrate only.

## ACP
repo=agentclientprotocol/agent-client-protocol;license=Apache2;STATUS=S_DIRECT_STANDARD.
V1 protocol is not chat-only: streams session updates including user/agent/thought chunks,tool_call/tool_call_update,plan,mode/config/session metadata,usage+cost. Tool calls classify kind={read,edit,delete,move,search,execute,think,fetch,other}; content includes diffs + live terminal references + affected file locations + raw input/output. `session/request_permission` supports allow_once/allow_always/reject_once/reject_always/cancelled; client MAY auto-decide from settings. Client owns permission UX/policy integration.
Protocol includes filesystem/terminal/client capabilities; supports context-window and cumulative cost reporting. Therefore Jarvis can supervise coding worker without importing its internal API.
SDKs: official Rust/Python/TypeScript/Kotlin ecosystem; Python SDK Apache2 verified. V1 stable; V2 evolving/draft => implement version negotiation/pinning.

## ACP REGISTRY — CURRENT 2026-08-20
repo=agentclientprotocol/registry;Apache2;hourly version update;CI verifies auth handshake. Official generated matrix timestamp 2026-08-20 reports 30 agents,29 initialize successfully. Includes={claude-acp,codex-acp,cursor,devin,gemini,github-copilot,github-copilot-cli,goose,glm-acp-agent,grok-build,junie,kimi,opencode,qwen-code,factory-droid,cline,kilo,etc}. Many support session list/fork/resume.
IMPLICATION=interoperable coding-agent market exists NOW. Jarvis Builder should become ACP client and choose worker by task/cost/provider/availability; no permanent coupling to one coder.
Potential worker policy={Codex,Claude,goose,OpenCode,Qwen/Gemini/local as available}; benchmark on same repo tasks; Jarvis owns checkout/sandbox/spec/budget/approval/CI/promotion.

## CODEX ACP
repo=agentclientprotocol/codex-acp;Apache2;active. Real adapter maps Codex app-server into ACP. Code handles session state,model/reasoning config,auth,MCP startup,terminal output,goals/steering,tool calls,file changes,command execution,MCP calls,subagent activity,token usage/rate limits/failures. This proves ACP can preserve rich worker semantics rather than flatten to text.

## GOOSE
repo=aaif-goose/goose;Apache2;Rust;AAIF/Linux Foundation;desktop+CLI+API;MCP;ACP;providers;subagents;recipes;MCP Apps. Real permission code audited.
Permission modes include AskBefore/SmartApprove/Auto. SmartApprove may use LLM to classify tool request read-only and auto-approve; fallback no-decision=>NeedsApproval; Auto=>all approved; inspectors can override. Therefore goose is NOT Jarvis authority. Use as ACP worker or runtime candidate under deterministic Jarvis/Cedar policy.
PIPPO=worker/runtime candidate; no wholesale trust in built-in permission semantics.

## RUNTIME MATRIX UPDATE
Hermes=S coding-agent/runtime candidate; excellent terminal/toolsearch/skills/subagents but now can be optional if ACP workers cover coding.
MAF=S strongest GENERAL_RUNTIME candidate so far: MIT,Production/Stable small core; progressive MCP disclosure; robust approval replay/substitution protections; Agent Skills implementation; shell approval default+Docker/microVM guidance;AG-UI/A2A/OTel/workflows.
PydanticAI=S typed service/runtime candidate: schema validation-before-execution,tool manager hooks/retries,capabilities/progressive loading,durable integrations. Coding workstation depth less evident.
OpenAI Agents=A+/S: strong sandbox/credential authority model, approvals/tool execution, multiple sandbox backends; primary-runtime neutrality TBD.
Goose=S/A+ worker/runtime; permission semantics require outer authority.
Strands=A+/S runtime/reference; Apache2, Python+TS, model-neutral, hooks,MCP,multi-agent,OTel,execution limits/guardrails. Current repo renamed/merged to `strands-agents/harness-sdk`; code/tests monorepo. Not yet winner.
RULE=do not require primary runtime to be best coder if ACP exists.

## CEDAR — SUNK COST ZERO AUTHORITY PIVOT
Repos={cedar-policy/cedar Apache2; cedar-policy/cedar-for-agents Apache2}. Cedar is authorization-specific principal/action/resource/context language, bounded evaluation, schema validation, automated reasoning/static analysis; unlike general OPA/Rego, designed for authorization and analyzability.
`cedar-for-agents` is real code: mcp-tools-sdk; MCP->Cedar schema generator; Python+WASM bindings; cedar-policy-agent-builder; analysis MCP server.
`cedar-policy-agent-builder` generates policy text,entity hierarchy,schema from declarative config; supports role permits,rate limits,time windows,environment denials,consent gates,input restrictions; validates generated policies against Cedar schema; validates identifiers to prevent policy injection. Tests present.
Strands design shows agent tool authorization chokepoint and maps tool arguments/session metadata into Cedar context; supports static reachability/completeness checks and proposes CI catches new-tool-without-policy. Delegation identity can propagate original user.

### Cedar vs current Jarvis RouterPolicy
PIPPO TEST: if rebuilding PippoOS, prefer mature policy engine over bespoke if equivalent.
Cedar SHOULD own candidate concerns={can principal invoke tool?,arguments/resource scope,environment/time constraints,consent requirement,delegated-user capability scope,tool/category allow/deny,static policy verification}.
Jarvis MUST still own non-Cedar stateful/mechanical concerns={identity establishment/claims verification,credential custody,secret material,budget counters/provider cost accounting,network sandbox implementation,artifact/content provenance,canonical engineering-state promotion,approval UI/session binding,durable audit records}. Cedar evaluates supplied context; it does not establish identity or enforce OS/container boundary.
Migration target=`AuthorityService` with policy backend Cedar + existing Jarvis compatibility adapter; equivalence/regression tests; delete handwritten rules superseded by Cedar. Avoid running both forever.
OPA=Apache2/CNCF/mature/general; keep oracle/alternative if authorization needs become broader policy-as-code. Cedar preferred provisionally because MCP-specific tooling+formal analysis+bounded authorization semantics.

## AWS STRANDS
Current repo resolves to `strands-agents/harness-sdk`; Apache2; Python+TS monorepo; agent loop,providers,tools,MCP,multi-agent,structured outputs,execution limits,observability/hooks/guardrails. `team/designs/0006-cedar-authorization.md` is unusually relevant and code-first adjacent; actual Cedar plugin not found inside core yet, but separate cedar-for-agents implementation exists. Runtime remains comparison candidate, not selected.

## OTHER LAB/PLATFORM FINDINGS
Cloudflare Agents=stateful durable deployment option: Durable Objects identity+SQL+realtime+scheduling/recovery; current MCP 2026-07-28 support; CodeMode. Strong vendor coupling=>DEPLOYMENT_OPTION,not core Jarvis/runtime authority.
IBM BeeAI=Apache/Linux Foundation history but repo explicitly says IBM will not maintain going forward=>REFERENCE/DO_NOT_FOUND_CORE.
OpenTelemetry GenAI semantic conventions now define agent/workflow/tool/MCP concepts but status still Development. Use generic stable OTel spans + namespaced attrs; follow conventions cautiously/versioned.
Temporal official OpenAI Agents integration demonstrates durable wrapper separation; reinforces runtime/durability decoupling.

## UPDATED TARGET
BLUECAD UI <-AG-UI-> Jarvis AuthorityService(Cedar candidate + budget/secrets/provenance/promotion) -> General Agent Runtime(MAF leading provisional) -> {MCP engineering adapters | ACP coding workers | A2A remote agents | FMI model components}.
Builder flow: authorized task/spec -> isolated checkout/sandbox -> select ACP worker -> stream plan/tool/diff/terminal/usage to Jarvis -> Jarvis permission decisions -> worker edits -> Dagger/build/test -> independent validation/review -> promotion/merge.

## NEXT
P0 audit Letta memory vs Jarvis/Hermes memory; Arize Phoenix/OpenInference + Langfuse vs custom traces/evals.
P0 audit Dagger build pipeline + uv/Pixi/devcontainer contract.
P0 ACP worker benchmark design and exact authority mapping ACP permission->Cedar/Jarvis.
P1 decide MAF vs Hermes vs PydanticAI vs Strands/OpenAI Agents general runtime after coding requirement removed from scoring.
P1 inspect MCP Apps host implementation/security and AG-UI event mapping.
