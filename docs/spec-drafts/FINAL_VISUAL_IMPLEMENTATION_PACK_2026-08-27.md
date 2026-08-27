# Final visual implementation pack — draft specifications — 2026-08-27

Status: planning drafts only; not implementation authority; not a parallel queue.

## Purpose

Translate the final maintainer-approved operator experience into independently promotable backend/domain/frontend specifications without pretending the exact runtime ownership/dependency graph is already known.

These entries are deliberately **pseudo-specs**. They preserve required product behavior, acceptance intent, likely ownership and non-goals. A future authority/queue-rederivation slice must audit exact master, reconcile overlap with every semantically overlapping active/planned `STATUS.md` row and merged capability, allocate canonical IDs, and then promote each retained slice through the normal definition -> full spec -> readiness -> implementation lifecycle.

No builder may implement directly from this file.

## Global invariants for every retained slice

- Backend authority remains FastAPI + SQLite unless a later accepted spec proves another boundary necessary.
- Frontend is an operator interface and never calls providers, filesystems, shell, Git or execution tools directly.
- Model/agent output is proposal; deterministic code/policy owns validation/promotion.
- Reuse existing canonical records/events/runs/evidence/search/security boundaries before creating a new store.
- One implementation front at a time.
- No fabricated runtime state, health, validation, repository facts, semantic deltas, previews or metrics.
- Exact repository/runtime/version ownership must remain visible whenever stale evidence would otherwise be misleading.

---

# Backend/domain draft slices

## FV-B01 — PROJECT-BASIS-1

**Goal:** provide canonical project-level objective/question, requirements, acceptance criteria, stable constraints, boundary conditions, standards/regulations, global decisions and resource/capability constraints for `Memory > Project Basis`.

**Likely overlap/prerequisites:** 001, 035, 040, 050/051, 098, planned 101/102.

**Required behavior:**
- expose exact authoritative project-basis records without duplicating per-model copies;
- preserve lifecycle/provenance and source links;
- support compact read projections grouped by user-facing Project Basis sections;
- expose exact value/rule/threshold/state for deterministically evaluable criteria where underlying records support them;
- produce dependency-impact inputs for PD-07 change classification.

**Acceptance intent:** one authoritative record edited once is reflected by every model that references that basis; no frontend-only basis state.

**Non-goals:** model working revisions, solver reruns, generic document store, second requirements schema.

## FV-B02 — MODEL-DOSSIER-1

**Goal:** aggregate one exact model/version into a coherent read dossier without duplicating canonical source records.

**Required read model:** Definition; Assumptions; Methods & Equations; Parameters & Inputs; Process; BLUECAD; Results & Validation; Criticalities; Sources; Artifacts; Runs; Changelog/Lineage.

**Required behavior:**
- every result/run/artifact/validation stays bound to exact model/version identity;
- provide truthful section counts/summaries for collapsed dossier disclosure;
- support bounded pagination/filtering for large sections;
- expose current reconciled/working revision identity distinctly.

**Non-goals:** another canonical model store, global Results/Runs/Evidence destinations.

## FV-B03 — MODEL-CHANGESET-1

**Goal:** support bounded accepted change sets and inspectable working revisions such as user-facing `v13.01`, `v13.02` without in-place overwrite of the reconciled parent.

**Required behavior:**
- stable backend IDs, exact parent revision and exact change set;
- user/Jarvis proposals remain proposals until explicit approval;
- accepted batches create a new working revision atomically;
- later working revisions derive from exact selected parent;
- discard working revision without deleting historical parent/evidence.

**Non-goals:** floating-point version identity, silent mutation, branchless overwrite.

## FV-B04 — DETERMINISTIC-IMPACT-REVALIDATION-1

**Goal:** implement PD-07 impact classification for accepted Project Basis/model changes.

**Required classes:**
- re-evaluate existing outputs;
- recalculate Process;
- recalculate BLUECAD;
- recalculate multiple domains;
- no material effect when deterministically provable.

