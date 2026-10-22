# 206 — Relay monitor in JarvisOS Coding

State: **ready** (live state in [`STATUS.md`](STATUS.md)). Maintainer [issue #859](https://github.com/AlbertoRacerro/JarvisOS_v1/issues/859) Phase B, ordered second by the binding 2026-10-22 directive `L20261022051213-c458`, after spec 205 (#866 and #859 Phase A). Depends on 205. Implementation starts only after 205 is merged.

## Outcome

From Coding → Runtime the maintainer sees what the spec 201 owner is doing without opening a terminal. The view shows the same semantic state as the spec 205 digest (mission, task, `running`/`checkpointed`/`held`/… with reason) and a terminal-style timeline of the active turn: assistant messages, tool calls and results, errors, provider switches and session handoffs. Each line is bounded and scrubbed, and details open on demand. The browser view and `relay_observe.py follow` can run at the same time and show the same events in the same order.

## Design constraints

- Reuse exactly the spec 205 adapter (`snapshot`, event rendering, redaction, session discovery and handoff). Do not copy its logic into the backend, and do not add a second session store, scheduler, provider, coordinator, daemon or standalone dashboard.
- The server reads and scrubs. The backend exposes a read-only endpoint, or a small pair of endpoints, that returns the snapshot and a bounded page of timeline events after an opaque cursor. Payloads have hard size limits, use redaction from the adapter and are rejected if `devctx.find_secret` matches. History is paged and reconnecting resumes from the cursor. The client may poll the cursor endpoint or use SSE, whichever is smaller. The browser never receives raw `output.jsonl`, filesystem paths outside the repository's relay tree, or hidden reasoning.
- The endpoint uses the same local-operator access rules as the existing Coding runtime routes. It never takes `coordinator.lease`, `serve.lock` or any other lock, writes owner, mission or ledger state, signals a process or calls a provider. When owner state is missing or unreadable, it returns a truthful `unknown` with a reason, not an error page.
- Frontend: a compact panel in the existing Coding runtime surface, using the shell's existing components and styles. Do not redesign the page. No input box in this slice. If one is added later, it must queue a ledger directive for the next boundary and never inject into a live turn.

## Acceptance

1. Backend tests cover cursor paging and resume, torn final JSONL lines, a session handoff in the middle of the timeline, bounds and secret redaction, `unknown` on missing state, and no lock or write in the control root (verified the same way as the spec 205 follow test).
2. Frontend tests cover the semantic header, timeline rendering, details disclosure, and the empty and unknown states.
3. A real browser on the workstation shows the active background mission while `relay_observe.py follow` is attached at the same time. Ordering and provenance match, the owner does not stall and there are no lock conflicts. Screenshots or a recording are stored without secrets.
4. Exact-head CI, merge and `STATUS.md` reconciliation follow the normal rules.

## Non-goals

Phase C of #859 (H2O/Qwen evaluation), any write or control action from the browser, notifications (spec 205 owns Slack), and changes to the installed Relay package.
