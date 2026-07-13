# WP6 — Hermes adoption architecture decision

Date: 2026-07-13

## Scope

Docs/report only. This stack appends ADR-060 after ADR-059 and records the durable
buy-vs-build decision for Hermes Agent:

- Hermes is the pinned, swappable operational agent-loop engine;
- JarvisOS retains state, domain services, provider credentials, sensitivity,
  route policy, budget, egress, ledger, proposal validation, and promotion;
- integration uses only an OpenAI-compatible passthrough and MCP;
- Hermes internals, memory, skills, and configuration are non-canonical;
- external passthrough execution remains blocked until 059b is merged and active;
- merged PR #90 / 059a remains unchanged.

No runtime, schema, dependency, workflow, provider, frontend, test, specification,
registry, secret, or Hermes installation/configuration change is included.

## Stack

This branch is based on PR #98 head after ADR-059 was added. ADR-059 remains owned
by PR #98; this stack adds ADR-060 only.

## Known merge blocker

The current branch comparison also contains one unrelated wording drift in
ADR-018:

- current base wording: `when real proprietary data enters the system`;
- current branch wording: `when real proprietary IP enters the system`.

That change is not required by the Hermes decision and must be reverted before
merge. The intended final delta relative to PR #98 is exactly:

1. append ADR-060 to `docs/DECISIONS.md`;
2. add this report.

The PR must remain draft and must not be marked ready while that one-line drift is
present.

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

## Merge gate

Keep draft until:

1. the ADR-018 wording drift is removed;
2. PR #98 is merged and this branch is retargeted/rebased to the resulting
   `master`;
3. the final diff contains exactly `docs/DECISIONS.md` and this report;
4. GitHub Actions execute and pass on the final head;
5. a current-head review completes and every finding is fixed or explicitly
   dispositioned;
6. the maintainer authorizes merge.
