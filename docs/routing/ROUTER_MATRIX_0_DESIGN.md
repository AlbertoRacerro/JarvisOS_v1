# ROUTER-MATRIX-0 Design

## Status

Design/specification only.

This document is not runtime authority. It does not approve provider calls,
external network, retrieval, memory injection, database schema changes, UI
changes, adaptive learning, or source selection.

## Problem

BRIDGE-1b introduces a useful Auto seam:

```text
classification -> capability row -> local route class
```

The missing piece is that context use is still too coarse. A boolean
`include_project_context` plus `needs_context` can only scale budget. It does
not decide which records are relevant.

ROUTER-MATRIX-0 should add a conservative context policy without pretending to
implement intelligent retrieval.

## Design Goals

- Keep Auto local-only.
- Keep RouterPolicy as the execution/safety gate.
- Keep classifier output advisory.
- Keep manual `context_blocks` preserved.
- Add stable metadata for capability and context decisions.
- Make context use explainable.
- Make `deep` rare.
- Make context budget depend on selected local route/model.
- Defer source selection.

## Non-Goals

- No external fallback.
- No provider SDK.
- No economic routing.
- No adaptive bandit.
- No grading/success feedback.
- No retrieval/source selection.
- No memory writes.
- No streaming.
- No prompt hard max length beyond existing validators.
- No frontend redesign.

## Proposed Contract

### Semantic Classification

Classifier output remains advisory:

```text
task_type
project_area
complexity_hint
needs_context
sensitivity_hint
allowed_next_step
confidence
source
fallback_reasons
deterministic_reasons
signals
```

Classifier output must not authorize:

- provider calls;
- external network;
- tool execution;
- memory writes;
- retrieval;
- file writes.

### Capability Matrix

Provider-agnostic capability rows:

| Capability row | Intended meaning | Local route |
| --- | --- | --- |
| `simple` | short answer, summary, trivial explanation | `local:fast` |
| `general_reasoning` | project reasoning, synthesis, decision support | `local:general` |
| `coding` | code review, bug analysis, bounded patch reasoning | `local:coder` |
| `heavy_coding` | architecture or multi-file code reasoning | `local:coder_heavy` |
| `deep_reasoning` | would benefit from stronger/deeper model, but Auto stays local | `local:general` initially |

External benefit is metadata only:

```text
would_benefit_from_external: true|false
external_candidate: external:...
external_execution_allowed: false
```

For this milestone, Auto never executes external providers.

### Context Permission

`include_project_context` is a permission cap:

| User permission | Classifier asks for context | Final workspace context |
| --- | --- | --- |
| false | any | none |
| true | false | none |
| true | true and relevant project area | level chosen by policy |
| true | fallback or low confidence | conservative level, never deep |

Manual `context_blocks` are different from workspace context:

- always preserved;
- still subject to request validator limits;
- counted before workspace context budget;
- never removed because `context_level=none`.

### Context Levels

`context_level` applies only to workspace/project context.

| Level | Meaning | Selection rule |
| --- | --- | --- |
| `none` | no workspace context injected | default, permission off, self-contained prompt |
| `light` | small amount of project context | project-related but bounded prompt |
| `standard` | normal project context | synthesis/decision/project reasoning with permission on |
| `deep` | largest context budget | explicit project/history/document/audit need only |

Deep must not be selected from `complexity_hint=high` alone.

Acceptable deep triggers:

- prompt explicitly asks to use project history/state/docs;
- task is architecture/project audit across multiple project records;
- classifier has high confidence, relevant project area, and context need;
- selected route can handle larger context.

If unsure, downgrade:

```text
deep -> standard
standard -> light
light -> none
```

### Route-Aware Context Budget

Budget is a policy derived from both context level and selected route.

Initial conservative table:

| Local route | none | light | standard | deep |
| --- | ---:| ---:| ---:| ---:|
| `local:fast` | 0 | 4000 | 6000 | downgrade to standard |
| `local:general` | 0 | 6000 | 16000 | 24000 |
| `local:coder` | 0 | 4000 | 10000 | downgrade to standard |
| `local:coder_heavy` | 0 | 6000 | 16000 | 32000 |

These are workspace-context ceilings, not prompt limits.

Manual context length is counted first:

```text
workspace_budget = max(0, route_level_budget - serialized_manual_context_chars)
```

If manual context already consumes the budget, workspace context is skipped and
metadata should say why.

### Context Decision Metadata

