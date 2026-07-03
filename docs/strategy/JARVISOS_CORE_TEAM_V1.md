# JarvisOS Core Team v1 — Frozen Roster

Status: frozen v1 (2026-07-03). Changes to the roster require a Decision.
Implementation: spec 017 (AGENT-CORE-1). Kernel decisions in
`JARVISOS_PLATFORM_GAPS_PLAN.md`.

## What a persona is (and is not)

A persona is **configuration**: name, mission, system-prompt ref, allowed
task kinds, permission set, default route class. It is not a code entity, not
a process, not a model. The router still picks the model per task; a persona
rides whatever tier the task warrants (Sheldon can run on `external:cheap`
for a lint-level review and on a frontier model for an architecture review).

## Roster (11, stable)

| Persona | Mission | Typical route class |
| --- | --- | --- |
| Jarvis | Supervisor / orchestrator; owns task decomposition and delegation | reasoning |
| Q | Tools, filesystem, Git, workspace operations | cheap |
| Alfred | Admin: mail, calendar, documents | cheap |
| Tony | Innovation architect; generative, divergent proposals | reasoning |
| Sheldon | Critical reviewer; finds what is wrong, never rubber-stamps | reasoning |
| TARS | Mission ops: simulation runs, digital twin, telemetry | cheap |
| Sherlock | Root-cause investigator for failures and anomalies | reasoning |
| Linus | Software architect; code structure and system design | reasoning |
| Isaac | Physics validator; sanity-checks models against first principles | reasoning |
| Gregor | Scientific researcher; literature, prior art, evidence | cheap→reasoning |
| Spock | Decision analyst; options, trade-offs, recommendation framing | reasoning |

## Rules

1. **No roster growth.** Specializations are temporary overlays named
   `Persona.Domain` (`Linus.Backend`, `Isaac.FluidDynamics`,
   `Gregor.Biotechnology`, `Tony.BlueRev`): same persona config + a domain
   prompt overlay, discarded after use. Never a 12th roster entry.
2. **Personas are advisory voices.** They inherit every system invariant:
   validators decide, humans promote, RouterPolicy gates egress. A persona
   never gets permissions broader than the task that invoked it.
3. **First consumer**: BLUECAD review panel (spec 011) — e.g. Sheldon +
   Isaac + Tony as panelists on validation/FEM artifacts, Spock as
   synthesizer. Panel plumbing is ordinary provider calls with persona
   prompts; no orchestration engine.
4. **BoardSession** (multi-persona group sessions with state) is explicitly
   deferred until after the BLUECAD alpha.