**Required behavior:** criterion/rule-only changes are evaluated immediately against exact stored outputs when sufficient; `STALE` is reserved for genuine recomputation-required cases; resulting evidence binds exact rule/basis revision and exact source outputs.

**Non-goals:** LLM confidence as validator; unnecessary expensive reruns.

## FV-B05 — MODEL-RECONCILIATION-1

**Goal:** promote a validated exact working revision to current reconciled model while preserving immutable history.

**Required behavior:**
- batch proposal approval applies only to the displayed bounded change set;
- unresolved mandatory recalculation blocks ordinary reconciliation;
- known FAIL may be reconciled only through explicit acknowledgement/policy when allowed;
- previous reconciled revision remains immutable and reproducible;
- promotion is atomic with provenance.

**Non-goals:** requiring every engineering criterion to PASS merely to record known current state; destroying old snapshots.

## FV-B06 — LITERATURE-SOURCE-1

**Goal:** structured external-source provenance for `Memory > Literature`.

**Conceptual model:** Source -> Document/imported file -> Claim or extracted Datum -> Citation/location/context -> Used-by project/model records.

**Required behavior:** preserve URL/DOI/original provenance, page/table/section when available, extracted value/unit/context/status and exact usage links; bridge existing `source_ref` rather than creating duplicate truth.

**Non-goals:** forcing backend taxonomy into compact UI labels; generic Files workspace.

## FV-B07 — PROJECT-SEARCH-1

**Goal:** unified project search across Project Basis, Models, Literature, runs/artifacts and indexed attached content.

**Required behavior:**
- extend current FTS/index infrastructure where possible;
- results return exact owner/type/path/version/provenance;
- literal and structured search first; semantic retrieval only after a bounded evidence-backed design;
- search is a read projection, never a second truth store.

**Non-goals:** vector database by default, model-generated search facts.

## FV-B08 — ROADMAP-1

**Goal:** canonical committed/planned project work model used by Timeline and Execution status.

**Required fields/semantics:** title, type, start/end, status `Planned | Ready | In progress | Blocked | Done | Cancelled`, priority `Critical | High | Normal | Opportunity`, description, domain, links, dependencies/blocks, scheduling constraints, done-when/acceptance, tags, owner, effort, progress/subtasks, resources/cost, notes/attachments, provenance.

**Required behavior:**
- same item identity across Timeline, execution snapshot and Calendar links;
- Ready means genuinely actionable according to known dependency gates where deterministic;
- transition to Done cannot silently bypass deterministic done-when conditions;
- manual items may commit directly under operator authority; Jarvis-generated items remain proposals until accepted.

**Non-goals:** separate Kanban store; Board peer page.

## FV-B09 — CALENDAR-SCHEDULING-1

**Goal:** actual hour/minute time allocation linked to Roadmap without duplicating Roadmap windows.

**Event types:** work session, call/meeting, experiment/lab, review, reminder, deadline, unavailable/personal.

**Required behavior:**
- exact start/end/date/time-zone semantics;
- zero/one/many calendar blocks may link to one Roadmap item;
- create-from-roadmap prelinks item; create-from-time-cell pre-fills selected time;
- preserve distinction `project window != scheduled effort`;
- expose planned/completed/remaining effort only when derived from real data.

**Non-goals:** replacing external calendar providers before a separate integration spec; treating every Roadmap span as occupied time.

## FV-B10 — BRAINSTORM-RECONCILIATION-1

**Goal:** non-authoritative Raw/Reconciled idea domain matching final visual direction.

**Required behavior:**
- preserve original Raw text/files;
- truthful raw states such as NEW/DISCUSSED/RECONCILED/SUPERSEDED;
- Reconciled record stores maintained discussion synthesis, decisions/trade-offs/open questions and provenance links;
- later discussion can revise an existing reconciled idea with lineage rather than create duplicates;
- explicit promotion targets Roadmap, Design proposal path or Coding development-proposal path;
- reading does not silently change Jarvis context.

**Non-goals:** old Inbox/Exploring/Candidate Kanban lifecycle; silent Memory promotion.

