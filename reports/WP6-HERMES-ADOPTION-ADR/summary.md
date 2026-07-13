# WP6 — Hermes adoption architecture decision

Date: 2026-07-13

## Scope

Docs/report only. This slice appends ADR-060 after merged ADR-059 and records the
durable buy-vs-build decision for Hermes Agent:

- Hermes is the pinned, swappable operational agent-loop engine;
- JarvisOS retains state, domain services, provider credentials, sensitivity,
  route policy, budget, egress, ledger, proposal validation, and promotion;
- integration uses only an OpenAI-compatible passthrough and MCP;
- Hermes internals, memory, skills, and configuration are non-canonical;
- external passthrough execution remains blocked until 059b is merged and active;
- merged PR #90 / 059a remains unchanged.

No runtime, schema, dependency, workflow, provider, frontend, test, specification,
registry, secret, or Hermes installation/configuration change is included.

## Reconstruction

The branch is reconstructed as one commit directly from post-#101 `master`
`6340d6832fc0248a547e3a820843aefd85be911e`.

The intended final master-relative delta is exactly:

1. append ADR-060 to `docs/DECISIONS.md`;
2. add this report.

ADR-059 remains owned by merged PR #98 and is preserved unchanged.

## Authority boundaries

- keys and provider OAuth credentials remain only in JarvisOS;
- every model call traverses `run_ai_task` and writes `ai_jobs` evidence;
- Hermes never owns sensitivity, route permission, egress, budget, promotion, or
  accepted engineering state;
- canonical engineering truth enters SQLite only through JarvisOS proposal and
  promotion paths;
- host-level isolation is required; YAML deny rules are not represented as a
  sandbox;
- browser, web search, computer use, cron, proactive triggers, broad
  terminal/filesystem access, MCP sampling, and unrelated MCP servers start
  disabled;
- model switching and subagents may choose only JarvisOS policy aliases.

## Remaining correction

Before merge, the unrelated ADR-018 wording drift must be reverted from
`real proprietary IP enters the system` to the master wording
`real proprietary data enters the system`. No other existing ADR text may change.

## Temporary reconstruction trigger

This line exists only to emit a pull-request synchronize event after installing
the branch-local CI reconstruction job. The reconstruction resets to `master`, so
this section and all temporary workflow changes must disappear from the final diff.

## Merge gate

Keep draft until:

1. the ADR-018 wording drift is removed;
2. the final diff contains exactly `docs/DECISIONS.md` and this report;
3. GitHub Actions execute and pass on the final head;
4. a current-head review completes and every finding is fixed or explicitly
   dispositioned;
5. the maintainer authorizes merge.