Every Auto response should expose:

```text
context_permission: true|false
context_level: none|light|standard|deep
context_budget_chars
context_budget_reason
context_used: true|false
workspace_id
manual_context_blocks_count
workspace_context_blocks_count
context_sources_count
context_digest
source_selection_status: budget_only|deferred|not_requested
```

`source_selection_status=budget_only` means JarvisOS selected budget, not
specific intelligent sources.

### Decision Order

Required order:

```text
1. build classifier input
2. classify prompt
3. handle control states
4. map classification to capability row
5. map capability row to local route class
6. build RouterPolicy input for local-only execution gate
7. evaluate RouterPolicy safe-local gate
8. derive context_level and budget
9. build workspace context only if permitted and executable-local
10. call run_ai_task with selected local route
```

Control states stop before context build and before `run_ai_task`.

### Control States

These never call `run_ai_task`:

| Classifier/task condition | Status |
| --- | --- |
| `external_api_request` | `proposed_external` |
| `ambiguous` or `ask_clarification` | `needs_clarification` |
| `unsafe_tool_request` | `blocked` |
| `overbroad_orchestration_request` | `blocked` |
| adversarial external RouterPolicy decision | non-executing control state |

Control-state ledger rows may be written by the gateway/bridge directly, but
must not invent provider/model/tokens.

## Tests Required

Offline tests only.

### Capability

- each semantic task type maps to expected capability row;
- each capability row maps to expected local route;
- external benefit is metadata only;
- missing/unknown capability falls back to `simple -> local:fast`.

### Context Level

- permission off always yields `none`;
- self-contained prompt yields `none`;
- project-related bounded prompt yields `light`;
- synthesis/decision support yields `standard`;
- `complexity_hint=high` alone does not yield `deep`;
- explicit project/history/audit need can yield `deep`;
- low confidence/fallback never yields `deep`;
- unsupported route downgrades `deep`.

### Context Budget

- local route caps are enforced;
- manual blocks are preserved;
- manual blocks reduce workspace budget;
- workspace context skipped when remaining budget is zero;
- metadata explains budget and skip reason.

### Safety

- Auto never executes external;
- control states never call `run_ai_task`;
- explicit non-auto route bypasses bridge;
- `route_class=None` still defaults to `local:fake`;
- RouterPolicy safe-local predicate remains the local execution gate.

### Metadata

- response includes capability row;
- response includes selected local route;
- response includes context level and budget;
- response distinguishes permission on from context actually used;
- response exposes `source_selection_status`.

## Implementation Slice Boundary

Allowed files for the code slice should be narrow:

```text
backend/app/modules/ai/routing/bridge.py
backend/app/modules/ai/routing/capability_route_matrix.py
backend/app/modules/ai/models.py
backend/tests/test_ai_auto_bridge.py
```

Touch `gateway.py` only if the existing Auto branch still builds workspace
context before the bridge.

Do not touch frontend, provider adapters, DB schema, settings, local runtime
lifecycle, or RouterPolicy producer unless a test proves the seam is broken.

## Reference Mapping

| JarvisOS concept | Reference source | Adaptation |
| --- | --- | --- |
| capability row | LiteLLM `RequestType`, RouteLLM strong/weak abstraction | small JarvisOS-owned enum |
| route explanation | LiteLLM complexity signals, LlamaIndex selector reasons | metadata fields with reasons |
| threshold/calibration future | RouteLLM threshold sweeps | future benchmark harness only |
| classifier/registry separation | AutoGen semantic router sample | classifier separate from capability registry |
| source selection future | LlamaIndex selector/router query engine | later source selector, not this slice |
| model inventory future | Open WebUI model list aggregation | read-only status only, no code copy |

## Acceptance Criteria

ROUTER-MATRIX-0 is acceptable when:

- Auto selects a real local route from semantic capability.
- Context level is explicit and conservative.
- Deep is rare and tested.
- Manual context is preserved.
- Context budget depends on selected route.
- Metadata explains why context was or was not used.
- Source selection is explicitly deferred.
- No external provider or live Ollama call happens in tests.

## Deferred Milestones

- `SOURCE-SELECTION-0`: choose which workspace records to inject.
- `ROUTER-CALIBRATION-0`: offline route benchmark and threshold/success curves.
- `ROUTER-FEEDBACK-0`: success/grading signals before adaptive routing.
- `ADAPTIVE-ROUTER-0`: bandit/feedback only after enough reliable outcomes.
