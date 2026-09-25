# 150 — Second Brain operationalization

State: **ready**. This is the bounded continuation of merged 148, authorized by the maintainer's 2026-09-25 Frontier Coordinator directive. It does not reopen or change the accepted 148 result.

## Outcome

The derived Second Brain becomes a fresh, bounded navigation service over current repository and canonical product knowledge. A Frontier Coordinator and the governed Hermes runtime can ask where relevant evidence lives, receive revision/digest-bound refs, and then use exact Git/source or canonical-owner reads for authority. An index hit never promotes exploratory or stale material into engineering truth.

## Fresh baseline and dependencies

Dependencies: 148 (derived hybrid index and authoritative resolution), 117 (Brainstorm lifecycle), 118 (repository truth), 146 (Hermes runtime), and 149 (engineering operator evidence). The 2026-09-25 audit found real FTS5/BM25, optional E5 and sqlite-vec, graph/symbol/summary indexing, bounded bundle construction, and owner reread in `backend/app/modules/ai/retrieval_index.py`. `retrieval_rebuild.py` remains a manual full rebuild; the default index omits repository files; index mutations are not connected to canonical owner changes; Brainstorm is absent; and no external coordinator retrieval entrypoint calls `build_bundle` in product code. These are the specific gaps this slice closes.

## Accepted capability

1. **Repository freshness.** Persist the exact indexed master SHA and index/extraction/embedder identity. Detect master movement, including startup or offline catch-up and a query-time freshness gate. Apply `OLD_SHA..NEW_SHA` changed/added/deleted files and Python symbols incrementally, with deterministic handling of renames and stale refs. Do not re-embed unchanged files on an ordinary merge. A schema/extractor/embedder change or actual index corruption may require an explicit full rebuild. A query that cannot establish current-master freshness reports that fact and does not present old repository hits as current.
2. **Derived-index lifecycle.** Coordinate concurrent index writers with a bounded durable lock/transaction strategy; an interrupted update must either remain at the prior complete generation or recover to the new complete generation. Audit SQLite/FTS/vector/reference integrity and repair by deterministic catch-up or a justified rebuild. The retrieval index remains disposable and never becomes a canonical record store.
3. **Canonical product knowledge.** Audit useful frontend-backed canonical domains and add owner-mediated retrieval for material gaps, including Brainstorm raw capture, discussion, reconciled revisions, promotion proposals, and superseded lineage. Preserve each lifecycle state and provenance; exploratory raw Brainstorm is not a promoted engineering decision. Include relevant literature, model dossiers, project knowledge, AI interaction history, engineering studies/evidence, DWSIM/process, BLUECAD/CFD/FEM evidence where authoritative owner projections exist. Future CalculationArtifacts can join through the same contract when their owner exists; 150 does not create them.
4. **Record synchronization.** A canonical mutation has a durable change indication in its existing owner transaction or an equivalent replayable owner-owned change source. Derived upsert/delete catches up after crashes and offline periods, including summaries and relationships affected by a change. No owner writes are redirected through retrieval storage, and no generic new event bus or polling daemon is introduced merely for this index.
5. **Bounded navigation.** Expose a narrow read-only query/ContextBundle path usable by the external Frontier Coordinator and Hermes through the existing capability boundary. It enforces workspace/source scope, limits, token budget, provenance, and query-time freshness; it returns refs and inspectable evidence, not executable instructions or promotion authority. Every canonical item is authoritatively reread and revision/digest validated before use. Second Brain does not replace Git, exact source reads, canonical SQL, or solver evidence.

These capabilities may land in a small number of dependency-ordered implementation PRs under this single spec. Repository freshness/lifecycle is the first coherent repair; canonical owner coverage and the consumer path follow against its stable generation contract. The Coordinator chooses the minimum mechanism after tracing existing owners and avoiding duplicate stores, daemons, and control planes.

## Non-goals and boundaries

- No provider or Ollama call for index maintenance or deterministic retrieval. Existing AI calls still use `run_ai_task` and `ai_jobs`.
- No automatic promotion of model, Brainstorm, literature, or index text into accepted engineering state.
- No broad SQL table dump, full E5 rebuild on every merge, cloud vector database, or standalone web RAG service.
- No change to branch protection, merge authority, repository credentials, or default-branch mutation rights through the retrieval tool.
- No calculation notebook or new physical-engine solver in this slice.

## Required evidence

- Deterministic two-SHA repository tests for add/edit/delete/rename and Python-symbol deltas, no unchanged re-embedding, stale-head refusal, restart catch-up, interrupted/concurrent writer behavior, and corruption/integrity recovery.
- Canonical owner mutation/deletion and crash catch-up tests, including Brainstorm raw→discussion→reconciled→promotion/superseded lifecycle without promotion confusion; unchanged owner records retain stable refs.
- Bounded search/bundle tests across repository and selected SQL domains, with authoritative reread failure on stale/missing/digest-mismatched sources, workspace isolation, token limits, and secret-safe output.
- A real local repository and canonical-SQL navigation smoke through the external Coordinator-facing path and a governed Hermes path where capability is enabled. Report indexed SHA, corpus generation, changed-document/embedding counts, latency, recall/known gaps, and actual token estimates. Do not claim an E5 or Hermes route was exercised if that runtime is unavailable.

## Completion

The current master and selected canonical records remain navigable after ordinary merges and product mutations without a manual whole-index rebuild. An external Coordinator and Hermes can obtain bounded, fresh, authoritatively validated ContextBundle refs through governed read-only paths. The registry and merged PR association are reconciled after exact-head evidence and merge.