## FV-B11 — DEVELOPMENT-JARVIS-CONTEXT-ACTIONS-1

**Goal:** explicit multi-record context basket and bounded Jarvis actions for Development.

**Required behavior:** add/remove multiple IDEA/raw/model/literature/project references; exact context identity; Jarvis may propose reconciled-record updates, derived ideas, Roadmap items or promotions; every mutation requires explicit accepted action and stale-target protection.

**Non-goals:** implicit context accumulation from browsing; autonomous project-authority mutation.

## FV-B12 — PROVIDER-SETTINGS-GENERIC-1

**Goal:** backend read/write contracts required by final `Settings > AI` provider-agnostic UI.

**Required behavior:** general provider/integration identities, secure credential state, endpoint/config status, connection test, model/capability catalogue where supported, usage/budget state where supported; separate provider API identity from tools such as Codex/Claude Code; reuse 015/018/082/094/policy/egress boundaries.

**Non-goals:** API key per model, frontend secret storage, mandatory OpenRouter routing, Hermes authority expansion.

## FV-B13 — REPOSITORY-OBSERVABILITY-1

**Goal:** typed read-only backend facade for Coding Repository remote state.

**Required behavior:** repository identity, default/current branch, exact SHA, branches, open PRs, exact PR heads, commits, changed files, check/workflow/review state, direct GitHub URLs, safe file content/metadata fetch for approved repository scope.

**Authority:** GitHub remote remains source of truth; cache may accelerate but cannot become canonical.

**Non-goals:** frontend GitHub tokens/API calls; mutation in this slice.

## FV-B14 — REPOSITORY-INSPECTOR-1

**Goal:** search/preview service for repository-readable artifacts.

**Required behavior:**
- literal/path/ID search across Markdown/specs/code/tests/config/workflows/architecture/SVG/images where safe;
- exact ref/path/blob identity;
- type-specific safe preview payloads: Markdown source/render basis, source text, SVG/image metadata/content where safe, structured config/code text;
- direct `Open on GitHub` URL generation;
- bounded file size/type allow-list and binary handling;
- optional semantic search is separate/proof-gated and must not invent facts.

**Non-goals:** arbitrary filesystem browser, repository duplication/index store without need.

## FV-B15 — DEV-PIPELINE-STATE-1

**Goal:** persistent inspectable software-development state machine:

`Proposal -> Plan -> Implementation -> Tests -> Independent Review -> Reconciliation -> Merge`

**Required behavior:** exact repository/head at every stage; stale CI/review invalidated when head changes; deterministic gates remain authoritative; review is evidence; current builder automation may be projected/imported only through explicit adapter semantics.

**Non-goals:** magical auto-merge authority; hidden background mutation.

## FV-B16 — JARVIS-CODING-ACTIONS-1

**Goal:** bounded Coding actions behind repository authority.

**Required actions:** inspect/explain; prepare modification proposal/diff; add development proposal; plan; create isolated branch/worktree when authorized; run permitted deterministic checks; summarize/reconcile review findings; prepare PR/merge decision under canonical policy.

**Hard line:** `Suggest modification` never equals direct file mutation. Live running code is never the mutation target.

## FV-B17 — CODING-KNOWLEDGE-1

**Goal:** searchable software knowledge that explains why JarvisOS is designed as it is without duplicating repository files.

**Sources:** accepted specs, ADRs/DECISIONS, ARCHITECTURE, AGENTS/process invariants, known limitations/debt and provenance-linked lessons from superseded approaches.

**Required behavior:** exact source links/ref dates; no generated fact promoted without provenance; can combine with Repository Inspector context.

**Non-goals:** separate magical Jarvis Memory tab; broad RAG store without evidence.

## FV-B18 — LOCAL-RUNTIME-IDENTITY-1

**Goal:** truthful local runtime identity and health versus GitHub remote.

**Required behavior:** observe actual local installation/worktree path, running commit/version/branch, dirty/clean state, frontend/backend/service health, approved remote target SHA and alignment state. Never report remote latest as executed locally.

