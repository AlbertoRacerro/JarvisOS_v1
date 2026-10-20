# Issue 847 — Relay post-turn CPU freeze, 2026-10-20

Authority: maintainer's explicit P1 host-maintenance request and
[issue #847](https://github.com/AlbertoRacerro/JarvisOS_v1/issues/847).
This is repository-development tooling maintenance. It does not implement planned
spec 201, change its readiness, launch another mission coordinator, or release the
historical continuity `effects_uncertain` hold.

## Diagnosis supported by live evidence

Starting repository HEAD: `755c9ab75956b08f842f521afa29845b7bdf103d`, branch `master`,
clean status. Isolated repair branch: `codex/847-relay-freeze`, worktree
`/home/thera/src/worktrees/codex-847-relay-freeze`.

Fresh process discovery identified interactive Relay PID **44906**, parent **44901**,
process group **44901**, terminal `/dev/pts/2`, cwd `/home/thera/src/JarvisOS_v1`.
These are incident observations, never reusable termination targets. PID 2426 from
the earlier incident was not reused. Parent 44901 is the PyInstaller bootloader;
44906 is the embedded Python process. Independent daemon processes were 488/792.

Two-second `/proc` thread deltas measured thread **46084 at 100.0% of one core**.
The main thread waited in a futex; the busy thread was runnable. All thread child
lists were empty. No live `devctx.py`, Git, Claude or design worker belonged to the
frozen process. Its fds 0/1/2 pointed to the terminal, fd 3 to `repl.log`; other fds
were one socket and two pipes. `/proc/locks` showed no ledger lock held by Relay
or a live ledger-writing Python process. Terminal flags showed a connected cbreak
terminal, not a terminal disconnect.

Same-user `/proc/.../stack` and `syscall` access was denied under
`kernel.yama.ptrace_scope=1`. The maintainer explicitly approved **one** bounded,
read-only WSL-root Python stack capture. No ptrace setting or permission was changed:

```bash
timeout 10 /mnt/c/Windows/System32/wsl.exe -u root -- /home/thera/.local/bin/py-spy dump --pid 44906
```

`py-spy==0.4.2` reported Python 3.12.13 and these decisive frames, without locals:

```text
Thread 46084 (active+gil): Thread-1 (_collect_output)
    user_facing_run_error (run_errors.py:76)
    _collect_output (agent_session.py:940)
MainThread (idle): threading.join
    stop (input_queue.py:187)
    _stop_queued_input (shell.py:1542)
    _thinking_status (shell.py:1509)
    _drain_agent_output (shell.py:2162)
```

The other threads were waiting in the status poller, daemon listener, Rich Live
refresh and queued input reader. Source inspection establishes that `_collect_output`
had already drained output and called `proc.wait()` before entering this detector.
The busy regex held the GIL, starving UI threads and Python signal processing.
This was **post-child output classification**, not a ledger lock, blocked Git,
productive worker, or proven terminal renderer defect.

The completed Claude journal corroborates that order:

- Native provider journal UUID: `648ff2b5-28b1-44e4-8b62-9413d913964a`.
- Displayed command completed at **2026-10-20 07:25:11 Europe/Rome** and returned
  ledger ID `L20261020052511-89d9`.
- Claude's final response completed at **07:25:23 Europe/Rome**. Do not rerun that
  append or the design work merely because Relay did not display completion.
- Largest image/base64 string in the journal: **604,628 characters**. Only sizes
  and structural locations were used in public evidence; no image data or private
  transcript was published.

The model detector had an unanchored `[^'"\s]+` token. On a long token with no
`model is not supported` suffix, it retried every remaining suffix: quadratic work.
Successful protocol output falls back to scanning the complete JSON stream when
no structured errors are collected, so image output exposed the defect.
A bounded causal sweep found the same retry problem in `sandbox.*denied` when
many sandbox words lack a denied suffix. Both are repaired together.

Combined interactive verification exposed a second, independently reproduced
completion defect. `TurnBasedAgentSession.busy` returned false as soon as the
subprocess exited, although the collector could still be parsing output. The
REPL's 0.4-second idle cutoff could then expire before `SessionOutputDone` and
the final response arrived, persisting `completed` with `No response captured`.
The repair retains busy ownership while `_proc` exists; the collector clears it
in its existing `finally` after output processing. A deterministic regression
delays classification after subprocess exit and asserts the session remains busy.
It failed before this correction and passes afterward. No new polling loop,
retry, provider request, or background coordinator was added.

## Host and preservation evidence

- WSL: 15,703 MiB RAM total, 13,687 MiB available; swap 0 MiB used.
- GPU: NVIDIA RTX 5070 Ti Laptop, 0% utilization, 7,870/12,227 MiB allocated.
  Idle model-server allocation was not evidence of GPU execution.
- Windows two-second CPU sampling after recovery found no corresponding pinned
  core; highest sampled process was ChatGPT at 17.97% of one core. Initial Windows
  `CPU` totals were cumulative and were not treated as instantaneous utilization.
- Backend processes 1752 and 10378, multiprocessing helper 10733, model server 1850,
  daemon 488/792 and the Codex maintenance session were left running.
- A read-only inventory covered **151 worktrees**, recording heads and status in
  the private incident directory. Nine pre-existing dirty worktrees were left
  untouched: agent-a9063dac23764cb53, k154-plan, k157, k161fix, k165, k173, k196,
  p834 and worker-lab. No resets, deletes, broad signals or WSL restart occurred.

Private on-host evidence lives at
`/home/thera/jarvis-control/work/incidents/847/`: initial process/thread snapshots,
`stack.txt`, `journal-manifest.json`, `worktree-inventory.json`,
`recovery-signals.json`, `lumen-completed-response.txt`, and workstation proof.
It is not committed. The completed response is a recovery artifact, not an
independent validation of Claude's design/contrast claims.

Immediately before cancellation, PID/start/executable identity and **every thread's**
child list were revalidated. With no live child and durable completed work,
targeted SIGINT and SIGTERM were each given two seconds; both failed. SIGKILL
terminated only 44906. Its bootloader then exited, returning the original terminal
to bash. `stty -F /dev/pts/2 sane` restored terminal flags. This recovered control;
termination itself is not the engineering fix.

## Repair and provenance

Upstream installed version: `agent-relay 0.7.7`, stripped PyInstaller ELF at
`/home/thera/.local/bin/relay`. Its extracted runtime used prompt_toolkit 3.0.53
and Textual 8.2.8. The exact source was obtained from the PyPI 0.7.7 sdist:

- sdist SHA-256: `58b54df4f788cf4b23930f9bdc9cfb31500a2002515fb0ad55a42d3b0d8a6b8e`;
- `run_errors.py` SHA-256:
  `75ed02a50e3815faba2c35def52f92a451a830323a95f1fe9c3d691fc8322601`;
- `repl/agent_session.py` SHA-256:
  `f104a09fbdd2c1faeeab2cfe1d6fa977f5133d34c3bbbcd989807986e804e493`;
- [upstream](https://github.com/bethvourc/agent--relay), Apache-2.0;
- public upstream inspection HEAD `dc18497ffb52954d7ecd22561f1ebdd01a014625`.
  That checkout exposes documentation, not the Python source, so the verified
  source distribution is the code evidence. Upstream issue search found only
  issue #1, unrelated to this parser defect. No upstream acceptance is claimed.

`scripts/relay_safe.py` loads the exact version/source, refuses unfamiliar source,
applies three checked substitutions in memory **before** the CLI imports the
detector, then forwards the original arguments to the original CLI:

1. Anchor model-token starts at a quote/whitespace boundary, preventing retries
   inside a base64 token while preserving captured model names.
2. Remove the ambiguous sandbox wildcard from the fixed-phrase regex.
3. Search the first sandbox and a later denied once per newline-delimited line.
   Preserve `re.IGNORECASE` Unicode semantics and the original treatment of CR,
   vertical tab, form feed and Unicode line separators.

It also verifies the exact session-module hash and applies the one-line collector
busy correction before the CLI imports the session classes. Both original source
files remain unchanged on disk.

The existing continuity guard assumed `/proc` argv started with a native Relay
binary. A Python script launcher adds an interpreter first; without normalization
the guard could miss an interactive coordinator. `scripts/relay_continuity.py`
now recognizes the known Relay entry scripts behind Python, retaining daemon/hook
exclusions and leaving unrelated Python untouched. This preserves existing
single-coordinator protection; it does not authorize takeover.

No upstream installation files, credentials, user configuration, permissions,
launch templates, or session journals are edited by this wrapper. The submitted
upstream-quality patch and regression tests are in
`docs/patches/847-agent-relay-0.7.7.patch`; it applies to the pristine sdist.
This patch artifact does not vendor the external repository.

The isolated local runtime uses Python 3.12.3. A first Python 3.11 environment
could run detector tests, but the upstream CLI failed with `SyntaxError: f-string:
unterminated string` in `dashboard_alerts.py:344`, despite declaring Python >=3.11.
The safe runtime and CI therefore use Python 3.12 rather than expanding the repair
to upstream Python-version compatibility.

## Liveness boundary and spec 201

`scripts/relay_diagnostics.py --pid PID --journal PATH --interval 1 --samples 3`
collects PID/start identities, ancestry, descendants from all threads, wait
channels, per-thread interval CPU, IO counters, fd 0/1/2 targets and journal
metadata. It reads no environment, command arguments, or journal contents.

Output distinguishes observed journal metadata changes, descendant activity,
exit/PID reuse, and no observed progress requiring investigation. Metadata
activity does not prove semantic progress; a sleeping worker or idle prompt is
not a proven stall. High CPU alone never authorizes termination. Sampling has
a 60-second deadline and at most 50 seconds of planned sleeps; individual blocked
kernel/filesystem metadata reads can exceed that deadline, an explicit limitation.
The tool performs **no signals, automatic retries, recovery or model calls**.

Minimum-necessary assessment:

```text
Criterio di accettazione: diagnose the P1 freeze and preserve safe recoverability.
Questo lavoro è necessario per soddisfarlo? sì: bounded parser repair and read-only evidence.
È raggiungibile senza questo lavoro? no: killing the process leaves the parser defect unchanged.
Quale rischio concreto giustifica la nuova superficie?
Reproduced post-tool GIL starvation; diagnostic metadata prevents CPU-only recovery decisions.
```

Planned 201 remains the owner of deterministic mission ownership, no-progress
policy, provider failover and autonomous continuation. This helper grants none
of those capabilities and does not alter the historical supervisor hold.

## Reproduction and verification

All provider-facing tests use synthetic output and fake executables. No paid/live
provider calls are needed to exercise the exact fault path. Regex regressions run
in separately owned subprocesses with deadlines so a future GIL-holding defect
cannot wedge the pytest process.

Measured before/after:

| Evidence | Original | Repaired |
| --- | --- | --- |
| Live post-turn thread | 100.0% of one core for hours | Original frozen process recovered; replacement measured separately |
| Successful Claude JSON, 100 KB image token | timeout >4 s | 0.0271 s, no error reported |
| Token matching actual 604,628-char journal image size | not allowed an unbounded run | 0.1486 s |
| Repeated sandbox negative | 100,000 words timeout >3 s | 125,000 words 0.00464 s |
| Original/repaired compatibility corpus | baseline oracle | 10,512 cases, zero mismatches |
| Representative isolated ledger append | 0.0767 s | devctx implementation unchanged |
| Concurrent ledger writers | 48 successful appends, 12 workers | all records complete, max child 0.1152 s |
| Held ledger lock | sleeping, 0% CPU | SIGINT exits without append; explicit subsequent recovery works |

Regression coverage includes parser negatives and provider-error compatibility,
source/version guards, immutable installation, concurrent ledger integrity,
held-lock interruption, slow/stuck children, stdout delivery stalled after a
durable append, and conservative liveness classification. The saturated-output
test proves why an uncertain append must be inspected rather than repeated.

Commands and final workstation/CI results are recorded in the delivery evidence
below once the candidate head is frozen. No frontend code changed; no design build
or browser redesign is part of this incident repair.

## Recoverable Lumen state

- Worktree: `/home/thera/src/worktrees/p198b`, clean.
- Branch: `explore/198b-lumen-v2`.
- Head: `d995f940f00fa9a2e5b87fa8de29081d2de0a5d6` (Lumen Light v2.1).
- Previous checkpoint: `d8325abe` (Lumen Dark/Light v2).
- Latest ledger record: `L20261020052511-89d9`; append already completed.
- Artifacts: `/home/thera/jarvis-control/work/out/v198b/v2.1/`, including
  `contact-sheet-lumen-light-v2.1.png` and five screenshot files.
- Next design action: await maintainer visual selection. No broad merge, visual
  redesign, repeated screenshot generation, or duplicated coordinator is implied.
- Native Claude session UUID above preserves the completed provider conversation.
  Relay's final turn persistence happens after the defective detector, so do not
  assume its older session lineage contains this last completed response. Use
  the preserved final response and exact ledger/worktree state when resuming.

## Delivery evidence

Local commands, run from the isolated repair worktree unless noted:

```bash
/home/thera/.local/share/jarvisos/relay-0.7.7-847/bin/python -m pytest -q -s tests/relay_reliability
# Final 41 passed in 13.48 s; actual PTY proof included.
/home/thera/.local/share/jarvisos/relay-0.7.7-847/bin/python -m pytest -q -s tests/relay_reliability/test_repl.py -k actual_pty
# Confirming run after repairing the race: 1 passed, 2 deselected in 8.31 s.
/home/thera/src/JarvisOS_v1/backend/.venv/bin/python -m pytest -q -o addopts='' -o cache_dir=/tmp/incident847-final-devctx-cache backend/tests/test_devctx.py backend/tests/test_devctx_incident847.py
# 17 passed, 1 warning in 3.29 s.
/home/thera/src/JarvisOS_v1/backend/.venv/bin/python -m pytest -q -o addopts='' backend/tests/test_relay_continuity.py
# 407 passed, 1 skipped, 1 warning in 14.96 s.
/home/thera/src/JarvisOS_v1/backend/.venv/bin/python -m ruff check scripts/relay_safe.py scripts/relay_diagnostics.py tests/relay_reliability backend/tests/test_devctx_incident847.py
# PASS.
/home/thera/src/JarvisOS_v1/backend/.venv/bin/python -m ruff check --config backend/pyproject.toml scripts/relay_continuity.py backend/tests/test_relay_continuity.py
# PASS under the existing canonical backend configuration.
python3 scripts/check_spec_status.py --self-test
python3 scripts/check_spec_status.py
python3 scripts/check_architecture_enforcement.py
python3 scripts/check_pr_attention_integration.py
python3 scripts/check_review_secret_boundary.py
git diff --check
# All PASS; registry 221 rows.
```

The optional existing test `test_real_codex_read_only_sandbox_blocks_writes` is
skipped because `RELAY_CONTINUITY_CODEX` is unset; no live provider was invoked
to substitute for it. Existing warning: deprecated `anyio.abc.BlockingPortal`
alias in `starlette/testclient.py:40`. Backend/frontend product suites and frontend
build were not run locally because no product code or frontend files changed;
exact-head repository CI remains separate evidence.

Failures retained as diagnostic history:

- System `python3 -m pytest ...test_devctx.py` initially failed: `No module named
  pytest`; rerun with the existing backend venv passed.
- An exploratory GitHub clone used `bethvourc/agent-relay` and returned repository
  not found. Package metadata established the correct `agent--relay` URL.
- The Python 3.11 upstream CLI failure is documented above; Python 3.12 is used.
- A first lock/stdout test expected `pipe_write`; this kernel reports
  `anon_pipe_write`. The assertion was corrected to the kernel-symbol family.
- First parser-test authoring expected `Claude` rather than the actual registry
  display name `Claude Code`; corrected to the existing public contract.
- Initial Ruff findings on new code were corrected. Root-default Ruff additionally
  reports 10 pre-existing findings in the old continuity module (I001, SIM115,
  RUF100, RUF059, FURB167, ISC004, 2x PLW1510, 2x SIM102); the module passes its
  canonical backend Ruff config. No unrelated cleanup or evidence weakening.
- Initial combined terminal runs were `40 passed, 1 failed`. The harness needed
  actual editor-echo readiness and ANSI-normalized matching, but tracing also
  established the real collector race above. No failed gate was skipped. The
  deterministic collector test failed before its patch; all 41 now pass.
- An initial Windows Terminal launch had a PowerShell quoting/positional-parameter
  error; the corrected structured argument/encoded-command invocation succeeded.
- One verification invocation used the upstream source directory for Jarvis tests
  and Ruff, producing file-not-found errors. Repeating from the repair worktree
  passed. The upstream patch check was separately run from the upstream directory.
- A later `/help` check expected `/resume` beyond the rendered help window even
  though help responded. It now checks an actually rendered help description;
  the separate real `/resume 1` recovery check remains. The fake CLI now emits
  the standard assistant text event after its image, avoiding raw-protocol
  fallback rendering. The final combined 41-test suite passed after these fixes.
- The first staged `git diff --cached --check` flagged four blank unified-diff
  context markers as trailing whitespace inside the patch artifact. Blank context
  lines were normalized; both `git apply --check` and staged whitespace checks
  then passed. No runtime source changed for this formatting correction.

Actual owned WSL PTY proof runs the real `devctx.py note attempt` in a temporary
Git repository and control root, waits on a fake Claude child, processes a
604,628-byte synthetic image token, responds to `/help`, disconnects after a
completed turn, preserves journals, and resumes with `/resume 1` in a fresh
process. `/exit` returns zero. Idle measurements: **0.0 then 0.01 CPU seconds per
one-second sample**. SIGINT also interrupts a planned 30-second child while
preserving its completed ledger append. No uncertain effect is repeated.

Limits: zero real provider calls; successful slow child delayed 1.5 seconds;
30-second sleeper interrupted early; disconnect proved after completion, not
during an irreversible write; Linux PTY proof is not a Windows-renderer proof.
No claim covers every possible Relay hang or grants spec-201 readiness.

## Workstation deployment and rollback

The repaired default `relay`/`agent-relay` entrypoint now points to the separate
Python 3.12 environment at `/home/thera/.local/share/jarvisos/relay-0.7.7-847`.
The launcher is a copy of the reviewed script with that environment's absolute
Python shebang. Original ELF preserved unchanged at
`/home/thera/.local/share/jarvisos/relay-0.7.7-847/original-relay-0.7.7`, SHA-256
`444507d368cf0dafca4744839c677765b38ca7a4d0aa39db63e2f0889aef5e83`.
The live daemon continues using that original inode; it was not restarted.

To preserve coordinator exclusion immediately, the exact tested
`scripts/relay_continuity.py` was also copied to the primary checkout as an
**intentional local host overlay**. Primary checkout status is consequently
` M scripts/relay_continuity.py`; all other files there remain unchanged.
Its original bytes and deployment hashes are recorded in the private incident
directory. This is explicit local deployment pending PR integration, not an
unreported dirty diff or a second source implementation.

`installation.json` records the paths, original hashes and installed hashes.
Rollback is local and reversible: first verify installed hashes still match that
manifest so later user work cannot be overwritten; replace the entrypoint with
the preserved original binary, and restore the continuity source from
`relay_continuity.before.py`. Do not roll back during active work, restart the
daemon, delete journals, or invoke broad signals. The old binary still contains
the reproduced bug; rollback is a recovery escape, not a recommended default.

A fresh Windows Terminal tab titled **JarvisOS Relay recovered** was launched
using the repaired entrypoint. The earlier maintenance-owned idle replacement
was replaced with SIGTERM after PID/start identity and empty child lists were
verified; it exited gracefully. Fresh PID discovery and liveness metadata are
recorded in `recovered-terminal*.json`. No prompt was injected into the user's
old terminal and no second design task was launched. The final source and
GitHub evidence are linked from issue #847 and its repair PR.

Final deployed process discovery: PID **67046**, terminal `/dev/pts/5`. Its
first two-second startup sample used 10.491% of one core; the next two idle
samples used **0.999% / 0.999%**, with no child in any snapshot. Production
`live_conflicts()` returned **`['repl_active']`**, verifying the deployed
coordinator exclusion against the actual process. PID values are observations;
future recovery must discover them anew.
