# 206 — Coding Relay monitor: implementation evidence

Spec: [206](../specs/206-coding-relay-monitor.md), issue #859 Phase B.

The Coding → Runtime panel reads the spec 205 adapter through two local-operator GET routes. The adapter supplies the owner snapshot and cursor-paged event items. The backend rejects secret-bearing or oversized responses. It takes no owner, mission, ledger or Relay lock and writes no control state. The panel polls, resumes from its cursor, bounds retained lines, and opens longer details on demand.

## Verification

- `backend/tests/test_coding_relay_monitor_206.py`: cursor paging and resume, a multi-item event split across pages, torn lines, turn/session/mission handoff, payload bounds and redaction, missing/unreadable state, and unchanged control/session files. The focused relay/Coding suite passed: 68 tests.
- Exact-head review found that browser path scrubbing missed Windows drive and UNC paths, as well as uncommon POSIX roots. The adapter now scrubs those paths in browser items; a regression test covers all three forms. The terminal observer's rendering remains unchanged.
- `frontend/tests/206-coding-relay-monitor.mjs`: rendered semantic header, timeline, details, unknown and empty states, and route wiring. `npm run build` passed, including TypeScript and the frontend suite.
- Live browser evidence from the running cycle 7 owner is in `/home/thera/jarvis-control/work/evidence/206-browser/`: `runtime-wide.png` and `runtime-narrow.png` show Coding → Runtime and the active mission; `follow.log` records the concurrent `relay_observe.py follow`; `order-compare.txt` records 158 compared events in the same order, zero mismatches, no detected secret or home path in the API payload; `locks-held-by-monitor.txt` is empty. This browser proof predates the later backend-only cursor fix for multi-item events. The fix is covered by the backend test above; it does not change the rendered panel.

The screenshots show the mission, task, owner liveness and current turn while the owner continued producing events. They contain no visible secret. No provider or owner control action was used for the proof.
