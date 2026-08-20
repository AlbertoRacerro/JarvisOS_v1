# AI INFRA DISCOVERY DELTA1 — 2026-08-20
PURPOSE=AI_REHYDRATION;FORMAT=TOKEN_DENSE;AUTHORITY=AUDIT_ONLY;IMPLEMENTATION_AUTHORIZED=NO;BRANCH=audit/hermes-agent-2026-08-20

## PRIORITY
CURRENT_PHASE=AI_SOFTWARE_INFRA;ENGINEERING_DETAIL=DEFERRED. PIPPO_OS;SUNK_COST_ZERO;REPLACE_NOT_LAYER;CODE_FIRST.

## EMERGING TARGET
JarvisAuthority -> MinimalAgentLoop -> CapabilityDiscovery/ToolSearch -> {CodeIntelligence,Memory,ScientificCompute,RepoWorkspace,...} -> deterministic validation/promotion.
RULE=capability complexity outside core loop. Runtime does not embed LSP/Wolfram/solver semantics. Discover optional capabilities only when needed.

## MICROSOFT AGENT FRAMEWORK
REPO=microsoft/agent-framework;LICENSE=MIT;CLASS=ADOPT_CANDIDATE_COMPONENTS/S.
CODE_FIRST: python core contains real `_agents,_sessions,_compaction,_evaluation,_harness,_mcp,_middleware,_serialization` plus workflow/checkpoint/durable orchestration and tests; not wrapper. COMPETES_WITH_HERMES especially durability/checkpointing/session persistence/middleware/evaluation/background agents. Hermes remains stronger baseline for coding-oriented ToolSearch/skills/terminal ecosystem until direct benchmark. ACTION=component-by-component comparison; DO_NOT_MONOLITHIC_SWAP yet.

## OPENHANDS SOFTWARE AGENT SDK
REPO=OpenHands/software-agent-sdk;LICENSE=MIT;CLASS=ADOPT_CANDIDATE_COMPONENTS/S.
CURRENT modular SDK powering OpenHands; uv workspace={openhands-sdk,openhands-tools,openhands-workspace,openhands-agent-server}. Root packaging has security guardrails incl recent-package exclusion and vulnerability floors; tests/lint/typecheck/stress infra. LIKELY_VALUE={workspace/sandbox,agent-server,terminal/file tools,event/context architecture}. ACTION=deeper exact workspace/runtime audit vs Hermes before adoption.

## MINI-SWE-AGENT
REPO=SWE-agent/mini-swe-agent;LICENSE=MIT;CLASS=REFERENCE+POSSIBLE_CORE_PATTERN/S.
CURRENT v2 supersedes full SWE-agent for much usage. Actual DefaultAgent core ~8KB and loop is intentionally trivial: messages; query(model); execute env actions; append observations; limits={steps,cost,walltime,format-errors}; serialize full trajectory. No requirement for complex tool-calling framework. PRINCIPLE=advanced LM capabilities reduce need for logic in core agent; use simple loop + optional capabilities. DOES_NOT_CONFLICT_WITH_SERENA: minimal core can call semantic capability. TARGET=keep Hermes-derived core minimal; avoid framework accretion.

## SERENA
REPO=oraios/serena;LICENSE=MIT;VERSION~1.5/1.6 current;CLASS=ADOPT_CANDIDATE/S.
FUNCTION=framework-independent semantic code intelligence exposed via MCP or direct tools; SolidLSP backend or JetBrains.
CODE: tool modules substantial; symbol tools provide get_symbols_overview, find_symbol, find_referencing_symbols, find_implementations, symbolic edits; file tools/memory/workflow/query project. Retrieval defaults deliberately token-cheap: bodies excluded unless requested, refs return minimal surrounding lines, max_answer_chars with progressively shortened fallback. Test hierarchy separate for serena and solidlsp.
DECISION=do not rebuild symbol navigation/editing in Jarvis/Hermes. Candidate `CodeIntelligence` capability behind MCP/direct adapter + Jarvis file/write authority. Semantic edit still proposal/validated diff; Serena never owns authority.

## AIDER REPOMAP
REPO=Aider-AI/aider;LICENSE=Apache-2;CLASS=ADOPT_ALGORITHM_OR_MODULE/A+.
CODE=`aider/repomap.py`: tree-sitter defs/refs (Pygments fallback), disk cache by mtime, graph files linked through referenced identifiers, weighted PageRank; boosts current chat files/mentioned filenames/identifiers/long structured identifiers, downweights private/common definitions; ranks definitions/files; renders minimal tree context; binary-searches number of ranked tags to maximize content under token budget. Handles no-files mode with larger overview.
DECISION=complements Serena. Pipeline=`RepoMapRanker(query/task/recent-context)->candidate files/symbols -> Serena LSP exact symbols/refs/body/edit`. This may materially reduce tokens vs global semantic/vector-only code retrieval.

## GRAPHITI MEMORY
REPO=getzep/graphiti;LICENSE=Apache-2;CLASS=ADOPT_CANDIDATE/S.
CODE_FIRST: real temporal graph; EntityEdge stores `fact`, provenance `episodes`, `created_at`, `expired_at`, `valid_at`, `invalid_at`, reference_time/attributes and embeddings; drivers/search/MCP/tests/OTel. MATCH=Jarvis engineering truth where assumptions/parameters/facts become valid/invalid/superseded but history/provenance retained.
TARGET_ARCH=Graphiti is temporal relational memory/index, NOT authority. Canonical deterministic engineering DB remains authority; LLM-extracted Graphiti updates are proposed/derived until validated. Need inspect contradiction/invalidation extraction before promotion.

