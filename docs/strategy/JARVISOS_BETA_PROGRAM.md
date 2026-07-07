# JarvisOS — Beta program (ordered)

Status: living document (created 2026-07-07; revised 2026-07-07 after expert
review — scene-2 scope, SC-1 amendment path, 051/052 status, drafting-order
fixes). Purpose: the single ordered
backbone from "the memory/swarm spine specs (040-044) are ready" to a beta
that is both usable and credible. Every item has a number, a one-line scope,
its dependencies, and — for deferred items — the pre-declared trigger that
promotes it. Full specs are drafted in dependency batches from this index;
this document is the queue and the ordering, not the specs themselves.

Relates to: `PROGRAM_BACKLOG.md` (the broader queue; this doc is the
beta-focused slice through it), `JARVISOS_SENIOR_HANDOFF.md` (the judgment
rules this ordering obeys), `bluerev-process-workbook` memory (the Excel v0.9
that seeds the process-model specs), `BLUECAD_CONVERSATIONAL_DESIGN_LAYER.md`
(the chat/flowsheet north star).

## What "beta" means (the gate — three scenes, not a checklist)

Beta = you, alone, do real Mark-1 work end to end without ever touching an API
by hand or opening the DB with an external tool — and you trust the numbers.
"Figa" and "ben funzionante" are the same property seen from two sides:
conversation + 3D at the center; every number one click from its evidence.

1. **Design a part in chat** → decision with alternatives auto-proposed to
   memory → calc script produces the numbers → CAD builds → mesh+FEM verify →
   verdict lands as evidence → you promote. All without leaving the home.
2. **The FEM fails** → the panel explains why in three voices → an alternative
   is proposed as a promotable proposal with its reasoning. (The built variant
   and side-by-side 3D compare are 046 — trigger-gated, deliberately outside
   the beta gate: the gate demands explanation + proposal, not the full loop.)
3. **One click** → a dossier of the decision→evidence chain, ready for the
   thesis advisor or an investor.

When the three scenes run on *real* BlueRev work (not fixtures), with the
alpha gate green, the FEM + process verification batteries green, and a
backup restore proven at least once — that is beta.

## Seam contracts (binding — read before drafting any spec below)

