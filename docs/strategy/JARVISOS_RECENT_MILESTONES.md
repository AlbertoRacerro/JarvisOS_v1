# JarvisOS Recent Milestones

## Current HEAD

| Field | Value |
| --- | --- |
| Current observed HEAD | `a6a7bc4 Add backend architecture handout with prioritized-direction notes` |
| Review-pack type | Docs-only |
| Runtime changes in this pack | None |

## Recent Commit Timeline

| Commit | Message | Strategic impact |
| --- | --- | --- |
| `a6a7bc4` | Add backend architecture handout with prioritized-direction notes | Consolidated current backend architecture and next priorities |
| `a9033bb` | Allow safe Auto local-only sensitive execution | Fixed Auto so confidential/sensitive-IP content can be answered locally while secret/external/tool/state cases stay non-executing |
| `2920afb` | Add semantic Auto routing with context levels | Added semantic Auto routing, capability matrix, context levels, and route-aware context budgets |
| `d1ff849` | Document semantic routing reference audit | Added docs-only external reference audit and routing matrix design |
| `86f1626` | Add Stop JarvisOS launcher | Added stop/launcher operational support |
| `ed63dca` | Serve built frontend from backend and add silent desktop launcher | Improved desktop/local deployment flow |
| `295f34f` | Expose Auto route and task_kind in AI console UI | UI exposed Auto and task kind controls |
| `d16c35f` | Wire Auto route to RouterPolicy local model selection | Connected Auto route to RouterPolicy/local model bridge |
| `28f59f5` | Resolve RouterPolicy baseline divergences | Fixed canonical RouterPolicy baseline cases |
| `2f927a2` | Make backend RouterPolicy producer canonical via re-export shim | Made backend RouterPolicy producer canonical; script became shim |
| `fd28840` | Promote RouterPolicy decision producer to backend runtime | Moved RouterPolicy producer into backend runtime |
| `26fd43e` | Add opt-in Ollama lifecycle management | Added local runtime lifecycle support, opt-in |
| `67dc0ca` | Harden shared Ollama endpoint resolver | Hardened local-only endpoint resolver behavior |
| `9701935` | Replace stale local model defaults with qwen3 | Removed stale `gemma3:4b` default path |
| `5a9f525` | Add read-only local AI runtime status | Added read-only Ollama runtime status |
| `cc8d734` | Add explicit local model route bindings | Added local route classes and model env overrides |
| `72f2ea3` | Reorganize AI workspace UI around execution console | Reduced AI UI around execution and diagnostics |
| `547009a` | Add local Ollama adapter to AI spine | Added local Ollama provider path |
| `e39feae` | Surface context metadata in AI task response | Surfaced context metadata in API/UI |
| `a40232b` | Add UI capability map (UI-MAP-1) | Added UI capability map |
| `ff9cef5` | Wire workspace context into AI task endpoint, opt-in (POS-2B) | Connected opt-in workspace context to AI task endpoint |
| `d71a54a` | Inject and budget AI context in the spine (POS-2) | Added budgeted context in AI spine |
| `8b4b2e7` | Add UI hook for AI task endpoint | Added frontend hook to run AI task endpoint |
| `ee59a8d` | Add AI task endpoint for positive execution spine | Exposed backend task endpoint |
| `71f3bfd` | Add positive AI execution spine: run_ai_task + ai_jobs ledger (POS-1) | Created positive AI execution spine and ledger |

## Milestone Interpretation

The recent sequence is coherent:

1. Build AI execution spine.
2. Add endpoint and UI.
3. Add context metadata and context injection.
4. Add local Ollama adapter and explicit local model routes.
5. Add runtime status/lifecycle hardening.
6. Canonicalize RouterPolicy in backend.
7. Add Auto as local-only semantic bridge.
8. Fix sensitive local execution.
9. Consolidate architecture handout.

This is the right direction because it builds a usable local AI capability
without immediately granting external, memory, or tool authority.

## Known Test Evidence From Recent Reports

Recent user-provided milestone summaries and commit hygiene reports mention:

| Slice | Reported evidence, not re-verified in this docs slice |
| --- | --- |
| POS-1 | Live Scaleway smoke passed; `ai_jobs` row written |
| POS-1B | Backend endpoint tests and ruff passed for scoped files |
| POS-1C | Frontend build passed before commit |
| OBS-1 | Scoped backend/frontend checks passed; broad ruff had unrelated baseline failures at the time |
| LOCAL-ADAPTER-1 | Targeted tests, full backend suite, scoped ruff, diff check passed |
| LOCAL-MODELS-1 | Local route binding tests and backend gates passed |
| LOCAL-RUNTIME-0 | Runtime status tests and backend gates passed |
| BRIDGE-1b-R2 | Full backend reportedly `632 passed`; Auto sensitive local execution fixed |

Exact full logs are not reproduced in this pack. They should be checked from
repo/test history if Fable needs audit-grade evidence.

## Current Architectural Boundary Achieved

| Boundary | Current status |
| --- | --- |
| AI task through spine | Implemented |
| Ledger for normal AI calls | Implemented |
| Auto local-only | Implemented |
| Sensitive local execution | Implemented |
| External Auto execution | Not built |
| Context budget/posture | Implemented |
| Semantic retrieval | Not built |
| Agent swarm | Not built |
| Tool execution from AI | Not built |
| Memory promotion runtime | Not built |

## Notes on Hash Length

This table uses short hashes from current `git log --oneline`. Full hashes
should be resolved with `git rev-parse <short-hash>` if a formal release note
requires full 40-character identifiers.

## What The Sequence Avoided

The recent sequence deliberately avoided several tempting shortcuts:

| Shortcut avoided | Why it matters |
| --- | --- |
| UI-first AI feature expansion | Backend spine and ledgers came first |
| Cloud-first Auto route | Auto stayed local-only |
| Classifier as authority | RouterPolicy and bridge gates own execution |
| Context as hidden memory | Context metadata is surfaced |
| Broad Ollama process automation first | Runtime status/lifecycle were staged |
| Duplicated Project Knowledge UI | Domain Foundation remains editor |
| Agent/tool autonomy | Registries exist, execution is not granted |

This restraint is a strength. The architecture is becoming useful without
collapsing into over-broad autonomy.

## Milestone Gaps That Remain

| Gap | Suggested next evidence |
| --- | --- |
| Local runtime reliability | Real local smoke matrix per route/model |
| Route quality | Offline prompt set with expected capability/context |
| Context source precision | Source-selection tests with known workspace fixtures |
| Redaction | Deterministic examples and adversarial leakage cases |
| Tool contract | Schema plus dry-run-only first tool |
| Memory runtime | Raw intake and promotion boundaries |
| Agent readiness | Read-only agent job record and review UI |
