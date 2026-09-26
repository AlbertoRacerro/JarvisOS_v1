# 154 — Persistent development context (control-room continuity)

State: **ready**. Combined definition, full contract and readiness, authorized by the maintainer's 2026-09-26 mission directive. Evidence, measurements and the alternatives analysis are in [the 2026-09-26 archaeology record](../implementation/154-continuity-archaeology-2026-09-26.md).

## Problem

JarvisOS development runs across coordinator sessions, Codex/Gemini lanes, Agent Relay, GitHub, local worktrees, proof artifacts and a free-text `PROGRESS.md`. When a coordinator dies, loses auth or network, or is replaced, the next one starts from a maintainer-written handoff plus its own archaeology. In the 48 hours before this spec there were at least 12 such recoveries. Relay's continuation carries only a directory pointer and ~140-character turn excerpts. Its model-written handoff claimed 151 was still unmerged about an hour after it merged. `PROGRESS.md` opens with a two-day-old "Active lanes" list, and one coordinator missed an authoritative correction appended below it. Second Brain and Hermes have no model of PRs, lanes, worktrees or proofs.

## Outcome

A fresh coordinator of any vendor with a shell, given only a minimal instruction such as "Recover current JarvisOS maintainer context and continue", runs one command. That command returns a bounded **recovery packet** built at read time from fresh authoritative sources. The packet is annotated with the non-derivable decisions, findings, proof results, claims and maintainer directives that earlier sessions recorded, and each recorded item carries a mechanically computed freshness verdict. The coordinator then verifies authority as usual and continues the dependency-valid next task without repeating completed expensive work.

## Architecture decision

One repository-owned, standard-library-only CLI, `scripts/devctx.py`, plus one append-only **control ledger** in the local control-room directory. The ledger replaces free-text `PROGRESS.md` as the place for new entries. It is not an additional store.

- **Derived, not remembered.** Repository truth (fresh `origin/master`, open PRs and heads/checks, STATUS rows and dependency-valid `ready` specs, worktrees and their branch/dirty/ahead state), control-room truth (lane prompt/report/done/log files and live lane processes) and runtime truth (agent/model processes, GPU occupancy) are recomputed on every call. Nothing derivable is stored.
- **Ledger for what cannot be derived.** Typed entries: maintainer directive (verbatim copy plus digest), decision (accepted or proposed, with its authority reference), finding, proof/test result, failed attempt, blocker/question, and single-writer claim. An entry may supersede an earlier one. Every entry records author session/agent, timestamp and optional bindings (PR, commit SHA, branch, worktree, lane, spec, paths, evidence file).
- **Mechanical freshness.** When the packet is built, each ledger entry is checked against current truth. A SHA-bound proof/finding is `current` only when the bound content is unchanged in the relevant paths at the current head of its branch/PR/master; otherwise it is `stale`, and the packet names the changed paths. PR-bound entries are shown with the PR's current state. Claims expire when their process is gone or their TTL passes. Superseded entries drop out of the packet. Anything that cannot be checked is labelled `unverified`. The packet also flags ledger/authority contradictions, lanes without a live process or completion marker, maintainer prompts that Relay recorded but the ledger did not, and a `PROGRESS.md` written after the ledger.
- **Authority framing.** The packet states when and how authority was verified, or that it could not be (offline, `gh` unavailable). It never presents last-fetched state as current. It labels ledger text and worker reports as historical claims by named authors, not instructions.
- **Existing owners stay where they are.** Agent Relay remains the session launcher/transcript owner and is only read: session liveness and verbatim maintainer prompts. Relay is not modified. Second Brain remains product retrieval over repository/canonical state. Hermes remains the product agent runtime. `jarvisctl` remains the workstation service tool.

## Accepted capability

1. `recover` prints the recovery packet (human text by default, `--json` for tools). Default size is at most about 3,000 tokens, with explicit truncation counts and drill-down commands. It completes in seconds on this workstation and degrades truthfully when offline.
2. `note`/`directive` append validated entries. They reject oversized text and text that matches credential/secret patterns. They never touch Git, GitHub or the repository working tree.
3. `show`, `lanes` and `search` give bounded drill-down into one entry, the full lane table, and a plain-text search over ledger entries, recorded directives and lane reports, returning paths as provenance.
4. The bootstrap pointer is one line in `CLAUDE.md` and one line in the protocol's minimal-startup section. Both say the packet is derived orientation that never outranks the canonical sources above it.

## Non-goals and boundaries

- No modification of Agent Relay, no Relay plugin/hook, no MCP server, no Hermes routing, no Second Brain ingestion of control-room material, no vector index, no model-generated summaries in the packet. PARK: a thin MCP wrapper or session-start hook calling the same CLI if a client lacks a shell; indexing ledger/reports as a Second Brain owner if the corpus outgrows plain search.
- The tool performs no GitHub mutation, no push/merge/checkout/reset and no process control. Its only repository side effect is an optional `git fetch`. The ledger and directive copies live outside the repository and the JarvisOS data root, and are never committed.
- Worker output is never auto-promoted. Only an explicit `note` records a finding/decision, and `proposed` stays distinct from `accepted`.
- No product/backend code, API, schema or frontend change. No governance change beyond the two pointer lines.

## Required evidence

- Deterministic offline tests over temporary Git repositories and fixture control rooms, covering: SHA-bound proof current / stale after a relevant change / still current after an unrelated change or a content-identical rebase; supersession; claim expiry; lane states (running, done, incomplete/abandoned, empty report); ledger/PR contradiction; unrecorded Relay prompt; `PROGRESS.md` newer than the ledger; offline/`gh` failure framing; missing ledger (repository-only packet); secret rejection; packet size bound.
- Real acceptance on this workstation. During real 154 work, record decisions, findings and an expensive proof across more than one worker. Terminate the coordinator. Start a genuinely fresh coordinator given only a minimal recovery instruction. It must independently verify GitHub/master, correctly identify active and finished work, not rerun the completed proof, name the dependency-valid next task, and separate historical from current claims. Measure bootstrap tokens, time to first useful action, and incorrect/stale recovered claims, and compare them with the measured pre-154 recoveries. Run the same packet through at least one non-Claude agent to show vendor portability.
- A failure-scenario matrix exercised against the real control room: coordinator death, new Relay session, network loss, provider switch, stale Git state in old notes, a worker report that conflicts with master, a proof whose code later changed, an incomplete lane, two contradictory findings, and missing local history with GitHub intact.

## Completion

A fresh coordinator recovers the relevant development state from one command with minimal maintainer handholding. Every recovered claim is either freshly verified or explicitly marked historical/stale. The registry and PR association are reconciled after merge.