Individual specs can each pass CI and still leave the system disconnected
(the handoff's "exists ≠ wired", applied at planning altitude). These four
contracts fix the integration seams up front so the specs converge instead of
each inventing its own edge. They are design decisions, not implementation
slices — but every spec below must honor them.

### SC-1 — Unified provenance contract (the flowsheet's foundation)

Three specs already emit provenance in three shapes: calc parameters carry
`source_ref='runner_job:<id>'` (string, spec 043/040); evidence records carry
`source_run_id`/`candidate_id`/`attempt_id` (FKs, spec 044); chat decisions
carry `source_ai_job_id` (spec 041/040). The flowsheet (050) must rebuild
**one** dependency graph from **three** provenance forms.

Binding decision: a normalized provenance reference is a
`"<kind>:<id>"` string — `ai_job:<id>`, `runner_job:<id>`, `sim_run:<id>`,
`candidate:<id>`, `attempt:<id>`, `evidence:<id>`, `<record_kind>:<id>`. Every
provenance-bearing write in Phases B/C/F stores at least this normalized form
(existing typed FK columns may remain alongside it for referential use).
Spec 050 owns the resolver that walks these references into a DAG — it is not
a new engine, it is a parser over a shared string convention. Specs 047-049
and 044 must be drafted to emit this form; 040's existing `source_ref` already
matches it and is the template. **This contract must be settled before 047 is
drafted** — it is the one seam whose drift is expensive.

Action (2026-07-07): 044 is already `Status: ready` with typed FK columns
only — before 044 is implemented, amend it with a dated review resolution so
evidence writes also store the normalized `<kind>:<id>` ref alongside the
FKs. Records written by 040/041 predate the convention (`source_ai_job_id`
is a bare id, not `ai_job:<id>`): the 050 resolver normalizes those legacy
columns at read time. One string convention plus one documented legacy
mapping — still a parser, not two engines.

### SC-2 — The promotion surface has an owner (spec 054)

Invariant 8 (proposals, never authority) means the user's promote/reject click
is the load-bearing moment of the whole system — the handoff names it as one
of only three places the user's attention is spent. Today 040 owns the
endpoints and 041 creates the proposals, but **no spec owns the UI where the
user sees a proposal with its provenance and clicks promote**. That surface is
spec 054 (below), not an afterthought folded into the navigator.

### SC-3 — The project aggregate view has an owner (spec 055)

Everything is workspace-scoped, but no spec assembles "the Mark-1 as one
object" — its decisions, calcs, CAD, evidence, and flowsheet in one navigable
place. Without it, JarvisOS is four tables, not the place BlueRev lives. That
view is spec 055 (below).

### SC-4 — Navigator and flowsheet are designed together

Spec 035 (record navigator) is numbered before 050 (flowsheet) but must be
**designed flowsheet-aware**: it renders records that will later carry
dependency edges. If 035 is built assuming flat records, it is rebuilt when
050 lands. The two share a display contract even though they implement at
different times — 035's record view must leave room for a "depends on / feeds"
affordance rather than hard-coding a flat list.

## Phase A — close and harden the physical loop

The loop that already builds + validates geometry must also simulate and
record, deterministically.

| # | Scope | Depends on |
| --- | --- | --- |
| 038 | SIM-WIRE: call mesh (008) + FEM (009) adapters inside the candidate/attempt loop; outcomes land in `evidence_records` via 044's hooks | 044, and 008/009 already implemented (currently unwired) |
| 021 | ALPHA-GATE: one CI-runnable script brief→build→validate→mesh→solve→artifacts asserting the outcome; plus data-root backup with a proven restore | 038 |

Note (2026-07-07): 021 now depends transitively on the memory spine
(038 → 044 → 042). Deliberate — the gate asserts the physical loop
*including* evidence records — but it redefines "alpha gate green" relative
to the older Horizon-2 meaning in `PROGRAM_BACKLOG.md`, which predates the
spine.

## Phase B — the process model (the Excel becomes code)

The ~21 ranked calc candidates from the BlueRev workbook (18 stable + 3
proxies, ranks 19-21) become 3 specs, not 21. Each ports the workbook's math
**with the model bugs corrected** (never a
straight copy) and ships a process verification battery (literature values),
the twin of the FEM battery (024). All depend on 043 (the `calc_v0` runner)
being merged.

| # | Scope | Depends on |
| --- | --- | --- |
| 047 | BLUEREV-PROCESS-0: geometry + hydraulics + pump nodes (workbook ranks 1-7). Fixes: separate internal hydraulic S/V from illuminated external area; separate tube residence time from full-loop turnover | 043 |
| 048 | BLUEREV-PROCESS-1: biomass + nutrients + gas stoichiometry + harvest + pump energy/cost KPIs (ranks 8-18). Fixes: explicit `productive_volume` (not total incl. dark reservoir); resolved recovery mass-balance convention; every incomplete KPI honestly named (pump-only, not total) | 043, 047 |
| 049 | BLUEREV-PROCESS-2: basic buoyancy + transmittance/light-center proxies (ranks 19-21). Buoyancy includes hardware mass + safety factor; light proxy takes explicit `path_length` (not diameter); both marked proxy and feeding FEM/flagging the light-model gap | 043, 047 |

Binding mandate for Phase B: the workbook is a v0.9 draft with known
definitional bugs (productivity on dark volume → ~35% overestimate; recovery
double-count; light path = full diameter). Porting means **correcting and
recording the correction as a traceable decision**, not reproducing the bug.

## Phase C — the flowsheet (the graph that ties the nodes)

The `parameters` produced by Phase B are already the nodes; `calc_v0`'s
`source_ref` is already the provenance. This phase makes the graph explicit
and then alive. This is the materialized-graph trigger from the handoff —
with one honest caveat: the trigger is pre-fired on *predicted* pain (Phase
B's multi-hop provenance queries are certain, not speculative). A recorded
exception to the observed-pain rule, not an application of it.

| # | Scope | Depends on |
| --- | --- | --- |
| 050 | FLOWSHEET-1: the parameter dependency DAG as data, derived from provenance; inspectable, no recompute engine. **Owns the SC-1 provenance resolver** (parses `<kind>:<id>` refs into the graph) | 047, 048 |
| 051 | FLOWSHEET-RECALC: stale propagation — change an input, mark dependent outputs stale; deterministic, testable | 050 |
| 052 | CAD-LINK: flowsheet geometric outputs (diameter, length, tube count) → CAD GeometrySpec inputs; FEM verdicts return as evidence constraining upstream nodes. "The reactor draws itself from the calculations" | 050, 038, 005 |

## Phase D — the face

| # | Scope | Depends on |
| --- | --- | --- |
| 037 | Chat entry point → workbench (creates a candidate) | 042 |
| 030 | Conversation v0: multi-turn → drafted GeometrySpec you approve → loop runs | 037 |
| 029 | R1 settings & secrets page (backend surface exists) | none |
| 020 | R2 workspace home: workbench + right AI chat + status strip; design tokens v0 | 029 |
| 035 | R3 Domain Foundation navigator: search/filter/edit over records — **flowsheet-aware per SC-4** (record view leaves room for depends-on/feeds edges, not a hard-coded flat list) | none |
| 054 | PROPOSAL-REVIEW UI (SC-2): the promote/reject surface — proposed records shown with provenance, one-click promote/reject over 040's endpoints; the load-bearing user moment | 040, 041, 020 |
| 055 | PROJECT-VIEW (SC-3): the Mark-1 as one navigable object — its decisions, calcs, CAD, evidence, and (when it lands) flowsheet in one workspace surface | 035, 044 |

## Phase E — the voices (honest swarm, not fake)

| # | Scope | Depends on |
| --- | --- | --- |
| 034 | AGENT-CORE: personas as config (roster frozen) | none |
| 011 | Review panel: personas critique artifacts, advisory | 034 |
| 039 | FRONTIER-1: Anthropic adapter + `external:frontier` for the hard loop steps | 015/018 |
| 036 | R5 multi-agent chat UI, honest advisory badges | 020, 034 |

Beta does NOT need real orchestration (045) or the alternative loop (046) to
feel like a swarm — it needs the panel to explain a FEM failure in three
voices. 045/046 stay trigger-gated (below).

## Phase F — credibility and the distinctive move

| # | Scope | Depends on |
| --- | --- | --- |
| 024 | FEM verification battery (cantilever, Lamé, Kirsch plate-with-hole vs analytic; beam-frequency case deferred, gated on 027 — erratum 2026-07-07, see spec 024) | 009 |
| 023 | Adversarial proposal corpus for the 010 loop (hostile/degenerate LLM output must park cleanly) | 010 |
| 053 | DECISION-PACKET + dossier export: decision-class outputs as typed artifacts (recommendation, alternatives, evidence, assumptions, uncertainty); one click → readable dossier of the decision→evidence chain | 041, 044, 048 |

053 is the distinctive move: no coding-agent competitor has it, and for
BlueRev it is a thesis-chapter / due-diligence generator. It is the handoff's
"one claim, one click from its evidence" made a product.

## Deferred research track (NOT specs — trigger-gated)

The coupled core of the process model — the physics the workbook fakes. Each
promotes only when its measurement exists (the workbook's `30_To_Measure`
sheet already lists these).

| Item | Promotes when |
| --- | --- |
| Calibrated light-attenuation model (Lambert-Beer with real `k_att`, explicit path) | `k_att` measured vs biomass concentration |
| Productivity as f(light, temperature, X) | light model exists + PAR/site irradiance input available |
| kLa gas transfer + DO profile along the loop | DO build-up measured along loop/degasser |
| Thermal balance with seawater sink | site/seawater thermal data + tube absorption basis |
| Structural wave/current/mooring loads | Mark-1 leaves sheltered water for open sea (today's scope is a sheltered module) |

Also trigger-gated: 045 (real orchestration — after the memory spine survives
a month of dogfood); 046 ALTERNATIVE-LOOP (FEM fails → panel critiques →
alternative variant built → side-by-side compare; deps 038, 011, 006b — was
listed in Phase F, moved here 2026-07-07 to resolve the contradiction with
the scene-2 gate; promotes after 011 proves useful in practice; note 006b
enters the beta path only through 046); escalation of 051/052 *beyond their
v0 slices* (after the flat DAG is used and found wanting — the v0 slices
themselves are Phase C and in the beta; 052's calc→CAD link is gate-critical
for scene 1).

## Reserved numbering (extends PROGRAM_BACKLOG.md)

- 038: SIM-WIRE; 039: FRONTIER-1 (renumbered from 019 — that number is taken by
  the merged senior-review-hardening spec).
- 045: AGENT-ORCH (memory/swarm block); 046: ALTERNATIVE-LOOP (memory/swarm block).
- 047-049: BLUEREV-PROCESS-0/1/2 (process model from the Excel workbook).
- 050-052: FLOWSHEET-1 / RECALC / CAD-LINK.
- 053: DECISION-PACKET + dossier export.
- 054: PROPOSAL-REVIEW UI (SC-2); 055: PROJECT-VIEW (SC-3).

Authoritative registry: the Reserved-numbering section of
`PROGRAM_BACKLOG.md` — claim numbers there first; this list is a convenience
copy, reconciled after every change.

## Drafting order (how this index becomes specs)

Full specs are written in dependency batches, 2-3 in flight (handoff carrying-
capacity rule), never all at once. **Settle SC-1 (the provenance contract)
before drafting 047** — it is the one seam whose drift is expensive. Natural
batch order after the current implementation queue (016→040→042→041→043→044)
lands:
**038+021+024 → 047 → 048+049 → 050 → 051+052 → 037+029 → 030+020 →
054+035+055 → 034+011 → 053 → the rest.**
024 rides in the first batch: it depends only on 009 (implemented), touches
nothing else, and the beta gate requires it green — no reason to queue it.
029 is drafted before 020, which depends on it. 051+052 follow 050 directly
because 052's calc→CAD link is gate-critical for scene 1. 054 (promotion UI)
is drafted in the batch after 020 so it is written against real design tokens
and layout — producers merge before consumers are drafted — but stays ahead
of the voices/dossier work, because the promote/reject click is what makes
every proposal-writing spec upstream actually usable. Each batch is drafted
(workhorse), expert-reviewed (decisions written into the file), set `ready`,
then implemented.
