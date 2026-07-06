# BLUECAD — Conversational Design Layer & Self-Extending Vocabulary

Status: north-star design (v0.1, 2026-07-04, Fable 5)
Relates to: `BLUECAD_CORE_DESIGN.md` (the loop, validators), specs 010 (loop),
011 (review panel), 012 (L2 scripts), 016 (runner extension), 037 (chat entry;
renumbered from 018 — that number is now taken by the merged
provider-gateway-v2 spec),
`JARVISOS_CORE_TEAM_V1.md` (personas). This doc unifies them into one product
arc. It is a direction, not a slice; slices are listed at the end.

## The observation that motivated this

The alpha loop is one-shot: a free-text brief → a GeometrySpec → validated
geometry. It works, and it degrades honestly (a brief asking for a "sliding
toroid" produced a valid tube and dropped the toroid it could not express).
But two limits surfaced:

1. **One-shot briefs can't refine intent.** The user cannot reason *with* the
   system about what the design should be before geometry is generated.
2. **The vocabulary is fixed.** Seven part kinds. The "sliding toroid" is
   BlueRev's anti-fouling collar — a part kind that does not exist yet, so the
   system can only approximate or drop it.

The target addresses both: a **conversational design phase** in which the user
and the AI reason about the design, and a **self-extending vocabulary** so the
system can grow new part kinds when the design needs them.

## Part A — the Conversational Design Layer

A two-phase model, on top of (not replacing) the deterministic loop:

```
  PHASE 1 — CONVERSE (advisory)                 PHASE 2 — GENERATE (deterministic)
  ┌───────────────────────────────┐            ┌──────────────────────────────┐
  │ user ⇄ AI design conversation │  approve   │ GeometrySpec → build →       │
  │ • clarifying questions        │ ─────────▶ │ validate → GLB  (the 010     │
  │ • honest vocabulary awareness │  a chosen  │ loop, unchanged)             │
  │ • drafts a structured brief   │  brief     │                              │
  │ • Core Team critique          │            │ validators remain the        │
  └───────────────────────────────┘            │ deciding authority           │
```

The conversation's job is to turn vague human intent into a **well-formed
request** — not to produce geometry. Concretely the chat:

1. **Asks clarifying questions.** "Is the toroid fixed or does it slide? What
   is it for?" Intent is captured, not guessed.
2. **Is honest about the vocabulary.** It knows the seven kinds and their
   limits, and says plainly what is expressible, what it will approximate, and
   what has no representation yet — instead of silently degrading.
3. **Drafts a candidate brief / GeometrySpec** and shows it for approval.
4. **Invokes the Core Team** as design voices (Tony proposes, Sheldon
   critiques, Isaac sanity-checks physics/units, Spock frames trade-offs) —
   this is the multi-agent design review made real, and the first genuine use
   of `JARVISOS_CORE_TEAM_V1.md` + the panel (011).
5. On the user's approval, hands the brief to the **existing validated loop**.

**Safety is preserved exactly.** The chat proposes *intent*; the deterministic
builders + validators still decide on *geometry*; the human still promotes a
valid candidate to a Decision. Nothing conversational becomes CAD without
passing the same gates. The conversation is advisory all the way down.

## Part B — Self-Extending Vocabulary (the delicate part)

The user's goal: when the design needs a part kind that does not exist (the
collar), the AI should be able to **extend the vocabulary itself**, not just
flag it for a human to hand-code. This is powerful and correct in spirit — but
"the AI mutates the trusted vocabulary" is precisely the kind of thing that can
poison the foundation everything else builds on. The trusted builders are the
bedrock: a single bad auto-added part kind would silently corrupt every future
design that uses it. So it must be gated by the same principle as everything
else: **the AI drafts; deterministic validation + a human promote decide.**

Three levels, from safest to most powerful:

| Level | What the AI does | Permanence | Gate | Status |
| --- | --- | --- | --- | --- |
| **L-eph** | Writes a build123d script for the novel part, for THIS design only | ephemeral (one candidate) | sandboxed runner + the same Tier 0/1 validators (watertight, ports, volume) | **already designed** = L2 scripts (spec 012), needs runner-ext (016) |
| **L-prop** | Drafts a *candidate builder* for a new named kind (e.g. `collar`): code + param schema + a proposed golden fixture | proposed, not yet trusted | validated across a param range (property-based, like slice 022) + Core Team code review; **the human promotes it into the vocabulary** | new arc (below) |
| **L-auto** | Adds part kinds to the trusted vocabulary with no human gate | permanent, unreviewed | none | **NOT RECOMMENDED** — see risk R1 |

