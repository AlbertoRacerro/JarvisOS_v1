# Spec 209 — Engineering Studio demonstrator: implementation evidence

## What was built

- `backend/app/modules/studio/demonstrator.py`: repository-owned demonstrator content and
  `ensure_example()`, which creates the `engineering-studio-example` workspace and drives the
  existing Studio services (`create` → `update` → `test` → `publish`) for four artifacts:
  - **Pipe pressure drop (Darcy-Weisbach)**: calculation; laminar 64/Re below Re 2300,
    Colebrook-White (Swamee-Jain start, fixed point) at and above. Three cases (two turbulent,
    one laminar) whose expected outputs come from an independent scipy `brentq` root solve.
  - **Flanged tube spool**: build123d geometry; volume bounds are the analytic annulus volume ±0.1 %.
  - **Harvest settler**: steady process unit splitting biomass by recovery; host balance checks pass.
  - **Harvest cycle**: draw/settle/refill/dose procedure, tested (simulate=true, 14 expectations) on
    an `Example culture loop` Process draft created in the workspace (dark, loss-free verification
    scenario with closed-form post-event tank states).
  Every artifact records AI-prepared, validity-range and unqualified assumptions.
- `POST /studio/example-workspace` (runner-origin guarded). Idempotent: an artifact that already
  exists by name is never touched, so a repeated request leaves operator edits intact, and an
  interrupted build completes only the missing artifacts. A runtime-unavailable request is refused
  (`studio_runtime_unavailable`, 503) before anything is created.
- Studio header control **Open example workspace**: calls the action, switches workspace and shows
  the result notice. The notice is carried across the remount that a new workspace triggers.

## Verification

- `backend/tests/test_studio_demonstrator_209.py` (5 tests, real bubblewrap runtime): four published
  artifacts with passing reports bound to source and contract; pipe outputs equal an independent
  Colebrook root solve (laminar and turbulent); spool volume and bounding box equal the analytic
  values; settler mass and biomass partition close; the procedure's literal expectations equal the
  closed form recomputed in the test; repeated action is idempotent and keeps an edited draft; a
  deleted artifact is recreated without touching the others; runtime-disabled refusal creates
  nothing; a foreign browser origin is refused. Existing Studio suites 187–193 plus 209: 142 passed.
  CI skips these runtime tests (`JARVISOS_STUDIO_CI_SANDBOX_UNAVAILABLE`), as for specs 188–191.
- Frontend: `npm run build` (all suites including the new `test:209`, `tsc`, Vite) passed.
- Real Chromium (`capture.mjs`, `r1/report.json`, screenshots in
  `~/jarvis-control/work/evidence/209-browser/`), fresh data root, backend with the Studio runtime
  enabled:

| Step | Result |
| --- | --- |
| Open example workspace | Created in 7.9 s; notice "Example workspace ready: 4 verified artifacts published"; Library lists the four published versions. |
| Open each artifact | Pipe, spool, settler and procedure each open in the normal editor with their tabs (Contract/Code/Documentation/Tests/Versions/Run; procedure Steps/Test bench). |
| Calculation run | Existing run flow, water case: pressure_drop 45.33852884570226 kPa, Re 70467.27, f 0.0226941875692, matching the independent reference. |
| Geometry run | Existing generation flow: valid single solid, 364739 mm³ (analytic 364736 mm³), 120 × 120 × 300 mm, 3D preview, STEP/STL/GLB artifacts. |
| Revise / edit / re-test / re-publish | Revise opened a draft, the source was edited in the code editor, a new case with expected pressure drop passed, and v2 was published. |
| Repeat action | Notice "existing artifacts, including your edits, were left unchanged"; pipe stays at v2, nothing duplicated. |
| Dark/Light × 1440/390 | Correct theme, 0 px horizontal overflow. |
| Errors | 0 page or console errors across the walk and matrix. |

Pre-existing and out of scope: the Library repeats the model name before a version label that
already contains it, for every Studio entry (for example "Harvest cycle Harvest cycle v1").
