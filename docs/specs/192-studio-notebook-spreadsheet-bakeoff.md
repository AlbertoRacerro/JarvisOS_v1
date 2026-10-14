# 192 — Engineering Studio notebook and spreadsheet bakeoff

State: **accepted and ready**. Written under the maintainer directive of 2026-10-13. Reviewed against master `bb85d739`. Architecture record: [Engineering Studio architecture](../implementation/engineering-studio-architecture-2026-10-13.md). Prior evidence: the wES upstream bakeoff (marimo and Univer both rated ADOPT on paper; this spec tests that claim).

- **Hard dependency:** 188 (merged, #808). It transitively needs 187 (merged, #806).
- **This spec is an evaluation contract.** It ships no product surface, no dependency in `backend/requirements.txt` or `frontend/package.json`, and no change to the 187 boundary.

## Fresh evidence (master `bb85d739`, 2026-10-14)

- **Licenses (registry metadata).** marimo 0.25.1 on PyPI: `license_expression` Apache-2.0 (wheel downloaded with `pip download --no-deps` into a throwaway directory). `@univerjs/core` and `@univerjs/presets` 1.0.4 on npm: `license` Apache-2.0 (`npm view`). The tool reads only the top-level package; transitive dependency licenses, and Univer's separately licensed paid "Pro" features, are **unverified** and are an evaluation question below.
- **187 boundary.** The sandbox unshares network and PID namespaces, has wall-clock, CPU, memory, process and output limits, and kills the whole sandbox on timeout. Runs are one-shot: source in, bounded result out. It has no listening port reachable from the host.
- **Consequence for marimo.** `marimo edit` is a long-running ASGI server with a websocket to a live Python kernel. Inside the 187 sandbox it has no reachable port, and outside it, it is unsandboxed user Python with a network. The two non-sandbox shapes are exactly what 187 forbids. Only one-shot shapes (`python nb.py`, `marimo export` of a notebook to HTML or script) fit 187 unchanged.
- **Parameter authority.** Project Parameters are owned by their existing owner; Studio versions are immutable `model_versions` rows (188). Neither may be written by an exploration surface.
- **Frontend.** Vite 6, React 18, no code-editor or spreadsheet dependency; CodeMirror 6 is already chosen by 188.

## Decision

1. **Questions answered.** The bakeoff answers exactly these and no others:
   - **Q1 marimo containment.** Can a marimo notebook be authored and viewed so that user Python runs only inside the 187 runtime, with no kernel server, no listening socket and no network outside it?
   - **Q2 marimo data in.** Can a notebook read published Parameter values and published Studio version metadata only through a read-only snapshot passed in as input, never through a live project connection?
   - **Q3 marimo data out and provenance.** Can a notebook export to a stable artifact (HTML and `.py`) with source SHA-256, snapshot hash and 187 run record attached?
   - **Q4 Univer embedding.** Can Univer's core, sheet and formula packages embed in the React frontend with acceptable license, bundle cost and no network, telemetry or CDN fetch?
   - **Q5 Univer authority.** Can a sheet be fed a read-only snapshot and be saved and exported as a file without any path that writes a Parameter, Studio version or model input?
2. **Prototype scope.** Time-boxed to one lane per tool, throwaway. Marimo prototype: a script run through the 187 runtime from a scratch data root. Univer prototype: a scratch Vite app outside the repo, or an in-repo page behind a default-off build flag that is not merged. Neither adds a dependency to the repo manifests on master, a route, an API, a table or a migration.
3. **No boundary change.** Q1 is evaluated only in the one-shot shapes above. A live kernel, a websocket kernel server, a bridge from host to a sandboxed server, or any relaxation of the 187 network or process rules is **out of scope** and is not prototyped in the repository. If the evaluation concludes that interactive marimo is wanted, the outcome is a separate **proposed** spec that states the 187 boundary change and its isolation proof. Nothing in this spec authorizes that change.
4. **Not parameter authorities.** Whatever is adopted later, notebooks and sheets are exploration surfaces. A value becomes a Parameter or a model input only through the existing proposal and review flow, as a proposal, never as a direct write.

## Acceptance (measurable criteria)

| Id | Criterion | Pass threshold |
|---|---|---|
| M1 | Containment | A notebook script runs via 187 with `ok`; external network connect fails; any sandbox-local loopback listener is unreachable from the host; no process survives; no marimo server process or listener opened by the notebook exists on the host at any time |
| M2 | Input | Snapshot JSON is the only input and fits within 187's 131,072-byte total request cap together with source and metadata; the notebook has no database path, token or project root |
| M3 | Export | HTML and `.py` artifacts are byte-stable across two runs of the same source and snapshot, excluding a documented timestamp field |
| M4 | Footprint | Wheel plus transitive install under 150 MB; cold script start under 5 s on the qualification host |
| M5 | License | marimo and all transitive runtime dependencies have permissive terms (MIT, BSD, Apache-2.0, ISC, 0BSD, PSF or public-domain equivalent); any mixed license is resolved against the installed files; none imposes strong copyleft, field-of-use restriction or source-available terms |
| U1 | License | Univer packages used and all their transitive runtime dependencies are permissive; no Pro or paid package is imported |
| U2 | Bundle | Added gzip JS for a lazy-loaded chunk under 1.5 MB; zero bytes added to the initial route chunk |
| U3 | Network | Browser network log of open, edit, save shows no request off the app origin |
| U4 | Authority | Source scan and a runtime check show the throwaway prototype imports no API client that mutates Parameters, models or runs; the snapshot is passed as a plain object |
| U5 | Fidelity | A 200-cell sheet with 20 formulas, unit-bearing columns and a CSV and XLSX export round-trips with values preserved; 10,000 rows scroll and edit without a frame above 100 ms |

## Required evidence

- Recorded in a new `docs/implementation/studio-notebook-spreadsheet-bakeoff-<date>.md` in the PR that closes this spec: one row per criterion with measured value, command or capture, tool versions, hashes, host, and master sha. Raw logs and captures stay outside the repo and are referenced by path and SHA-256.
- Package versions and license metadata are re-queried on the closing date; a changed license fails M5 or U1 until re-reviewed.
- Prototype source is deleted or left unmerged. If kept as evidence, it is attached by hash only.
- An adoption decision requires real-browser evidence for U2, U3 and U5 against a candidate backend serving `frontend/dist` on the same origin. For a rejection on a decisive measured failure, record the real-browser prototype evidence and the unmet criterion; a product route that this evaluation does not ship is not required solely to repeat that failure.

## Decision outcomes

For each tool, exactly one of:

- **Adopt:** every criterion passes. A follow-up spec is written, with a hard dependency on 188, for the product surface, and with an explicit statement of the authority boundary.
- **Adopt with boundary change:** passes except that the wanted shape needs a 187 change. A separate proposed spec states the change and its isolation proof. No code ships until it is accepted.
- **Reject:** any criterion fails and cannot be mitigated within the thresholds. The record states the failing criterion and the evidence. Reject is a valid, complete outcome.

Either tool may be adopted, both, or neither. A marginal result is a reject, not a retry.

## Non-goals

- Shipping marimo, Univer, a kernel server or any notebook or spreadsheet route.
- Any change to 187 limits, namespaces or the one-shot execution model.
- A Jupyter, JupyterLite, Monaco or Handsontable evaluation.
- Spreadsheet formulas as a calculation authority, or notebook outputs as qualified results.
- Collaboration, real-time sync, AI-assisted notebook authoring.