**Acceptance intent:** Runtime can prove `local actually executed SHA` and `remote latest SHA` independently.

**Non-goals:** update/restart mutation.

## FV-B19 — RUNTIME-DIVERGENCE-SUMMARY-1

**Goal:** produce evidence-backed semantic delta between local executed SHA and selected approved remote SHA.

**Required behavior:** exact commit ancestry/diff; concise summaries tied to real commits/files/specs; classify docs/reference-only vs runtime-affecting where deterministically supportable; expose underlying evidence for inspection; fail honestly on divergent/unrelated histories.

**Non-goals:** LLM-only delta presented as fact; assuming every commit is a user-visible feature.

## FV-B20 — SAFE-SELF-UPDATE-1

**Goal:** controlled exact-target update/restart with rollback.

**Required sequence:** preserve needed state -> fetch exact approved target -> dirty-worktree refusal/reconciliation -> migrations/build -> deterministic smoke -> restart -> post-restart health -> automatic rollback to known-good on failed startup/health.

**Required behavior:** exact current/target SHAs, target eligibility, state backup, migration evidence, logs and rollback identity.

**Non-goals:** blind `git pull && hope`; auto-update without operator/policy authority.

## FV-B21 — LOCAL-TERMINAL-PTY-1

**Goal:** real integrated terminal execution behind a typed local backend boundary, PowerShell-default on Windows.

**Required behavior:**
- create/close bounded PTY/session;
- set/get session working directory under allowed policy;
- execute the terminal process with a deliberately scrubbed/minimum environment that does not inherit provider API keys, repository tokens, credential-store secrets or other protected values by default;
- stream stdout/stderr and terminal-control data only through a backend-owned **secret-safe display boundary**; raw PTY bytes are never forwarded directly to the frontend without policy/redaction processing;
- deny or isolate protected credential/config paths and secret-store access according to the accepted local terminal security policy; frontend path requests never grant filesystem authority;
- if the target OS/runtime cannot prove adequate secret isolation/redaction for an interactive shell, arbitrary PTY streaming remains unavailable/`DEFER_TRIGGERED` rather than weakening the repository no-secret frontend invariant;
- stdin and interrupt/Ctrl+C support;
- session history/scroll belongs to terminal session, not canonical project memory;
- `Open terminal here` may target repo/worktree/path only after backend path validation;
- commands proposed by Jarvis are text proposals; explicit operator action inserts/executes;
- high-risk/destructive command families require explicit confirmation/policy;
- scrub/avoid secret leakage into Jarvis context/logs in addition to the mandatory frontend display boundary;
- Linux CI uses fake PTY/process adapter; no test requires live Windows PowerShell.

**Security boundary:** no raw arbitrary-process endpoint exposed to remote clients; loopback/local auth, OS-level process/environment isolation, path/cwd validation, output redaction and command/session policy must be explicitly re-derived and failure-mode tested in the full spec. Prompt text or a command-string denylist alone is not a sufficient secret boundary.

**Non-goals:** bypassing Git/spec lifecycle; remote shell server; hidden autonomous shell execution; weakening the repository-wide rule that secrets must not appear in frontend responses.

## FV-B22 — BRAINSTORM-SPEECH-CAPTURE-1

**Goal:** local speech-to-text capture for Raw Brainstorm notes.

**Required behavior:** record/attach audio through a bounded local media path; every transcription inference — including local-first execution — must enter the canonical AI execution spine through `run_ai_task` (or its exact accepted successor) and create the corresponding `ai_jobs` audit/ledger record; preserve original audio only according to explicit retention policy; transcription remains Raw content until user accepts/saves; model/provider selection respects privacy/egress policy; the media boundary never invokes a model/provider adapter directly.

**Non-goals:** always-on microphone; background recording; cloud speech provider by default; an unaudited parallel speech-model execution path.

## FV-B23 — ARCHITECTURE-SEMANTIC-ARTIFACT-1

**Goal:** optional semantic architecture representation searchable through Repository Inspector, separate from layout coordinates.

**Required model:** stable node/edge IDs, responsibility, interfaces/capabilities, typed dependencies, code paths, lifecycle/status, provenance/version.