Recommended path: **L-eph gives you self-extension now-ish** (the AI already can
express arbitrary geometry via a sandboxed, validated script — the collar just
becomes an L2 script for that design). **L-prop gives durable growth safely**
(the AI proposes a reusable `collar` kind; it is validated and human-promoted
into the permanent set, after which it is as trusted as `tube_run`). This gives
the user exactly what they want — the AI grows the vocabulary from within a
conversation — while keeping the trusted core deterministic and auditable.

**Why not L-auto.** The whole engineering-trust story rests on the builders
being deterministic, reviewed, clean-room code. An AI silently writing new
trusted builders means: unreviewed code becomes the foundation of every
downstream design and every FEM/CFD result; a subtle geometric bug propagates
invisibly; and the clean-room/licensing guarantees can no longer be asserted.
The promotion gate is cheap (one human review of a small builder) and it is the
only thing standing between "self-extending" and "self-corrupting." Keep it.

### How a collar actually gets added, end to end
1. Chat: user asks for a sliding collar. AI recognizes no matching kind.
2. AI offers: "I can (a) approximate it as an oversized ring for this design
   now [L-eph script], or (b) propose a reusable `collar` part kind."
3. If (b): AI drafts `collar` builder + params + a golden fixture; it runs
   through property-based validation (watertight, ports, volume vs analytic
   torus); the Core Team reviews the code; the reviewer-owned conformance
   pattern applies.
4. Human promotes → `collar` joins the vocabulary; the prompt template gains
   one kind; every future design can use it.
The AI drove the extension; determinism and a human kept it safe.

## How it maps to what already exists

- **The loop (010)** is Phase 2, unchanged.
- **L2 scripts (012) + runner-ext (016)** are L-eph — the ephemeral
  self-extension mechanism, already specced.
- **Chat entry (037)** grows from "chat creates a candidate" into the Phase-1
  conversation surface.
- **Review panel (011) + Core Team** become the design voices in the chat and
  the code reviewers for L-prop proposals.
- **Provider gateway (015)** is a prerequisite: a chat that asks good
  clarifying questions and drafts specs wants strong models (DeepSeek/GLM/
  frontier), which 015 unlocks.
- **Property-based testing (022)** is the validation muscle for L-prop.
- **The green mockup** (JarvisOS shell, central CAD workspace, right-side
  multi-agent chat) is this layer's eventual UI.

## Incremental slices (rough arc, post-alpha)

1. **030 — Conversation v0**: a chat tied to a project/workspace that turns a
   multi-turn conversation into a drafted GeometrySpec the user approves before
   the loop runs (single model; builds on 037). No vocabulary changes.
2. **031 — Vocabulary-aware chat**: the chat is given the live part-kind
   catalog + limits, and explicitly reports expressible / approximate /
   impossible for each request.
3. **012 + 016** (already specced): L-eph — L2 scripts for novel geometry in
   one design.
4. **032 — Core Team in the loop**: personas critique the drafted design in the
   conversation (consumes 011 + the roster).
5. **033 — L-prop, propose-a-kind**: AI drafts a new part-kind builder +
   fixture; property-based validation; human promotion flow. The durable
   self-extension, human-gated.
6. UI arc (020-series) folds the conversation + CAD viewer into the workspace
   shell.

## Non-goals and risks

- **R1 (highest): autonomous mutation of the trusted vocabulary (L-auto).** Do
  not let the AI add trusted builders without human promotion. Mitigation: the
  L-prop gate; builders live in reviewed code; promotion is a human Decision.
- **R2: the conversation becoming an authority.** The chat is advisory; it
  never bypasses the validators or auto-promotes. Same invariant as the loop.
- **R3: L2 / proposed-builder code is AI-written and executes.** Mitigation:
  the sandboxed runner (016, AST allowlist), reviewer-owned conformance, and —
  for promoted kinds — human code review. Clean-room: generated builders target
  documented build123d API only.
- **R4: scope creep into a general CAD chat.** Keep it domain-anchored
  (floating tubular photobioreactor) and vocabulary-bounded; growth is
  deliberate part-kind additions, not open-ended.
- Non-goal: replacing the deterministic loop. The conversation feeds it.
- Non-goal: real-time multi-agent swarm before the backend supports it (UI
  first, orchestration later — the Core Team plan already says this).

## One-line summary

Add a conversational phase that turns human intent into a validated brief, and
let the AI **draft** vocabulary extensions (ephemeral L2 scripts now; proposed,
human-promoted part kinds later) — while the deterministic builders, validators,
and human promotion remain the only authorities. Self-extending, never
self-corrupting.