## MEM0
REPO=mem0ai/mem0;LICENSE=Apache-2;CLASS=ADOPT_CANDIDATE_FOR_RETRIEVAL/A+.
CODE_FIRST Memory has pluggable embedder/vectorstore/LLM/reranker, SQLite history, entity store, identity scope user/agent/run, secret telemetry redaction. Search pipeline=`lemmatize + entity extraction + semantic overfetch + keyword/BM25 + entity boosts + fused scoring + optional rerank`, advanced metadata filters/explain. CAVEAT=OSS `reference_date` temporal query explicitly rejected/platform-only; expiration exists but not full temporal truth query.
DECISION=Mem0 may improve fact extraction/retrieval but does NOT replace local Graphiti temporal truth. Avoid managed-only dependency for canonical engineering semantics. Need benchmark Mem0 retrieval vs lighter custom hybrid before adoption; framework accumulation prohibited.

## LETTA CURRENT STATE
OLD `letta-ai/letta` main=landing page; V1 server archived/unsupported. CURRENT=`letta-ai/letta-code`;LICENSE=Apache-2.
HIGH_VALUE_FINDING=repo itself is explicitly optimized for coding-agent navigability: enforced zero circular imports; layer direction; no parent relative imports; named/export-function conventions for grep; 1000-line max ratchet; module ownership; adjacent tests; unsafe Bun mock isolation; full checks for cycles/boundaries/file-size/coverage/types/skills. Layer map cli->websocket->agent->tools->backend->providers->permissions->leaf layers. Local experimental backend supports deterministic executor for tests.
DECISION=even if Letta memory runtime does not win, its `AI-operated repository hygiene` rules are S reference for Jarvis builders. Audit current src/agent/backend/permissions/memory next.

## WOLFRAM
REPOS={WolframResearch/AgentTools MIT;WolframResearch/WolframClientForPython MIT;WolframLanguageForJupyter MIT;LSPServer MIT};ENGINE=proprietary Wolfram Engine/Mathematica/Chatbook dependency;CLASS=BOUNDARY/SERVICE S for symbolic/scientific compute.
AgentTools 2026 implements MCP server directly; built-in servers={Wolfram,WolframAlpha,WolframLanguage,WolframPacletDevelopment}; tools include WolframContext semantic search, WolframLanguageEvaluator, WolframAlpha, notebook read/write, SymbolDefinition, CodeInspector, TestReport, paclet dev tools. Local stdio MCP + remote Wolfram MCP Service.
CODE_FIRST: substantial Kernel modules; evaluator has isolated session IDs, options Method/Image/TimeConstraint/MaxCharacterCount/MaxSessionCount/MaxSessionBytes/MaxSessionAge, default time=60s, char=10k, sessions=100, bytes=1GB, age=1mo; evaluator routes through Chatbook sandbox/evaluator and returns structured text/image content. Extensive Tests include EvaluatorSessions, CodeInspectorTool, Create/InstallMCPServer, cloud deployment, MCP Apps etc.
CAVEAT evaluator tool description states local file read access; session method may have write semantics. Jarvis must enforce roots/capabilities externally. MCP standard != security boundary.
DECISION=DO_NOT_BUILD_CUSTOM_WOLFRAM_BRIDGE. Integrate AgentTools MCP/local service if/when Engine available; classify Wolfram compute as optional deterministic/symbolic oracle/service. Use same pattern for scientific backends: standardized capability server + external authority.

## MEMORY ROLES — PRELIMINARY NONOVERLAP
canonical_engineering_truth=Jarvis deterministic DB/modeling records;
temporal_relational_index=Graphiti candidate;
episodic/fact_retrieval=Mem0 candidate only if benchmark wins;
agent_runtime_short_context=Hermes/MAF/Letta component comparison;
document_corpus=GraphRAG later if needed.
RULE=no two canonical stores; derived indexes reconstructible.

## CODE INTELLIGENCE TARGET
Task/query/current edits -> Aider-like RepoMapRanker (structural global ranking/token budget) -> Serena (LSP symbol/ref exact retrieval and symbolic editing) -> patch/diff -> tests/static analysis -> Jarvis approval/promotion. Vector/RAG only supplement natural-language docs/non-code; do not use embeddings as primary code navigation when symbol graph exists.

## NEXT
P0 audit Letta current agent/memory/permissions + Microsoft AF checkpoint/session + OpenHands workspace sandbox.
P0 audit DSPy for eval/program optimization and whether self-improvement should be offline optimizer behind promotion gates.
P0 audit Block Goose + Google ADK/OpenAI Agents SDK only for unique components; avoid framework catalog for its own sake.
P0 audit official MCP SDK/spec/security patterns; ToolSearch can operate on MCP capability descriptors.
P1 Graphiti contradiction/invalidation tests; Mem0 OSS benchmark separation.
P1 scientific service ecosystem beyond Wolfram: Jupyter kernel execution/provenance, symbolic verification; only high-leverage.