**Required behavior:** existing SVG/Markdown architecture remains inspectable even if this semantic model is never promoted. Semantic edits, if later allowed, generate a development proposal/impact analysis rather than code mutation.

**Non-goals:** making a visual SVG authoritative by appearance; permanent graph on Repository first screen.

---

# Frontend draft slices

## FV-F01 — FINAL-APP-SHELL-RECONCILIATION-1

**Goal:** reconcile normal primary navigation to exactly `Design | Memory | Development | Coding | Settings` using approved shell/reference components.

**Required behavior:** remove normal Home/legacy peer destinations without deleting backend capabilities; route old destinations through contextual owners/compatible redirects where rederived; preserve direct-load/history/accessibility behavior.

**Depends on:** exact post-100/100b runtime audit plus authority rederivation.

## FV-F02 — DESIGN-FINAL-COMPOSITION-1

**Goal:** implement final `Design > Process | BLUECAD` composition/context strip from approved references without inventing Process semantics.

**Required behavior:** Process/BLUECAD only; contextual model/current/run/proposals/sources anchors; shared right Jarvis/Properties language; BLUECAD technical dock as subordinate surface.

**Depends on:** existing merged Design/BLUECAD owners and future engineering backend chosen by 101–110/rederivation.

## FV-F03 — MEMORY-PROJECT-BASIS-UI-1

**Goal:** final `Project search | Project Basis | Jarvis` UI.

**Required behavior:** compact dossier sections; semantic chips adjacent to item; Value/Rule-or-Threshold/truthful state; contextual validation action; Jarvis bounded multi-change proposal and `Approve all` only when backend change-set authority exists.

**No fake state:** frontend must not simulate working revisions/revalidation before backend contracts.

## FV-F04 — MEMORY-MODELS-UI-1

**Goal:** version dossier with overview-first disclosures and bounded expansion.

**Required behavior:** exact selected version/revision identity; collapsed summaries/counts; `Collapse all`; large-section internal scrolling/paging; accessibility; version-scoped Process/BLUECAD validation/results/runs/artifacts.

## FV-F05 — MEMORY-LITERATURE-UI-1

**Goal:** compact literature list with inline multi-expand and bounded preview.

**Required behavior:** text/detail left, preview right; PDF/image/source preview where actual backend/file route supports it; multiple sources open; full file opens browser/native viewer; source usage/provenance inspectable without forcing taxonomy at rest.

## FV-F06 — ROADMAP-TIMELINE-UI-1

**Goal:** final large Timeline plus integrated collapsible Execution status.

**Required behavior:** only `Timeline | Calendar`; workstream bars use approved condensed light type treatment only inside colored bars; `Ready | In progress | Blocked` state cards use normal app typography; Add/Edit/Delete; dependency/milestone interactions; presentation filters; no standalone Board page.

## FV-F07 — ROADMAP-CALENDAR-UI-1

**Goal:** day/week/month/agenda actual time-management UI.

**Required behavior:** Week default, hour grid, calls/work sessions/etc, all-day deadlines/milestones, linked Roadmap item, add/edit/delete, create-from-cell prefill, Jarvis proposed scheduling with explicit approval.

## FV-F08 — BRAINSTORM-UI-1

**Goal:** final Raw/Reconciled/Jarvis-context experience.

**Required behavior:** Raw capture with attachment and future microphone affordance; compact Reconciled list; multi-expand inline; discussion synthesis/provenance; explicit multi-item Jarvis context basket; Add to Roadmap / Promote Design / Promote Coding.

## FV-F09 — SETTINGS-FINAL-UI-1

**Goal:** final `Appearance | AI | System` compact settings UI.

**Required behavior:** provider credentials at provider/integration level, not model level; generic provider management; orchestration and budget/limits views; compact System diagnostics; reuse appearance/secure-storage owners.

## FV-F10 — CODING-REPOSITORY-UI-1

**Goal:** final Coding Repository screen using approved Repository Inspector reference.

