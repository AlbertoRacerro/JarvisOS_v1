# BLUECAD — Tool Landscape, Licensing, and Integration Boundaries

Status: draft v0.1 (2026-07-03)
Scope: Task 1 of 4 of the BLUECAD architecture series.
Companion doc: `BLUECAD_CORE_DESIGN.md` (contracts, AI-CAD loop, routing
integration, roadmap — compressed from the originally planned three docs).

## What BLUECAD is (and is not)

BLUECAD is a **domain-specific CAD-as-code and engineering orchestration layer**
inside JarvisOS, targeted at one system family: a floating tubular
photobioreactor (tube runs, bends, smart joints, manifolds, floats, anchors,
harvesting module). It orchestrates existing open-source CAD/mesh/FEM/CFD tools
as **external backends behind adapters**. It is not a general CAD application,
not a kernel, and not a GUI.

Core principle: **the LLM proposes; deterministic geometry and engineering
validators decide.** No AI-generated geometry is accepted without passing
deterministic validation, and promotion into the BlueRev design record is a
human-gated Decision (consistent with the existing Workspace/Decision model in
`JARVISOS_COMPUTATIONAL_ENGINEERING_WORKSPACE.md`).

Clean-room rule: adapters are written against **public, documented APIs, CLI
interfaces, and file formats only**. No source code from any referenced project
is copied, translated, or paraphrased into JarvisOS or BlueRev code.

---

## 1. Tool comparison table

| Tool | Category | Language / interface surface | What it offers BLUECAD | Maturity & notes | Decision |
| --- | --- | --- | --- | --- | --- |
| **build123d** | CAD-as-code (B-rep) | Python library; builder + algebra APIs; STEP/STL import-export | Parametric solid modeling in plain Python: sweeps along paths (tube runs/bends), booleans, fillets, direct topology access (faces/edges for joint features) | Active, modern successor-style API over the same OCCT bindings as CadQuery | **MVP primary CAD backend** |
| **CadQuery** | CAD-as-code (B-rep) | Python library; fluent selector API; STEP/STL | Same kernel capabilities as build123d; larger example corpus (more LLM training data → better AI codegen hit rate) | Mature, widely used | **Accepted alternate**; adapter contract stays kernel-agnostic so either runs |
| **OCCT (Open CASCADE)** | B-rep geometry kernel | C++ lib; consumed indirectly via OCP Python wheels | The actual kernel under CadQuery/build123d: B-rep, booleans, STEP AP203/214/242, STL, BRepCheck validity analysis | Industrial-grade; the only serious permissively-usable open kernel | **Indirect dependency only** (via unmodified OCP wheels); never vendored or modified |
| **FreeCAD** | CAD application | GUI app; Python console; own document format | Human viewer for STEP outputs; TechDraw for quick drawings; FEM workbench duplicates what we do directly | Heavy, GUI-coupled, LGPL app | **Viewer only, out of pipeline**; never a code dependency |
| **SolveSpace** | Parametric sketcher | GUI app; constraint solver | 2D/3D constraint solving | GPL-3.0; GUI-centric; constraint solving not needed for code-defined geometry | **Excluded** |
| **OpenSCAD** | CSG CAD-as-code | Own DSL; CLI | Script-based CSG | GPL-2.0+; mesh/CSG only, no B-rep, no STEP export → unusable for engineering exchange | **Excluded** |
| **Gmsh** | Meshing (+ light FEM pre/post) | CLI + `.geo` scripts; reads STEP; writes `.msh`, `.inp`, `.unv`; also a Python/C++ SDK | STEP → volume/surface mesh for FEM/CFD; physical groups for boundary conditions; mesh quality metrics | De-facto standard open mesher; excellent CLI automation | **MVP mesher, external process only** (see license table) |
| **CalculiX (ccx)** | FEM solver | CLI; `.inp` input (Abaqus-like), `.frd`/`.dat` output | Static/modal/thermal structural analysis of tube runs, joints, floats under load | Proven solver, stable text-file contract | **MVP FEM solver, external process only** |
| **MFEM** | FEM library | C++ (PyMFEM bindings) | Build-your-own FEM: full control, permissive license | Excellent library, but it is a toolkit — we would be writing the solver | **Deferred**; revisit only if a custom PDE (e.g. gas transfer) can't be expressed in off-the-shelf solvers |
| **OpenFOAM** | CFD | Case-directory + CLI utilities (`blockMesh`, `snappyHexMesh`, solvers); dict text files | External flow around floats, internal multiphase flow in tubes (long-term), wave loading (very long-term) | Heavy; Linux-native (WSL2/container on this machine) | **Future backend behind a frozen case-directory boundary**; boundary defined now, implementation deferred |
| **PicoGK + LEAP71 ShapeKernel/LatticeLibrary** | Computational geometry (implicit/voxel) | C#/.NET library; STL/3MF output; OpenVDB-based runtime | Implicit modeling and lattices — relevant later for harvesting-module internals or optimized joint infill; the LEAP71 "computational engineering model" pattern is the philosophical reference for BLUECAD | Young but serious; different runtime (.NET) | **Optional future backend**; pattern adopted now, dependency deferred |

