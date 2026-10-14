# Spec 190 GUI acceptance — 2026-10-14

The browser journey ran against repaired product-code HEAD `764cfb022e259156dd9268ce3cf255b9cbcf1574` on the WSL2 qualification host. It used headless Playwright Chromium, a fresh isolated `JARVISOS_DATA_ROOT`, the enabled 187 bubblewrap runtime, and real DWSIM 10.2.9 through MCP executable SHA-256 `d20f97426c264ac91114240b085b3c4e7877dfda83ecb487c0125f838cf66cfa`. The operator used the GUI only; no backend API mutation, hand-written draft JSON, terminal action in the product workflow, or direct DWSIM operation supplied a step.

The operator created a `process_unit` with `culture` and `dose` inlets, `outlet` and `unused_dose` outlets, and a percent `dose_split` parameter. They edited `evaluate` in CodeMirror, saved, passed a real sandbox test, and published v1. In Process they placed the published unit and a Heater, wired two feeds and both unit outlets, set feed states and parameters through inspectors, and ran the solve.

| GUI run | Result |
| --- | --- |
| v1, split 20%, `e184ae1a72a04d65a01e4c20f7116464` | Converged. Product nitrogen 0.14264 kg/m³; both outlets had DWSIM properties; downstream Heater outlet 310 K; whole-graph mass and culture balances passed. |
| v1, split 90%, `5e14f84fe9834dbf9de00c2eaefadfc7` | Converged. Product nitrogen 0.40747 kg/m³; both outlets and balances passed. |
| v2 after explicit GUI update, `a2c523cacdc04e4d87c2199a3034c08e` | Converged with balances passed. Publishing v2 had left the placed v1 pin and its past run unchanged; the old run was shown as superseded. |

The seven screenshots here are original captures from that journey. Their SHA-256 values are in [SHA256SUMS](SHA256SUMS) and match the raw evidence manifest at `/tmp/jarvis190-browser-764cfb02/SHA256SUMS` on the qualification host. The raw report there records the exact GUI actions and replay commands. `test-report.png` shows the passing Studio test; `process-placed.png` shows the palette and placed unit; the two `run-v1-*-balances.png` captures show both balance checks; `v2-published-old-pin.png` shows the unchanged pin; `run-v2-current.png` shows the final run.

One nonblocking wording issue was observed: an acyclic mixed solve summary says “culture-only loop.” It did not affect the solve or acceptance result.