**Required behavior:** remote repo/header status, active-development lifecycle, current work, inspector search/filter/results/preview, Markdown rendered/raw, SVG selected preview, code/config safe preview, Add to Jarvis context, Suggest modification proposal, Open on GitHub.

**Hard line:** architecture is searchable/inspectable, not permanently pinned.

## FV-F11 — CODING-RUNTIME-UI-1

**Goal:** final Runtime version-alignment screen.

**Required behavior:** local actually executed version visually green plus text; newer GitHub version orange plus text; explicit alignment state; evidence-backed `What GitHub added after local version`; inspect commits/files; services/health subordinate; compact update safeguards.

**Accessibility:** alignment/meaning never relies on green/orange alone.

## FV-F12 — INTEGRATED-TERMINAL-UI-1

**Goal:** replace/augment lower Runtime log surface with a real `Terminal | Logs` panel after FV-B21 exists.

**Required behavior:** xterm-like terminal emulator; PowerShell prompt on Windows; active cwd/session indicator; scrollback; keyboard/interrupt; optional tab creation only if backend supports it; `Send output to Jarvis`; `Insert command` from Jarvis proposal; `Open terminal here` from Repository Inspector; explicit confirmation UI for backend-classified high-risk commands. The UI receives only the secret-safe/redacted stream defined by FV-B21 and must never expose a raw PTY transport that can bypass that boundary.

**Non-goals:** browser-side command execution; terminal mock that pretends to execute; raw secret-bearing PTY output in frontend responses.

## FV-F13 — REPOSITORY-SUGGEST-MODIFICATION-UI-1

**Goal:** bounded modification proposal from selected repository artifact.

**Required flow:** selected target/ref -> user instruction -> Jarvis proposed diff/plan/reason/affected files -> discuss -> create development proposal/plan. No direct save-to-file action bypassing Coding lifecycle.

## FV-F14 — RUNTIME-UPDATE-UI-1

**Goal:** operator-facing safe update preparation only after FV-B20.

**Required behavior:** show current/target exact SHAs, dirty state, semantic delta, migration/build/smoke plan and rollback point; detailed phases expand only when requested; update/restart explicit; failure exposes exact failed gate and rollback result.

## FV-F15 — ARCHITECTURE-INSPECTION-UI-1

**Goal:** architecture artifacts behave like other Repository Inspector content.

**Required behavior:** select SVG/Markdown/semantic graph result -> bounded preview -> expand/full inspect -> Add to context / Suggest modification / Open GitHub. Semantic editing is deferred until FV-B23 and a separate editor readiness prove need.

---

# Promotion / dependency guidance

The future authority spec must not mechanically allocate one canonical ID per draft above. It must perform overlap analysis first.

Likely merge opportunities:

- FV-B03/B04/B05 may map onto or extend planned 101/102 rather than become three new stores;
- FV-B08/B09 may share one canonical Development store while retaining independently removable Calendar scheduling behavior;
- FV-B13/B14/B17 may share one read/search service if that minimizes semantic surface without conflating authority;
- FV-B18/B19 may be one local-runtime read slice;
- FV-B20 and FV-B21 must remain separate because self-update authority and interactive shell authority have materially different security/failure modes;
- frontend slices should follow owning backend/read contracts and must not fabricate future states while waiting.

Likely sequencing shape after 100a/100b and final authority rederivation:

1. canonical state/evidence foundations that survive overlap audit;
2. Memory/domain read models and PD-07 working-revision/revalidation/reconciliation;
3. Development Roadmap/Calendar/Brainstorm domain;
4. provider/settings generalization;
5. Repository observability/inspector and development pipeline;
6. Runtime identity/divergence;
7. safe update;
8. integrated terminal PTY as a separate security-bounded slice;
9. frontend workspace migrations over stable contracts;
10. optional speech capture/semantic architecture only when prerequisites and product value remain valid;
11. engineering Process/PBR/multifidelity work remains ordered according to the revalidated engineering dependency graph.

The authority spec may change this order only with explicit evidence/dependency reasoning and must preserve already merged work.