## 2. License risk and integration boundary table

Integration modes:

- **A — in-process library**: imported into the JarvisOS/BlueRev Python process. Permissive licenses only.
- **B — dynamically-linked LGPL runtime**: unmodified official binary wheels, dynamically linked, replaceable by the user. No vendoring, no source modification, no static bundling.
- **C — external process**: separate OS process, communication via files/CLI/stdio only. The GPL-safe boundary.
- **D — external process, containerized** (WSL2/Docker): same as C with environment isolation.
- **X — excluded.**

| Tool | License (SPDX) | Verified | Copyleft class | Allowed mode | Vendor/fork allowed? | Key obligations & risk notes |
| --- | --- | --- | --- | --- | --- | --- |
| build123d | Apache-2.0 | high-confidence, re-verify at version pin | none | **A** | Legally yes; policy **no** (stay on upstream) | Attribution in NOTICE if redistributed; explicit patent grant |
| CadQuery | Apache-2.0 | high-confidence, re-verify at pin | none | **A** | Legally yes; policy no | Same as build123d |
| OCP (OCCT Python bindings) | Apache-2.0 (bindings) over LGPL OCCT | high-confidence, re-verify at pin | via OCCT | **B** | **No** | Consume only as unmodified pip wheels |
| OCCT | LGPL-2.1 + OCCT exception | high-confidence, re-verify at pin | weak (file/library) | **B** (indirect) | **No** | Keep dynamically linked and user-replaceable; never modify sources; if BLUECAD is ever frozen/bundled (PyInstaller etc.), verify relink-ability is preserved |
| FreeCAD | LGPL-2.0-or-later | high-confidence | weak | **C** (as viewer app) or X | **No** | Only launched as an app by the user; zero code dependency |
| SolveSpace | GPL-3.0 | high-confidence | strong | **X** | No | No need that justifies even a process boundary |
| OpenSCAD | GPL-2.0-or-later | high-confidence | strong | **X** | No | Superseded by build123d for every BLUECAD need |
| **Gmsh** | **GPL-2.0-or-later** | **verified 2026-07-03** (LICENSE.txt) | **strong** | **C only** | **No** | The license exception only lets *Gmsh itself* combine with Netgen/METIS/OCCT/ParaView; it grants **no exemption to programs linking Gmsh**. Therefore the `gmsh` Python SDK must **never** be imported into a JarvisOS/BlueRev process. Invoke the `gmsh` CLI on `.geo`/STEP files as a subprocess |
| CalculiX (ccx) | GPL-2.0 | high-confidence, re-verify at pin | strong | **C only** | No | Standard industry practice: drive `ccx` via `.inp` files, parse `.frd`/`.dat`. Windows binaries: use a well-known build, record provenance + hash in the tool registry |
| MFEM | BSD-3-Clause | high-confidence | none | A (if ever used) | Legally yes; policy no | Deferred anyway |
| OpenFOAM | GPL-3.0 | high-confidence, re-verify at pin | strong | **D only** | No | Case-directory + CLI boundary; runs in WSL2/container on this Windows host. "OpenFOAM" is an OpenCFD Ltd trademark — describe as "compatible with", never "powered by" without checking the trademark policy |
| PicoGK | Apache-2.0 | **verified 2026-07-03** (GitHub license API) | none | A (in a .NET sidecar) or C | Legally yes; policy no | Runtime depends on OpenVDB (MPL-2.0, file-level copyleft — fine if unmodified) |
| LEAP71 ShapeKernel / LatticeLibrary | Apache-2.0 | high-confidence, re-verify before first use | none | A (.NET sidecar) | Legally yes; policy no | Adopt the *pattern* (code-defined engineering objects) without the dependency for MVP |

