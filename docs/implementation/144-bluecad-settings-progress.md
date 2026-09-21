# Spec 144 BLUECAD / Settings checkpoint

2026-09-16. Bounded implementation only; not full spec acceptance and not merge authority.

Changes:
- BLUECAD no longer labels existing mesh selection, orbit, pan, zoom, inspection or artifact access as unavailable authoring. Visible instructions describe actual OrbitControls/pick behavior; unsupported authoring controls remain disabled. Inspect candidate opens the existing sidecar.
- Stage inspector content appears before model-contract controls without a collapsed disclosure. Candidate lifecycle, parked reason, validation and artifact links remain canonical aggregate reads.
- New candidate explains server-controlled generation and reports the reread saved lifecycle/parked reason. Archived geometry-empty copy describes the historical generation outcome rather than claiming the candidate remains parked.
- Settings distinguishes enabled configuration from runtime reachability. Failed initial canonical reads offer Reload settings; missing usage and external-call permission are unavailable/checking rather than fabricated zero/blocked facts. No credential, egress, provider, budget or backend policy changes.

Evidence:
- `cd frontend && npm run build`: PASS, including existing contract gates, TypeScript and Vite. Existing chunk-size warning remains. Final subsequent change only adjusts archived geometry-empty wording; browser below exercised that final copy.
- `git diff --check` on the four owned frontend files: PASS.
- Real Chromium + Vite + FastAPI + isolated SQLite, ports 5193/8023, no mocked success responses: candidate brief saved under paid-disabled/zero-budget defaults; actual result `parked` / `budget_blocked`; inspector visible; page reload retained candidate; Archive + Show archived worked; backend restart retained archived candidate.
- BLUECAD screenshots at 1600 and 1280 widths: no document horizontal overflow. Visually inspected compact BLUECAD and Settings screenshots.
- Settings browser confirmed configured/runtime wording; deliberately aborted `/ai/settings` read exposed Reload settings and unavailable usage, then removal of the fault and Reload recovered actual canonical data. No Settings writes or credentials exercised. No browser page errors.
- Reproduction harness: scratch `/workspace/scratch/61bf444950e2/bluecad-settings-smoke.mjs`, derived from checked-in `scripts/144-operator-browser-smoke.mjs`; evidence `/workspace/scratch/61bf444950e2/bluecad-settings-evidence`. Uses venv Python, primary-runtime Playwright and scratch `roadmap-browser/chromium`. Backend, frontend and browser must share one command/network namespace. Archived checkbox proof uses keyboard Space; Playwright click/check intermittently observed the checkbox before React propagated the change.

Remaining proof limits:
- No paid generation executed; no live provider availability claimed.
- Actual generated GLB orbit/pan/pick and artifact download were traced to existing owners, not newly exercised with generated geometry in this browser run. Parked candidate has no geometry/artifacts.
- Full spec 144 acceptance and approved-reference fidelity remain the coordinator's broader work.
