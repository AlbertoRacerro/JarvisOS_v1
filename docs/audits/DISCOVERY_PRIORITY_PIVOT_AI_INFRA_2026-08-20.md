# DISCOVERY PRIORITY PIVOT — AI/INFORMATICS INFRASTRUCTURE — 2026-08-20
PURPOSE=AI_REHYDRATION;AUTHORITY=AUDIT_ONLY;IMPLEMENTATION_AUTHORIZED=NO;BRANCH=audit/hermes-agent-2026-08-20

## USER PRIORITY OVERRIDE
ENGINEERING_REPO_COVERAGE=SUFFICIENT_FOR_CURRENT_DISCOVERY_PHASE.
DEPRIORITIZE={corrosion,materials-detail,mechanical-detail,wave/fatigue-deep-dive} except SERENDIPITOUS_HIGH_LEVERAGE_FINDING.
PRIORITIZE={agent_runtime,orchestration,memory,retrieval,repo_coding_automation,tool_integration,scientific_tool_access,knowledge_provenance,workflow_durability,evaluation,self_improvement,sandboxing,software_services,Wolfram/ecosystems}.

## DECISION RULE
Treat JarvisOS, Hermes, and every external repo as equal candidates under PIPPO_OS_TEST. SUNK_COST=ZERO. If external component dominates Jarvis/Hermes on code quality,generality,tests,maintainability,license,capability -> REPLACE rather than layer. Preserve Jarvis only where it has superior authority/governance/engineering-truth semantics. Avoid framework accumulation.

## DISCOVERY METHOD
CODE_FIRST. README only locator. For each candidate inspect >= {license,package/deps,core execution path,state/memory/tool abstractions,tests/CI,security/approval boundary,storage/retrieval semantics,extension interface}. Classify={ADOPT_CANDIDATE,HYBRID,REFERENCE_ONLY,EXTERNAL,CLEAN_ROOM,NEGATIVE_REFERENCE}. Record migration target and deletion target when applicable.

## TARGET AXES
A_AGENT_RUNTIME={Hermes baseline competitor; OpenHands; SWE-agent; Microsoft/Google/OpenAI/HF/Stanford frameworks; other research agents}.
B_MEMORY_RETRIEVAL={Letta/MemGPT; Mem0; Graphiti/Zep; GraphRAG; HippoRAG/LightRAG/cognee; vector+graph+temporal retrieval; provenance-aware engineering memory}.
C_CODING_REPO_AUTOMATION={OpenHands runtime; SWE-agent ACI; patch/test loops; sandbox/terminal; repo indexing; trajectory/evaluation; multi-agent review}.
D_TOOL_PROTOCOLS={MCP SDK/ecosystem; plugin/tool search/progressive disclosure; remote/local services; capability manifests; sandboxing}.
E_SCIENTIFIC_COMPUTE_ACCESS={Wolfram client/kernel/cloud APIs; symbolic/numeric systems; notebook kernels; computation-as-tool; provenance+deterministic verification}.
F_EVAL_SELF_IMPROVEMENT={DSPy/optimizers; agent benchmarks; trace/replay; prompt/policy optimization; offline learning; regression gates}.

## STOP RULE
Do NOT spend time closing low-priority scientific subdomains during this tranche. Return to engineering-detail only when needed for MVP implementation, validation gap, or a newly found infrastructure mechanism needs a real engineering stress-test.