**Boundary rules (hard invariants for BLUECAD):**

1. **No GPL code in any JarvisOS or BlueRev process.** GPL tools are separate
   OS processes; the only shared surface is files, CLI arguments, and exit
   codes ("mere aggregation").
2. **No copyleft source is ever vendored, forked, patched, or copied** into
   this repo or the BlueRev repo — including "just one helper function".
3. **LGPL (OCCT) stays dynamically linked via unmodified upstream wheels** and
   must remain user-replaceable in any future distributed form.
4. **Adapters are clean-room**: written from documentation, public API
   reference, and file-format specs. Reading upstream *source* to write an
   adapter is prohibited by policy (docs/examples/tests are fine).
5. JarvisOS-side adapters must stay **generic** (no BlueRev formulas inside
   the glue code); BlueRev domain logic lives in its own package and reaches
   adapters through the neutral geometry-spec contract (defined in the
   contracts doc). **This is code layering, not runtime secrecy**: everything
   runs locally, and the *data* flowing through adapters (geometry, loads,
   parameters) is of course BlueRev-specific — that is fine and carries no
   extra controls. The rule only keeps sizing rules, correlations, and design
   heuristics in one module so adapters stay reusable, testable with dummy
   geometry, and safely delegable to cheap external agents without exposing
   the domain formulas.

Rationale for rule 1 even though JarvisOS is single-user today: GPL
obligations trigger on distribution, and BlueRev is a startup — assume BLUECAD
or parts of it will someday be distributed. Retrofitting a process boundary
later is expensive; having it from day one is nearly free because these tools
already have first-class CLI contracts.

## 3. Recommended MVP stack

| Layer | Choice | Mode | Why |
| --- | --- | --- | --- |
| CAD kernel + CAD-as-code | **build123d** (on OCP/OCCT) | A/B in-process | Apache-2.0; plain-Python parametric B-rep; sweeps along wire paths map 1:1 to tube runs and bends; direct topology access for joint faces; STEP + STL export built in |
| CAD codegen fallback | CadQuery accepted as alternate script dialect | A | Same kernel; more training-data coverage for LLM proposals; adapter treats "CAD script" as either dialect |
| Exchange formats | STEP AP214 (canonical), STL (mesh/preview), 3MF later | — | STEP is the engineering source of truth; STL feeds Gmsh/preview |
| Meshing | **Gmsh CLI** | C subprocess | Reads our STEP, writes `.inp` for CalculiX and `.msh` generally; physical groups let the FEM adapter address named boundaries deterministically |
| FEM | **CalculiX `ccx`** | C subprocess | Static/modal/thermal covers MVP questions (tube bending under wave/self-weight, joint stress, float attachment); pure-text `.inp`/`.frd` contract is easy to generate and parse deterministically |
| CFD | **OpenFOAM — boundary defined, implementation deferred** | D (future) | MVP does not need CFD; drag/added-mass first-pass comes from correlations in BlueRev domain code. Freeze the case-directory contract now so the adapter slot exists |
| Human verification | FreeCAD as STEP viewer | app only | Zero coupling |
| Implicit/lattice geometry | PicoGK + ShapeKernel | deferred sidecar | Only if harvesting-module internals or joint optimization demand it |
| Excluded | SolveSpace, OpenSCAD, MFEM (for now) | X | See comparison table |

Platform note (this machine, Windows 11): build123d/CadQuery and Gmsh have
first-class Windows distributions; CalculiX needs a trusted Windows binary
(record provenance in the registry) or a WSL2 build; OpenFOAM is WSL2/Docker
only — one more reason it is deferred.

## 4. Non-goals and legal risks (deliverable 11)

### Non-goals

