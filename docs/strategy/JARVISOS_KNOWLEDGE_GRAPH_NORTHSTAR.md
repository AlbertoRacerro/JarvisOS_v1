# JarvisOS Knowledge Substrate — North Star (PKG)

Status: north-star + decision record (v0.1, 2026-07-04, Fable 5)
Verdict: **direction accepted; do NOT write an implementation spec now.** This
is a kernel + trigger, not a ready slice — consistent with the precision ladder
in `PROGRAM_BACKLOG.md` (backlog → kernel → spec). Prompted by a proposal to
adopt Graphify (a Claude-Code code knowledge-graph tool, "70x on large repos").

## The claim, honestly

Graphify-style tools build a persistent representation of a codebase (graph +
embeddings + AST) so an agent does deterministic, targeted retrieval instead of
re-reading the repo every session. The "70x" figure is real in a narrow sense
and misleading in general: it measures an agent's **re-orientation cost** on a
large repo across many sessions, is usually author/community-benchmarked, and
scales with repo size. It does not make the model reason better. On a small
repo the gain is modest; on a growing one it becomes real.

## The distinction the proposal blurs (the crux)

There are **two different graphs**, and conflating them is the main error:

1. **Code knowledge graph** — files, classes, functions, tests, commits. A
   *developer-tooling* index that helps an agent navigate source. This is what
   Graphify is.
2. **Domain / project knowledge graph (the "world model")** — models,
   assumptions, parameters, simulation runs, decisions, sensitivity/IP, costs,
   dependencies. This is JarvisOS's *product substrate*, not dev tooling.

JarvisOS **already has the seeds of #2**: the Domain Foundation
(`workspaces`, `modeling`, `engineering` modules; the `EntityLink` graph;
ModelSpec / Assumption / Parameter / SimulationRun / Decision). The BLUECAD
candidate/attempt ledger and Decisions extend it. The genuinely strategic prize
— "closer to your world-model idea" — is #2, and it is an **incremental
extension of something that already exists**, not a new Graphify install.

## Who consumes it — and why NOT now

Retrieval infrastructure is worthless without a consumer, and building it before
the consumer exists means building the wrong retrieval (you don't yet know the
queries).

- **Code-KG consumers = agents that navigate JarvisOS's own source.** Today that
  is **Codex Cloud** (which has its *own* indexing/context and clones the repo)
  and **Claude review** (its own context window, targeted file reads). Neither
  would query a JarvisOS-internal code graph. JarvisOS has **no internal
  code-navigating agent yet**. So a code-KG built now speeds up nobody.
- **Domain-KG consumers = the conversational design layer + Core Team agents**
  (`BLUECAD_CONVERSATIONAL_DESIGN_LAYER.md`, slices 030+) and the future agent
  swarm. These **do not exist yet**; they arrive after 015 (real models) and the
  conversation slices. When they do, they will query domain knowledge (past
  designs, decisions, parameters) far more than source code.

Conclusion: the acute bottleneck today is *not* re-reading the repo. It is the
AI-CAD loop maturity, the provider gateway (015), and vocabulary. A persistent
knowledge graph is a high-value *future* investment aimed at consumers that are
still on the roadmap. Building it now is premature optimization of retrieval.

## Recommended shape — two tracks, when the time comes

**Track A — Domain/world-model graph (the real prize).** Do NOT big-bang it.
Extend the existing Domain Foundation *incrementally, pulled by each consumer*:
when the conversational layer needs "have we designed a manifold like this
before?", add that query and the edges it needs. The graph grows to fit real
queries instead of being speculated up front. This is the path to the world
model, and it is already underway in spirit.

**Track B — Code-KG (Graphify-style).** Defer until BOTH: (a) JarvisOS has an
internal agent that repeatedly navigates its own source, AND (b) profiling
shows re-orientation is a measured cost. Then adopt Graphify **or equivalent as
an index layer** behind a retriever — never as a source of truth. Prefer a
provider-agnostic, self-hostable approach (works for Codex/Claude/Qwen/Gemma
alike) over a tool coupled to one agent.

## Kernel (binding IF/WHEN either track is built)

1. **The graph is an index, never an authority.** Source code and canonical
   records (DB, Decisions, artifacts) are the truth. The graph accelerates
   retrieval; it never *decides*. Same invariant as everything else in JarvisOS
   (validators/records decide; advisory layers advise).
2. **Staleness is assumed.** Incremental update on changed files/records; any
   retrieval that matters is re-verified against the source before use. A stale
   graph must degrade to "re-read the file", not to a wrong answer.
3. **Deterministic retrieval.** Given the same graph state + query, the same
   result set. Auditable.
4. **Provider-agnostic.** Serves local and cloud models; not welded to one agent
   or one LLM.
5. **Sensitivity is a first-class edge, and egress-gated (critical).** A rich
   domain graph will contain BlueRev IP, costs, and decisions — i.e. S3/S4
   material. Retrieval that feeds an external model MUST pass the existing
   sensitivity/redaction gates. A knowledge graph that silently ships IP-tagged
   nodes to a cloud provider is exactly the egress leak the sensitivity taxonomy
   exists to prevent. The graph must carry sensitivity labels and the retriever
   must honor them.

## Decision / trigger to start

Start Track A's first real slice when a consumer query exists (the conversational
layer's first "recall a past design/decision" need — likely alongside slices
030-032). Start Track B only after an internal code-navigating agent exists and
re-orientation cost is measured. Until a trigger fires, this stays a north star,
not a milestone. Provisional id: **PKG-1** (Track A first).

## Non-goals / risks

- **R1: building retrieval before the consumer** → wrong retrieval. Mitigation:
  consumer-pulled, incremental.
- **R2: the graph becoming a false authority** (stale nodes trusted as truth).
  Mitigation: kernel 1+2 — index advises, source decides, re-verify.
- **R3: IP/sensitivity leak via retrieval to external models.** Mitigation:
  kernel 5 — sensitivity edges + egress gate. This is the highest risk of a
  *rich* domain graph and must not be an afterthought.
- **R4: adopting a single-agent-coupled tool (Graphify) as core infra** and
  inheriting its lifecycle. Mitigation: index-layer only, provider-agnostic,
  code stays authority.
- Non-goal: making JarvisOS depend on a persistent graph for correctness. It is
  an accelerator, removable without breaking the system.

## One-line summary

A persistent knowledge graph is a high-ROI *future* investment — but the prize
is the **domain/world-model graph JarvisOS already seeds**, grown incrementally
as its future agents ask real questions, with sensitivity egress-gated; the
Graphify-style *code* graph is deferred until an internal code-navigating agent
exists to consume it. Direction yes; implementation spec, not yet.
