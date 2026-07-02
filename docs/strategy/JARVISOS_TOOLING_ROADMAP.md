# JarvisOS Tooling Roadmap

## Current Tooling State

JarvisOS currently has:

| Tooling area | Status |
| --- | --- |
| Local Python Runner V0 | Implemented for bounded simulation use |
| Tool registry | Minimal protocol/registry skeleton |
| Agent registry | Minimal protocol/registry skeleton |
| AI provider adapters | Fake, local Ollama, Scaleway |
| Ollama runtime helpers | Endpoint resolver/status/lifecycle work exists |
| Launcher scripts | Desktop/start/stop support exists |
| MCP/browser/worker execution | Not integrated into AI spine |
| General shell execution from AI | Not allowed |

This is the right sequence: build the policy and ledger spine before exposing
powerful tools.

## Tool Policy Principles

Any future tool layer should follow these principles:

| Principle | Requirement |
| --- | --- |
| Explicit capability | Tool declares what it can read/write/execute |
| Scope-bound inputs | Tool receives a constrained payload, not arbitrary prompt text |
| Deterministic validation | JarvisOS validates before execution |
| Ledger first | Every tool call gets an auditable record |
| Dry-run where possible | Proposed changes visible before execution |
| Reversible where possible | State changes should support rollback or compensation |
| No secret leakage | Tool context must be sensitivity-aware |
| No hidden network | Network access must be declared and gated |

## Tool Types

Recommended future taxonomy:

| Tool type | Examples | Risk |
| --- | --- | --- |
| Read-only local | File/repo/db inspection, status checks | Low to medium |
| Deterministic transform | Format, validate, convert, render | Medium |
| Simulation | Run model with bounded inputs | Medium |
| Write local state | Create artifacts, update assumptions | Medium to high |
| Network read | Search, fetch docs, API status | High for privacy/copyright |
| External provider | Cloud model/API calls | High for privacy/cost |
| Shell/process | General command execution | Very high |
| Actuation | Devices, services, money, external state | Not ready |

JarvisOS should start with read-only and deterministic tools, then expand only
after the ledger and approval model are solid.

## Runner Roadmap

The local runner should evolve before general agent tools:

| Stage | Capability |
| --- | --- |
| V0 | Existing bounded batch-growth runner |
| V1 | More templates, stronger artifact lineage, better error reports |
| V2 | Parameter sweeps and sensitivity analysis |
| V3 | Sandbox hardening and resource controls |
| V4 | Multi-language or containerized execution, if justified |

The runner should remain separate from the AI provider layer. AI may propose
runs, but the runner validates and executes.

## Provider Tooling

Provider integrations should remain adapters behind the AI spine:

- Fake provider for tests/dev.
- Local Ollama provider for local models.
- Scaleway provider for explicit cloud route.
- Future providers only through provider registry/adapters.

Provider adapters should not decide memory, tool execution, or sensitivity.

## Observability Roadmap

JarvisOS needs stronger observability before autonomy:

| Ledger/signal | Purpose |
| --- | --- |
| `ai_jobs` | AI calls, route decisions, usage, context digests |
| Tool jobs | Tool execution attempts, payload digests, outputs |
| Agent jobs | Agent plans, subtask state, source manifests |
| Memory events | Intake, enrichment, promotion, supersession |
| Simulation lineage | Model version, input digest, output artifacts |
| Cost ledger | Provider usage and estimated spend |
| Safety ledger | Blocked/confirmation/control states |

Without these, debugging and trust will collapse as soon as agents act.

## Recommended Tool Milestones

| Milestone | Description |
| --- | --- |
| `TOOL-CONTRACT-0` | Define tool schema: capabilities, inputs, outputs, permissions |
| `TOOL-LEDGER-0` | Add tool job ledger before broad execution |
| `TOOL-READONLY-0` | Add safe read-only tools for workspace/repo inspection |
| `RUNNER-1` | Expand controlled computational runner |
| `TOOL-DRYRUN-0` | Add patch/change proposal workflow |
| `AGENT-TOOL-0` | Let agent propose tool calls, not execute directly |
| `EXTERNAL-TOOL-0` | Add network tools only after redaction and confirmation |

## What Fable Should Challenge

1. Should tools use one generic ledger or domain-specific ledgers?
2. Should tool permission be per route, per sensitivity, per workspace, or all
   three?
3. What minimal tool set creates real engineering value without autonomy risk?
4. How should the UI expose approval without becoming noisy?
5. Should tool execution be synchronous through API routes or asynchronous jobs?

## Hard Boundary

Do not add broad tool execution simply because agents need it. Agents should be
forced to operate through narrow, logged, typed tools. Tooling is the real
safety boundary between "AI suggested" and "system changed".

## Approval UX Direction

Tool approval should be compact but evidence-rich. For each proposed action, the
UI should show:

- Tool name.
- Workspace/scope.
- Inputs or input digest.
- Files/records affected.
- Network/provider behavior.
- Cost estimate if any.
- Sensitivity classification.
- Reversibility.
- Expected outputs.
- Reason the model/agent requested it.

Approval should not be a generic "yes/no" over a hidden prompt. Users need to
approve a typed operation.

## Tool Contract Fields

A minimal tool contract should include:

| Field | Purpose |
| --- | --- |
| `name` | Stable tool identifier |
| `version` | Contract migration |
| `description` | Human review |
| `input_schema` | Deterministic validation |
| `output_schema` | Safe downstream use |
| `read_scopes` | What it can inspect |
| `write_scopes` | What it can change |
| `network_scopes` | Any external access |
| `side_effect_level` | Policy gate |
| `reversibility` | Approval and rollback |
| `sensitivity_allowed` | Data boundary |
| `default_mode` | Dry run vs execute |

This schema can be implemented before any powerful tools are exposed.