1. **Not a general CAD clone.** No GUI *modeler*: no sketch-constraint UX, no
   feature tree, no mouse-driven editing. An interactive GUI **is** in scope,
   as a viewer/control surface: 3D preview of generated geometry (three.js,
   MIT, in the existing JarvisOS frontend), validation reports, and later
   parameter controls that re-run the CAD script. Geometry stays code-defined.
2. **No kernel work.** B-rep math stays in OCCT; if OCCT can't do it, BLUECAD
   doesn't do it (until a deliberate future decision, e.g. PicoGK for
   implicits).
3. **No autonomous acceptance of AI-generated CAD.** LLM output is a proposal
   artifact; only deterministic validators + human Decision promote it.
4. **No certified engineering claims.** FEM/CFD results are design aids, not
   class-society or regulatory sign-off (relevant later for marine deployment).
5. **No vendoring of copyleft code, ever** (boundary rules above).
6. **Not a FreeCAD plugin/macro ecosystem.** That would drag BLUECAD into an
   LGPL GUI process and an unstable API surface.
7. **No BlueRev formulas in JarvisOS adapter code.** Sizing rules,
   correlations, gas-exchange models, and design heuristics live in the
   BlueRev domain package; adapters receive them already resolved into
   neutral geometry/analysis specs. Code layering only — see boundary rule 5;
   the data itself flows freely, everything is local.

### Legal risk register

| # | Risk | Severity | Mitigation |
| --- | --- | --- | --- |
| R1 | Someone imports the `gmsh` (or future GPL tool) Python SDK in-process for convenience, creating a derivative-work condition if ever distributed | High | Boundary rule 1 as a hard invariant in `AGENTS.md`-level policy; adapter contract exposes only subprocess runners; CI grep for `import gmsh` and similar in JarvisOS/BlueRev packages |
| R2 | Future freezing/bundling (installer, PyInstaller) statically combines OCCT/OCP, weakening LGPL compliance | Medium | Before any distribution decision, re-audit packaging; keep OCP as replaceable wheels |
| R3 | Untrusted third-party CalculiX Windows binaries (provenance/malware/license ambiguity) | Medium | Tool registry records source URL, version, SHA-256 for every external binary; prefer official or widely-trusted builds |
| R4 | LLM-generated adapter or geometry code reproduces copyleft snippets from training data | Medium | Generated code may target only documented public APIs; keep GPL source out of prompt context; license-similarity scan on adapter code at review time (fits the existing tiered PR-review pipeline) |
| R5 | Trademark misuse ("powered by OpenFOAM/FreeCAD") | Low | Use factual compatibility wording; check OpenCFD trademark policy before any public material |
| R6 | Assuming "internal use, so GPL doesn't matter" and letting boundaries erode until a distribution event makes cleanup expensive | Medium | Treat mode C/D boundaries as architecture, not legalese; enforced by adapter contracts |
| R7 | GPL-2.0 tools carry no express patent grant | Low | Accepted; noted for completeness |
| R8 | Clean-room erosion: reading upstream source "to understand" and unconsciously translating it | Medium | Policy: adapters authored from docs/public API/examples only; source reading requires an explicit note in the PR describing what was read and why |

## Verification ledger

| Item | How verified | Date |
| --- | --- | --- |
| Gmsh GPL-2.0-or-later; linking exception covers only Gmsh-with-{Netgen, METIS, OpenCASCADE, ParaView}; no downstream linking exemption | Fetched `gmsh.info/LICENSE.txt` | 2026-07-03 |
| PicoGK Apache-2.0 | GitHub license API for `leap71/PicoGK` | 2026-07-03 |
| All other rows | Model knowledge, high confidence | must be re-verified against each repo's LICENSE at version-pin time (roadmap slice) |

## Open questions carried to Task 2 (contracts)

- Exact neutral geometry-spec schema shared by BlueRev domain code and the CAD
  adapter (JSON, versioned, deterministic).
- Whether the CAD adapter executes LLM-proposed scripts in the existing
  JarvisOS sandboxed runner (network-blocked, path-constrained) — likely yes;
  it already matches the threat model.
- CalculiX result-parsing contract (`.frd` subset) and which quantities are
  first-class (max von Mises, max displacement, first natural frequency).
- CAD adapter must emit a web-viewable artifact (GLB or STL) alongside STEP,
  so the JarvisOS frontend can render an interactive 3D preview (roadmap
  slice in Task 4).
