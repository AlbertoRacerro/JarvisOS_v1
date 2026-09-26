# 154 continuity archaeology — 2026-09-26

Evidence base for [spec 154](../specs/154-persistent-development-context.md). Fresh baseline: `origin/master` `d34de8de`, 0 open PRs, 153 merged (#715) and reconciled (#716). Agent Relay 0.7.7 (`~/.local/bin/relay`). Measurements are from local artifacts on the maintainer workstation. Paths below are local, not repository content.

## 1. What exists today

| Layer | What it persists | What it gives a fresh coordinator | Verified defects for continuity |
| --- | --- | --- | --- |
| Agent Relay | Per repo `.agent-relay/sessions/<id>/`: manifest, journal, git checkpoints, per-turn `prompt.md`/`output.jsonl`/`summary.json`, `successor.json`; global `~/.relay` | `run/chat --continue`: session id, directory pointer, truncated objective and ~140-char excerpts of recent turns | `derived/view.json` decisions/blockers/notes empty in the inspected sessions. Quota handoff `remaining_scope` is model-written: the 10:07 handoff said 151 was awaiting a Codex push, but #709 had merged around 09:05. The compactor summarized a working session as "No work performed". `status` lists 18 sessions as `active` while one agent process is live. An in-flight turn prompt exists only as a `/tmp/tmpXXXX` file until the turn completes. No supported bootstrap/state hook (`hook` only has fixed adapter entrypoints). |
| Provider transcripts | Full Claude/Codex conversations | `--resume` replays the whole stale conversation | Up to 4 MB per coordinator transcript; provider-specific; stale by construction |
| `PROGRESS.md` | Free-text append log (34 KB ≈ 9k tokens) | Must be read in full | Header "Active lanes" dates from 09-24 and is stale. Corrections are appended as prose ("supersedes my 20:16 entry"). One coordinator missed the authoritative 20:12 maintainer correction. No machine-checkable binding to SHAs/PRs. |
| Lane files (`out/w2`, `out/w3`) | `l<lane>.md` prompt, `<lane>.report.md`, `<lane>.done`, `<lane>.aN.log` | Readable by convention | `.done` is absent when the launcher dies while the worker survives (Codex reparents to init). Report overwrite by `codex -o` happened twice. No index of which lanes are live. |
| Committed proof JSON (`scripts/qualification/NNN`) | `source_sha`, status, measurements | Durable, reviewed | Not linked to a "do not rerun" decision; staleness against later heads is judged by hand |
| Second Brain (148/150) | Derived index over repo files at master plus workspace-scoped canonical SQL; authoritative reread; `retrieval_query` CLI | Code/canonical navigation with freshness gate | No PRs, branches, worktrees, lanes, proofs or directives. Repository recall with the default hashing embedder was weak in the 150 smoke (a query about the Ollama finish reason returned unrelated symbols). Needs the backend venv and index. |
| Hermes (146/152/153) | Product agent runtime under backend supervisor, workspace grants, operational memory adapter | Product Sidecar agent | Requires the running backend, a Hermes worker and a local model (GPU contention with proofs). Grants cover product workspaces, not repository development. |
| `jarvisctl` (control room, unversioned) | Nothing (live probe) | Workstation services, ports, GPU, Relay session count | No development context |

## 2. Cost of recovery today

Maintainer recovery prompts stored by Relay (`turns/*/prompt.md`, > 1 KB): 44.1, 28.9, 23.3, 20.6, 11.5, 8.3, 7.8, 6.1, 5.1, 4.7, 3.1, 3.0, 2.3, 2.2 (×3 Relay-wrapped), 2.1, 1.6, 1.4, 1.3, 1.2 KB across 12+ recoveries between 09-24 08:00 and 09-26 12:36.

Content classes (coordinator classification; a Gemini attempt at this classification was rejected because it scored clearly new product direction as governance restatement):

- **Large prompts (20–44 KB)** are mostly genuinely new maintainer direction and product evidence: Sidecar findings, llama.cpp/Qwen direction, the calculation-notebook vision, 149/155 requirements. That is irreducible input. Only their opening "fresh first / recover" sections (roughly 5–15%) are recovery.
- **Small resume prompts (1–8 KB)** are almost entirely reconstructible recovery facts and "do not repeat" warnings. Example: the 09-26 network-loss prompt (1.6 KB) states master `89d4134b`, "#715 EXISTS … do NOT create another PR", "do NOT rerun the expensive real proof", the CI failure cause, the audit lane status and the model_select 4/6 qualification. Every fact was available in GitHub, worktrees, lane files or proof JSON, but only a human could assemble it.
- **Repeated durable direction** ("ARCHITECTURE REMAINS: DWSIM = preferred engine …", "SECOND BRAIN FOLLOW-UP — MUST NOT BE LOST", Blue-plant completeness) is restated because there is no recorded directive the next session can find.
- **Stale facts propagate.** Relay's successor text (above) and the `PROGRESS.md` "Active lanes" header carried stale state forward. The 09-25 20:12–20:55 episode shows a correction recorded as prose that a coordinator missed.

Coordinator-side archaeology, from Claude transcripts (assistant turns before the first mutating action or end of session; cumulative input tokens include cached context):

| Session start | Prompt | Tool calls | Turns | Cumulative input tokens |
| --- | --- | --- | --- | --- |
| 09-24 19:58 takeover | 7.8 KB | 22 | 44 | 2.42 M |
| 09-25 20:47 Relay auth resume | 2.1 KB | 16 | 27 | 0.96 M (no mutation reached) |
| 09-25 20:55 Relay auth resume | 2.1 KB | 16 | 24 | 0.83 M (no mutation reached) |
| 09-25 20:58 Relay restore | 1.8 KB | 14 | 29 | 1.17 M |
| 09-26 06:56 Relay restore | 2.7 KB | 13 | 22 | 1.07 M |
| 09-26 10:21 Relay restore | 3.2 KB | 9 | 16 | 0.55 M |

That is typically 9–22 read calls (git/gh/worktree/PROGRESS/report reads) before any action, repeated on every recovery, with a fixed floor of ~44k input tokens per turn.

## 3. Alternatives

| Candidate | Context quality | Freshness / authority safety | Portability | Coupling / maintenance | Verdict |
| --- | --- | --- | --- | --- | --- |
| A. Status quo: human handoff + free-text PROGRESS | High where the human is careful | Human-verified but goes stale; prose corrections get missed | Any | Maintainer time on every recovery | Baseline to beat |
| B. Improve Relay handoff/compaction or modify Relay | Model-written summaries | Measured stale and wrong; no hook to inject verified state | Only Relay-launched sessions (misses the Codex desktop session) | Closed binary, upstream-owned | Reject as memory owner; read Relay only for verbatim prompts and session liveness |
| C. Resume provider transcripts | Complete but unfiltered | Stale by construction | Per vendor | Largest token cost (MBs) | Reject |
| D. Ingest control-room artifacts/transcripts into Second Brain | Similarity search over history | Returns historical text by relevance, not currency; control-room files are not canonical owners and live outside repo/data root | Needs backend venv | Couples the product index to machine-local dev tooling | Reject now; PARK ledger/report indexing if the corpus outgrows grep |
| E. Hermes as broker for external agents | Hermes memory + Second Brain | Adds a model hop; grants are product-workspace scoped | Agents already have a shell | Needs backend + worker + GPU model, and competes with proofs | Reject |
| F. MCP context server | Same data as a CLI | Same | Per-client registration differs across Claude/Codex/agy | Extra process | PARK as a thin wrapper over the CLI |
| G. Session-start hook injecting a packet | Same data | Same | Claude-specific | Local config | PARK as an optional caller of the CLI |
| **H. Deterministic recovery packet CLI + typed control ledger with mechanical freshness** | Authoritative state recomputed plus recorded non-derivable facts with provenance | Every item verified or labelled; stale SHA-bound evidence detected by content diff | Any agent with a shell | Stdlib script in repo with tests; ledger replaces PROGRESS | **Selected** |

Why H satisfies the minimum-necessary test. The accepted outcome, fewer and safer manual recoveries, cannot be reached with the existing owners: none of them represents PRs, lanes, proofs and directives together with a freshness verdict. The ledger replaces `PROGRESS.md` rather than adding a second log. The concrete risks it removes were all observed in the last 48 hours: stale model handoffs, a missed correction, rerun or near-rerun proofs, and maintainer re-typing of verified state.

## 4. Residual risks accepted

- A coordinator that dies before running `directive` loses nothing from the maintainer's side: Relay keeps the prompt once the turn completes, and the packet lists Relay prompts not recorded in the ledger. A prompt from a turn that was still in flight lives only in Relay's `/tmp` file.
- Ledger quality depends on coordinators recording outcomes. Anything left unrecorded is still recoverable from derived state (lanes, proofs, PRs) but without the coordinator's judgment.
- Plain-text search is sufficient for the current corpus (about 170 lane files and one ledger). Revisit via the PARK item if it stops being sufficient.
