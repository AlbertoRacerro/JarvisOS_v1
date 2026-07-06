# JarvisOS — Senior handoff

Status: written 2026-07-06, on the reviewer's last day. Not a roadmap — the
backlog owns that. This is the judgment that produced the roadmap, written
down so it survives the person.

## The one thing

JarvisOS wins on a single property: **every claim is one click from its
evidence, and every irreversible action passed a gate.** Not bigger models,
not more agents, not a prettier UI. A thesis defense and an investor pitch
are both traceability under hostile questioning — that is what BlueRev needs
and what no general coding agent provides. Every slice should be judged by
whether it strengthens that property. When the Mark-1's tube diameter can be
justified, one click deep, from chat to decision to calc to FEM verdict —
JarvisOS works. That is the acceptance test for the whole project.

## The five judgment rules (the constitution behind AGENTS.md)

1. **Blast-radius determinism.** Hard, fail-closed gates only where failure
   means data escape, money spent, or something irreversible. Everywhere
   else — quality, context selection, model choice — trust semantics and
   test lightly. Do not let safety rhetoric creep into gating *quality*;
   that way lies a system too annoying to use.
2. **Carrying capacity is ~2-3 slices in flight.** The backlog is a queue,
   not a promise. The most valuable output of any planning session is what
   got *rejected*. When research (or enthusiasm) proposes fifteen feature
   clusters, the correct response is a decision matrix and a short "no" list
   — this happened once (Deep Research, 2026-07) and will happen again.
3. **Trigger-gated deferral.** Nothing gets built "because we'll need it."
   Every deferred item carries a pre-declared trigger, written down:
   the knowledge graph waits for recurring multi-hop queries against the
   flat ledger; a formal benchmark waits for golden traces to plateau;
   swarm L5 waits for the memory spine surviving a month of real use. If a
   deferred item has no trigger written next to it, that is a bug.
4. **Proposals, never authority.** Model output becomes project state only
   through promotion (explicit click or pre-declared deterministic policy).
   Auto-promotion starts disabled and earns categories one at a time. When
   one-click promotion becomes annoying, the fix is better approval packets
   — never removing the gate.
5. **Dogfood is the research instrument.** Real BlueRev work flowing through
   the system generates the only pain data that matters. Every week of
   meta-infrastructure built without dogfooding is a week optimizing for
   other people's problems. When in doubt between building and using: use.

## The process that works (keep running it)

The loop that produced specs 040-044 in one day, verified and reviewed:

```
backlog row → kernel (binding decisions; frontier judgment, expensive)
           → draft (workhorse model; cheap, parallel)
           → expert review (decisions written INTO the file)
           → ready → Codex implements → tiered review (017 chain) → merge
```

What makes it work, in order of importance:

- **The kernel carries the judgment.** A drafting prompt must contain the
  binding decisions inline, numbered, plus: a required-reading list, binding
  non-goals, "verify every claim against the actual code," and "stop and
  report on conflict — do not guess." Given that, a workhorse model drafts
  as well as a frontier model; the quality bottleneck is the kernel, not
  the drafter.
- **Review decisions become text in the file** — a dated "Review
  resolutions" section, plus surgical edits wherever the body was binding
  and wrong. A decision that lives only in chat does not exist.
- **Drafters are graded on what they refuse to invent.** The best moments
  of the 040-044 batch were agents stopping: "SQLite can't add this FK",
  "this enum doesn't contain that value", "this function has no caller."
  Reward that behavior in prompts; it is the whole point.

## The traps I watched happen (they will happen again)

1. **Stale-branch blindness.** Twice in one week the reviewer (me) made
   confident false claims — "009 is not implemented" — because analysis ran
   on a branch behind master. Rule: before any status claim, `git fetch`,
   compare against `origin/master`, and grep the spec files' own `Status:`
   lines. Never trust the README index or the backlog tables without
   checking; they are caches, and caches go stale.
2. **Exists ≠ wired.** `mesh_adapter.py` and `fem_adapter.py` exist, are
   tested, and as of 2026-07-06 are called by *nothing* in routes or the
   loop. A capability is not real until something invokes it. Before
   declaring anything done, ask: who calls this? (The wiring of mesh+FEM
   into the candidate/attempt loop is the highest-value missing slice on
   the physical path — a natural 038/039.)
3. **Numbering drift.** Three collisions in one week (017 twice-assigned,
   030-033 double-booked, 018 taken by a merged spec while the backlog
   still used it). The Reserved-numbering section in PROGRAM_BACKLOG.md now
   exists: extend it *every time* a number is claimed, and reconcile the
   README index after every merge. Living documents lie unless actively
   reconciled.
4. **Drafting agents soften hard dependencies.** Left alone, a drafter adds
   fallbacks and stand-in implementations "so tests don't block." Review
   specifically at dependency boundaries; a hard dependency with a soft
   fallback is not a dependency.
5. **Docs describing desire as fact.** Several strategy documents narrate
   target state in the present tense. When doc and code disagree: code
   wins, the doc gets a dated erratum, and nobody edits history silently.

## The map as of 2026-07-06 (so nobody re-derives it)

- **Implemented** (pending review at various stages): 001-008, 009 (adapter
  only — unwired, see trap 2), 010, 015+018 (provider gateway v1+v2), 017
  (three-tier review chain).
- **Ready queue, in dependency order**: 040 + 016 (parallel, launchable
  now) → 042 → 041 → 043 → 044. The consumers (041/043/044) must wait for
  their producers (040/042) to *merge*, so they are written against real
  function signatures, not review prose.
- **After that**: mesh+FEM wiring into the loop (to be specced), 037 chat
  entry, 034 personas, 011 panel — and only then, gated on a month of
  memory-spine dogfood, real orchestration (L5).

## For the maintainer

Your scarce resource is attention, and the system is designed to spend it
only at three points: promotion clicks, ARCH-prefixed findings, and merge
decisions. If any process starts consuming your attention outside those
points, that is a bug in the process — fix the process, do not become the
process. You do not need to become a programmer for JarvisOS to succeed;
you need to keep the constitution, feed it real BlueRev work, and keep
saying no in planning sessions. The invariants in AGENTS.md are the
project. Everything else — including any particular reviewer — is
replaceable.
