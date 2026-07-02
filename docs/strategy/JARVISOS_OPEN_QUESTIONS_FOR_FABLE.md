# JarvisOS Open Questions for Fable

## How To Use This File

These are targeted questions for a frontier-model strategic review. They are
not implementation tasks. The goal is to pressure-test architecture and
sequencing before expensive runtime features are added.

## Architecture Questions

| Question | Why it matters |
| --- | --- |
| Is backend-led policy/execution/audit the right center, or should more live in the frontend/workbench layer? | Determines long-term maintainability |
| Is the current subsystem split enough for a technical OS, or should tools/agents/memory get stricter boundaries now? | Avoids future refactor debt |
| Should `ai_jobs` remain the main AI ledger, or should Auto/control/tool/agent states get separate ledgers? | Affects audit and observability |
| Is "AI models propose, JarvisOS validates" strong enough for future autonomy? | Core safety invariant |

## Routing and Model Economy Questions

| Question | Why it matters |
| --- | --- |
| Should `deep_reasoning` remain best-effort local until redaction/external confirmation exists? | Balances quality vs safety |
| How should JarvisOS decide when local capability is insufficient without leaking data? | Needed for external escalation |
| Is the current capability matrix too coarse, too complex, or about right? | Determines route maintainability |
| Should `local:coder_heavy` be used routinely if it spills/loads slowly on 12 GB VRAM? | Cost is latency and user trust, not only money |
| What minimum evaluation set is needed before adaptive routing or bandits? | Avoids optimizing noise |

## Memory and Context Questions

| Question | Why it matters |
| --- | --- |
| Should first retrieval be structured SQL/FTS over accepted records before vector search? | Simpler, auditable start |
| What is the right source-selection contract for `context_level`? | Current context is budget-only |
| How should stale or superseded memory be kept visible without contaminating prompts? | Engineering projects evolve |
| Should memory promotion require human confirmation, deterministic policy, or both? | Prevents hallucinated memory |
| What is the minimum memory UI needed before runtime memory writes? | Prevents hidden state |

## Agent Swarm Questions

| Question | Why it matters |
| --- | --- |
| Which first agent creates the most value with least autonomy risk: reviewer, planner, memory curator, or code analyst? | Sequencing |
| Should agent jobs be synchronous API calls or durable async jobs from the start? | UX and audit tradeoff |
| How should agents request tools without directly executing them? | Safety boundary |
| What is the smallest agent output schema that remains useful? | Prevents prompt-only orchestration |
| Should there be a critic/reviewer agent before executor agents? | Reduces unsafe action |

## Computational Engineering Questions

| Question | Why it matters |
| --- | --- |
| What is the right next runner expansion after batch-growth V0? | Determines engineering value |
| How should model specs, assumptions, parameters, and simulation runs become one reviewable graph? | Builds model capital |
| Should AI-generated model code be stored as draft artifacts before runnable versions? | Preserves review boundary |
| How should validation criteria attach to simulation runs? | Needed before trusting output |
| What BlueRev workflow should be first: assumptions, parameter ranges, simulation comparison, or literature intake? | Domain prioritization |

## Tooling Questions

| Question | Why it matters |
| --- | --- |
| Should tools be registered by capability, risk tier, or domain module? | Determines policy checks |
| What tool permissions are workspace-level vs global? | Multi-project safety |
| Should read-only tools be available to Auto before agent swarm exists? | Could improve utility with low risk |
| How should dry-run and approval be represented in API/UI? | Human trust |
| What network tools are acceptable after redaction exists? | External research path |

## Safety/IP/Cost Questions

| Question | Why it matters |
| --- | --- |
| What exact data categories may ever leave the machine? | External escalation policy |
| What redaction quality is sufficient before external reasoning? | Prevents false confidence |
| Should external confirmation be per call, per workspace, per session, or persistent policy? | UX vs safety |
| How should JarvisOS estimate cost before executing a provider call? | Budget control |
| Should local-sensitive answers be flagged for audit/manual review without blocking? | Current local sensitive path is useful but still deserves visibility |

## Known Uncertainties

| Item | Status |
| --- | --- |
| Production readiness of `external:reasoning` | unknown / needs verification |
| Current latency of each installed local model on target hardware | unknown / needs verification |
| Best first retrieval backend | unknown / needs verification |
| Preferred ledger split for agents/tools/control states | unknown / needs verification |
| Full UI acceptance after latest Auto changes | unknown / needs verification |
| Exact model quality ceiling for qwen/gemma/deepseek routes | unknown / needs verification |

## Fable Deliverable Request

Fable should return:

1. A ranked architecture-risk list.
2. A recommended next 5 milestones.
3. Any boundary that should be hardened before agents/tools.
4. A proposed memory/retrieval milestone sequence.
5. A proposed local/external model-economy policy.
6. A critique of the computational engineering workspace direction.

## Decision Constraints for Fable

Any recommendation should respect:

- Auto external execution is currently forbidden.
- Sensitive/IP content may be answered locally when no external/tool/state
  action is requested.
- Secret content should remain blocked.
- `context_level` is not semantic retrieval.
- Domain Foundation remains the project-knowledge editor.
- Local model outputs are advisory unless deterministic policy promotes them.
- Agents/tools should not be introduced before their ledgers and policy gates.
- External references are design evidence, not vendored runtime authority.

## Ideal Fable Review Style

Preferred output:

- Direct architectural critique.
- Clear "keep/change/defer" table.
- Milestone sequence with blockers.
- Specific files/modules to inspect next.
- Explicit risk of overengineering or underbuilding.
- Warnings where current docs sound more mature than runtime reality.

Avoid:

- Generic praise.
- Recommending a broad agent framework immediately.
- Treating memory as solved by vector search.
- Treating external providers as an automatic quality fix.
- Ignoring local hardware and latency constraints.
