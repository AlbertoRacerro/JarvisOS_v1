# 217 — Provider quota rings in Coding → Runtime

State: **in review** (live state in [`STATUS.md`](STATUS.md)). Maintainer [issue #919](https://github.com/AlbertoRacerro/JarvisOS_v1/issues/919), assigned by the maintainer to a separate interactive cloud lane ([claim](https://github.com/AlbertoRacerro/JarvisOS_v1/issues/919#issuecomment-6384160561)). Depends on 206. Contract and implementation ship in one PR because this is a small read-only enhancement.

## Outcome

Beside the spec 206 Relay owner panel, Coding → Runtime shows how much provider quota is left: one column each for Claude, Codex (ChatGPT) and Antigravity; a 5-hour row and a weekly row; and an extra row only for a model-specific pool the provider actually reports (for example an Opus weekly window). Each cell is a ring with the **remaining** percentage visible in its centre, the time to reset, and distinct states for exhausted, out of date, not signed in and not available. A missing value is never drawn as 0 %.

## Contract

1. **Source.** Claude and Codex windows come from `agent-relay --json limits --refresh`, the source spec 195 already uses (`agents[].agent_key/status/as_of/windows[].id/used_percent/resets_at`, optional `label` and `window_minutes`). The backend runs it at most once per TTL (default 600 s, `JARVISOS_PROVIDER_QUOTA_TTL_S`, bounded 60–3600 s), with concurrent requests sharing one reading. The binary can be overridden with `JARVISOS_AGENT_RELAY_BIN`. No provider is probed for the UI, and no credit-consuming call is made.
2. **Normalisation.**
   - `window_minutes` 300/10080 classifies a window as 5-hour or weekly. Otherwise these ids do: `five_hour`, `5h`, `session`, `primary`, `hourly` for 5-hour; `seven_day`, `weekly`, `week`, `7d`, `secondary` for weekly. Anything else is a pool row.
   - `remaining = 100 − used_percent`.
   - Out-of-range, non-numeric or boolean usage drops the window.
   - A window is *out of date* when the reading is older than 30 minutes or its reset time has already passed. A passed reset never shows as exhausted.
3. **Antigravity** has no verified legitimate local source, so it is reported as not available with a pointer to its own settings page. Nothing is estimated from sessions or tokens, and no private endpoint or cookie is used.
4. **Safety.** The endpoint `GET /api/coding/provider-quotas?repository=…` is read-only and repository-scoped like spec 206. Only validated numbers, ISO timestamps and short identifiers reach the browser. Ids or labels that look like tokens or match `devctx.find_secret` are dropped. No stdout, stderr or paths are forwarded.
5. **UI.** The view is read-only with no controls and re-asks the server once a minute (the server cache bounds CLI calls). It uses Lumen tokens in Light and Dark, stacks under the owner panel below 900 px, provides ARIA labels with the same value as the ring, and respects reduced motion.

## Non-goals

No change to the supervisor, failover, mission state, provider login, credentials or quotas. No new store, daemon or scheduler. No ChatGPT web-conversation quota (Codex CLI only).

## Evidence

- Backend tests: `backend/tests/test_coding_provider_quota_217.py` covers window kinds, `window_minutes`, exhausted/stale/past reset, unusable windows, unauthenticated/missing/unreadable states, Antigravity never estimated, secret and path exclusion, TTL cache and bounds, missing binary, and repository scoping.
- Frontend test: `frontend/tests/217-provider-quota-rings.mjs`, which renders the real view.
- Chromium screenshots in Light/Dark, wide and narrow, against a fake `agent-relay`, attached to the PR.

The exact `agent-relay limits` window ids on the maintainer's host still need to be checked once with a real reading. The normaliser accepts both id conventions above, and an unknown id appears as its own row instead of being misfiled.
